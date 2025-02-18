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
    def __init__(self, input_file_name: str):
        self.logger = Logger()
        self.input_file_name = input_file_name
        self.file_handler = FileHandler()
        self.lexical_analyzer = LexicalAnalyzer()
        self.rd_parser = RDParser()
        self.source_code_string = None
        self.tokens = []

        self.run()

    def run(self):
        self.logger.debug("Reading source code from file.")
        self.source_code_string = self.get_source_code_from_file()

        self.logger.debug("Processing source code into tokens.")
        self.tokens = self.process_tokens()

        self.logger.debug("Parsing tokens using the Recursive Descent Parser.")
        self.rd_parser.parse(self.tokens)

    def get_source_code_from_file(self) -> str:
        return self.file_handler.read_file(self.input_file_name)

    def get_source_code_from_file(self):
        """
        Read the source code from a file and store it in the source_code_string attribute.

        Parameters:
          input_file_name (str): The file path of the source code.

        Raises:
          FileNotFoundError: If the source file cannot be read.
        """
        self.logger.debug(f"Attempting to read source code from file: {self.input_file_name}")
        self.source_code_string = self.file_handler.read_file_as_string(self.input_file_name)
        if self.source_code_string is None:
            self.logger.critical(f"Error: Could not read the file '{self.input_file_name}'.")
            raise FileNotFoundError(f"File '{self.input_file_name}' not found.")
        else:
            self.logger.debug("Source code read successfully as character stream.")

    def process_tokens(self) -> List[Token]:
        return self.lexical_analyzer.tokenize(self.source_code_string)