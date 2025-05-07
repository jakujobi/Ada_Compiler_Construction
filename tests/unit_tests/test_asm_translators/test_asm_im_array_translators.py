import unittest
from unittest.mock import Mock, call, patch
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
project_root = repo_root.parent 
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.asm_gen.asm_im_array_translators import ArrayTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger

class TestArrayTranslators(unittest.TestCase, ArrayTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock()
        self.symbol_table = Mock()

        self.asm_generator.get_operand_asm = Mock(
             # op_val_str is the string version of TACOperand.value
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) if op_val_str is not None else "ERROR_NONE_OP_VAL"
        )
        self.asm_generator.is_immediate = Mock(return_value=False)
        # self.asm_generator.is_register = Mock(return_value=False) # Not directly used by array translators
        self.asm_generator.current_procedure_context = Mock()


    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode
        instr.label = label
        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    # ARRAY_ASSIGN_FROM: dest_var := array_base[index_op]
    # TAC: dest=dest_var, op1=array_base, op2=index_op
    def test_translate_array_assign_from_global_array_index_reg_si(self):
        # Target := MyGlobalArray[SI] (index already in SI)
        def get_op_asm_side_effect(op_val_str, tc):
            if op_val_str == "Target": return "DX"
            if op_val_str == "MyGlobalArray": return "MyGlobalArray_label"
            if op_val_str == "IDX_REG_SI": return "SI" # Index is already SI
            return "unexpected_op_from"
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        
        tac = self._create_tac(TACOpcode.ARRAY_ASSIGN_FROM, dest="Target", op1="MyGlobalArray", op2="IDX_REG_SI")
        result = self._translate_array_assign_from(tac)
        expected = [
            # MOV SI, SI (optimized out)
            "SHL SI, 1",
            "LEA BX, MyGlobalArray_label", 
            "MOV AX, [BX+SI]",
            "MOV DX, AX"         
        ]
        self.assertEqual(result, expected)

    def test_translate_array_assign_from_local_array_index_imm(self):
        # TargetReg := MyLocalArray[5]
        def get_op_asm_side_effect(op_val_str, tc):
            if op_val_str == "TargetReg": return "CX"
            if op_val_str == "MyLocalArray": return "[BP-20]"
            if op_val_str == "5": return "5" # Index is immediate 5
            return "unexpected_op_from2"
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        # is_immediate not directly used by array translator logic itself, but by get_operand_asm

        tac = self._create_tac(TACOpcode.ARRAY_ASSIGN_FROM, dest="TargetReg", op1="MyLocalArray", op2="5")
        result = self._translate_array_assign_from(tac)
        expected = [
            "MOV SI, 5",
            "SHL SI, 1",
            "LEA BX, [BP-20]",  
            "MOV AX, [BX+SI]",
            "MOV CX, AX"
        ]
        self.assertEqual(result, expected)

    # ARRAY_ASSIGN_TO: array_base[index_op] := source_val
    # TAC: dest=array_base, op1=index_op, op2=source_val
    def test_translate_array_assign_to_source_reg_ax(self):
        # GlobalArr[IndexReg_DI] := AX (source value already in AX)
        def get_op_asm_side_effect(op_val_str, tc):
            if op_val_str == "GlobalArr": return "GLOBAL_ARR_LBL"
            if op_val_str == "IndexReg_DI": return "DI"
            if op_val_str == "SourceAX": return "AX" # Source value is AX
            return "unexpected_op_to"
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        self.asm_generator.is_immediate = Mock(return_value=False)

        tac = self._create_tac(TACOpcode.ARRAY_ASSIGN_TO, dest="GlobalArr", op1="IndexReg_DI", op2="SourceAX")
        result = self._translate_array_assign_to(tac)
        expected = [
            "MOV SI, DI", 
            "SHL SI, 1",
            "LEA BX, GLOBAL_ARR_LBL",
            # MOV AX, AX (optimized out)
            "MOV [BX+SI], AX"
        ]
        self.assertEqual(result, expected)

    def test_translate_array_assign_to_source_imm(self):
        # LocalArr[IndexVar] := 100
        def get_op_asm_side_effect(op_val_str, tc):
            if op_val_str == "LocalArr": return "[BP-50]"
            if op_val_str == "IndexVar": return "MyIndex_val" # Some variable holding index
            if op_val_str == "100": return "100" # Source value is immediate
            return "unexpected_op_to2"
        self.asm_generator.get_operand_asm.side_effect = get_op_asm_side_effect
        self.asm_generator.is_immediate = lambda op_asm_str: op_asm_str == "100"

        tac = self._create_tac(TACOpcode.ARRAY_ASSIGN_TO, dest="LocalArr", op1="IndexVar", op2="100")
        result = self._translate_array_assign_to(tac)
        expected = [
            "MOV SI, MyIndex_val",
            "SHL SI, 1",
            "LEA BX, [BP-50]",
            "MOV WORD PTR [BX+SI], 100"
        ]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()