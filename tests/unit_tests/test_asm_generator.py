# tests/unit_tests/test_asm_generator.py

import unittest
import sys
import os
from unittest.mock import MagicMock, patch, call, mock_open
from pathlib import Path

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.SymTable import SymbolTable #, SymbolTableEntry, EntryType, VarType
from jakadac.modules.asm_gen.asm_generator import ASMGenerator
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode
from jakadac.modules.asm_gen.asm_instruction_mapper import ASMInstructionMapper

# Mock the entire logger for all modules under asm_gen for these tests
# This is a broader approach if individual patching per class becomes cumbersome
@patch('jakadac.modules.asm_gen.asm_generator.logger')
@patch('jakadac.modules.asm_gen.tac_parser.logger') # ASMGenerator instantiates TACParser
@patch('jakadac.modules.asm_gen.data_segment_manager.logger') # ASMGenerator instantiates DataSegmentManager
@patch('jakadac.modules.asm_gen.asm_operand_formatter.logger') # ASMGenerator instantiates ASMOperandFormatter
@patch('jakadac.modules.asm_gen.asm_instruction_mapper.logger') # ASMGenerator instantiates ASMInstructionMapper
class TestASMGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_symbol_table = MagicMock(spec=SymbolTable)
        self.tac_filepath = "dummy.tac"
        self.asm_filepath = "dummy.asm"

    # The multiple logger patches are passed as arguments in reverse order of decorator application
    def test_initialization(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser:
            with patch('jakadac.modules.asm_gen.asm_generator.DataSegmentManager') as MockDataSegmentManager:
                with patch('jakadac.modules.asm_gen.asm_generator.ASMOperandFormatter') as MockASMOperandFormatter:
                    with patch('jakadac.modules.asm_gen.asm_generator.ASMInstructionMapper') as MockASMInstructionMapper:
                        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
                        
                        self.assertEqual(generator.tac_filepath, self.tac_filepath)
                        self.assertEqual(generator.asm_filepath, self.asm_filepath)
                        self.assertEqual(generator.symbol_table, self.mock_symbol_table)
                        
                        MockTACParser.assert_called_once_with(self.tac_filepath)
                        MockDataSegmentManager.assert_called_once_with(self.mock_symbol_table)
                        MockASMOperandFormatter.assert_called_once_with(self.mock_symbol_table)
                        MockASMInstructionMapper.assert_called_once_with(self.mock_symbol_table, MockASMOperandFormatter.return_value)
                        
                        self.assertEqual(generator.parsed_tac, [])
                        self.assertIsNone(generator.start_proc_name)

    def test_generate_boilerplate_header(self, *mocks):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        header = generator._generate_boilerplate_header()
        self.assertIn(".MODEL SMALL", header)
        self.assertIn(".STACK 100h", header)

    def test_generate_boilerplate_footer_no_start_proc(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        generator.start_proc_name = None
        footer = generator._generate_boilerplate_footer()
        self.assertIn("END main", footer)
        mock_asm_gen_logger.warning.assert_any_call("No STARTPROC found in TAC. Using 'main' as fallback END label. This might be incorrect.")

    def test_generate_boilerplate_footer_with_start_proc(self, *mocks):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        generator.start_proc_name = "MyMainProc"
        footer = generator._generate_boilerplate_footer()
        self.assertIn("END MyMainProc", footer)

    def test_generate_main_procedure_shell_no_start_proc(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        generator.start_proc_name = None
        shell = generator._generate_main_procedure_shell()
        self.assertIn("main PROC", "\n".join(shell))
        self.assertIn("main ENDP", "\n".join(shell))
        mock_asm_gen_logger.warning.assert_any_call("Main procedure name not identified from STARTPROC TAC. Using 'main' as fallback.")

    def test_generate_main_procedure_shell_with_start_proc(self, *mocks):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        generator.start_proc_name = "AppStart"
        shell = generator._generate_main_procedure_shell()
        self.assertIn("AppStart PROC", "\n".join(shell))
        self.assertIn("AppStart ENDP", "\n".join(shell))

    def test_scan_for_start_procedure_found(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        tac_instructions = [
            ParsedTACInstruction(1, None, TACOpcode.LABEL, "L1", None, None),
            ParsedTACInstruction(2, None, TACOpcode.PROGRAM_START, None, None, "MainProc"),
            ParsedTACInstruction(3, None, TACOpcode.ASSIGN, "_t0", "5", None)
        ]
        generator._scan_for_start_procedure(tac_instructions)
        self.assertEqual(generator.start_proc_name, "MainProc")
        mock_asm_gen_logger.info.assert_any_call("STARTPROC found. Main procedure identified as: MainProc")

    def test_scan_for_start_procedure_not_found(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        tac_instructions = [
            ParsedTACInstruction(1, None, TACOpcode.LABEL, "L1", None, None),
            ParsedTACInstruction(2, None, TACOpcode.ASSIGN, "_t0", "5", None)
        ]
        generator._scan_for_start_procedure(tac_instructions)
        self.assertIsNone(generator.start_proc_name)
        mock_asm_gen_logger.info.assert_any_call("No STARTPROC directive found in TAC instructions.")

    def test_scan_for_start_procedure_startproc_no_dest(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
        tac_instructions = [ParsedTACInstruction(1, None, TACOpcode.PROGRAM_START, None, None, None)]
        generator._scan_for_start_procedure(tac_instructions)
        self.assertIsNone(generator.start_proc_name)
        mock_asm_gen_logger.warning.assert_any_call("STARTPROC found but 'dest' (procedure name) is missing.")

    def test_generate_asm_basic_flow(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser:
            with patch('jakadac.modules.asm_gen.asm_generator.DataSegmentManager') as MockDataSegmentManager:
                with patch('builtins.open', mock_open()) as mock_file_open:
                    
                    mock_tac_parser_instance = MockTACParser.return_value
                    mock_tac_parser_instance.parse_tac_file.return_value = [
                        ParsedTACInstruction(1, None, TACOpcode.PROGRAM_START, None, None, "MyProgram")
                    ]
                    
                    mock_data_manager_instance = MockDataSegmentManager.return_value
                    mock_data_manager_instance.get_data_section_asm.return_value = ".DATA\n    MyVar DW ?"
                    
                    generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
                    # Re-assign mocks as __init__ would have used the class-level ones
                    generator.tac_parser = mock_tac_parser_instance
                    generator.data_manager = mock_data_manager_instance
                    
                    generator.generate_asm()
                    
                    mock_tac_parser_instance.parse_tac_file.assert_called_once()
                    mock_data_manager_instance.collect_definitions.assert_called_once()
                    mock_data_manager_instance.get_data_section_asm.assert_called_once()
                    
                    self.assertEqual(generator.start_proc_name, "MyProgram")
                    
                    mock_file_open.assert_called_once_with(self.asm_filepath, 'w')
                    handle = mock_file_open()
                    written_content = "".join(call_args[0][0] for call_args in handle.write.call_args_list)
                    
                    self.assertIn(".MODEL SMALL", written_content)
                    self.assertIn(".STACK 100h", written_content)
                    self.assertIn(".DATA\n    MyVar DW ?", written_content)
                    self.assertIn(".CODE", written_content)
                    self.assertIn("MyProgram PROC", written_content)
                    self.assertIn("mov ax, @data", written_content) # Part of main shell
                    self.assertIn("mov ax, 4C00h", written_content) # Part of main shell
                    self.assertIn("MyProgram ENDP", written_content)
                    self.assertIn("include io.asm", written_content)
                    self.assertIn("END MyProgram", written_content)
                    mock_asm_gen_logger.info.assert_any_call(f"Starting ASM generation for {self.tac_filepath} -> {self.asm_filepath}")
                    mock_asm_gen_logger.info.assert_any_call(f"ASM file generated successfully: {self.asm_filepath}")

    def test_generate_asm_tac_parsing_error(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser:
            with patch('builtins.open', mock_open()) as mock_file_open:
                mock_tac_parser_instance = MockTACParser.return_value
                mock_tac_parser_instance.parse_tac_file.side_effect = Exception("TAC Read Error")
                
                generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
                generator.tac_parser = mock_tac_parser_instance # Re-assign after init
                
                generator.generate_asm()
                
                mock_asm_gen_logger.error.assert_called_with("Error during TAC parsing: TAC Read Error")
                mock_file_open.assert_called_once_with(self.asm_filepath, 'w')
                handle = mock_file_open()
                handle.write.assert_called_once_with("; Error during TAC parsing: TAC Read Error\n")

    def test_generate_asm_file_write_error(self, mock_ins_map_logger, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger, mock_asm_gen_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser:
            with patch('jakadac.modules.asm_gen.asm_generator.DataSegmentManager'):
                with patch('builtins.open', mock_open()) as mock_file_open:
                    
                    mock_tac_parser_instance = MockTACParser.return_value
                    mock_tac_parser_instance.parse_tac_file.return_value = [] # Empty TAC list
                    
                    mock_file_open.side_effect = IOError("Disk full")
                    
                    generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table)
                    generator.tac_parser = mock_tac_parser_instance # Re-assign

                    generator.generate_asm()
                    mock_asm_gen_logger.error.assert_called_with(f"Failed to write ASM file {self.asm_filepath}: Disk full")

if __name__ == '__main__':
    unittest.main()
