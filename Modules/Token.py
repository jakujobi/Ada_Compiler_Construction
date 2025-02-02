# Token.py


import os
import sys
import logging
from typing import List, Optional

from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

#from Modules.



class Token:
    """
    Represents a token with metadata including its type, lexeme, location,
    and any associated values such as number or literal.
    """
    def __init__(
            self,
            token_type,
            lexeme,
            line_number,
            column_number,
            value=None,
            real_value=None,
            literal_value=None
        ):
        self.token_type = token_type  # Instance of Definitions.TokenType
        self.lexeme = lexeme
        self.line_number = line_number
        self.column_number = column_number
        self.value = value          # For numeric tokens
        self.real_value = real_value  # For real (floating) tokens
        self.literal_value = literal_value  # For string literal tokens

    def __repr__(self):
        try:
            return (
                f"Token(type={self.token_type}, "
                f"lexeme='{self.lexeme}', "
                f"value={self.value}, "
                f"line={self.line_number}, "
                f"column={self.column_number})"
            )
        except Exception:
            logging.error('Error in Token __repr__: %s', self.__dict__)
            raise

    def __str__(self):
        return f"<{self.token_type.value}, '{self.lexeme}'>"