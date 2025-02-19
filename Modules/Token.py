# Token.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-01
# Version: 1.0
#
# This module defines the Token class, which represents an individual token generated
# by the lexical analyzer. A token typically contains information such as its type,
# the actual text (lexeme), and the position in the source code (line and column) where it was found.
#
# This code is documented to help beginners understand what each part does.

import os
import sys
from typing import List, Optional
from pathlib import Path

# Set up the repository home path so that we can import modules from the parent directory.
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Logger import Logger

class Token:
    def __init__(self, token_type, lexeme, line_number, column_number,
                 value=None, real_value=None, literal_value=None):
        """
        Initialize a Token instance.

        Parameters:
          token_type: The type of the token (usually from the TokenType enumeration).
          lexeme (str): The actual text matched from the source code.
          line_number (int): The line number in the source code where this token appears.
          column_number (int): The column number in the source code where this token starts.
          value: (Optional) The numeric value if this is an integer token.
          real_value: (Optional) The floating-point value if this is a real number token.
          literal_value: (Optional) The inner text for string or character literals.
        """
        # Create a logger instance to log any issues inside the Token class.
        self.logger = Logger()
        self.token_type = token_type
        self.lexeme = lexeme
        self.line_number = line_number
        self.column_number = column_number
        self.value = value
        self.real_value = real_value
        self.literal_value = literal_value

    def __repr__(self):
        """
        Return an official string representation of the Token.
        
        This is useful for debugging. It shows the token type, lexeme, value,
        and the location (line and column) where it was found.
        """
        try:
            return (f"Token(type={self.token_type}, lexeme='{self.lexeme}', "
                    f"value={self.value}, line={self.line_number}, "
                    f"column={self.column_number})")
        except Exception:
            # If an error occurs during representation, log it and re-raise.
            self.logger.error('Error in Token __repr__: %s', self.__dict__)
            raise

    def __str__(self):
        """
        Return a user-friendly string representation of the Token.
        
        For example: <ID, 'myVariable'>
        """
        # Note: There's a small typo in the attribute name ("self. Lexeme" with a space).
        # It should be "self.lexeme".
        return f"<{self.token_type}, {self.lexeme}>"
