"""
RDParser.py
-----------
Recursive Descent Parser for a subset of Ada.
Author: John Akujobi
GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
Date: 2024-02-17
Version: 1.0

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

A summary report is printed at the end of parsing.
"""

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger

class RDParser:
    def __init__(self, tokens, defs, stop_on_error=False, panic_mode_recover=False):
        """
        Initialize the recursive descent parser.

        Parameters:
            tokens (List[Token]): The list of tokens provided by the lexical analyzer.
            defs (Definitions): The definitions instance provided by the lexical analyzer.
            stop_on_error (bool): If True, the parser stops on error and prompts the user.
            panic_mode_recover (bool): If True, the parser attempts panic-mode recovery.
        """
        self.tokens = tokens
        self.current_index = 0
        self.current_token = tokens[0] if tokens else None
        self.stop_on_error = stop_on_error
        self.panic_mode_recover = panic_mode_recover
        self.errors = []
        self.logger = Logger()  # Using the singleton Logger instance
        # Use the provided definitions instance.
        self.defs = defs

    def parse(self) -> bool:
        """
        Main entry point to start parsing.
        Invokes the start symbol (parseProg) and then checks for EOF.
        Returns True if no errors were encountered.
        """
        self.logger.debug("Starting parse with RDParser.")
        self.parseProg()
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
            # Create a dummy EOF token if we run out
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
            # Optionally, if panic recovery is enabled, try to recover here.
            # For example:
            # self.panic_recovery({expected_token_type})
    
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

    # ------------------------------
    # Nonterminal Methods (CFG)
    # ------------------------------

    def parseProg(self):
        """
        Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;
        """
        self.logger.debug("Parsing Prog")
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

    def parseDeclarativePart(self):
        """
        DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε
        """
        self.logger.debug("Parsing DeclarativePart")
        if self.current_token.token_type == self.defs.TokenType.ID:
            self.parseIdentifierList()
            self.match(self.defs.TokenType.COLON)
            self.parseTypeMark()
            self.match(self.defs.TokenType.SEMICOLON)
            self.parseDeclarativePart()  # Recursive call for additional declarations
        else:
            self.logger.debug("DeclarativePart -> ε")

    def parseIdentifierList(self):
        """
        IdentifierList -> idt | IdentifierList , idt
        """
        self.logger.debug("Parsing IdentifierList")
        self.match(self.defs.TokenType.ID)
        while self.current_token.token_type == self.defs.TokenType.COMMA:
            self.match(self.defs.TokenType.COMMA)
            self.match(self.defs.TokenType.ID)

    def parseTypeMark(self):
        """
        TypeMark -> integert | realt | chart | const assignop Value 
        Here we assume basic types are represented by INTEGER, REAL, and CHAR.
        For a constant, we expect the CONSTANT keyword, an ASSIGN, then a value.
        """
        self.logger.debug("Parsing TypeMark")
        if self.current_token.token_type in {
            self.defs.TokenType.INTEGERT, 
            self.defs.TokenType.REALT, 
            self.defs.TokenType.CHART
        }:
            self.match(self.current_token.token_type)
        elif self.current_token.token_type == self.defs.TokenType.CONSTANT:
            self.match(self.defs.TokenType.CONSTANT)
            self.match(self.defs.TokenType.ASSIGN)
            self.parseValue()
        else:
            self.report_error("Expected a type (INTEGER, REAL, CHAR) or a constant declaration.")

    def parseValue(self):
        """
        Value -> NumericalLiteral
        We assume a numerical literal is represented by NUM.
        """
        self.logger.debug("Parsing Value")
        self.match(self.defs.TokenType.NUM)

    def parseProcedures(self):
        """
        Procedures -> Prog Procedures | ε
        """
        self.logger.debug("Parsing Procedures")
        if self.current_token.token_type == self.defs.TokenType.PROCEDURE:
            self.parseProg()
            self.parseProcedures()
        else:
            self.logger.debug("Procedures -> ε")

    def parseArgs(self):
        """
        Args -> ( ArgList ) | ε
        """
        self.logger.debug("Parsing Args")
        if self.current_token.token_type == self.defs.TokenType.LPAREN:
            self.match(self.defs.TokenType.LPAREN)
            self.parseArgList()
            self.match(self.defs.TokenType.RPAREN)
        else:
            self.logger.debug("Args -> ε")

    def parseArgList(self):
        """
        ArgList -> Mode IdentifierList : TypeMark MoreArgs
        """
        self.logger.debug("Parsing ArgList")
        self.parseMode()
        self.parseIdentifierList()
        self.match(self.defs.TokenType.COLON)
        self.parseTypeMark()
        self.parseMoreArgs()

    def parseMoreArgs(self):
        """
        MoreArgs -> ; ArgList | ε
        """
        self.logger.debug("Parsing MoreArgs")
        if self.current_token.token_type == self.defs.TokenType.SEMICOLON:
            self.match(self.defs.TokenType.SEMICOLON)
            self.parseArgList()
        else:
            self.logger.debug("MoreArgs -> ε")

    def parseMode(self):
        """
        Mode -> in | out | inout | ε
        """
        self.logger.debug("Parsing Mode")
        if self.current_token.token_type in {
            self.defs.TokenType.IN, 
            self.defs.TokenType.OUT, 
            self.defs.TokenType.INOUT
        }:
            self.match(self.current_token.token_type)
        else:
            self.logger.debug("Mode -> ε")

    def parseSeqOfStatements(self):
        """
        SeqOfStatements -> ε
        For the current grammar, no statements are defined.
        """
        self.logger.debug("Parsing SeqOfStatements -> ε")
        # Future extension: implement statement parsing

# End of RDParser.py
