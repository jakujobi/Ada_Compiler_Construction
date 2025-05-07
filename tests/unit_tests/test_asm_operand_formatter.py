# tests/unit_tests/test_asm_operand_formatter.py

import unittest
from unittest.mock import MagicMock, patch


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

    def create_mock_symbol_entry(self, name, entry_type, depth=0, const_value=None, var_type=None):
        mock_entry = MagicMock(spec=Symbol)
        mock_entry.name = name
        mock_entry.entry_type = entry_type
        mock_entry.depth = depth
        mock_entry.const_value = const_value
        mock_entry.var_type = var_type if var_type else MagicMock(spec=VarType)
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
        mock_logger.debug.assert_any_call("ASMOperandFormatter: Formatting operand: '123' (context: None)")
        mock_logger.debug.assert_any_call("Formatted '123' as immediate: 123")

    def test_format_operand_global_variable(self, mock_logger):
        global_var_entry = self.create_mock_symbol_entry("MyGlobal", EntryType.VARIABLE, depth=1)
        self.mock_symbol_table.lookup_any_depth.return_value = global_var_entry
        
        self.assertEqual(self.formatter.format_operand("MyGlobal"), "MyGlobal")
        self.mock_symbol_table.lookup_any_depth.assert_called_with("MyGlobal")
        mock_logger.debug.assert_any_call("Formatted 'MyGlobal' as global variable: MyGlobal")

    def test_format_operand_string_label_wrs_context(self, mock_logger):
        string_label_entry = self.create_mock_symbol_entry("_S0", EntryType.CONSTANT, const_value="AString")
        self.mock_symbol_table.lookup_any_depth.return_value = string_label_entry
        
        self.assertEqual(self.formatter.format_operand("_S0", context_opcode="WRS"), "OFFSET _S0")
        self.mock_symbol_table.lookup_any_depth.assert_called_with("_S0")
        mock_logger.debug.assert_any_call("Formatted string label '_S0' as OFFSET _S0")

    def test_format_operand_string_label_no_wrs_context(self, mock_logger):
        string_label_entry = self.create_mock_symbol_entry("_S1", EntryType.CONSTANT, const_value="Another")
        self.mock_symbol_table.lookup_any_depth.return_value = string_label_entry
        
        self.assertEqual(self.formatter.format_operand("_S1"), "_S1") # Default context
        self.assertEqual(self.formatter.format_operand("_S1", context_opcode="MOV"), "_S1") # Other context
        mock_logger.debug.assert_any_call("Formatted string label '_S1' as _S1")

    def test_format_operand_temporary_variable(self, mock_logger):
        # Temporaries don't typically exist in symbol table as entries we check here, 
        # but are recognized by name pattern if not found otherwise.
        self.mock_symbol_table.lookup_any_depth.return_value = None 
        self.assertEqual(self.formatter.format_operand("_t1"), "_t1")
        mock_logger.debug.assert_any_call("Operand '_t1' treated as a non-immediate identifier (temp, local, label). Returning as is.")

    def test_format_operand_procedure_label_or_other_identifier(self, mock_logger):
        # Identifiers not in symbol table and not matching temp pattern are returned as is.
        self.mock_symbol_table.lookup_any_depth.return_value = None
        self.assertEqual(self.formatter.format_operand("MyProc"), "MyProc")
        self.assertEqual(self.formatter.format_operand("L1"), "L1")
        mock_logger.debug.assert_any_call("Operand 'MyProc' treated as a non-immediate identifier (temp, local, label). Returning as is.")

    def test_format_operand_unknown_symbol_fallback(self, mock_logger):
        self.mock_symbol_table.lookup_any_depth.return_value = None
        # Assuming 'unknown_op' is not a number, not a _t var, not _S string label
        # and not found in symbol table
        self.assertEqual(self.formatter.format_operand("unknown_op@"), "unknown_op@") # Non-identifier
        mock_logger.warning.assert_called_with("Could not definitively format operand: 'unknown_op@'. Returning as is. This may indicate an unhandled case or an error.")

    def test_format_operand_non_global_variable_as_identifier(self, mock_logger):
        # For phase 2, non-global variables (depth > 1) or params are not yet [BP+/-offset]
        # They should be returned as is, like other identifiers, if not an immediate.
        local_var_entry = self.create_mock_symbol_entry("LocalA", EntryType.VARIABLE, depth=2)
        self.mock_symbol_table.lookup_any_depth.return_value = local_var_entry
        
        # Since the current format_operand specifically checks for depth == 1 for globals,
        # a depth > 1 variable will fall through to the generic identifier handling if not immediate.
        self.assertEqual(self.formatter.format_operand("LocalA"), "LocalA")
        mock_logger.debug.assert_any_call("Operand 'LocalA' treated as a non-immediate identifier (temp, local, label). Returning as is.")

if __name__ == '__main__':
    unittest.main()
