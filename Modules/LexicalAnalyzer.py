# LexicalAnalyzer
# LexicalAnalyzer is a module that provides a lexical analyzer for Ada programs.



import os
import sys
import logging
from typing import List, Optional

from pathlib import Path

repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.FileHandler import FileHandler
from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.ErrorHandler import ErrorHandler


class LexicalAnalyzer:
    def __init__(self,
                 file_handler: Optional[FileHandler] = None,
                 error_handler: Optional[ErrorHandler] = None
                 ):
        self.file_handler = file_handler or FileHandler()
        self.error_handler = error_handler or ErrorHandler()
        self.pos = 0
        self.current_char = ''
        self.line = 1
        self.column = 0
        #self._read_next_char()  # Initialize the first character

    def get_char(self):
        pass

    def analyze(self, source_code_string: str) -> List[Token]:
        pass