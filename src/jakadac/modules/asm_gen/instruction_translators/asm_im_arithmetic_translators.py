# src/jakadac/modules/asm_gen/instruction_translators/asm_im_arithmetic_translators.py

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator
    from ...Logger import Logger
    from ...SymTable import SymbolTable # Added for self.symbol_table hint

from ..tac_instruction import ParsedTACInstruction, TACOpcode

class ArithmeticTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_add(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translate TAC ADD (dest = op1 + op2) to 8086 assembly.
        Handles dereferencing for pass-by-reference parameters.
        TAC Format: (ADD, dest, op1, op2)
        """
        asm = []
        dest = tac_instruction.destination
        op1 = tac_instruction.operand1
        op2 = tac_instruction.operand2

        if not all([dest, op1, op2]):
            self.logger.error(f"Invalid ADD TAC: Missing operands/destination. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid ADD TAC: {tac_instruction.raw_line}"]

        dest_asm = self.formatter.format_operand(str(dest), tac_instruction.opcode)
        op1_asm = self.formatter.format_operand(str(op1), tac_instruction.opcode)
        op2_asm = self.formatter.format_operand(str(op2), tac_instruction.opcode)

        is_dest_ref = self._is_param_address(dest_asm)
        is_op1_ref = self._is_param_address(op1_asm)
        is_op2_ref = self._is_param_address(op2_asm)

        asm.append(f"; TAC: {dest} = {op1} + {op2}")

        # Load op1 into AX (dereference if needed)
        if is_op1_ref:
            asm.append(f" mov bx, {op1_asm} ; Load address of op1")
            asm.append(f" mov ax, [bx]      ; Dereference op1 into AX")
        else:
            asm.append(f" mov ax, {op1_asm}    ; Load op1 into AX")

        # Load op2 into BX (dereference if needed) or determine if direct use
        was_op2_loaded_to_bx = False
        if is_op2_ref:
            asm.append(f" mov cx, {op2_asm} ; Load address of op2") # Use CX
            asm.append(f" mov bx, [cx]      ; Dereference op2 into BX")
            was_op2_loaded_to_bx = True
        elif not self.generator.is_immediate(op2_asm) and not self.generator.is_register(op2_asm): # op2 is memory
             asm.append(f" mov bx, {op2_asm}    ; Load op2 into BX")
             was_op2_loaded_to_bx = True
        # else: op2 is immediate or register, use op2_asm directly

        # Perform addition
        if was_op2_loaded_to_bx:
            asm.append(f" add ax, bx        ; Add op2 (from BX) to op1 (in AX)") # Use BX
        else:
            asm.append(f" add ax, {op2_asm}    ; Add op2 to op1 (in AX)") # Use op2_asm (imm/reg)

        # Store result from AX into destination (dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store result into dereferenced dest")
        else:
            asm.append(f" mov {dest_asm}, ax   ; Store result into destination")

        return asm

    def _translate_sub(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translate TAC SUB (dest = op1 - op2) to 8086 assembly.
        Handles dereferencing for pass-by-reference parameters.
        TAC Format: (SUB, dest, op1, op2)
        """
        asm = []
        dest = tac_instruction.destination
        op1 = tac_instruction.operand1
        op2 = tac_instruction.operand2

        if not all([dest, op1, op2]):
            self.logger.error(f"Invalid SUB TAC: Missing operands/destination. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid SUB TAC: {tac_instruction.raw_line}"]

        dest_asm = self.formatter.format_operand(str(dest), tac_instruction.opcode)
        op1_asm = self.formatter.format_operand(str(op1), tac_instruction.opcode)
        op2_asm = self.formatter.format_operand(str(op2), tac_instruction.opcode)

        is_dest_ref = self._is_param_address(dest_asm)
        is_op1_ref = self._is_param_address(op1_asm)
        is_op2_ref = self._is_param_address(op2_asm)

        asm.append(f"; TAC: {dest} = {op1} - {op2}")

        # Load op1 into AX (dereference if needed)
        if is_op1_ref:
            asm.append(f" mov bx, {op1_asm} ; Load address of op1")
            asm.append(f" mov ax, [bx]      ; Dereference op1 into AX")
        else:
            asm.append(f" mov ax, {op1_asm}    ; Load op1 into AX")

        # Load op2 into BX (dereference if needed) or determine if direct use
        was_op2_loaded_to_bx = False
        if is_op2_ref:
            asm.append(f" mov cx, {op2_asm} ; Load address of op2")
            asm.append(f" mov bx, [cx]      ; Dereference op2 into BX")
            was_op2_loaded_to_bx = True
        elif not self.generator.is_immediate(op2_asm) and not self.generator.is_register(op2_asm): # op2 is memory
             asm.append(f" mov bx, {op2_asm}    ; Load op2 into BX")
             was_op2_loaded_to_bx = True
        # else: op2 is immediate or register, use op2_asm directly

        # Perform subtraction
        if was_op2_loaded_to_bx:
            asm.append(f" sub ax, bx        ; Subtract op2 (from BX) from op1 (in AX)") # Use BX
        else:
            asm.append(f" sub ax, {op2_asm}    ; Subtract op2 from op1 (in AX)") # Use op2_asm (imm/reg)

        # Store result from AX into destination (dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store result into dereferenced dest")
        else:
            asm.append(f" mov {dest_asm}, ax   ; Store result into destination")

        return asm

    def _translate_mul(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translate TAC MUL (dest = op1 * op2) to 8086 assembly using IMUL.
        Handles dereferencing for pass-by-reference parameters.
        Assumes 16-bit multiplication, result in AX.
        TAC Format: (MUL, dest, op1, op2)
        """
        asm = []
        dest = tac_instruction.destination
        op1 = tac_instruction.operand1
        op2 = tac_instruction.operand2

        if not all([dest, op1, op2]):
            self.logger.error(f"Invalid MUL TAC: Missing operands/destination. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid MUL TAC: {tac_instruction.raw_line}"]

        dest_asm = self.formatter.format_operand(str(dest), tac_instruction.opcode)
        op1_asm = self.formatter.format_operand(str(op1), tac_instruction.opcode)
        op2_asm = self.formatter.format_operand(str(op2), tac_instruction.opcode)

        is_dest_ref = self._is_param_address(dest_asm)
        is_op1_ref = self._is_param_address(op1_asm)
        is_op2_ref = self._is_param_address(op2_asm)

        asm.append(f"; TAC: {dest} = {op1} * {op2}")

        # Load op1 into AX (dereference if needed)
        if is_op1_ref:
            asm.append(f" mov bx, {op1_asm} ; Load address of op1")
            asm.append(f" mov ax, [bx]      ; Dereference op1 into AX")
        else:
            asm.append(f" mov ax, {op1_asm}    ; Load op1 into AX")

        # Load op2 into BX (dereference if needed)
        # IMUL operand can be register or memory, so we might not always need BX
        operand_for_imul = op2_asm # Default
        if is_op2_ref:
            asm.append(f" mov bx, {op2_asm} ; Load address of op2")
            operand_for_imul = "bx" # Use register containing address for potential dereference? NO, need value.
            asm.append(f" mov bx, [bx]      ; Dereference op2 into BX") # Now BX holds the value
            operand_for_imul = "bx"
        elif not self.generator.is_immediate(op2_asm) and not self.generator.is_register(op2_asm):
            # If op2 is memory, IMUL can handle it directly (IMUL memory_operand)
            operand_for_imul = op2_asm
        else:
            # If op2 is immediate or register, need to load into register first for IMUL reg
            asm.append(f" mov bx, {op2_asm}    ; Load op2 into BX for IMUL")
            operand_for_imul = "bx"

        # Perform multiplication (DX:AX = AX * operand_for_imul)
        asm.append(f" imul {operand_for_imul}     ; Multiply AX by op2")
        # Result (low 16 bits) is in AX

        # Store result from AX into destination (dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store result into dereferenced dest")
        else:
            asm.append(f" mov {dest_asm}, ax   ; Store result into destination")

        return asm

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
        """
        Translate TAC Unary Minus (dest = -op1) to 8086 assembly.
        Handles destination dereferencing.
        TAC Format: (=, dest, uminus, op1) ? Or custom opcode?
                    Assuming (UMINUS, dest, op1) for clarity.
        """
        # Assuming TAC format: (UMINUS, dest, op1)
        asm = []
        dest = tac_instruction.destination
        op1 = tac_instruction.operand1

        if not all([dest, op1]):
            self.logger.error(f"Invalid UMINUS TAC: Missing operands/destination. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid UMINUS TAC: {tac_instruction.raw_line}"]

        dest_asm = self.formatter.format_operand(str(dest), tac_instruction.opcode)
        op1_asm = self.formatter.format_operand(str(op1), tac_instruction.opcode)

        is_dest_ref = self._is_param_address(dest_asm)
        is_op1_ref = self._is_param_address(op1_asm)

        asm.append(f"; TAC: {dest} = - {op1}")

        # Load op1 into AX (dereference if needed)
        if is_op1_ref:
            asm.append(f" mov bx, {op1_asm} ; Load address of op1")
            asm.append(f" mov ax, [bx]      ; Dereference op1 into AX")
        else:
            asm.append(f" mov ax, {op1_asm}    ; Load op1 into AX")

        # Negate AX
        asm.append(f" neg ax            ; Negate value in AX")

        # Store result from AX into destination (dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store result into dereferenced dest")
        else:
            asm.append(f" mov {dest_asm}, ax   ; Store result into destination")

        return asm

    def _translate_not_op(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translate TAC Logical NOT (dest = not op1) to 8086 assembly.
        Handles destination dereferencing.
        TAC Format: (=, dest, not, op1) ? Or custom opcode?
                    Assuming (NOT_OP, dest, op1) for clarity.
        """
        # Assuming TAC format: (NOT_OP, dest, op1)
        asm = []
        dest = tac_instruction.destination
        op1 = tac_instruction.operand1

        if not all([dest, op1]):
            self.logger.error(f"Invalid NOT_OP TAC: Missing operands/destination. Instruction: {tac_instruction}")
            return [f"; ERROR: Invalid NOT_OP TAC: {tac_instruction.raw_line}"]

        dest_asm = self.formatter.format_operand(str(dest), tac_instruction.opcode)
        op1_asm = self.formatter.format_operand(str(op1), tac_instruction.opcode)

        is_dest_ref = self._is_param_address(dest_asm)
        is_op1_ref = self._is_param_address(op1_asm)

        asm.append(f"; TAC: {dest} = not {op1}")

        # Load op1 into AX (dereference if needed)
        if is_op1_ref:
            asm.append(f" mov bx, {op1_asm} ; Load address of op1")
            asm.append(f" mov ax, [bx]      ; Dereference op1 into AX")
        else:
            asm.append(f" mov ax, {op1_asm}    ; Load op1 into AX")

        # Apply NOT to AX
        asm.append(f" not ax            ; Logical NOT on value in AX")

        # Store result from AX into destination (dereference if needed)
        if is_dest_ref:
            asm.append(f" mov bx, {dest_asm} ; Load address of reference param dest")
            asm.append(f" mov [bx], ax      ; Store result into dereferenced dest")
        else:
            asm.append(f" mov {dest_asm}, ax   ; Store result into destination")

        return asm