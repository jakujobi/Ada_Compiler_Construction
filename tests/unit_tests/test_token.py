import unittest
import sys
import os
from pathlib import Path

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Updated import paths
from jakadac.modules.Token import Token
from jakadac.modules.Definitions import Definitions

class TestToken(unittest.TestCase):
    def setUp(self):
        self.defs = Definitions()
        
    def test_token_creation_with_basic_attributes(self):
        token = Token(self.defs.TokenType.ID, "test", 1, 1)
        self.assertEqual(token.token_type, self.defs.TokenType.ID)
        self.assertEqual(token.lexeme, "test")
        self.assertEqual(token.line_number, 1)
        self.assertEqual(token.column_number, 1)
        self.assertIsNone(token.value)
        self.assertIsNone(token.real_value)
        self.assertIsNone(token.literal_value)

    def test_token_creation_with_numeric_value(self):
        token = Token(self.defs.TokenType.NUM, "42", 1, 1, value=42)
        self.assertEqual(token.value, 42)
        self.assertEqual(token.lexeme, "42")

    def test_token_creation_with_real_value(self):
        token = Token(self.defs.TokenType.REAL, "3.14", 1, 1, real_value=3.14)
        self.assertEqual(token.real_value, 3.14)
        self.assertEqual(token.lexeme, "3.14")

    def test_token_creation_with_literal_value(self):
        token = Token(self.defs.TokenType.LITERAL, '"hello"', 1, 1, literal_value="hello")
        self.assertEqual(token.literal_value, "hello")
        self.assertEqual(token.lexeme, '"hello"')

    def test_token_str_representation(self):
        token = Token(self.defs.TokenType.ID, "identifier", 1, 1)
        expected_str = f"<{self.defs.TokenType.ID.value}, 'identifier'>"
        self.assertEqual(str(token), expected_str)

    def test_token_repr_representation(self):
        token = Token(self.defs.TokenType.NUM, "123", 1, 1, value=123)
        expected_repr = "Token(type=TokenType.NUM, lexeme='123', value=123, line=1, column=1)"
        self.assertEqual(repr(token), expected_repr)

    def test_token_creation_with_all_attributes(self):
        token = Token(
            self.defs.TokenType.NUM,
            "42.5",
            5,
            10,
            value=42,
            real_value=42.5,
            literal_value="42.5"
        )
        self.assertEqual(token.token_type, self.defs.TokenType.NUM)
        self.assertEqual(token.lexeme, "42.5")
        self.assertEqual(token.line_number, 5)
        self.assertEqual(token.column_number, 10)
        self.assertEqual(token.value, 42)
        self.assertEqual(token.real_value, 42.5)
        self.assertEqual(token.literal_value, "42.5")

if __name__ == '__main__':
    unittest.main()
