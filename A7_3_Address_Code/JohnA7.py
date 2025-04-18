#!/usr/bin/env python3
# JohnA7.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-18
# Version: 1.0
"""
Driver program for Assignment 7: Three Address Code Generation

This program extends JohnA6 by adding a Three Address Code generation phase.
It includes:
1. Lexical analysis
2. Parsing
3. Symbol table creation
4. Semantic analysis
5. Three Address Code generation

Output: .TAC file with the same base name as the input file
"""

import os
import sys
import argparse
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path so we can import modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

# Import required modules
from Modules.Driver import BaseDriver
from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.FileHandler import FileHandler
from Modules.RDParserExtended import RDParserExtended, ParseTreeNode
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType
from Modules.Logger import Logger
from Modules.SemanticAnalyzer import SemanticAnalyzer
from Modules.ThreeAddressCodeGenerator import ThreeAddressCodeGenerator, TACProgram


class JohnA7(BaseDriver):
    """
    Driver class for Assignment 7: Three Address Code Generation
    Inherits from BaseDriver to reuse common functionality
    """

    def __init__(
        self, 
        input_file_name: str, 
        output_file_name: Optional[str] = None, 
        debug: bool = False, 
        print_tree: bool = True, 
        logger: Optional[Logger] = None
    ):
        """
        Initialize the JohnA7 driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            print_tree: Whether to print the parse tree
            logger: Optional logger instance to use
        """
        # Call the parent class constructor
        super().__init__(input_file_name, output_file_name, debug, logger)
        
        # Additional settings
        self.print_tree = print_tree
        self.build_parse_tree = True
        self.panic_mode_recover = True
        self.stop_on_error = False

        # Initialize compilation components
        self.tokens = []
        self.parse_tree = None
        self.symbol_table = None
        self.tac_program = None

        # If no output file specified, use the same base name with .TAC extension
        if not self.output_file_name and self.input_file_name:
            base_name = os.path.splitext(os.path.basename(self.input_file_name))[0]
            output_dir = os.path.dirname(self.input_file_name)
            self.output_file_name = os.path.join(output_dir, base_name + '.TAC')
        
        # Start the compilation process
        self.run()

    def run(self):
        """
        Main method to run the compilation process.
        """
        try:
            self.logger.info(f"Starting compilation of {self.input_file_name}")
            self.logger.info(f"Output file will be: {self.output_file_name}")

            # Execute compilation phases
            if self.stage1_lexical_analysis() and \
               self.stage2_syntax_analysis() and \
               self.stage3_semantic_analysis() and \
               self.stage4_tac_generation():
                self.logger.info("Compilation completed successfully")
                return True
            else:
                self.logger.error("Compilation failed")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error during compilation: {e}")
            if self.debug:
                self.logger.error(traceback.format_exc())
            return False

    def stage1_lexical_analysis(self) -> bool:
        """
        Stage 1: Lexical Analysis
        """
        self.logger.info("Starting lexical analysis phase")

        # Read the source code
        source_code = self.read_source_code()
        if not source_code:
            return False

        # Tokenize the source code
        lexical_analyzer = LexicalAnalyzer()
        defs = Definitions()
        lexical_analyzer.defs = defs
        self.tokens = lexical_analyzer.analyze(source_code)

        # Check for lexical errors
        if lexical_analyzer.errors:
            for error in lexical_analyzer.errors:
                self.logger.error(f"Lexical error: {error}")
            return False

        self.logger.info(f"Lexical analysis completed successfully: {len(self.tokens)} tokens found")
        return True

    def stage2_syntax_analysis(self) -> bool:
        """
        Stage 2: Syntax Analysis
        """
        if not self.tokens:
            self.logger.error("There are no tokens to parse.")
            return False

        self.logger.info("Starting parsing phase")
        
        try:
            # Create the symbol table first (needed for semantic checks during parsing)
            self.symbol_table = AdaSymbolTable()
            self.logger.debug(f"Created symbol table with size {self.symbol_table.table_size}")
            
            # Get definitions from the first stage's lexical analyzer
            lexical_analyzer = LexicalAnalyzer()
            defs = Definitions()
            lexical_analyzer.defs = defs
            
            # Create the extended parser with symbol table
            parser = RDParserExtended(
                self.tokens, 
                defs,
                symbol_table=self.symbol_table,
                stop_on_error=self.stop_on_error,
                panic_mode_recover=self.panic_mode_recover, 
                build_parse_tree=self.build_parse_tree
            )
            
            # Parse the tokens
            success = parser.parse()
            
            if not success:
                self.logger.error("Parsing failed")
                return False
    
            # Get the parse tree
            self.parse_tree = parser.get_parse_tree()
    
            # Print the parse tree if requested
            if self.print_tree:
                parser.print_parse_tree()
    
            self.logger.info("Parsing completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"An error occurred during syntax analysis: {str(e)}")
            if self.debug:
                self.logger.error(traceback.format_exc())
            return False

    def stage3_semantic_analysis(self) -> bool:
        """
        Stage 3: Semantic Analysis
        """
        self.logger.info("Starting semantic analysis phase")

        # Create symbol table and semantic analyzer
        self.symbol_table = AdaSymbolTable()
        semantic_analyzer = SemanticAnalyzer(self.parse_tree, self.symbol_table, logger=self.logger)
        success = semantic_analyzer.analyze()

        if not success:
            self.logger.error("Semantic analysis failed")
            return False

        self.logger.info("Semantic analysis completed successfully")
        return True

    def stage4_tac_generation(self) -> bool:
        """
        Stage 4: Three Address Code Generation
        """
        self.logger.info("Starting Three Address Code generation phase")

        # Generate Three Address Code
        tac_generator = ThreeAddressCodeGenerator(self.parse_tree, self.symbol_table, logger=self.logger)
        self.tac_program = tac_generator.generate()

        self.logger.info("Three Address Code generation completed successfully")

        # Write the TAC to the output file
        self.logger.info(f"Writing Three Address Code to {self.output_file_name}")
        success = self.tac_program.write_to_file(self.output_file_name)

        if not success:
            self.logger.error(f"Failed to write TAC to file: {self.output_file_name}")
            return False

        self.logger.info(f"Three Address Code successfully written to {self.output_file_name}")
        return True

    def read_source_code(self) -> Optional[str]:
        """
        Read the source code from the input file.

        Returns:
            The source code as a string, or None if reading failed
        """
        try:
            with open(self.input_file_name, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read source file: {self.input_file_name} - {e}")
            return None


def main():
    """
    Main entry point for the program.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Ada Compiler Construction - Three Address Code Generation (A7)')
    parser.add_argument('input_file', help='Path to the input source file')
    parser.add_argument('-o', '--output', dest='output_file', help='Specify output file (default: input filename with .TAC extension)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-p', '--print-tree', action='store_true', help='Print the parse tree')
    args = parser.parse_args()

    # Set up logging level based on verbosity
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logger = Logger(log_level_console=log_level, source_name="JohnA7")

    # Create and run the JohnA7 driver
    driver = JohnA7(
        input_file_name=args.input_file,
        output_file_name=args.output_file,
        debug=args.debug,
        print_tree=args.print_tree,
        logger=logger
    )

    # Return appropriate exit code
    return 0 if driver else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
