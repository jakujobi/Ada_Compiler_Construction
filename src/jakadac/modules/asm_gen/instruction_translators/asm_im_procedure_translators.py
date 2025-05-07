# src/jakadac/modules/asm_gen/asm_im_procedure_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .asm_generator import ASMGenerator
    from ..SymTable import Symbol, SymbolTable
    from ..Logger import Logger

from .tac_instruction import ParsedTACInstruction, TACOpcode

class ProcedureTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_program_start(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROGRAM_START: Marks the beginning of the main user procedure."""
        proc_name_operand = tac_instruction.destination 
        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROGRAM_START TAC at line {tac_instruction.line_number} is missing procedure name.")
            return [f"; ERROR: Malformed PROGRAM_START TAC at line {tac_instruction.line_number}"]
        
        proc_name = str(proc_name_operand.value)
        proc_entry = self.asm_generator.current_procedure_context # Set by ASMGenerator before calling translate for this proc
        
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.warning(f"PROGRAM_START for '{proc_name}', but current_procedure_context is for '{proc_entry.name if proc_entry else 'None'}'. Re-checking SymbolTable.")
            # This implies ASMGenerator might not have set current_procedure_context correctly before this.
            # However, ASMGenerator should set it based on this very PROGRAM_START or PROC_BEGIN instruction.
            proc_entry_lookup = self.symbol_table.lookup_globally(proc_name) 
            if not proc_entry_lookup:
                 self.logger.error(f"SymbolTableEntry for main procedure '{proc_name}' not found for PROGRAM_START.")
                 return [f"; ERROR: SymbolTableEntry for main procedure '{proc_name}' not found."]
            proc_entry = proc_entry_lookup # Use the looked up entry
            self.asm_generator.current_procedure_context = proc_entry # Correct the context if it was wrong
        
        asm_lines = [f"{proc_name} PROC NEAR"]
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_size', 0) 
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROGRAM_START {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROGRAM_START {proc_name}: No local variable space allocated (size 0).")
            
        return asm_lines

    def _translate_proc_begin(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_BEGIN: Marks the beginning of a sub-procedure."""
        proc_name_operand = tac_instruction.destination
        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROC_BEGIN TAC at line {tac_instruction.line_number} is missing procedure name.")
            return [f"; ERROR: Malformed PROC_BEGIN TAC at line {tac_instruction.line_number}"]

        proc_name = str(proc_name_operand.value)
        proc_entry = self.asm_generator.current_procedure_context
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.warning(f"PROC_BEGIN for '{proc_name}', but current_procedure_context is for '{proc_entry.name if proc_entry else 'None'}'. Re-checking SymbolTable.")
            proc_entry_lookup = self.symbol_table.lookup_globally(proc_name)
            if not proc_entry_lookup:
                self.logger.error(f"SymbolTableEntry for procedure '{proc_name}' not found for PROC_BEGIN.")
                return [f"; ERROR: SymbolTableEntry for procedure '{proc_name}' not found."]
            proc_entry = proc_entry_lookup
            self.asm_generator.current_procedure_context = proc_entry


        asm_lines = [f"{proc_name} PROC NEAR"]
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_size', 0)
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROC_BEGIN {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROC_BEGIN {proc_name}: No local variable space allocated (size 0).")
        return asm_lines

    def _translate_proc_end(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_END: Marks the end of a procedure."""
        proc_name_operand = tac_instruction.destination
        if not proc_name_operand or proc_name_operand.value is None:
            self.logger.error(f"PROC_END TAC at line {tac_instruction.line_number} is missing procedure name.")
            return [f"; ERROR: Malformed PROC_END TAC at line {tac_instruction.line_number}"]
        
        proc_name = str(proc_name_operand.value)
        # proc_entry is needed if local_size might be > 0, should be current_procedure_context
        proc_entry = self.asm_generator.current_procedure_context 
        
        asm_lines = []
        if proc_entry and proc_entry.name == proc_name and getattr(proc_entry, 'local_size', 0) > 0:
             asm_lines.append(f"MOV SP, BP") 
        elif not proc_entry or proc_entry.name != proc_name:
             # If context is lost or mismatched, we can't reliably know local_size.
             # Lookup to see if we can find it. This implies context wasn't preserved by ASMGenerator.
             looked_up_entry = self.symbol_table.lookup_globally(proc_name)
             if looked_up_entry and getattr(looked_up_entry, 'local_size', 0) > 0:
                 asm_lines.append(f"MOV SP, BP")
                 self.logger.warning(f"PROC_END {proc_name}: Context mismatch but found entry; assuming MOV SP,BP based on looked up local_size.")
             else:
                self.logger.warning(f"PROC_END {proc_name}: Context mismatch/no entry, cannot determine if MOV SP,BP needed for locals.")
        
        asm_lines.append(f"POP BP")      
        asm_lines.append(f"{proc_name} ENDP")
        self.logger.debug(f"PROC_END {proc_name}: Generated stack cleanup and ENDP.")
        return asm_lines

    def _translate_return(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC RETURN: op1 (optional return value for functions)"""
        asm_lines = []
        
        if tac_instruction.operand1 and tac_instruction.operand1.value is not None:
            op1_asm = self.asm_generator.get_operand_asm(str(tac_instruction.operand1.value), tac_instruction.opcode)
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
                self.logger.debug(f"RETURN {tac_instruction.operand1.value} -> MOV AX, {op1_asm}")
            else:
                self.logger.debug(f"RETURN {tac_instruction.operand1.value}: Value already in AX.")
        else:
            self.logger.debug(f"RETURN (procedure return, no value)")

        # Important: Stack frame cleanup (MOV SP, BP; POP BP) is done by PROC_END.
        # RETURN TAC itself should only generate RET.
        asm_lines.append(f"RET")
        return asm_lines

    def _translate_call(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC CALL: proc_label (op1), num_params (op2), Optional: dest (return_dest_operand)"""
        asm_lines = []
        proc_label_operand = tac_instruction.operand1 
        num_params_operand = tac_instruction.operand2 
        return_dest_operand = tac_instruction.destination

        if not proc_label_operand or proc_label_operand.value is None:
            self.logger.error(f"CALL TAC at line {tac_instruction.line_number} is missing procedure label.")
            return [f"; ERROR: Malformed CALL TAC (missing label) at line {tac_instruction.line_number}"]

        proc_label_asm = str(proc_label_operand.value)
        asm_lines.append(f"CALL {proc_label_asm}")

        num_params = 0
        if num_params_operand and num_params_operand.value is not None:
            try:
                num_params = int(str(num_params_operand.value)) # Ensure value is string before int
            except ValueError:
                self.logger.error(f"CALL TAC: num_params '{num_params_operand.value}' is not a valid integer.")
                return [f"; ERROR: CALL TAC with invalid num_params '{num_params_operand.value}'"]
        
        if num_params > 0:
            stack_cleanup_bytes = num_params * 2 
            asm_lines.append(f"ADD SP, {stack_cleanup_bytes}")

        if return_dest_operand and return_dest_operand.value is not None:
            dest_asm = self.asm_generator.get_operand_asm(str(return_dest_operand.value), tac_instruction.opcode)
            if dest_asm.upper() != "AX": 
                 asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"CALL to {proc_label_asm} with {num_params} params, returning to {dest_asm}")
        else:
            self.logger.debug(f"CALL to {proc_label_asm} with {num_params} params, no return value assigned.")
        
        self.logger.debug(f"Translated CALL {tac_instruction} -> {asm_lines}")    
        return asm_lines

    def _translate_push(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        param_operand = tac_instruction.operand1 
        asm_lines = []

        if not param_operand or param_operand.value is None: # param_operand itself can be None, or its value
            self.logger.error(f"PUSH TAC at line {tac_instruction.line_number} is missing operand or operand value.")
            return [f"; ERROR: Malformed PUSH TAC at line {tac_instruction.line_number}"]

        param_asm = self.asm_generator.get_operand_asm(str(param_operand.value), tac_instruction.opcode)
        
        if param_operand.is_address_of:
            if param_asm.startswith("["): 
                asm_lines.append(f"LEA AX, {param_asm}")
                asm_lines.append(f"PUSH AX")
                self.logger.debug(f"Translated PUSH @{param_operand.value} (local/param address via LEA) -> LEA AX, {param_asm}; PUSH AX")
            else: 
                asm_lines.append(f"PUSH OFFSET {param_asm}") 
                self.logger.debug(f"Translated PUSH @{param_operand.value} (global address via OFFSET) -> PUSH OFFSET {param_asm}")
        else: 
            asm_lines.append(f"PUSH {param_asm}")
            self.logger.debug(f"Translated PUSH {param_operand.value} (value) -> PUSH {param_asm}")
        
        return asm_lines

    def _translate_param(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        self.logger.debug(f"PARAM TAC at line {tac_instruction.line_number} is being handled like PUSH.")
        return self._translate_push(tac_instruction)