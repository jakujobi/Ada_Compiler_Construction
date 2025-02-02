# Definitions

from enum import Enum
from typing import Dict, Optional
# import re
# import logging


"""_summary_
Definitions Module

Responsibility: Define constants, reserved words, token regular expressions, and other static data.
Features:
Data structure (e.g., dictionary or list) for reserved words.
Regular expressions for identifiers, numbers, string literals, and operators.

"""


from enum import Enum
import re

class Definitions:
    def __init__(self):
        self.TokenType = Enum('TokenType', [
            'PROCEDURE', 'MODULE', 'CONSTANT', 'IS', 'BEGIN', 'END',
            'IF', 'THEN', 'ELSE', 'ELSIF', 'WHILE', 'LOOP', 'FLOAT',
            'INTEGER', 'CHAR', 'GET', 'PUT', 'ID', 'NUM', 'REAL',
            'LITERAL', 'RELOP', 'ADDOP', 'MULOP', 'ASSIGN',
            'LPAREN', 'RPAREN', 'COMMA', 'COLON', 'SEMICOLON',
            'DOT', 'QUOTE', 'EOF'
        ])

        self.reserved_words = {
            "BEGIN": self.TokenType.BEGIN,
            "MODULE": self.TokenType.MODULE,
            "CONSTANT": self.TokenType.CONSTANT,
            "PROCEDURE": self.TokenType.PROCEDURE,
            "IS": self.TokenType.IS,
            "IF": self.TokenType.IF,
            "THEN": self.TokenType.THEN,
            "ELSE": self.TokenType.ELSE,
            "ELSIF": self.TokenType.ELSIF,
            "WHILE": self.TokenType.WHILE,
            "LOOP": self.TokenType.LOOP,
            "FLOAT": self.TokenType.FLOAT,
            "INTEGER": self.TokenType.INTEGER,
            "CHAR": self.TokenType.CHAR,
            "GET": self.TokenType.GET,
            "PUT": self.TokenType.PUT,
            "END": self.TokenType.END
        }

        # Pre-compile the patterns for better performance.
        self.token_patterns = {
            "ASSIGN": re.compile(r":="),
            "RELOP": re.compile(r"<=|>=|/=|=|<|>"),
            "ADDOP": re.compile(r"\+|-|\bor\b"),
            "MULOP": re.compile(r"\*|/|\brem\b|\bmod\b|\band\b"),
            "LPAREN": re.compile(r"\("),
            "RPAREN": re.compile(r"\)"),
            "COMMA": re.compile(r","),
            "COLON": re.compile(r":"),
            "SEMICOLON": re.compile(r";"),
            "DOT": re.compile(r"\."),
            "QUOTE": re.compile(r'"'),
            "COMMENT": re.compile(r"--.*"),
            "WHITESPACE": re.compile(r"[ \t\r\n]+"),
            "LITERAL": re.compile(r'"[^"\n]*"'),
            "REAL": re.compile(r"\d+\.\d+"),
            "NUM": re.compile(r"\d+"),
            "ID": re.compile(r"[a-zA-Z][a-zA-Z0-9_]{0,16}")
        }


    def is_reserved(self, word: str) -> bool:
        """Check if a word is a reserved word."""
        return word.upper() in self.reserved_words

    def get_reserved_token(self, word: str) -> Optional[Enum]:
        """Get the token type for a reserved word."""
        return self.reserved_words.get(word.upper(), None)

    def get_token_type(self, token_type_str: str) -> Optional[Enum]:
        """Get the token type from a string."""
        return getattr(self.TokenType, token_type_str, None)