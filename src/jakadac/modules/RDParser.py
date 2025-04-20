"""
RDParser.py
-----------
Recursive Descent Parser for a subset of Ada.
Author: John Akujobi
GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
Date: 2024-02-17
Version: 1.3

This module defines the RDParser class which receives a list of tokens
from the lexical analyzer (via JohnA3.py) and verifies the syntactic correctness
of the source program according to the following CFG:

    Prog -> procedure idt Args is
            DeclarativePart
            Procedures
            begin
            SeqOfStatements
            end idt;

    DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε

    IdentifierList -> idt | IdentifierList , idt

    TypeMark       -> integert | realt | chart | const assignop Value 

    Value          -> NumericalLiteral

    Procedures     -> Prog Procedures | ε

    Args           -> ( ArgList ) | ε

    ArgList        -> Mode IdentifierList : TypeMark MoreArgs

    MoreArgs       -> ; ArgList | ε

    Mode           -> in | out | inout | ε

    SeqOfStatements -> ε

The parser supports configurable error handling:
    - stop_on_error: if True, it stops on error and asks the user whether to continue.
    - panic_mode_recover: if True, it attempts panic-mode recovery.
    
If build_parse_tree is enabled, the parser constructs a parse tree and prints it
using wide indentation with hyphens and vertical bars.
A summary report is printed at the end of parsing.

The implementation includes comprehensive null safety checks to prevent
attribute access on potentially None objects, and proper type hints
to support static type checking.
"""
from typing import List, Optional, Any, Dict, Union

from .Token import Token
from .Definitions import Definitions
from .Logger import Logger

class RDParser:
    def __init__(self, tokens, defs, stop_on_error=False, panic_mode_recover=False, build_parse_tree=False):
        """
        Initialize the recursive descent parser.

        Parameters:
            tokens (List[Token]): The list of tokens provided by the lexical analyzer.
            defs (Definitions): The definitions instance provided by the lexical analyzer.
            stop_on_error (bool): If True, the parser stops on error and prompts the user.
            panic_mode_recover (bool): If True, the parser attempts panic-mode recovery.
            build_parse_tree (bool): If True, a parse tree is built during parsing.
            
        Note:
            The parser includes null safety checks to prevent runtime errors
            when accessing attributes of tokens or nodes that might be None.
        """
        self.tokens = tokens
        self.current_index = 0
        self.current_token: Optional[Token] = tokens[0] if tokens else None
        self.stop_on_error = stop_on_error
        self.panic_mode_recover = panic_mode_recover
        self.build_parse_tree = build_parse_tree
        self.errors = []
        self.logger = Logger()  # Using the singleton Logger instance
        self.defs = defs
        self.parse_tree_root = None  # Will hold the root if tree building is enabled
        self.current_node: Optional[ParseTreeNode] = None

    def parse(self) -> bool:
        """
        Main entry point to start parsing.
        Invokes the start symbol (parseProg) and then checks for EOF.
        If build_parse_tree is enabled, stores the resulting tree.
        Returns True if no errors were encountered.
        """
        self.logger.debug("Starting parse with RDParser.")
        tree = self.parseProg()
        if self.build_parse_tree:
            self.parse_tree_root = tree
        if self.current_token and self.current_token.token_type != self.defs.TokenType.EOF:
            self.report_error("Extra tokens found after program end.")
        self.print_summary()
        return len(self.errors) == 0

    def advance(self):
        """Advance to the next token."""
        self.current_index += 1
        if self.current_index < len(self.tokens):
            self.current_token = self.tokens[self.current_index]
        else:
            self.current_token = Token(self.defs.TokenType.EOF, "EOF", -1, -1)

    def match(self, expected_token_type: Any) -> None:
        """
        Compare the current token against the expected token type.
        If they match, advance to the next token.
        Otherwise, report an error.
        """
        if self.current_token and self.current_token.token_type == expected_token_type:
            self.logger.debug(f"Matched {expected_token_type.name} with token '{self.current_token.lexeme}'.")
            self.advance()
        else:
            lexeme = self.current_token.lexeme if self.current_token else "None"
            self.report_error(f"Expected {expected_token_type.name}, found '{lexeme}'")
            # Optionally, panic recovery could be invoked here.

    def match_leaf(self, expected_token_type: Any, parent_node: Optional['ParseTreeNode']) -> None:
        """
        Helper function for parse tree building.
        Matches the expected token type, creates a leaf ParseTreeNode,
        attaches it to parent_node (if provided), and advances the token.
        """
        if self.current_token and self.current_token.token_type == expected_token_type:
            leaf = ParseTreeNode(expected_token_type.name, self.current_token)
            if parent_node:
                parent_node.add_child(leaf)
            self.logger.debug(f"Matched {expected_token_type.name} with token '{self.current_token.lexeme}'.")
            self.advance()
        else:
            lexeme = self.current_token.lexeme if self.current_token else "None"
            self.report_error(f"Expected {expected_token_type.name}, found '{lexeme}'")

    def report_error(self, message: str):
        """
        Log and record an error message.
        If stop_on_error is True, prompt the user to continue.
        """
        line_number = self.current_token.line_number if self.current_token else "unknown"
        column_number = self.current_token.column_number if self.current_token else "unknown"
        full_message = (f"Error at line {line_number}, column {column_number}: {message}")
        self.logger.error(full_message)
        self.errors.append(full_message)
        if self.stop_on_error:
            user_choice = input("Stop on error? (y/n): ")
            if user_choice.lower() == 'y':
                raise Exception("Parsing halted by user due to error.")

    def panic_recovery(self, sync_set: set):
        """
        Attempt panic-mode recovery by skipping tokens until a synchronization token is found.
        """
        if not self.panic_mode_recover or not self.current_token:
            return
        self.logger.debug("Entering panic-mode recovery.")
        while (self.current_token and 
               self.current_token.token_type not in sync_set and 
               self.current_token.token_type != self.defs.TokenType.EOF):
            self.advance()
        self.logger.debug("Panic-mode recovery completed.")

    def print_summary(self):
        """
        Print a summary report indicating the number of errors and overall success.
        """
        if self.errors:
            self.logger.info(f"Parsing completed with {len(self.errors)} error(s).")
            for err in self.errors:
                self.logger.error(err)
        else:
            self.logger.info("Parsing completed successfully with no errors.")

    def print_parse_tree(self):
        """
        Print the constructed parse tree using a wide indentation style with connectors.
        """
        if not self.build_parse_tree:
            self.logger.info("Parse tree building is disabled.")
            return
        if not self.parse_tree_root:
            self.logger.info("No parse tree available.")
            return
        self._print_tree(self.parse_tree_root)

    def _print_tree(self, node, prefix="", is_last=True):
        """
        Recursive helper to print a parse tree node with wide indentation.
        Uses ASCII connectors (+--, |--) to avoid Unicode rendering issues.
        """
        # Use ASCII connectors to avoid Unicode issues
        connector = "+-- " if is_last else "|-- "
        print(prefix + connector + str(node))
        new_prefix = prefix + ("    " if is_last else "|   ")
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            self._print_tree(child, new_prefix, i == (child_count - 1))

    # ------------------------------
    # Nonterminal Methods (CFG)
    # ------------------------------

    def parseProg(self):
        """
        Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Prog")
        else:
            node = None
        self.logger.debug("Parsing Prog")
        if self.build_parse_tree:
            self.match_leaf(self.defs.TokenType.PROCEDURE, node)
            self.match_leaf(self.defs.TokenType.ID, node)
            child = self.parseArgs()
            if child and node: node.add_child(child)
            self.match_leaf(self.defs.TokenType.IS, node)
            child = self.parseDeclarativePart()
            if child and node: node.add_child(child)
            child = self.parseProcedures()
            if child and node: node.add_child(child)
            self.match_leaf(self.defs.TokenType.BEGIN, node)
            child = self.parseSeqOfStatements()
            if child and node: node.add_child(child)
            self.match_leaf(self.defs.TokenType.END, node)
            self.match_leaf(self.defs.TokenType.ID, node)
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            return node
        else:
            self.match(self.defs.TokenType.PROCEDURE)
            self.match(self.defs.TokenType.ID)
            self.parseArgs()
            self.match(self.defs.TokenType.IS)
            self.parseDeclarativePart()
            self.parseProcedures()
            self.match(self.defs.TokenType.BEGIN)
            self.parseSeqOfStatements()
            self.match(self.defs.TokenType.END)
            self.match(self.defs.TokenType.ID)
            self.match(self.defs.TokenType.SEMICOLON)
            return None

    def parseDeclarativePart(self):
        """
        DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("DeclarativePart")
        else:
            node = None
        self.logger.debug("Parsing DeclarativePart")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            child = self.parseIdentifierList()
            if self.build_parse_tree and child and node: node.add_child(child)
            self.match_leaf(self.defs.TokenType.COLON, node)
            child = self.parseTypeMark()
            if self.build_parse_tree and child and node: node.add_child(child)
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            child = self.parseDeclarativePart()
            if self.build_parse_tree and child and node: node.add_child(child)
            return node
        else:
            if self.build_parse_tree and node:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("DeclarativePart -> ε")
                return None

    def parseIdentifierList(self):
        """
        IdentifierList -> idt | IdentifierList , idt
        """
        if self.build_parse_tree:
            node = ParseTreeNode("IdentifierList")
        else:
            node = None
        self.logger.debug("Parsing IdentifierList")
        self.match_leaf(self.defs.TokenType.ID, node)
        while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
            self.match_leaf(self.defs.TokenType.COMMA, node)
            self.match_leaf(self.defs.TokenType.ID, node)
        return node

    def parseTypeMark(self):
        """
        TypeMark -> integert | realt | chart | float | const/constant assignop Value 
        """
        if self.build_parse_tree:
            node = ParseTreeNode("TypeMark")
        else:
            node = None
        self.logger.debug("Parsing TypeMark")
        if self.current_token and self.current_token.token_type in {
            self.defs.TokenType.INTEGERT, 
            self.defs.TokenType.REALT, 
            self.defs.TokenType.CHART,
            self.defs.TokenType.FLOAT
        }:
            self.match_leaf(self.current_token.token_type, node)
        elif (self.current_token and self.current_token.token_type == self.defs.TokenType.CONSTANT or
              (self.current_token and self.current_token.lexeme.lower() in {"const", "constant"})):
            self.match_leaf(self.defs.TokenType.CONSTANT, node)
            self.match_leaf(self.defs.TokenType.ASSIGN, node)
            child = self.parseValue()
            if self.build_parse_tree and child and node:
                node.add_child(child)
        else:
            self.report_error("Expected a type (INTEGERT, REALT, CHART, FLOAT) or a constant declaration.")
        return node

    def parseValue(self):
        """
        Value -> NumericalLiteral (NUM or REAL)
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Value")
        else:
            node = None
        self.logger.debug("Parsing Value")
        
        if self.current_token and self.current_token.token_type == self.defs.TokenType.NUM:
            self.match_leaf(self.defs.TokenType.NUM, node)
        elif self.current_token and self.current_token.token_type == self.defs.TokenType.REAL:
            self.match_leaf(self.defs.TokenType.REAL, node)
        else:
            self.report_error("Expected a numerical literal (integer or float).")
        
        return node

    def parseProcedures(self):
        """
        Procedures -> Prog Procedures | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Procedures")
        else:
            node = None
        self.logger.debug("Parsing Procedures")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.PROCEDURE:
            child = self.parseProg()
            if self.build_parse_tree and child and node: node.add_child(child)
            child = self.parseProcedures()
            if self.build_parse_tree and child and node: node.add_child(child)
            return node
        else:
            if self.build_parse_tree and node:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("Procedures -> ε")
                return None

    def parseArgs(self):
        """
        Modified Args -> ( ArgList ) | ε.
        Always returns a ParseTreeNode when build_parse_tree is True.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Args")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                child = self.parseArgList()
                if child and node:
                    node.add_child(child)
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            else:
                # Add an ε leaf so that semantic analyzer can detect an empty argument list
                if node:
                    node.add_child(ParseTreeNode("ε"))
            return node
        else:
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match(self.defs.TokenType.LPAREN)
                self.parseArgList()
                self.match(self.defs.TokenType.RPAREN)
            return None

    def parseArgList(self):
        """
        ArgList -> Mode IdentifierList : TypeMark MoreArgs
        """
        if self.build_parse_tree:
            node = ParseTreeNode("ArgList")
        else:
            node = None
        self.logger.debug("Parsing ArgList")
        child = self.parseMode()
        if self.build_parse_tree and child and node: node.add_child(child)
        child = self.parseIdentifierList()
        if self.build_parse_tree and child and node: node.add_child(child)
        self.match_leaf(self.defs.TokenType.COLON, node)
        child = self.parseTypeMark()
        if self.build_parse_tree and child and node: node.add_child(child)
        child = self.parseMoreArgs()
        if self.build_parse_tree and child and node: node.add_child(child)
        return node

    def parseMoreArgs(self):
        """
        MoreArgs -> ; ArgList | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("MoreArgs")
        else:
            node = None
        self.logger.debug("Parsing MoreArgs")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            child = self.parseArgList()
            if self.build_parse_tree and child and node: node.add_child(child)
            return node
        else:
            if self.build_parse_tree and node:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("MoreArgs -> ε")
                return None

    def parseMode(self):
        """
        Mode -> in | out | inout | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Mode")
        else:
            node = None
        self.logger.debug("Parsing Mode")
        if self.current_token and self.current_token.token_type in {
            self.defs.TokenType.IN, 
            self.defs.TokenType.OUT, 
            self.defs.TokenType.INOUT
        }:
            self.match_leaf(self.current_token.token_type, node)
            return node
        else:
            if self.build_parse_tree and node:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("Mode -> ε")
                return None

    def parseSeqOfStatements(self):
        """
        SeqOfStatements -> ε | Statement SeqOfStatements
        
        In the current grammar, we have an empty body, but in future versions
        we'll expand this to support statements.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SeqOfStatements")
            # Loop until we see the END token
            while self.current_token and self.current_token.token_type != self.defs.TokenType.END:
                child = self.parseStatement()
                if child and node:
                    node.add_child(child)
            return node
        else:
            while self.current_token and self.current_token.token_type != self.defs.TokenType.END:
                self.parseStatement()
            return None

    def parseStatement(self):
        """
        Statement -> ID ASSIGN Value SEMICOLON
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Statement")
        else:
            node = None
        self.logger.debug("Parsing Statement")
        self.match_leaf(self.defs.TokenType.ID, node)
        self.match_leaf(self.defs.TokenType.ASSIGN, node)
        child = self.parseValue()
        if self.build_parse_tree and child and node:
            node.add_child(child)
        self.match_leaf(self.defs.TokenType.SEMICOLON, node)
        return node

# ------------------------------
# Parse Tree Node Class
# ------------------------------
class ParseTreeNode:
    def __init__(self, name: str, token: Optional[Token] = None):
        """
        Initialize a parse tree node.

        Parameters:
            name (str): The name of the nonterminal or token.
            token (Optional[Token]): The token associated with a terminal, or None for nonterminals.
        """
        self.name = name
        self.token = token
        self.children = []

    def add_child(self, child: 'ParseTreeNode') -> None:
        """
        Add a child node to this node.
        
        Parameters:
            child (ParseTreeNode): The child node to add
        """
        self.children.append(child)

    def find_child_by_name(self, name: str) -> Optional['ParseTreeNode']:
        """
        Find a child node by name.
        
        Args:
            name (str): The name of the child node to find
            
        Returns:
            Optional[ParseTreeNode]: The child node if found, None otherwise
        """
        for child in self.children:
            if child.name == name:
                return child
        return None
        
    def find_children_by_name(self, name: str) -> List['ParseTreeNode']:
        """
        Find all child nodes with the specified name.
        
        Args:
            name (str): The name of the child nodes to find
            
        Returns:
            List[ParseTreeNode]: List of child nodes with the specified name
        """
        return [child for child in self.children if child.name == name]
        
    def find_child_by_token_type(self, token_type: Any) -> Optional['ParseTreeNode']:
        """
        Find a child node by token type.
        
        Args:
            token_type: The token type to search for
            
        Returns:
            Optional[ParseTreeNode]: The child node if found, None otherwise
        """
        for child in self.children:
            if child.token and child.token.token_type == token_type:
                return child
        return None

    @property
    def line_number(self) -> Union[int, str]:
        """
        Get the line number from the token, or -1 if not available.
        
        Returns:
            Union[int, str]: The line number or -1 if no token is present
        """
        return self.token.line_number if self.token else -1
    
    @property
    def column_number(self) -> Union[int, str]:
        """
        Get the column number from the token, or -1 if not available.
        
        Returns:
            Union[int, str]: The column number or -1 if no token is present
        """
        return self.token.column_number if self.token else -1

    def __str__(self) -> str:
        """
        String representation of the node.
        
        Returns:
            str: A string representation including the node name and token lexeme if present
        """
        if self.token:
            return f"{self.name}: {self.token.lexeme}"
        return self.name

# End of RDParser.py
#Ada_Compiler_Construction\Modules\RDParser.py