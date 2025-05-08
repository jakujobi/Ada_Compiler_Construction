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
        # The 'self' in the translator methods (e.g., _translate_assign) refers to an ASMInstructionMapper instance.
        # So, we need to mock the attributes/methods that _translate_assign will call on 'self'.

        # Mock for self.formatter.format_operand
        self.formatter = Mock()
        self.formatter.format_operand = Mock(side_effect=lambda op_val_str, tac_opcode: str(op_val_str) if op_val_str is not None else "ERROR_NONE_OP_VAL")

        # Mock for self._is_param_address
        self._is_param_address = Mock(return_value=False) # Default to False

        # Mock for self.generator.is_immediate and self.generator.is_register
        # The translator calls self.generator.is_immediate, etc.
        # 'generator' is an attribute of ASMInstructionMapper, so it becomes self.generator
        self.generator = Mock() 
        self.generator.is_immediate = Mock(return_value=False)
        self.generator.is_register = Mock(return_value=False)
        
        # Keep other mocks if they are used by other test methods or older versions
        self.asm_generator = Mock() 
        self.asm_generator.get_operand_asm = self.formatter.format_operand # For legacy if any test uses it
        self.asm_generator.is_immediate = self.generator.is_immediate
        self.asm_generator.is_register = self.generator.is_register
        self.asm_generator.current_procedure_context = Mock()
        self.symbol_table = Mock()

    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode
        instr.label = label
        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    def test_translate_assign_reg_to_reg(self):
        dest_tac, src_tac = "X", "Y"
        dest_asm, src_asm = "AX", "BX"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str in [dest_asm, src_asm])
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source value/address into AX", # src_asm (BX) is not ref, not mem-to-mem path
            f" mov {dest_asm}, ax   ; Store AX into destination"  # dest_asm (AX) is not ref
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_mem_to_reg(self):
        dest_tac, src_tac = "RetVal", "MemVar"
        dest_asm, src_asm = "AX", "[BP-2]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == dest_asm) # Only AX is reg
        self.generator.is_immediate.return_value = False
        
        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src ([BP-2]) is not ref. dest (AX) is not ref.
        # is_dest_mem (for AX) = False. is_src_mem (for [BP-2]) = True. Not mem-to-mem path.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source value/address into AX",
            f" mov {dest_asm}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_reg_to_mem(self):
        dest_tac, src_tac = "MyVar", "SourceReg"
        dest_asm, src_asm = "[BP-4]", "CX"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == src_asm) # Only CX is reg
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src (CX) is not ref. dest ([BP-4]) is not ref.
        # is_dest_mem (for [BP-4]) = True. is_src_mem (for CX) = False. Not mem-to-mem.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source value/address into AX",
            f" mov {dest_asm}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_imm_to_reg(self):
        dest_tac, src_tac = "Counter", "5"
        dest_asm, src_asm = "CX", "5"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == dest_asm) # Only CX is reg
        self.generator.is_immediate = Mock(side_effect=lambda op_str: op_str == src_asm) # 5 is imm

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src (5) is not ref. dest (CX) is not ref.
        # is_dest_mem (CX) = False. is_src_mem (5) = False (as is_immediate is true). Not mem-to-mem.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source value/address into AX",
            f" mov {dest_asm}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_imm_to_mem(self):
        dest_tac, src_tac = "StatusFlag", "0"
        dest_asm, src_asm = "[DI+2]", "0"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register.return_value = False # Neither is reg
        self.generator.is_immediate = Mock(side_effect=lambda op_str: op_str == src_asm) # 0 is imm

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src (0) is not ref. dest ([DI+2]) is not ref.
        # is_dest_mem ([DI+2]) = True. is_src_mem (0) = False. Not mem-to-mem.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source value/address into AX",
            f" mov {dest_asm}, ax   ; Store AX into destination" # No WORD PTR by translator
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_mem_to_mem(self):
        dest_tac, src_tac = "MemDest", "MemSource"
        dest_asm, src_asm = "[BP-4]", "[BP-2]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register.return_value = False # Neither is reg
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src ([BP-2]) is not ref. dest ([BP-4]) is not ref.
        # is_dest_mem = True. is_src_mem = True. IS mem-to-mem.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm}    ; Load source into AX (mem-to-mem workaround)",
            f" mov {dest_asm}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_offset_to_mem(self):
        dest_tac, src_tac = "TargetAddr", "MyString"
        dest_asm, src_asm_formatted = "[BX]", "OFFSET _S0"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm if op == dest_tac else (src_asm_formatted if op == src_tac else "ERR"))
        self._is_param_address.return_value = False
        self.generator.is_register.return_value = False
        self.generator.is_immediate = Mock(side_effect=lambda op_str: op_str == src_asm_formatted) # OFFSET is imm

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src (OFFSET _S0) is not ref. dest ([BX]) is not ref.
        # is_dest_mem ([BX]) = True. is_src_mem (OFFSET _S0) = False. Not mem-to-mem.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm_formatted}    ; Load source value/address into AX",
            f" mov {dest_asm}, ax   ; Store AX into destination" # No WORD PTR
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_same_operand_no_op_explicit_ax_ax(self):
        # This case is X = X where X is AX.
        # The current simple translator will still do: mov ax, AX; mov AX, ax.
        # A smarter one might optimize. Test what current one does.
        tac_op = "X_is_AX"
        op_asm = "AX"
        self.formatter.format_operand = Mock(return_value=op_asm)
        self._is_param_address.return_value = False
        self.generator.is_register = Mock(return_value=True) # AX is a register
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=tac_op, op1=tac_op)
        result = self._translate_assign(tac)
        # src (AX) not ref. dest (AX) not ref.
        # is_dest_mem (AX) = False. is_src_mem (AX) = False. Not mem-to-mem.
        expected = [
            f"; TAC: {tac_op} = {tac_op}",
            f" mov ax, {op_asm}    ; Load source value/address into AX", # mov ax, AX
            f" mov {op_asm}, ax   ; Store AX into destination"  # mov AX, ax
        ]
        self.assertEqual(result, expected)
        # No logger debug for no-op with this simple translator version.

    def test_translate_assign_malformed_tac_missing_dest_val(self):
        tac = self._create_tac(TACOpcode.ASSIGN, op1="Y_val")
        tac.destination = TACOperand(value=None)
        # tac.operand1 is TACOperand(value="Y_val") which is valid.
        result = self._translate_assign(tac)
        expected = [f"; ERROR: Invalid ASSIGN TAC (missing value): {tac.raw_line}"]
        self.assertEqual(result, expected)
        self.logger.error.assert_called_once_with(f"Invalid ASSIGN TAC: Missing destination or source value. Instruction: {tac}")

    def test_translate_assign_malformed_tac_missing_op1_val(self):
        tac = self._create_tac(TACOpcode.ASSIGN, dest="X_val")
        tac.operand1 = TACOperand(value=None)
        # tac.destination is TACOperand(value="X_val") which is valid.
        result = self._translate_assign(tac)
        expected = [f"; ERROR: Invalid ASSIGN TAC (missing value): {tac.raw_line}"]
        self.assertEqual(result, expected)
        self.logger.error.assert_called_once_with(f"Invalid ASSIGN TAC: Missing destination or source value. Instruction: {tac}")

    # --- ADDED/REVISED TESTS FOR PASS-BY-REFERENCE --- 

    def test_translate_assign_dest_is_ref_param_src_reg(self):
        dest_tac, src_tac = "RefParamDest", "SRC_REG"
        dest_asm_ref, src_asm_val = "[bp+4]", "CX"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_ref if op == dest_tac else (src_asm_val if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == dest_asm_ref)
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == src_asm_val)
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}", 
            f" mov ax, {src_asm_val}    ; Load source value/address into AX", # src (CX) not ref
            f" mov bx, {dest_asm_ref} ; Load address of reference param dest",
            f" mov [bx], ax      ; Store AX into dereferenced dest param"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_src_is_ref_param_dest_reg(self):
        dest_tac, src_tac = "DEST_REG", "RefParamSrc"
        dest_asm_val, src_asm_ref = "DX", "[bp+6]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_val if op == dest_tac else (src_asm_ref if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == src_asm_ref)
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == dest_asm_val) 
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov bx, {src_asm_ref} ; Load address of reference param source",
            f" mov ax, [bx]      ; Dereference source param into AX",
            f" mov {dest_asm_val}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)
        
    def test_translate_assign_src_is_ref_param_dest_ax(self):
        dest_tac, src_tac = "DEST_AX", "RefParamSrcAX"
        dest_asm_val, src_asm_ref = "AX", "[bp+7]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_val if op == dest_tac else (src_asm_ref if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == src_asm_ref)
        self.generator.is_register = Mock(side_effect=lambda op_str: op_str == dest_asm_val)
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov bx, {src_asm_ref} ; Load address of reference param source",
            f" mov ax, [bx]      ; Dereference source param into AX",
            f" mov {dest_asm_val}, ax   ; Store AX into destination" # mov AX, AX
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_both_ref_params(self):
        dest_tac, src_tac = "RefDest", "RefSrc"
        dest_asm_ref, src_asm_ref = "[bp+2]", "[bp+8]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_ref if op == dest_tac else (src_asm_ref if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str in [dest_asm_ref, src_asm_ref])
        self.generator.is_register.return_value = False
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov bx, {src_asm_ref} ; Load address of reference param source",
            f" mov ax, [bx]      ; Dereference source param into AX",
            f" mov bx, {dest_asm_ref} ; Load address of reference param dest",
            f" mov [bx], ax      ; Store AX into dereferenced dest param"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_dest_ref_src_mem(self):
        dest_tac, src_tac = "RefDest", "MemSrc"
        dest_asm_ref, src_asm_val = "[bp+10]", "[DirectMem]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_ref if op == dest_tac else (src_asm_val if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == dest_asm_ref)
        self.generator.is_register.return_value = False 
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        # src (Mem) not ref. dest (Ref) is ref.
        # is_dest_mem (for Ref) = True (due to startswith '['). is_src_mem (for Mem) = True. Not mem-to-mem path because dest is ref.
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov ax, {src_asm_val}    ; Load source value/address into AX", 
            f" mov bx, {dest_asm_ref} ; Load address of reference param dest",
            f" mov [bx], ax      ; Store AX into dereferenced dest param"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_src_ref_dest_mem(self):
        dest_tac, src_tac = "MemDest", "RefSrc"
        dest_asm_val, src_asm_ref = "[DirectMemDest]", "[bp+12]"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_val if op == dest_tac else (src_asm_ref if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == src_asm_ref)
        self.generator.is_register.return_value = False
        self.generator.is_immediate.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}",
            f" mov bx, {src_asm_ref} ; Load address of reference param source",
            f" mov ax, [bx]      ; Dereference source param into AX",
            f" mov {dest_asm_val}, ax   ; Store AX into destination"
        ]
        self.assertEqual(result, expected)

    def test_translate_assign_dest_ref_src_imm(self):
        dest_tac, src_tac = "RefDestImm", "5"
        dest_asm_ref, src_asm_val = "[bp+14]", "5"
        self.formatter.format_operand = Mock(side_effect=lambda op, tc: dest_asm_ref if op == dest_tac else (src_asm_val if op == src_tac else "ERR"))
        self._is_param_address = Mock(side_effect=lambda op_str: op_str == dest_asm_ref)
        self.generator.is_immediate = Mock(side_effect=lambda op_str: op_str == src_asm_val)
        self.generator.is_register.return_value = False

        tac = self._create_tac(TACOpcode.ASSIGN, dest=dest_tac, op1=src_tac)
        result = self._translate_assign(tac)
        expected = [
            f"; TAC: {dest_tac} = {src_tac}", 
            f" mov ax, {src_asm_val}    ; Load source value/address into AX", 
            f" mov bx, {dest_asm_ref} ; Load address of reference param dest",
            f" mov [bx], ax      ; Store AX into dereferenced dest param"
        ]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()