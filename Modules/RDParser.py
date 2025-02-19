# RDParser.py

# Recursive Descent Parser
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-17
# Version: 1.0
# Description: Recursive Descent Parser for Ada Compiler Construction

import os
import re
import sys
import logging
from typing import List, Optional
from pathlib import Path

# Setup the repository home path so that we can import modules from the parent directory.
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger
from Modules.LexicalAnalyzer import LexicalAnalyzer


class RDParser:
    def __init__(self, stop_on_error=False):
        self.tokens = []
        self.current_index = 0
        self.current_token = None
        self.stop_on_error = stop_on_error
        self.errors = []
        self.parse_tree_root = None
        self.logger = Logger()

    def parse(self, tokens: List[Token]):
        self.logger.debug("Starting parse with RDParser.")
        self.tokens = tokens
        self.current_index = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
        try:
            self.parseProg()  # Start symbol
            if self.current_token and self.current_token.token_type != Definitions().TokenType.EOF:
                self.report_error("Extra tokens after program end.")
            self.print_summary()
            return len(self.errors) == 0
        except Exception as e:
            self.logger.error(f"Parsing failed: {str(e)}")
            return False

    def advance(self):
        self.current_index += 1
        if self.current_index < len(self.tokens):
            self.current_token = self.tokens[self.current_index]
        else:
            self.current_token = None

    def match(self, expected_token_type):
        if self.current_token and self.current_token.token_type == expected_token_type:
            # Store the original identifier if this is an ID token for end procedure name matching
            if expected_token_type == Definitions().TokenType.ID:
                if not hasattr(self, 'procedure_name'):
                    self.procedure_name = self.current_token.lexeme.lower()
                elif expected_token_type == Definitions().TokenType.ID and self.current_token.lexeme.lower() != self.procedure_name:
                    self.report_error(f"Procedure name mismatch. Expected '{self.procedure_name}', found '{self.current_token.lexeme}'")
            
            self.logger.debug(f"Matched {expected_token_type.name} with token '{self.current_token.lexeme}'.")
            self.advance()
        else:
            token_name = self.current_token.lexeme if self.current_token else "EOF"
            self.report_error(f"Expected {expected_token_type.name}, found '{token_name}'")

    def report_error(self, message: str):
        # Only report each unique error once
        line_num = self.current_token.line_number if self.current_token else "unknown"
        col_num = self.current_token.column_number if self.current_token else "unknown"
        full_message = f"Error at line {line_num}, column {col_num}: {message}"
        
        if full_message not in self.errors:  # Only add if not already reported
            self.logger.error(full_message)
            self.errors.append(full_message)
        
        if self.stop_on_error:
            raise Exception(full_message)

    def print_summary(self):
        if self.errors:
            self.logger.info(f"\nParsing completed with {len(self.errors)} error(s):")
            for err in self.errors:
                print(err)  # Print directly to console for cleaner output
        else:
            self.logger.info("\nParsing completed successfully with no errors.")

    # Grammar implementation methods below
    def parseProg(self):
        self.procedure_name = None  # Reset procedure name at start of each procedure
        self.match(Definitions().TokenType.PROCEDURE)
        self.match(Definitions().TokenType.ID)
        self.parseArgs()
        self.match(Definitions().TokenType.IS)
        self.parseDeclarativePart()
        self.parseProcedures()
        self.match(Definitions().TokenType.BEGIN)
        self.parseSeqOfStatements()
        self.match(Definitions().TokenType.END)
        self.match(Definitions().TokenType.ID)  # Will verify procedure name matches
        self.match(Definitions().TokenType.SEMICOLON)
        self.procedure_name = None  # Clear for next procedure

    def parseDeclarativePart(self):
        if self.current_token and self.current_token.token_type == Definitions().TokenType.ID:
            self.parseIdentifierList()
            self.match(Definitions().TokenType.COLON)
            self.parseTypeMark()
            self.match(Definitions().TokenType.SEMICOLON)
            self.parseDeclarativePart()
        else:
            self.logger.debug("DeclarativePart -> ε")

    def parseIdentifierList(self):
        self.match(Definitions().TokenType.ID)
        while self.current_token and self.current_token.token_type == Definitions().TokenType.COMMA:
            self.match(Definitions().TokenType.COMMA)
            self.match(Definitions().TokenType.ID)

    def parseTypeMark(self):
        dt = Definitions().TokenType
        if self.current_token and self.current_token.token_type in {dt.INTEGER, dt.REAL, dt.CHAR}:
            self.match(self.current_token.token_type)
        elif self.current_token and self.current_token.token_type == dt.CONSTANT:
            self.match(dt.CONSTANT)
            self.match(dt.ASSIGN)
            self.parseValue()
        else:
            self.report_error("Expected type (integer, real, char) or constant declaration.")

    def parseValue(self):
        self.match(Definitions().TokenType.NUM)

    def parseProcedures(self):
        if self.current_token and self.current_token.token_type == Definitions().TokenType.PROCEDURE:
            self.parseProg()
            self.parseProcedures()
        else:
            self.logger.debug("Procedures -> ε")

    def parseArgs(self):
        if self.current_token and self.current_token.token_type == Definitions().TokenType.LPAREN:
            self.match(Definitions().TokenType.LPAREN)
            self.parseArgList()
            self.match(Definitions().TokenType.RPAREN)
        else:
            self.logger.debug("Args -> ε")

    def parseArgList(self):
        self.parseMode()
        self.parseIdentifierList()
        self.match(Definitions().TokenType.COLON)
        self.parseTypeMark()
        self.parseMoreArgs()

    def parseMoreArgs(self):
        if self.current_token and self.current_token.token_type == Definitions().TokenType.SEMICOLON:
            self.match(Definitions().TokenType.SEMICOLON)
            self.parseArgList()
        else:
            self.logger.debug("MoreArgs -> ε")

    def parseMode(self):
        dt = Definitions().TokenType
        if self.current_token and self.current_token.token_type in {dt.IN, dt.OUT, dt.INOUT}:
            self.match(self.current_token.token_type)
        else:
            self.logger.debug("Mode -> ε")

    def parseSeqOfStatements(self):
        self.logger.debug("SeqOfStatements -> ε")