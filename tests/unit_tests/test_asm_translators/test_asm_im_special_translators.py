import unittest
from unittest.mock import Mock, call, patch
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
project_root = repo_root.parent 
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

from jakadac.modules.asm_gen.asm_im_special_translators import SpecialTranslators
from jakadac.modules.asm_gen.tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from jakadac.modules.Logger import Logger
from jakadac.modules.asm_gen.asm_im_arithmetic_translators import ArithmeticTranslators # For _translate_rem

class TestSpecialTranslators(unittest.TestCase, SpecialTranslators, ArithmeticTranslators): 
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

    def test_translate_string_def(self):
        string_content = '"Hello$"'
        tac = self._create_tac(TACOpcode.STRING_DEF, op1=string_content, label="_S0")
        result = self._translate_string_def(tac)
        expected = [f'; Data Definition (Handled in .DATA): _S0 DB {string_content}']
        self.assertEqual(result, expected)
        self.logger.debug.assert_called_with(f'STRING_DEF TAC for _S0 with value {string_content} encountered. Data segment handles this.')

    def test_translate_string_def_malformed_no_op1(self):
        tac = self._create_tac(TACOpcode.STRING_DEF, label="_S1") 
        tac.operand1 = None # Malform
        result = self._translate_string_def(tac)
        self.assertTrue("WARNING: Malformed STRING_DEF TAC" in result[0])
        self.logger.warning.assert_called_once()
        
    def test_translate_string_def_malformed_no_label(self):
        tac = self._create_tac(TACOpcode.STRING_DEF, op1='"Text$"') 
        tac.label = None # Malform
        result = self._translate_string_def(tac)
        self.assertTrue("WARNING: Malformed STRING_DEF TAC" in result[0])
        self.logger.warning.assert_called_once()


    def test_translate_mod_delegates_to_rem(self):
        tac = self._create_tac(TACOpcode.MOD, dest="M", op1="N", op2="D")
        expected_rem_asm = ["mocked_rem_instruction_1", "mocked_rem_instruction_2"]
        
        # Patch _translate_rem on the instance since TestSpecialTranslators also inherits ArithmeticTranslators
        with patch.object(self, '_translate_rem', return_value=expected_rem_asm) as mock_rem_translator:
            result = self._translate_mod(tac)
            mock_rem_translator.assert_called_once_with(tac)
            self.assertEqual(result, expected_rem_asm)
            self.logger.info.assert_called_with(f"MOD TAC at line {tac.line_number} is being handled like REM (using IDIV's remainder).")

if __name__ == '__main__':
    unittest.main()