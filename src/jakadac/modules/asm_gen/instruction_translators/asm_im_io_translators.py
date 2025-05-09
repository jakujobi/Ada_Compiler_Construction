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
        """Translates TAC READ_INT (rdi): dest_var (destination)"""
        dest_var_operand = tac_instruction.destination
        asm_lines = []

        if not dest_var_operand or dest_var_operand.value is None:
            self.logger.error(f"READ_INT TAC at line {tac_instruction.line_number} is missing destination operand value.")
            return [f"; ERROR: Malformed READ_INT TAC at line {tac_instruction.line_number}"]

        dest_var_asm = self.asm_generator.get_operand_asm(str(dest_var_operand.value), tac_instruction.opcode)
        
        asm_lines.append(f"CALL READINT") 
        if dest_var_asm.upper() != "AX":
            asm_lines.append(f"MOV {dest_var_asm}, BX")
        
        self.logger.debug(f"Translated READ_INT {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_int(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC WRITE_INT (wri): source_var_or_literal (operand1)"""
        source_operand = tac_instruction.operand1
        asm_lines = []

        if not source_operand or source_operand.value is None:
            self.logger.error(f"WRITE_INT TAC at line {tac_instruction.line_number} is missing source operand value.")
            return [f"; ERROR: Malformed WRITE_INT TAC at line {tac_instruction.line_number}"]

        source_asm = self.asm_generator.get_operand_asm(str(source_operand.value), tac_instruction.opcode)

        if source_asm.upper() != "AX":
            asm_lines.append(f"MOV AX, {source_asm}")
        asm_lines.append(f"CALL WRITEINT") 
        
        self.logger.debug(f"Translated WRITE_INT {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_str(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC WRITE_STR (wrs): string_label (operand1)"""
        string_label_operand = tac_instruction.operand1
        asm_lines = []

        if not string_label_operand or string_label_operand.value is None:
            self.logger.error(f"WRITE_STR TAC at line {tac_instruction.line_number} is missing string label operand value.")
            return [f"; ERROR: Malformed WRITE_STR TAC at line {tac_instruction.line_number}"]

        string_label_str = str(string_label_operand.value)
        # get_operand_asm for a string label like _S0 should return "OFFSET _S0" or just "_S0"
        # if it's globally defined. For WRITESTRING, we need OFFSET.
        # The get_operand_asm method should be smart enough to add OFFSET if it's a label for WRS.
        
        # For WRITESTRING from io.asm, DX needs the offset of the string.
        # Ensure get_operand_asm returns "OFFSET label" if string_label_str is a label.
        # If it returns just "label", then "MOV DX, OFFSET label" is needed.
        # The provided get_operand_asm returns "OFFSET _S0" for string labels.

        string_label_asm_with_offset = self.asm_generator.get_operand_asm(string_label_str, tac_instruction.opcode)
        
        if string_label_asm_with_offset.upper() != "DX": 
             asm_lines.append(f"MOV DX, {string_label_asm_with_offset}")
        asm_lines.append(f"CALL WRITESTRING")
        
        self.logger.debug(f"Translated WRITE_STR {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_write_newline(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC WRITE_NEWLINE (wrln)"""
        asm_lines = ["CALL NEWLINE"] 
        self.logger.debug(f"Translated WRITE_NEWLINE {tac_instruction} -> {asm_lines}")
        return asm_lines