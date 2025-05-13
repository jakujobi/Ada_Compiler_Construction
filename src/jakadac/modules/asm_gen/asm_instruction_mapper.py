# src/jakadac/modules/asm_gen/asm_instruction_mapper.py

from typing import TYPE_CHECKING, Dict, Callable, List, Optional, Tuple, Union
import re # ADDED: Import regex module
# from ..SymTable import SymbolTable, Symbol, ArraySymbol # Old relative import
# from ..Logger import Logger # Old relative import
from jakadac.modules.SymTable import SymbolTable, Symbol #,ArraySymbol # New absolute import
from jakadac.modules.Logger import Logger # New absolute import

# Forward declaration for type hinting to avoid circular import
if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from .asm_operand_formatter import ASMOperandFormatter
    
from .tac_instruction import ParsedTACInstruction, TACOpcode
from .asm_operand_formatter import ASMOperandFormatter # <--- ADD THIS LINE

# Import the translator mixin classes
from .instruction_translators.asm_im_data_mov_translators import DataMovementTranslators
from .instruction_translators.asm_im_arithmetic_translators import ArithmeticTranslators
from .instruction_translators.asm_im_procedure_translators import ProcedureTranslators
from .instruction_translators.asm_im_control_flow_translators import ControlFlowTranslators
from .instruction_translators.asm_im_array_translators import ArrayTranslators
from .instruction_translators.asm_im_io_translators import IOTranslators
from .instruction_translators.asm_im_special_translators import SpecialTranslators


class ASMInstructionMapper(
    DataMovementTranslators,
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
        self.formatter = ASMOperandFormatter(symbol_table, asm_generator_instance, logger_instance)
        self.generator = asm_generator_instance # Reference to the generator for calling helpers
        
        self.logger.debug("ASMInstructionMapper initialized with all translator mixins.")

        # Dispatch dictionary mapping opcodes to translator methods
        self.dispatch_table: Dict[TACOpcode, Callable[[ParsedTACInstruction], List[str]]] = {
            # Arithmetic
            TACOpcode.ADD: self._translate_add,
            TACOpcode.SUB: self._translate_sub,
            TACOpcode.MUL: self._translate_mul,
            TACOpcode.DIV: self._translate_div,
            TACOpcode.REM: self._translate_rem,
            TACOpcode.MOD: self._translate_mod, # Delegate to REM
            TACOpcode.UMINUS: self._translate_neg,
            TACOpcode.NOT_OP: self._translate_not_op,

            # Data Movement
            TACOpcode.ASSIGN: self._translate_assign,

            # Control Flow
            TACOpcode.GOTO: self._translate_goto,
            TACOpcode.LABEL: self._translate_label,
            TACOpcode.IF_EQ_GOTO: self._translate_if_eq_goto,
            TACOpcode.IF_NE_GOTO: self._translate_if_ne_goto,
            TACOpcode.IF_LT_GOTO: self._translate_if_lt_goto,
            TACOpcode.IF_LE_GOTO: self._translate_if_le_goto,
            TACOpcode.IF_GT_GOTO: self._translate_if_gt_goto,
            TACOpcode.IF_GE_GOTO: self._translate_if_ge_goto,
            TACOpcode.IF_FALSE_GOTO: self._translate_if_false_goto,

            # Procedures
            TACOpcode.PARAM: self._translate_param,
            TACOpcode.PUSH: self._translate_push,
            TACOpcode.CALL: self._translate_call,
            TACOpcode.RETURN: self._translate_return,
            TACOpcode.PROC_BEGIN: self._translate_proc_begin,
            TACOpcode.PROC_END: self._translate_proc_end,
            TACOpcode.PROGRAM_START: self._translate_program_start,
            # PROGRAM_END might not need specific handling beyond normal exit

            # I/O
            TACOpcode.READ_INT: self._translate_read_int,
            TACOpcode.WRITE_INT: self._translate_write_int,
            TACOpcode.WRITE_STR: self._translate_write_str,
            TACOpcode.WRITE_NEWLINE: self._translate_write_ln,

            # Special / Data Definition
            TACOpcode.STRING_DEF: self._translate_string_def,
            
            # Array Operations
            TACOpcode.ARRAY_ASSIGN_TO: self._translate_array_assign_to, # e.g., A[i] = x
            TACOpcode.ARRAY_ASSIGN_FROM: self._translate_array_assign_from, # e.g., x = A[i]
        }

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