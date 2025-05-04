#!/usr/bin/env python3
# test_asm_generator.py
# Author: AI Assistant
# Date: 2024-05-08
# Version: 1.0
"""
Unit tests for the ASM Generator components.
"""

import unittest
import os
import tempfile
from unittest.mock import MagicMock, patch

# Import components to test
import sys
import os.path as path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from tac_instruction import TACInstruction
from data_segment_manager import DataSegmentManager
from asm_operand_formatter import ASMOperandFormatter

class TestTACInstruction(unittest.TestCase):
    """Test cases for the TACInstruction class."""
    
    def test_from_tuple_assignment(self):
        """Test parsing an assignment instruction."""
        tac = ('=', 'a', 'b')
        instr = TACInstruction.from_tuple(tac)
        
        self.assertEqual(instr.opcode, '=')
        self.assertEqual(instr.dest, 'a')
        self.assertEqual(instr.op1, 'b')
        self.assertIsNone(instr.op2)
        self.assertEqual(instr.original_tuple, tac)
    
    def test_from_tuple_binary_op(self):
        """Test parsing a binary operation instruction."""
        tac = ('+', 'c', 'a', 'b')
        instr = TACInstruction.from_tuple(tac)
        
        self.assertEqual(instr.opcode, '+')
        self.assertEqual(instr.dest, 'c')
        self.assertEqual(instr.op1, 'a')
        self.assertEqual(instr.op2, 'b')
        self.assertEqual(instr.original_tuple, tac)
    
    def test_from_tuple_proc(self):
        """Test parsing a procedure declaration."""
        tac = ('proc', 'main')
        instr = TACInstruction.from_tuple(tac)
        
        self.assertEqual(instr.opcode, 'proc')
        self.assertEqual(instr.op1, 'main')
        self.assertIsNone(instr.dest)
        self.assertIsNone(instr.op2)
        self.assertEqual(instr.original_tuple, tac)

class TestASMOperandFormatter(unittest.TestCase):
    """Test cases for the ASMOperandFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for temp_offsets
        self.temp_offsets = {
            'main': {
                '_t1': -8,
                '_t2': -10
            }
        }
        self.formatter = ASMOperandFormatter(self.temp_offsets)
        self.formatter.set_current_procedure('main')
    
    def test_format_immediate(self):
        """Test formatting an immediate value."""
        self.assertEqual(self.formatter.format_operand('42'), '42')
        self.assertEqual(self.formatter.format_operand('-7'), '-7')
    
    def test_format_bp_relative(self):
        """Test formatting BP-relative addresses."""
        self.assertEqual(self.formatter.format_operand('_BP+4'), '[bp+4]')
        self.assertEqual(self.formatter.format_operand('_BP-6'), '[bp-6]')
    
    def test_format_string_label(self):
        """Test formatting string labels."""
        self.assertEqual(self.formatter.format_operand('_S0'), '_S0')
        self.assertEqual(self.formatter.format_operand('_S1'), '_S1')
    
    def test_format_temp(self):
        """Test formatting temporary variables."""
        self.assertEqual(self.formatter.format_operand('_t1'), '[bp-8]')
        self.assertEqual(self.formatter.format_operand('_t2'), '[bp-10]')
    
    def test_format_global(self):
        """Test formatting global variables."""
        self.assertEqual(self.formatter.format_operand('globalVar'), 'globalVar')

class TestDataSegmentManager(unittest.TestCase):
    """Test cases for the DataSegmentManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock SymbolTable with EntryType enum
        self.symbol_table = MagicMock()
        
        # Set up EntryType enum mock
        class EntryType:
            VARIABLE = 1
            PROCEDURE = 2
            FUNCTION = 3
            PARAMETER = 4
            CONSTANT = 5
        
        self.symbol_table.EntryType = EntryType
        
        # Create a mock Symbol class
        class Symbol:
            def __init__(self, name, entry_type):
                self.name = name
                self.entry_type = entry_type
        
        # Set up global scope with variables
        global_scope = {
            'var1': Symbol('var1', EntryType.VARIABLE),
            'var2': Symbol('var2', EntryType.VARIABLE),
            'proc1': Symbol('proc1', EntryType.PROCEDURE)
        }
        
        # Mock get_scope_at_depth to return our global scope
        self.symbol_table.get_scope_at_depth.return_value = global_scope
        
        # Create DataSegmentManager instance
        self.data_manager = DataSegmentManager(self.symbol_table)
    
    def test_collect_definitions(self):
        """Test collecting global variable definitions."""
        self.data_manager.collect_definitions()
        
        # Check that global variables were collected (only variables, not procedures)
        self.assertEqual(len(self.data_manager.global_vars), 2)
        self.assertIn('var1', self.data_manager.global_vars)
        self.assertIn('var2', self.data_manager.global_vars)
        self.assertNotIn('proc1', self.data_manager.global_vars)
    
    def test_get_data_section_asm(self):
        """Test generating the .data section assembly."""
        # Collect definitions first
        self.data_manager.collect_definitions()
        
        # Define some string literals
        string_literals = {
            '_S0': 'Hello$',
            '_S1': 'World$'
        }
        
        # Generate data section
        data_lines = self.data_manager.get_data_section_asm(string_literals)
        
        # Check section directive
        self.assertEqual(data_lines[0], 'section .data')
        
        # Check string literals section
        self.assertIn('; --- String Literals ---', data_lines)
        self.assertIn('_S0      db      "Hello$"', data_lines)
        self.assertIn('_S1      db      "World$"', data_lines)
        
        # Check global variables section
        self.assertIn('; --- Global Variables ---', data_lines)
        self.assertIn('var1     dw      ?', data_lines)
        self.assertIn('var2     dw      ?', data_lines)

if __name__ == '__main__':
    unittest.main() 