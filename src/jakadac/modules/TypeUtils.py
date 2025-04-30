#!/usr/bin/env python3
# TypeUtils.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-01
# Version: 1.0
"""
Type Utilities for Ada Compiler

This module provides utility functions and mappings for type conversion
between different representations of types across the compiler components.
"""

from .SymTable import VarType

class TypeUtils:
    """
    Utilities for handling type conversions between different components.
    """
    
    @staticmethod
    def token_type_to_var_type(token_type: str) -> VarType:
        """
        Convert a token type to a variable type.
        
        Args:
            token_type: The token type from the lexical analyzer
            
        Returns:
            The corresponding variable type
        """
        mapping = {
            "INTEGERT": VarType.INT,
            "INTEGER": VarType.INT,
            "INT": VarType.INT,
            "REALT": VarType.FLOAT,
            "REAL": VarType.FLOAT,
            "FLOAT": VarType.FLOAT,
            "CHART": VarType.CHAR,
            "CHAR": VarType.CHAR,
            "BOOLEAN": VarType.BOOLEAN
        }
        
        # Case-insensitive lookup
        return mapping.get(token_type.upper(), None)
    
    @staticmethod
    def get_type_size(var_type: VarType) -> int:
        """
        Get the size in bytes for a variable type.
        
        Args:
            var_type: The variable type
            
        Returns:
            Size in bytes
        """
        sizes = {
            VarType.INT: 2,
            VarType.FLOAT: 4,
            VarType.REAL: 4,  # Alias for FLOAT
            VarType.CHAR: 1,
            VarType.BOOLEAN: 1
        }
        
        return sizes.get(var_type, 0)


    
    @staticmethod
    def parse_value_from_token(token_type: str, lexeme: str) -> tuple:
        """
        Parse a value from a token based on its type.
        
        Args:
            token_type: The token type
            lexeme: The token lexeme
            
        Returns:
            Tuple of (var_type, value)
        """
        if token_type in ("NUM", "INTLIT"):
            return (VarType.INT, int(lexeme))
        elif token_type in ("REAL", "FLOATLIT"):
            return (VarType.FLOAT, float(lexeme))
        elif token_type in ("CHRLIT"):
            return (VarType.CHAR, lexeme.strip("'"))
        else:
            return (None, None)

    @staticmethod
    def map_ada_op_to_tac(ada_op):  
        # Map Ada operators to TAC operators  
        op_map = {  
            "+": "ADD",  
            "-": "SUB",  
            "*": "MUL",  
            "/": "DIV",  
            "and": "AND",  
            "or": "OR",  
            "mod": "MOD",  
            "rem": "REM"  
        }  
        return op_map.get(ada_op, ada_op.upper())  