import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, call, patch
import sys

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.asm_gen.asm_instruction_mapper import ASMInstructionMapper
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.SymTable import Symbol, EntryType, SymbolTable

class TestASMInstructionMapper(unittest.TestCase):

    def setUp(self):
        self.mock_asm_generator = Mock()
        self.mock_asm_generator.logger = Mock() 
        self.mock_asm_generator.symbol_table = Mock(spec=SymbolTable)
        # Update the side_effect to accept 'is_destination'
        self.mock_asm_generator.get_operand_asm = Mock(side_effect=lambda op, opcode, is_destination=False: str(op.value) + "_asm" if op and hasattr(op, 'value') else (str(op) + "_asm" if op else ""))
        self.mock_current_procedure_context = Mock(spec=Symbol)
        self.mock_current_procedure_context.name = "test_proc"
        self.mock_current_procedure_context.local_vars_total_size = 0 
        self.mock_asm_generator.current_procedure_context = self.mock_current_procedure_context

        # Correctly instantiate ASMInstructionMapper with all required arguments
        self.mapper = ASMInstructionMapper(
            symbol_table=self.mock_asm_generator.symbol_table, 
            logger=self.mock_asm_generator.logger,
            asm_generator_instance=self.mock_asm_generator
        )

    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        """Helper to create ParsedTACInstruction instances for tests."""
        instr = ParsedTACInstruction(line_number=line_number, label=label, raw_line=raw_line)
        instr.opcode = opcode

        # Wrap string/numeric operands in TACOperand objects if they are not None
        instr.dest = TACOperand(value=dest) if dest is not None else None
        instr.op1 = TACOperand(value=op1) if op1 is not None else None
        instr.op2 = TACOperand(value=op2) if op2 is not None else None
        # Note: TACOperand's 'value' field is Union[str, int, float].
        # The tests currently pass strings or numbers (e.g. op2=0 in test_translate_call_with_ret),
        # which is compatible with TACOperand's definition.
        return instr

    def test_translate_unknown_opcode(self):
        # Create a ParsedTACInstruction with a valid initial opcode, then overwrite it
        # Provide some dummy operands for a more complete test of the UNHANDLED message
        tac_unknown = self._create_tac(TACOpcode.ASSIGN, dest="d", op1="o1", op2="o2", raw_line="d := o1 op o2")
        tac_unknown.opcode = "MADE_UP_OPCODE" # Manually set to an unknown string
        
        # Expected output from _translate_unknown
        # Note: ParsedTACInstruction.dest, .op1, .op2 store TACOperands, so stringifying them might give TACOperand(value='d', type=...) etc.
        # For simplicity in matching the string output, we'll assume they are mocked to return their value for __str__ or use their value directly.
        # The actual _translate_unknown uses str(tac_instruction.dest) etc.
        expected_asm = [f"; UNHANDLED TAC Opcode: MADE_UP_OPCODE (Operands: D:{str(tac_unknown.dest)}, O1:{str(tac_unknown.op1)}, O2:{str(tac_unknown.op2)})"]
        result_asm = self.mapper.translate(tac_unknown)
        self.assertEqual(result_asm, expected_asm)

        # The warning is logged by _translate_unknown, using the logger from self.mapper 
        # (which is self.mock_asm_generator.logger)
        self.mock_asm_generator.logger.warning.assert_called_with(
            f"No specific translator for TAC opcode: MADE_UP_OPCODE at line {tac_unknown.line_number}"
        )

    def test_translate_assign_simple(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "var_x": "var_x_asm", 
            "var_y": "[BP-2]"
        }.get(op.value, "unexpected_op_in_assign_simple")
        tac_assign = self._create_tac(TACOpcode.ASSIGN, dest="var_x", op1="var_y")
        # Expected: MOV AX, [BP-2] then MOV var_x_asm, AX (for mem to mem)
        expected_asm = [
            "MOV AX, [BP-2]", 
            "MOV var_x_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_assign)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_assign_op1_is_ax(self):
        # Test case: X := AX (where X is var_x_asm)
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "var_x": "var_x_asm",
            "AX": "AX"
        }.get(op.value, "unexpected_op_in_assign_op1_is_ax")
        tac_assign = self._create_tac(TACOpcode.ASSIGN, dest="var_x", op1="AX")
        expected_asm = ["MOV var_x_asm, AX"]
        result_asm = self.mapper.translate(tac_assign)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_assign_dest_is_ax(self):
        # Test case: AX := Y (where Y is [BP-2])
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "AX": "AX",
            "var_y": "[BP-2]"
        }.get(op.value, "unexpected_op_in_assign_dest_is_ax")
        tac_assign = self._create_tac(TACOpcode.ASSIGN, dest="AX", op1="var_y")
        expected_asm = ["MOV AX, [BP-2]"]
        result_asm = self.mapper.translate(tac_assign)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_assign_both_ax(self):
        # Test case: AX := AX (should be optimized to nothing)
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "AX": "AX"
        }.get(op.value, "unexpected_op_in_assign_both_ax")
        tac_assign = self._create_tac(TACOpcode.ASSIGN, dest="AX", op1="AX")
        expected_asm = [] # Expecting optimization to no-op
        result_asm = self.mapper.translate(tac_assign)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_add_simple(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "res": "res_asm", "val1": "val1_asm", "val2": "val2_asm"
        }.get(op.value, "unexpected_op_in_add_simple")
        tac_add = self._create_tac(TACOpcode.ADD, dest="res", op1="val1", op2="val2")
        expected_asm = [
            "MOV AX, val1_asm",
            "ADD AX, val2_asm",
            "MOV res_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_add)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_sub_simple(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "res": "res_asm", "val1": "val1_asm", "val2": "val2_asm"
        }.get(op.value, "unexpected_op_in_sub_simple")
        tac_sub = self._create_tac(TACOpcode.SUB, dest="res", op1="val1", op2="val2")
        expected_asm = [
            "MOV AX, val1_asm", 
            "SUB AX, val2_asm", 
            "MOV res_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_sub)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_mul_simple(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "res": "res_asm", "val1": "val1_asm", "val2": "val2_asm"
        }.get(op.value, "unexpected_op_in_mul_simple")
        tac_mul = self._create_tac(TACOpcode.MUL, dest="res", op1="val1", op2="val2")
        expected_asm = [
            "MOV AX, val1_asm", 
            "MOV BX, val2_asm", 
            "MUL BX", 
            "MOV res_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_mul)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_div_simple(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "res": "res_asm", "val1": "val1_asm", "val2": "val2_asm"
        }.get(op.value, "unexpected_op_in_div_simple")
        tac_div = self._create_tac(TACOpcode.DIV, dest="res", op1="val1", op2="val2")
        expected_asm = [
            "MOV AX, val1_asm", 
            "MOV BX, val2_asm", 
            "XOR DX, DX", # Clear DX for DIV
            "DIV BX", 
            "MOV res_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_div)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_goto(self):
        tac_goto = self._create_tac(TACOpcode.GOTO, dest="L1")
        expected_asm = ["JMP L1"]
        result_asm = self.mapper.translate(tac_goto)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_label(self):
        tac_label = self._create_tac(TACOpcode.LABEL, dest="L1")
        expected_asm = ["L1:"]
        result_asm = self.mapper.translate(tac_label)
        self.assertEqual(result_asm, expected_asm)

    # Conditional Jumps
    def test_translate_if_eq_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_eq_goto")
        tac_if_eq = self._create_tac(TACOpcode.IF_EQ_GOTO, dest="L1_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JE L1_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JE L1_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_eq)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_eq_goto_op1_imm(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "5", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_eq_goto_op1_imm")
        tac_if_eq = self._create_tac(TACOpcode.IF_EQ_GOTO, dest="L1_LABEL", op1="op1", op2="op2")
        # Expected: CMP op2_asm, 5; JE L1_LABEL (immediate first in CMP if possible)
        expected_asm = [
            "CMP op2_asm, 5",
            "JE L1_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_eq)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_eq_goto_op2_imm(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "10"
        }.get(op.value, "unexpected_op_in_if_eq_goto_op2_imm")
        tac_if_eq = self._create_tac(TACOpcode.IF_EQ_GOTO, dest="L1_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, 10; JE L1_LABEL
        expected_asm = [
            "CMP op1_asm, 10",
            "JE L1_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_eq)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_eq_goto_both_imm(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "5", "op2": "10"
        }.get(op.value, "unexpected_op_in_if_eq_goto_both_imm")
        tac_if_eq = self._create_tac(TACOpcode.IF_EQ_GOTO, dest="L1_LABEL", op1="op1", op2="op2")
        # Expected: MOV AX, 5; CMP AX, 10; JE L1_LABEL 
        expected_asm = [
            "MOV AX, 5",
            "CMP AX, 10", # Or CMP 5, 10 if assembler supports imm,imm
            "JE L1_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_eq)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_false_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm"
        }.get(op.value, "unexpected_op_in_if_false_goto")
        tac_if_false = self._create_tac(TACOpcode.IF_FALSE_GOTO, dest="L1_LABEL", op1="op1")
        # Expected: CMP op1_asm, 0; JE L1_LABEL (or similar logic)
        expected_asm = [
            "CMP op1_asm, 0",
            "JE L1_LABEL" # Jump if op1 is false (0)
        ]
        result_asm = self.mapper.translate(tac_if_false)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_ne_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_ne_goto")
        tac_if_ne = self._create_tac(TACOpcode.IF_NE_GOTO, dest="L2_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JNE L2_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JNE L2_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_ne)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_lt_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_lt_goto")
        tac_if_lt = self._create_tac(TACOpcode.IF_LT_GOTO, dest="L3_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JL L3_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JL L3_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_lt)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_le_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_le_goto")
        tac_if_le = self._create_tac(TACOpcode.IF_LE_GOTO, dest="L4_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JLE L4_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JLE L4_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_le)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_gt_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_gt_goto")
        tac_if_gt = self._create_tac(TACOpcode.IF_GT_GOTO, dest="L5_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JG L5_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JG L5_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_gt)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_ge_goto(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "op1_asm", "op2": "op2_asm"
        }.get(op.value, "unexpected_op_in_if_ge_goto")
        tac_if_ge = self._create_tac(TACOpcode.IF_GE_GOTO, dest="L6_LABEL", op1="op1", op2="op2")
        # Expected: CMP op1_asm, op2_asm; JGE L6_LABEL
        expected_asm = [
            "CMP op1_asm, op2_asm",
            "JGE L6_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_ge)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_if_ge_goto_imm_mem(self):
        # TAC: IF_GE_GOTO GE_LABEL, op1 (5), op2 ([SI])
        # op1 >= op2. With CMP op2, op1 this becomes: op2 <= op1 (JLE)
        op1_val, op2_val = "5", "[SI]" # Mocked values for op1_asm_val, op2_asm_val
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": op1_val, "op2": op2_val
        }.get(op.value, "unexpected_op_in_if_ge_goto_imm_mem")
        
        tac_if_ge_imm_mem = self._create_tac(TACOpcode.IF_GE_GOTO, dest="GE_LABEL", op1="op1", op2="op2")
        
        expected_asm = [
            f"CMP {op2_val}, {op1_val}", # CMP [SI], 5
            f"JLE GE_LABEL"              # Jump if op2 <= op1 (which is op1 >= op2)
        ]
        expected_log_message = f"Comparing immediate {op1_val} with memory/register {op2_val}, swapping for optimal CMP and inverting jump."

        with self.assertLogs(self.mapper.logger, level='DEBUG') as log_watcher:
            result_asm = self.mapper.translate(tac_if_ge_imm_mem)
        
        self.assertEqual(result_asm, expected_asm, f"Expected ASM {expected_asm} but got {result_asm}")
        
        # Check if the specific log message is present in the output
        found_log = False
        for record in log_watcher.records:
            if expected_log_message in record.getMessage():
                found_log = True
                break
        self.assertTrue(found_log, f"Expected log message '{expected_log_message}' not found. Logs: {log_watcher.output}")

    # Test IF_NE_GOTO variants
    def test_translate_if_ne_goto_reg_reg(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "op1": "AX", "op2": "BX"
        }.get(op.value, "unexpected_op_in_if_ne_goto_reg_reg")
        tac_if_ne = self._create_tac(TACOpcode.IF_NE_GOTO, dest="L2_LABEL", op1="op1", op2="op2")
        # Expected: CMP AX, BX; JNE L2_LABEL
        expected_asm = [
            "CMP AX, BX",
            "JNE L2_LABEL"
        ]
        result_asm = self.mapper.translate(tac_if_ne)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_param(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "param_val": "param_asm"
        }.get(op.value, "unexpected_op_in_param")
        tac_param = self._create_tac(TACOpcode.PARAM, op1="param_val")
        expected_asm = ["PUSH param_asm"] # ASM for op1
        result_asm = self.mapper.translate(tac_param)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_call_no_ret(self):
        tac_call = self._create_tac(TACOpcode.CALL, op1="proc_label", op2=0) # op2 = num_params
        expected_asm = ["CALL proc_label"]
        result_asm = self.mapper.translate(tac_call)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_call_with_ret(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "ret_var": "ret_var_asm"
        }.get(op.value, "unexpected_op_in_call_with_ret")
        tac_call = self._create_tac(TACOpcode.CALL, dest="ret_var", op1="proc_label_ret", op2=0)
        expected_asm = [
            "CALL proc_label_ret",
            "MOV ret_var_asm, AX" # Assuming AX holds return value
        ]
        result_asm = self.mapper.translate(tac_call)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_call_with_params_and_ret(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "ret_val": "ret_val_asm"
        }.get(op.value, "unexpected_op_in_call_with_params_and_ret")
        tac_call = self._create_tac(TACOpcode.CALL, dest="ret_val", op1="proc_with_params", op2=2)
        expected_asm = [
            "CALL proc_with_params",
            "ADD SP, 4",           # Cleanup 2 params * 2 bytes/param
            "MOV ret_val_asm, AX"
        ]
        result_asm = self.mapper.translate(tac_call)
        self.assertEqual(result_asm, expected_asm)
        self.mock_asm_generator.get_symbol_by_name.assert_called_with("proc_with_params")

    def test_translate_return_void(self):
        tac_return = self._create_tac(TACOpcode.RETURN)
        expected_asm = ["RET"]
        result_asm = self.mapper.translate(tac_return)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_return_value(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "return_val": "return_val_asm"
        }.get(op.value, "unexpected_op_in_return_value")
        tac_return = self._create_tac(TACOpcode.RETURN, op1="return_val")
        expected_asm = [
            "MOV AX, return_val_asm", 
            "RET"
        ]
        result_asm = self.mapper.translate(tac_return)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_proc_begin_end(self):
        proc_name = "main"
        self.mock_current_procedure_context.name = proc_name
        self.mock_current_procedure_context.local_vars_total_size = 10
        self.mock_asm_generator.current_procedure_context = self.mock_current_procedure_context
        tac_proc_begin = self._create_tac(TACOpcode.PROC_BEGIN, dest=proc_name)
        # Expected from _translate_proc_begin
        expected_asm_begin = [
            "main:",
            "PUSH BP",
            "MOV BP, SP",
            "SUB SP, 10" # locals_size
        ]
        self.assertEqual(self.mapper.translate(tac_proc_begin), expected_asm_begin)
        self.mock_current_procedure_context.enter_procedure.assert_called_with(proc_name)

        tac_proc_end = self._create_tac(TACOpcode.PROC_END, dest=proc_name)
        # Expected from _translate_proc_end
        expected_asm_end = [
            "MOV SP, BP",
            "POP BP"
            # RET is handled by RETURN instruction
        ]
        self.assertEqual(self.mapper.translate(tac_proc_end), expected_asm_end)
        self.mock_current_procedure_context.exit_procedure.assert_called_once()

    def test_translate_array_assign_from(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "idx": "idx_asm", "val": "val_asm", "arr": "arr_asm"
        }.get(op.value if isinstance(op, TACOperand) else op, "unexpected_op_in_array_assign_from")
        tac_array_assign_from = self._create_tac(TACOpcode.ARRAY_ASSIGN_FROM, dest="arr", op1="idx", op2="val")
        # arr[idx] := val  =>  MOV AX, idx_asm; MOV BX, val_asm; MOV [arr_asm+AX], BX
        expected_asm = [
            "MOV AX, idx_asm",
            "MOV BX, val_asm",
            "MOV [arr_asm+AX], BX"
        ]
        result_asm = self.mapper.translate(tac_array_assign_from)
        self.assertEqual(result_asm, expected_asm)

    def test_translate_array_assign_to(self):
        self.mock_asm_generator.get_operand_asm.side_effect = lambda op, opcode, is_destination=False: {
            "idx": "idx_asm", "val": "val_asm", "arr": "arr_asm"
        }.get(op.value if isinstance(op, TACOperand) else op, "unexpected_op_in_array_assign_to")
        tac_array_assign_to = self._create_tac(TACOpcode.ARRAY_ASSIGN_TO, dest="val", op1="arr", op2="idx")
        # val := arr[idx]  =>  MOV AX, idx_asm; MOV BX, [arr_asm+AX]; MOV val_asm, BX
        expected_asm = [
            "MOV AX, idx_asm",
            "MOV BX, [arr_asm+AX]",
            "MOV val_asm, BX"
        ]
        result_asm = self.mapper.translate(tac_array_assign_to)
        self.assertEqual(result_asm, expected_asm)

    def test_get_operand_asm_direct_register(self):
        pass

if __name__ == '__main__':
    unittest.main()
