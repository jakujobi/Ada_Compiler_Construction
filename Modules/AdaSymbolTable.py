#!/usr/bin/env python3
# AdaSymbolTable.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-03-13
# Version: 1.0
"""
Symbol Table Implementation for Ada Compiler

This module implements a symbol table for an Ada compiler, using a hash table with
chaining for collision resolution. The symbol table provides operations for
inserting, looking up, deleting, and writing entries.

The symbol table is designed to support lexical scoping through depth parameters
and is compatible with the token system used in the lexical analyzer.

Key components:
- AdaSymbolTable: The main hash table implementation
- TableEntry: Represents entries in the symbol table
- VarType: Enumeration for variable types (CHAR, INT, FLOAT)
- EntryType: Enumeration for entry types (VARIABLE, CONSTANT, PROCEDURE)
- ParameterMode: Enumeration for parameter passing modes (IN, OUT, INOUT)
- Parameter: Represents parameters for procedures

Usage:
    # Create a symbol table
    symbol_table = AdaSymbolTable()
    
    # Insert entries
    var_entry = symbol_table.insert("counter", token, 1)
    var_entry.set_variable_info(VarType.INT, 0, 4)
    
    # Look up entries
    found = symbol_table.lookup("counter")
    
    # Delete entries at a specific depth
    symbol_table.deleteDepth(2)
    
    # Write out entries at a specific depth
    entries = symbol_table.writeTable(1)
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union


class VarType(Enum):
    """
    Enumeration for variable types supported in the Ada compiler.
    
    These types are used for variables, constants, and procedure return types.
    """
    CHAR = auto()
    INT = auto()
    FLOAT = auto()


class EntryType(Enum):
    """
    Enumeration for entry types in the symbol table.
    
    The symbol table stores different types of entries, each with specific
    information fields.
    """
    VARIABLE = auto()
    CONSTANT = auto()
    PROCEDURE = auto()


class ParameterMode(Enum):
    """
    Enumeration for parameter passing modes in procedures.
    
    - IN: Parameter is read-only within the procedure.
    - OUT: Parameter is write-only within the procedure.
    - INOUT: Parameter can be both read and written within the procedure.
    """
    IN = auto()
    OUT = auto()
    INOUT = auto()


class Parameter:
    """
    Class to represent parameters in procedure entries.
    
    Stores the parameter type and passing mode, which are used in procedure
    calls and for semantic analysis.
    
    Attributes:
        param_type (VarType): The data type of the parameter.
        param_mode (ParameterMode): The passing mode of the parameter.
    """
    def __init__(self, param_type: VarType, param_mode: ParameterMode):
        """
        Initialize a parameter with a type and passing mode.
        
        Args:
            param_type: The data type of the parameter (CHAR, INT, FLOAT).
            param_mode: The passing mode of the parameter (IN, OUT, INOUT).
        """
        self.param_type = param_type
        self.param_mode = param_mode
    
    def __str__(self) -> str:
        """
        Return a string representation of the Parameter.
        
        Returns:
            String in the format 'mode:type', e.g., 'IN:INT'.
        """
        return f"{self.param_mode.name}:{self.param_type.name}"


class TableEntry:
    """
    Class to represent an entry in the symbol table.
    
    Stores all information related to a symbol, including its lexeme, token type,
    scope depth, and specific information based on the entry type (variable,
    constant, or procedure).
    
    Attributes:
        lexeme (str): The identifier for this entry.
        token_type (Any): The token type from the lexical analyzer.
        depth (int): The lexical scope depth.
        next (Optional[TableEntry]): Pointer to the next entry in the chain for collision resolution.
        entry_type (Optional[EntryType]): The type of this entry (VARIABLE, CONSTANT, PROCEDURE).
        
        # Variable-specific attributes
        var_type (Optional[VarType]): The data type for variables.
        offset (Optional[int]): The memory offset for variables.
        size (Optional[int]): The memory size for variables.
        
        # Constant-specific attributes
        const_type (Optional[VarType]): The data type for constants.
        const_value (Optional[Any]): The value of the constant.
        
        # Procedure-specific attributes
        local_size (Optional[int]): The size of local variables for procedures.
        param_count (Optional[int]): The number of parameters for procedures.
        return_type (Optional[VarType]): The return type for procedures.
        param_list (Optional[List[Parameter]]): The list of parameters for procedures.
    """
    def __init__(self, lexeme: str, token_type: Any, depth: int):
        """
        Initialize a table entry with the basic information.
        
        Args:
            lexeme: The identifier for this entry.
            token_type: The token type from the lexical analyzer.
            depth: The lexical scope depth.
        """
        # Basic information
        self.lexeme = lexeme
        self.token_type = token_type
        self.depth = depth
        self.next = None
        
        # Type of entry
        self.entry_type = None
        
        # Variable-specific fields
        self.var_type = None
        self.offset = None
        self.size = None
        
        # Constant-specific fields
        self.const_type = None
        self.const_value = None
        
        # Procedure-specific fields
        self.local_size = None
        self.param_count = None
        self.return_type = None
        self.param_list = None
    
    def set_variable_info(self, var_type: VarType, offset: int, size: int):
        """
        Set information specific to variable entries.
        
        Args:
            var_type: The data type of the variable.
            offset: The memory offset of the variable.
            size: The memory size of the variable in bytes.
        """
        self.entry_type = EntryType.VARIABLE
        self.var_type = var_type
        self.offset = offset
        self.size = size
    
    def set_constant_info(self, const_type: VarType, value: Any):
        """
        Set information specific to constant entries.
        
        Args:
            const_type: The data type of the constant.
            value: The value of the constant.
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
        Set information specific to procedure entries.
        
        Args:
            local_size: The size of local variables in bytes.
            param_count: The number of parameters.
            return_type: The return type of the procedure.
            param_list: The list of parameter information.
        """
        self.entry_type = EntryType.PROCEDURE
        self.local_size = local_size
        self.param_count = param_count
        self.return_type = return_type
        self.param_list = param_list
    
    def __str__(self) -> str:
        """
        Return a string representation of the TableEntry.
        
        Returns:
            A string describing the entry, with different formats based on the entry type.
        """
        base = f"Entry(lexeme='{self.lexeme}', depth={self.depth}"
        
        if self.entry_type == EntryType.VARIABLE:
            return f"{base}, type=VARIABLE, var_type={self.var_type.name})"
        elif self.entry_type == EntryType.CONSTANT:
            return f"{base}, type=CONSTANT, const_type={self.const_type.name}, value={self.const_value})"
        elif self.entry_type == EntryType.PROCEDURE:
            params = ", ".join(str(p) for p in self.param_list) if self.param_list else ""
            return f"{base}, type=PROCEDURE, return_type={self.return_type.name}, params=[{params}])"
        else:
            return f"{base}, type=UNDEFINED)"


class AdaSymbolTable:
    """
    Symbol table implementation for Ada compiler using a hash table with chaining.
    
    The symbol table maps lexemes to their associated information, including
    type, scope, and specific fields based on the entry type. It supports
    lexical scoping through depth parameters and efficient lookups through
    a hash function.
    
    Attributes:
        table_size (int): The size of the hash table array.
        table (List[Optional[TableEntry]]): The hash table array.
    """
    def __init__(self, table_size: int = 211):
        """
        Initialize a symbol table with a specified size.
        
        Args:
            table_size: The size of the hash table; default is 211 (a prime number).
                        Prime numbers are recommended for hash table sizes to
                        minimize collisions.
                        
        Raises:
            ValueError: If table_size is not positive.
        """
        if table_size <= 0:
            raise ValueError("Table size must be positive")
            
        self.table_size = table_size
        self.table = [None] * table_size
    
    def _hash(self, lexeme: str) -> int:
        """
        Hash function based on the hashpjw algorithm used in many compilers.
        
        This function computes a hash value for a lexeme by considering all
        characters in the string, making it suitable for compiler symbol tables.
        
        Args:
            lexeme: The lexeme to hash.
        
        Returns:
            An integer hash value in the range [0, table_size).
            
        Raises:
            ValueError: If lexeme is empty.
        """
        if not lexeme:
            raise ValueError("Cannot hash an empty lexeme")
            
        h = 0
        g = 0
        for c in lexeme:
            h = (h << 4) + ord(c)
            g = h & 0xF0000000
            if g != 0:
                h = h ^ (g >> 24)
                h = h ^ g
        return h % self.table_size
    
    def insert(self, lexeme: str, token_type: Any, depth: int) -> TableEntry:
        """
        Insert a new entry into the symbol table.
        
        Creates a new entry with the given lexeme, token type, and depth,
        and inserts it at the front of the appropriate chain. Front insertion
        ensures that lookups find the most recent declaration first.
        
        Args:
            lexeme: The identifier to insert.
            token_type: The token type from the lexical analyzer.
            depth: The lexical scope depth.
        
        Returns:
            The newly created and inserted table entry.
            
        Raises:
            ValueError: If lexeme is empty or depth is negative.
        """
        if not lexeme:
            raise ValueError("Cannot insert an empty lexeme")

        if depth < 0:
            raise ValueError("Depth cannot be negative")

        # Create a new entry
        entry = TableEntry(lexeme, token_type, depth)
        
        # Insert at the front of the chain
        hash_val = self._hash(lexeme)
        entry.next = self.table[hash_val]
        self.table[hash_val] = entry
        
        return entry
    
    def lookup(self, lexeme: str) -> Optional[TableEntry]:
        """
        Look up an entry in the symbol table by lexeme.
        
        Computes the hash value for the lexeme and searches the appropriate
        chain for a matching entry. Returns the first (most recent) entry
        found with the given lexeme, or None if not found.
        
        Args:
            lexeme: The identifier to look up.
        
        Returns:
            The found table entry, or None if not found.
            
        Raises:
            ValueError: If lexeme is empty.
        """
        if not lexeme:
            raise ValueError("Cannot lookup an empty lexeme")
            
        hash_val = self._hash(lexeme)
        entry = self.table[hash_val]
        
        while entry is not None:
            if entry.lexeme == lexeme:
                return entry
            entry = entry.next
        
        # You could uncomment this to raise an exception instead of returning None
        # raise LookupError(f"Lexeme '{lexeme}' not found in symbol table")
        
        return None
    
    def deleteDepth(self, depth: int) -> None:
        """
        Delete all entries at a specified depth.
        
        Scans the entire hash table and removes entries at the given depth,
        updating the chains as needed. This is used when exiting a scope.
        
        Args:
            depth: The lexical scope depth to delete.
            
        Raises:
            ValueError: If depth is negative.
        """
        if depth < 0:
            raise ValueError("Depth cannot be negative")
            
        for i in range(self.table_size):
            prev = None
            curr = self.table[i]
            
            while curr is not None:
                if curr.depth == depth:
                    # Remove this entry
                    if prev is None:
                        # This is the first entry in the chain
                        self.table[i] = curr.next
                    else:
                        # This is not the first entry
                        prev.next = curr.next
                    
                    # Move to the next entry, but don't update prev
                    curr = curr.next
                else:
                    # Keep this entry, move both pointers
                    prev = curr
                    curr = curr.next
    
    def writeTable(self, depth: int) -> Dict[str, TableEntry]:
        """
        Write out all entries at a specified depth.
        
        Scans the entire hash table and collects entries at the given depth
        into a dictionary mapping lexemes to their entries.
        
        Args:
            depth: The lexical scope depth to write.
        
        Returns:
            A dictionary mapping lexemes to their entries.
            
        Raises:
            ValueError: If depth is negative.
        """
        if depth < 0:
            raise ValueError("Depth cannot be negative")
            
        result = {}
        
        for i in range(self.table_size):
            entry = self.table[i]
            
            while entry is not None:
                if entry.depth == depth:
                    result[entry.lexeme] = entry
                entry = entry.next
        
        return result

# Example usage:
if __name__ == "__main__":
    # Create a symbol table
    st = AdaSymbolTable()
    
    # Insert entries
    var1 = st.insert("x", "ID", 1)
    var1.set_variable_info(VarType.INT, 0, 4)
    
    const1 = st.insert("PI", "ID", 1)
    const1.set_constant_info(VarType.FLOAT, 3.14159)
    
    # Demonstrate lookup
    print(f"Looking up 'x': {st.lookup('x')}")
    print(f"Looking up 'y': {st.lookup('y')}")
    
    # Demonstrate writeTable
    print(f"Entries at depth 1: {st.writeTable(1)}")
    
    # Delete entries
    st.deleteDepth(1)
    print(f"After deletion - entries at depth 1: {st.writeTable(1)}")
