# src/jakadac/modules/asm_gen/asm_instruction_mapper.py

from typing import TYPE_CHECKING, List, Any
import re # ADDED: Import regex module

# Forward declaration for type hinting to avoid circular import
if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from ..SymTable import SymbolTable
    from ..Logger import Logger # Assuming Logger is a class, logger is an instance
    
from .tac_instruction import ParsedTACInstruction, TACOpcode

# Import the translator mixin classes
from .instruction_translators.asm_im_data_mov_translators import DataMovTranslators
from .instruction_translators.asm_im_arithmetic_translators import ArithmeticTranslators
from .instruction_translators.asm_im_procedure_translators import ProcedureTranslators
from .instruction_translators.asm_im_control_flow_translators import ControlFlowTranslators
from .instruction_translators.asm_im_array_translators import ArrayTranslators
from .instruction_translators.asm_im_io_translators import IOTranslators
from .instruction_translators.asm_im_special_translators import SpecialTranslators


class ASMInstructionMapper(
    DataMovTranslators,
    ArithmeticTranslators,
    ProcedureTranslators,
    ControlFlowTranslators,
    ArrayTranslators,
    IOTranslators,
    SpecialTranslators
):
    def __init__(self, symbol_table: 'SymbolTable', logger_instance: 'Logger', asm_generator_instance: 'ASMGenerator'):
        self.symbol_table: 'SymbolTable' = symbol_table
        self.logger: 'Logger' = logger_instance 
        self.asm_generator: 'ASMGenerator' = asm_generator_instance
        self.formatter = ASMOperandFormatter(symbol_table)
        self.generator = asm_generator_instance # Reference to the generator for calling helpers
        
        self.logger.debug("ASMInstructionMapper initialized with all translator mixins.")

        # Dispatch dictionary mapping opcodes to translator methods
        # ... existing code ...

        # Precompile regex for efficiency
        self._param_addr_regex = re.compile(r'^\[bp\+(\d+)\]$')

    def _is_param_address(self, operand_asm: str) -> bool:
        """Checks if a formatted operand string represents a parameter address ([bp+N])."""
        return bool(self._param_addr_regex.match(operand_asm))

    def translate(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translates a single TAC instruction to its corresponding ASM code lines.
        Dynamically dispatches to a _translate_<opcode> method.
        Returns a list of ASM instruction strings.
        """
        if tac_instruction.opcode is None:
            self.logger.error(f"TAC instruction at line {tac_instruction.line_number} has no opcode.")
            return [f"; ERROR: TAC instruction at line {tac_instruction.line_number} has no opcode."]

        opcode_value_str = ""
        log_opcode_repr = ""

        if isinstance(tac_instruction.opcode, TACOpcode):
            opcode_value_str = tac_instruction.opcode.name.lower()
            log_opcode_repr = tac_instruction.opcode.name
        elif isinstance(tac_instruction.opcode, str):
            # Handle potential direct string opcodes from parser if TACOpcode.from_string mapped to UNKNOWN
            # but the string itself is kept.
            # Convert known string opcodes to their canonical enum name lowercased if possible.
            # This section might need refinement based on how tac_parser.py handles truly unknown opcodes vs.
            # opcodes that have direct string representation like "=" or "+".
            # For now, assume if it's a string, it's already in a form that can be lowercased for method lookup.
            temp_opcode_enum = TACOpcode.from_string(tac_instruction.opcode)
            if temp_opcode_enum != TACOpcode.UNKNOWN:
                opcode_value_str = temp_opcode_enum.name.lower()
                log_opcode_repr = temp_opcode_enum.name
            else: # Truly unknown string opcode
                opcode_value_str = tac_instruction.opcode.replace(":", "_").replace(" ", "_").lower() # Sanitize for method name
                log_opcode_repr = tac_instruction.opcode
        else:
            self.logger.error(f"Invalid opcode type: {type(tac_instruction.opcode)} for TAC: {tac_instruction}")
            return [f"; ERROR: Invalid opcode type at line {tac_instruction.line_number}."]

        handler_method_name = f"_translate_{opcode_value_str}"
        handler_method = getattr(self, handler_method_name, self._translate_unknown)
        
        self.logger.debug(f"Translating TAC Op: {log_opcode_repr}, Line: {tac_instruction.line_number} using {handler_method_name if handler_method != self._translate_unknown else 'unknown handler'}")
        
        asm_lines = handler_method(tac_instruction)
        
        if not isinstance(asm_lines, list):
            self.logger.warning(f"Handler {handler_method_name} for opcode {log_opcode_repr} did not return a list. Returned: {asm_lines}. Wrapping in a list.")
            if asm_lines is None:
                return [f"; ERROR: Handler for {log_opcode_repr} returned None"]
            return [str(asm_lines)]
            
        return asm_lines

    def _translate_unknown(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        opcode_name = tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else str(tac_instruction.opcode)
        
        dest_str = str(tac_instruction.destination.value) if tac_instruction.destination and tac_instruction.destination.value is not None else "None"
        op1_str = str(tac_instruction.operand1.value) if tac_instruction.operand1 and tac_instruction.operand1.value is not None else "None"
        op2_str = str(tac_instruction.operand2.value) if tac_instruction.operand2 and tac_instruction.operand2.value is not None else "None"
        
        line_num = tac_instruction.line_number if hasattr(tac_instruction, 'line_number') else 'N/A'
        
        self.logger.warning(f"No specific translator for TAC opcode: {opcode_name} at line {line_num}")
        
        return [f"; UNHANDLED TAC Opcode: {opcode_name} (Operands: D:{dest_str}, O1:{op1_str}, O2:{op2_str})"]