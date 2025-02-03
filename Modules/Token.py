# Token.py


import os
import sys
from typing import List, Optional

from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Logger import Logger



class Token:
    def __init__(self, token_type, lexeme, line_number, column_number,
                 value=None, real_value=None, literal_value=None):
        self.logger = Logger()
        self.token_type = token_type
        self.lexeme = lexeme
        self.line_number = line_number
        self.column_number = column_number
        self.value = value
        self.real_value = real_value
        self.literal_value = literal_value

    def __repr__(self):
        try:
            return (f"Token(type={self.token_type}, lexeme='{self.lexeme}', "
                    f"value={self.value}, line={self.line_number}, "
                    f"column={self.column_number})")
        except Exception:
            self.logger.error('Error in Token __repr__: %s', self.__dict__)
            raise

    def __str__(self):
        return f"<{self.token_type.value}, '{self.lexeme}'>"
