#!/usr/bin/env python3
# JohnA1.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.1
"""
Driver program for Assignment 1: Lexical Analyzer for Ada Compiler

This program demonstrates the lexical analysis phase of the compiler:
1. Reads source code from a file
2. Tokenizes the source code using LexicalAnalyzer
3. Outputs the tokens to console and optionally to a file

The implementation includes proper type annotations with Optional types
for parameters that can be None, ensuring type safety and improved code quality.

Usage:
    python JohnA1.py <input_file> [output_file]
"""

import os
import sys

import logging
from pathlib import Path
from typing import Optional

# Attempt to import from installed package; fallback for local development
try:
    import jakadac
    from jakadac.modules.Driver import BaseDriver
    from jakadac.modules.Logger import Logger
except ImportError:
    # Add 'src' directory to path for local imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger





class JohnA1(BaseDriver):
    """
    Driver class for Assignment 1: Lexical Analysis
    Inherits from BaseDriver to reuse common functionality
    """

    def __init__(self, input_file_name: str, output_file_name: Optional[str] = None, debug: bool = False, logger: Optional[Logger] = None):
        """
        Initialize the JohnA1 driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            logger: Optional logger instance to use
        """
        super().__init__(input_file_name, output_file_name, debug, logger)
        self.run()

    def run(self) -> None:
        """
        Main function to run the lexical analysis process.
        
        It:
            1. Reads the source file
            2. Prints the source code
            3. Processes the source code to extract tokens
            4. Formats and outputs the tokens
        """
        self.logger.info("Starting lexical analysis process.")
        
        try:
            self.get_source_code_from_file()
            self.print_source_code()
            
            if self.source_code:
                self.process_tokens()
                self.format_and_output_tokens()
                self.print_compilation_summary()
            else:
                self.logger.error("No source code to process.")
                sys.exit(1)
                
        except Exception as e:
            self.logger.critical(f"An error occurred during lexical analysis: {str(e)}")
            sys.exit(1)


def main():
    """
    Main entry point for the lexical analyzer program.
    
    It:
        1. Initializes the Logger
        2. Checks command-line arguments
        3. Creates and runs a JohnA1 instance
    """
    # Initialize the Logger
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA1 program.")
    
    # Check command line arguments
    args = sys.argv[1:]
    if len(args) == 2:
        input_file, output_file = args
        logger.debug(f"Input file: {input_file}, Output file: {output_file}")
        JohnA1(input_file, output_file, logger=logger)
    elif len(args) == 1:
        input_file = args[0]
        logger.debug(f"Input file: {input_file}")
        JohnA1(input_file, logger=logger)
    else:
        print("Usage: python JohnA1.py <input_file> [output_file]")
        logger.critical("Invalid number of arguments. Exiting program.")
        sys.exit(1)


if __name__ == "__main__":
    main()
