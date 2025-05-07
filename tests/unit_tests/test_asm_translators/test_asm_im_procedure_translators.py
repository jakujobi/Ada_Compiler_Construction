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

from jakadac.modules.asm_gen.instruction_translators.asm_im_procedure_translators import ProcedureTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.SymTable import Symbol, EntryType, SymbolTable
from jakadac.modules.Logger import Logger

class TestProcedureTranslators(unittest.TestCase, ProcedureTranslators):
    def setUp(self):
        self.logger = Mock(spec=Logger)
        self.asm_generator = Mock()
        self.symbol_table = Mock(spec=SymbolTable) 

        self.asm_generator.logger = self.logger 
        self.asm_generator.symbol_table = self.symbol_table 

        self.asm_generator.get_operand_asm = Mock(
            side_effect=lambda op_val_str, tac_opcode: str(op_val_str) + "_asm" if op_val_str is not None else ""
        )
        
        self.mock_proc_sym = Mock(spec=Symbol)
        self.mock_proc_sym.name = "TestProc"
        self.mock_proc_sym.local_size = 0 
        self.mock_proc_sym.entry_type = EntryType.PROCEDURE
        self.asm_generator.current_procedure_context = self.mock_proc_sym # Default context
        self.symbol_table.lookup_globally = Mock(return_value=self.mock_proc_sym) # Default lookup


    def _create_tac(self, opcode, dest=None, op1=None, op2=None, label=None, line_number=1, raw_line="mock_raw_tac_line"):
        instr = ParsedTACInstruction(line_number=line_number, raw_line=raw_line)
        instr.opcode = opcode
        instr.label = label
        instr.destination = TACOperand(value=dest) if dest is not None else None
        instr.operand1 = TACOperand(value=op1) if op1 is not None else None
        instr.operand2 = TACOperand(value=op2) if op2 is not None else None
        return instr

    def test_translate_program_start_no_locals(self):
        proc_name = "MyMain"
        self.mock_proc_sym.name = proc_name
        self.mock_proc_sym.local_size = 0
        self.asm_generator.current_procedure_context = self.mock_proc_sym
        self.symbol_table.lookup_globally.return_value = self.mock_proc_sym

        tac = self._create_tac(TACOpcode.PROGRAM_START, dest=proc_name)
        result = self._translate_program_start(tac)
        expected = [f"{proc_name} PROC NEAR", "PUSH BP", "MOV BP, SP"]
        self.assertEqual(result, expected)

    def test_translate_program_start_with_locals_context_mismatch_resolved(self):
        proc_name = "AppEntry"
        # Simulate context being initially for a different proc or None
        self.asm_generator.current_procedure_context = None 
        
        correct_proc_sym = Mock(spec=Symbol)
        correct_proc_sym.name = proc_name
        correct_proc_sym.local_size = 8
        correct_proc_sym.entry_type = EntryType.PROCEDURE
        self.symbol_table.lookup_globally.return_value = correct_proc_sym

        tac = self._create_tac(TACOpcode.PROGRAM_START, dest=proc_name)
        result = self._translate_program_start(tac)
        expected = [f"{proc_name} PROC NEAR", "PUSH BP", "MOV BP, SP", "SUB SP, 8"]
        self.assertEqual(result, expected)
        self.logger.warning.assert_called_once() # Due to initial context mismatch
        self.assertEqual(self.asm_generator.current_procedure_context, correct_proc_sym)


    def test_translate_proc_begin_with_locals(self):
        proc_name = "Subroutine"
        self.mock_proc_sym.name = proc_name
        self.mock_proc_sym.local_size = 4
        self.asm_generator.current_procedure_context = self.mock_proc_sym
        self.symbol_table.lookup_globally.return_value = self.mock_proc_sym

        tac = self._create_tac(TACOpcode.PROC_BEGIN, dest=proc_name)
        result = self._translate_proc_begin(tac)
        expected = [f"{proc_name} PROC NEAR", "PUSH BP", "MOV BP, SP", "SUB SP, 4"]
        self.assertEqual(result, expected)

    def test_translate_proc_end_no_locals(self):
        proc_name = "UtilProc"
        self.mock_proc_sym.name = proc_name
        self.mock_proc_sym.local_size = 0
        self.asm_generator.current_procedure_context = self.mock_proc_sym

        tac = self._create_tac(TACOpcode.PROC_END, dest=proc_name)
        result = self._translate_proc_end(tac)
        expected = ["POP BP", f"{proc_name} ENDP"]
        self.assertEqual(result, expected)

    def test_translate_proc_end_with_locals_context_mismatch_resolved(self):
        proc_name = "CalcProc"
        # Simulate current context is for another procedure
        other_proc_sym = Mock(spec=Symbol, name="OtherProc", local_size=2)
        self.asm_generator.current_procedure_context = other_proc_sym
        
        # Setup lookup_globally to return the correct proc info for "CalcProc"
        calc_proc_sym = Mock(spec=Symbol, name=proc_name, local_size=6, entry_type=EntryType.PROCEDURE)
        self.symbol_table.lookup_globally.return_value = calc_proc_sym

        tac = self._create_tac(TACOpcode.PROC_END, dest=proc_name)
        result = self._translate_proc_end(tac)
        expected = ["MOV SP, BP", "POP BP", f"{proc_name} ENDP"]
        self.assertEqual(result, expected)
        self.logger.warning.assert_called_with(f"PROC_END {proc_name}: Context mismatch but found entry; assuming MOV SP,BP based on looked up local_size.")


    def test_translate_return_void(self):
        tac = self._create_tac(TACOpcode.RETURN)
        result = self._translate_return(tac)
        self.assertEqual(result, ["RET"])

    def test_translate_return_value_not_ax(self):
        self.asm_generator.get_operand_asm.return_value = "MyReturnValue_asm"
        tac = self._create_tac(TACOpcode.RETURN, op1="MyReturnValue")
        result = self._translate_return(tac)
        expected = ["MOV AX, MyReturnValue_asm", "RET"]
        self.assertEqual(result, expected)

    def test_translate_return_value_is_ax(self):
        self.asm_generator.get_operand_asm.return_value = "AX" 
        tac = self._create_tac(TACOpcode.RETURN, op1="ValInAX")
        result = self._translate_return(tac)
        expected = ["RET"] 
        self.assertEqual(result, expected)
        self.logger.debug.assert_any_call("RETURN ValInAX: Value already in AX.")


    def test_translate_call_no_params_no_ret(self):
        tac = self._create_tac(TACOpcode.CALL, op1="SimpleProc", op2=0)
        result = self._translate_call(tac)
        self.assertEqual(result, ["CALL SimpleProc_asm"])

    def test_translate_call_with_params_no_ret(self):
        tac = self._create_tac(TACOpcode.CALL, op1="ProcWithArgs", op2=2) 
        result = self._translate_call(tac)
        expected = ["CALL ProcWithArgs_asm", "ADD SP, 4"] 
        self.assertEqual(result, expected)

    def test_translate_call_no_params_with_ret_not_ax(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, tc: "ResultVar_asm" if op_v_s == "ResultVar" else (str(op_v_s)+"_asm" if op_v_s else "")
        tac = self._create_tac(TACOpcode.CALL, dest="ResultVar", op1="FuncNoArgs", op2=0)
        result = self._translate_call(tac)
        expected = ["CALL FuncNoArgs_asm", "MOV ResultVar_asm, AX"]
        self.assertEqual(result, expected)

    def test_translate_call_with_params_with_ret_is_ax(self):
        self.asm_generator.get_operand_asm.side_effect = lambda op_v_s, tc: "AX" if op_v_s == "ResultInAX" else (str(op_v_s)+"_asm" if op_v_s else "")
        tac = self._create_tac(TACOpcode.CALL, dest="ResultInAX", op1="ComplexFunc", op2=1)
        result = self._translate_call(tac)
        expected = ["CALL ComplexFunc_asm", "ADD SP, 2"] # MOV AX, AX optimized out
        self.assertEqual(result, expected)
        self.logger.debug.assert_any_call("CALL to ComplexFunc_asm with 1 params, returning to AX")


    def test_translate_push_value(self):
        tac_operand = TACOperand(value="MyVal", is_address_of=False)
        tac = self._create_tac(TACOpcode.PUSH)
        tac.operand1 = tac_operand
        self.asm_generator.get_operand_asm.return_value = "MyVal_asm"
        result = self._translate_push(tac)
        self.assertEqual(result, ["PUSH MyVal_asm"])

    def test_translate_push_address_global(self):
        tac_operand = TACOperand(value="GlobalVar", is_address_of=True)
        tac = self._create_tac(TACOpcode.PUSH)
        tac.operand1 = tac_operand
        self.asm_generator.get_operand_asm.return_value = "GlobalVar_asm" 
        result = self._translate_push(tac)
        self.assertEqual(result, ["PUSH OFFSET GlobalVar_asm"])

    def test_translate_push_address_local(self):
        tac_operand = TACOperand(value="LocalVar", is_address_of=True)
        tac = self._create_tac(TACOpcode.PUSH)
        tac.operand1 = tac_operand
        self.asm_generator.get_operand_asm.return_value = "[BP-4]" 
        result = self._translate_push(tac)
        self.assertEqual(result, ["LEA AX, [BP-4]", "PUSH AX"])

    def test_translate_param_delegates_to_push(self):
        with patch.object(self, '_translate_push', return_value=["mocked_push_asm"]) as mock_push_method:
            tac = self._create_tac(TACOpcode.PARAM, op1="ParamToPush")
            result = self._translate_param(tac)
            mock_push_method.assert_called_once_with(tac)
            self.assertEqual(result, ["mocked_push_asm"])
            self.logger.debug.assert_called_with(f"PARAM TAC at line {tac.line_number} is being handled like PUSH.")

if __name__ == '__main__':
    unittest.main()