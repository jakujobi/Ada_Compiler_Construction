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

from .Token import Token
from .Definitions import Definitions
from .Logger import Logger
from .LexicalAnalyzer import LexicalAnalyzer
from .FileHandler import FileHandler
from .RDParser import RDParser
from .RDParserExtended import RDParserExtended
from .TACGenerator import TACGenerator


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
        logger: Optional[Logger] = None,
        use_extended_parser: bool = False,
        use_tac_generator: bool = False,
        tac_output_filename: Optional[str] = None
    ):
        """
        Initialize the base driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            logger: Optional logger instance to use
            use_extended_parser: Whether to use the extended RDParser
            use_tac_generator: Whether to enable TAC generation
            tac_output_filename: Optional path for the TAC output file (defaults to <input>.tac)
        """
        # Use provided logger or create a new one
        self.logger = logger if logger is not None else Logger(log_level_console=logging.INFO)
        
        # Store file paths
        self.input_file_name = Path(input_file_name)
        self.output_file_name = output_file_name
        self.tac_output_filename = tac_output_filename
        
        # Set debug mode
        self.debug = debug
        
        # Initialize common components
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        
        # Initialize data storage
        self.source_code: Optional[str] = None
        self.tokens: List[Token] = []
        
        # Phase run flags for modular summary
        self.ran_lexical = False
        self.ran_syntax = False
        self.ran_semantic = False
        self.ran_tac_write = False
        
        # Initialize error tracking
        self.lexical_errors: List[Dict[str, Any]] = []
        self.syntax_errors: List[Dict[str, Any]] = []
        self.semantic_errors: List[Dict[str, Any]] = []
        self.tac_errors: List[Dict[str, Any]] = []
        # Parser selection flag
        self.use_extended_parser = use_extended_parser
        # Initialize parser attribute to None
        self.parser: Optional[RDParser | RDParserExtended] = None
        # Initialize TAC Generator (conditionally)
        self.use_tac_generator = use_tac_generator
        self.tac_generator: Optional[TACGenerator] = None

        if self.use_tac_generator:
            if self.tac_output_filename is None:
                # Default TAC output filename is <input_base>.tac
                self.tac_output_filename = self.input_file_name.with_suffix('.tac')
            else:
                # Use the provided specific TAC output filename
                self.tac_output_filename = Path(self.tac_output_filename)

            self.logger.info(f"TAC Generation enabled. Output will be written to: {self.tac_output_filename}")
            self.tac_generator = TACGenerator(str(self.tac_output_filename))
        else:
            self.logger.info("TAC Generation disabled.")

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
            # Mark that lexical phase was run
            self.ran_lexical = True
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
            'semantic_errors': len(self.semantic_errors),
            'tac_errors': len(self.tac_errors)
        }

    def print_compilation_summary(self) -> None:
        """Print a summary of the compilation process and any errors."""
        # Print a simple summary of each phase
        print("\nCompilation Summary")
        print("---------------------")
        total_errors = 0
        phases = [
            ("Lexical", self.ran_lexical, len(self.lexical_errors)),
            ("Syntax", self.ran_syntax, len(self.syntax_errors)),
            ("Semantic", self.ran_semantic, len(self.semantic_errors)),
            ("TAC Write", self.ran_tac_write, len(self.tac_errors))
        ]
        for phase, ran, errs in phases:
            status = "Done" if ran else "Skipped"
            print(f"{phase:<10}: {status:<7} | Errors: {errs}")
            if ran:
                total_errors += errs
        print("---------------------")
        print(f"Total Errors: {total_errors}")
        if total_errors == 0:
            print("Compilation completed successfully!")
            self.logger.info("Compilation completed successfully!")
        else:
            print("Compilation failed due to errors.")
            self.logger.error(f"Compilation failed with {total_errors} total errors.")
            # Always show detailed errors if any occurred
            self._print_error_details()

    def _print_error_details(self) -> None:
        """Print detailed error information for all phases in a consolidated list."""
        all_errors = []
        # Collect all errors with their type
        for error in self.lexical_errors:
            all_errors.append(("Lexical", error))
        for error in self.syntax_errors:
            all_errors.append(("Syntax", error))
        for error in self.semantic_errors:
            all_errors.append(("Semantic", error))
        for error in self.tac_errors:
            all_errors.append(("TAC", error))

        if not all_errors:
            return # No errors to print

        print("\nError Details:")
        print("--------------")
        for i, (err_type, error) in enumerate(all_errors, 1):
            message = "Unknown Error"
            location = ""
            
            # Robustly handle dict, str, or other error types
            if isinstance(error, dict):
                # Attempt to extract message and location from dict
                message = error.get('message', message)
                line = error.get('line', None)
                col = error.get('column', None)
                if line is not None and line != -1 and col is not None and col != -1:
                    location = f" (Line {line}, Col {col})"
            elif isinstance(error, str):
                # Use the string directly as the message
                message = error
            else:
                # Handle unexpected error types
                message = f"Unexpected error format: {type(error)} - {str(error)}"

            print(f"{i}. [{err_type}]{location}: {message}")
        print("--------------")

    def run_lexical(self) -> None:
        """
        Run the lexical analysis phase (read source, tokenize, format output).
        """
        self.get_source_code_from_file()
        self.process_tokens()
        self.format_and_output_tokens()

    def run_syntax(self, stop_on_error: bool = False, panic_mode_recover: bool = False, build_parse_tree: bool = False) -> bool:
        """
        Run the syntax analysis phase (recursive descent parser).
        Returns True if parsing succeeded, False otherwise.
        If `use_extended_parser` was set, uses RDParserExtended instead of RDParser.
        """
        # Ensure lexical analysis has been run
        if not self.ran_lexical:
            self.logger.info("Tokens not found; running lexical analysis before syntax.")
            self.run_lexical()
        if not self.tokens:
            self.logger.error("No tokens available for syntax analysis after lexical phase.")
            return False
        self.ran_syntax = True
        self.logger.info("Starting syntax analysis.")
        # Choose parser implementation
        if self.use_extended_parser:
            self.logger.info("Using extended RDParser for syntax analysis.")
            # Placeholder for SymbolTable, needs proper instantiation if required by RDParserExtended
            # symbol_table = None
            # Pass tac_generator if it exists
            parser_kwargs = {
                'tokens': self.tokens,
                'defs': self.lexical_analyzer.defs,
                'symbol_table': None, # Placeholder, needs proper instantiation
                'stop_on_error': stop_on_error,
                'panic_mode_recover': panic_mode_recover,
                'build_parse_tree': build_parse_tree
            }
            if self.tac_generator:
                # RDParserExtended needs to be updated to accept this argument
                parser_kwargs['tac_generator'] = self.tac_generator
                self.logger.debug("Passing TACGenerator instance to RDParserExtended.")

            # TODO: Update RDParserExtended.__init__ signature to accept tac_generator
            self.parser = RDParserExtended(**parser_kwargs)
        else:
            self.parser = RDParser(
                self.tokens,
                self.lexical_analyzer.defs,
                stop_on_error=stop_on_error,
                panic_mode_recover=panic_mode_recover,
                build_parse_tree=build_parse_tree
            )
        success = self.parser.parse()
        self.syntax_errors = self.parser.errors
        # Optionally print parse tree
        if build_parse_tree and hasattr(self.parser, 'parse_tree_root') and self.parser.parse_tree_root:
            self.parser.print_parse_tree()
        return success

    def run_semantic(self) -> None:
        """
        Run the semantic analysis phase.
        """
        # Ensure syntax analysis has been run
        if not self.ran_syntax:
            self.logger.info("Syntax not yet run; running syntax analysis before semantic.")
            # build parse tree by default for semantic
            self.run_syntax(build_parse_tree=True)
        # Mark that semantic phase was run (to be extended by assignments)
        self.ran_semantic = True
        self.logger.info("Semantic analysis phase is not yet implemented.")

    def run_tac_write(self) -> bool:
        """
        Run the TAC writing phase.
        This assumes the parser has already driven the TACGenerator to emit instructions.
        Returns True if writing succeeded without errors, False otherwise.
        """
        if not self.use_tac_generator or self.tac_generator is None:
            self.logger.info("TAC generation was not enabled, skipping TAC write phase.")
            return True # Not an error if TAC wasn't requested

        if not self.ran_syntax:
            self.logger.error("Cannot write TAC output: Syntax analysis phase did not run or failed.")
            # Optionally add an error to tac_errors or rely on syntax_errors
            return False

        if self.syntax_errors:
             self.logger.warning(f"Skipping TAC write due to {len(self.syntax_errors)} syntax errors.")
             return False

        self.logger.info(f"Starting TAC write phase to {self.tac_output_filename}.")
        self.ran_tac_write = True # Mark phase as attempted
        try:
            # The parser should have called emitProgramStart during parsing.
            # We just need to call writeOutput here.
            self.tac_generator.writeOutput()
            self.logger.info("TAC write phase completed successfully.")
            return True
        except RuntimeError as e:
            # Likely caused by start_proc_name not being set by parser
            self.logger.error(f"TAC write failed: {e}")
            self.tac_errors.append({"message": str(e), "type": "RuntimeError"})
            return False
        except IOError as e:
            self.logger.error(f"TAC write failed due to file I/O error: {e}")
            self.tac_errors.append({"message": str(e), "type": "IOError"})
            return False
        except Exception as e:
            # Catch any other unexpected errors during write
            self.logger.error(f"An unexpected error occurred during TAC write: {e}")
            self.tac_errors.append({"message": str(e), "type": "UnexpectedError"})
            return False 