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


class LexicalAnalyzer:
    def __init__(self, stop_on_error=False):
        self.defs = Definitions()
        self.stop_on_error = stop_on_error  # Change behavior based on this flag.
        self.errors = []  # Collect errors to be reported later.

    def analyze(self, source_code: str):
        tokens = []
        pos = 0
        line = 1
        column = 1

        while pos < len(source_code):
            # Skip whitespace
            ws_match = self.defs.token_patterns["WHITESPACE"].match(source_code, pos)
            if ws_match:
                ws_text = ws_match.group()
                # Update line and column numbers accordingly.
                line += ws_text.count("\n")
                if "\n" in ws_text:
                    column = len(ws_text.split("\n")[-1]) + 1
                else:
                    column += len(ws_text)
                pos = ws_match.end()
                continue

            # Skip comments
            comment_match = self.defs.token_patterns["COMMENT"].match(source_code, pos)
            if comment_match:
                pos = comment_match.end()
                # Assume comment is one line so set column appropriately
                column = 1
                line += 1
                continue

            # Attempt to match tokens in order of priority.
            token_found = False
            for token_name, pattern in self.defs.token_patterns.items():
                match = pattern.match(source_code, pos)
                if match:
                    lexeme = match.group()
                    token_type = None

                    # Identify token type based on token_name.
                    if token_name == "ID":
                        # Check if the lexeme is a reserved word.
                        if self.defs.is_reserved(lexeme):
                            token_type = self.defs.get_reserved_token(lexeme)
                        else:
                            if len(lexeme) > 17:
                                error_msg = f"Identifier '{lexeme}' exceeds maximum length at line {line}, column {column}."
                                logging.error(error_msg)
                                self.errors.append(error_msg)
                                if self.stop_on_error:
                                    raise Exception(error_msg)
                            token_type = self.defs.TokenType.ID

                    elif token_name == "NUM":
                        token_type = self.defs.TokenType.NUM
                        try:
                            value = int(lexeme)
                        except ValueError:
                            value = None
                            error_msg = f"Invalid number '{lexeme}' at line {line}, column {column}."
                            logging.error(error_msg)
                            self.errors.append(error_msg)
                            if self.stop_on_error:
                                raise Exception(error_msg)
                    elif token_name == "REAL":
                        token_type = self.defs.TokenType.REAL
                        try:
                            value = float(lexeme)
                        except ValueError:
                            value = None
                            error_msg = f"Invalid real number '{lexeme}' at line {line}, column {column}."
                            logging.error(error_msg)
                            self.errors.append(error_msg)
                            if self.stop_on_error:
                                raise Exception(error_msg)
                    elif token_name == "LITERAL":
                        token_type = self.defs.TokenType.LITERAL
                        # Remove the enclosing quotes
                        literal_value = lexeme[1:-1]
                    else:
                        # For operators and punctuation, determine token type.
                        token_type = getattr(self.defs.TokenType, token_name, None)

                    # Create token. (Adjust attribute assignments as needed)
                    token = Token(
                        token_type=token_type,
                        lexeme=lexeme,
                        line_number=line,
                        column_number=column,
                        value=locals().get('value', None),
                        literal_value=locals().get('literal_value', None)
                    )
                    tokens.append(token)
                    token_found = True

                    # Update position and column
                    pos = match.end()
                    column += len(lexeme)
                    break

            if not token_found:
                # Unrecognized character encountered.
                error_msg = f"Unrecognized character '{source_code[pos]}' at line {line}, column {column}."
                logging.error(error_msg)
                self.errors.append(error_msg)
                pos += 1
                column += 1

        # Append EOF token at the end.
        eof_token = Token(
            token_type=self.defs.TokenType.EOF,
            lexeme="EOF",
            line_number=line,
            column_number=column
        )
        tokens.append(eof_token)
        return tokens
