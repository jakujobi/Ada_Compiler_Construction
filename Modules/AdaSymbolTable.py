# AdaSymbolTable.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-28
# Version: 1.0
# Description:
# This module defines the AdaSymbolTable class, which represents a symbol table for an Ada compiler.
# It manages the storage and retrieval of symbols, such as variables, procedures, and constants,


class AdaSymbolTable:
    """
    AdaSymbolTable represents a symbol table for an Ada compiler.
    It manages the storage and retrieval of symbols, such as variables, procedures, and constants,
    in the context of Ada programming language.
    """
    def __init__(self):
        """
        Initializes an empty symbol table.
        """
        self.symbol_table = {}
