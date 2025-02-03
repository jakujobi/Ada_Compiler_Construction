# A1 - Lexical Analyzer
# John A1.py

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the parent directory to the system path
repo_home_path = Path(__file__).resolve().parent.parent
sys.path.append(str(repo_home_path))

from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.FileHandler import FileHandler
from Modules.Logger import Logger  # Our custom Logger class

class JohnA1:
    """
    **********************************************************************
    ***  CLASS  : JohnA1                                               ***
    **********************************************************************
    ***  DESCRIPTION : This class is responsible for reading a file,     ***
    ***  processing it with a Lexical Analyzer, and outputting the      ***
    ***  results to a file.                                             ***
    **********************************************************************
    """
    def __init__(self, input_file_name: str, output_file_name: str = None):
        # Get the shared logger instance.
        self.logger = Logger()  # Because Logger is a singleton, this is the shared instance.
        
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        
        self.logger.debug("Initializing FileHandler and LexicalAnalyzer.")
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        
        self.source_code_string = None
        self.tokens = []
        
        self.run()

    def run(self):
        """
        **********************************************************************
        ***  FUNCTION : run                                                 ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************
        ***  DESCRIPTION : Runs the JohnA1 class.                           ***
        **********************************************************************
        """
        self.logger.debug("Starting run() method.")
        self.get_source_code_from_file(self.input_file_name)
        self.print_source_code()
        if self.source_code_string:
            self.process_tokens()
            self.format_and_output_tokens()

    def get_source_code_from_file(self, input_file_name: str):
        """
        Retrieves a character stream from the file.
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
        Processes the character stream using the lexical analyzer to produce a list of tokens.
        """
        try:
            self.logger.debug("Processing tokens from source code.")
            # The analyze method returns a list of tokens.
            self.tokens = self.lexical_analyzer.analyze(self.source_code_string)
            self.logger.debug(f"Tokenization complete. {len(self.tokens)} tokens produced.")
        except Exception as e:
            self.logger.error(f"An error occurred during tokenization: {e}")

    def print_source_code(self):
        """
        Prints the source code to the console.
        """
        if not self.source_code_string:
            self.logger.warning("No source code to print.")
            return
        print(self.source_code_string)
        self.logger.debug("Source code printed to console.")

    def format_and_output_tokens(self):
        """
        Formats the tokens into a table and outputs them.
        Also writes the table to an output file if specified.
        """
        if not self.tokens:
            self.logger.warning("No tokens to format.")
            return

        # Create a table header.
        header = f"{'Token Type':15} | {'Lexeme':15} | {'Line':5} | {'Column':6} | {'Value'}"
        separator = "-" * (len(header) + 10)
        table_lines = [header, separator]
        for token in self.tokens:
            row = f"{str(token.token_type):15} | {token.lexeme:15} | {token.line_number:<5} | {token.column_number:<6} | {token.value}"
            self.logger.debug(f"Formatted token: {row}")
            table_lines.append(row)
        
        table_output = "\n".join(table_lines)
        print(table_output)
        self.logger.debug("Token table printed successfully.")

        if self.output_file_name:
            success = self.write_output_to_file(self.output_file_name, table_output)
            if success:
                self.logger.debug(f"Token table written to file: {self.output_file_name}")

    def write_output_to_file(self, output_file_name: str, content: str) -> bool:
        """
        Writes the provided content to the specified output file.
        """
        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.debug(f"Content successfully written to {output_file_name}.")
            return True
        except Exception as e:
            self.logger.error(f"An error occurred while writing to the file '{output_file_name}': {e}")
            return False

def main():
    """
    **********************************************************************
    ***  FUNCTION : main                                                ***
    **********************************************************************
    ***  DESCRIPTION : The main function of the program.                 ***
    **********************************************************************
    """
    # Initialize the Logger here. This sets up the configuration for the entire application.
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA1 program.")
    
    # Check command line arguments.
    logger.debug("Checking command line arguments.")
    args = sys.argv[1:]
    
    # Usage: python JohnA1.py input_file [output_file]
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
        logger.error("Invalid number of arguments. Exiting program.")
        sys.exit(1)

if __name__ == "__main__":
    main()
