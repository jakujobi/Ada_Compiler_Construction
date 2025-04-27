import unittest
import os
import sys
from pathlib import Path

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.Definitions import Definitions


class TestDefinitions(unittest.TestCase):

    def setUp(self):
        """Create a Definitions instance for each test."""
        self.defs = Definitions()

    def test_token_type_enum(self):
        """Verify the existence of key TokenType members."""
        self.assertTrue(hasattr(self.defs.TokenType, 'ID'))
        self.assertTrue(hasattr(self.defs.TokenType, 'NUM'))
        self.assertTrue(hasattr(self.defs.TokenType, 'REAL'))
        self.assertTrue(hasattr(self.defs.TokenType, 'PROCEDURE'))
        self.assertTrue(hasattr(self.defs.TokenType, 'BEGIN'))
        self.assertTrue(hasattr(self.defs.TokenType, 'END'))
        self.assertTrue(hasattr(self.defs.TokenType, 'SEMICOLON'))
        self.assertTrue(hasattr(self.defs.TokenType, 'ASSIGN'))
        self.assertTrue(hasattr(self.defs.TokenType, 'LPAREN'))
        self.assertTrue(hasattr(self.defs.TokenType, 'RPAREN'))
        self.assertTrue(hasattr(self.defs.TokenType, 'EOF'))
        # Add more checks for other essential token types
        self.assertTrue(hasattr(self.defs.TokenType, 'INTEGERT'))
        self.assertTrue(hasattr(self.defs.TokenType, 'REALT'))
        self.assertTrue(hasattr(self.defs.TokenType, 'CONSTANT'))
        self.assertTrue(hasattr(self.defs.TokenType, 'MOD'))
        self.assertTrue(hasattr(self.defs.TokenType, 'ADDOP'))
        self.assertTrue(hasattr(self.defs.TokenType, 'MULOP'))

    def test_reserved_words(self):
        """Verify the mapping of reserved words to their TokenTypes."""
        # Access as instance attribute
        reserved = self.defs.reserved_words
        # Convert keys to lowercase for consistent checking
        reserved_lower = {k.lower(): v for k, v in reserved.items()}

        self.assertEqual(reserved_lower['procedure'], self.defs.TokenType.PROCEDURE)
        self.assertEqual(reserved_lower['is'], self.defs.TokenType.IS)
        self.assertEqual(reserved_lower['begin'], self.defs.TokenType.BEGIN)
        self.assertEqual(reserved_lower['end'], self.defs.TokenType.END)
        self.assertEqual(reserved_lower['integer'], self.defs.TokenType.INTEGERT)
        self.assertEqual(reserved_lower['real'], self.defs.TokenType.REALT)
        self.assertEqual(reserved_lower['constant'], self.defs.TokenType.CONSTANT)
        self.assertEqual(reserved_lower['mod'], self.defs.TokenType.MOD)
        self.assertEqual(reserved_lower['rem'], self.defs.TokenType.REM)
        self.assertEqual(reserved_lower['in'], self.defs.TokenType.IN)
        self.assertEqual(reserved_lower['out'], self.defs.TokenType.OUT)
        self.assertEqual(reserved_lower['inout'], self.defs.TokenType.INOUT)
        # Add checks for all other reserved words (ensure keys are lowercase)

    # Potentially add tests for PUNCTUATION, WHITESPACE_CHARS etc. if needed

if __name__ == '__main__':
    unittest.main() 