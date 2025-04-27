import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Modules to test/mock
from jakadac.modules.Driver import BaseDriver
from jakadac.modules.Logger import Logger
# Mock other dependencies if BaseDriver initialization calls them
# from jakadac.modules.LexicalAnalyzer import LexicalAnalyzer
# from jakadac.modules.RDParser import RDParser
# from jakadac.modules.RDParserExtended import RDParserExtended

# Create a dummy logger for tests to avoid actual logging
dummy_logger = Logger(log_level_console=None, log_level_file=None)

class TestBaseDriver(unittest.TestCase):

    def test_initialization_defaults(self):
        """Test BaseDriver initialization with minimal arguments."""
        input_file = "test.ada"
        # Use patch context managers if __init__ creates instances
        # with patch('jakadac.modules.Driver.LexicalAnalyzer') as MockLexer, \
        #      patch('jakadac.modules.Driver.RDParser') as MockParser:

        driver = BaseDriver(input_file_name=input_file, logger=dummy_logger)

        self.assertEqual(driver.input_file_name, input_file)
        self.assertIsNone(driver.output_file_name)
        self.assertFalse(driver.debug)
        self.assertIs(driver.logger, dummy_logger)
        self.assertFalse(driver.use_extended_parser) # Default should be False
        # Add assertions for other default states if necessary
        self.assertIsNone(driver.source_code)
        self.assertIsNotNone(driver.lexical_analyzer)
        self.assertIsNone(driver.parser)
        self.assertEqual(driver.tokens, [])
        self.assertEqual(driver.syntax_errors, [])
        self.assertEqual(driver.semantic_errors, [])

    def test_initialization_with_output(self):
        """Test BaseDriver initialization with an output file specified."""
        input_file = "in.ada"
        output_file = "out.txt"
        driver = BaseDriver(input_file, output_file, logger=dummy_logger)
        self.assertEqual(driver.input_file_name, input_file)
        self.assertEqual(driver.output_file_name, output_file)
        self.assertFalse(driver.debug)

    def test_initialization_debug_mode(self):
        """Test BaseDriver initialization with debug mode enabled."""
        input_file = "debug_test.ada"
        driver = BaseDriver(input_file, debug=True, logger=dummy_logger)
        self.assertEqual(driver.input_file_name, input_file)
        self.assertTrue(driver.debug)

    def test_initialization_extended_parser(self):
        """Test BaseDriver initialization with use_extended_parser=True."""
        input_file = "extended.ada"
        # Use patch context managers if __init__ creates instances based on flag
        # with patch('jakadac.modules.Driver.LexicalAnalyzer') as MockLexer, \
        #      patch('jakadac.modules.Driver.RDParserExtended') as MockExtendedParser:

        driver = BaseDriver(input_file, use_extended_parser=True, logger=dummy_logger)
        self.assertEqual(driver.input_file_name, input_file)
        self.assertTrue(driver.use_extended_parser)
        # Verify if the correct parser class *would* be selected later
        # This might require mocking the parser setup method if it happens in __init__

    def test_initialization_with_all_args(self):
        """Test BaseDriver initialization with all arguments provided."""
        input_file = "all_in.ada"
        output_file = "all_out.log"
        debug_mode = True
        use_extended = True
        # Create a specific logger instance for this test
        test_logger = Logger(log_level_console='DEBUG', log_level_file=None)

        driver = BaseDriver(
            input_file_name=input_file,
            output_file_name=output_file,
            debug=debug_mode,
            logger=test_logger,
            use_extended_parser=use_extended
        )

        self.assertEqual(driver.input_file_name, input_file)
        self.assertEqual(driver.output_file_name, output_file)
        self.assertEqual(driver.debug, debug_mode)
        self.assertIs(driver.logger, test_logger)
        self.assertEqual(driver.use_extended_parser, use_extended)

    # --- Tests for other BaseDriver methods --- 
    # We would need mocking for file operations and component interactions

    # Example: Test get_source_code_from_file (requires mocking Path.read_text)
    # @patch('pathlib.Path.read_text')
    # def test_get_source_code(self, mock_read_text):
    #     """Test reading source code from file."""
    #     input_file = "dummy.ada"
    #     expected_code = "procedure test is begin null; end test;"
    #     mock_read_text.return_value = expected_code
        
    #     driver = BaseDriver(input_file, logger=dummy_logger)
    #     driver.get_source_code_from_file()
        
    #     mock_read_text.assert_called_once()
    #     self.assertEqual(driver.source_code, expected_code)

    # Similar tests for run_lexical, run_syntax, run_semantic would require
    # mocking the Lexer, Parser, and Analyzer respectively.

if __name__ == '__main__':
    unittest.main() 