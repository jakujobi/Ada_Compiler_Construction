# src/jakadac/modules/asm_gen/instruction_translators/asm_im_arithmetic_translators.py

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator
    from ...Logger import Logger
    from ...SymTable import SymbolTable # Added for self.symbol_table hint
    from ..asm_operand_formatter import ASMOperandFormatter

from ..tac_instruction import ParsedTACInstruction, TACOpcode

class ArithmeticTranslators:
    # self will be an instance of ASMInstructionMapper

    def _is_param_address(self, operand_asm: str) -> bool:
        """Checks if an operand string looks like a parameter address (e.g., [BP+offset])."""
        return operand_asm.startswith("[BP+") and operand_asm.endswith("]")

    def _translate_add(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates ADD: dest = op1 + op2"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, op1_operand, op2_operand, dest_operand.value is not None, op1_operand.value is not None, op2_operand.value is not None]):
            self.logger.error(f"ADD TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed ADD TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        asm_lines.append(f" mov ax, {op1_asm}    ; Load op1 into AX")
        asm_lines.append(f" mov bx, {op2_asm}    ; Load op2 into BX")
        asm_lines.append(f" add ax, bx        ; Add op2 (from BX) to op1 (in AX)")
        asm_lines.append(f" mov {dest_asm}, ax   ; Store result into destination")
        
        self.logger.debug(f"Translated ADD {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_sub(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates SUB: dest = op1 - op2"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, op1_operand, op2_operand, dest_operand.value is not None, op1_operand.value is not None, op2_operand.value is not None]):
            self.logger.error(f"SUB TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed SUB TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        asm_lines.append(f" mov ax, {op1_asm}    ; Load op1 into AX")
        asm_lines.append(f" mov bx, {op2_asm}    ; Load op2 into BX")
        asm_lines.append(f" sub ax, bx        ; Subtract op2 (from BX) from op1 (in AX)")
        asm_lines.append(f" mov {dest_asm}, ax   ; Store result into destination")
        
        self.logger.debug(f"Translated SUB {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_mul(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates MUL: dest = op1 * op2"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, op1_operand, op2_operand, dest_operand.value is not None, op1_operand.value is not None, op2_operand.value is not None]):
            self.logger.error(f"MUL TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed MUL TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        asm_lines.append(f" mov ax, {op1_asm}    ; Load op1 into AX")
        if op2_asm.startswith("[") or not op2_asm.isdigit(): # Memory or register (heuristic)
            asm_lines.append(f" imul {op2_asm}     ; Multiply AX by op2")
        else: # Immediate value
            asm_lines.append(f" mov bx, {op2_asm}")
            asm_lines.append(f" imul bx         ; Multiply AX by op2 in BX")
        
        asm_lines.append(f" mov {dest_asm}, ax   ; Store result (lower word) into destination")
        
        self.logger.debug(f"Translated MUL {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_div(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates DIV: dest = op1 / op2"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, op1_operand, op2_operand, dest_operand.value is not None, op1_operand.value is not None, op2_operand.value is not None]):
            self.logger.error(f"DIV TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed DIV TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        
        asm_lines.append(f" mov ax, {op1_asm}    ; Load dividend (op1) into AX")
        asm_lines.append(f" cwd               ; Sign-extend AX into DX (DX:AX)")
        if op2_asm.startswith("[") or not op2_asm.isdigit(): # Memory or register
            asm_lines.append(f" idiv {op2_asm}     ; Divide DX:AX by op2")
        else: # Immediate value
            asm_lines.append(f" mov bx, {op2_asm}")
            asm_lines.append(f" idiv bx         ; Divide DX:AX by op2 in BX")

        asm_lines.append(f" mov {dest_asm}, ax   ; Store quotient into destination")
        
        self.logger.debug(f"Translated DIV {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_neg(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # UMINUS
        """Translates NEG (Unary Minus): dest = -op1"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not dest_operand or dest_operand.value is None or not op1_operand or op1_operand.value is None:
            self.logger.error(f"NEG/UMINUS TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed NEG/UMINUS TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        if dest_asm == op1_asm and not op1_asm.isdigit():
            asm_lines.append(f" neg {op1_asm}")
        else:
            asm_lines.append(f" mov ax, {op1_asm}")
            asm_lines.append(f" neg ax")
            asm_lines.append(f" mov {dest_asm}, ax")

        self.logger.debug(f"Translated NEG/UMINUS {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_not_op(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates NOT_OP (Logical NOT): dest = NOT op1"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not dest_operand or dest_operand.value is None or not op1_operand or op1_operand.value is None:
            self.logger.error(f"NOT_OP TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed NOT_OP TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)

        if dest_asm == op1_asm and not op1_asm.isdigit():
            asm_lines.append(f" not {op1_asm}")
        else:
            asm_lines.append(f" mov ax, {op1_asm}")
            asm_lines.append(f" not ax")
            asm_lines.append(f" mov {dest_asm}, ax")
            
        self.logger.debug(f"Translated NOT_OP {tac_instruction} -> {asm_lines}")
        return asm_lines

    # Relational ops (EQ, NE, LT, GT, LE, GE) use a different pattern
    # They typically set flags based on CMP and then might use SETcc or conditional jumps.
    # If they assign a boolean 0/1 to a variable, format_operand would be needed for the destination.
    # Their operands for CMP also need formatting.

    def _translate_generic_relational_op(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction, jump_if_true: str, jump_if_false: str) -> List[str]:
        """Helper for relational TAC opcodes that result in conditional jumps."""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        label_true = tac_instruction.destination # For Jumps, destination is the label

        active_proc_ctx = self.asm_generator.current_procedure_context

        if not op1_operand or op1_operand.value is None or \
           not op2_operand or op2_operand.value is None or \
           not label_true or label_true.value is None:
            self.logger.error(f"Relational JUMP TAC at line {tac_instruction.line_number} is missing operands or label.")
            return [f"; ERROR: Malformed Relational JUMP TAC at line {tac_instruction.line_number}"]

        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        label_asm = str(label_true.value) # Labels are used directly

        asm_lines.append(f" mov ax, {op1_asm}")
        asm_lines.append(f" cmp ax, {op2_asm}")
        asm_lines.append(f" {jump_if_true} {label_asm}")
        # Implicit fall-through means the false condition, or use jump_if_false if needed for structured IF/ELSE

        self.logger.debug(f"Translated Relational JUMP {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_eq(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JEQ
        return self._translate_generic_relational_op(tac_instruction, "JE", "JNE")

    def _translate_ne(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JNE
        return self._translate_generic_relational_op(tac_instruction, "JNE", "JE")

    def _translate_lt(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JLT
        return self._translate_generic_relational_op(tac_instruction, "JL", "JGE") # Signed comparison

    def _translate_gt(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JGT
        return self._translate_generic_relational_op(tac_instruction, "JG", "JLE") # Signed comparison

    def _translate_le(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JLE
        return self._translate_generic_relational_op(tac_instruction, "JLE", "JG") # Signed comparison

    def _translate_ge(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]: # JGE
        return self._translate_generic_relational_op(tac_instruction, "JGE", "JL") # Signed comparison

    def _translate_rem(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates REM: dest = op1 REM op2 (remainder of division)"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        dest_operand = tac_instruction.destination
        op1_operand = tac_instruction.operand1
        op2_operand = tac_instruction.operand2
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not all([dest_operand, op1_operand, op2_operand, 
                    dest_operand.value is not None, op1_operand.value is not None, op2_operand.value is not None]):
            self.logger.error(f"REM TAC at line {tac_instruction.line_number} is missing one or more operands/values.")
            return [f"; ERROR: Malformed REM TAC at line {tac_instruction.line_number}"]

        dest_asm = self.formatter.format_operand(str(dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op1_asm = self.formatter.format_operand(str(op1_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        op2_asm = self.formatter.format_operand(str(op2_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        
        asm_lines.append(f" mov ax, {op1_asm}    ; Load dividend (op1) into AX")
        asm_lines.append(f" cwd               ; Sign-extend AX into DX (DX:AX)")
        
        # Divisor (op2) for IDIV can be reg or mem. If immediate, load to reg first.
        if op2_asm.startswith("[") or not op2_asm.isdigit(): # Memory or register
            asm_lines.append(f" idiv {op2_asm}     ; Divide DX:AX by op2")
        else: # Immediate value
            asm_lines.append(f" mov bx, {op2_asm}")
            asm_lines.append(f" idiv bx         ; Divide DX:AX by op2 in BX")

        # Remainder is in DX after IDIV
        asm_lines.append(f" mov {dest_asm}, dx   ; Store remainder into destination")
        
        self.logger.debug(f"Translated REM {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_mod(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates MOD: dest = op1 MOD op2. For many integer contexts, this is the same as REM."""
        # Note: True mathematical MOD might differ from REM for negative numbers based on language spec.
        # For simplicity here, treating MOD as REM.
        self.logger.debug(f"MOD TAC at line {tac_instruction.line_number} is being handled like REM.")
        return self._translate_rem(tac_instruction)

    # Boolean results (e.g. dest = op1 < op2) would be different
    # They would use CMP, then SETcc AL, then MOVZX AX, AL, then MOV dest, AX

    # Placeholder for other arithmetic/boolean ops (MOD, AND, OR etc. if they assign results)
    # For logical AND/OR on booleans (0 or 1), it's more complex than bitwise AND/OR.
    # It often involves short-circuiting or converting to 0/non-0 and then standard bitwise ops.
    # If TAC ensures operands are 0/1, then bitwise AND/OR on AX/BX can work.