#!/usr/bin/env python3
# test_runner.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-04-06
# Version: 1.0
"""
Test Runner for Ada Compiler Construction

This program allows you to run any of the driver files (JohnA1, JohnA3, etc.)
on any test file in the test_files directory or its subdirectories.

Usage:
    python test_runner.py
"""

import os
import sys
import glob
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add the parent directory to the path so we can import modules
repo_home_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(repo_home_path)

from Modules.Logger import Logger


class TestRunner:
    """
    Test Runner for Ada Compiler Construction
    Allows running any driver file on any test file
    """

    def __init__(self):
        """Initialize the test runner."""
        self.logger = Logger(log_level_console=logging.INFO)
        self.logger.info("Initializing Test Runner")
        
        # Get the repository home path
        self.repo_home = repo_home_path
        
        # Find all driver files
        self.driver_files = self._find_driver_files()
        
        # Find all test files
        self.test_files = self._find_test_files()
        
        self.logger.info(f"Found {len(self.driver_files)} driver files and {len(self.test_files)} test files")

    def _find_driver_files(self) -> Dict[str, str]:
        """
        Find all driver files (JohnA*.py) in the project.
        
        Returns:
            Dict mapping driver name to full path
        """
        driver_files = {}
        
        # Look for JohnA*.py files in all directories
        for file_path in glob.glob(os.path.join(self.repo_home, "**", "JohnA*.py"), recursive=True):
            # Extract the driver name (e.g., "JohnA1" from "JohnA1.py")
            driver_name = os.path.basename(file_path).replace(".py", "")
            driver_files[driver_name] = file_path
            
        return driver_files

    def _find_test_files(self) -> Dict[str, str]:
        """
        Find all test files in the test_files directory and its subdirectories.
        
        Returns:
            Dict mapping test file name to full path
        """
        test_files = {}
        test_dir = os.path.join(self.repo_home, "test_files")
        
        if not os.path.exists(test_dir):
            self.logger.warning(f"Test directory not found: {test_dir}")
            return test_files
        
        # Find all .ada files in the test_files directory and its subdirectories
        for file_path in glob.glob(os.path.join(test_dir, "**", "*.ada"), recursive=True):
            # Get the relative path from the test_files directory
            rel_path = os.path.relpath(file_path, test_dir)
            test_files[rel_path] = file_path
            
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

    def run_test(self, driver_path: str, test_file_path: str) -> None:
        """
        Run a test file with the specified driver.
        
        Args:
            driver_path: Path to the driver file
            test_file_path: Path to the test file
        """
        self.logger.info(f"Running {os.path.basename(driver_path)} on {os.path.basename(test_file_path)}")
        
        try:
            # Run the driver with the test file as an argument
            cmd = [sys.executable, driver_path, test_file_path]
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            # Run the command and capture output
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Print the output
            print("\nOutput:")
            print("-" * 50)
            print(result.stdout)
            
            if result.stderr:
                print("\nErrors:")
                print("-" * 50)
                print(result.stderr)
                
            self.logger.info("Test completed")
            
        except Exception as e:
            self.logger.error(f"Error running test: {str(e)}")
            print(f"Error: {str(e)}")

    def run(self) -> None:
        """Run the test runner."""
        print("\nAda Compiler Construction Test Runner")
        print("=====================================")
        
        while True:
            # Let the user select a driver
            driver_path = self._display_menu("Driver Files", self.driver_files)
            if not driver_path:
                break
                
            # Let the user select a test file
            test_file_path = self._display_menu("Test Files", self.test_files)
            if not test_file_path:
                continue
                
            # Run the test
            self.run_test(driver_path, test_file_path)
            
            # Ask if the user wants to run another test
            again = input("\nRun another test? (y/n): ").lower()
            if again != 'y':
                break
                
        self.logger.info("Test Runner completed")


def main():
    """Main entry point for the test runner."""
    test_runner = TestRunner()
    test_runner.run()


if __name__ == "__main__":
    main() 