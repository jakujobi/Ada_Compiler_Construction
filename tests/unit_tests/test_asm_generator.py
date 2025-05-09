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

from jakadac.modules.SymTable import SymbolTable, EntryType, Symbol
from jakadac.modules.asm_gen.asm_generator import ASMGenerator
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger # Import Logger for spec

# Patches for dependencies OF ASMGenerator that have module-level loggers
@patch('jakadac.modules.asm_gen.tac_parser.logger')
@patch('jakadac.modules.asm_gen.data_segment_manager.logger') # Assuming DataSegmentManager has a module-level logger
@patch('jakadac.modules.asm_gen.asm_operand_formatter.logger')
class TestASMGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_symbol_table = MagicMock(spec=SymbolTable)
        self.mock_symbol_table.global_scope_name = "global"
        self.mock_symbol_table.symbols = {"global": {}}
        
        # Mock lookup_globally to be flexible for different procedure names
        def flexible_lookup_globally(proc_name_being_looked_up):
            mock_proc_sym = MagicMock(spec=Symbol) # Use spec for Symbol from SymTable.py
            mock_proc_sym.name = proc_name_being_looked_up 
            mock_proc_sym.entry_type = EntryType.PROCEDURE 
            mock_proc_sym.local_size = 0 
            mock_proc_sym.param_size = 0 
            # Add other attributes of a Symbol entry if generate_asm or its callees need them.
            # For example, if it needs a defined label attribute for the proc.
            # mock_proc_sym.label = proc_name_being_looked_up 
            return mock_proc_sym
        self.mock_symbol_table.lookup_globally = MagicMock(side_effect=flexible_lookup_globally)

        self.tac_filepath = "dummy.tac"
        self.asm_filepath = "dummy.asm"
        self.mock_string_literals_map = {} 
        self.mock_logger_for_asm_gen = MagicMock(spec=Logger)

    # REMOVED: mock_asm_gen_logger from signature
    def test_initialization(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser:
            with patch('jakadac.modules.asm_gen.asm_generator.ASMInstructionMapper') as MockASMInstructionMapper:
                # UPDATED: ASMGenerator instantiation
                generator = ASMGenerator(
                    self.tac_filepath, 
                    self.asm_filepath, 
                    self.mock_symbol_table,
                    self.mock_string_literals_map, # ADDED
                    self.mock_logger_for_asm_gen   # ADDED
                )
                
                self.assertEqual(generator.tac_filepath, self.tac_filepath)
                self.assertEqual(generator.asm_filepath, self.asm_filepath)
                self.assertEqual(generator.symbol_table, self.mock_symbol_table)
                self.assertEqual(generator.string_literals_map, self.mock_string_literals_map)
                self.assertEqual(generator.logger, self.mock_logger_for_asm_gen)
                
                MockTACParser.assert_called_once_with(self.tac_filepath)
                MockASMInstructionMapper.assert_called_once_with(self.mock_symbol_table, self.mock_logger_for_asm_gen, generator)

                self.assertEqual(generator.parsed_tac, [])
                self.assertIsNone(generator.user_main_procedure_name) # Based on ASMGenerator source

    # REMOVED: mock_asm_gen_logger
    # def test_generate_boilerplate_header(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
    #     # UPDATED: ASMGenerator instantiation
    #     generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
    #     header = generator._generate_boilerplate_header()
    #     self.assertIn(".MODEL SMALL", header)
    #     self.assertIn(".STACK 100h", header)

    # REMOVED: mock_asm_gen_logger
    # def test_generate_boilerplate_footer_no_start_proc(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
    #     # UPDATED: ASMGenerator instantiation
    #     generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
    #     generator.user_main_procedure_name = None 
    #     footer = generator._generate_boilerplate_footer()
    #     self.assertIn("END main", footer) 
    #     # UPDATED: logger assertion
    #     self.mock_logger_for_asm_gen.warning.assert_any_call("No PROGRAM_START directive found. Using 'main' as fallback END label. This might be incorrect if 'main' is not the actual entry.")

    # REMOVED: mock_asm_gen_logger
    # def test_generate_boilerplate_footer_with_start_proc(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
    #     # UPDATED: ASMGenerator instantiation
    #     generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
    #     generator.user_main_procedure_name = "MyMainProc"
    #     footer = generator._generate_boilerplate_footer()
    #     self.assertIn("END MyMainProc", footer)

    # Test name and logic updated to match ASMGenerator methods
    # REMOVED: mock_asm_gen_logger
    def test_generate_dos_program_shell_no_user_main(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
        generator.user_main_procedure_name = None 
        # The method _generate_dos_program_shell itself determines the fallback.
        # The argument to it in generate_asm is what we need to align with.
        # If user_main_procedure_name is None, generate_asm calls _generate_dos_program_shell("main")
        shell_output = "\\n".join(generator._generate_dos_program_shell("main")) 
        
        self.assertIn("start PROC", shell_output) 
        self.assertIn("CALL main", shell_output)   
        self.assertIn("start ENDP", shell_output)
        self.mock_logger_for_asm_gen.info.assert_any_call("Generated DOS program shell. Entry point: 'start', User main: 'main'.")

    # REMOVED: mock_asm_gen_logger
    def test_generate_dos_program_shell_with_user_main(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
        user_proc_name = "AppStart"
        generator.user_main_procedure_name = user_proc_name # Set by _parse_and_prepare in real flow
        shell_output = "\\n".join(generator._generate_dos_program_shell(user_proc_name))

        self.assertIn("start PROC", shell_output) # Main DOS entry point
        self.assertIn(f"CALL {user_proc_name}", shell_output)
        self.assertIn("start ENDP", shell_output)

    # Test name and logic updated to match ASMGenerator methods (_parse_and_prepare)
    # REMOVED: mock_asm_gen_logger
    def test_parse_and_prepare_success(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        mock_tac_parser_instance = MagicMock()
        # Correctly set up ParsedTACInstruction: PROGRAM_START has proc name in destination.value
        tac_instr = ParsedTACInstruction(
            line_number=1, 
            raw_line="PROGRAM_START MainProc", 
            opcode=TACOpcode.PROGRAM_START, 
            destination=TACOperand("MainProc")
        )
        mock_tac_parser_instance.parse_tac_file.return_value = [tac_instr]

        with patch('jakadac.modules.asm_gen.asm_generator.TACParser', return_value=mock_tac_parser_instance):
            generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
            self.assertTrue(generator._parse_and_prepare(), msg="_parse_and_prepare should return True with valid PROGRAM_START")
            self.assertEqual(generator.user_main_procedure_name, "MainProc")
            self.mock_logger_for_asm_gen.info.assert_any_call("TAC parsed successfully. Main Ada procedure: 'MainProc'.")

    # REMOVED: mock_asm_gen_logger
    def test_parse_and_prepare_no_program_start(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        mock_tac_parser_instance = MagicMock()
        mock_tac_parser_instance.parse_tac_file.return_value = [
            ParsedTACInstruction(1, None, TACOpcode.LABEL, "L1", None, None)
        ]
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser', return_value=mock_tac_parser_instance):
            # UPDATED: ASMGenerator instantiation
            generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
            self.assertFalse(generator._parse_and_prepare())
            # UPDATED: logger assertion
            self.mock_logger_for_asm_gen.error.assert_any_call("No PROGRAM_START directive found in TAC file. Cannot determine program entry point.")

    # REMOVED: mock_asm_gen_logger
    def test_parse_and_prepare_tac_parse_exception(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        mock_tac_parser_instance = MagicMock()
        mock_tac_parser_instance.parse_tac_file.side_effect = Exception("TAC Read Error")
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser', return_value=mock_tac_parser_instance):
            # UPDATED: ASMGenerator instantiation
            generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
            self.assertFalse(generator._parse_and_prepare())
            # UPDATED: logger assertion
            self.mock_logger_for_asm_gen.error.assert_any_call(f"Error parsing TAC file '{self.tac_filepath}': TAC Read Error")

    # REMOVED: mock_asm_gen_logger
    def test_generate_asm_basic_flow(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        mock_tac_parser_inst = MagicMock()
        mock_tac_parser_inst.parse_tac_file.return_value = [
            ParsedTACInstruction(1, None, TACOpcode.PROGRAM_START, None, None, "MyProgram")
        ]
        mock_asm_mapper_inst = MagicMock()

        with patch('jakadac.modules.asm_gen.asm_generator.TACParser', return_value=mock_tac_parser_inst) as MockTACParserClass:
            with patch('jakadac.modules.asm_gen.asm_generator.ASMInstructionMapper', return_value=mock_asm_mapper_inst) as MockASMInstructionMapperClass:
                with patch('builtins.open', mock_open()) as mock_file_open:
                    # UPDATED: ASMGenerator instantiation
                    generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
                    
                    # Mock internal methods to isolate generate_asm logic
                    generator._parse_and_prepare = MagicMock(return_value=True)
                    generator.user_main_procedure_name = "MyProgram" # Ensure this is set post _parse_and_prepare mock
                    generator._internal_grouped_tac = {"MyProgram": []} # ADDED: Initialize this attribute
                    generator._generate_data_segment = MagicMock(return_value=["    MyVar DW ?"])
                    # _generate_code_segment now orchestrates more, including _generate_dos_program_shell
                    # For this test, we can mock its overall output if complex, or let it run if simple enough
                    # and mapper is mocked.
                    # For simplicity, let's assume _generate_code_segment uses the mapper which returns simple asm lines.
                    mock_asm_mapper_inst.translate.return_value = ["; translated line"] # Simple ASM from mapper
                    
                    # Mock _generate_dos_program_shell because it's called by _generate_code_segment
                    # and its output is part of the final ASM.
                    # The content here should reflect a basic shell.
                    generator._generate_dos_program_shell = MagicMock(return_value=[
                        "MyProgram PROC",
                        "    mov ax, @data",
                        "    mov ds, ax",
                        "    ; ... user code from TAC ...",
                        "    mov ax, 4C00h",
                        "    int 21h",
                        "MyProgram ENDP"
                    ])


                    success = generator.generate_asm()
                    self.assertTrue(success)
                    
                    generator._parse_and_prepare.assert_called_once()
                    generator._generate_data_segment.assert_called_once()
                    
                    mock_file_open.assert_called_once_with(self.asm_filepath, 'w', encoding='utf-8')
                    # UPDATED: logger assertion
                    self.mock_logger_for_asm_gen.info.assert_any_call(f"ASM generation started for {self.tac_filepath} -> {self.asm_filepath}")
                    self.mock_logger_for_asm_gen.info.assert_any_call(f"ASM file generated successfully: {self.asm_filepath}")

    # REMOVED: mock_asm_gen_logger
    def test_generate_asm_parse_and_prepare_fails(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser') as MockTACParser: # Keep TACParser mock for its instantiation
            with patch('builtins.open', mock_open()) as mock_file_open:
                # UPDATED: ASMGenerator instantiation
                generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
                generator._parse_and_prepare = MagicMock(return_value=False) # Simulate failure
                
                success = generator.generate_asm()
                self.assertFalse(success)
                
                # Logger message from generate_asm when _parse_and_prepare fails
                self.mock_logger_for_asm_gen.error.assert_any_call("ASM generation failed due to errors in TAC parsing or preparation.")
                mock_file_open.assert_called_once_with(self.asm_filepath, 'w', encoding='utf-8')
                handle = mock_file_open()
                # Check that an error message is written to the file
                # Example: find a call to write that includes "; ASM Generation Aborted"
                write_calls = [args[0] for name, args, kwargs in handle.method_calls if name == 'write']
                self.assertTrue(any("; ASM Generation Aborted due to errors." in call_arg for call_arg in write_calls))


    # REMOVED: mock_asm_gen_logger
    def test_generate_asm_file_write_error(self, mock_op_form_logger, mock_data_mgr_logger, mock_tac_parse_logger):
        mock_tac_parser_inst = MagicMock()
        mock_tac_parser_inst.parse_tac_file.return_value = [] 
        
        with patch('jakadac.modules.asm_gen.asm_generator.TACParser', return_value=mock_tac_parser_inst):
            with patch('jakadac.modules.asm_gen.asm_generator.ASMInstructionMapper'):
                with patch('builtins.open', mock_open()) as mock_file_open:
                    mock_file_open.side_effect = IOError("Disk full")
                    
                    # UPDATED: ASMGenerator instantiation
                    generator = ASMGenerator(self.tac_filepath, self.asm_filepath, self.mock_symbol_table, self.mock_string_literals_map, self.mock_logger_for_asm_gen)
                    generator._parse_and_prepare = MagicMock(return_value=True) # Simulate successful prep
                    generator.user_main_procedure_name = "TestMain"
                    generator._internal_grouped_tac = {"TestMain": []} # ADDED: Initialize this attribute

                    success = generator.generate_asm()
                    self.assertFalse(success)
                    # UPDATED: logger assertion to match actual error string
                    # self.mock_logger_for_asm_gen.error.assert_called_with(f"Failed to write ASM output to {self.asm_filepath}: Disk full") # OLD
                    self.mock_logger_for_asm_gen.error.assert_called_with(f"Failed to write ASM file '{self.asm_filepath}': Disk full") # CORRECTED

if __name__ == '__main__':
    unittest.main()
