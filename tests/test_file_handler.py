import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.FileHandler import FileHandler

class TestFileHandler(unittest.TestCase):
    def setUp(self):
        self.file_handler = FileHandler()
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test.txt")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_read_file_as_string(self):
        content = "Test content\nSecond line"
        with open(self.test_file_path, 'w') as f:
            f.write(content)
            
        result = self.file_handler.read_file_as_string(self.test_file_path)
        self.assertEqual(result, content)
        
    def test_process_file_char_stream(self):
        content = "ABC"
        with open(self.test_file_path, 'w') as f:
            f.write(content)
            
        chars = list(self.file_handler.process_file_char_stream(self.test_file_path))
        self.assertEqual(chars, ['A', 'B', 'C'])
        
    def test_write_string_to_file(self):
        content = "Test string content"
        self.file_handler.write_string_to_file(self.test_file_path, content)
        
        with open(self.test_file_path, 'r') as f:
            result = f.read()
        self.assertEqual(result, content)
        
    def test_append_to_file(self):
        initial_content = ["Line 1", "Line 2"]
        append_content = ["Line 3", "Line 4"]
        
        self.file_handler.write_file(self.test_file_path, initial_content)
        self.file_handler.append_to_file(self.test_file_path, append_content)
        
        with open(self.test_file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            
        self.assertEqual(lines, ["Line 1", "Line 2", "Line 3", "Line 4"])
        
    def test_read_line_from_file(self):
        test_cases = [
            ("normal line", "normal line"),
            ("line with comment // ignored", "line with comment"),
            ("   spaces   ", "spaces"),
            ("// comment only", ""),
            ("\n", None)
        ]
        
        for input_line, expected in test_cases:
            result = self.file_handler.read_line_from_file(input_line)
            self.assertEqual(result, expected)
            
    def test_file_exists(self):
        with open(self.test_file_path, 'w') as f:
            f.write("test")
            
        self.assertTrue(self.file_handler.file_exists(self.test_file_path))
        self.assertFalse(self.file_handler.file_exists(os.path.join(self.temp_dir, "nonexistent.txt")))
        
    def test_create_new_file_in_main(self):
        file_name = "test_create"
        extension = "txt"
        result = self.file_handler.create_new_file_in_main(file_name, extension)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        os.remove(result)
        
    def test_read_file_raw(self):
        content = ["Line 1\n", "Line 2\n", "Line 3"]
        with open(self.test_file_path, 'w') as f:
            f.writelines(content)
            
        result = self.file_handler.read_file_raw(self.test_file_path)
        self.assertEqual(result, content)
        
    def test_write_file_empty_lines(self):
        lines = []
        success = self.file_handler.write_file(self.test_file_path, lines)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.test_file_path))
        
    def test_process_file_with_empty_file(self):
        with open(self.test_file_path, 'w') as f:
            pass
            
        result = self.file_handler.process_file(self.test_file_path)
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
