#!/usr/bin/env python3
# JohnA7.py - Driver for A7 (Three Address Code Generation)
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-18
# Version: 1.0
"""
Three Address Code Generator Driver (A7)

This module drives the Three Address Code generation phase of the Ada compiler.
It processes Ada source files, performs lexical analysis, parsing, semantic analysis,
and generates Three Address Code (TAC) as the final output.

It creates a TAC file with the same base name as the input file but with a .TAC extension.

Usage:
    python JohnA7.py <input_file>

    Example: python JohnA7.py ../../test_files/sample.ada
"""

import os
import sys
import time
from pathlib import Path

# Add the root directory to the path so we can import modules
repo_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(repo_home)

# Import modules from the Modules directory
from Modules.FileHandler import FileHandler
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.RDParserExtended import RDParserExtended
from Modules.SemanticAnalyzer import SemanticAnalyzer
from Modules.ThreeAddressCodeGenerator import ThreeAddressCodeGenerator
from Modules.AdaSymbolTable import AdaSymbolTable
from Modules.Logger import Logger
from Modules.Driver import BaseDriver


class JohnA7Driver(BaseDriver):
    """
    Driver for the Three Address Code Generation phase (A7) of the Ada compiler.
    
    This driver orchestrates the complete compilation pipeline:
    1. Lexical analysis to produce tokens
    2. Parsing to create an AST
    3. Semantic analysis to verify program correctness
    4. Three Address Code generation to produce intermediate code
    
    It outputs the Three Address Code to a .TAC file.
    """
    
    def __init__(self):
        """
        Initialize the driver with a logger and file handler.
        """
        super().__init__()
        self.logger = Logger()
        self.file_handler = FileHandler()
        self.lexical_analyzer = None
        self.parser = None
        self.semantic_analyzer = None
        self.tac_generator = None
        self.symbol_table = AdaSymbolTable()
    
    def run(self, input_file):
        """
        Run the complete compilation pipeline for the Three Address Code generation phase.
        
        Args:
            input_file: Path to the input Ada source file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Starting A7 - Three Address Code Generation for {input_file}")
            
            # Step 1: Read the input file
            if not os.path.exists(input_file):
                self.logger.error(f"Input file not found: {input_file}")
                return False
                
            source_code = self.file_handler.read_file(input_file)
            if not source_code:
                self.logger.error(f"Error reading input file: {input_file}")
                return False
                
            self.logger.info(f"Read {len(source_code)} characters from {input_file}")
            
            # Step 2: Lexical Analysis
            self.lexical_analyzer = LexicalAnalyzer()
            tokens = self.lexical_analyzer.tokenize(source_code)
            
            if not tokens:
                self.logger.error("Lexical analysis failed to produce tokens.")
                return False
                
            self.logger.info(f"Lexical analysis complete. Generated {len(tokens)} tokens.")
            
            # Step 3: Parsing
            self.parser = RDParserExtended(tokens, self.symbol_table, self.logger)
            parse_tree = self.parser.parse()
            
            if not parse_tree:
                self.logger.error("Parsing failed to produce a parse tree.")
                return False
                
            self.logger.info("Parsing complete. Parse tree generated.")
            
            # Step 4: Semantic Analysis
            self.semantic_analyzer = SemanticAnalyzer(parse_tree, self.symbol_table, self.logger)
            success = self.semantic_analyzer.analyze()
            
            if not success:
                self.logger.error("Semantic analysis failed.")
                return False
                
            self.logger.info("Semantic analysis complete. Program is semantically valid.")
            
            # Step 5: Three Address Code Generation
            self.tac_generator = ThreeAddressCodeGenerator(parse_tree, self.symbol_table, self.logger)
            tac_program = self.tac_generator.generate()
            
            if not tac_program:
                self.logger.error("Three Address Code generation failed.")
                return False
                
            self.logger.info("Three Address Code generation complete.")
            
            # Step 6: Write the TAC to a file
            output_file = self._get_output_filename(input_file)
            success = tac_program.write_to_file(output_file)
            
            if not success:
                self.logger.error(f"Error writing TAC to file: {output_file}")
                return False
                
            self.logger.info(f"Three Address Code written to {output_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in A7 Driver: {e}")
            return False
    
    def _get_output_filename(self, input_file):
        """
        Convert the input filename to the TAC output filename.
        
        Args:
            input_file: Path to the input Ada source file
            
        Returns:
            Path to the output TAC file
        """
        # Change the extension to .TAC
        path = Path(input_file)
        base_name = path.stem
        output_file = path.with_name(f"{base_name}.TAC")
        
        return str(output_file)


def main():
    """
    Main entry point for the A7 driver.
    
    Processes command-line arguments and runs the compilation pipeline.
    """
    if len(sys.argv) < 2:
        print("Usage: python JohnA7.py <input_file>")
        return
        
    input_file = sys.argv[1]
    driver = JohnA7Driver()
    
    start_time = time.time()
    success = driver.run(input_file)
    end_time = time.time()
    
    if success:
        print(f"\nA7 - Three Address Code Generation completed successfully in {end_time - start_time:.2f} seconds.")
    else:
        print("\nA7 - Three Address Code Generation failed. See log for details.")


if __name__ == "__main__":
    main()