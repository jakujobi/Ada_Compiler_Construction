# src/jakadac/modules/asm_gen/asm_im_arithmetic_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from ..Logger import Logger
    from ..SymTable import SymbolTable # Added for self.symbol_table hint

from .tac_instruction import ParsedTACInstruction, TACOpcode

class ArithmeticTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_add(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ADD: dest := op1 + op2"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None,
                    tac_instruction.operand2, tac_instruction.operand2.value is not None]):
            self.logger.error(f"ADD TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed ADD TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand2.value), tac_instruction.opcode)

        asm_lines = []
        if dest_asm.upper() == op1_asm.upper():
            # ADD dest, op2 (if dest and op1 are the same)
            asm_lines.append(f"ADD {dest_asm}, {op2_asm}")
            self.logger.debug(f"ADD {tac_instruction.destination.value} := {tac_instruction.operand1.value} + {tac_instruction.operand2.value} -> ADD {dest_asm}, {op2_asm}")
        else:
            # General case: MOV AX, op1; ADD AX, op2; MOV dest, AX
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
            else: # op1_asm is AX
                pass # Value already in AX
            asm_lines.append(f"ADD AX, {op2_asm}")
            if dest_asm.upper() != "AX":
                asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"ADD {tac_instruction.destination.value} := {tac_instruction.operand1.value} + {tac_instruction.operand2.value} -> ... MOV {dest_asm}, AX")
        return asm_lines

    def _translate_sub(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC SUB: dest := op1 - op2"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None,
                    tac_instruction.operand2, tac_instruction.operand2.value is not None]):
            self.logger.error(f"SUB TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed SUB TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand2.value), tac_instruction.opcode)

        asm_lines = []
        if dest_asm.upper() == op1_asm.upper():
            asm_lines.append(f"SUB {dest_asm}, {op2_asm}")
        else:
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
            asm_lines.append(f"SUB AX, {op2_asm}")
            if dest_asm.upper() != "AX":
                asm_lines.append(f"MOV {dest_asm}, AX")
        
        self.logger.debug(f"SUB {tac_instruction.destination.value} := {tac_instruction.operand1.value} - {tac_instruction.operand2.value} -> Generated SUB sequence, result in {dest_asm}")
        return asm_lines

    def _translate_mul(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC MUL: dest := op1 * op2 (signed multiplication)"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None,
                    tac_instruction.operand2, tac_instruction.operand2.value is not None]):
            self.logger.error(f"MUL TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed MUL TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand2.value), tac_instruction.opcode)

        asm_lines = []
        if op1_asm.upper() != "AX":
            asm_lines.append(f"MOV AX, {op1_asm}")
        
        multiplier_reg_or_mem = "BX" # Default for op2 if it needs to be moved
        
        is_op2_imm = self.asm_generator.is_immediate(op2_asm)

        if op2_asm.upper() == "AX": # op1 was moved to AX, op2 is also AX. Move op2 to BX.
            asm_lines.append(f"MOV {multiplier_reg_or_mem}, AX") 
            asm_lines.append(f"IMUL {multiplier_reg_or_mem}")
        elif self.asm_generator.is_register(op2_asm) or op2_asm.startswith("["): # op2 is register (not AX) or memory
            asm_lines.append(f"IMUL {op2_asm}")
        elif is_op2_imm: # op2 is immediate, move to register first
            asm_lines.append(f"MOV {multiplier_reg_or_mem}, {op2_asm}")
            asm_lines.append(f"IMUL {multiplier_reg_or_mem}")
        else:
            self.logger.error(f"MUL: Multiplier {op2_asm} is not a recognized register, memory, or immediate.")
            return [f"; ERROR: Multiplier {op2_asm} cannot be used directly with IMUL."]
        
        # Result of 16-bit IMUL reg/mem is in DX:AX. Low word in AX.
        if dest_asm.upper() != "AX":
            asm_lines.append(f"MOV {dest_asm}, AX")

        self.logger.debug(f"MUL {tac_instruction.destination.value} * {tac_instruction.operand1.value} * {tac_instruction.operand2.value} -> IMUL, result in AX to {dest_asm}")
        return asm_lines

    def _translate_div_or_rem(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction, is_div: bool) -> List[str]:
        """Helper for DIV and REM translation (signed IDIV)"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None,
                    tac_instruction.operand2, tac_instruction.operand2.value is not None]):
            op_name = "DIV" if is_div else "REM"
            self.logger.error(f"{op_name} TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed {op_name} TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand2.value), tac_instruction.opcode)
        asm_lines = []

        if op1_asm.upper() != "AX":
            asm_lines.append(f"MOV AX, {op1_asm}")
        
        asm_lines.append("CWD") # Sign-extend AX into DX for IDIV

        divisor_for_idiv = "BX" # Default register to move divisor into

        if self.asm_generator.is_register(op2_asm):
            if op2_asm.upper() == "AX": 
                asm_lines.append(f"MOV {divisor_for_idiv}, AX") # op2 was AX, op1 in AX, so move op2's val
            else: # op2 is register other than AX
                divisor_for_idiv = op2_asm
        elif self.asm_generator.is_immediate(op2_asm) or op2_asm.startswith("["): # op2 is memory or immediate
            asm_lines.append(f"MOV {divisor_for_idiv}, {op2_asm}")
        else:
            op_name = "DIV" if is_div else "REM"
            self.logger.error(f"{op_name}: Divisor {op2_asm} is not recognized.")
            return [f"; ERROR: Divisor {op2_asm} cannot be used for {op_name}."]
        
        asm_lines.append(f"IDIV {divisor_for_idiv}")
        
        result_reg = "AX" if is_div else "DX" # DIV quotient in AX, REM remainder in DX
        if dest_asm.upper() != result_reg:
            asm_lines.append(f"MOV {dest_asm}, {result_reg}")

        self.logger.debug(f"Translated {tac_instruction.opcode.name} {tac_instruction} -> {asm_lines}")    
        return asm_lines

    def _translate_div(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._translate_div_or_rem(tac_instruction, is_div=True)

    def _translate_rem(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._translate_div_or_rem(tac_instruction, is_div=False)

    def _translate_uminus(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC UMINUS: dest := -op1"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None]):
            self.logger.error(f"UMINUS TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed UMINUS TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        asm_lines = []

        if dest_asm.upper() == op1_asm.upper(): 
            asm_lines.append(f"NEG {dest_asm}")
        else: 
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
            else: # op1_asm is AX
                pass # Value already in AX
            asm_lines.append(f"NEG AX")
            if dest_asm.upper() != "AX":
                asm_lines.append(f"MOV {dest_asm}, AX")
        
        self.logger.debug(f"Translated UMINUS {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_not_op(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC NOT_OP: dest := not op1 (bitwise NOT)"""
        if not all([tac_instruction.destination, tac_instruction.destination.value is not None,
                    tac_instruction.operand1, tac_instruction.operand1.value is not None]):
            self.logger.error(f"NOT_OP TAC at line {tac_instruction.line_number} is missing operand values.")
            return [f"; ERROR: Malformed NOT_OP TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(str(tac_instruction.destination.value), tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
        asm_lines = []

        if dest_asm.upper() == op1_asm.upper():
            asm_lines.append(f"NOT {dest_asm}")
        else:
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
            else: # op1_asm is AX
                pass
            asm_lines.append(f"NOT AX")
            if dest_asm.upper() != "AX":
                asm_lines.append(f"MOV {dest_asm}, AX")
            
        self.logger.debug(f"Translated NOT_OP {tac_instruction} -> {asm_lines}")
        return asm_lines