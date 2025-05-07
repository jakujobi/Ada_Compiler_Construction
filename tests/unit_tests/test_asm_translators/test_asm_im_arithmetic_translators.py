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

from jakadac.modules.asm_gen.instruction_translators.asm_im_arithmetic_translators import ArithmeticTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger

class TestArithmeticTranslators(unittest.TestCase, ArithmeticTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock()
        self.symbol_table = Mock() # For lookups if get_operand_asm needs it

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

    # --- ADD ---
    def test_translate_add_dest_equals_op1(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Sum": "AX", "Val": "BX"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.ADD, dest="Sum", op1="Sum", op2="Val") 
        result = self._translate_add(tac)
        self.assertEqual(result, ["ADD AX, BX"])

    def test_translate_add_dest_differs_op1_not_ax(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "CX", "OpA": "DX_val", "OpB": "SI_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.ADD, dest="Res", op1="OpA", op2="OpB") 
        result = self._translate_add(tac)
        self.assertEqual(result, ["MOV AX, DX_val", "ADD AX, SI_val", "MOV CX, AX"])

    def test_translate_add_dest_differs_op1_is_ax(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "CX", "OpA": "AX", "OpB": "DI_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.ADD, dest="Res", op1="OpA", op2="OpB")
        result = self._translate_add(tac) 
        self.assertEqual(result, ["ADD AX, DI_val", "MOV CX, AX"])
        
    # --- SUB ---
    def test_translate_sub_dest_equals_op1(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Diff": "DX_val", "Val": "[BP-2]_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.SUB, dest="Diff", op1="Diff", op2="Val") 
        result = self._translate_sub(tac)
        self.assertEqual(result, ["SUB DX_val, [BP-2]_val"])

    def test_translate_sub_dest_differs(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"R": "BX_val", "A": "CX_val", "B": "DX_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.SUB, dest="R", op1="A", op2="B") 
        result = self._translate_sub(tac)
        self.assertEqual(result, ["MOV AX, CX_val", "SUB AX, DX_val", "MOV BX_val, AX"])

    # --- MUL (IMUL for signed) ---
    def test_translate_mul_op1_not_ax_op2_reg(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "DX_val", "Val1": "Count_val", "Val2": "Multiplier_reg"}.get(op_v_s)
        self.asm_generator.is_register = lambda op_asm_str: op_asm_str == "Multiplier_reg"
        tac = self._create_tac(TACOpcode.MUL, dest="Res", op1="Val1", op2="Val2")
        result = self._translate_mul(tac)
        self.assertEqual(result, ["MOV AX, Count_val", "IMUL Multiplier_reg", "MOV DX_val, AX"])

    def test_translate_mul_op1_ax_op2_mem(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "CX_val", "Val1": "AX", "Val2": "[FactorMem]"}.get(op_v_s)
        self.asm_generator.is_register = lambda op_asm_str: op_asm_str == "AX" # Val1 is AX
        tac = self._create_tac(TACOpcode.MUL, dest="Res", op1="Val1", op2="Val2")
        result = self._translate_mul(tac) 
        self.assertEqual(result, ["IMUL [FactorMem]", "MOV CX_val, AX"])
        
    def test_translate_mul_op2_imm(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "SI_val", "Val1": "Quantity_val", "Val2": "5"}.get(op_v_s)
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "5"
        tac = self._create_tac(TACOpcode.MUL, dest="Res", op1="Val1", op2="Val2")
        result = self._translate_mul(tac)
        self.assertEqual(result, ["MOV AX, Quantity_val", "MOV BX, 5", "IMUL BX", "MOV SI_val, AX"])
        
    def test_translate_mul_op2_is_ax_op1_not_ax(self):
        # Res := SomeVar * AX (SomeVar -> AX; AX value (orig op2) -> BX; IMUL BX)
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Res": "DX_val", "Val1": "SomeVar_val", "Val2": "AX"}.get(op_v_s)
        self.asm_generator.is_register = lambda op_asm_str: op_asm_str == "AX" # Val2 is AX
        tac = self._create_tac(TACOpcode.MUL, dest="Res", op1="Val1", op2="Val2")
        result = self._translate_mul(tac)
        self.assertEqual(result, ["MOV AX, SomeVar_val", "MOV BX, AX", "IMUL BX", "MOV DX_val, AX"])

    # --- DIV/REM (IDIV for signed) ---
    def run_div_rem_test(self, opcode, is_div_flag, op1_val, op2_val, op1_asm, op2_asm_setup, expected_dest_reg):
        dest_var = "ResultVar"
        
        def get_op_asm_side_effect(op_str_val, tac_opc):
            if op_str_val == op1_val: return op1_asm
            if op_str_val == op2_val: return op2_asm_setup
            if op_str_val == dest_var: return dest_var + "_asm"
            return "unexpected_op"
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        
        self.asm_generator.is_register = lambda op_s: op_s in ["AX", "BX", "CX", "DX", "SI", "DI"] # For divisor check
        self.asm_generator.is_immediate = lambda op_s: op_s.isdigit()

        tac = self._create_tac(opcode, dest=dest_var, op1=op1_val, op2=op2_val)
        result = self._translate_div_or_rem(tac, is_div=is_div_flag)
        
        expected_asm = []
        if op1_asm != "AX":
            expected_asm.append(f"MOV AX, {op1_asm}")
        expected_asm.append("CWD")
        
        current_divisor_asm = op2_asm_setup
        if self.asm_generator.is_register(op2_asm_setup):
            if op2_asm_setup == "AX": # op1 was already moved to AX, or op1 was AX. op2 is also AX.
                expected_asm.append(f"MOV BX, AX") # Move op2's value (which is in AX) to BX
                current_divisor_asm = "BX"
            # else: divisor is another register, use it directly
        elif self.asm_generator.is_immediate(op2_asm_setup) or op2_asm_setup.startswith("["):
            expected_asm.append(f"MOV BX, {op2_asm_setup}")
            current_divisor_asm = "BX"
        # else if op2_asm_setup is a suitable register, it's used directly

        expected_asm.append(f"IDIV {current_divisor_asm}")
        if (dest_var + "_asm") != expected_dest_reg:
            expected_asm.append(f"MOV {dest_var + '_asm'}, {expected_dest_reg}")
            
        self.assertEqual(result, expected_asm)

    def test_translate_div_reg_divisor(self):
        self.run_div_rem_test(TACOpcode.DIV, True, "Num", "Denom", "Num_val", "CX", "AX")

    def test_translate_rem_mem_divisor(self):
        self.run_div_rem_test(TACOpcode.REM, False, "ValA", "ValB", "AX", "[BP-2]", "DX")
        
    def test_translate_div_imm_divisor(self):
        self.run_div_rem_test(TACOpcode.DIV, True, "Total", "5", "Total_val", "5", "AX")

    def test_translate_rem_divisor_is_ax(self): # Dividend is SomeOtherVar, Divisor is AX
        self.run_div_rem_test(TACOpcode.REM, False, "SomeOtherVar", "DivisorAX", "SomeOtherVar_val", "AX", "DX")


    # --- UMINUS ---
    def test_translate_uminus_inplace(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Val": "CX_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.UMINUS, dest="Val", op1="Val") 
        result = self._translate_uminus(tac)
        self.assertEqual(result, ["NEG CX_val"])

    def test_translate_uminus_outofplace_op1_ax(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"NegVal": "DX_val", "OrigVal": "AX"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.UMINUS, dest="NegVal", op1="OrigVal") 
        result = self._translate_uminus(tac)
        self.assertEqual(result, ["NEG AX", "MOV DX_val, AX"]) # MOV AX, AX skipped

    # --- NOT_OP ---
    def test_translate_not_op_inplace(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Flags": "FLG_REG_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.NOT_OP, dest="Flags", op1="Flags")
        result = self._translate_not_op(tac)
        self.assertEqual(result, ["NOT FLG_REG_val"])
        
    def test_translate_not_op_outofplace(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, oc: {"Inv": "INV_MEM_val", "Orig": "Source_val"}.get(op_v_s)
        tac = self._create_tac(TACOpcode.NOT_OP, dest="Inv", op1="Orig")
        result = self._translate_not_op(tac)
        self.assertEqual(result, ["MOV AX, Source_val", "NOT AX", "MOV INV_MEM_val, AX"])

if __name__ == '__main__':
    unittest.main()