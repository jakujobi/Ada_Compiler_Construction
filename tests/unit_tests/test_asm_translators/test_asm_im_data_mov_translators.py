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

from jakadac.modules.asm_gen.instruction_translators.asm_im_data_mov_translators import DataMovTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger 

class TestDataMovTranslators(unittest.TestCase, DataMovTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock() 
        self.symbol_table = Mock() 

        self.asm_generator.get_operand_asm = Mock(
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) + "_asm" if op_val_str is not None else ""
        )
        self.asm_generator.is_immediate = Mock(return_value=False)
        self.asm_generator.is_register = Mock(return_value=False)
        self.asm_generator.current_procedure_context = Mock() 

    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode
        instr.label = label
        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    def test_translate_assign_reg_to_reg(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"X": "AX", "Y": "BX"}.get(op_val_str)
        tac = self._create_tac(TACOpcode.ASSIGN, dest="X", op1="Y")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV AX, BX"])

    def test_translate_assign_mem_to_reg(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"RetVal": "AX", "MemVar": "[BP-2]"}.get(op_val_str)
        tac = self._create_tac(TACOpcode.ASSIGN, dest="RetVal", op1="MemVar")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV AX, [BP-2]"])

    def test_translate_assign_reg_to_mem(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"MyVar": "[BP-4]", "SourceReg": "CX"}.get(op_val_str)
        tac = self._create_tac(TACOpcode.ASSIGN, dest="MyVar", op1="SourceReg")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV [BP-4], CX"])

    def test_translate_assign_imm_to_reg(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"Counter": "CX", "5": "5"}.get(op_val_str)
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "5"
        tac = self._create_tac(TACOpcode.ASSIGN, dest="Counter", op1="5")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV CX, 5"])

    def test_translate_assign_imm_to_mem(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"StatusFlag": "[DI+2]", "0": "0"}.get(op_val_str)
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "0"
        tac = self._create_tac(TACOpcode.ASSIGN, dest="StatusFlag", op1="0")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV WORD PTR [DI+2], 0"])

    def test_translate_assign_mem_to_mem(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"MemDest": "[BP-4]", "MemSource": "[BP-2]"}.get(op_val_str)
        self.asm_generator.is_immediate = lambda op_asm_str: False
        tac = self._create_tac(TACOpcode.ASSIGN, dest="MemDest", op1="MemSource")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV AX, [BP-2]", "MOV [BP-4], AX"])

    def test_translate_assign_offset_to_mem(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: {"TargetAddr": "[BX]", "MyString": "OFFSET _S0"}.get(op_val_str)
        # is_immediate should also catch "OFFSET ..." as a form of literal for MOV mem, literal
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "OFFSET _S0" 
        tac = self._create_tac(TACOpcode.ASSIGN, dest="TargetAddr", op1="MyString")
        result = self._translate_assign(tac)
        self.assertEqual(result, ["MOV WORD PTR [BX], OFFSET _S0"])

    def test_translate_assign_same_operand_no_op(self):
        # Mock get_operand_asm to return "AX" for the value "X"
        self.asm_generator.get_operand_asm.side_effect = lambda op_val_str, oc: "AX" if op_val_str == "X" else "unexpected"
        tac = self._create_tac(TACOpcode.ASSIGN, dest="X", op1="X")
        result = self._translate_assign(tac)
        self.assertEqual(result, []) 
        self.logger.debug.assert_called_with("ASSIGN X := X -> No-op (dest and src are the same: AX)")

    def test_translate_assign_malformed_tac_missing_dest_val(self):
        tac = self._create_tac(TACOpcode.ASSIGN, op1="Y_val")
        tac.destination = TACOperand(value=None) # Malformed
        result = self._translate_assign(tac)
        self.assertEqual(result, [f"; ERROR: Malformed ASSIGN TAC at line {tac.line_number}"])
        self.logger.error.assert_called_with(f"ASSIGN TAC at line {tac.line_number} is missing destination or source operand value.")


    def test_translate_assign_malformed_tac_missing_op1_val(self):
        tac = self._create_tac(TACOpcode.ASSIGN, dest="X_val")
        tac.operand1 = TACOperand(value=None) # Malformed
        result = self._translate_assign(tac)
        self.assertEqual(result, [f"; ERROR: Malformed ASSIGN TAC at line {tac.line_number}"])
        self.logger.error.assert_called_with(f"ASSIGN TAC at line {tac.line_number} is missing destination or source operand value.")


if __name__ == '__main__':
    unittest.main()