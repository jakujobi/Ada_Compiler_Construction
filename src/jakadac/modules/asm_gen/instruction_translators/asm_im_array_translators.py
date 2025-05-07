# src/jakadac/modules/asm_gen/asm_im_array_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from ..Logger import Logger
    from ..SymTable import SymbolTable

from .tac_instruction import ParsedTACInstruction, TACOpcode

class ArrayTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_array_assign_from(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ARRAY_ASSIGN_FROM: dest_var := array_base[index_op]
           TAC: dest=dest_var, op1=array_base, op2=index_op"""
        dest_var_operand = tac_instruction.destination
        array_base_operand = tac_instruction.operand1
        index_operand = tac_instruction.operand2
        asm_lines = []

        if not (dest_var_operand and dest_var_operand.value is not None and
                array_base_operand and array_base_operand.value is not None and 
                index_operand and index_operand.value is not None):
            self.logger.error(f"ARRAY_ASSIGN_FROM TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_FROM TAC at line {tac_instruction.line_number}"]

        dest_var_asm = self.asm_generator.get_operand_asm(str(dest_var_operand.value), tac_instruction.opcode)
        array_base_str = str(array_base_operand.value)
        index_str = str(index_operand.value)
        
        # Get ASM for base and index separately for manipulation
        array_base_asm = self.asm_generator.get_operand_asm(array_base_str, tac_instruction.opcode)
        index_asm = self.asm_generator.get_operand_asm(index_str, tac_instruction.opcode)
        
        # Load index into SI (or DI)
        if index_asm.upper() != "SI":
            asm_lines.append(f"MOV SI, {index_asm}")
        asm_lines.append(f"SHL SI, 1") # Scale index by 2 for WORD arrays (element_size = 2)
        
        # Load base address of array into BX.
        # If array_base_asm is like '[BP-X]' (local array), LEA BX, [BP-X] is correct.
        # If array_base_asm is a global label 'MY_ARRAY', LEA BX, MY_ARRAY is correct.
        if array_base_asm.upper() != "BX":
            asm_lines.append(f"LEA BX, {array_base_asm}")
        
        asm_lines.append(f"MOV AX, [BX+SI]") # Access element: content of [base_addr_in_BX + scaled_index_in_SI]
        
        if dest_var_asm.upper() != "AX":
            asm_lines.append(f"MOV {dest_var_asm}, AX")

        self.logger.debug(f"Translated ARRAY_ASSIGN_FROM {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_array_assign_to(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ARRAY_ASSIGN_TO: array_base[index_op] := source_val
           TAC: dest=array_base, op1=index_op, op2=source_val"""
        array_base_operand = tac_instruction.destination 
        index_operand = tac_instruction.operand1
        source_value_operand = tac_instruction.operand2
        asm_lines = []

        if not (array_base_operand and array_base_operand.value is not None and 
                index_operand and index_operand.value is not None and 
                source_value_operand and source_value_operand.value is not None):
            self.logger.error(f"ARRAY_ASSIGN_TO TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_TO TAC at line {tac_instruction.line_number}"]

        array_base_str = str(array_base_operand.value)
        index_str = str(index_operand.value)
        source_value_str = str(source_value_operand.value)

        array_base_asm = self.asm_generator.get_operand_asm(array_base_str, tac_instruction.opcode)
        index_asm = self.asm_generator.get_operand_asm(index_str, tac_instruction.opcode)
        source_value_asm = self.asm_generator.get_operand_asm(source_value_str, tac_instruction.opcode)
        
        if index_asm.upper() != "SI":
            asm_lines.append(f"MOV SI, {index_asm}")
        asm_lines.append(f"SHL SI, 1") 
        
        if array_base_asm.upper() != "BX":
            asm_lines.append(f"LEA BX, {array_base_asm}")
        
        is_source_literal = self.asm_generator.is_immediate(source_value_asm)
        
        if not is_source_literal:
            if source_value_asm.upper() != "AX":
                 asm_lines.append(f"MOV AX, {source_value_asm}")
            asm_lines.append(f"MOV [BX+SI], AX")
        else: 
            asm_lines.append(f"MOV WORD PTR [BX+SI], {source_value_asm}")

        self.logger.debug(f"Translated ARRAY_ASSIGN_TO {tac_instruction} -> {asm_lines}")
        return asm_lines