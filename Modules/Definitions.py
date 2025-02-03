# Definitions.py

from enum import Enum
from typing import Dict, Optional
import re

class Definitions:
    """
    A class used to define token types and patterns for a compiler.

    Attributes
    ----------
    TokenType : Enum
        An enumeration of all possible token types.
    reserved_words : dict
        A dictionary mapping reserved words to their corresponding token types.
    token_patterns : dict
        A dictionary mapping token names to their corresponding regular expression patterns.

    Methods
    -------
    is_reserved(word: str) -> bool
        Checks if a given word is a reserved word.
    get_reserved_token(word: str) -> Optional[Enum]
        Returns the token type for a given reserved word.
    get_token_type(token_type_str: str) -> Optional[Enum]
        Returns the token type for a given token type string.
    """
    def __init__(self):
        self.TokenType = Enum('TokenType', [
            'PROCEDURE', 'MODULE', 'CONSTANT', 'IS', 'BEGIN', 'END',
            'IF', 'THEN', 'ELSE', 'ELSIF', 'WHILE', 'LOOP', 'FLOAT',
            'INTEGER', 'CHAR', 'GET', 'PUT', 'ID', 'NUM', 'REAL',
            'LITERAL', 'CHAR_LITERAL', 'RELOP', 'ADDOP', 'MULOP', 'ASSIGN',
            'LPAREN', 'RPAREN', 'COMMA', 'COLON', 'SEMICOLON',
            'DOT', 'EOF'
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

        # Reorder patterns so that LITERAL and CHAR_LITERAL are checked before QUOTE.
        self.token_patterns: Dict[str, re.Pattern] = {
            "COMMENT": re.compile(r"--.*"),
            "WHITESPACE": re.compile(r"[ \t\r\n]+"),
            # String literal: a starting ", then any sequence of (non-" or doubled ") until a closing " (or end-of-input)
            "LITERAL": re.compile(r'"(?:[^"\n]|"")*(?:"|$)'),
            # Character literal: a starting ', then one character (or doubled ') then a closing ' (or end-of-input)
            "CHAR_LITERAL": re.compile(r"'(?:[^'\n]|'')(?:"+"'|$)"),
            "REAL": re.compile(r"\d+\.\d+"),
            "NUM": re.compile(r"\d+"),
            "ID": re.compile(r"[a-zA-Z][a-zA-Z0-9_]{0,16}"),
            "ASSIGN": re.compile(r":="),
            "RELOP": re.compile(r"<=|>=|/=|=|<|>"),
            "ADDOP": re.compile(r"\+|-|\bor\b"),
            "MULOP": re.compile(r"\*|/|\brem\b|\bmod\b|\band\b"),
            "LPAREN": re.compile(r"\("),
            "RPAREN": re.compile(r"\)"),
            "COMMA": re.compile(r","),
            "COLON": re.compile(r":"),
            "SEMICOLON": re.compile(r";"),
            "DOT": re.compile(r"\.")
            # Note: If you need a separate QUOTE token, you can add it here *after* LITERAL.
        }

    def is_reserved(self, word: str) -> bool:
        """
        Check if a given word is a reserved word.

        Args:
            word (str): The word to check.

        Returns:
            bool: True if the word is a reserved word, False otherwise.
        """
        return word.upper() in self.reserved_words

    def get_reserved_token(self, word: str) -> Optional[Enum]:
        """
        Retrieve the reserved token for a given word.

        Args:
            word (str): The word to look up in the reserved words dictionary.

        Returns:
            Optional[Enum]: The corresponding reserved token if the word is found,
                            otherwise None.
        """
        return self.reserved_words.get(word.upper(), None)

    def get_token_type(self, token_type_str: str) -> Optional[Enum]:
        """
        Retrieves the token type from the TokenType enumeration based on the provided token type string.

        Args:
            token_type_str (str): The string representation of the token type.

        Returns:
            Optional[Enum]: The corresponding token type from the TokenType enumeration if it exists, otherwise None.
        """
        return getattr(self.TokenType, token_type_str, None)
