# RDParser.py

# Recursive Descent Parser
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-17
# Version: 1.0
# Description: Recursive Descent Parser for Ada Compiler Construction

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


class RDParser:
    def __init__(self, stop_on_error=False):
        pass

    def parse(self, tokens: List[Token]):
        pass