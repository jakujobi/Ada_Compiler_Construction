# src/jakadac/modules/asm_gen/instruction_translators/asm_im_data_mov_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator # For type hinting active_procedure_context
    from ...SymTable import Symbol # For type hinting active_procedure_symbol
    # ASMOperandFormatter is available via self.formatter
    
from ..tac_instruction import ParsedTACInstruction, TACOpcode

class DataMovementTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_assign(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates ASSIGN: dest = source"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        source_operand = tac_instruction.operand1 # In simple assign, source is operand1
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not dest_operand or dest_operand.value is None or \
           not source_operand or source_operand.value is None:
            self.logger.error(f"ASSIGN TAC at line {tac_instruction.line_number} is missing destination or source value.")
            return [f"; ERROR: Malformed ASSIGN TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        source_asm = self.formatter.format_operand(str(source_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        # Avoid memory-to-memory MOV if both are memory operands (e.g. [BP-2] = [BP-4])
        # Heuristic: if both start with \"[\"
        is_dest_mem = dest_asm.startswith("[")
        is_source_mem = source_asm.startswith("[")

        if is_dest_mem and is_source_mem:
            asm_lines.append(f" mov ax, {source_asm}    ; Load source into AX (mem-to-mem workaround)")
            asm_lines.append(f" mov {dest_asm}, ax   ; Store AX into destination")
        elif dest_asm == source_asm:
            asm_lines.append(f"; mov {dest_asm}, {source_asm} ; Redundant MOV, skipped")
            self.logger.debug(f"ASSIGN {tac_instruction}: Skipped redundant mov {dest_asm}, {source_asm}")
        else:
            asm_lines.append(f" mov ax, {source_asm}    ; Load source value/address into AX") # General case: use AX
            asm_lines.append(f" mov {dest_asm}, ax   ; Store AX into destination")
            
        self.logger.debug(f"Translated ASSIGN {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_array_assign_from(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates ARRAY_ASSIGN_FROM (Indexed Read): dest = array[index]"""
        # TAC: (ARRAY_ASSIGN_FROM, dest, array_base_name, index_val_or_temp)
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        array_name_operand = tac_instruction.operand1 
        index_operand = tac_instruction.operand2 
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, array_name_operand, index_operand,
                    dest_operand.value is not None, array_name_operand.value is not None, index_operand.value is not None]):
            self.logger.error(f"ARRAY_ASSIGN_FROM TAC at line {tac_instruction.line_number} missing operands/values.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_FROM TAC: {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        array_base_asm = self.formatter.format_operand(str(array_name_operand.value), TACOpcode.ARRAY_BASE_ADDR, active_procedure_symbol=active_proc_ctx) # Special context for base
        index_asm = self.formatter.format_operand(str(index_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        # Assuming element size is WORD (2 bytes)
        asm_lines.append(f" mov bx, {index_asm}    ; Load index into BX")
        asm_lines.append(f" shl bx, 1           ; Multiply index by 2 (element size)")
        # If array_base_asm is a label (global/static), LEA is fine.
        # If array_base_asm is [BP-offset] (local array base on stack), LEA [BP-offset] is valid.
        asm_lines.append(f" lea si, {array_base_asm} ; Load base address of array into SI")
        asm_lines.append(f" add si, bx            ; Add scaled index to base address (SI = addr of element)")
        asm_lines.append(f" mov ax, [si]          ; Load array element value into AX")
        asm_lines.append(f" mov {dest_asm}, ax   ; Store element value into destination")

        self.logger.debug(f"Translated ARRAY_ASSIGN_FROM {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_array_assign_to(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates ARRAY_ASSIGN_TO (Indexed Write): array[index] = source"""
        # TAC: (ARRAY_ASSIGN_TO, array_base_name, index_val_or_temp, source_val_or_temp)
        # Note: operand mapping in TACInstruction might be: dest=arr_name, op1=index, op2=source
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        array_name_operand = tac_instruction.destination # First operand in TAC for this form
        index_operand = tac_instruction.operand1
        source_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([array_name_operand, index_operand, source_operand,
                    array_name_operand.value is not None, index_operand.value is not None, source_operand.value is not None]):
            self.logger.error(f"ARRAY_ASSIGN_TO TAC at line {tac_instruction.line_number} missing operands/values.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_TO TAC: {tac_instruction.line_number}"]

        array_base_asm = self.formatter.format_operand(str(array_name_operand.value), TACOpcode.ARRAY_BASE_ADDR, active_procedure_symbol=active_proc_ctx)
        index_asm = self.formatter.format_operand(str(index_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        source_asm = self.formatter.format_operand(str(source_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        asm_lines.append(f" mov ax, {source_asm}   ; Load source value into AX")
        asm_lines.append(f" mov bx, {index_asm}    ; Load index into BX")
        asm_lines.append(f" shl bx, 1           ; Multiply index by 2 (element size)")
        asm_lines.append(f" lea si, {array_base_asm} ; Load base address of array into SI")
        asm_lines.append(f" add si, bx            ; Add scaled index to base address")
        asm_lines.append(f" mov [si], ax          ; Store source value into array element")

        self.logger.debug(f"Translated ARRAY_ASSIGN_TO {tac_instruction} -> {asm_lines}")
        return asm_lines