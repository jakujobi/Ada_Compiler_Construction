#!/usr/bin/env python3
# test_runner.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-04-06
# Version: 1.1
"""
Test Runner for Ada Compiler Construction

This program allows you to run any of the driver files (JohnA1, JohnA3, etc.)
on any test file in the test_files directory or its subdirectories.

Usage:
    python test_runner.py [--config CONFIG_FILE]
"""

import os
import sys
import glob
import subprocess
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

try:
    import jakadac
    from jakadac.modules.Logger import Logger
except (ImportError, FileNotFoundError):
    # Add 'src' directory to path for local imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Logger import Logger

# Determine project root and test files directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEST_FILES_DIR = os.path.join(PROJECT_ROOT, 'tests', 'test_files')

class TestRunner:
    """
    Test Runner for Ada Compiler Construction
    Allows running any driver file on any test file
    """

    # CLI args annotation for batch mode
    cli_args: Optional[argparse.Namespace]

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the test runner.
        
        Args:
            config_file: Optional path to a configuration file
        """
        # Initialize CLI args to None
        self.cli_args = None

        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize logger with config settings
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        self.logger = Logger(log_level_console=log_level)
        self.logger.info("Initializing Test Runner")
        
        # Set repository home path
        self.repo_home = PROJECT_ROOT
        
        # Find all driver files
        self.driver_files = self._find_driver_files()
        
        # Find all test files under tests/test_files
        self.test_files = self._find_test_files()
        
        self.logger.info(f"Found {len(self.driver_files)} driver files and {len(self.test_files)} test files")

    def _load_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_file: Optional path to a configuration file
            
        Returns:
            Dict containing configuration settings
        """
        # Default configuration
        default_config = {
            'log_level': 'INFO',
            'driver_pattern': 'JohnA*.py',
            'test_file_extensions': ['.ada'],
            'test_directory': 'test_files',
            'output_format': 'text',
            'timeout': 30,  # seconds
            'max_output_lines': 1000
        }
        
        # If no config file specified, return defaults
        if not config_file:
            return default_config
            
        # Try to load config file
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                
            # Merge user config with defaults (user config takes precedence)
            config = default_config.copy()
            config.update(user_config)
            return config
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration")
            return default_config

    def _find_driver_files(self) -> Dict[str, str]:
        """
        Find all driver files in the project.
        
        Returns:
            Dict mapping driver name to full path
        """
        driver_files = {}
        pattern = self.config.get('driver_pattern', 'JohnA*.py')
        
        try:
            # Look for driver files in all directories
            for file_path in glob.glob(os.path.join(self.repo_home, "**", pattern), recursive=True):
                # Extract the driver name (e.g., "JohnA1" from "JohnA1.py")
                driver_name = os.path.basename(file_path).replace(".py", "")
                driver_files[driver_name] = file_path
                
            # Debug: Print found driver files
            self.logger.debug(f"Found driver files: {driver_files}")
                
            return driver_files
            
        except Exception as e:
            self.logger.error(f"Error finding driver files: {e}")
            return {}

    def _find_test_files(self) -> Dict[str, str]:
        """
        Find all test files in the tests/test_files directory and its subdirectories.
        
        Returns:
            Dict mapping test file name to full path
        """
        test_files = {}
        test_dir = TEST_FILES_DIR
        extensions = self.config.get('test_file_extensions', ['.ada'])
        
        if not os.path.exists(test_dir):
            self.logger.warning(f"Test directory not found: {test_dir}")
            return test_files
        
        try:
            for ext in extensions:
                for file_path in glob.glob(os.path.join(test_dir, "**", f"*{ext}"), recursive=True):
                    rel_path = os.path.relpath(file_path, test_dir)
                    test_files[rel_path] = file_path
            return test_files
        except Exception as e:
            self.logger.error(f"Error finding test files: {e}")
            return test_files

    def _display_menu(self, title: str, items: Dict[str, str]) -> Optional[str]:
        """
        Display a menu of items and let the user select one.
        
        Args:
            title: The title of the menu
            items: Dict mapping item name to item path
            
        Returns:
            The selected item path or None if the user cancels
        """
        if not items:
            self.logger.warning(f"No {title.lower()} found")
            return None
            
        print(f"\n{title}:")
        print("-" * (len(title) + 1))
        
        # Sort items by name for consistent display
        sorted_items = sorted(items.items())
        
        for i, (name, path) in enumerate(sorted_items, 1):
            print(f"{i}. {name}")
            
        print("0. Cancel")
        
        while True:
            try:
                choice = input("\nEnter your choice (0-{}): ".format(len(items)))
                choice_num = int(choice)
                
                if choice_num == 0:
                    return None
                    
                if 1 <= choice_num <= len(items):
                    return sorted_items[choice_num - 1][1]
                    
                print(f"Invalid choice. Please enter a number between 0 and {len(items)}")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def run_test(self, driver_path: str, test_file_path: str) -> bool:
        """
        Run a test file with the specified driver.
        
        Args:
            driver_path: Path to the driver file
            test_file_path: Path to the test file
            
        Returns:
            True if the test ran successfully, False otherwise
        """
        self.logger.info(f"Running {os.path.basename(driver_path)} on {os.path.basename(test_file_path)}")
        
        try:
            # Run the driver with the test file as an argument
            cmd = [sys.executable, driver_path, test_file_path]
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            # Get timeout from config
            timeout = self.config.get('timeout', 30)
            
            # Run the command and capture output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            # Print the output
            print("\nOutput:")
            print("-" * 50)
            
            # Limit output lines if configured
            max_lines = self.config.get('max_output_lines', 1000)
            stdout_lines = result.stdout.splitlines()
            if len(stdout_lines) > max_lines:
                print("\n".join(stdout_lines[:max_lines]))
                print(f"\n... (output truncated, {len(stdout_lines) - max_lines} more lines)")
            else:
                print(result.stdout)
            
            if result.stderr:
                print("\nErrors:")
                print("-" * 50)
                print(result.stderr)
                
            self.logger.info("Test completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Test timed out after {timeout} seconds")
            print(f"Error: Test timed out after {timeout} seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"Error running test: {str(e)}")
            print(f"Error: {str(e)}")
            return False

    def run(self) -> None:
        """Run the test runner."""
        print("\nAda Compiler Construction Test Runner")
        print("=====================================")
        
        # Batch mode: if driver and all-tests flags provided, run all tests automatically
        if self.cli_args is not None:
            driver = getattr(self.cli_args, 'driver', None)
            all_tests = getattr(self.cli_args, 'all_tests', False)
            if driver and all_tests:
                self.logger.info(f"Batch mode: running driver {driver} against all test files")
                driver_path = self.driver_files.get(driver)
                if not driver_path:
                    self.logger.error(f"Driver not found: {driver}")
                    return
                for test_name, test_path in sorted(self.test_files.items()):
                    self.run_test(driver_path, test_path)
                self.logger.info("Batch run completed")
                return
        
        while True:
            # Let the user select a driver
            print("\nDriver Files:")
            print("-------------")
            
            # Sort items by name for consistent display
            sorted_drivers = sorted(self.driver_files.items())
            
            for i, (name, path) in enumerate(sorted_drivers, 1):
                print(f"{i}. {name}")
                
            print("0. Cancel")
            
            while True:
                try:
                    choice = input("\nEnter your choice (0-{}): ".format(len(sorted_drivers)))
                    choice_num = int(choice)
                    
                    if choice_num == 0:
                        return
                        
                    if 1 <= choice_num <= len(sorted_drivers):
                        driver_path = sorted_drivers[choice_num - 1][1]
                        break
                        
                    print(f"Invalid choice. Please enter a number between 0 and {len(sorted_drivers)}")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            # Let the user select a test file
            print("\nTest Files:")
            print("-----------")
            
            # Sort items by name for consistent display
            sorted_tests = sorted(self.test_files.items())
            
            for i, (name, path) in enumerate(sorted_tests, 1):
                print(f"{i}. {name}")
                
            print("0. Cancel")
            
            while True:
                try:
                    choice = input("\nEnter your choice (0-{}): ".format(len(sorted_tests)))
                    choice_num = int(choice)
                    
                    if choice_num == 0:
                        break
                        
                    if 1 <= choice_num <= len(sorted_tests):
                        test_file_path = sorted_tests[choice_num - 1][1]
                        
                        # Run the test
                        self.run_test(driver_path, test_file_path)
                        break
                        
                    print(f"Invalid choice. Please enter a number between 0 and {len(sorted_tests)}")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            # Ask if the user wants to run another test
            again = input("\nRun another test? (y/n): ").lower()
            if again != 'y':
                break
                
        self.logger.info("Test Runner completed")


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Test Runner for Ada Compiler Construction")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--driver", help="Driver name to use (e.g., JohnA6)")
    parser.add_argument("--all-tests", action="store_true", help="Run all test files with selected driver")
    return parser.parse_args()


def main() -> None:
    """Main entry point for the test runner."""
    args = parse_arguments()
    test_runner = TestRunner(config_file=args.config)
    # Attach CLI args for batch processing
    test_runner.cli_args = args
    test_runner.run()


if __name__ == "__main__":
    main() 