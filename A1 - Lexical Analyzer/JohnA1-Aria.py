# A1 - Lexical Analyzer
# JohnA1.py
# This is the main driver file for the Lexical Analyzer project.
# It reads a source file, uses the LexicalAnalyzer to tokenize the source code,
# and outputs the tokens (both to the console and optionally to a file).
#
# The code is documented in a friendly tone so that a beginner can follow how the program works.

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the system path so that modules can be imported.
repo_home_path = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_home_path))

from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.FileHandler import FileHandler
from Modules.Logger import Logger  # Our custom Logger class

class JohnA1:
    """
    Class: JohnA1
    ---------------
    This class is responsible for:
      - Reading a source code file.
      - Processing the source code using the LexicalAnalyzer.
      - Outputting the resulting tokens to the console and optionally to a file.

    Key methods:
      - run(): Orchestrates the reading, tokenization, and output process.
      - get_source_code_from_file(): Reads the source code from a file.
      - process_tokens(): Tokenizes the source code.
      - print_source_code(): Prints the source code to the console.
      - format_and_output_tokens(): Formats the tokens into a table and prints/writes it.
      - write_output_to_file(): Writes the formatted token table to an output file.
    """

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
            self.process_tokens()
            self.format_and_output_tokens()

    def get_source_code_from_file(self, input_file_name: str):
        """
        Read the source code from a file and store it in the source_code_string attribute.

        Parameters:
          input_file_name (str): The file path of the source code.

        Raises:
          FileNotFoundError: If the source file cannot be read.
        """
        self.logger.debug(f"Attempting to read source code from file: {input_file_name}")
        self.source_code_string = self.file_handler.read_file_as_string(input_file_name)
        if self.source_code_string is None:
            self.logger.critical(f"Error: Could not read the file '{input_file_name}'.")
            raise FileNotFoundError(f"File '{input_file_name}' not found.")
        else:
            self.logger.debug("Source code read successfully as character stream.")

    def process_tokens(self):
        """
        Tokenize the source code using the LexicalAnalyzer.

        This method calls the analyze() function of the lexical analyzer, which returns
        a list of tokens. The tokens are then stored in the tokens attribute.
        """
        try:
            self.logger.debug("Processing tokens from source code.")
            self.tokens = self.lexical_analyzer.analyze(self.source_code_string)
            self.logger.debug(f"Tokenization complete. {len(self.tokens)} tokens produced.")
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

def main():
    """
    Main function for the Lexical Analyzer program.

    It performs the following steps:
      1. Initializes the Logger (which sets up the logging configuration).
      2. Checks command-line arguments to determine the input (and optionally output) file.
      3. Creates an instance of JohnA1 with the provided file names.
      4. Starts the tokenization process.
      
    Usage:
      python JohnA1.py <input_file> [output_file]
    """
    # Initialize the Logger. This creates the logging configuration for the application.
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA1 program.")
    
    # Read command-line arguments.
    logger.debug("Checking command line arguments.")
    args = sys.argv[1:]
    
    # Validate arguments and start the process.
    if len(args) == 2:
        input_file, output_file = args
        logger.debug(f"Input file: {input_file}, Output file: {output_file}")
        JohnA1(input_file, output_file)
    elif len(args) == 1:
        input_file = args[0]
        logger.debug(f"Input file: {input_file}")
        JohnA1(input_file)
    else:
        print("Usage: python JohnA1.py <input_file> [output_file]")
        logger.critical("Invalid number of arguments. Exiting program.")
        sys.exit(1)

if __name__ == "__main__":
    main()
