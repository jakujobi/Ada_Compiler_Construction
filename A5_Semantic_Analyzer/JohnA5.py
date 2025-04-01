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
import logging
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
    

    def __init__(self, input_file_name: str, output_file_name: str = None, debug: bool = False, print_tree: bool = True):
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
        self.output_file_name = output_file_name
        
        self.debug = debug
        self.print_tree = print_tree
        self.build_parse_tree = True
        self.panic_mode_recover = True
        self.stop_on_error = False

        self.logger.debug("Initializing FileHandler and LexicalAnalyzer.")
        # FileHandler is the helper class for file I/O.
        self.file_handler = FileHandler()
        # LexicalAnalyzer processes the source code into tokens.
        self.lexical_analyzer = LexicalAnalyzer()

        # Initialize components
        self.logger.debug("Initializing FileHandler and other components.")
        self.file_handler = FileHandler()

        # Initialize data
        self.source_code = None
        self.output_code = None
        self.tokens = []
        
        # Results
        self.logger.debug("Initializing lists for errors")
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
        self.logger.info("Starting run() method.")

        self.logger.info("Getting code from file")
        self.get_source_code_from_file(self.input_file_name)
        self.print_source_code()
        
        # Prompt for stop_on_error option
        #self.prompt_stop_on_error()
        
        # Run the compilation phases
        if self.source_code:
            self.logger.info("Going into stage 1")
            self.stage1_lexical_analysis()
            self.stage2_syntax_analysis()
            # self.stage3_semantic_analysis()
            # self.print_compilation_summary()
        else:
            self.logger.error("No source code to process.")
            print("No source code to process.")
            sys.exit(1)


# region stage1
    def stage1_lexical_analysis(self):
        if self.source_code:
            self.process_tokens()
            self.format_and_output_tokens()
            self.logger.info("Stage 1 complete.")
        else:
            # If there is no source code, we cannot proceed to the next stage.
            self.logger.error("No source code to process.")
            self.logger.critical("Stage 1 Lexical Analysis failed. Exiting program.")
            sys.exit(1)

    def get_source_code_from_file(self, input_file_name: str):
        """
        Read the source code from a file and store it in the source_code attribute.
        """
        self.logger.debug(f"Reading source code from file: {input_file_name}")
        try:
            with open(input_file_name, 'r') as file:
                self.source_code = file.read().strip()
            self.logger.debug("Source code read successfully.")
        except Exception as e:
            self.logger.critical(f"Error reading file: {str(e)}")
            raise

    def process_tokens(self):
        """
        Tokenize the source code using the LexicalAnalyzer.

        This method calls the analyze() function of the lexical analyzer, which returns
        a list of tokens. The tokens are then stored in the tokens attribute.
        """
        self.logger.debug("Processing tokens from source code.")
        try:
            self.tokens = self.lexical_analyzer.analyze(self.source_code)
        except ValueError as e:
            self.logger.error(f"Invalid token found: {e}")
        except Exception as e:
            self.logger.critical(f"An error occurred during tokenization: {e}")


    def print_source_code(self):
        """
        Print the source code to the console.
        
        If the source code could not be read, log a warning.
        """
        if not self.source_code:
            self.logger.warning("No source code to print.")
            return
        print(self.source_code)
        self.logger.debug("Source code printed to console.")

    def format_and_output_tokens(self):
        """
        Format the tokens into a table and output them to the console and file.

        This method builds a table-like string where each row represents a token,
        including its type, lexeme, and value. It then prints the table and writes it
        to an output file if an output file name was provided.
        """
        if not self.tokens:
            self.logger.warning("No tokens to format.")
            return

        # Create a header for the token table.
        header = f"{'Token Type':15} | {'Lexeme':24} | {'Value'}"
        separator = "-" * (len(header) + 10)
        table_lines = [header, separator]
        # For each token, format a row with its type, lexeme, and value.
        for token in self.tokens:
            # Get the token type name (without the TokenType prefix).
            token_type_name = token.token_type.name
            row = f"{token_type_name:15} | {token.lexeme:24} | {token.value}"
            self.logger.debug(f"Formatted token: {row}")
            table_lines.append(row)
        
        table_output = "\n".join(table_lines)
        print(table_output)
        self.logger.debug("Token table printed successfully.")

        self.print_tokens()
        # Write the token table to an output file if specified.
        if self.output_file_name:
            success = self.write_output_to_file(self.output_file_name, table_output)
            if success:
                self.logger.debug(f"Token table written to file: {self.output_file_name}")

    def write_output_to_file(self, output_file_name: str, content: str) -> bool:
        """
        Write the given content to a file.

        Parameters:
            output_file_name (str): The path of the file to write to.
            content (str): The string content to write.

        Returns:
            bool: True if writing was successful, False otherwise.
        """
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.debug(f"Content successfully written to {output_file_name}.")
            return True
        except Exception as e:
            self.logger.critical(f"An error occurred while writing to the file '{output_file_name}': {e}")
            return False

    def print_tokens(self):
        """
        Print the tokens to the console.
        """
        if not self.tokens:
            self.logger.warning("No tokens to print.")
            return
        for token in self.tokens:
            print(token)
        self.logger.debug("Tokens printed to console.")
# endregion


# region stage2
    def stage2_syntax_analysis(self):
        """
        Stage 2: Syntax Analysis
        
        Parse the tokens using the RDParser.
        """
        if not self.tokens:
            self.logger.error("There are no tokens to parse.")
            self.logger.critical("Stage 2 failed. Exiting program.")
            sys.exit(1)


        print("\nPhase 2: Syntax Analysis")
        print("-" * 50)
        
        try:
            # Parse the tokens
            parsing_successful = self.parse_with_RDparser()
            
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
            

    def parse_with_RDparser(self):
        self.logger.debug("Parsing Tokens with RDParser")
        self.parser = RDParser(self.tokens, self.lexical_analyzer.defs,
                                stop_on_error=False,
                                panic_mode_recover=False,
                                build_parse_tree=True)
        
        # Parse the tokens
        parsing_successful = self.parser.parse()
        self.syntax_errors = self.parser.errors
        
        self.logger.debug("Parsing complete.")
        return parsing_successful
# endregion


    def get_processing_status(self) -> dict:
        return {
            'tokens_count': len(self.tokens) if self.tokens else 0,
            'has_source': bool(self.source_code),
            'parsing_complete': hasattr(self, 'parsing_success') and self.parsing_success
        }

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