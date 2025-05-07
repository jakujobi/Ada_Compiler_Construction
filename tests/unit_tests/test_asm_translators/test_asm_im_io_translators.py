import unittest
from unittest.mock import Mock, call, patch
import sys
from pathlib import Path

# Correctly calculate the project's src directory and add it to sys.path
_current_file_path = Path(__file__).resolve()
# ..\..\..\.. gets to the project root (Ada_Compiler_Construction) from the test file location
_project_root_actual = _current_file_path.parent.parent.parent.parent
_src_dir_actual = _project_root_actual / "src"
if str(_src_dir_actual) not in sys.path:
    sys.path.insert(0, str(_src_dir_actual))

from jakadac.modules.asm_gen.instruction_translators.asm_im_io_translators import IOTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger

class TestIOTranslators(unittest.TestCase, IOTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock()
        self.symbol_table = Mock() # Though not directly used by IO translators

        self.asm_generator.get_operand_asm = Mock(
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) + "_asm" if op_val_str is not None else ""
        )
        self.asm_generator.current_procedure_context = Mock()


    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode
        instr.label = label
        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    def test_translate_read_int_dest_not_ax(self):
        self.asm_generator.get_operand_asm.return_value = "TargetVar_asm"
        tac = self._create_tac(TACOpcode.READ_INT, dest="TargetVar")
        result = self._translate_read_int(tac)
        self.assertEqual(result, ["CALL READINT", "MOV TargetVar_asm, AX"])

    def test_translate_read_int_dest_is_ax(self):
        self.asm_generator.get_operand_asm.return_value = "AX"
        tac = self._create_tac(TACOpcode.READ_INT, dest="AX_val_placeholder") 
        result = self._translate_read_int(tac)
        self.assertEqual(result, ["CALL READINT"]) 

    def test_translate_write_int_source_not_ax(self):
        self.asm_generator.get_operand_asm.return_value = "SourceVar_asm"
        tac = self._create_tac(TACOpcode.WRITE_INT, op1="SourceVar")
        result = self._translate_write_int(tac)
        self.assertEqual(result, ["MOV AX, SourceVar_asm", "CALL WRITEINT"])

    def test_translate_write_int_source_is_ax(self):
        self.asm_generator.get_operand_asm.return_value = "AX"
        tac = self._create_tac(TACOpcode.WRITE_INT, op1="AX_val_placeholder")
        result = self._translate_write_int(tac)
        self.assertEqual(result, ["CALL WRITEINT"]) 

    def test_translate_write_str(self):
        # Mock get_operand_asm to return "OFFSET _S0" when op_val_str is "_S0"
        # AND tac_opcode is WRITE_STR (or similar context implying address)
        def get_op_asm_side_effect(op_val_str, tac_opc):
            if op_val_str == "_S0" and tac_opc == TACOpcode.WRITE_STR:
                return "OFFSET _S0"
            return str(op_val_str) + "_asm" # Default fallback
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        
        tac = self._create_tac(TACOpcode.WRITE_STR, op1="_S0")
        result = self._translate_write_str(tac)
        self.assertEqual(result, ["MOV DX, OFFSET _S0", "CALL WRITESTRING"])
        
    def test_translate_write_str_operand_already_dx_with_offset(self):
        # Simulate get_operand_asm returning "DX" because the offset value was already moved to DX
        # This test is more about the translator's optimization if DX is already set.
        # The realistic scenario is get_operand_asm returns "OFFSET _S1", then MOV DX, OFFSET _S1
        # If somehow _get_operand_asm returned "DX" directly (implying it IS the offset string in DX),
        # then MOV DX, DX would be skipped.
        self.asm_generator.get_operand_asm.return_value = "DX" # Mocking that the operand IS DX.
        tac = self._create_tac(TACOpcode.WRITE_STR, op1="PreloadedStrOffsetInDX")
        result = self._translate_write_str(tac)
        self.assertEqual(result, ["CALL WRITESTRING"]) # MOV DX, DX optimized out

    def test_translate_write_newline(self):
        tac = self._create_tac(TACOpcode.WRITE_NEWLINE)
        result = self._translate_write_newline(tac)
        self.assertEqual(result, ["CALL NEWLINE"])

if __name__ == '__main__':
    unittest.main()