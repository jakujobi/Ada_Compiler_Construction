import unittest
import logging
import os
import tempfile
import shutil
from pathlib import Path
import sys
from unittest.mock import patch, mock_open

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.Logger import Logger, ColoredFormatter, CallerFilter

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        Logger._instance = None  # Reset singleton for each test
        
    def tearDown(self):
        # Attempt to close logger handlers to release file locks
        logger_instance = Logger._instance
        # Check if instance exists, has the _logger attribute, and _logger is not None
        if logger_instance and hasattr(logger_instance, '_logger') and logger_instance._logger:
            handlers = logger_instance._logger.handlers[:]
            for handler in handlers:
                handler.close()
                logger_instance._logger.removeHandler(handler)
        
        # Reset the singleton instance so subsequent tests get a fresh one
        Logger._instance = None
        
        # Now remove the directory
        # Add error handling in case the directory is already gone or removal fails
        try:
            shutil.rmtree(self.temp_dir)
        except FileNotFoundError:
            pass # Directory already gone, ignore
        except OSError as e:
            print(f"Warning: Could not remove temp dir {self.temp_dir}: {e}")
        
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
        # Nested class needs access to temp_dir
        outer_temp_dir = self.temp_dir
        
        class TestClass:
            def __init__(self, temp_dir):
                # Use the passed temp_dir
                self.logger = Logger(log_directory=temp_dir)
                
            def log_something(self):
                self.logger.info("test message")
                
        # Pass temp_dir when creating instance
        test_instance = TestClass(outer_temp_dir)
        test_instance.log_something()
        
        # Check log file content using the correct logger instance
        # Ensure the logger instance exists and has a filename
        log_filename = getattr(test_instance.logger, 'log_filename', None)
        self.assertIsNotNone(log_filename, "Logger instance should have a log_filename")
        
        # Satisfy linter by checking log_filename is not None before opening
        if log_filename:
            with open(log_filename, 'r') as f:
                log_content = f.read()
                # Check if the class name or method name is in the log content
                # based on the expected log format
                self.assertTrue("TestClass" in log_content or "log_something" in log_content,
                                f"Log content should contain caller info. Content:\\n{log_content}")
            
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
