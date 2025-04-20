# LexicalAnalyzer.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-01
# Version: 1.0
# Description:
# This module implements a lexical analyzer for a subset of the Ada programming language.
# It scans source code, breaks it into tokens, and enforces specific rules (like a max identifier length).
# The code is documented so that even a Python beginner can understand what’s going on.

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

class LexicalAnalyzer:
    # A special marker (object) used to signal that a token should be skipped.
    SKIP = object()

    def __init__(self, stop_on_error=False):
        """
        Initialize the lexical analyzer.

        Parameters:
          stop_on_error (bool): If True, the analyzer stops processing when it encounters an error.
                                If False, it logs the error and skips the problematic token.
        """
        # Get our custom logger instance.
        self.logger = Logger()
        # Create an instance of Definitions to hold token patterns and token type info.
        self.defs = Definitions()
        # Configure whether to stop on error or continue and log errors.
        self.stop_on_error = stop_on_error
        # List to collect error messages.
        self.errors = []

    def analyze(self, source_code: str):
        """
        Tokenize the given source code.

        This is the main function that goes through the source code,
        skipping whitespace and comments, then matching tokens using the defined patterns.
        It returns a list of tokens ending with an EOF token.

        Parameters:
          source_code (str): The input source code as a string.

        Returns:
          List[Token]: A list of Token objects representing the tokenized source code.
        """
        tokens = []  # List to hold the tokens.
        pos = 0     # Current position in the source code.
        line = 1    # Current line number (starting at 1).
        column = 1  # Current column number (starting at 1).

        self.logger.debug("Starting tokenization of source code.")

        # Main loop: run until we reach the end of the source code.
        while pos < len(source_code):
            self.logger.debug(f"At position {pos} (line {line}, column {column}).")
            
            # Keep skipping any whitespace until nothing changes.
            while True:
                new_pos, new_line, new_column = self._skip_whitespace(source_code, pos, line, column)
                if new_pos == pos:  # No additional whitespace found.
                    break
                pos, line, column = new_pos, new_line, new_column

            # Similarly, skip over any comments (and any whitespace after them).
            while True:
                new_pos, new_line, new_column = self._skip_comment(source_code, pos, line, column)
                if new_pos == pos:
                    break  # No comment found.
                pos, line, column = new_pos, new_line, new_column
                # After a comment, there may be more whitespace – skip that too.
                while True:
                    np, nl, nc = self._skip_whitespace(source_code, pos, line, column)
                    if np == pos:
                        break
                    pos, line, column = np, nl, nc

            # Add this check to avoid matching tokens when at the end of the source code.
            if pos >= len(source_code):
                break

            # Try to match a token at the current position.
            token, new_pos, new_line, new_column = self._match_token(source_code, pos, line, column)
            if token is LexicalAnalyzer.SKIP:
                # The token matched (e.g., an identifier) was too long and should be skipped.
                pos, line, column = new_pos, new_line, new_column
                continue
            elif token:
                # If a token was successfully matched, add it to our token list.
                self.logger.debug(f"Matched token: {token} at line {line}, column {column}.")
                tokens.append(token)
                pos, line, column = new_pos, new_line, new_column
            else:
                # If no token matched, log an error and move on by one character.
                error_msg = f"Unrecognized character '{source_code[pos]}' at line {line}, column {column}."
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                pos += 1
                column += 1

        # Create and append an End-Of-File token.
        eof_token = Token(
            token_type=self.defs.TokenType.EOF,
            lexeme="EOF",
            line_number=line,
            column_number=column
        )
        tokens.append(eof_token)
        self.logger.debug("Tokenization complete. EOF token appended.")
        return tokens

    def _skip_whitespace(self, source: str, pos: int, line: int, column: int):
        """
        Skip over any whitespace characters (spaces, tabs, newlines).

        Parameters:
          source (str): The full source code.
          pos (int): The current position in the source code.
          line (int): The current line number.
          column (int): The current column number.

        Returns:
          tuple: A tuple (new_pos, new_line, new_column) after skipping whitespace.
        """
        ws_match = self.defs.token_patterns["WHITESPACE"].match(source, pos)
        if ws_match:
            ws_text = ws_match.group()
            self.logger.debug(f"Skipping whitespace: '{ws_text}' at line {line}, column {column}.")
            # Update line count by counting the number of newline characters in the whitespace.
            line += ws_text.count("\n")
            # If there was a newline, update column to the length of the last line plus one.
            if "\n" in ws_text:
                column = len(ws_text.split("\n")[-1]) + 1
            else:
                column += len(ws_text)
            pos = ws_match.end()
        return pos, line, column

    def _skip_comment(self, source: str, pos: int, line: int, column: int):
        """
        Skip over comments in the source code.
        In Ada, a comment starts with '--' and goes until the end of the line.

        Parameters:
          source (str): The full source code.
          pos (int): The current position in the source code.
          line (int): The current line number.
          column (int): The current column number.

        Returns:
          tuple: A tuple (new_pos, new_line, new_column) after skipping the comment.
        """
        comment_match = self.defs.token_patterns["COMMENT"].match(source, pos)
        if comment_match:
            comment_text = comment_match.group()
            self.logger.debug(f"Skipping comment: '{comment_text.strip()}' at line {line}, column {column}.")
            line += comment_text.count("\n")
            if "\n" in comment_text:
                column = len(comment_text.split("\n")[-1]) + 1
            else:
                column += len(comment_text)
            pos = comment_match.end()
        return pos, line, column

    def _match_token(self, source: str, pos: int, line: int, column: int):
        """
        Attempt to match a token starting at the given position.
        Iterates through all token patterns (except whitespace and comments) and returns
        the first token it finds along with updated position, line, and column information.
        If a token is matched but should be skipped (e.g. an identifier that is too long
        or an unterminated string literal), it returns a special SKIP flag.

        Parameters:
          source (str): The full source code.
          pos (int): The current position in the source code.
          line (int): The current line number.
          column (int): The current column number.

        Returns:
          tuple: (token, new_pos, new_line, new_column)
                 - token: A Token object, or LexicalAnalyzer.SKIP if the token should be skipped, or None if no match.
        """
        self.logger.debug(f"Attempting to match a token at pos {pos} (line {line}, column {column}).")
        # Go through each token pattern defined in our Definitions.
        for token_name, pattern in self.defs.token_patterns.items():
            if token_name in ["WHITESPACE", "COMMENT"]:
                continue

            # SPECIAL CASE: For string literals, do an extra check for termination.
            if token_name == "LITERAL":
                # If the current character is a double quote, check for the next double quote on the same line.
                if source[pos] == '"':
                    next_quote = source.find('"', pos + 1)
                    newline_pos = source.find('\n', pos)
                    # If no closing quote is found on this line, then it's unterminated.
                    if next_quote == -1 or (newline_pos != -1 and next_quote > newline_pos):
                        error_msg = f"Unterminated string literal starting at line {line}, column {column}."
                        self.logger.error(error_msg)
                        self.errors.append(error_msg)
                        # Advance to the end of the line (or end-of-input) so we skip the whole unterminated literal.
                        if newline_pos == -1:
                            new_pos = len(source)
                            new_line = line
                            new_column = column + (len(source) - pos)
                        else:
                            new_pos = newline_pos
                            new_line = line + 1
                            new_column = 1
                        return LexicalAnalyzer.SKIP, new_pos, new_line, new_column

            # Try matching this token pattern.
            match = pattern.match(source, pos)
            if match:
                lexeme = match.group()
                self.logger.debug(f"Pattern '{token_name}' matched lexeme '{lexeme}' at line {line}, column {column}.")
                token_type = None
                value = None
                literal_value = None

                if token_name == "ID":
                    token_type = self._process_identifier(lexeme, line, column)
                    if token_type is None:
                        self.logger.debug(f"Skipping identifier '{lexeme}' (exceeds length limit).")
                        new_line = line + lexeme.count("\n")
                        new_column = (len(lexeme.split("\n")[-1]) + 1) if "\n" in lexeme else column + len(lexeme)
                        new_pos = match.end()
                        return LexicalAnalyzer.SKIP, new_pos, new_line, new_column
                elif token_name == "NUM":
                    token_type, value = self._process_num(lexeme, line, column)
                elif token_name == "REAL":
                    token_type, value = self._process_real(lexeme, line, column)
                elif token_name == "LITERAL":
                    token_type, literal_value = self._process_literal(lexeme, line, column)
                    if token_type is None:
                        # Should not happen now because we check above—but just in case.
                        self.logger.debug(f"Skipping unterminated literal '{lexeme}'.")
                        new_line = line + lexeme.count("\n")
                        new_column = (len(lexeme.split("\n")[-1]) + 1) if "\n" in lexeme else column + len(lexeme)
                        new_pos = match.end()
                        return LexicalAnalyzer.SKIP, new_pos, new_line, new_column
                elif token_name == "CHAR_LITERAL":
                    token_type, literal_value = self._process_char_literal(lexeme, line, column)
                elif token_name == "CONCAT":
                    token_type = self.defs.TokenType.CONCAT
                else:
                    token_type = getattr(self.defs.TokenType, token_name, None)
                    self.logger.debug(f"Assigned token type '{token_type}' for operator/punctuation '{lexeme}'.")

                # Create the token.
                token = Token(
                    token_type=token_type,
                    lexeme=lexeme,
                    line_number=line,
                    column_number=column,
                    value=value,
                    literal_value=literal_value
                )

                # Update our position info.
                new_line = line + lexeme.count("\n")
                new_column = (len(lexeme.split("\n")[-1]) + 1) if "\n" in lexeme else column + len(lexeme)
                new_pos = match.end()
                self.logger.debug(f"Token '{lexeme}' processed. New pos {new_pos}, line {new_line}, column {new_column}.")
                return token, new_pos, new_line, new_column

        self.logger.debug(f"No matching token found at pos {pos} (line {line}, column {column}).")
        return None, pos, line, column



    def _process_identifier(self, lexeme: str, line: int, column: int):
        """
        Process an identifier token.
        If the identifier is a reserved word, return its reserved token type.
        Otherwise, if the identifier's length is more than 17 characters,
        log an error and return None (so that this token will be skipped).
        If the identifier is valid, return the generic ID token type.

        Parameters:
          lexeme (str): The matched identifier text.
          line (int): The current line number.
          column (int): The current column number.

        Returns:
          Token type for the identifier, or None if it should be skipped.
        """
        self.logger.debug(f"Processing identifier: '{lexeme}' at line {line}, column {column}.")
        if self.defs.is_reserved(lexeme):
            reserved_type = self.defs.get_reserved_token(lexeme)
            self.logger.debug(f"Identifier '{lexeme}' is reserved; token type set to {reserved_type}.")
            return reserved_type
        else:
            if len(lexeme) > 17:
                error_msg = f"Identifier '{lexeme}' exceeds maximum length at line {line}, column {column}."
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                # Return None to indicate that this token should be skipped.
                return None
            return self.defs.TokenType.ID

    def _process_num(self, lexeme: str, line: int, column: int):
        """
        Process a numeric token (an integer).

        Parameters:
          lexeme (str): The numeric string.
          line (int): Current line number.
          column (int): Current column number.

        Returns:
          A tuple (TokenType, value) where value is the integer value.
        """
        self.logger.debug(f"Processing number: '{lexeme}' at line {line}, column {column}.")
        token_type = self.defs.TokenType.NUM
        try:
            value = int(lexeme)
        except ValueError:
            error_msg = f"Invalid number '{lexeme}' at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            value = None
        return token_type, value

    def _process_real(self, lexeme: str, line: int, column: int):
        """
        Process a real number (floating-point).

        Parameters:
          lexeme (str): The numeric string containing a decimal.
          line (int): Current line number.
          column (int): Current column number.

        Returns:
          A tuple (TokenType, value) where value is the float value.
        """
        self.logger.debug(f"Processing real number: '{lexeme}' at line {line}, column {column}.")
        token_type = self.defs.TokenType.REAL
        try:
            value = float(lexeme)
        except ValueError:
            error_msg = f"Invalid real number '{lexeme}' at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            value = None
        return token_type, value

    def _process_literal(self, lexeme: str, line: int, column: int):
        """
        Process a string literal token.
        The lexeme should start and end with a double quote.
        If it doesn't end with a double quote, log an error and signal to skip the token.
        Otherwise, it replaces doubled double quotes with a single quote.

        Parameters:
          lexeme (str): The matched string literal (including the quotes).
          line (int): Current line number.
          column (int): Current column number.

        Returns:
          A tuple (TokenType, literal_value) where literal_value is the inner string.
          Returns (None, None) if the literal is unterminated.
        """
        token_type = self.defs.TokenType.LITERAL
        self.logger.debug(f"Processing string literal: {lexeme} at line {line}, column {column}.")
        # Check if the literal ends with a double quote.
        if not lexeme.endswith('"'):
            error_msg = f"Unterminated string literal starting at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            # Signal that this token is invalid by returning None.
            return None, None
        else:
            inner_text = lexeme[1:-1]
            # Replace any doubled double quotes with a single quote.
            literal_value = inner_text.replace('""', '"')
        self.logger.debug(f"Extracted string literal value: '{literal_value}' from lexeme {lexeme}.")
        return token_type, literal_value

    def _process_char_literal(self, lexeme: str, line: int, column: int):
        """
        Process a character literal token.
        The lexeme should start and end with a single quote.
        If it doesn't end properly, log an error.
        It replaces any doubled single quotes with a single quote.

        Parameters:
          lexeme (str): The matched character literal (including the quotes).
          line (int): Current line number.
          column (int): Current column number.

        Returns:
          A tuple (TokenType, literal_value) where literal_value is the character.
        """
        token_type = self.defs.TokenType.CHAR_LITERAL
        self.logger.debug(f"Processing character literal: {lexeme} at line {line}, column {column}.")
        if not lexeme.endswith("'"):
            error_msg = f"Unterminated character literal starting at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            literal_value = lexeme[1:]
        else:
            inner_text = lexeme[1:-1]
            # Replace doubled single quotes with a single quote.
            literal_value = inner_text.replace("''", "'")
        self.logger.debug(f"Extracted character literal value: '{literal_value}' from lexeme {lexeme}.")
        return token_type, literal_value

###############################################################################
# Full Documentation for LexicalAnalyzer Class
###############################################################################
"""
Class: LexicalAnalyzer
----------------------
This class implements a lexical analyzer for a subset of the Ada programming language.
It reads in source code (as a string) and processes it to produce a list of tokens. 
Each token represents a meaningful component of the language such as an identifier,
number, keyword, operator, or literal.

Key Features:
  - Uses regular expressions (defined in the Definitions class) to match tokens.
  - Skips over whitespace and comments automatically.
  - Checks identifiers against reserved words.
  - Enforces a maximum identifier length of 17 characters. If an identifier exceeds 
    this limit, it is logged as an error and skipped (i.e., it is not added to the token list).
  - Processes numeric tokens (both integers and real numbers).
  - Processes string and character literals, handling escaped quotes.
  - Logs detailed debug information for each step, which is helpful for beginners to
    understand how the analyzer works.
  - Configurable error handling: it can either stop on error or log the error and continue.

Usage:
  1. Create an instance of LexicalAnalyzer:
         lexer = LexicalAnalyzer(stop_on_error=False)
  2. Call the analyze() method with the source code as input:
         tokens = lexer.analyze(source_code)
  3. The returned list of tokens can be used by a parser for further processing.
  
This implementation is designed to be easy to understand and extend. The inline comments
explain what each block of code is doing, making it suitable for a college student or a
Python beginner to learn from and modify as needed.
"""

# End of LexicalAnalyzer.py
