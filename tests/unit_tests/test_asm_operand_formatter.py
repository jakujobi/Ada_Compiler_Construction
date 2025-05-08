# tests/unit_tests/test_asm_operand_formatter.py

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Modules to test/mock
from jakadac.modules.SymTable import *
from jakadac.modules.asm_gen.asm_operand_formatter import ASMOperandFormatter
from jakadac.modules.Logger import Logger

@patch('jakadac.modules.asm_gen.asm_operand_formatter.logger')
class TestASMOperandFormatter(unittest.TestCase):

    def create_mock_symbol_entry(self, name, entry_type, depth=0, const_value=None, var_type=None, offset=None):
        mock_entry = MagicMock(spec=Symbol)
        mock_entry.name = name
        mock_entry.entry_type = entry_type
        mock_entry.depth = depth
        mock_entry.const_value = const_value
        mock_entry.var_type = var_type if var_type else MagicMock(spec=VarType)
        mock_entry.offset = offset
        mock_entry.scope = f"scope_depth_{depth}"
        return mock_entry

    def setUp(self):
        self.mock_symbol_table = MagicMock(spec=SymbolTable)
        self.formatter = ASMOperandFormatter(self.mock_symbol_table)

    def test_initialization(self, mock_logger):
        self.assertEqual(self.formatter.symbol_table, self.mock_symbol_table)
        mock_logger.debug.assert_not_called()

    def test_format_operand_integer_immediate(self, mock_logger):
        self.assertEqual(self.formatter.format_operand("123"), "123")
        self.assertEqual(self.formatter.format_operand("-5"), "-5")
        mock_logger.debug.assert_any_call("ASMOperandFormatter: Formatting operand: '123' (context: None)", stacklevel=2)
        mock_logger.debug.assert_any_call("Formatted '123' as immediate integer: 123")

    def test_format_operand_global_variable(self, mock_logger):
        global_var_entry = self.create_mock_symbol_entry("MyGlobal", EntryType.VARIABLE, depth=1)
        self.mock_symbol_table.lookup.return_value = global_var_entry
        
        self.assertEqual(self.formatter.format_operand("MyGlobal"), "MyGlobal")
        self.mock_symbol_table.lookup.assert_called_with("MyGlobal")
        mock_logger.debug.assert_any_call("Formatted 'MyGlobal' as global variable/constant: MyGlobal")

    def test_format_operand_global_variable_c(self, mock_logger):
        global_var_entry = self.create_mock_symbol_entry("c", EntryType.VARIABLE, depth=1)
        self.mock_symbol_table.lookup.return_value = global_var_entry

        self.assertEqual(self.formatter.format_operand("c"), "cc")
        self.mock_symbol_table.lookup.assert_called_with("c")
        mock_logger.debug.assert_any_call("Formatted 'c' as global variable/constant: cc")

    def test_format_operand_string_label_wrs_context(self, mock_logger):
        try:
            from jakadac.modules.asm_gen.tac_instruction import TACOpcode
            wrs_opcode = TACOpcode.WRITE_STR
        except ImportError:
            wrs_opcode = "WRITE_STR"
        
        self.assertEqual(self.formatter.format_operand("_S0", context_opcode=wrs_opcode), "OFFSET _S0")
        mock_logger.debug.assert_any_call("Formatted string label '_S0' as OFFSET _S0 for WRS context.")

    def test_format_operand_string_label_no_wrs_context(self, mock_logger):
        self.assertEqual(self.formatter.format_operand("_S1"), "_S1")
        try:
            from jakadac.modules.asm_gen.tac_instruction import TACOpcode
            mov_opcode = TACOpcode.ASSIGN
        except ImportError:
            mov_opcode = "ASSIGN"
            
        self.assertEqual(self.formatter.format_operand("_S1", context_opcode=mov_opcode), "_S1")
        mock_logger.debug.assert_any_call("Formatted string label '_S1' as itself (non-WRS context). Potential address needed.")

    def test_format_operand_temporary_variable(self, mock_logger):
        temp_entry = self.create_mock_symbol_entry("_t1", EntryType.VARIABLE, depth=2, offset=0)
        self.mock_symbol_table.lookup.return_value = temp_entry
        
        self.assertEqual(self.formatter.format_operand("_t1"), "[bp-2]")
        self.mock_symbol_table.lookup.assert_called_with("_t1")
        mock_logger.debug.assert_any_call("Calculated LOCAL/TEMP variable offset for '_t1' (internal: 0) -> [bp-2]")

    def test_format_operand_procedure_label_or_other_identifier(self, mock_logger):
        proc_entry = self.create_mock_symbol_entry("MyProc", EntryType.PROCEDURE, depth=0)
        self.mock_symbol_table.lookup.return_value = proc_entry
        self.assertEqual(self.formatter.format_operand("MyProc"), "MyProc")
        mock_logger.debug.assert_any_call("Formatted 'MyProc' as procedure/function/type name: MyProc")

        self.mock_symbol_table.lookup.side_effect = SymbolNotFoundError("L1")
        self.assertEqual(self.formatter.format_operand("L1"), "L1")
        mock_logger.debug.assert_any_call("Operand 'L1' not found in symbol table or matched other patterns. Returning as potential label/temp name.")
        self.mock_symbol_table.lookup.side_effect = None

    def test_format_operand_unknown_symbol_fallback(self, mock_logger):
        self.mock_symbol_table.lookup.side_effect = SymbolNotFoundError("unknown_op@")
        self.assertEqual(self.formatter.format_operand("unknown_op@"), "unknown_op@")
        mock_logger.debug.assert_any_call("Operand 'unknown_op@' not found in symbol table or matched other patterns. Returning as potential label/temp name.")
        self.mock_symbol_table.lookup.side_effect = None

    def test_format_operand_local_variable(self, mock_logger):
        local_var_entry = self.create_mock_symbol_entry("LocalA", EntryType.VARIABLE, depth=2, offset=2)
        self.mock_symbol_table.lookup.return_value = local_var_entry
        
        self.assertEqual(self.formatter.format_operand("LocalA"), "[bp-4]")
        self.mock_symbol_table.lookup.assert_called_with("LocalA")
        mock_logger.debug.assert_any_call("Calculated LOCAL/TEMP variable offset for 'LocalA' (internal: 2) -> [bp-4]")

    def test_format_operand_parameter(self, mock_logger):
        param_entry = self.create_mock_symbol_entry("ParamX", EntryType.PARAMETER, depth=2, offset=0)
        self.mock_symbol_table.lookup.return_value = param_entry
        
        self.assertEqual(self.formatter.format_operand("ParamX"), "[bp+4]")
        self.mock_symbol_table.lookup.assert_called_with("ParamX")
        mock_logger.debug.assert_any_call("Calculated PARAMETER offset for 'ParamX' (internal: 0) -> [bp+4]")

    def test_format_operand_parameter_second(self, mock_logger):
        param_entry = self.create_mock_symbol_entry("ParamY", EntryType.PARAMETER, depth=2, offset=2)
        self.mock_symbol_table.lookup.return_value = param_entry
        
        self.assertEqual(self.formatter.format_operand("ParamY"), "[bp+6]")
        self.mock_symbol_table.lookup.assert_called_with("ParamY")
        mock_logger.debug.assert_any_call("Calculated PARAMETER offset for 'ParamY' (internal: 2) -> [bp+6]")

    def test_format_operand_local_no_offset(self, mock_logger):
        local_no_offset = self.create_mock_symbol_entry("NoOffsetLocal", EntryType.VARIABLE, depth=2, offset=None)
        self.mock_symbol_table.lookup.return_value = local_no_offset
        
        self.assertEqual(self.formatter.format_operand("NoOffsetLocal"), "<ERROR_NO_OFFSET_NoOffsetLocal>")
        mock_logger.error.assert_any_call("Local/Param operand 'NoOffsetLocal' (Depth 2) in scope 'scope_depth_2' has no offset.")

if __name__ == '__main__':
    unittest.main()
