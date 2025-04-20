#!/usr/bin/env python3
# TestSymbolTable.py
# Author: John Akujobi
# Date: 2025-03-13
# Description: Comprehensive test suite for the AdaSymbolTable module
# This script tests all functionality of the symbol table implementation,
# including edge cases and integration with other compiler components.

import os
import sys
import unittest
from typing import List, Dict, Any

# Add parent directory to path for module imports
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

# Import modules from the compiler
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter, TableEntry
from Modules.Token import Token
from Modules.Definitions import Definitions

# Get token type definitions
definitions = Definitions()
TokenType = definitions.TokenType


class TestAdaSymbolTable(unittest.TestCase):
    """Test suite for AdaSymbolTable implementation"""

    def setUp(self):
        """Set up a fresh symbol table before each test"""
        self.symbol_table = AdaSymbolTable()
        # Set up some tokens for testing with real compiler tokens
        self.tokens = {
            'id': Token(TokenType.ID, 'testVar', 1, 1),
            'int': Token(TokenType.INTEGERT, 'INTEGER', 1, 10),
            'real': Token(TokenType.REALT, 'REAL', 1, 20),
            'procedure': Token(TokenType.PROCEDURE, 'PROCEDURE', 1, 30)
        }

    def test_hash_function(self):
        """Test the hash function distribution"""
        # Test that different lexemes hash to different values
        lexemes = ['a', 'b', 'test', 'variable', 'procedure', 'integer', 'float']
        hash_values = [self.symbol_table._hash(lexeme) for lexeme in lexemes]
        # Test uniqueness
        self.assertEqual(len(hash_values), len(set(hash_values)), 
                         "Hash function should generate different values for different lexemes")
        
        # Test range of hash values
        for h in hash_values:
            self.assertTrue(0 <= h < self.symbol_table.table_size, 
                           f"Hash value {h} out of range [0, {self.symbol_table.table_size})")
        
        # Test consistent hashing
        for lexeme in lexemes:
            self.assertEqual(self.symbol_table._hash(lexeme), self.symbol_table._hash(lexeme),
                            "Hash function should be deterministic")

    def test_insert_lookup_basic(self):
        """Test basic insert and lookup functionality"""
        # Insert an entry
        entry = self.symbol_table.insert("testVar", self.tokens['id'], 1)
        entry.set_variable_info(VarType.INT, 0, 4)
        
        # Look up the entry
        found = self.symbol_table.lookup("testVar")
        self.assertIsNotNone(found, "Should find the inserted entry")
        self.assertEqual(found.lexeme, "testVar", "Lookup should return the correct entry")
        self.assertEqual(found.entry_type, EntryType.VARIABLE, "Entry should be a variable")
        self.assertEqual(found.var_type, VarType.INT, "Variable should be of type INT")

    def test_insert_lookup_nonexistent(self):
        """Test lookup of nonexistent entries"""
        self.assertIsNone(self.symbol_table.lookup("nonexistent"), 
                         "Lookup of nonexistent entry should return None")

    def test_insert_lookup_multiple_entries(self):
        """Test inserting and looking up multiple entries"""
        # Insert multiple entries
        entries = {
            'var1': self.symbol_table.insert("counter", self.tokens['id'], 1),
            'var2': self.symbol_table.insert("index", self.tokens['id'], 1),
            'const1': self.symbol_table.insert("MAX_SIZE", self.tokens['id'], 1),
            'proc1': self.symbol_table.insert("calculate", self.tokens['id'], 1)
        }
        
        # Set entry information
        entries['var1'].set_variable_info(VarType.INT, 0, 4)
        entries['var2'].set_variable_info(VarType.INT, 4, 4)
        entries['const1'].set_constant_info(VarType.INT, 100)
        
        params = [Parameter(VarType.INT, ParameterMode.IN)]
        entries['proc1'].set_procedure_info(8, 1, VarType.INT, params)
        
        # Test lookups
        for lexeme in ["counter", "index", "MAX_SIZE", "calculate"]:
            self.assertIsNotNone(self.symbol_table.lookup(lexeme), 
                               f"Should find entry with lexeme '{lexeme}'")

    def test_write_table(self):
        """Test writing entries at specific depths"""
        # Insert entries at different depths
        depth1_entries = ["var1", "var2", "const1"]
        depth2_entries = ["local1", "local2"]
        
        # Insert depth 1 entries
        for lexeme in depth1_entries:
            entry = self.symbol_table.insert(lexeme, self.tokens['id'], 1)
            entry.set_variable_info(VarType.INT, 0, 4)
        
        # Insert depth 2 entries
        for lexeme in depth2_entries:
            entry = self.symbol_table.insert(lexeme, self.tokens['id'], 2)
            entry.set_variable_info(VarType.INT, 0, 4)
        
        # Test writeTable
        written_depth1 = self.symbol_table.writeTable(1)
        written_depth2 = self.symbol_table.writeTable(2)
        
        # Check that all entries are included
        self.assertEqual(len(written_depth1), len(depth1_entries), 
                        f"Should find {len(depth1_entries)} entries at depth 1")
        self.assertEqual(len(written_depth2), len(depth2_entries), 
                        f"Should find {len(depth2_entries)} entries at depth 2")
        
        # Check that the correct entries are at each depth
        for lexeme in depth1_entries:
            self.assertIn(lexeme, written_depth1, f"Entry '{lexeme}' should be at depth 1")
        for lexeme in depth2_entries:
            self.assertIn(lexeme, written_depth2, f"Entry '{lexeme}' should be at depth 2")

    def test_delete_depth(self):
        """Test deleting entries at specific depths"""
        # Insert entries at different depths
        for i in range(5):
            entry = self.symbol_table.insert(f"var{i}", self.tokens['id'], 1)
            entry.set_variable_info(VarType.INT, i*4, 4)
        
        for i in range(3):
            entry = self.symbol_table.insert(f"local{i}", self.tokens['id'], 2)
            entry.set_variable_info(VarType.INT, i*4, 4)
        
        # Check entries before deletion
        self.assertEqual(len(self.symbol_table.writeTable(1)), 5, 
                        "Should have 5 entries at depth 1 before deletion")
        self.assertEqual(len(self.symbol_table.writeTable(2)), 3, 
                        "Should have 3 entries at depth 2 before deletion")
        
        # Delete depth 2 entries
        self.symbol_table.deleteDepth(2)
        
        # Check entries after deletion
        self.assertEqual(len(self.symbol_table.writeTable(1)), 5, 
                        "Should still have 5 entries at depth 1 after deletion")
        self.assertEqual(len(self.symbol_table.writeTable(2)), 0, 
                        "Should have 0 entries at depth 2 after deletion")
        
        # Check that lookups still work for depth 1 entries
        for i in range(5):
            self.assertIsNotNone(self.symbol_table.lookup(f"var{i}"), 
                               f"Should still find entry 'var{i}' after deletion")

    def test_hash_collisions(self):
        """Test handling of hash collisions"""
        # Find two lexemes that hash to the same value
        # For testing, we'll use a smaller table size to increase collision probability
        small_table = AdaSymbolTable(table_size=11)
        
        # Find collision by brute force
        base_lexeme = "test"
        base_hash = small_table._hash(base_lexeme)
        
        collision_lexeme = None
        for i in range(100):
            candidate = f"collision{i}"
            if small_table._hash(candidate) == base_hash:
                collision_lexeme = candidate
                break
        
        # If we found a collision, test it
        if collision_lexeme:
            # Insert both lexemes
            entry1 = small_table.insert(base_lexeme, self.tokens['id'], 1)
            entry1.set_variable_info(VarType.INT, 0, 4)
            
            entry2 = small_table.insert(collision_lexeme, self.tokens['id'], 1)
            entry2.set_variable_info(VarType.FLOAT, 4, 8)
            
            # Lookup both entries
            found1 = small_table.lookup(base_lexeme)
            found2 = small_table.lookup(collision_lexeme)
            
            # Both should be found and have the correct types
            self.assertIsNotNone(found1, f"Should find entry '{base_lexeme}' after collision")
            self.assertIsNotNone(found2, f"Should find entry '{collision_lexeme}' after collision")
            self.assertEqual(found1.var_type, VarType.INT, "First entry should be INT")
            self.assertEqual(found2.var_type, VarType.FLOAT, "Second entry should be FLOAT")
        else:
            self.skipTest("Could not find hash collision in reasonable time")

    def test_entry_record_types(self):
        """Test different entry record types (variable, constant, procedure)"""
        # Insert a variable
        var = self.symbol_table.insert("counter", self.tokens['id'], 1)
        var.set_variable_info(VarType.INT, 0, 4)
        
        # Insert a constant
        const = self.symbol_table.insert("PI", self.tokens['id'], 1)
        const.set_constant_info(VarType.FLOAT, 3.14159)
        
        # Insert a procedure
        params = [
            Parameter(VarType.INT, ParameterMode.IN),
            Parameter(VarType.FLOAT, ParameterMode.OUT)
        ]
        proc = self.symbol_table.insert("calculate", self.tokens['procedure'], 1)
        proc.set_procedure_info(16, 2, VarType.INT, params)
        
        # Check variable
        found_var = self.symbol_table.lookup("counter")
        self.assertEqual(found_var.entry_type, EntryType.VARIABLE, "Should be a variable entry")
        self.assertEqual(found_var.var_type, VarType.INT, "Variable type should be INT")
        self.assertEqual(found_var.offset, 0, "Variable offset should be 0")
        self.assertEqual(found_var.size, 4, "Variable size should be 4")
        
        # Check constant
        found_const = self.symbol_table.lookup("PI")
        self.assertEqual(found_const.entry_type, EntryType.CONSTANT, "Should be a constant entry")
        self.assertEqual(found_const.const_type, VarType.FLOAT, "Constant type should be FLOAT")
        self.assertEqual(found_const.const_value, 3.14159, "Constant value should be correct")
        
        # Check procedure
        found_proc = self.symbol_table.lookup("calculate")
        self.assertEqual(found_proc.entry_type, EntryType.PROCEDURE, "Should be a procedure entry")
        self.assertEqual(found_proc.param_count, 2, "Procedure should have 2 parameters")
        self.assertEqual(found_proc.local_size, 16, "Procedure local size should be 16")
        self.assertEqual(found_proc.return_type, VarType.INT, "Procedure return type should be INT")
        self.assertEqual(len(found_proc.param_list), 2, "Procedure should have 2 parameters in list")
        self.assertEqual(found_proc.param_list[0].param_type, VarType.INT, "First parameter should be INT")
        self.assertEqual(found_proc.param_list[1].param_type, VarType.FLOAT, "Second parameter should be FLOAT")

    def test_integration_with_token_system(self):
        """Test integration with the compiler's token system"""
        # Create entries with actual Token objects
        var = self.symbol_table.insert("x", self.tokens['id'], 1)
        var.set_variable_info(VarType.INT, 0, 4)
        
        # Test token type is preserved
        found = self.symbol_table.lookup("x")
        self.assertEqual(found.token_type, self.tokens['id'], "Token should be preserved in entry")

    def test_stress_many_entries(self):
        """Stress test with many entries"""
        # Insert a large number of entries
        num_entries = 1000
        for i in range(num_entries):
            lexeme = f"var{i}"
            entry = self.symbol_table.insert(lexeme, self.tokens['id'], 1)
            entry.set_variable_info(VarType.INT, i*4, 4)
        
        # Check that all entries can be looked up
        for i in range(num_entries):
            lexeme = f"var{i}"
            found = self.symbol_table.lookup(lexeme)
            self.assertIsNotNone(found, f"Should find entry '{lexeme}' in stress test")
            self.assertEqual(found.offset, i*4, f"Entry '{lexeme}' should have correct offset")
        
        # Check table size hasn't changed
        self.assertEqual(self.symbol_table.table_size, 211, "Table size should remain constant")

    def test_scope_with_same_lexeme(self):
        """Test scope handling with the same lexeme at different depths"""
        # Insert same lexeme at different depths
        var1 = self.symbol_table.insert("x", self.tokens['id'], 1)
        var1.set_variable_info(VarType.INT, 0, 4)
        
        var2 = self.symbol_table.insert("x", self.tokens['id'], 2)
        var2.set_variable_info(VarType.FLOAT, 4, 8)
        
        # Lookup should find the most recent entry (higher depth)
        found = self.symbol_table.lookup("x")
        self.assertEqual(found.depth, 2, "Lookup should find entry at highest depth first")
        self.assertEqual(found.var_type, VarType.FLOAT, "Lookup should find FLOAT entry first")
        
        # Delete depth 2
        self.symbol_table.deleteDepth(2)
        
        # Now lookup should find the depth 1 entry
        found = self.symbol_table.lookup("x")
        self.assertEqual(found.depth, 1, "After deletion, lookup should find entry at depth 1")
        self.assertEqual(found.var_type, VarType.INT, "After deletion, lookup should find INT entry")

    def test_lookup_with_depth(self):
        """Test looking up entries with depth parameter."""
        # Create entries with the same lexeme at different depths
        self.symbol_table.insert("variable1", self.tokens['id'], 1).set_variable_info(VarType.INT, 0, 4)
        self.symbol_table.insert("variable1", self.tokens['id'], 2).set_variable_info(VarType.FLOAT, 4, 8)
        self.symbol_table.insert("variable1", self.tokens['id'], 3).set_variable_info(VarType.CHAR, 12, 1)
        
        # Look up by specific depths
        entry_depth1 = self.symbol_table.lookup("variable1", 1)
        self.assertIsNotNone(entry_depth1, "Entry at depth 1 should be found")
        self.assertEqual(entry_depth1.var_type, VarType.INT, "Entry at depth 1 should have INT type")
        
        entry_depth2 = self.symbol_table.lookup("variable1", 2)
        self.assertIsNotNone(entry_depth2, "Entry at depth 2 should be found")
        self.assertEqual(entry_depth2.var_type, VarType.FLOAT, "Entry at depth 2 should have FLOAT type")
        
        entry_depth3 = self.symbol_table.lookup("variable1", 3)
        self.assertIsNotNone(entry_depth3, "Entry at depth 3 should be found")
        self.assertEqual(entry_depth3.var_type, VarType.CHAR, "Entry at depth 3 should have CHAR type")
        
        # Non-existent depth should return None
        entry_depth4 = self.symbol_table.lookup("variable1", 4)
        self.assertIsNone(entry_depth4, "Entry at depth 4 should not be found")
        
        # Default lookup should find the most recent entry (highest depth number)
        entry_default = self.symbol_table.lookup("variable1")
        self.assertIsNotNone(entry_default, "Default lookup should find an entry")
        self.assertEqual(entry_default.depth, 3, "Default lookup should find entry at highest depth")
        self.assertEqual(entry_default.var_type, VarType.CHAR, "Default lookup should find CHAR type")
        
        # After deleting entries at depth 3, default lookup should find depth 2
        self.symbol_table.deleteDepth(3)
        entry_after_delete = self.symbol_table.lookup("variable1")
        self.assertEqual(entry_after_delete.depth, 2, "After deletion, lookup should find entry at depth 2")
        self.assertEqual(entry_after_delete.var_type, VarType.FLOAT, "After deletion, lookup should find FLOAT type")


def simple_test():
    """Run simple tests without unittest framework"""
    print("Simple Symbol Table Tests")
    print("-" * 40)
    
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
    
    print("Simple tests completed")


if __name__ == "__main__":
    # Run simple tests
    simple_test()
    print("\n" + "=" * 50 + "\n")
    
    # Run unittest tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
