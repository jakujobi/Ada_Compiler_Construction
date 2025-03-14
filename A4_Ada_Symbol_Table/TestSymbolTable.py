#!/usr/bin/env python3
# TestSymbolTable.py
# Author: John Akujobi
# Date: 2025-03-13
# Simple test script for AdaSymbolTable functionality

import os
import sys

# Add parent directory to path for module imports
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, TableEntry

# Create symbol table
symbol_table = AdaSymbolTable()
print("1. Symbol table created")

# Test insert
entry = symbol_table.insert("testVar", "ID", 1)
entry.set_variable_info(VarType.INT, 0, 4)
print("2. Insert successful")

# Test lookup
found_entry = symbol_table.lookup("testVar")
print(f"3. Lookup: {'Successful' if found_entry else 'Failed'}")

# Test writeTable
symbol_table.insert("another", "ID", 1)
entries = symbol_table.writeTable(1)
print(f"4. WriteTable: Found {len(entries)} entries at depth 1")

# Test deleteDepth
symbol_table.insert("temp", "ID", 2)
print(f"5. Before deleteDepth: {len(symbol_table.writeTable(2))} entries at depth 2")
symbol_table.deleteDepth(2)
print(f"6. After deleteDepth: {len(symbol_table.writeTable(2))} entries at depth 2")

print("All tests completed")
