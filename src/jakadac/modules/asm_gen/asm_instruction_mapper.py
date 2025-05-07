# src/jakadac/modules/asm_gen/asm_instruction_mapper.py

from ..SymTable import SymbolTable
from .asm_operand_formatter import ASMOperandFormatter
from .tac_instruction import ParsedTACInstruction #, TACOpcode
from ..Logger import logger

class ASMInstructionMapper:
    def __init__(self, symbol_table: SymbolTable, operand_formatter: ASMOperandFormatter):
        self.symbol_table = symbol_table
        self.operand_formatter = operand_formatter
        logger.debug("ASMInstructionMapper initialized.")

    def translate(self, tac_instruction: ParsedTACInstruction) -> str:
        """
        Translates a single TAC instruction to its corresponding ASM code string(s).
        This is a placeholder for Phase 2. Full implementation in later phases.
        Returns a string, which could contain multiple lines of ASM ('\n' separated).
        """

        logger.debug(f"ASMInstructionMapper.translate called for {tac_instruction.opcode} (currently basic placeholder)")
        
        # Example of how it might start for Phase 3:
        # opcode_str = tac_instruction.opcode.name.upper() if tac_instruction.opcode else "UNKNOWN"
        # handler_method_name = f"_translate_{opcode_str.lower()}"
        # handler_method = getattr(self, handler_method_name, self._translate_unknown)
        # return handler_method(tac_instruction)

        return f"; TAC Opcode: {tac_instruction.opcode.name if tac_instruction.opcode else 'UNKNOWN'} - Placeholder translation. Operands: {tac_instruction.op1}, {tac_instruction.op2}, {tac_instruction.dest}"

    def _translate_unknown(self, tac_instruction: ParsedTACInstruction) -> str:
        logger.warning(f"No specific translator for TAC opcode: {tac_instruction.opcode}")
        return f"; UNHANDLED TAC Opcode: {tac_instruction.opcode.name if tac_instruction.opcode else 'UNKNOWN'}"

# Future methods like:
# def _translate_assign(self, tac_instruction: ParsedTACInstruction) -> str:
#     dest = self.operand_formatter.format_operand(tac_instruction.dest)
#     op1 = self.operand_formatter.format_operand(tac_instruction.op1)
#     if tac_instruction.op2: # Binary assignment (should be handled by specific opcodes like ADD, MUL)
#         # This case for generic 'assign' with op2 is unlikely if TAC is well-formed
#         return f"; Complex assignment, should be specific op: {tac_instruction.opcode}"
#     else: # Simple assignment
#         return f"    MOV AX, {op1}\n    MOV {dest}, AX"