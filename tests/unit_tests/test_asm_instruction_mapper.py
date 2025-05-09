import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, call, patch
import sys
from enum import Enum

# --- Adjust path to import modules from src ---
# Assuming tests are in tests/unit/
# Adjust relative path if your test directory structure is different
repo_root = Path(__file__).resolve().parent.parent 
# To get to the root of the project (e.g., jakadac_project_root containing src/ and tests/)
project_root = repo_root.parent 
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.asm_gen.asm_instruction_mapper import ASMInstructionMapper
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.SymTable import Symbol, EntryType, SymbolTable 
from jakadac.modules.Logger import Logger 

class TestASMInstructionMapperMain(unittest.TestCase):

    def setUp(self):
        self.mock_logger = Mock(spec=Logger)
        self.mock_symbol_table = Mock(spec=SymbolTable)
        self.mock_asm_generator = Mock() 
        
        self.mock_asm_generator.logger = self.mock_logger
        self.mock_asm_generator.symbol_table = self.mock_symbol_table
        
        self.mock_asm_generator.get_operand_asm = Mock(
            # op_val_str is the string version of TACOperand.value
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) + "_asm" if op_val_str is not None else ""
        )
        self.mock_asm_generator.is_immediate = Mock(return_value=False)
        self.mock_asm_generator.is_register = Mock(return_value=False)

        self.mock_proc_context = Mock(spec=Symbol)
        self.mock_proc_context.name = "DefaultTestProc"
        self.mock_proc_context.local_size = 0 
        self.mock_asm_generator.current_procedure_context = self.mock_proc_context

        self.mapper = ASMInstructionMapper(
            symbol_table=self.mock_symbol_table,
            logger_instance=self.mock_logger, 
            asm_generator_instance=self.mock_asm_generator
        )

    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode 
        instr.label = label

        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    def test_translate_unknown_opcode_enum(self):
        # class ExtendedTACOpcode(Enum): # Simple Enum for testing
        #     MADE_UP_ENUM_OP = "made_up_enum_op_val"
        #     # Add a name attribute to mimic TACOpcode enum members
        #     @property
        #     def name(self):
        #         return self._name_
        # 
        # ExtendedTACOpcode.MADE_UP_ENUM_OP._name_ = "MADE_UP_ENUM_OP"

        # Use TACOpcode.UNKNOWN to test the fallback to _translate_unknown
        # when an opcode is of TACOpcode type but not in the dispatch table.
        unknown_tac_op = TACOpcode.UNKNOWN 
        tac_unknown_enum = self._create_tac(unknown_tac_op, dest="d", op1="o1") # Using TACOpcode.UNKNOWN
        
        dest_val_str = "d"
        op1_val_str = "o1"
        op2_val_str = "None"

        # Expected ASM when TACOpcode.UNKNOWN is encountered
        expected_asm = [f"; UNHANDLED TAC Opcode: {TACOpcode.UNKNOWN.name} (Operands: D:{dest_val_str}, O1:{op1_val_str}, O2:{op2_val_str})"]
        result_asm = self.mapper.translate(tac_unknown_enum)
        self.assertEqual(result_asm, expected_asm)
        self.mock_logger.warning.assert_called_with(
            f"No specific translator for TAC opcode: {TACOpcode.UNKNOWN.name} at line {tac_unknown_enum.line_number}"
        )

    def test_translate_unknown_opcode_str(self):
        unknown_op_str = "COMPLETELY_UNKNOWN_STR_OP"
        tac_unknown_str = self._create_tac(unknown_op_str, dest="x", op1="y")
        dest_val_str = "x"
        op1_val_str = "y"
        op2_val_str = "None"

        expected_asm = [f"; UNHANDLED TAC Opcode: {unknown_op_str} (Operands: D:{dest_val_str}, O1:{op1_val_str}, O2:{op2_val_str})"]
        result_asm = self.mapper.translate(tac_unknown_str)
        self.assertEqual(result_asm, expected_asm)
        self.mock_logger.warning.assert_called_with(
            f"No specific translator for TAC opcode: {unknown_op_str} at line {tac_unknown_str.line_number}"
        )
    
    @patch.object(ASMInstructionMapper, '_translate_assign')
    def test_translate_dispatches_to_correct_handler(self, mock_translate_assign):
        mock_translate_assign.return_value = ["mocked assign asm"]
        tac_assign = self._create_tac(TACOpcode.ASSIGN, dest="x", op1="y")
        
        result = self.mapper.translate(tac_assign)
        
        mock_translate_assign.assert_called_once_with(tac_assign)
        self.assertEqual(result, ["mocked assign asm"])
        self.mock_logger.debug.assert_any_call(
            f"Translating TAC Op: ASSIGN, Line: {tac_assign.line_number} using _translate_assign"
        )

    def test_translate_handles_handler_not_returning_list(self):
        # Use a real opcode that has a handler for this test
        tac_instruction = self._create_tac(TACOpcode.ADD, dest="d", op1="o1", op2="o2")
        
        # Mock the specific handler (_translate_add) to return a non-list
        with patch.object(self.mapper, '_translate_add', return_value="NotAList") as mock_handler:
            result = self.mapper.translate(tac_instruction)
            self.assertEqual(result, ["NotAList"])
            self.mock_logger.warning.assert_called_with(
                 f"Handler _translate_add for opcode ADD did not return a list. Returned: NotAList. Wrapping in a list."
            )

        # Mock the specific handler to return None
        with patch.object(self.mapper, '_translate_add', return_value=None) as mock_handler_none:
            result = self.mapper.translate(tac_instruction)
            self.assertTrue("; ERROR: Handler for ADD returned None" in result[0])
            self.mock_logger.warning.assert_called_with(
                f"Handler _translate_add for opcode ADD did not return a list. Returned: None. Wrapping in a list."
            )

if __name__ == '__main__':
    unittest.main()