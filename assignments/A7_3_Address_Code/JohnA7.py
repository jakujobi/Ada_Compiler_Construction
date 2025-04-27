#!/usr/bin/env python3
# JohnA7.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.0
"""
Driver program for Assignment 7: Three Address Code Generator for Ada Compiler

This program generates three address code from the parsed AST.
"""


import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import traceback
from typing import Union

try:
    import jakadac
    from jakadac.modules.Driver import BaseDriver
    from jakadac.modules.Logger import Logger
    from jakadac.modules.AdaSymbolTable import *
    from jakadac.modules.SemanticAnalyzer import *
    from jakadac.modules.RDParser import *
    from jakadac.modules.RDParserExtended import *
    from jakadac.modules.FileHandler import *
    from jakadac.modules.Token import *
    from jakadac.modules.Definitions import *
    from jakadac.modules.LexicalAnalyzer import *
    from jakadac.modules.TACGenerator import *
except (ImportError, FileNotFoundError):
    # Add 'src' directory to path for local imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
    from src.jakadac.modules.AdaSymbolTable import *
    from src.jakadac.modules.SemanticAnalyzer import *
    from src.jakadac.modules.RDParser import *
    from src.jakadac.modules.RDParserExtended import *
    from src.jakadac.modules.FileHandler import *
    from src.jakadac.modules.Token import *
    from src.jakadac.modules.Definitions import *
    from src.jakadac.modules.LexicalAnalyzer import *
    from src.jakadac.modules.TACGenerator import *