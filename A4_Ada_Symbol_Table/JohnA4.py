#!/usr/bin/env python3
# JohnA4.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-03-13
# Version: 1.0
# Description:
# Assignment #4 - Symbol Table Implementation
# This file demonstrates the functionality of the AdaSymbolTable class.

import os
import sys
from enum import Enum
from typing import List

# Add the parent directory to the path so we can import the modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

# Import the necessary modules
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter, TableEntry


def main():
    """
    Main function to demonstrate the functionality of the AdaSymbolTable class.
    """
    print("Symbol Table Demonstration")
    print("-" * 30)
    
    # Create a new symbol table
    symbol_table = AdaSymbolTable()
    print("Created a new symbol table with size 211.")
    
    print("\n1. Testing insert and lookup operations:")
    # Insert a variable
    var1 = symbol_table.insert("counter", "ID", 1)
    var1.set_variable_info(VarType.INT, 0, 4)
    print(f"Inserted: {var1}")
    
    # Insert a constant
    const1 = symbol_table.insert("PI", "ID", 1)
    const1.set_constant_info(VarType.FLOAT, 3.14159)
    print(f"Inserted: {const1}")
    
    # Insert a procedure
    params = [Parameter(VarType.INT, ParameterMode.IN)]
    proc1 = symbol_table.insert("calculate", "ID", 1)
    proc1.set_procedure_info(local_size=8, param_count=1, return_type=VarType.INT, param_list=params)
    print(f"Inserted: {proc1}")
    
    # Demonstrate lookup
    print("\nLookup results:")
    for name in ["counter", "nonexistent", "PI", "calculate"]:
        result = symbol_table.lookup(name)
        if result:
            print(f"  '{name}': Found")
        else:
            print(f"  '{name}': Not found")
    
    print("\n2. Testing writeTable and deleteDepth operations:")
    # Add entries at depth 2
    symbol_table.insert("index", "ID", 2).set_variable_info(VarType.INT, 4, 4)
    symbol_table.insert("flag", "ID", 2).set_variable_info(VarType.CHAR, 8, 1)
    
    # Add an entry with the same name at a different depth
    symbol_table.insert("counter", "ID", 2).set_variable_info(VarType.FLOAT, 12, 8)
    
    # Write table at depth 2
    print("Entries at depth 2:", symbol_table.writeTable(2))
    
    # Demonstrate depth-specific lookup
    print("\nDepth-specific lookup results:")
    # Try to find 'counter' at different depths
    counter_depth1 = symbol_table.lookup("counter", 1)
    counter_depth2 = symbol_table.lookup("counter", 2)
    counter_depth3 = symbol_table.lookup("counter", 3)  # Shouldn't exist
    
    print(f"  'counter' at depth 1: {counter_depth1.var_type.name if counter_depth1 else 'Not found'}")
    print(f"  'counter' at depth 2: {counter_depth2.var_type.name if counter_depth2 else 'Not found'}")
    print(f"  'counter' at depth 3: {counter_depth3.var_type.name if counter_depth3 else 'Not found'}")
    
    # Compare with the default lookup that finds the most recent entry
    counter_any_depth = symbol_table.lookup("counter")
    print(f"  'counter' at any depth: {counter_any_depth.var_type.name if counter_any_depth else 'Not found'}")
    print(f"  Found at depth: {counter_any_depth.depth if counter_any_depth else 'N/A'}")
    
    # Delete entries at depth 2
    symbol_table.deleteDepth(2)
    print("\nAfter deletion - entries at depth 2:", symbol_table.writeTable(2))
    print("Entries at depth 1 (should be unchanged):", symbol_table.writeTable(1))
    
    # Check 'counter' again to show we now get the depth 1 version
    counter_after_delete = symbol_table.lookup("counter")
    print(f"  'counter' after deletion: {counter_after_delete.var_type.name if counter_after_delete else 'Not found'}")
    print(f"  Found at depth: {counter_after_delete.depth if counter_after_delete else 'N/A'}")
    
    print("\n3. Testing hash collisions and chaining:")
    # Create two entries with potentially the same hash
    lex1 = "test1"
    lex2 = "test2"
    h1 = symbol_table._hash(lex1)
    h2 = symbol_table._hash(lex2)
    
    if h1 == h2:
        print(f"Found collision: '{lex1}' and '{lex2}' both hash to {h1}")
    else:
        print(f"No collision: '{lex1}' hashes to {h1}, '{lex2}' hashes to {h2}")
    
    # Insert both lexemes regardless
    symbol_table.insert(lex1, "ID", 3).set_variable_info(VarType.INT, 0, 4)
    symbol_table.insert(lex2, "ID", 3).set_variable_info(VarType.FLOAT, 4, 8)
    
    # Verify both can be looked up
    print(f"Lookup '{lex1}': {'Found' if symbol_table.lookup(lex1) else 'Not found'}")
    print(f"Lookup '{lex2}': {'Found' if symbol_table.lookup(lex2) else 'Not found'}")
    
    print("\nSymbol Table Demonstration Complete")


if __name__ == "__main__":
    main()
