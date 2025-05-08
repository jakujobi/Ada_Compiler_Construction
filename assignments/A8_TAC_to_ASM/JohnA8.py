#!/usr/bin/env python3
# JohnA7.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-04-27 # Updated Date
# Version: 1.0
"""
Driver program for Assignment 8: TAC to ASM Generator for Ada Compiler


"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
import traceback

# Adjust import path based on where this script is run relative to the src directory
# If run from the project root (Ada_Compiler_Construction/):
script_dir = Path(__file__).parent.parent.parent # Go up 3 levels to project root
sys.path.insert(0, str(script_dir))

try:
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
    # Import necessary components for A8
    from src.jakadac.modules.SymTable import SymbolTable # Need to instantiate this
    from src.jakadac.modules.RDParserExtExt import RDParserExtExt # Need the A7 parser
    from src.jakadac.modules.TACGenerator import TACGenerator # Need the TAC generator
    from src.jakadac.modules.asm_gen import ASMGenerator # Import the ASM Generator
    from src.jakadac.modules.RDParser import RDParser # For type hints
    from src.jakadac.modules.RDParserExtended import RDParserExtended # For type hints
except ImportError as e:
    print(f"Error importing modules: {e}", file=sys.stderr)
    print("Ensure the script is run from the project root directory or PYTHONPATH is set.", file=sys.stderr)
    sys.exit(1)

class JohnA8(BaseDriver):
    """Driver specifically for Assignment 8, enabling TAC generation."""
    def __init__(self,
                 input_file_name: str,
                 output_file_name: Optional[str] = None, # For non-TAC output if needed
                 tac_output_filename: Optional[str] = None,
                 asm_output_filename: Optional[str] = None, # ADDED for ASM output
                 debug: bool = False,
                 logger: Optional[Logger] = None):
        """
        Initializes the A8 driver, running TAC generation and then ASM generation.
        Also initializes the SymbolTable needed for RDParserExtExt.
        """
        # Instantiate SymbolTable *before* calling super().__init__
        # so it's available if BaseDriver needs it during init (it doesn't currently, but good practice)
        local_symbol_table = SymbolTable()
        self.logger = logger if logger is not None else Logger(log_level_console=logging.INFO) # Temp logger for init message

        # Call super().__init__, setting the appropriate flags and passing the symbol table
        super().__init__(
            input_file_name=input_file_name,
            output_file_name=output_file_name, # Not typically used in A7
            debug=debug,
            logger=self.logger, # Pass the potentially newly created logger
            use_extended_parser=False, # Not needed, use_tac_parser takes precedence
            use_tac_parser=True,       # Explicitly select RDParserExtExt
            use_tac_generator=True,    # Enable TAC generator logic and instantiation
            tac_output_filename=tac_output_filename,
            symbol_table=local_symbol_table # Pass the created symbol table
        )

        # Determine ASM output filename (default to <input_base>.asm if not provided)
        if asm_output_filename:
            self.asm_output_filename = Path(asm_output_filename)
        else:
            self.asm_output_filename = self.input_file_name.with_suffix('.asm')

        self.logger.info("JohnA8Driver initialized (RDParserExtExt + TAC Gen Enabled, SymbolTable created).")
        self.logger.info(f" Input Ada file: {self.input_file_name}")
        self.logger.info(f" Output TAC file: {self.tac_output_filename}")
        self.logger.info(f" Output ASM file: {self.asm_output_filename}") # Log ASM output path

    def run_pipeline(self, stop_on_syntax_error: bool = False, panic_mode: bool = True) -> None: # Changed stop_on_error default
        """Runs the full compilation pipeline for A8: Lex -> Syntax (with TAC gen) -> TAC Write -> ASM Gen."""
        try:
            self.logger.info(f"Starting A8 compilation for: {self.input_file_name}")
            # SymbolTable is now created in __init__ and assigned to self.symbol_table

            self.run_lexical()
            if self.lexical_errors:
                self.logger.error("Lexical errors detected. Stopping pipeline.")
                # self.print_compilation_summary() # Print summary even on early exit
                return # Stop if lexical errors

            # Run syntax. _create_parser in BaseDriver will now select RDParserExtExt
            # because use_tac_parser=True. RDParserExtExt will drive TAC generation.
            # Set build_parse_tree=False if TAC is the primary goal and tree isn't needed.
            # If RDParserExtExt relies on tree nodes sometimes, set it to True. Assume False for pure TAC.
            syntax_ok = self.run_syntax(
                stop_on_error=stop_on_syntax_error, # Use argument
                panic_mode_recover=panic_mode,      # Use argument
                build_parse_tree=False # Set to False for A7 focus on TAC
            )

            # Collect semantic errors reported by the parser
            # Check if the parser instance exists and has the semantic_errors attribute
            if self.parser and hasattr(self.parser, 'semantic_errors'):
                 # Check if the attribute is a list (basic type safety)
                 parser_semantic_errors = getattr(self.parser, 'semantic_errors')
                 if isinstance(parser_semantic_errors, list):
                     self.semantic_errors.extend(parser_semantic_errors)
                     # Mark semantic phase as 'run' conceptually since the parser does checks
                     if self.semantic_errors:
                          self.ran_semantic = True

            if not syntax_ok or self.syntax_errors or self.semantic_errors:
                 # Check syntax AND semantic errors before writing TAC
                 messages = []
                 if self.syntax_errors: messages.append("syntax errors")
                 if self.semantic_errors: messages.append("semantic errors")
                 # Ensure error_msg is not empty if only one type of error occurred
                 error_desc = " and ".join(messages) if messages else "errors"
                 self.logger.error(f"{error_desc.capitalize()} detected. TAC generation likely incomplete or incorrect. Skipping TAC write.")
                 # self.print_compilation_summary() # Print summary even on early exit
                 return # Stop if syntax or semantic errors

            # Write the generated TAC file
            tac_write_ok = self.run_tac_write()
            if not tac_write_ok:
                 self.logger.error("Errors occurred during TAC file writing. Skipping ASM generation.")
                 # self.print_compilation_summary() # Print summary even on early exit
                 return # Stop if TAC write failed

            # --- ADDED FOR A8: ASM Generation Phase ---
            self.logger.info("--- Starting Assembly Generation Phase ---")
            # Ensure TAC Generator exists and has the string definitions
            if not self.tac_generator or not hasattr(self.tac_generator, 'string_definitions'):
                 self.logger.error("TAC Generator or its string definitions are not available for ASM generation.")
                 # self.print_compilation_summary()
                 return

            # Ensure Symbol Table exists
            if not self.symbol_table:
                 self.logger.error("Symbol Table is not available for ASM generation.")
                 # self.print_compilation_summary()
                 return

            # Instantiate and run the ASM Generator
            try:
                 asm_gen = ASMGenerator(
                     tac_filepath=str(self.tac_output_filename),
                     asm_filepath=str(self.asm_output_filename),
                     symbol_table=self.symbol_table,
                     string_literals_map=self.tac_generator.string_definitions,
                     logger=self.logger
                 )
                 asm_gen_ok = asm_gen.generate_asm()
                 if asm_gen_ok:
                     self.logger.info(f"Assembly generation completed successfully. Output: {self.asm_output_filename}")
                 else:
                     self.logger.error("Assembly generation failed.")
                     # Optionally add specific ASM errors if collected by ASMGenerator
                     # self.asm_errors = asm_gen.errors 
            except Exception as asm_e:
                 self.logger.critical(f"An unexpected error occurred during Assembly Generation: {asm_e}")
                 self.logger.critical(traceback.format_exc())
            # --- END ADDED FOR A8 ---

            self.logger.info("A8 compilation pipeline finished.")

        except FileNotFoundError:
            self.logger.critical(f"Input file not found: {self.input_file_name}. Aborting.")
        except Exception as e:
            self.logger.critical(f"An unexpected error occurred during the A8 pipeline: {e}")
            self.logger.critical(traceback.format_exc())
        finally:
            # Always print summary regardless of exceptions
            self.print_compilation_summary()

def main():
    """Main function to parse arguments and run the JohnA8Driver."""
    parser = argparse.ArgumentParser(description="JakAdaC Assignment 8 Driver - TAC to ASM Generator")
    parser.add_argument("input_file", help="Path to the Ada source file (.ada)")
    parser.add_argument("-o", "--output", help="Optional: Path for the generated TAC file (defaults to <input_file_base>.tac)")
    parser.add_argument("-asm", "--asm_output", help="Optional: Path for the generated ASM file (defaults to <input_file_base>.asm)") # ADDED ASM output arg
    parser.add_argument("-d", "--debug", action="store_true", help="Enable detailed debug logging")
    # Add other args if needed (e.g., symbol table output?)
    args = parser.parse_args()

    # Configure Logger
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = Logger(log_level_console=log_level)

    # Instantiate and run the driver
    driver = JohnA8(
        input_file_name=args.input_file,
        tac_output_filename=args.output, # Pass the specific TAC output filename if provided
        asm_output_filename=args.asm_output, # Pass the specific ASM output filename if provided
        debug=args.debug,
        logger=logger
    )

    driver.run_pipeline()

if __name__ == "__main__":
    main()

