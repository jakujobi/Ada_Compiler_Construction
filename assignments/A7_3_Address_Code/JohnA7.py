#!/usr/bin/env python3
# JohnA7.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-04-27 # Updated Date
# Version: 1.0
"""
Driver program for Assignment 7: Three Address Code Generator for Ada Compiler

This program generates three address code from the parsed AST by:
1. Running Lexical Analysis
2. Running Syntax Analysis (using RDParserExtended)
3. Driving the TACGenerator during parsing (handled by RDParserExtended)
4. Writing the generated TAC to an output file.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import traceback

# Adjust import path based on where this script is run relative to the src directory
# If run from the project root (Ada_Compiler_Construction/):
script_dir = Path(__file__).parent.parent.parent # Go up 3 levels to project root
sys.path.insert(0, str(script_dir))

try:
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
except ImportError as e:
    print(f"Error importing modules: {e}", file=sys.stderr)
    print("Ensure the script is run from the project root directory or PYTHONPATH is set.", file=sys.stderr)
    sys.exit(1)

class JohnA7Driver(BaseDriver):
    """Driver specifically for Assignment 7, enabling TAC generation."""
    def __init__(self,
                 input_file_name: str,
                 output_file_name: Optional[str] = None, # For non-TAC output if needed
                 tac_output_filename: Optional[str] = None,
                 debug: bool = False,
                 logger: Optional[Logger] = None):
        """
        Initializes the A7 driver, forcing extended parser and TAC generation.
        """
        super().__init__(
            input_file_name=input_file_name,
            output_file_name=output_file_name, # Pass along original output if used
            debug=debug,
            logger=logger,
            use_extended_parser=True, # A7 requires the extended parser
            use_tac_generator=True,   # A7 requires TAC generation
            tac_output_filename=tac_output_filename # Pass specific TAC filename if provided
        )
        self.logger.info("JohnA7Driver initialized (Extended Parser & TAC Gen Enabled).")

    def run_pipeline(self, stop_on_syntax_error: bool = True, panic_mode: bool = True) -> None:
        """Runs the full compilation pipeline for A7: Lex -> Syntax -> TAC Write."""
        try:
            self.logger.info(f"Starting A7 compilation for: {self.input_file_name}")
            self.run_lexical()
            if self.lexical_errors:
                self.logger.error("Lexical errors detected. Stopping pipeline.")
                return # Stop if lexical errors

            # Run syntax, which will also drive TAC generation via callbacks
            # build_parse_tree might be needed depending on how TAC actions are implemented in parser
            syntax_ok = self.run_syntax(
                stop_on_error=stop_on_syntax_error,
                panic_mode_recover=panic_mode,
                build_parse_tree=True # Assume needed for TAC generation context
            )

            if not syntax_ok or self.syntax_errors:
                self.logger.error("Syntax errors detected. TAC generation likely incomplete. Skipping TAC write.")
                return # Stop if syntax errors

            # Write the generated TAC file
            tac_write_ok = self.run_tac_write()
            if not tac_write_ok:
                 self.logger.error("Errors occurred during TAC file writing.")

            self.logger.info("A7 compilation pipeline finished.")

        except FileNotFoundError:
            self.logger.critical(f"Input file not found: {self.input_file_name}. Aborting.")
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred during the A7 pipeline: {e}")
            self.logger.critical(traceback.format_exc())
        finally:
            # Always print summary regardless of exceptions
            self.print_compilation_summary()

def main():
    """Main function to parse arguments and run the JohnA7Driver."""
    parser = argparse.ArgumentParser(description="JakADaC Assignment 7 Driver - Three Address Code Generator")
    parser.add_argument("input_file", help="Path to the Ada source file (.ada)")
    parser.add_argument("-o", "--output", help="Optional: Path for the generated TAC file (defaults to <input_file_base>.tac)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable detailed debug logging")
    # Add other args if needed (e.g., symbol table output?)
    args = parser.parse_args()

    # Configure Logger
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = Logger(log_level_console=log_level)

    # Instantiate and run the driver
    driver = JohnA7Driver(
        input_file_name=args.input_file,
        tac_output_filename=args.output, # Pass the specific TAC output filename if provided
        debug=args.debug,
        logger=logger
    )

    driver.run_pipeline()

if __name__ == "__main__":
    main()

