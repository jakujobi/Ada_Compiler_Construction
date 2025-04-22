#!/usr/bin/env python3
# JohnA4.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-03-31
# Version: 1.0
"""
Driver program for Assignment 4: Symbol Table Implementation for Ada Compiler

This program demonstrates the symbol table functionality:
1. Creates and manages a symbol table
2. Inserts various types of symbols (variables, constants, procedures)
3. Demonstrates lookup and scope management

Usage:
    python JohnA4.py
"""

import os
import sys
import logging
from pathlib import Path


try:
    import jakadac    # type: ignore
    from jakadac.modules.Driver import BaseDriver    # type: ignore
    from jakadac.modules.Logger import Logger    # type: ignore
    from jakadac.modules.AdaSymbolTable import *    # type: ignore
except (ImportError, FileNotFoundError):
    # Add 'src' directory to path for local imports
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
    from src.jakadac.modules.AdaSymbolTable import *


class JohnA4(BaseDriver):
    """
    Driver class for Assignment 4: Symbol Table Implementation
    Inherits from BaseDriver to reuse common functionality
    """

    def __init__(self, debug: bool = False, logger: Logger = None):
        """
        Initialize the JohnA4 driver.

        Args:
            debug: Whether to enable debug mode
            logger: Optional logger instance to use
        """
        # Call parent constructor with None for file paths since this driver doesn't use files
        super().__init__("", None, debug, logger)
        self.symbol_table = None
        self.run()

    def run(self) -> None:
        """
        Main function to run the symbol table demonstration.
        
        It:
            1. Creates a symbol table
            2. Demonstrates various symbol table operations
            3. Shows scope management
        """
        self.logger.info("Starting symbol table demonstration.")
        
        try:
            self.demonstrate_symbol_table()
            self.logger.info("Symbol table demonstration complete.")
        except Exception as e:
            self.logger.critical(f"An error occurred during symbol table demonstration: {str(e)}")
            if self.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)

    def demonstrate_symbol_table(self) -> None:
        """Demonstrate the functionality of the symbol table."""
        print("Symbol Table Demonstration")
        print("-" * 30)
        
        # Create a new symbol table
        self.symbol_table = AdaSymbolTable()
        print("Created a new symbol table with size 211.")
        
        print("\n1. Testing insert and lookup operations:")
        # Insert a variable
        var1 = self.symbol_table.insert("counter", "ID", 1)
        var1.set_variable_info(VarType.INT, 0, 4)
        print(f"Inserted: {var1}")
        
        # Insert a constant
        const1 = self.symbol_table.insert("PI", "ID", 1)
        const1.set_constant_info(VarType.FLOAT, 3.14159)
        print(f"Inserted: {const1}")
        
        # Insert a procedure
        params = [Parameter(VarType.INT, ParameterMode.IN)]
        proc1 = self.symbol_table.insert("calculate", "ID", 1)
        proc1.set_procedure_info(local_size=8, param_count=1, return_type=VarType.INT, param_list=params)
        print(f"Inserted: {proc1}")
        
        # Demonstrate lookup
        print("\nLookup results:")
        for name in ["counter", "nonexistent", "PI", "calculate"]:
            result = self.symbol_table.lookup(name)
            if result:
                print(f"  '{name}': Found")
            else:
                print(f"  '{name}': Not found")
        
        print("\n2. Testing writeTable and deleteDepth operations:")
        # Add entries at depth 2
        self.symbol_table.insert("index", "ID", 2).set_variable_info(VarType.INT, 4, 4)
        self.symbol_table.insert("flag", "ID", 2).set_variable_info(VarType.CHAR, 8, 1)
        
        # Add an entry with the same name at a different depth
        self.symbol_table.insert("counter", "ID", 2).set_variable_info(VarType.FLOAT, 12, 8)
        
        # Write table at depth 2
        print("Entries at depth 2:", self.symbol_table.writeTable(2))
        
        # Demonstrate depth-specific lookup
        print("\nDepth-specific lookup results:")
        # Try to find 'counter' at different depths
        counter_depth1 = self.symbol_table.lookup("counter", 1)
        counter_depth2 = self.symbol_table.lookup("counter", 2)
        counter_depth3 = self.symbol_table.lookup("counter", 3)  # Shouldn't exist
        
        print(f"  'counter' at depth 1: {counter_depth1.var_type.name if counter_depth1 else 'Not found'}")
        print(f"  'counter' at depth 2: {counter_depth2.var_type.name if counter_depth2 else 'Not found'}")
        print(f"  'counter' at depth 3: {counter_depth3.var_type.name if counter_depth3 else 'Not found'}")
        
        # Compare with the default lookup that finds the most recent entry
        counter_any_depth = self.symbol_table.lookup("counter")
        print(f"  'counter' at any depth: {counter_any_depth.var_type.name if counter_any_depth else 'Not found'}")
        print(f"  Found at depth: {counter_any_depth.depth if counter_any_depth else 'N/A'}")
        
        # Delete entries at depth 2
        self.symbol_table.deleteDepth(2)
        print("\nAfter deletion - entries at depth 2:", self.symbol_table.writeTable(2))
        print("Entries at depth 1 (should be unchanged):", self.symbol_table.writeTable(1))
        
        # Check 'counter' again to show we now get the depth 1 version
        counter_after_delete = self.symbol_table.lookup("counter")
        print(f"  'counter' after deletion: {counter_after_delete.var_type.name if counter_after_delete else 'Not found'}")
        print(f"  Found at depth: {counter_after_delete.depth if counter_after_delete else 'N/A'}")
        
        print("\n3. Testing hash collisions and chaining:")
        # Create two entries with potentially the same hash
        lex1 = "test1"
        lex2 = "test2"
        h1 = self.symbol_table._hash(lex1)
        h2 = self.symbol_table._hash(lex2)
        
        if h1 == h2:
            print(f"Found collision: '{lex1}' and '{lex2}' both hash to {h1}")
        else:
            print(f"No collision: '{lex1}' hashes to {h1}, '{lex2}' hashes to {h2}")
        
        # Insert both lexemes regardless
        self.symbol_table.insert(lex1, "ID", 3).set_variable_info(VarType.INT, 0, 4)
        self.symbol_table.insert(lex2, "ID", 3).set_variable_info(VarType.FLOAT, 4, 8)
        
        # Verify both can be looked up
        print(f"Lookup '{lex1}': {'Found' if self.symbol_table.lookup(lex1) else 'Not found'}")
        print(f"Lookup '{lex2}': {'Found' if self.symbol_table.lookup(lex2) else 'Not found'}")
        
        print("\nSymbol Table Demonstration Complete")


def main():
    """
    Main entry point for the symbol table demonstration program.
    
    It:
        1. Initializes the Logger
        2. Creates and runs a JohnA4 instance
    """
    # Initialize the Logger
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Starting JohnA4 program.")
    
    # Create and run the driver
    JohnA4(debug=True, logger=logger)


if __name__ == "__main__":
    main()
