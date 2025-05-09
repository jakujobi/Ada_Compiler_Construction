# src/jakadac/modules/asm_gen/instruction_translators/asm_im_procedure_translators.py

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator # For type hinting current_procedure_context
    from ...SymTable import Symbol # For type hinting active_procedure_symbol
    # ASMOperandFormatter is available via self.formatter

from ..tac_instruction import ParsedTACInstruction, TACOpcode

class ProcedureTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_program_start(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROGRAM_START: Marks the beginning of the main user procedure."""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        proc_name_operand = tac_instruction.operand1 
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROGRAM_START TAC at line {tac_instruction.line_number} is missing procedure name in operand1.")
            return [f"; ERROR: Malformed PROGRAM_START TAC at line {tac_instruction.line_number}"]
        
        proc_name = str(proc_name_operand.value)
        proc_entry = active_proc_ctx # ASMGenerator should have set this to the current proc being translated
        
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.warning(f"PROGRAM_START for '{proc_name}', but current_procedure_context is '{proc_entry.name if proc_entry else 'None'}'. Attempting direct lookup.")
            proc_entry = self.symbol_table.get_procedure_definition(proc_name)
            if not proc_entry:
                 self.logger.error(f"SymbolTableEntry for main procedure '{proc_name}' not found via get_procedure_definition for PROGRAM_START.")
                 return [f"; ERROR: SymbolTableEntry for main procedure '{proc_name}' not found."]
        
        asm_lines.append(f"{proc_name} PROC NEAR")
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = proc_entry.local_size if proc_entry and proc_entry.local_size is not None else 0
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROGRAM_START {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROGRAM_START {proc_name}: No local variable space allocated (size 0).")
            
        return asm_lines

    def _translate_proc_begin(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_BEGIN: Marks the beginning of a sub-procedure."""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        proc_name_operand = tac_instruction.operand1 
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROC_BEGIN TAC at line {tac_instruction.line_number} is missing procedure name in operand1.")
            return [f"; ERROR: Malformed PROC_BEGIN TAC at line {tac_instruction.line_number}"]

        proc_name = str(proc_name_operand.value)
        proc_entry = active_proc_ctx

        if not proc_entry or proc_entry.name != proc_name:
            self.logger.warning(f"PROC_BEGIN for '{proc_name}', but current_procedure_context is '{proc_entry.name if proc_entry else 'None'}'. Attempting direct lookup.")
            proc_entry = self.symbol_table.get_procedure_definition(proc_name)
            if not proc_entry:
                self.logger.error(f"SymbolTableEntry for procedure '{proc_name}' not found via get_procedure_definition for PROC_BEGIN.")
                return [f"; ERROR: SymbolTableEntry for procedure '{proc_name}' not found."]

        asm_lines.append(f"{proc_name} PROC NEAR")
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = proc_entry.local_size if proc_entry and proc_entry.local_size is not None else 0
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROC_BEGIN {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROC_BEGIN {proc_name}: No local variable space allocated (size 0).")
        return asm_lines

    def _translate_proc_end(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_END: Marks the end of a procedure."""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        proc_name_operand = tac_instruction.operand1 
        active_proc_ctx = self.asm_generator.current_procedure_context
        
        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROC_END TAC at line {tac_instruction.line_number} is missing procedure name in operand1.")
            return [f"; ERROR: Malformed PROC_END TAC at line {tac_instruction.line_number}"]
        
        proc_name = str(proc_name_operand.value)
        proc_entry = active_proc_ctx
        
        local_var_size_to_restore = 0
        if proc_entry and proc_entry.name == proc_name:
            local_var_size_to_restore = proc_entry.local_size if proc_entry.local_size is not None else 0
        else:
            self.logger.warning(f"PROC_END for '{proc_name}', context mismatch ('{proc_entry.name if proc_entry else 'None'}'). Looking up local_size.")
            looked_up_entry = self.symbol_table.get_procedure_definition(proc_name)
            if looked_up_entry:
                local_var_size_to_restore = looked_up_entry.local_size if looked_up_entry.local_size is not None else 0

        if local_var_size_to_restore > 0:
            asm_lines.append(f"MOV SP, BP  ; Restore SP, deallocating locals") 
        
        asm_lines.append(f"POP BP")      
        asm_lines.append(f"{proc_name} ENDP")
        self.logger.debug(f"PROC_END {proc_name}: Generated stack cleanup (local size: {local_var_size_to_restore}) and ENDP.")
        return asm_lines

    def _translate_return(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC RETURN: op1 (optional return value for functions)"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        active_proc_ctx = self.asm_generator.current_procedure_context
        
        if tac_instruction.operand1 and tac_instruction.operand1.value is not None:
            op1_asm = self.formatter.format_operand(str(tac_instruction.operand1.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
            self.logger.debug(f"RETURN {tac_instruction.operand1.value}: Value placed in AX.")
        else:
            self.logger.debug(f"RETURN (procedure return, no value in AX)")

        # Stack frame cleanup (MOV SP,BP; POP BP) is by PROC_END.
        asm_lines.append(f"RET")
        return asm_lines

    def _translate_call(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC CALL: proc_label (op1), num_params (op2), Optional: dest (return_dest_operand)"""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        proc_label_operand = tac_instruction.operand1 
        num_params_operand = tac_instruction.operand2 
        return_dest_operand = tac_instruction.destination
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not proc_label_operand or proc_label_operand.value is None:
            self.logger.error(f"CALL TAC at line {tac_instruction.line_number} is missing procedure label.")
            return [f"; ERROR: Malformed CALL TAC (missing label) at line {tac_instruction.line_number}"]

        proc_label_asm = self.formatter.format_operand(str(proc_label_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        asm_lines.append(f"CALL {proc_label_asm}")

        num_params = 0
        if num_params_operand and num_params_operand.value is not None:
            try:
                num_params = int(str(num_params_operand.value))
            except ValueError:
                self.logger.error(f"CALL TAC: num_params '{num_params_operand.value}' is not a valid integer.")
        
        if num_params > 0:
            stack_cleanup_bytes = num_params * 2 
            asm_lines.append(f"ADD SP, {stack_cleanup_bytes}  ; Clean up {num_params} parameter(s) from stack")

        if return_dest_operand and return_dest_operand.value is not None:
            dest_asm = self.formatter.format_operand(str(return_dest_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
            if dest_asm.upper() != "AX": 
                 asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"CALL to {proc_label_asm}: {num_params} params, result to {dest_asm}")
        else:
            self.logger.debug(f"CALL to {proc_label_asm}: {num_params} params, no return value assigned.")
        
        return asm_lines

    def _translate_push(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates PUSH/PARAM: Pushes an operand onto the stack."""
        asm_lines = [f"; TAC: {tac_instruction.raw_line.strip()}"]
        param_operand = tac_instruction.operand1 
        active_proc_ctx = self.asm_generator.current_procedure_context

        if not param_operand or param_operand.value is None:
            op_name = tac_instruction.opcode.name
            self.logger.error(f"{op_name} TAC at line {tac_instruction.line_number} is missing operand or operand value.")
            return [f"; ERROR: Malformed {op_name} TAC at line {tac_instruction.line_number}"]

        param_asm = self.formatter.format_operand(str(param_operand.value), tac_instruction.opcode, active_procedure_symbol=active_proc_ctx)
        
        if param_operand.is_address_of:
            if param_asm.startswith("["): 
                asm_lines.append(f"LEA AX, {param_asm}    ; Load address of stack variable/param")
                asm_lines.append(f"PUSH AX")
            else: 
                asm_lines.append(f"PUSH OFFSET {param_asm} ; Push address of global variable") 
        else: 
            asm_lines.append(f"PUSH {param_asm}")
        
        self.logger.debug(f"Translated {tac_instruction.opcode.name} for operand '{param_operand.value}' -> PUSH {param_asm} (is_addr: {param_operand.is_address_of})")
        return asm_lines

    def _translate_param(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._translate_push(tac_instruction)