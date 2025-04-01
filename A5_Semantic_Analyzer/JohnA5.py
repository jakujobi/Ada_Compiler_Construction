#!/usr/bin/env python3
# JohnA5.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-03-31
# Version: 1.0
"""
Driver program for Assignment 5: Semantic Analysis for Ada Compiler

This program coordinates the following compilation phases:
1. Lexical Analysis: Tokenizes the source code using LexicalAnalyzer
2. Syntax Analysis: Parses the tokens using RDParser 
3. Semantic Analysis: Performs semantic actions including:
    - Symbol table management (inserting variables, constants, procedures)
    - Type checking
    - Offset calculation
    - Duplicate declaration detection

Usage:
    python JohnA5.py <source_file>

The program will prompt the user to activate the "stop on error" option.
If activated, the program will stop at the first semantic error.
Otherwise, it will continue processing and report all errors at the end.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import traceback
from prettytable import PrettyTable

# Add the parent directory to the path so we can import modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

# Import modules
from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.RDParser import RDParser, ParseTreeNode
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter, TableEntry
from Modules.FileHandler import FileHandler
from Modules.Logger import Logger
from Modules.SemanticAnalyzer import SemanticAnalyzer

class JohnA5:
    @classmethod    
    def from_args(cls, args):
        """
        Create a JohnA5 instance from command line arguments.
        
        Parameters:
            args (list): Command line arguments (excluding script name)
        
        Returns:
            JohnA3: Instance of JohnA3
        """
        logger = Logger(log_level_console=logging.INFO)
        logger.info("Starting JohnA3 program.")
        logger.debug("Checking command line arguments.")
        
        if len(args) == 2:
            input_file, output_file = args
            logger.debug(f"Input file: {input_file}, Output file: {output_file}")
            return cls(input_file, output_file)
        elif len(args) == 1:
            input_file = args[0]
            logger.debug(f"Input file: {input_file}")
            return cls(input_file)
        else:
            print("Usage: python JohnA5.py <input_file> [output_file]")
            logger.critical("Invalid number of arguments. Exiting program.")
            sys.exit(1)

    # def from_args(cls, args):
    #     """
    #     Create a JohnA5 instance from command line arguments.
        
    #     Parameters:
    #         args (list): Command line arguments (excluding script name)
        
    #     Returns:
    #         JohnA5: Instance of JohnA5
    #     """
    #     logger = Logger()
    #     logger.info("Starting JohnA5 program.")
    #     logger.debug("Checking command line arguments.")
        
    #     # Set up argument parser
    #     parser = argparse.ArgumentParser(description="Semantic analyzer for Ada compiler")
    #     parser.add_argument("source_file", help="Path to the Ada source file")
    #     parser.add_argument("--debug", action="store_true", help="Enable debug output")
    #     parser.add_argument("--print-tree", action="store_true", help="Print the parse tree")
        
    #     # Parse command line arguments
    #     parsed_args = parser.parse_args(args)
        
    #     # Create instance with parsed arguments
    #     return cls(parsed_args.source_file, debug=parsed_args.debug, print_tree=parsed_args.print_tree)

    def __init__(self, input_file_name: str, debug: bool = False, print_tree: bool = False):
        """
        Initialize the JohnA5 object.

        Parameters:
            input_file_name (str): Name/path of the source code file to process.
            debug (bool): Whether to enable debug output.
            print_tree (bool): Whether to print the parse tree.
        """
        # Get the shared logger instance
        self.logger = Logger()
        self.input_file_name = input_file_name
        self.debug = debug
        self.print_tree = print_tree

        # Initialize components
        self.logger.debug("Initializing FileHandler and other components.")
        self.file_handler = FileHandler()
        self.lexical_analyzer = None
        self.parser = None
        self.semantic_analyzer = None
        self.symbol_table = None

        # Initialize data
        self.source_code = None
        self.tokens = []
        self.stop_on_error = False
        
        # Results
        self.lexical_errors = []
        self.syntax_errors = []
        self.semantic_errors = []

        # Start the process
        self.run()

    def run(self):
        """
        Main function to run the JohnA5 process.
        
        Coordinates all the compilation phases:
        1. Lexical Analysis
        2. Syntax Analysis
        3. Semantic Analysis
        """
        self.logger.debug("Starting run() method.")
        
        # Read the source file
        self.read_source_file()
        
        # Print the source code
        self.print_source_code()
        
        # Prompt for stop_on_error option
        self.prompt_stop_on_error()
        
        # Run the compilation phases
        if self.source_code:
            self.stage1_lexical_analysis()
            self.stage2_syntax_analysis()
            self.stage3_semantic_analysis()
            self.print_compilation_summary()
        else:
            self.logger.error("No source code to process.")
            print("No source code to process.")
            sys.exit(1)

    def read_source_file(self):
        """
        Read the contents of the source file.
        """
        self.logger.debug(f"Reading source code from file: {self.input_file_name}")
        try:
            # Use read_file_as_string instead of read_file to get a string rather than a list
            self.source_code = self.file_handler.read_file_as_string(self.input_file_name)
            self.logger.info(f"Successfully read file {self.input_file_name}")
        except FileNotFoundError:
            self.logger.critical(f"Error: File '{self.input_file_name}' not found.")
            print(f"Error: File '{self.input_file_name}' not found.")
            sys.exit(1)
        except Exception as e:
            self.logger.critical(f"Error reading file: {str(e)}")
            print(f"Error reading file: {str(e)}")
            sys.exit(1)

    def print_source_code(self):
        """
        Print the source code to the console.
        """
        if not self.source_code:
            self.logger.warning("No source code to print.")
            return
            
        print("\nSource Code:")
        print("-" * 50)
        print(self.source_code)
        print("-" * 50)
        self.logger.debug("Source code printed to console.")

    def prompt_stop_on_error(self):
        """
        Prompt the user to decide whether to stop on the first semantic error.
        """
        response = input("Activate stop on error? Press 'y' to activate, or just hit Enter to leave it deactivated: ")
        self.stop_on_error = response.lower() == 'y'
        self.logger.info(f"Stop on error: {self.stop_on_error}")

    def stage1_lexical_analysis(self):
        """
        Stage 1: Lexical Analysis
        
        Tokenize the source code using the LexicalAnalyzer.
        """
        print("\nPhase 1: Lexical Analysis")
        print("-" * 50)
        
        self.lexical_analyzer = LexicalAnalyzer(self.stop_on_error)
        
        try:
            self.tokens = self.lexical_analyzer.analyze(self.source_code)
            self.lexical_errors = self.lexical_analyzer.errors
            
            # Process tokens to convert reserved words to uppercase
            self.normalize_tokens()
            
            if self.tokens:
                print(f"Generated {len(self.tokens)} tokens")
                if self.debug:
                    for token in self.tokens[:10]:  # Show first 10 tokens
                        print(f"  {token}")
                    if len(self.tokens) > 10:
                        print(f"  ... and {len(self.tokens) - 10} more")
            else:
                print("No tokens generated. Check for lexical errors.")
                
            if self.lexical_errors:
                print(f"Found {len(self.lexical_errors)} lexical errors")
                if self.debug:
                    for error in self.lexical_errors[:5]:  # Show first 5 errors
                        print(f"  Line {error.get('line', 'unknown')}, "
                              f"Column {error.get('column', 'unknown')}: {error.get('message', 'Unknown error')}")
                    if len(self.lexical_errors) > 5:
                        print(f"  ... and {len(self.lexical_errors) - 5} more")
                        
            self.logger.debug("Stage 1 complete.")
        except Exception as e:
            self.logger.critical(f"An error occurred during lexical analysis: {str(e)}")
            print(f"Error during lexical analysis: {str(e)}")
            if self.debug:
                traceback.print_exc()
            sys.exit(1)

    def normalize_tokens(self):
        """
        Process tokens after lexical analysis to ensure compatibility with RDParser.
        
        This function normalizes tokens by:
        1. Converting reserved words to uppercase
        2. Ensuring token type names are uppercase
        """
        definitions = Definitions()
        reserved_words_upper = {k.upper(): v for k, v in definitions.reserved_words.items()}
        
        for token in self.tokens:
            # Check if the lexeme (case-insensitive) matches any reserved word
            upper_lexeme = token.lexeme.upper()
            if upper_lexeme in reserved_words_upper:
                # Update token type to be the reserved word type
                token.token_type = reserved_words_upper[upper_lexeme]
                # Update lexeme to be uppercase (for consistent display)
                token.lexeme = upper_lexeme
                self.logger.debug(f"Token {token.lexeme} normalized to reserved word {upper_lexeme}")
            
            # We also need to ensure the first token has the right type for the program
            if token.line_number == 1 and token.column_number == 1 and token.lexeme.upper() == "PROCEDURE":
                token.lexeme = "PROCEDURE"
                token.token_type = definitions.TokenType.PROCEDURE
                self.logger.debug(f"First token normalized to PROCEDURE")
        
        self.logger.debug("Token normalization complete.")

    def stage2_syntax_analysis(self):
        """
        Stage 2: Syntax Analysis
        
        Parse the tokens using the RDParser.
        """
        if not self.tokens:
            self.logger.error("No tokens to parse.")
            print("No tokens to parse. Skipping syntax analysis.")
            return
            
        print("\nPhase 2: Syntax Analysis")
        print("-" * 50)
        
        try:
            # Create parser
            definitions = Definitions()
            self.parser = RDParser(self.tokens, definitions, 
                                  self.stop_on_error, 
                                  panic_mode_recover=True, 
                                  build_parse_tree=True)
            
            # Parse the tokens
            parsing_successful = self.parser.parse()
            self.syntax_errors = self.parser.errors
            
            if parsing_successful:
                print("Parsing completed successfully")
            else:
                print(f"Parsing failed with {len(self.syntax_errors)} errors")
                if self.debug:
                    for error in self.syntax_errors[:5]:  # Show first 5 errors
                        print(f"  Line {error.get('line', 'unknown')}, "
                              f"Column {error.get('column', 'unknown')}: {error.get('message', 'Unknown error')}")
                    if len(self.syntax_errors) > 5:
                        print(f"  ... and {len(self.syntax_errors) - 5} more")
            
            # Print parse tree if requested
            if self.print_tree and self.parser.parse_tree_root:
                self.print_parse_tree(self.parser.parse_tree_root)
                
            self.logger.debug("Stage 2 complete.")
        except Exception as e:
            self.logger.critical(f"An error occurred during syntax analysis: {str(e)}")
            print(f"Error during syntax analysis: {str(e)}")
            if self.debug:
                traceback.print_exc()
            sys.exit(1)

    def stage3_semantic_analysis(self):
        """
        Stage 3: Semantic Analysis
        
        Perform semantic analysis on the parse tree.
        """
        if not hasattr(self.parser, 'parse_tree_root') or not self.parser.parse_tree_root:
            self.logger.error("No parse tree to analyze.")
            print("No parse tree to analyze. Skipping semantic analysis.")
            return
            
        print("\nPhase 3: Semantic Analysis")
        print("-" * 50)
        
        try:
            # Create symbol table
            self.symbol_table = AdaSymbolTable()
            print(f"Created symbol table with size {self.symbol_table.table_size}")
            
            # Create semantic analyzer
            self.semantic_analyzer = SemanticAnalyzer(self.symbol_table, self.stop_on_error)
            
            # Perform semantic analysis
            analysis_successful = self.semantic_analyzer.analyze_parse_tree(self.parser.parse_tree_root)
            self.semantic_errors = self.semantic_analyzer.errors
            
            if analysis_successful:
                print("Semantic analysis completed successfully")
            else:
                print(f"Semantic analysis failed with {len(self.semantic_errors)} errors")
                
            # Print the symbol table
            self.semantic_analyzer.print_symbol_table()
            
            # Print semantic errors
            self.semantic_analyzer.print_errors()
            
            self.logger.debug("Stage 3 complete.")
        except Exception as e:
            self.logger.critical(f"An error occurred during semantic analysis: {str(e)}")
            print(f"Error during semantic analysis: {str(e)}")
            if self.debug:
                traceback.print_exc()
            sys.exit(1)

    def print_compilation_summary(self):
        """
        Print a summary of all errors found during compilation.
        """
        total_errors = len(self.lexical_errors) + len(self.syntax_errors) + len(self.semantic_errors)
        
        print("\n" + "=" * 50)
        print("Compilation Summary")
        print("=" * 50)
        
        print(f"Lexical Errors: {len(self.lexical_errors)}")
        print(f"Syntax Errors: {len(self.syntax_errors)}")
        print(f"Semantic Errors: {len(self.semantic_errors)}")
        print(f"Total Errors: {total_errors}")
        
        if total_errors == 0:
            print("\nCompilation completed successfully!")
        else:
            print("\nCompilation failed due to errors.")

    def print_parse_tree(self, root: ParseTreeNode, semantic_info: bool = False):
        """
        Print the parse tree with ASCII art.
        
        Args:
            root: Root node of the parse tree
            semantic_info: Whether to include semantic information in the output
        """
        def _print_node(node, prefix="", is_last=True):
            # Choose the appropriate connector
            connector = "└── " if is_last else "├── "
            
            # Print the current node
            node_info = f"{node.name}"
            if node.token:
                node_info += f" ({node.token.lexeme})"
            
            # Add semantic info if available and requested
            if semantic_info and hasattr(node, 'semantic_info') and node.semantic_info:
                node_info += f" {node.semantic_info}"
                
            print(prefix + connector + node_info)
            
            # Prepare the prefix for children
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            # Print children
            if node.children:
                for i, child in enumerate(node.children):
                    is_last_child = (i == len(node.children) - 1)
                    _print_node(child, new_prefix, is_last_child)
        
        print("\nParse Tree:")
        _print_node(root)

def main():
    """Main entry point that creates JohnA5 instance from command line args."""
    JohnA5.from_args(sys.argv[1:])

if __name__ == "__main__":
    main()