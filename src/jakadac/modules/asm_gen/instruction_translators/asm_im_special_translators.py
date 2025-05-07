# src/jakadac/modules/asm_gen/asm_im_special_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from ..Logger import Logger
    from ..SymTable import SymbolTable # Added for self.symbol_table hint
    from .asm_im_arithmetic_translators import ArithmeticTranslators # For _translate_rem

from .tac_instruction import ParsedTACInstruction, TACOpcode

class SpecialTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_string_def(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC STRING_DEF (:ASCIZ). This is a data definition.
           The ASMGenerator's _generate_data_segment handles actual data emission.
        """
        label = tac_instruction.label
        # operand1 of STRING_DEF holds the string value itself (e.g. '"Hello$"')
        string_val_op = tac_instruction.operand1 

        if label and string_val_op and string_val_op.value is not None:
            self.logger.debug(f"STRING_DEF TAC for {label} with value {string_val_op.value} encountered. Data segment handles this.")
            # This TAC instruction does not produce executable code here.
            return [f"; Data Definition (Handled in .DATA): {label} DB {string_val_op.value}"]
        else:
            self.logger.warning(f"Malformed STRING_DEF TAC at line {tac_instruction.line_number}: {tac_instruction.raw_line.strip()}")
            return [f"; WARNING: Malformed STRING_DEF TAC: {tac_instruction.raw_line.strip()}"]

    def _translate_mod(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC MOD: dest := op1 mod op2"""
        # For signed integers using IDIV, the remainder is in DX.
        # This behavior is often what's expected for 'rem'.
        # Ada 'mod' might have specific rules for signs (e.g. result has sign of divisor).
        # If current 'rem' (IDIV) behavior is acceptable for 'mod':
        self.logger.info(f"MOD TAC at line {tac_instruction.line_number} is being handled like REM (using IDIV's remainder).")
        # We need to call _translate_rem, which is in ArithmeticTranslators.
        # Since ASMInstructionMapper inherits from ArithmeticTranslators, self has the method.
        
        # Explicitly type self for the IDE if it struggles with multiple inheritance here
        arithmetic_translator_self = self
        return arithmetic_translator_self._translate_rem(tac_instruction)