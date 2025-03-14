# AdaSymbolTable.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-28
# Version: 1.0
# Description:
# This module defines the AdaSymbolTable class, which represents a symbol table for an Ada compiler.
# It manages the storage and retrieval of symbols, such as variables, procedures, and constants,

from enum import Enum
from typing import Dict, List, Union, Optional, Any


class VarType(Enum):
    """Enumeration for variable types"""
    CHAR = 1
    INT = 2
    FLOAT = 3


class EntryType(Enum):
    """Enumeration for symbol table entry types"""
    VARIABLE = 1
    CONSTANT = 2
    PROCEDURE = 3


class ParameterMode(Enum):
    """Enumeration for parameter passing modes"""
    IN = 1
    OUT = 2
    INOUT = 3


class Parameter:
    """
    Class representing a procedure parameter
    """
    def __init__(self, param_type: VarType, passing_mode: ParameterMode):
        """
        Initialize a parameter
        
        Parameters:
            param_type: Type of the parameter
            passing_mode: How the parameter is passed (IN, OUT, INOUT)
        """
        self.param_type = param_type
        self.passing_mode = passing_mode
    
    def __str__(self):
        return f"Parameter(type={self.param_type.name}, mode={self.passing_mode.name})"


class TableEntry:
    """
    Class representing an entry in the symbol table
    """
    def __init__(self, lexeme: str, token_type: Any, depth: int):
        """
        Initialize a table entry
        
        Parameters:
            lexeme: The identifier name
            token_type: Token type from lexical analyzer
            depth: Scope depth of this entry
        """
        # Common fields for all entries
        self.lexeme = lexeme
        self.token_type = token_type
        self.depth = depth
        self.entry_type = None  # Will be set based on the type of entry
        self.next = None  # For linked list implementation (chaining)
        
        # Variable fields (used if entry_type is VARIABLE)
        self.var_type = None
        self.offset = None
        self.size = None
        
        # Constant fields (used if entry_type is CONSTANT)
        self.const_type = None
        self.const_value = None
        
        # Procedure fields (used if entry_type is PROCEDURE)
        self.local_size = None
        self.param_count = None
        self.return_type = None
        self.param_list = None
    
    def set_variable_info(self, var_type: VarType, offset: int, size: int):
        """
        Set information specific to variable entries
        
        Parameters:
            var_type: Type of the variable
            offset: Memory offset
            size: Size in memory
        """
        self.entry_type = EntryType.VARIABLE
        self.var_type = var_type
        self.offset = offset
        self.size = size
    
    def set_constant_info(self, const_type: VarType, value: Union[int, float]):
        """
        Set information specific to constant entries
        
        Parameters:
            const_type: Type of the constant
            value: Value of the constant
        """
        self.entry_type = EntryType.CONSTANT
        self.const_type = const_type
        self.const_value = value
    
    def set_procedure_info(
            self, local_size: int,
            param_count: int, 
            return_type: VarType,
            param_list: List[Parameter]):
        """
        Set information specific to procedure entries
        
        Parameters:
            local_size: Size of local variables
            param_count: Number of parameters
            return_type: Return type of the procedure
            param_list: List of parameter information
        """
        self.entry_type = EntryType.PROCEDURE
        self.local_size = local_size
        self.param_count = param_count
        self.return_type = return_type
        self.param_list = param_list
    
    def __str__(self):
        """Return a string representation of the entry"""
        base = f"Entry(lexeme='{self.lexeme}', depth={self.depth}"
        
        if self.entry_type == EntryType.VARIABLE:
            return f"{base}, type=VARIABLE, var_type={self.var_type.name if self.var_type else None})"
        elif self.entry_type == EntryType.CONSTANT:
            return f"{base}, type=CONSTANT, const_type={self.const_type.name if self.const_type else None}, value={self.const_value})"
        elif self.entry_type == EntryType.PROCEDURE:
            return f"{base}, type=PROCEDURE, param_count={self.param_count})"
        else:
            return f"{base}, type=UNDEFINED)"


class AdaSymbolTable:
    """
    AdaSymbolTable represents a symbol table for an Ada compiler.
    It manages the storage and retrieval of symbols, such as variables, procedures, and constants,
    in the context of Ada programming language.
    """
    def __init__(self, table_size: int = 211):
        """
        Initializes an empty symbol table.
        
        Parameters:
            table_size: Size of the hash table (default: 211, a prime number)
        """
        self.table_size = table_size
        # Initialize the hash table as a list of None values (empty chains)
        self.table = [None] * table_size
    
    def _hash(self, lexeme: str) -> int:
        """
        Private hash function for the symbol table.
        Implements the hashpjw algorithm mentioned in the course notes.
        
        Parameters:
            lexeme: The identifier to hash
            
        Returns:
            The hash value (index in the table)
        """
        h = 0
        g = 0
        
        # Process each character in the lexeme
        for char in lexeme:
            # Shift h left by 4 bits and add ASCII value of the character
            h = (h << 4) + ord(char)
            
            # Check if any of the 4 high-order bits are set
            g = h & 0xF0000000
            
            if g != 0:
                # If high-order bits are set, shift them right by 24, XOR with h, and reset them
                h = h ^ (g >> 24)
                h = h ^ g
        
        # Return the hash value modulo table size
        return h % self.table_size
    
    def insert(self, lexeme: str, token_type: Any, depth: int) -> TableEntry:
        """
        Insert a new entry into the symbol table.
        
        Parameters:
            lexeme: The identifier name
            token_type: Token type from lexical analyzer
            depth: Scope depth of this entry
            
        Returns:
            The created table entry
        """
        # Create a new entry
        entry = TableEntry(lexeme, token_type, depth)
        
        # Calculate hash value
        hash_value = self._hash(lexeme)
        
        # Insert at the front of the chain (supports scope rules)
        entry.next = self.table[hash_value]
        self.table[hash_value] = entry
        
        return entry
    
    def lookup(self, lexeme: str) -> Optional[TableEntry]:
        """
        Look up an entry in the symbol table.
        
        Parameters:
            lexeme: The identifier to look up
            
        Returns:
            The found entry or None if not found
        """
        # Calculate hash value
        hash_value = self._hash(lexeme)
        
        # Traverse the chain to find the entry
        current = self.table[hash_value]
        while current is not None:
            if current.lexeme == lexeme:
                return current
            current = current.next
        
        # Entry not found
        return None
    
    def deleteDepth(self, depth: int) -> None:
        """
        Delete all entries at the specified depth.
        
        Parameters:
            depth: The depth to delete
        """
        # Iterate through all chains in the hash table
        for i in range(self.table_size):
            # Handle the case where the first entry in the chain needs to be deleted
            while self.table[i] is not None and self.table[i].depth == depth:
                self.table[i] = self.table[i].next
            
            # Handle the case where an entry in the middle or end of the chain needs to be deleted
            if self.table[i] is not None:
                current = self.table[i]
                while current.next is not None:
                    if current.next.depth == depth:
                        current.next = current.next.next
                    else:
                        current = current.next
    
    def writeTable(self, depth: int) -> List[str]:
        """
        Write out all lexemes at the specified depth.
        
        Parameters:
            depth: The depth to write
            
        Returns:
            List of lexemes at the specified depth
        """
        lexemes = []
        
        # Iterate through all chains in the hash table
        for i in range(self.table_size):
            current = self.table[i]
            while current is not None:
                if current.depth == depth:
                    lexemes.append(current.lexeme)
                current = current.next
        
        return lexemes
    
    def print_table(self) -> None:
        """
        Print the entire symbol table for debugging purposes.
        """
        for i in range(self.table_size):
            if self.table[i] is not None:
                print(f"Chain {i}:")
                current = self.table[i]
                while current is not None:
                    print(f"  {current}")
                    current = current.next
