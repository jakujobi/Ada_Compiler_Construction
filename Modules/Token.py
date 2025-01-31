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
    def __init__(self, type, lexeme, line_number, column_number, value=None):
        self.type = type  # Instance of Definitions.TokenType
        self.lexeme = lexeme
        self.line_number = line_number
        self.column_number = column_number
        self.value = value  # For NUM, REAL, LITERAL tokens

    def __repr__(self):
        try:
            return f"Token(type={self.type}, lexeme='{self.lexeme}', value={self.value}, line={self.line_number}, column={self.column_number})"
        except:
            logging.error('%s raised an exception', self)
