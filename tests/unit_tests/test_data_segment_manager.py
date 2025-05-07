# tests/unit_tests/test_data_segment_manager.py

import unittest
from unittest.mock import MagicMock, patch


repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Adjust the import path based on your project structure
from jakadac.modules.SymTable import SymbolTable, Symbol, EntryType, VarType # Assuming VarType is needed for SymbolTableEntry
from jakadac.modules.asm_gen.data_segment_manager import DataSegmentManager
from jakadac.modules.Logger import Logger

# Mock logger to prevent actual logging during tests
@patch('jakadac.modules.asm_gen.data_segment_manager.logger')
class TestDataSegmentManager(unittest.TestCase):

    def create_mock_symbol_entry(self, name, entry_type, depth=0, const_value=None, var_type=None, is_param=False, size=0, offset=0):
        mock_entry = MagicMock(spec=Symbol)
        mock_entry.name = name
        mock_entry.entry_type = entry_type
        mock_entry.depth = depth
        mock_entry.const_value = const_value
        mock_entry.var_type = var_type if var_type else MagicMock(spec=VarType)
        mock_entry.is_parameter = is_param
        mock_entry.size = size
        mock_entry.offset = offset
        return mock_entry

    def test_initialization(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        manager = DataSegmentManager(mock_symbol_table)
        self.assertEqual(manager.symbol_table, mock_symbol_table)
        self.assertEqual(manager.global_vars, {})
        self.assertEqual(manager.string_literals, {})
        mock_logger.debug.assert_not_called() # Initialization itself might not log debug

    def test_collect_definitions_empty_symbol_table(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        mock_symbol_table.table = {}
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        self.assertEqual(manager.global_vars, {})
        self.assertEqual(manager.string_literals, {})
        mock_logger.debug.assert_any_call("DataSegmentManager: Collecting definitions from symbol table.")

    def test_collect_definitions_globals_only(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        global_var1 = self.create_mock_symbol_entry("GlobalA", EntryType.VARIABLE, depth=1)
        global_var2 = self.create_mock_symbol_entry("GlobalB", EntryType.VARIABLE, depth=1)
        local_var = self.create_mock_symbol_entry("LocalC", EntryType.VARIABLE, depth=2)
        mock_symbol_table.table = {
            "GlobalA": global_var1,
            "GlobalB": global_var2,
            "LocalC": local_var
        }
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        self.assertEqual(manager.global_vars, {"GlobalA": "DW ?", "GlobalB": "DW ?"})
        self.assertEqual(manager.string_literals, {})
        mock_logger.debug.assert_any_call("Collected global variable: GlobalA DW ?")
        mock_logger.debug.assert_any_call("Collected global variable: GlobalB DW ?")

    def test_collect_definitions_strings_only(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        str_const1 = self.create_mock_symbol_entry("_S0", EntryType.CONSTANT, const_value="Hello")
        str_const2 = self.create_mock_symbol_entry("_S1", EntryType.CONSTANT, const_value="World")
        num_const = self.create_mock_symbol_entry("NUM_CONST", EntryType.CONSTANT, const_value=123)
        proc_entry = self.create_mock_symbol_entry("MyProc", EntryType.PROCEDURE)
        mock_symbol_table.table = {
            "_S0": str_const1,
            "_S1": str_const2,
            "NUM_CONST": num_const,
            "MyProc": proc_entry
        }
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        self.assertEqual(manager.global_vars, {})
        self.assertEqual(manager.string_literals, {"_S0": "Hello", "_S1": "World"})
        mock_logger.debug.assert_any_call('Collected string literal: _S0 -> "Hello"')
        mock_logger.debug.assert_any_call('Collected string literal: _S1 -> "World"')

    def test_collect_definitions_mixed_content(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        global_var = self.create_mock_symbol_entry("MyGlobal", EntryType.VARIABLE, depth=1)
        str_const = self.create_mock_symbol_entry("_S_Greeting", EntryType.CONSTANT, const_value="Hi there")
        mock_symbol_table.table = {"MyGlobal": global_var, "_S_Greeting": str_const}
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        self.assertEqual(manager.global_vars, {"MyGlobal": "DW ?"})
        self.assertEqual(manager.string_literals, {"_S_Greeting": "Hi there"})

    def test_get_data_section_asm_empty(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        mock_symbol_table.table = {}
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions() # Populate internal lists (they will be empty)
        asm_output = manager.get_data_section_asm()
        expected_asm = ".DATA\n    ; No global variables or string literals defined in the .DATA section."
        self.assertEqual(asm_output.strip(), expected_asm.strip())

    def test_get_data_section_asm_globals_only_sorted(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        global_b = self.create_mock_symbol_entry("GlobalB", EntryType.VARIABLE, depth=1)
        global_a = self.create_mock_symbol_entry("GlobalA", EntryType.VARIABLE, depth=1)
        mock_symbol_table.table = {"GlobalB": global_b, "GlobalA": global_a}
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        asm_output = manager.get_data_section_asm()
        expected_asm = (
            ".DATA\n"
            "    GlobalA DW ?\n"
            "    GlobalB DW ?"
        )
        self.assertEqual(asm_output.strip(), expected_asm.strip())

    def test_get_data_section_asm_strings_only_sorted(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        str_s1 = self.create_mock_symbol_entry("_S1", EntryType.CONSTANT, const_value="World")
        str_s0 = self.create_mock_symbol_entry("_S0", EntryType.CONSTANT, const_value="Hello")
        mock_symbol_table.table = {"_S1": str_s1, "_S0": str_s0}
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        asm_output = manager.get_data_section_asm()
        expected_asm = (
            ".DATA\n"
            "    _S0 DB \"Hello\", '$'\n"
            "    _S1 DB \"World\", '$'"
        )
        self.assertEqual(asm_output.strip(), expected_asm.strip())

    def test_get_data_section_asm_mixed_sorted(self, mock_logger):
        mock_symbol_table = MagicMock(spec=SymbolTable)
        global_b = self.create_mock_symbol_entry("VarX", EntryType.VARIABLE, depth=1)
        str_s1 = self.create_mock_symbol_entry("_S_Test", EntryType.CONSTANT, const_value="Test Str")
        global_a = self.create_mock_symbol_entry("VarA", EntryType.VARIABLE, depth=1)
        str_s0 = self.create_mock_symbol_entry("_S_Another", EntryType.CONSTANT, const_value="Another")
        mock_symbol_table.table = {
            "VarX": global_b, 
            "_S_Test": str_s1, 
            "VarA": global_a, 
            "_S_Another": str_s0
        }
        manager = DataSegmentManager(mock_symbol_table)
        manager.collect_definitions()
        asm_output = manager.get_data_section_asm()
        # Note: Globals are typically listed before strings due to typical ASM practices, 
        # but current implementation sorts all collected items together by name.
        # If specific ordering (globals then strings) is desired, collect_definitions or get_data_section_asm needs adjustment.
        # The current sorting is purely alphabetical by label/name.
        expected_asm = (
            ".DATA\n"
            "    VarA DW ?\n"
            "    VarX DW ?\n"
            "    _S_Another DB \"Another\", '$'\n"
            "    _S_Test DB \"Test Str\", '$'"
        )
        # Adjusting expectation based on current implementation: Globals sorted, then strings sorted
        # Actually, it will be fully mixed and sorted alphabetically by name.
        expected_asm_actual_sorting = (
            ".DATA\n"
            "    VarA DW ?\n"
            "    VarX DW ?\n"
            "    _S_Another DB \"Another\", '$'\n"
            "    _S_Test DB \"Test Str\", '$'"
        )
        # The sorting in DataSegmentManager is: all global_vars sorted, then all string_literals sorted.
        # So VarA, VarX then _S_Another, _S_Test is correct.
        self.assertEqual(asm_output.strip(), expected_asm_actual_sorting.strip())

if __name__ == '__main__':
    unittest.main()
