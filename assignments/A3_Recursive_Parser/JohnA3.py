#!/usr/bin/env python3
# JohnA3.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.1
"""
Driver program for Assignment 3: Recursive Descent Parser for Ada Compiler

This program demonstrates the syntax analysis phase of the compiler:
1. Lexical Analysis: Tokenizes the source code
2. Syntax Analysis: Parses the tokens using a recursive descent parser

The implementation includes proper type annotations with Optional types
for parameters that can be None, ensuring type safety and improved code quality.

Usage:
    python JohnA3.py <input_file> [output_file]
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List


try:
    import jakadac
    from jakadac.modules.Driver import BaseDriver
    from jakadac.modules.Logger import Logger
    from jakadac.modules.RDParser import RDParser
except (ImportError, FileNotFoundError):
    # Add 'src' directory to path for local imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
    from src.jakadac.modules.RDParser import RDParser

class JohnA3(BaseDriver):
    """
    Driver class for Assignment 3: Recursive Descent Parser
    Inherits from BaseDriver to reuse common functionality
    """

    def __init__(self, input_file_name: str, output_file_name: Optional[str] = None, debug: bool = False, logger: Optional[Logger] = None):
        """
        Initialize the JohnA3 driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            logger: Optional logger instance to use
        """
        super().__init__(input_file_name, output_file_name, debug, logger)
        self.parser = None
        self.run()

    def run(self) -> None:
        """
        Main function to run the compilation process.
        
        It:
            1. Reads the source file
            2. Prints the source code
            3. Performs lexical analysis
            4. Performs syntax analysis
            5. Prints compilation summary
        """
        self.logger.info("Starting compilation process.")
        
        try:
            self.get_source_code_from_file()
            self.print_source_code()
            
            if self.source_code:
                self.stage1_lexical_analysis()
                self.stage2_syntax_analysis()
                self.print_compilation_summary()
            else:
                self.logger.error("No source code to process.")
                sys.exit(1)
                
        except Exception as e:
            self.logger.critical(f"An error occurred during compilation: {str(e)}")
            sys.exit(1)

    def stage1_lexical_analysis(self) -> None:
        """
        Stage 1: Lexical Analysis
        Tokenize the source code and output the tokens.
        """
        self.logger.info("Starting lexical analysis.")
        self.process_tokens()
        self.format_and_output_tokens()
        self.logger.info("Lexical analysis complete.")

    def stage2_syntax_analysis(self) -> None:
        """
        Stage 2: Syntax Analysis
        Parse the tokens using the recursive descent parser.
        """
        if not self.tokens:
            self.logger.error("No tokens to parse.")
            self.logger.critical("Syntax analysis failed. Exiting program.")
            sys.exit(1)

        self.logger.info("Starting syntax analysis.")
        print("\nPhase 2: Syntax Analysis")
        print("-" * 50)
        
        try:
            # Create and configure the parser
            self.parser = RDParser(
                self.tokens,
                self.lexical_analyzer.defs,
                stop_on_error=False,
                panic_mode_recover=False,
                build_parse_tree=True
            )
            
            # Parse the tokens
            parsing_successful = self.parser.parse()
            self.syntax_errors = self.parser.errors
            
            if parsing_successful:
                print("Parsing completed successfully")
                self.logger.info("Parsing completed successfully.")
            else:
                print(f"Parsing failed with {len(self.syntax_errors)} errors")
                if self.debug:
                    for error in self.syntax_errors[:5]:  # Show first 5 errors
                        print(f"  Line {error.get('line', 'unknown')}, "
                              f"Column {error.get('column', 'unknown')}: {error.get('message', 'Unknown error')}")
                    if len(self.syntax_errors) > 5:
                        print(f"  ... and {len(self.syntax_errors) - 5} more")
            
            # Print parse tree if available
            if hasattr(self.parser, 'parse_tree_root') and self.parser.parse_tree_root:
                self.parser.print_parse_tree()
                
            self.logger.info("Syntax analysis complete.")
            
        except Exception as e:
            self.logger.critical(f"An error occurred during syntax analysis: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """
    Main entry point for the recursive descent parser program.
    
    It:
        1. Initializes the Logger
        2. Checks command-line arguments
        3. Creates and runs a JohnA3 instance
    """
    # Initialize the Logger
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA3 program.")
    
    # Check command line arguments
    args = sys.argv[1:]
    if len(args) == 2:
        input_file, output_file = args
        logger.debug(f"Input file: {input_file}, Output file: {output_file}")
        JohnA3(input_file, output_file, logger=logger)
    elif len(args) == 1:
        input_file = args[0]
        logger.debug(f"Input file: {input_file}")
        JohnA3(input_file, logger=logger)
    else:
        print("Usage: python JohnA3.py <input_file> [output_file]")
        logger.critical("Invalid number of arguments. Exiting program.")
        sys.exit(1)


if __name__ == "__main__":
    main()