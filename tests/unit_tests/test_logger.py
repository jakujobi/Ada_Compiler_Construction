import unittest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Logger import Logger, ColoredFormatter, CallerFilter

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        Logger._instance = None  # Reset singleton for each test
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_singleton_pattern(self):
        logger1 = Logger(log_directory=self.temp_dir)
        logger2 = Logger(log_directory=self.temp_dir)
        self.assertIs(logger1, logger2)
        
    def test_log_directory_creation(self):
        log_dir = os.path.join(self.temp_dir, "test_logs")
        logger = Logger(log_directory=log_dir)
        self.assertTrue(os.path.exists(log_dir))
        
    def test_log_file_creation(self):
        logger = Logger(log_directory=self.temp_dir)
        self.assertTrue(os.path.exists(logger.log_filename))
        
    def test_log_levels(self):
        logger = Logger(log_directory=self.temp_dir)
        logger.set_level(logging.WARNING)
        
        # Get console handler
        console_handler = next(h for h in logger._logger.handlers 
                             if isinstance(h, logging.StreamHandler))
        self.assertEqual(console_handler.level, logging.WARNING)
        
    def test_colored_formatter(self):
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            "test", logging.INFO, "", 0, "test message", (), None
        )
        formatted = formatter.format(record)
        self.assertIn("\033[36m", formatted)  # Cyan color for INFO
        
    def test_custom_format(self):
        custom_format = "%(levelname)s - %(message)s"
        logger = Logger(
            log_directory=self.temp_dir,
            fmt=custom_format
        )
        self.assertEqual(
            logger._logger.handlers[0].formatter._fmt,
            custom_format
        )
        
    def test_caller_filter(self):
        class TestClass:
            def __init__(self):
                self.logger = Logger(log_directory=self.temp_dir)
                
            def log_something(self):
                self.logger.info("test message")
                
        test_instance = TestClass()
        test_instance.log_something()
        
        # Check log file content
        with open(logger.log_filename, 'r') as f:
            log_content = f.read()
            self.assertIn("TestClass", log_content)
            
    def test_log_level_change_handlers(self):
        logger = Logger(log_directory=self.temp_dir)
        
        # Test console handler only
        logger.set_level(logging.ERROR, handler_type="console")
        console_handler = next(h for h in logger._logger.handlers 
                             if isinstance(h, logging.StreamHandler))
        self.assertEqual(console_handler.level, logging.ERROR)
        
        # Test file handler only
        logger.set_level(logging.DEBUG, handler_type="file")
        file_handler = next(h for h in logger._logger.handlers 
                          if isinstance(h, logging.FileHandler))
        self.assertEqual(file_handler.level, logging.DEBUG)
        
    def test_source_name_detection(self):
        logger = Logger(log_directory=self.temp_dir)
        self.assertIn("TestLogger", logger.log_filename)
        
    def test_initialization_with_invalid_directory(self):
        invalid_dir = "/invalid/directory/path"
        with self.assertRaises(Exception):
            Logger(log_directory=invalid_dir)

if __name__ == '__main__':
    unittest.main()
