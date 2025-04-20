import unittest
import sys
import os
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch, MagicMock

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from A1 - Lexical Analyzer.JohnA1 import JohnA1
from Modules.Token import Token
from Modules.Definitions import Definitions

class TestJohnA1(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "test_input.txt")
        self.output_file = os.path.join(self.temp_dir, "test_output.txt")
        self.defs = Definitions()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)

    def test_initialization_with_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            JohnA1("nonexistent_file.txt")

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_source_code_empty(self, mock_stdout):
        with open(self.input_file, 'w') as f:
            f.write("")
        analyzer = JohnA1(self.input_file)
        self.assertEqual(mock_stdout.getvalue().strip(), "")

    def test_process_tokens_with_complex_input(self):
        test_code = "if x > 10 then\n    y := 20;\nend if;"
        with open(self.input_file, 'w') as f:
            f.write(test_code)
        analyzer = JohnA1(self.input_file, self.output_file)
        self.assertTrue(len(analyzer.tokens) > 0)
        self.assertEqual(analyzer.tokens[0].token_type, self.defs.TokenType.IF)

    def test_output_file_creation(self):
        test_code = "procedure Test is\nbegin\n    null;\nend Test;"
        with open(self.input_file, 'w') as f:
            f.write(test_code)
        analyzer = JohnA1(self.input_file, self.output_file)
        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, 'r') as f:
            content = f.read()
            self.assertIn("Token Type", content)
            self.assertIn("PROCEDURE", content)

    @patch('Modules.LexicalAnalyzer.LexicalAnalyzer.analyze')
    def test_error_handling_during_tokenization(self, mock_analyze):
        mock_analyze.side_effect = Exception("Tokenization error")
        with open(self.input_file, 'w') as f:
            f.write("test code")
        analyzer = JohnA1(self.input_file)
        self.assertEqual(analyzer.tokens, [])

    def test_write_output_with_special_characters(self):
        test_code = 'x := "Hello\nWorld";'
        with open(self.input_file, 'w') as f:
            f.write(test_code)
        analyzer = JohnA1(self.input_file, self.output_file)
        with open(self.output_file, 'r') as f:
            content = f.read()
            self.assertIn("LITERAL", content)

    @patch('sys.stdout', new_callable=StringIO)
    def test_format_output_without_values(self, mock_stdout):
        with open(self.input_file, 'w') as f:
            f.write("null;")
        analyzer = JohnA1(self.input_file)
        output = mock_stdout.getvalue()
        self.assertIn("Token Type", output)
        self.assertIn("NULL", output)

    def test_multiple_line_processing(self):
        test_code = "-- Comment\nidentifier1\n\nidentifier2"
        with open(self.input_file, 'w') as f:
            f.write(test_code)
        analyzer = JohnA1(self.input_file)
        id_tokens = [t for t in analyzer.tokens if t.token_type == self.defs.TokenType.ID]
        self.assertEqual(len(id_tokens), 2)
        self.assertEqual(id_tokens[0].line_number, 2)
        self.assertEqual(id_tokens[1].line_number, 4)

if __name__ == '__main__':
    unittest.main()
