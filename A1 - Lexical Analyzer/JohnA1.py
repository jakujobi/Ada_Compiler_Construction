# JohnA1.py

"""_summary_
The JohnA1 class is responsible for reading a file, processing it with a Lexical Analyzer, and outputting the results.

### JohnA1 class
- Create a log file 
- Receives the input file name at initialization as string, and the output file name(optional)
- Confirm if the input file exists
	- Log an error if the input file does not exist
	- 
- Log each step it performs with relevant level of logging
- Get the source code from the file
- Process it with the lexical analyzer and receive a list of tokens
- Format the tokens in to a table
- Print the table
- Write the table to a file
## main
Acquire files:
- If there are 2 arguements,
	- The first one is the name of the input file
	- The second one is the name of the output file
	- It should pass them to the JohnA1 class initialized
- If there is 1 arguement
	- it is the name of the input file
	- Pass it to the JohnA1 class initialized
- If no arguments, it should ask the user to provide the name of the file or exit the program

"""

import os
import re
import sys
import logging
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
    **********************************************************************/
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
        **********************************************************************/
        ***  DESCRIPTION : Initializes the JohnA1 class.                    ***
        **********************************************************************/
        """
        self.configure_logging()
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        
        self.input_file_name = None
        self.output_file_name = None
        
        self.source_code_string = None
        
        self.run()

    def run(self):
        """
        /**********************************************************************
        ***  FUNCTION : run                                                 ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************/
        ***  DESCRIPTION : Runs the JohnA1 class.                           ***
        **********************************************************************/
        """
        self.get_source_code_from_file(self.input_file_name)

    def configure_logging(self):
        """
        /**********************************************************************
        ***  FUNCTION : configure_logging                                   ***
        ***  CLASS  : JohnA1                                               ***
        **********************************************************************/
        ***  DESCRIPTION : Configures the logging for the JohnA1 class.     ***
        **********************************************************************/
        """
        # the log file should be named after the class name and the input file name and date and time
        log_title = f"{self.__class__.__name__}_{self.input_file_name}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        logging.basicConfig(filename=log_title, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.debug(f"Log file created: {log_title}")

        
    def get_source_code_from_file(self, input_file_name: str):
            self.source_code_string = self.file_handler.process_file_char_stream(input_file_name)
            if self.source_code_string is None:
                logging.error(f"Error: Could not read the file '{input_file_name}'.")
                return
            logging.debug("Source code read successfully.")
    
    def print_source_code(self):
        print(self.source_code_string)
        logging.debug("Source code printed successfully.")





def main():
    """
    /**********************************************************************
    ***  FUNCTION : main                                                ***
    **********************************************************************/
    ***  DESCRIPTION : The main function of the program.                 ***
    **********************************************************************/
    ***  
    """
    
    """
    
    """
