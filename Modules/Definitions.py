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


class Definitions:
    def __init__(self):
        """Initialize token definitions."""
        self.TokenType = Enum('TokenType', [
            'PROCEDURE', 'MODULE', 'CONSTANT', 'IS', 'BEGIN', 'END',
            'IF', 'THEN', 'ELSE', 'ELSIF', 'WHILE', 'LOOP', 'FLOAT',
            'INTEGER', 'CHAR', 'GET', 'PUT', 'ID', 'NUM', 'REAL',
            'LITERAL', 'RELOP', 'ADDOP', 'MULOP', 'ASSIGN',
            'LPAREN', 'RPAREN', 'COMMA', 'COLON', 'SEMICOLON',
            'DOT', 'QUOTE', 'EOF'
        ])

        self.reserved_words = self._initialize_reserved_words()
        self.token_patterns = self._initialize_token_patterns()
        self.operators = self._initialize_operators()
        self.operator_names = self._initialize_operator_names()
        self.symbols = self._initialize_symbols()

    def _initialize_reserved_words(self) -> Dict[str, Enum]:
        """Initialize reserved words."""
        return {
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

    def _initialize_token_patterns(self) -> Dict[str, str]:
        """Initialize token patterns using regular expressions."""
        return {
            "ASSIGN": r":=",
            "RELOP": r"<=|>=|/=|=|<|>",
            "ADDOP": r"\+|-|\bor\b",
            "MULOP": r"\*|/|\brem\b|\bmod\b|\band\b",
            "LPAREN": r"\(",
            "RPAREN": r"\)",
            "COMMA": r",",
            "COLON": r":",
            "SEMICOLON": r";",
            "DOT": r"\.",
            "QUOTE": r'"',
            "COMMENT": r"--.*",
            "WHITESPACE": r"[ \t\r\n]+",
            "LITERAL": r'"[^"\n]*"',
            "REAL": r"\d+\.\d+",
            "NUM": r"\d+",
            "ID": r"[a-zA-Z_][a-zA-Z0-9_]{0,16}"
        }

    def _initialize_operators(self) -> Dict[str, str]:
        """Initialize operators and their symbols."""
        return {
            "AssignTok": ":=",
            "LessThanOrEqualTok": "<=",
            "GreaterThanOrEqualTok": ">=",
            "NotEqualTok": "/=",
            "EqualsSignTok": "=",
            "LessThanTok": "<",
            "GreaterThanTok": ">",
            "PlusTok": "+",
            "MinusTok": "-",
            "OrTok": "or",
            "MultiplyTok": "*",
            "DivideTok": "/",
            "RemainderTok": "rem",
            "ModuloTok": "mod",
            "AndTok": "and"
        }

    def _initialize_operator_names(self) -> Dict[str, str]:
        """Initialize operator names and their corresponding tokens."""
        return {
            ":=": "AssignTok",
            "<=": "LessThanOrEqualTok",
            ">=": "GreaterThanOrEqualTok",
            "/=": "NotEqualTok",
            "=": "EqualsSignTok",
            "<": "LessThanTok",
            ">": "GreaterThanTok",
            "+": "PlusTok",
            "-": "MinusTok",
            "or": "OrTok",
            "*": "MultiplyTok",
            "/": "DivideTok",
            "rem": "RemainderTok",
            "mod": "ModuloTok",
            "and": "AndTok"
        }

    def _initialize_symbols(self) -> Dict[str, str]:
        """Initialize symbols."""
        return {
            "LPAREN": "(",
            "RPAREN": ")",
            "COMMA": ",",
            "COLON": ":",
            "SEMICOLON": ";",
            "DOT": ".",
            "QUOTE": '"'
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