"""
RDParser.py
-----------
Recursive Descent Parser for a subset of Ada.
Author: John Akujobi
GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
Date: 2024-02-17
Version: 1.2

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
"""

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger

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
        """
        self.tokens = tokens
        self.current_index = 0
        self.current_token = tokens[0] if tokens else None
        self.stop_on_error = stop_on_error
        self.panic_mode_recover = panic_mode_recover
        self.build_parse_tree = build_parse_tree
        self.errors = []
        self.logger = Logger()  # Using the singleton Logger instance
        self.defs = defs
        self.parse_tree_root = None  # Will hold the root if tree building is enabled

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
        if self.current_token.token_type != self.defs.TokenType.EOF:
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

    def match(self, expected_token_type):
        """
        Compare the current token against the expected token type.
        If they match, advance to the next token.
        Otherwise, report an error.
        """
        if self.current_token.token_type == expected_token_type:
            self.logger.debug(f"Matched {expected_token_type.name} with token '{self.current_token.lexeme}'.")
            self.advance()
        else:
            self.report_error(f"Expected {expected_token_type.name}, found '{self.current_token.lexeme}'")
            # Optionally, panic recovery could be invoked here.

    def match_leaf(self, expected_token_type, parent_node):
        """
        Helper function for parse tree building.
        Matches the expected token type, creates a leaf ParseTreeNode,
        attaches it to parent_node (if provided), and advances the token.
        """
        if self.current_token.token_type == expected_token_type:
            leaf = ParseTreeNode(expected_token_type.name, self.current_token)
            if parent_node:
                parent_node.add_child(leaf)
            self.logger.debug(f"Matched {expected_token_type.name} with token '{self.current_token.lexeme}'.")
            self.advance()
        else:
            self.report_error(f"Expected {expected_token_type.name}, found '{self.current_token.lexeme}'")

    def report_error(self, message: str):
        """
        Log and record an error message.
        If stop_on_error is True, prompt the user to continue.
        """
        full_message = (f"Error at line {self.current_token.line_number}, column {self.current_token.column_number}: {message}")
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
        if not self.panic_mode_recover:
            return
        self.logger.debug("Entering panic-mode recovery.")
        while (self.current_token.token_type not in sync_set and 
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
        Uses connectors (├──, └──, │) to visually trace the tree structure.
        """
        connector = "└── " if is_last else "├── "
        print(prefix + connector + str(node))
        new_prefix = prefix + ("    " if is_last else "│   ")
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
            if child: node.add_child(child)
            self.match_leaf(self.defs.TokenType.IS, node)
            child = self.parseDeclarativePart()
            if child: node.add_child(child)
            child = self.parseProcedures()
            if child: node.add_child(child)
            self.match_leaf(self.defs.TokenType.BEGIN, node)
            child = self.parseSeqOfStatements()
            if child: node.add_child(child)
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
        if self.current_token.token_type == self.defs.TokenType.ID:
            child = self.parseIdentifierList()
            if self.build_parse_tree and child: node.add_child(child)
            self.match_leaf(self.defs.TokenType.COLON, node)
            child = self.parseTypeMark()
            if self.build_parse_tree and child: node.add_child(child)
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            child = self.parseDeclarativePart()
            if self.build_parse_tree and child: node.add_child(child)
            return node
        else:
            if self.build_parse_tree:
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
        while self.current_token.token_type == self.defs.TokenType.COMMA:
            self.match_leaf(self.defs.TokenType.COMMA, node)
            self.match_leaf(self.defs.TokenType.ID, node)
        return node

    def parseTypeMark(self):
        """
        TypeMark -> integert | realt | chart | const assignop Value
        """
        if self.build_parse_tree:
            node = ParseTreeNode("TypeMark")
        else:
            node = None
        self.logger.debug("Parsing TypeMark")
        if self.current_token.token_type in {
            self.defs.TokenType.INTEGERT, 
            self.defs.TokenType.REALT, 
            self.defs.TokenType.CHART
        }:
            self.match_leaf(self.current_token.token_type, node)
        elif self.current_token.token_type == self.defs.TokenType.CONSTANT:
            self.match_leaf(self.defs.TokenType.CONSTANT, node)
            self.match_leaf(self.defs.TokenType.ASSIGN, node)
            child = self.parseValue()
            if self.build_parse_tree and child: node.add_child(child)
        else:
            self.report_error("Expected a type (INTEGERT, REALT, CHART) or a constant declaration.")
        return node

    def parseValue(self):
        """
        Value -> NumericalLiteral (assumed to be NUM)
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Value")
        else:
            node = None
        self.logger.debug("Parsing Value")
        self.match_leaf(self.defs.TokenType.NUM, node)
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
        if self.current_token.token_type == self.defs.TokenType.PROCEDURE:
            child = self.parseProg()
            if self.build_parse_tree and child: node.add_child(child)
            child = self.parseProcedures()
            if self.build_parse_tree and child: node.add_child(child)
            return node
        else:
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("Procedures -> ε")
                return None

    def parseArgs(self):
        """
        Args -> ( ArgList ) | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Args")
        else:
            node = None
        self.logger.debug("Parsing Args")
        if self.current_token.token_type == self.defs.TokenType.LPAREN:
            self.match_leaf(self.defs.TokenType.LPAREN, node)
            child = self.parseArgList()
            if self.build_parse_tree and child: node.add_child(child)
            self.match_leaf(self.defs.TokenType.RPAREN, node)
            return node
        else:
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("Args -> ε")
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
        if self.build_parse_tree and child: node.add_child(child)
        child = self.parseIdentifierList()
        if self.build_parse_tree and child: node.add_child(child)
        self.match_leaf(self.defs.TokenType.COLON, node)
        child = self.parseTypeMark()
        if self.build_parse_tree and child: node.add_child(child)
        child = self.parseMoreArgs()
        if self.build_parse_tree and child: node.add_child(child)
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
        if self.current_token.token_type == self.defs.TokenType.SEMICOLON:
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            child = self.parseArgList()
            if self.build_parse_tree and child: node.add_child(child)
            return node
        else:
            if self.build_parse_tree:
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
        if self.current_token.token_type in {
            self.defs.TokenType.IN, 
            self.defs.TokenType.OUT, 
            self.defs.TokenType.INOUT
        }:
            self.match_leaf(self.current_token.token_type, node)
            return node
        else:
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
                return node
            else:
                self.logger.debug("Mode -> ε")
                return None

    def parseSeqOfStatements(self):
        """
        SeqOfStatements -> ε
        (No statements are defined in the current grammar.)
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SeqOfStatements")
            node.add_child(ParseTreeNode("ε"))
            return node
        else:
            self.logger.debug("Parsing SeqOfStatements -> ε")
            return None

# ------------------------------
# Parse Tree Node Class
# ------------------------------
class ParseTreeNode:
    def __init__(self, name, token=None):
        """
        Initialize a parse tree node.

        Parameters:
            name (str): The name of the nonterminal or token.
            token (Token, optional): The token associated with a terminal.
        """
        self.name = name
        self.token = token
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        if self.token:
            return f"{self.name}: {self.token.lexeme}"
        return self.name

# End of RDParser.py
#Ada_Compiler_Construction\Modules\RDParser.py  