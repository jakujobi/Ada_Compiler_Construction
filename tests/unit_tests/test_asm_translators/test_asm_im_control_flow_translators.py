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

from jakadac.modules.asm_gen.instruction_translators.asm_im_control_flow_translators import ControlFlowTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger

class TestControlFlowTranslators(unittest.TestCase, ControlFlowTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock()
        self.symbol_table = Mock() 

        self.asm_generator.get_operand_asm = Mock(
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) if op_val_str is not None else "" 
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

    def test_translate_label(self):
        tac = self._create_tac(TACOpcode.LABEL, label="LoopStart") # label is in instr.label
        result = self._translate_label(tac)
        self.assertEqual(result, ["LoopStart:"])

    def test_translate_label_malformed_no_label_field(self):
        tac = self._create_tac(TACOpcode.LABEL) 
        tac.label = None # Explicitly malform
        result = self._translate_label(tac)
        self.assertEqual(result, [f"; ERROR: Malformed LABEL TAC at line {tac.line_number} - Missing label name in .label field."])
        self.logger.error.assert_called_once()
        
    def test_translate_goto(self):
        tac = self._create_tac(TACOpcode.GOTO, dest="ExitPoint") # Target label is in dest.value
        result = self._translate_goto(tac)
        self.assertEqual(result, ["JMP ExitPoint"]) 

    def test_translate_if_false_goto_mem_op(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, tc: "[BP-2]" if op_v_s == "CondVar" else str(op_v_s)
        tac = self._create_tac(TACOpcode.IF_FALSE_GOTO, dest="TargetLbl", op1="CondVar")
        result = self._translate_if_false_goto(tac)
        self.assertEqual(result, ["CMP WORD PTR [BP-2], 0", "JE TargetLbl"])

    def test_translate_if_false_goto_reg_op(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, tc: "CX" if op_v_s == "FlagReg" else str(op_v_s)
        tac = self._create_tac(TACOpcode.IF_FALSE_GOTO, dest="FalsePath", op1="FlagReg")
        result = self._translate_if_false_goto(tac)
        self.assertEqual(result, ["CMP CX, 0", "JE FalsePath"])
        
    def test_translate_if_false_goto_imm_op(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, tc: "1" if op_v_s == "TrueConst" else str(op_v_s)
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "1"
        tac = self._create_tac(TACOpcode.IF_FALSE_GOTO, dest="SkipPath", op1="TrueConst")
        result = self._translate_if_false_goto(tac)
        self.assertEqual(result, ["MOV AX, 1", "CMP AX, 0", "JE SkipPath"])


    def run_common_jump_test(self, opcode_enum, jump_mnemonic_base, op1_val_str, op2_val_str, 
                             op1_asm_repr, op2_asm_repr, 
                             is_op1_imm_flag, is_op2_imm_flag, 
                             is_op1_reg_flag, is_op2_reg_flag,
                             expected_asm_sequence):
        
        # Configure mocks based on parameters
        def get_op_asm(op_str, tc_op):
            if op_str == op1_val_str: return op1_asm_repr
            if op_str == op2_val_str: return op2_asm_repr
            return str(op_str) # For label
        self.asm_generator.get_operand_asm.side_effect = get_op_asm
        self.asm_generator.is_immediate = lambda op_s: (op_s == op1_asm_repr and is_op1_imm_flag) or \
                                                       (op_s == op2_asm_repr and is_op2_imm_flag)
        self.asm_generator.is_register = lambda op_s: (op_s == op1_asm_repr and is_op1_reg_flag) or \
                                                      (op_s == op2_asm_repr and is_op2_reg_flag)

        tac = self._create_tac(opcode_enum, dest="TestLabel", op1=op1_val_str, op2=op2_val_str)
        result = self._common_conditional_jump_translation(tac, jump_mnemonic_base)
        self.assertEqual(result, expected_asm_sequence)

    # Test cases for _common_conditional_jump_translation
    def test_if_eq_reg_reg(self): # AX == BX
        self.run_common_jump_test(TACOpcode.IF_EQ_GOTO, "JE", "ValA", "ValB", "AX", "BX", False, False, True, True,
                                  ["CMP AX, BX", "JE TestLabel"])

    def test_if_lt_mem_imm(self): # [BP-2] < 5
        self.run_common_jump_test(TACOpcode.IF_LT_GOTO, "JL", "Mem", "Imm", "[BP-2]", "5", False, True, False, False,
                                  ["CMP [BP-2], 5", "JL TestLabel"])

    def test_if_gt_imm_mem(self): # 10 > [SI] -> CMP [SI], 10; JL TestLabel (inverted)
        self.run_common_jump_test(TACOpcode.IF_GT_GOTO, "JG", "Imm", "Mem", "10", "[SI]", True, False, False, False,
                                  ["CMP [SI], 10", "JL TestLabel"])
                                  
    def test_if_ge_mem_mem(self): # [DI] >= [BX] -> MOV AX, [BX]; CMP [DI], AX; JGE TestLabel
         self.run_common_jump_test(TACOpcode.IF_GE_GOTO, "JGE", "MemA", "MemB", "[DI]", "[BX]", False, False, False, False,
                                   ["MOV AX, [BX]", "CMP [DI], AX", "JGE TestLabel"])

    def test_if_le_imm_reg(self): # 3 <= CX -> CMP CX, 3; JGE TestLabel (inverted)
        self.run_common_jump_test(TACOpcode.IF_LE_GOTO, "JLE", "Imm", "RegC", "3", "CX", True, False, False, True,
                                  ["CMP CX, 3", "JGE TestLabel"])

    def test_if_ne_both_imm(self): # 7 != 7 -> MOV AX, 7; CMP AX, 7; JNE TestLabel
        self.run_common_jump_test(TACOpcode.IF_NE_GOTO, "JNE", "Imm1", "Imm2", "7", "7", True, True, False, False,
                                  ["MOV AX, 7", "CMP AX, 7", "JNE TestLabel"])
                                  
    def test_if_eq_reg_mem(self): # AX == [DI]
        self.run_common_jump_test(TACOpcode.IF_EQ_GOTO, "JE", "RegA", "MemB", "AX", "[DI]", False, False, True, False,
                                  ["CMP AX, [DI]", "JE TestLabel"])


if __name__ == '__main__':
    unittest.main()