# src/jakadac/modules/asm_gen/instruction_translators/asm_im_data_mov_translators.py

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator 
    from ...Logger import Logger
    from ...SymTable import SymbolTable # Added for self.symbol_table hint
    from ..asm_instruction_mapper import ASMInstructionMapper
    from ..tac_instruction import ParsedTACInstruction
    
from ..tac_instruction import ParsedTACInstruction, TACOpcode

class DataMovTranslators:
    # self will be an instance of ASMInstructionMapper
    # Required attributes from ASMInstructionMapper:
    # self.logger: Logger
    # self.asm_generator: ASMGenerator
    # self.symbol_table: SymbolTable

    def _translate_assign(self: 'ASMInstructionMapper', tac_instruction: 'ParsedTACInstruction') -> List[str]:
        """
        Translate TAC ASSIGN (dest = src) to 8086 assembly.
        Handles dereferencing for pass-by-reference parameters.
        Format: dest = src (e.g., x = y, x = 5, [bp-2] = _t1, [bp+4] = ax)
        TAC Format: (ASSIGN, dest, src) or (ASSIGN, dest, op, src) for unary?
                    Assuming (ASSIGN, dest, src) for simple assignment.
        """
        asm = []
        # Check for missing operand VALUES
        if tac_instruction.destination is None or tac_instruction.destination.value is None or \
           tac_instruction.operand1 is None or tac_instruction.operand1.value is None:
            self.logger.error(f"Invalid ASSIGN TAC: Missing destination or source value. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid ASSIGN TAC (missing value): {tac_instruction.raw_line}"]

        # Get formatted ASM operands
        dest_asm = self.formatter.format_operand(str(tac_instruction.destination), tac_instruction.opcode)
        src_asm = self.formatter.format_operand(str(tac_instruction.operand1), tac_instruction.opcode)

        # Check if operands are reference parameters
        is_dest_ref = self._is_param_address(dest_asm)
        is_src_ref = self._is_param_address(src_asm)
        is_src_immediate = self.generator.is_immediate(src_asm)

        asm.append(f"; TAC: {tac_instruction.destination} = {tac_instruction.operand1}")

        # Step 1: Load source value into AX (handle dereference if needed)
        if is_src_ref:
            asm.append(f" mov bx, {src_asm} ; Load address of reference param source")
            asm.append(f" mov ax, [bx]      ; Dereference source param into AX")
        else:
            # Check for direct memory-to-memory move, which is illegal
            is_dest_mem = dest_asm.startswith('[') or not self.generator.is_register(dest_asm) and not self.generator.is_immediate(dest_asm)
            is_src_mem = src_asm.startswith('[') or not self.generator.is_register(src_asm) and not self.generator.is_immediate(src_asm)
            
            if is_dest_mem and is_src_mem and not is_dest_ref and not is_src_ref:
                # Illegal memory-to-memory: Use AX as intermediate
                 asm.append(f" mov ax, {src_asm}    ; Load source into AX (mem-to-mem workaround)")
                 # AX now holds the source value for Step 2
            else:
                 # Can potentially move directly if destination is register or source is immediate/register
                 # Or if one is memory and the other is not (handled below in Step 2)
                 # For simplicity, we often use AX anyway. Let's load source into AX.
                 asm.append(f" mov ax, {src_asm}    ; Load source value/address into AX")

        # Step 2: Store value from AX into destination (handle dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store AX into dereferenced dest param")
        else:
            # If we didn't need AX as intermediate for mem-to-mem, this is direct store
            # If we *did* use AX as intermediate, this stores AX to the final dest
            asm.append(f" mov {dest_asm}, ax   ; Store AX into destination")

        return asm