# Definitions

from enum import Enum

class TokenDefinitions:
    def __init__(self):
        # Define token types using Enum for better type safety
        self.TokenType = Enum('TokenType', [
            'PROCEDURE', 'MODULE', 'CONSTANT', 'IS', 'BEGIN', 'END',
            'IF', 'THEN', 'ELSE', 'ELSIF', 'WHILE', 'LOOP', 'FLOAT',
            'INTEGER', 'CHAR', 'GET', 'PUT', 'ID', 'NUM', 'REAL',
            'LITERAL', 'RELOP', 'ADDOP', 'MULOP', 'ASSIGN',
            'LPAREN', 'RPAREN', 'COMMA', 'COLON', 'SEMICOLON',
            'DOT', 'QUOTE', 'EOF'
        ])

        # Reserved words (stored as uppercase for case-insensitive matching)
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

        # Token patterns using regular expressions
        self.token_patterns = {
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

        # Operators and symbols for categorization
        self.operators = {
            "ASSIGN": ":=",
            "RELOP": ["<=", ">=", "/=", "=", "<", ">"],
            "ADDOP": ["+", "-", "or"],
            "MULOP": ["*", "/", "rem", "mod", "and"]
        }

        self.operator_names = {
            "ASSIGN": {
                "AssignTok": ":=",
            },
            "RELOP": {
                "LessThanOrEqualTok": "<=",
                "GreaterThanOrEqualTok": ">=",
                "NotEqualTok": "/=",
                "EqualsSignTok": "=",
                "LessThanTok": "<",
                "GreaterThanTok": ">",
            },
            "ADDOP": {
                "PlusTok": "+",
                "MinusTok": "-",
                "OrTok": "or",
            },
            "MULOP": {
                "MultiplyTok": "*",
                "DivideTok": "/",
                "RemainderTok": "rem",
                "ModuloTok": "mod",
                "AndTok": "and"
            }
        }

        self.symbols = {
            "LPAREN": "(",
            "RPAREN": ")",
            "COMMA": ",",
            "COLON": ":",
            "SEMICOLON": ";",
            "DOT": ".",
            "QUOTE": '"'
        }

    def is_reserved(self, word):
        return word.upper() in self.reserved_words

    def get_reserved_token(self, word):
        return self.reserved_words.get(word.upper(), None)

    def get_token_type(self, token_type_str):
        return getattr(self.TokenType, token_type_str, None)