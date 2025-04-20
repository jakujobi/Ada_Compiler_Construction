#!/usr/bin/env python3
# JohnA5.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.0
"""
Driver program for Assignment 5: Semantic Analysis for Ada Compiler

This program demonstrates the complete compilation process:
1. Lexical Analysis: Tokenizes the source code
2. Syntax Analysis: Parses the tokens using a recursive descent parser
3. Semantic Analysis: Performs semantic checks and builds symbol table

Usage:
    python JohnA5.py <input_file> [output_file]
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the parent directory to the path so we can import modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Driver import BaseDriver
from Modules.Logger import Logger
from Modules.RDParser import RDParser, ParseTreeNode
from Modules.AdaSymbolTable import AdaSymbolTable
from Modules.SemanticAnalyzer import SemanticAnalyzer


class JohnA5(BaseDriver):
    """
    Driver class for Assignment 5: Semantic Analysis
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
        Initialize the JohnA5 driver.

        Args:
            input_file_name: Path to the input source file
            output_file_name: Optional path to the output file
            debug: Whether to enable debug mode
            print_tree: Whether to print the parse tree
            logger: Optional logger instance to use
        """
        super().__init__(input_file_name, output_file_name, debug, logger)
        self.print_tree = print_tree
        self.parser: Optional[RDParser] = None
        self.symbol_table: Optional[AdaSymbolTable] = None
        self.semantic_analyzer: Optional[SemanticAnalyzer] = None
        self.run()

    def run(self) -> None:
        """
        Main function to run the compilation process.
        
        It:
            1. Reads the source file
            2. Prints the source code
            3. Performs lexical analysis
            4. Performs syntax analysis
            5. Performs semantic analysis
            6. Prints compilation summary
        """
        self.logger.info("Starting compilation process.")
        
        try:
            self.get_source_code_from_file()
            self.print_source_code()
            
            if self.source_code:
                self.stage1_lexical_analysis()
                self.stage2_syntax_analysis()
                self.stage3_semantic_analysis()
                self.print_compilation_summary()
            else:
                self.logger.error("No source code to process.")
                sys.exit(1)
                
        except Exception as e:
            self.logger.critical(f"An error occurred during compilation: {str(e)}")
            if self.debug:
                traceback.print_exc()
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
            
            # Print parse tree if requested
            if self.print_tree and self.parser and hasattr(self.parser, 'parse_tree_root') and self.parser.parse_tree_root:
                self.print_parse_tree(self.parser.parse_tree_root)
                
            self.logger.info("Syntax analysis complete.")
            
        except Exception as e:
            self.logger.critical(f"An error occurred during syntax analysis: {str(e)}")
            if self.debug:
                traceback.print_exc()
            sys.exit(1)

    def stage3_semantic_analysis(self) -> None:
        """
        Stage 3: Semantic Analysis
        Perform semantic analysis on the parse tree.
        """
        if not self.parser or not hasattr(self.parser, 'parse_tree_root') or not self.parser.parse_tree_root:
            self.logger.error("No parse tree to analyze.")
            print("No parse tree to analyze. Skipping semantic analysis.")
            return
            
        print("\nPhase 3: Semantic Analysis")
        print("-" * 50)
        
        try:
            # Create symbol table
            self.symbol_table = AdaSymbolTable()
            self.logger.info(f"Created symbol table with size {self.symbol_table.table_size}")
            print(f"Created symbol table with size {self.symbol_table.table_size}")
            
            # Create semantic analyzer
            self.semantic_analyzer = SemanticAnalyzer(self.symbol_table, self.debug, logger=self.logger)
            self.logger.info("Created semantic analyzer")
            
            # Add 'type' attribute to parse tree nodes for compatibility with SemanticAnalyzer
            self._add_type_to_parse_tree(self.parser.parse_tree_root)
            
            # Log the parse tree being passed to semantic analyzer
            self.logger.info(f"Parse tree root node type: {getattr(self.parser.parse_tree_root, 'type', self.parser.parse_tree_root.name)}")
            
            # Perform semantic analysis
            self.logger.info("Starting semantic analysis...")
            analysis_successful = self.semantic_analyzer.analyze_parse_tree(self.parser.parse_tree_root)
            self.semantic_errors = self.semantic_analyzer.errors
            
            if analysis_successful:
                self.logger.info("Semantic analysis completed successfully")
                print("Semantic analysis completed successfully")
                
                # Print the symbol table
                print("\nSymbol Table Contents:")
                print("-" * 50)
                self.semantic_analyzer.print_symbol_table()
            else:
                self.logger.error(f"Semantic analysis failed with {len(self.semantic_errors)} errors")
                print(f"Semantic analysis failed with {len(self.semantic_errors)} errors")
                
                # Display detailed error information
                if self.debug:
                    self.semantic_analyzer.print_errors()
                    for error in self.semantic_errors[:5]:  # Show first 5 errors
                        print(f"  Line {error.get('line', 'unknown')}, "
                              f"Column {error.get('column', 'unknown')}: {error.get('message', 'Unknown error')}")
                    if len(self.semantic_errors) > 5:
                        print(f"  ... and {len(self.semantic_errors) - 5} more")
            
            # If we're requested to print the tree with semantic info, do it
            if self.print_tree and self.parser and self.parser.parse_tree_root:
                print("\nParse Tree with Semantic Information:")
                print("-" * 50)
                self.print_parse_tree(self.parser.parse_tree_root, semantic_info=True)
            
            self.logger.info("Semantic analysis complete.")
            
        except Exception as e:
            self.logger.critical(f"An error occurred during semantic analysis: {str(e)}")
            print(f"Error during semantic analysis: {str(e)}")
            if self.debug:
                traceback.print_exc()

    def _add_type_to_parse_tree(self, node: ParseTreeNode) -> None:
        """
        Recursively add 'type' attribute to ParseTreeNode objects.
        This makes the parse tree compatible with the SemanticAnalyzer,
        which expects nodes to have a 'type' attribute.
        
        Args:
            node: The current ParseTreeNode to process
        """
        if node is None:
            return
            
        # Add type attribute (copy from name)
        node.type = node.name
        
        # Process all children recursively
        for child in node.children:
            self._add_type_to_parse_tree(child)

    def print_parse_tree(self, root: ParseTreeNode, semantic_info: bool = False) -> None:
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
    """
    Main entry point for the semantic analyzer program.
    
    It:
        1. Initializes the Logger
        2. Checks command-line arguments
        3. Creates and runs a JohnA5 instance
    """
    # Initialize the Logger
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA5 program.")
    
    # Check command line arguments
    args = sys.argv[1:]
    if len(args) == 2:
        input_file, output_file = args
        logger.debug(f"Input file: {input_file}, Output file: {output_file}")
        JohnA5(input_file, output_file, debug=True, logger=logger)
    elif len(args) == 1:
        input_file = args[0]
        logger.debug(f"Input file: {input_file}")
        JohnA5(input_file, debug=True, logger=logger)
    else:
        print("Usage: python JohnA5.py <input_file> [output_file]")
        logger.critical("Invalid number of arguments. Exiting program.")
        sys.exit(1)


if __name__ == "__main__":
    main()