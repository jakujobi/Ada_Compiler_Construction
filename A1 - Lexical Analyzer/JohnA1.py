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


class JohnA1:
    """
    /**********************************************************************
    ***  CLASS  : JohnA1                                               ***
    **********************************************************************
    ***  DESCRIPTION : This class is responsible for reading a file,     ***
    ***  processing it with a Lexical Analyzer, and outputting the      ***
    ***  results to a file.                                             ***
    **********************************************************************/
    """
    def __init__(self, input_file_name: str, output_file_name: str = None):
        """
        /**********************************************************************
        ***  FUNCTION : __init__                                            ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************
        ***  DESCRIPTION : Initializes the JohnA1 class.                    ***
        **********************************************************************/
        """
        self.input_file_name = input_file_name
        self.output_file_name = output_file_name
        
        self.configure_logging()
        logging.debug("Initializing FileHandler and LexicalAnalyzer.")
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        
        self.source_code_string = None
        self.tokens = []
        
        self.run()

    def configure_logging(self):
        """
        /**********************************************************************
        ***  FUNCTION : configure_logging                                   ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************
        ***  DESCRIPTION : Configures the logging for the JohnA1 class.     ***
        **********************************************************************/
        """
        log_directory = Path("logs")
        log_directory.mkdir(exist_ok=True)  # Create the directory if it doesn't exist
    
        log_title = log_directory / f"{self.__class__.__name__}_{self.input_file_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        logging.basicConfig(filename=log_title, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug(f"Log file created: {log_title}")

    def run(self):
        """
        /**********************************************************************
        ***  FUNCTION : run                                                 ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************
        ***  DESCRIPTION : Runs the JohnA1 class.                           ***
        **********************************************************************/
        """
        logging.debug("Starting run() method.")
        self.get_source_code_from_file(self.input_file_name)
        self.print_source_code()
        if self.source_code_string:
            self.process_tokens()
            self.format_and_output_tokens()

    def get_source_code_from_file(self, input_file_name: str):
        """
        Retrieves a character stream from the file.
        """
        logging.debug(f"Attempting to read source code from file: {input_file_name}")
        self.source_code_string = self.file_handler.read_file_as_string(input_file_name)
        if self.source_code_string is None:
            logging.critical(f"Error: Could not read the file '{input_file_name}'.")
            raise FileNotFoundError(f"File '{input_file_name}' not found.")
        else:
            logging.debug("Source code read successfully as character stream.")

    def process_tokens(self):
        """
        Processes the character stream using the lexical analyzer to produce a list of tokens.
        Assumes that the lexical analyzer has a method 'analyze' that accepts a character generator.
        """
        try:
            logging.debug("Processing tokens from source code.")
            # The analyze method is assumed to take a character stream generator and return a list of tokens.
            self.tokens = self.lexical_analyzer.analyze(self.source_code_string)
            logging.debug(f"Tokenization complete. {len(self.tokens)} tokens produced.")
        except Exception as e:
            logging.error(f"An error occurred during tokenization: {e}")

    def print_source_code(self):
        """
        Prints the source code to the console.
        """
        if not self.source_code_string:
            logging.warning("No source code to print.")
            return
        print (self.source_code_string)
        logging.debug("Source code printed to console.")

    def format_and_output_tokens(self):
        """
        Formats the tokens into a table and outputs them.
        Also writes the table to an output file if specified.
        """
        if not self.tokens:
            logging.warning("No tokens to format.")
            return

        # Formatting tokens into a table (as a string).
        header = f"{'Token Type':15} | {'Lexeme':15} | {'Line':5} | {'Column':6} | {'Value'}"
        separator = "-" * (len(header) + 10)
        table_lines = [header, separator]
        for token in self.tokens:
            # Assuming each token has attributes: token_type, lexeme, line_number, column_number, value.
            row = f"{str(token.token_type):15} | {token.lexeme:15} | {token.line_number:<5} | {token.column_number:<6} | {token.value}"
            table_lines.append(row)
        
        table_output = "\n".join(table_lines)
        print(table_output)
        logging.debug("Token table printed successfully.")

        if self.output_file_name:
            success = self.write_output_to_file(self.output_file_name, table_output)
            if success:
                logging.debug(f"Token table written to file: {self.output_file_name}")

    def write_output_to_file(self, output_file_name: str, content: str) -> bool:
        """
        Writes the provided content to the specified output file.
        """
        try:
            # Write content to output file (overwrite if exists).
            with open(output_file_name, "w", encoding="utf-8") as f:
                f.write(content)
            logging.debug(f"Content successfully written to {output_file_name}.")
            return True
        except Exception as e:
            logging.error(f"An error occurred while writing to the file '{output_file_name}': {e}")
            return False


def main():
    """
    /**********************************************************************
    ***  FUNCTION : main                                                ***
    **********************************************************************
    ***  DESCRIPTION : The main function of the program.                 ***
    **********************************************************************/
    """
    # Check command line arguments
    args = sys.argv[1:]
    
    # Usage: python JohnA1.py input_file [output_file]
    if len(args) == 2:
        input_file, output_file = args
        JohnA1(input_file, output_file)
    elif len(args) == 1:
        input_file = args[0]
        JohnA1(input_file)
    else:
        print("Usage: python JohnA1.py <input_file> [output_file]")
        sys.exit(1)


if __name__ == "__main__":
    main()