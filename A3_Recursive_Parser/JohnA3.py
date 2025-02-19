# JohnA3.py
# A3 - Recursive Descent Parser
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-17
# Version: 1.0
# Description:


import os
import re
import sys
import logging
from typing import List, Optional
from pathlib import Path

# Setup the repository home path so that we can import modules from the parent directory.
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.RDParser import RDParser
from Modules.FileHandler import FileHandler

class JohnA3:
    @classmethod
    def from_args(cls, args):
        """
        Create a JohnA3 instance from command line arguments.
        
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
            print("Usage: python JohnA3.py <input_file> [output_file]")
            logger.critical("Invalid number of arguments. Exiting program.")
            sys.exit(1)

    def __init__(self, input_file_name: str, output_file_name: str = None):
        """
        Initialize the JohnA1 object.

        Parameters:
            input_file_name (str): Name/path of the source code file to process.
            output_file_name (str, optional): Name/path of the file where tokens will be written.
        """
        # Get the shared logger instance (Logger is a singleton).
        self.logger = Logger()
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name

        self.logger.debug("Initializing FileHandler and LexicalAnalyzer.")
        # FileHandler is assumed to be a helper class for file I/O.
        self.file_handler = FileHandler()
        # LexicalAnalyzer processes the source code into tokens.
        self.lexical_analyzer = LexicalAnalyzer()

        self.source_code_string = None  # Will hold the complete source code as a string.
        self.tokens = []                # List to store tokens produced by the lexer.

        # Start the process by calling the run() method.
        self.run()

    def run(self):
        """
        Main function to run the JohnA1 process.
        
        It:
            - Reads the source file.
            - Prints the source code.
            - Processes the source code to extract tokens.
            - Formats and outputs the tokens.
        """
        self.logger.debug("Starting run() method.")
        self.get_source_code_from_file(self.input_file_name)
        self.print_source_code()
        if self.source_code_string:
            self.stage1()
            self.stage2()
        else:
            self.logger.error("No source code to process.")
            self.logger.critical("Exiting program.")
            sys.exit(1)

# region stage1
    def stage1(self):
        if self.source_code_string:
            self.process_tokens()
            self.format_and_output_tokens()
            self.logger.debug("Stage 1 complete.")
        else:
            # If there is no source code, we cannot proceed to the next stage.
            self.logger.error("No source code to process.")
            self.logger.critical("Stage 1 failed. Exiting program.")
            sys.exit(1)

    def get_source_code_from_file(self, input_file_name: str):
        """
        Read the source code from a file and store it in the source_code_string attribute.
        """
        self.logger.debug(f"Reading source code from file: {input_file_name}")
        try:
            with open(input_file_name, 'r') as file:
                self.source_code_string = file.read().strip()
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
            self.tokens = self.lexical_analyzer.analyze(self.source_code_string)
        except ValueError as e:
            self.logger.error(f"Invalid token found: {e}")
        except Exception as e:
            self.logger.critical(f"An error occurred during tokenization: {e}")


    def print_source_code(self):
        """
        Print the source code to the console.
        
        If the source code could not be read, log a warning.
        """
        if not self.source_code_string:
            self.logger.warning("No source code to print.")
            return
        print(self.source_code_string)
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

    def stage2(self):
        if self.tokens:
            self.logger.debug("Starting Stage 2: Recursive Descent Parser.")
            
            # Parse the tokens
            success = self.parse_with_RDparser()
            
            if success:
                self.logger.info("Parsing completed successfully.")
            else:
                self.logger.error("Parsing failed with errors.")
            
            self.logger.debug("Stage 2 complete.")
        else:
            self.logger.error("No tokens to parse.")
            self.logger.critical("Stage 2 failed. Exiting program.")
            sys.exit(1)

    def parse_with_RDparser(self):
        """
        Parse the given list of tokens.
        Returns True if parsing was successful, False otherwise.
        """
        self.logger.debug("Parsing tokens.")
        self.rdparser = RDParser(self.tokens, self.lexical_analyzer.defs, stop_on_error=False, panic_mode_recover=False, build_parse_tree=True)
        success = self.rdparser.parse()
        self.logger.debug("Parsing complete.")
        self.rdparser.print_parse_tree()
        return success

    def get_processing_status(self) -> dict:
        return {
            'tokens_count': len(self.tokens) if self.tokens else 0,
            'has_source': bool(self.source_code_string),
            'parsing_complete': hasattr(self, 'parsing_success') and self.parsing_success
        }


def main():
    """Main entry point that creates JohnA3 instance from command line args."""
    JohnA3.from_args(sys.argv[1:])

if __name__ == "__main__":
    main()