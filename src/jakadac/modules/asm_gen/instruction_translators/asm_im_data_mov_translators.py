# src/jakadac/modules/asm_gen/instruction_translators/asm_im_data_mov_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator 
    from ...Logger import Logger
    from ...SymTable import SymbolTable # Added for self.symbol_table hint
    
from ..tac_instruction import ParsedTACInstruction, TACOpcode

class DataMovTranslators:
    # self will be an instance of ASMInstructionMapper
    # Required attributes from ASMInstructionMapper:
    # self.logger: Logger
    # self.asm_generator: ASMGenerator
    # self.symbol_table: SymbolTable

    def _translate_assign(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ASSIGN: dest := op1"""
        if tac_instruction.destination is None or tac_instruction.destination.value is None or \
           tac_instruction.operand1 is None or tac_instruction.operand1.value is None:
            self.logger.error(f"ASSIGN TAC at line {tac_instruction.line_number} is missing destination or source operand value.")
            return [f"; ERROR: Malformed ASSIGN TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)

        asm_lines = []
        
        is_op1_literal = self.asm_generator.is_immediate(op1_asm) or op1_asm.startswith("OFFSET ")

        if dest_asm.startswith("[") and op1_asm.startswith("[") and not is_op1_literal:
            # Memory to Memory: MOV mem, mem (not allowed directly)
            asm_lines.append(f"MOV AX, {op1_asm}")
            asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"ASSIGN {tac_instruction.destination.value} := {tac_instruction.operand1.value} -> MOV AX, {op1_asm}; MOV {dest_asm}, AX")
        elif dest_asm.startswith("[") and is_op1_literal:
            # Literal to Memory: MOV mem, literal (allowed)
            asm_lines.append(f"MOV WORD PTR {dest_asm}, {op1_asm}") 
            self.logger.debug(f"ASSIGN {tac_instruction.destination.value} := {tac_instruction.operand1.value} -> MOV WORD PTR {dest_asm}, {op1_asm}")
        else:
            # Register to Memory, Memory to Register, Register to Register, Literal to Register
            if dest_asm.upper() == op1_asm.upper(): # MOV reg, reg (same register)
                self.logger.debug(f"ASSIGN {tac_instruction.destination.value} := {tac_instruction.operand1.value} -> No-op (dest and src are the same: {dest_asm})")
            else:
                asm_lines.append(f"MOV {dest_asm}, {op1_asm}")
                self.logger.debug(f"ASSIGN {tac_instruction.destination.value} := {tac_instruction.operand1.value} -> MOV {dest_asm}, {op1_asm}")
            
        return asm_lines