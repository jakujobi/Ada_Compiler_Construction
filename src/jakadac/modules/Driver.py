#!/usr/bin/env python3
# Driver.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.0
"""
Base driver class for Ada compiler construction assignments.
This module provides a common foundation for all compiler driver classes.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.FileHandler import FileHandler
from Modules.RDParser import RDParser
from Modules.SemanticAnalyzer import SemanticAnalyzer


class BaseDriver:
    """
    Base driver class that provides common functionality for all compiler drivers.
    This class handles file I/O, logging, and basic compilation setup.
    """

    def __init__(
        self, 
        input_file_name: str, 
        output_file_name: Optional[str] = None, 
        debug: bool = False, 
        logger: Optional[Logger] = None
    ):
        """
        Initialize the base driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            logger: Optional logger instance to use
        """
        # Use provided logger or create a new one
        self.logger = logger if logger is not None else Logger(log_level_console=logging.INFO)
        
        # Store file paths
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        
        # Set debug mode
        self.debug = debug
        
        # Initialize common components
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        
        # Initialize data storage
        self.source_code: Optional[str] = None
        self.tokens: List[Token] = []
        
        # Initialize error tracking
        self.lexical_errors: List[Dict[str, Any]] = []
        self.syntax_errors: List[Dict[str, Any]] = []
        self.semantic_errors: List[Dict[str, Any]] = []

    def get_source_code_from_file(self) -> None:
        """
        Read the source code from the input file.
        
        Raises:
            FileNotFoundError: If the input file cannot be found
            IOError: If there are issues reading the file
        """
        self.logger.debug(f"Reading source code from file: {self.input_file_name}")
        try:
            with open(self.input_file_name, 'r') as file:
                self.source_code = file.read().strip()
            self.logger.debug("Source code read successfully.")
        except FileNotFoundError:
            self.logger.critical(f"Input file not found: {self.input_file_name}")
            raise
        except Exception as e:
            self.logger.critical(f"Error reading file: {str(e)}")
            raise

    def print_source_code(self) -> None:
        """Print the source code to the console."""
        if not self.source_code:
            self.logger.warning("No source code to print.")
            return
        print(self.source_code)
        self.logger.debug("Source code printed to console.")

    def process_tokens(self) -> None:
        """
        Process the source code into tokens using the lexical analyzer.
        
        Raises:
            ValueError: If invalid tokens are found
            Exception: For other tokenization errors
        """
        if not self.source_code:
            self.logger.error("No source code to process.")
            return
            
        self.logger.debug("Processing tokens from source code.")
        try:
            self.tokens = self.lexical_analyzer.analyze(self.source_code)
            self.logger.debug(f"Tokenization complete. {len(self.tokens)} tokens produced.")
        except ValueError as e:
            self.logger.error(f"Invalid token found: {e}")
            self.lexical_errors.append({"message": str(e)})
            self.logger.critical(f"An error occurred during tokenization: {e}")
            self.lexical_errors.append({"message": str(e)})

    def format_and_output_tokens(self) -> None:
        """
        Format the tokens into a table and output them to the console and file.
        """
        if not self.tokens:
            self.logger.warning("No tokens to format.")
            return

        # Create a header for the token table
        header = f"{'Token Type':15} | {'Lexeme':24} | {'Value'}"
        separator = "-" * (len(header) + 10)
        table_lines = [header, separator]
        
        # Format each token
        for token in self.tokens:
            token_type_name = token.token_type.name
            row = f"{token_type_name:15} | {token.lexeme:24} | {token.value}"
            self.logger.debug(f"Formatted token: {row}")
            table_lines.append(row)
        
        table_output = "\n".join(table_lines)
        print(table_output)
        self.logger.debug("Token table printed successfully.")

        # Write to output file if specified
        if self.output_file_name:
            self.write_output_to_file(self.output_file_name, table_output)

    def write_output_to_file(self, output_file_name: str, content: str) -> bool:
        """
        Write content to the specified output file.

        Args:
            output_file_name: Path to the output file
            content: Content to write to the file

        Returns:
            bool: True if writing was successful, False otherwise
        """
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.debug(f"Content successfully written to {output_file_name}.")
            return True
        except Exception as e:
            self.logger.critical(f"An error occurred while writing to the file '{output_file_name}': {e}")
            return False

    def print_tokens(self) -> None:
        """Print the tokens to the console."""
        if not self.tokens:
            self.logger.warning("No tokens to print.")
            return
        for token in self.tokens:
            print(token)
        self.logger.debug("Tokens printed to console.")

    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get the current processing status.

        Returns:
            Dict containing processing status information
        """
        return {
            'tokens_count': len(self.tokens) if self.tokens else 0,
            'has_source': bool(self.source_code),
            'lexical_errors': len(self.lexical_errors),
            'syntax_errors': len(self.syntax_errors),
            'semantic_errors': len(self.semantic_errors)
        }

    def print_compilation_summary(self) -> None:
        """Print a summary of the compilation process and any errors."""
        total_errors = len(self.lexical_errors) + len(self.syntax_errors) + len(self.semantic_errors)
        
        print("\n" + "=" * 50)
        print("Compilation Summary")
        print("=" * 50)
        
        print(f"Lexical Errors: {len(self.lexical_errors)}")
        print(f"Syntax Errors: {len(self.syntax_errors)}")
        print(f"Semantic Errors: {len(self.semantic_errors)}")
        print(f"Total Errors: {total_errors}")
        
        if self.debug and total_errors > 0:
            self._print_error_details()
        
        if total_errors == 0:
            print("\nCompilation completed successfully!")
            self.logger.info("Compilation completed successfully!")
        else:
            print("\nCompilation failed due to errors.")
            self.logger.error(f"Compilation failed with {total_errors} total errors.")

    def _print_error_details(self) -> None:
        """Print detailed error information when in debug mode."""
        if self.lexical_errors:
            print("\nLexical Errors:")
            print("-" * 20)
            for i, error in enumerate(self.lexical_errors[:5], 1):
                print(f"{i}. {error.get('message', 'Unknown error')}")
            if len(self.lexical_errors) > 5:
                print(f"...and {len(self.lexical_errors) - 5} more lexical errors")
        
        if self.syntax_errors:
            print("\nSyntax Errors:")
            print("-" * 20)
            for i, error in enumerate(self.syntax_errors[:5], 1):
                print(f"{i}. {error.get('message', 'Unknown error')}")
            if len(self.syntax_errors) > 5:
                print(f"...and {len(self.syntax_errors) - 5} more syntax errors")
        
        if self.semantic_errors:
            print("\nSemantic Errors:")
            print("-" * 20)
            for i, error in enumerate(self.semantic_errors[:5], 1):
                print(f"{i}. {error.get('message', 'Unknown error')}")
            if len(self.semantic_errors) > 5:
                print(f"...and {len(self.semantic_errors) - 5} more semantic errors") 