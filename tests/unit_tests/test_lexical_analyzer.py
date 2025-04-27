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
from jakadac.modules.LexicalAnalyzer import LexicalAnalyzer
from jakadac.modules.Definitions import Definitions
from jakadac.modules.Token import Token # Likely needed

class TestLexicalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.defs = Definitions() # Create defs first
        # Pass the Definitions instance to the Lexer
        self.lexer = LexicalAnalyzer(self.defs)

    def test_basic_identifier(self):
        tokens = self.lexer.analyze("variable_name")
        self.assertEqual(len(tokens), 2)  # Including EOF token
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.ID)
        self.assertEqual(tokens[0].lexeme, "variable_name")
        self.assertEqual(tokens[0].line_number, 1)
        self.assertEqual(tokens[0].column_number, 1)

    def test_reserved_word(self):
        tokens = self.lexer.analyze("begin")
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.BEGIN)
        self.assertEqual(tokens[0].lexeme, "begin")

    def test_numeric_literal(self):
        tokens = self.lexer.analyze("42")
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.NUM)
        self.assertEqual(tokens[0].value, 42)

    def test_real_number(self):
        tokens = self.lexer.analyze("3.14")
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.REAL)
        self.assertEqual(tokens[0].value, 3.14)

    def test_string_literal(self):
        tokens = self.lexer.analyze('"Hello, World!"')
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.LITERAL)
        self.assertEqual(tokens[0].literal_value, "Hello, World!")

    def test_character_literal(self):
        tokens = self.lexer.analyze("'A'")
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.CHAR_LITERAL)
        self.assertEqual(tokens[0].literal_value, "A")

    def test_escaped_string_literal(self):
        tokens = self.lexer.analyze('"Contains ""quotes"" inside"')
        self.assertEqual(tokens[0].literal_value, 'Contains "quotes" inside')

    def test_escaped_char_literal(self):
        tokens = self.lexer.analyze("''''")
        self.assertEqual(tokens[0].literal_value, "'")

    def test_comment_skipping(self):
        tokens = self.lexer.analyze("-- This is a comment\nidentifier")
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.ID)
        self.assertEqual(tokens[0].line_number, 2)

    def test_multiple_tokens(self):
        tokens = self.lexer.analyze("if x > 10 then")
        self.assertEqual(len(tokens), 6)  # 5 tokens + EOF
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.IF)
        self.assertEqual(tokens[1].token_type, self.defs.TokenType.ID)
        self.assertEqual(tokens[2].token_type, self.defs.TokenType.GT)
        self.assertEqual(tokens[3].token_type, self.defs.TokenType.NUM)
        self.assertEqual(tokens[4].token_type, self.defs.TokenType.THEN)

    def test_whitespace_handling(self):
        tokens = self.lexer.analyze("a\n  b\t\tc")
        self.assertEqual(len(tokens), 4)  # 3 identifiers + EOF
        self.assertEqual(tokens[1].line_number, 2)

    def test_long_identifier_error(self):
        long_identifier = "a" * 18
        tokens = self.lexer.analyze(long_identifier)
        self.assertTrue(any("exceeds maximum length" in error for error in self.lexer.errors))

    def test_unterminated_string(self):
        self.lexer.analyze('"unterminated')
        self.assertTrue(any("Unterminated string literal" in error for error in self.lexer.errors))

    def test_concatenation_operator(self):
        tokens = self.lexer.analyze('&')
        self.assertEqual(tokens[0].token_type, self.defs.TokenType.CONCAT)

if __name__ == '__main__':
    unittest.main()
