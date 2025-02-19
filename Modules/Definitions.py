# Definitions.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-01
# Version: 1.0
# This module defines the token types and regular expression patterns used by the compiler.
# It provides a Definitions class that stores an enumeration of token types, a mapping for reserved words,
# and a dictionary of regex patterns for matching tokens in the source code.

from enum import Enum
from typing import Dict, Optional
import re

class Definitions:
    """
    Definitions holds all the static definitions used by the compiler, including token types,
    reserved words, and regular expression patterns for matching various tokens.

    Attributes
    ----------
    TokenType : Enum
        An enumeration of all possible token types.
    reserved_words : dict
        A dictionary mapping reserved words (like BEGIN, PROCEDURE, etc.) to their corresponding token types.
    token_patterns : dict
        A dictionary mapping token names (like ID, NUM, LITERAL, etc.) to their compiled regular expression patterns.

    Methods
    -------
    is_reserved(word: str) -> bool
        Checks if a given word is a reserved word.
    get_reserved_token(word: str) -> Optional[Enum]
        Returns the token type for a given reserved word.
    get_token_type(token_type_str: str) -> Optional[Enum]
        Returns the token type from the TokenType enumeration based on the given token type string.
    """
    def __init__(self):
        # Create an enumeration for token types
        self.TokenType = Enum(
            'TokenType', [
                # Existing tokens
                'PROCEDURE', 'MODULE', 'CONSTANT', 'IS', 'BEGIN', 'END',
                'IF', 'THEN', 'ELSE', 'ELSIF', 'WHILE', 'LOOP', 'FLOAT',
                'INTEGER', 'CHAR', 'GET', 'PUT', 'ID', 'NUM', 'REAL',
                'LITERAL', 'CHAR_LITERAL', 'RELOP', 'ADDOP', 'MULOP', 'ASSIGN',
                'LPAREN', 'RPAREN', 'COMMA', 'COLON', 'SEMICOLON',
                'DOT', 'EOF', 'CONCAT', 'IN', 'OUT', 'INOUT',
                # New tokens from Ada 2022
                'ABORT', 'ABS', 'ABSTRACT', 'ACCEPT', 'ACCESS',
                'ALIASED', 'ALL', 'AND', 'ARRAY', 'AT',
                'BODY', 'CASE', 'DECLARE', 'DELAY', 'DELTA',
                'DIGITS', 'DO', 'ENTRY', 'EXCEPTION', 'EXIT',
                'FOR', 'FUNCTION', 'GENERIC', 'GOTO',
                'INTERFACE', 'LIMITED', 'MOD', 'NEW', 'NOT',
                'NULL', 'OF', 'OR', 'OTHERS', 'OVERRIDING',
                'PACKAGE', 'PARALLEL', 'PRAGMA', 'PRIVATE',
                'PROTECTED', 'RAISE', 'RANGE', 'RECORD', 'REM',
                'RENAMES', 'REQUEUE', 'RETURN', 'REVERSE', 'SELECT',
                'SEPARATE', 'SOME', 'SUBTYPE', 'SYNCHRONIZED',
                'TAGGED', 'TASK', 'TERMINATE', 'TYPE', 'UNTIL',
                'USE', 'WHEN', 'WITH', 'XOR',
                # Add required token types for grammar
                'INTEGERT', 'REALT', 'CHART', 'CONST'
            ]
        )

        # Dictionary mapping reserved words
        self.reserved_words = {
            # Existing reserved words
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
            "INTEGER": self.TokenType.INTEGERT,  # Map INTEGER to INTEGERT
            "REAL": self.TokenType.REALT,       # Map REAL to REALT
            "CHAR": self.TokenType.CHART,       # Map CHAR to CHART
            "GET": self.TokenType.GET,
            "PUT": self.TokenType.PUT,
            "END": self.TokenType.END,
            "IN": self.TokenType.IN,
            "OUT": self.TokenType.OUT,
            "INOUT": self.TokenType.INOUT,
            # New reserved words from Ada 2022
            "ABORT": self.TokenType.ABORT,
            "ABS": self.TokenType.ABS,
            "ABSTRACT": self.TokenType.ABSTRACT,
            "ACCEPT": self.TokenType.ACCEPT,
            "ACCESS": self.TokenType.ACCESS,
            "ALIASED": self.TokenType.ALIASED,
            "ALL": self.TokenType.ALL,
            "AND": self.TokenType.AND,
            "ARRAY": self.TokenType.ARRAY,
            "AT": self.TokenType.AT,
            "BODY": self.TokenType.BODY,
            "CASE": self.TokenType.CASE,
            "DECLARE": self.TokenType.DECLARE,
            "DELAY": self.TokenType.DELAY,
            "DELTA": self.TokenType.DELTA,
            "DIGITS": self.TokenType.DIGITS,
            "DO": self.TokenType.DO,
            "ENTRY": self.TokenType.ENTRY,
            "EXCEPTION": self.TokenType.EXCEPTION,
            "EXIT": self.TokenType.EXIT,
            "FOR": self.TokenType.FOR,
            "FUNCTION": self.TokenType.FUNCTION,
            "GENERIC": self.TokenType.GENERIC,
            "GOTO": self.TokenType.GOTO,
            "INTERFACE": self.TokenType.INTERFACE,
            "LIMITED": self.TokenType.LIMITED,
            "MOD": self.TokenType.MOD,
            "NEW": self.TokenType.NEW,
            "NOT": self.TokenType.NOT,
            "NULL": self.TokenType.NULL,
            "OF": self.TokenType.OF,
            "OR": self.TokenType.OR,
            "OTHERS": self.TokenType.OTHERS,
            "OVERRIDING": self.TokenType.OVERRIDING,
            "PACKAGE": self.TokenType.PACKAGE,
            "PARALLEL": self.TokenType.PARALLEL,
            "PRAGMA": self.TokenType.PRAGMA,
            "PRIVATE": self.TokenType.PRIVATE,
            "PROTECTED": self.TokenType.PROTECTED,
            "RAISE": self.TokenType.RAISE,
            "RANGE": self.TokenType.RANGE,
            "RECORD": self.TokenType.RECORD,
            "REM": self.TokenType.REM,
            "RENAMES": self.TokenType.RENAMES,
            "REQUEUE": self.TokenType.REQUEUE,
            "RETURN": self.TokenType.RETURN,
            "REVERSE": self.TokenType.REVERSE,
            "SELECT": self.TokenType.SELECT,
            "SEPARATE": self.TokenType.SEPARATE,
            "SOME": self.TokenType.SOME,
            "SUBTYPE": self.TokenType.SUBTYPE,
            "SYNCHRONIZED": self.TokenType.SYNCHRONIZED,
            "TAGGED": self.TokenType.TAGGED,
            "TASK": self.TokenType.TASK,
            "TERMINATE": self.TokenType.TERMINATE,
            "TYPE": self.TokenType.TYPE,
            "UNTIL": self.TokenType.UNTIL,
            "USE": self.TokenType.USE,
            "WHEN": self.TokenType.WHEN,
            "WITH": self.TokenType.WITH,
            "XOR": self.TokenType.XOR
        }

        # The token_patterns dictionary holds compiled regular expressions for each token type.
        # Note: The order of patterns is important. For example, the patterns for LITERAL and CHAR_LITERAL
        # must come before any pattern that might match a single quote.
        self.token_patterns: Dict[str, re.Pattern] = {
            # COMMENT: Matches a comment in Ada which starts with '--' and continues to the end of the line.
            # The pattern is simple: '--' followed by any characters until the end of the line.
            "COMMENT": re.compile(r"--.*"),
            
            # WHITESPACE: Matches one or more whitespace characters including space, tab, carriage return, and newline.
            "WHITESPACE": re.compile(r"[ \t\r\s\n]+"),
            #"WHITESPACE": re.compile(r"[ \t\r\n]+"),
            # "WHITESPACE": re.compile(r"\s+"),

            
            # CONCAT: Matches the ampersand character '&', used in Ada for string concatenation.
            "CONCAT": re.compile(r"\&"),
            
            # LITERAL (String Literal):
            # Matches a string literal that starts with a double quote ("),
            # then allows any sequence of characters that are either not a double quote or are a pair of double quotes (escaped quote),
            # and then either ends with a double quote or reaches end-of-input.
            # Think of it as a state machine: you enter a "string" state when you see a ", then you loop over valid characters,
            # and exit when you see a " that is not doubled.
            "LITERAL": re.compile(r'"(?:[^"\n]|"")*(?:"|$)'),
            
            # CHAR_LITERAL (Character Literal):
            # Matches a character literal that starts with a single quote ('),
            # then matches exactly one character (or an escaped single quote represented as two single quotes),
            # and then ends with a single quote or reaches end-of-input.
            # The inner part ensures that you only have one character (with the possibility of an escape).
            "CHAR_LITERAL": re.compile(r"'(?:[^'\n]|'')(?:"+"'|$)"),
            
            # REAL: Matches a real (floating-point) number.
            # It looks for one or more digits, followed by a literal period, and then one or more digits.
            # (This is a simplified version and does not handle exponents.)
            "REAL": re.compile(r"\d+\.\d+"),
            
            # NUM: Matches an integer (one or more digits).
            "NUM": re.compile(r"\d+"),
            
            # ID: Matches an identifier.
            # In Ada, an identifier must start with a letter, followed by any number of letters, digits, or underscores.
            # Note: We no longer limit the match length in the regex; instead, the length is checked in the token processor.
            "ID": re.compile(r"[a-zA-Z][a-zA-Z0-9_]*"),
            
            # ASSIGN: Matches the assignment operator, which in Ada is ':='.
            "ASSIGN": re.compile(r":="),
            
            # RELOP: Matches relational operators. This includes <=, >=, /=, =, <, >.
            "RELOP": re.compile(r"<=|>=|/=|=|<|>"),
            
            # ADDOP: Matches additive operators. This includes +, -, and the keyword 'or' (with word boundaries).
            "ADDOP": re.compile(r"\+|-|\bor\b"),
            
            # MULOP: Matches multiplicative operators. This includes *, /, and the keywords 'rem', 'mod', and 'and'
            # (with word boundaries).
            "MULOP": re.compile(r"\*|/|\brem\b|\bmod\b|\band\b"),
            
            # LPAREN: Matches the left parenthesis '('.
            "LPAREN": re.compile(r"\("),
            
            # RPAREN: Matches the right parenthesis ')'.
            "RPAREN": re.compile(r"\)"),
            
            # COMMA: Matches a comma.
            "COMMA": re.compile(r","),
            
            # COLON: Matches a colon.
            "COLON": re.compile(r":"),
            
            # SEMICOLON: Matches a semicolon.
            "SEMICOLON": re.compile(r";"),
            
            # DOT: Matches a period.
            "DOT": re.compile(r"\.")
            # Note: If needed, you can add a separate QUOTE token here, but it's not necessary
            # because LITERAL handles the double quotes.
        }

    def is_reserved(self, word: str) -> bool:
        """
        Check if a given word is a reserved word in Ada.

        Parameters
        ----------
        word : str
            The word to check.

        Returns
        -------
        bool
            True if the word (in uppercase) is in the reserved words dictionary, False otherwise.
        """
        return word.upper() in self.reserved_words

    def get_reserved_token(self, word: str) -> Optional[Enum]:
        """
        Retrieve the token type for a reserved word.

        Parameters
        ----------
        word : str
            The word to look up in the reserved words dictionary.

        Returns
        -------
        Optional[Enum]
            The corresponding token type from the reserved words dictionary if the word is reserved;
            otherwise, None.
        """
        return self.reserved_words.get(word.upper(), None)

    def get_token_type(self, token_type_str: str) -> Optional[Enum]:
        """
        Retrieve the token type from the TokenType enumeration based on a given string.

        Parameters
        ----------
        token_type_str : str
            The string representation of the token type.

        Returns
        -------
        Optional[Enum]
            The corresponding token type from the TokenType enumeration if it exists; otherwise, None.
        """
        return getattr(self.TokenType, token_type_str, None)

###############################################################################
# Full Documentation for Definitions Class
###############################################################################
"""
Class: Definitions
------------------
The Definitions class serves as a central repository for all the static information
needed by the compiler's lexical analyzer. This includes:

1. **TokenType Enumeration:**
   An Enum that lists all possible types of tokens (keywords, identifiers, operators, literals, etc.).

2. **Reserved Words:**
   A dictionary that maps reserved keywords (like BEGIN, PROCEDURE, etc.) to their corresponding token types.
   These are case-insensitive.

3. **Regular Expression Patterns:**
   A dictionary mapping token names to their compiled regex patterns. Each pattern is carefully designed to
   match specific lexical constructs:
      - **COMMENT:** Matches Ada comments, which start with "--" and continue until the end of the line.
      - **WHITESPACE:** Matches spaces, tabs, carriage returns, and newlines.
      - **CONCAT:** Matches the '&' character used for string concatenation.
      - **LITERAL:** Matches string literals enclosed in double quotes. It supports escaped quotes by allowing
        two consecutive double quotes ("").
      - **CHAR_LITERAL:** Matches character literals enclosed in single quotes, allowing for a doubled single quote as an escape.
      - **REAL:** Matches floating-point numbers with a decimal point.
      - **NUM:** Matches integer numbers (one or more digits).
      - **ID:** Matches identifiers that start with a letter, followed by any number of letters, digits, or underscores.
               (Length is later checked in the lexer.)
      - **ASSIGN:** Matches the assignment operator ":=".
      - **RELOP:** Matches relational operators (<=, >=, /=, =, <, >).
      - **ADDOP:** Matches additive operators (+, -, and the word "or").
      - **MULOP:** Matches multiplicative operators (*, /, "rem", "mod", and "and").
      - **LPAREN & RPAREN:** Match the left and right parentheses.
      - **COMMA, COLON, SEMICOLON, DOT:** Match the corresponding punctuation characters.

Usage:
  Create an instance of Definitions and use its attributes and methods to access token types,
  reserved words, and patterns when building your lexical analyzer.

This class is designed to centralize all language definitions in one place, making it easier
to update or extend the language rules.
"""

# End of Definitions.py
