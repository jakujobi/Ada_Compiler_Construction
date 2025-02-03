# LexicalAnalyzer
# LexicalAnalyzer is a module that provides a lexical analyzer for Ada programs.


import os
import re
import sys
import logging
from typing import List, Optional
from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger

class LexicalAnalyzer:
    def __init__(self, stop_on_error=False):
        self.logger = Logger()
        self.defs = Definitions()
        self.stop_on_error = stop_on_error  # Configurable error handling flag
        self.errors = []  # Collect errors for later reporting

    def analyze(self, source_code: str):
        """Main function to tokenize the given source code."""
        tokens = []
        pos = 0
        line = 1
        column = 1

        self.logger.debug("Starting tokenization of source code.")
        while pos < len(source_code):
            self.logger.debug(f"At position {pos} (line {line}, column {column}).")
            # Skip whitespace and comments.
            pos, line, column = self._skip_whitespace(source_code, pos, line, column)
            pos, line, column = self._skip_comment(source_code, pos, line, column)

            # Try to match a token.
            token, new_pos, new_line, new_column = self._match_token(source_code, pos, line, column)
            if token:
                self.logger.debug(f"Matched token: {token} at line {line}, column {column}.")
                tokens.append(token)
                pos, line, column = new_pos, new_line, new_column
            else:
                # Handle unrecognized characters.
                error_msg = f"Unrecognized character '{source_code[pos]}' at line {line}, column {column}."
                self.logger.error(error_msg)
                self.errors.append(error_msg)
                pos += 1
                column += 1

        # Append an EOF token at the end.
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
        ws_match = self.defs.token_patterns["WHITESPACE"].match(source, pos)
        if ws_match:
            ws_text = ws_match.group()
            self.logger.debug(f"Skipping whitespace: '{ws_text}' at line {line}, column {column}.")
            line += ws_text.count("\n")
            if "\n" in ws_text:
                column = len(ws_text.split("\n")[-1]) + 1
            else:
                column += len(ws_text)
            pos = ws_match.end()
        return pos, line, column

    def _skip_comment(self, source: str, pos: int, line: int, column: int):
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
        self.logger.debug(f"Attempting to match a token at pos {pos} (line {line}, column {column}).")
        for token_name, pattern in self.defs.token_patterns.items():
            if token_name in ["WHITESPACE", "COMMENT"]:
                continue

            match = pattern.match(source, pos)
            if match:
                lexeme = match.group()
                self.logger.debug(f"Pattern '{token_name}' matched lexeme '{lexeme}' at line {line}, column {column}.")
                token_type = None
                value = None
                literal_value = None

                if token_name == "ID":
                    token_type = self._process_identifier(lexeme, line, column)
                elif token_name == "NUM":
                    token_type, value = self._process_num(lexeme, line, column)
                elif token_name == "REAL":
                    token_type, value = self._process_real(lexeme, line, column)
                elif token_name == "LITERAL":
                    token_type, literal_value = self._process_literal(lexeme, line, column)
                elif token_name == "CHAR_LITERAL":
                    token_type, literal_value = self._process_char_literal(lexeme, line, column)
                else:
                    token_type = getattr(self.defs.TokenType, token_name, None)
                    self.logger.debug(f"Assigned token type '{token_type}' for operator/punctuation '{lexeme}'.")

                token = Token(
                    token_type=token_type,
                    lexeme=lexeme,
                    line_number=line,
                    column_number=column,
                    value=value,
                    literal_value=literal_value
                )

                new_line = line + lexeme.count("\n")
                if "\n" in lexeme:
                    new_column = len(lexeme.split("\n")[-1]) + 1
                else:
                    new_column = column + len(lexeme)
                new_pos = match.end()
                self.logger.debug(f"Token '{lexeme}' processed. New pos {new_pos}, line {new_line}, column {new_column}.")
                return token, new_pos, new_line, new_column

        self.logger.debug(f"No matching token found at pos {pos} (line {line}, column {column}).")
        return None, pos, line, column

    def _process_identifier(self, lexeme: str, line: int, column: int):
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
                if self.stop_on_error:
                    raise Exception(error_msg)
            return self.defs.TokenType.ID

    def _process_num(self, lexeme: str, line: int, column: int):
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
        token_type = self.defs.TokenType.LITERAL
        self.logger.debug(f"Processing string literal: {lexeme} at line {line}, column {column}.")
        # Check if the lexeme ends with a double quote.
        if not lexeme.endswith('"'):
            error_msg = f"Unterminated string literal starting at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            literal_value = lexeme[1:]
        else:
            inner_text = lexeme[1:-1]
            # Replace any doubled quotes with a single quote.
            literal_value = inner_text.replace('""', '"')
        self.logger.debug(f"Extracted string literal value: '{literal_value}' from lexeme {lexeme}.")
        return token_type, literal_value

    def _process_char_literal(self, lexeme: str, line: int, column: int):
        token_type = self.defs.TokenType.CHAR_LITERAL
        self.logger.debug(f"Processing character literal: {lexeme} at line {line}, column {column}.")
        # Check if the lexeme ends with a single quote.
        if not lexeme.endswith("'"):
            error_msg = f"Unterminated character literal starting at line {line}, column {column}."
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            if self.stop_on_error:
                raise Exception(error_msg)
            literal_value = lexeme[1:]
        else:
            inner_text = lexeme[1:-1]
            # Replace any doubled single quotes with a single quote.
            literal_value = inner_text.replace("''", "'")
        self.logger.debug(f"Extracted character literal value: '{literal_value}' from lexeme {lexeme}.")
        return token_type, literal_value
