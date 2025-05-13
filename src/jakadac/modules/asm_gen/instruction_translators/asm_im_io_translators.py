# src/jakadac/modules/asm_gen/instruction_translators/asm_im_io_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator
    from ...Logger import Logger
    from ...SymTable import SymbolTable

from ..tac_instruction import ParsedTACInstruction, TACOpcode

class IOTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_read_int(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates READ_INT: Reads an integer into dest_var."""
        # TAC: (RDI, dest_var)
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_var_operand = tac_instruction.destination
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not dest_var_operand or dest_var_operand.value is None:
            self.logger.error(f"READ_INT TAC at line {tac_instruction.line_number} is missing destination operand value.")
            return [f"; ERROR: Malformed READ_INT TAC at line {tac_instruction.line_number}"]

        dest_var_asm = self.formatter.format_operand(str(dest_var_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        
        asm_lines.append(f"CALL READINT") 
        # READINT from io.asm returns value in BX
        if dest_var_asm.upper() != "BX": # Avoid MOV BX, BX
            asm_lines.append(f"MOV {dest_var_asm}, BX")
        
        self.logger.debug(f"Translated READ_INT {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_int(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates WRITE_INT: Writes an integer source_var."""
        # TAC: (WRI, source_var)
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        source_operand = tac_instruction.operand1 # Source for WRI is operand1
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not source_operand or source_operand.value is None:
            self.logger.error(f"WRITE_INT TAC at line {tac_instruction.line_number} is missing source operand value.")
            return [f"; ERROR: Malformed WRITE_INT TAC at line {tac_instruction.line_number}"]

        source_asm = self.formatter.format_operand(str(source_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        # WRITEINT from io.asm expects value in AX
        if source_asm.upper() != "AX": # Avoid MOV AX, AX
            asm_lines.append(f"MOV AX, {source_asm}")
        asm_lines.append(f"CALL WRITEINT")
        asm_lines.append(f"CALL NEWLINE") # Add a newline for better output formatting after int

        self.logger.debug(f"Translated WRITE_INT {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_str(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates WRITE_STR: Writes a string_label."""
        # TAC: (WRS, string_label_operand) e.g. _S0
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        string_label_operand = tac_instruction.operand1 # String label for WRS is operand1
        active_proc_ctx = self.asm_generator.current_procedure_context # Though not strictly needed for string labels

        if not string_label_operand or string_label_operand.value is None:
            self.logger.error(f"WRITE_STR TAC at line {tac_instruction.line_number} is missing string label operand.")
            return [f"; ERROR: Malformed WRITE_STR TAC at line {tac_instruction.line_number}"]

        # The formatter should return "OFFSET _S0" if string_label_operand.value is "_S0"
        # and _S0 is a known string literal from asm_generator.string_literals_map
        string_label_asm_with_offset = self.formatter.format_operand(str(string_label_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        # WRITESTR from io.asm expects address of string in DX
        # string_label_asm_with_offset should be like "OFFSET _S0"
        # We need to ensure DX gets the actual address, not the word "OFFSET"
        # If formatter returns "OFFSET _S0", we load _S0 into DX. Assembler handles OFFSET.
        actual_label = string_label_asm_with_offset.replace("OFFSET ", "")

        if actual_label.upper() != "DX": # Avoid MOV DX, DX, though unlikely
             asm_lines.append(f"MOV DX, OFFSET {actual_label}") # Correct way to load address for WRITESTR
        asm_lines.append(f"CALL WRITESTR")
        # WRITESTR in provided io.asm might or might not add a newline. 
        # Assuming it doesn't, for consistency like WRITEINT:
        asm_lines.append(f"CALL NEWLINE")
        
        self.logger.debug(f"Translated WRITE_STR {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_ln(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates WRITE_LN: Writes a newline character."""
        # TAC: (WRLN)
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        asm_lines.append(f"CALL NEWLINE")
        self.logger.debug(f"Translated WRITE_LN {tac_instruction} -> {asm_lines}")
        return asm_lines