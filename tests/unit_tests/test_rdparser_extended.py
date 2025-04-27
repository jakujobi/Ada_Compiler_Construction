import unittest
import os
import sys
from pathlib import Path

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.Token import Token
from jakadac.modules.Definitions import Definitions
from jakadac.modules.LexicalAnalyzer import LexicalAnalyzer
from jakadac.modules.RDParserExtended import RDParserExtended
from jakadac.modules.SymTable import SymbolTable, Symbol, EntryType, VarType, DuplicateSymbolError
from jakadac.modules.Logger import Logger # Import logger if needed, or disable/mock

# Disable logging during tests unless debugging
# logger.disable_logging()

class TestRDParserExtended(unittest.TestCase):

    def setUp(self):
        """Set up shared resources for tests."""
        self.defs = Definitions()
        self.lexer = LexicalAnalyzer("", self.defs) # Initialize lexer
        self.logger = Logger(log_level_console=None, log_level_file=None) # Suppress logs

    def _get_tokens(self, source_code):
        """Helper method to tokenize source code string."""
        self.lexer.source_code = source_code
        self.lexer.current_pos = 0
        self.lexer.current_line = 1
        self.lexer.current_col = 1
        tokens = self.lexer.analyze(source_code)
        # Filter out comments if necessary (assuming analyze includes them)
        # tokens = [t for t in tokens if t.token_type != self.defs.TokenType.COMMENT]
        return tokens

    def _setup_parser(self, tokens, build_tree=False, stop_on_error=False):
        """Helper to initialize the parser with tokens and options."""
        symtab = SymbolTable()
        parser = RDParserExtended(
            tokens,
            self.defs,
            symbol_table=symtab,
            stop_on_error=stop_on_error,
            panic_mode_recover=False, # Keep panic mode off for now
            build_parse_tree=build_tree
        )
        parser.logger = self.logger # Assign suppressed logger
        return parser

    def test_empty_program(self):
        """Test parsing the minimal valid program structure."""
        source = "procedure empty is begin null; end empty;"
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)
        parse_ok = parser.parse()
        self.assertTrue(parse_ok, f"Parsing failed. Errors: {parser.errors}")
        self.assertEqual(len(parser.errors), 0, "Should have no syntax errors")
        self.assertEqual(len(parser.semantic_errors), 0, "Should have no semantic errors")

    def test_simple_assignment(self):
        """Test parsing a single assignment statement."""
        source = """
        procedure assign_test is
            x : integer;
        begin
            x := 5;
        end assign_test;
        """
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)

        # Manually insert 'x' before parsing statements for semantic check
        x_token = Token(self.defs.TokenType.ID, 'x', 2, 13)
        x_sym = Symbol('x', x_token, EntryType.VARIABLE, 0)
        x_sym.set_variable_info(VarType.INT, 0, 2)
        try:
            # Insert into the parser's symbol table BEFORE parse starts
            parser.symbol_table.insert(x_sym)
        except DuplicateSymbolError:
            self.fail("Setup failed: could not insert symbol")

        parse_ok = parser.parse()

        # Debug output if parse fails
        if not parse_ok or parser.errors or parser.semantic_errors:
            print("--- Test Simple Assignment Errors ---")
            print("Syntax Errors:", parser.errors)
            print("Semantic Errors:", parser.semantic_errors)
            print("Tokens:", tokens)
            print("------------------------------------")

        self.assertTrue(parse_ok, "Parsing failed for simple assignment")
        self.assertEqual(len(parser.errors), 0, "Should have no syntax errors")
        # Semantic check during parsing should pass as 'x' is declared
        # Note: The current parser setup doesn't run full semantic analysis,
        # it only checks for undeclared IDs during Factor/AssignStat parsing.
        self.assertEqual(len(parser.semantic_errors), 0, "Should have no semantic errors")

    def test_undeclared_variable_assignment(self):
        """Test semantic error for assignment to undeclared variable."""
        source = """
        procedure undeclared is
        begin
            y := 10;
        end undeclared;
        """
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)
        parse_ok = parser.parse() # Parse should succeed syntactically

        self.assertTrue(parse_ok, "Parsing should succeed syntactically even with semantic errors")
        self.assertEqual(len(parser.errors), 0, "Should have no syntax errors")
        self.assertEqual(len(parser.semantic_errors), 1, "Should have one semantic error for undeclared 'y'")
        self.assertIn("Undeclared variable 'y'", parser.semantic_errors[0]['message'])

    def test_undeclared_variable_factor(self):
        """Test semantic error for undeclared variable in an expression factor."""
        source = """
        procedure undeclared_expr is
            x : integer;
        begin
            x := z + 5;
        end undeclared_expr;
        """
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)

        # Declare 'x'
        x_token = Token(self.defs.TokenType.ID, 'x', 2, 13)
        x_sym = Symbol('x', x_token, EntryType.VARIABLE, 0)
        parser.symbol_table.insert(x_sym)

        parse_ok = parser.parse()

        self.assertTrue(parse_ok, "Parsing should succeed syntactically")
        self.assertEqual(len(parser.errors), 0, "Should have no syntax errors")
        self.assertEqual(len(parser.semantic_errors), 1, "Should have one semantic error for undeclared 'z'")
        self.assertIn("Undeclared variable 'z'", parser.semantic_errors[0]['message'])

    def test_procedure_name_mismatch(self):
        """Test error reporting for mismatched procedure end name."""
        source = "procedure name_test is begin null; end different_name;"
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)
        parse_ok = parser.parse()

        self.assertFalse(parse_ok, "Parsing should fail due to name mismatch")
        self.assertEqual(len(parser.errors), 1, "Should have one syntax error for name mismatch")
        self.assertIn("Procedure name mismatch", parser.errors[0])
        self.assertEqual(len(parser.semantic_errors), 1, "Should have one semantic error for name mismatch")
        self.assertIn("Procedure name mismatch", parser.semantic_errors[0]['message'])

    def test_sequence_of_statements(self):
        """Test parsing multiple statements."""
        source = """
        procedure multi is
            a, b, c : integer;
        begin
            a := 1;
            b := a + 2;
            c := a * b;
        end multi;
        """
        tokens = self._get_tokens(source)
        parser = self._setup_parser(tokens)

        # Declare variables
        tok_a = Token(self.defs.TokenType.ID, 'a', 2, 13)
        tok_b = Token(self.defs.TokenType.ID, 'b', 2, 16)
        tok_c = Token(self.defs.TokenType.ID, 'c', 2, 19)
        parser.symbol_table.insert(Symbol('a', tok_a, EntryType.VARIABLE, 0))
        parser.symbol_table.insert(Symbol('b', tok_b, EntryType.VARIABLE, 0))
        parser.symbol_table.insert(Symbol('c', tok_c, EntryType.VARIABLE, 0))

        parse_ok = parser.parse()
        self.assertTrue(parse_ok, f"Parsing failed. Errors: {parser.errors} SemErrs: {parser.semantic_errors}")
        self.assertEqual(len(parser.errors), 0, "Should have no syntax errors")
        self.assertEqual(len(parser.semantic_errors), 0, "Should have no semantic errors")

    # --- Add more tests for specific grammar rules --- 
    # e.g., test_expression_with_mod, test_nested_procedure_parsing, etc.


if __name__ == '__main__':
    unittest.main() 