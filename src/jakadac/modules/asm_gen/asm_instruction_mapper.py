# src/jakadac/modules/asm_gen/asm_instruction_mapper.py

import sys
import os
from typing import TYPE_CHECKING, List

# Ensure the 'modules' directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..SymTable import SymbolTable, Symbol, EntryType
from ..Logger import logger
from .tac_instruction import ParsedTACInstruction, TACOpcode 
# from .asm_operand_formatter import ASMOperandFormatter # No longer directly used here, ASMGenerator handles it.

# Forward declaration for type hinting to avoid circular import
if TYPE_CHECKING:
    from .asm_generator import ASMGenerator # Only for type checking

class ASMInstructionMapper:
    def __init__(self, symbol_table: SymbolTable, logger: logger, asm_generator_instance: 'ASMGenerator'):
        self.symbol_table = symbol_table
        self.logger = logger
        self.asm_generator = asm_generator_instance # For calling get_operand_asm
        self.logger.debug("ASMInstructionMapper initialized.")

    def translate(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
        Translates a single TAC instruction to its corresponding ASM code lines.
        Dynamically dispatches to a _translate_<opcode> method.
        Returns a list of ASM instruction strings.
        """
        if tac_instruction.opcode is None:
            self.logger.error("TAC instruction has no opcode.")
            return [f"; ERROR: TAC instruction at line {tac_instruction.line_number} has no opcode."]

        opcode_value_str = ""
        log_opcode_repr = ""

        if isinstance(tac_instruction.opcode, TACOpcode):
            opcode_value_str = tac_instruction.opcode.value # Use .value for handler lookup (e.g., 'assign', 'add')
            log_opcode_repr = tac_instruction.opcode.name   # Use .name for logging (e.g., 'ASSIGN', 'ADD')
        elif isinstance(tac_instruction.opcode, str):
            opcode_value_str = tac_instruction.opcode.lower() # Normalize string opcode for handler lookup
            log_opcode_repr = tac_instruction.opcode         # Use the string itself for logging
        else:
            self.logger.error(f"Invalid opcode type: {type(tac_instruction.opcode)} for TAC: {tac_instruction}")
            return [f"; ERROR: Invalid opcode type at line {tac_instruction.line_number}."]

        handler_method_name = f"_translate_{opcode_value_str}"
        handler_method = getattr(self, handler_method_name, self._translate_unknown)
        
        self.logger.debug(f"Translating TAC Op: {log_opcode_repr}, Line: {tac_instruction.line_number} using {handler_method_name if handler_method != self._translate_unknown else 'unknown handler'}")
        
        asm_lines = handler_method(tac_instruction)
        
        # Ensure all handlers return a list, even if it's a list with one comment string
        if not isinstance(asm_lines, list):
            self.logger.warning(f"Handler {handler_method_name} for opcode {tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else tac_instruction.opcode} did not return a list. Returned: {asm_lines}. Wrapping in a list.")
            if asm_lines is None:
                return [f"; ERROR: Handler for {tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else tac_instruction.opcode} returned None"]
            return [str(asm_lines)] # Convert to string just in case, then wrap
            
        return asm_lines

    def _translate_unknown(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        self.logger.warning(f"No specific translator for TAC opcode: {tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else tac_instruction.opcode} at line {tac_instruction.line_number}")
        return [f"; UNHANDLED TAC Opcode: {tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else tac_instruction.opcode} (Operands: D:{tac_instruction.dest}, O1:{tac_instruction.op1}, O2:{tac_instruction.op2})"]

    # --- Specific TAC Opcode Translators ---

    def _translate_assign(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ASSIGN: dest := op1"""
        if tac_instruction.dest is None or tac_instruction.op1 is None:
            self.logger.error(f"ASSIGN TAC at line {tac_instruction.line_number} is missing destination or source operand.")
            return [f"; ERROR: Malformed ASSIGN TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(tac_instruction.dest, tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)

        # Standard 8086: MOV cannot move memory to memory directly.
        # Need to use a register (AX) as an intermediary.
        # Exception: if op1 is a literal, it can be moved directly to memory.
        
        asm_lines = []
        # Check if op1_asm is a direct numeric literal (or resolvable immediate)
        is_op1_literal = False
        try:
            int(op1_asm) # This is a simplistic check; get_operand_asm might return 'OFFSET _S0' etc.
            is_op1_literal = True 
        except ValueError:
            # Could also check if op1_asm is a known string offset label like 'OFFSET _S0', etc.
            # For now, only pure numbers are direct literals for this optimization.
            pass

        if dest_asm.startswith("[") and op1_asm.startswith("[") and not is_op1_literal:
            # Memory to Memory: MOV mem, mem (not allowed)
            asm_lines.append(f"MOV AX, {op1_asm}")
            asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"  ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV AX, {op1_asm}; MOV {dest_asm}, AX")
        elif dest_asm.startswith("[") and is_op1_literal:
            # Literal to Memory: MOV mem, literal (allowed)
            asm_lines.append(f"MOV WORD PTR {dest_asm}, {op1_asm}") # Assuming WORD for now, could be BYTE
            self.logger.debug(f"  ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV WORD PTR {dest_asm}, {op1_asm}")
        else:
            # Register to Memory, Memory to Register, Register to Register, Literal to Register
            asm_lines.append(f"MOV {dest_asm}, {op1_asm}")
            self.logger.debug(f"  ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV {dest_asm}, {op1_asm}")
            
        return asm_lines

    # Example for a binary operation (placeholder)
    def _translate_add(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ADD: dest := op1 + op2"""
        if not all([tac_instruction.dest, tac_instruction.op1, tac_instruction.op2]):
            self.logger.error(f"ADD TAC at line {tac_instruction.line_number} is missing operands.")
            return [f"; ERROR: Malformed ADD TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(tac_instruction.dest, tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(tac_instruction.op2, tac_instruction.opcode)

        asm_lines = []
        # Assuming dest is the same as op1 for 2-address form (ADD dest, src)
        # If TAC is strictly 3-address (dest, op1, op2) and dest can be different from op1:
        # MOV AX, op1_asm
        # ADD AX, op2_asm
        # MOV dest_asm, AX
        # For simplicity, let's assume op1 is the primary operand and also the destination if they are the same
        # or if dest_asm is different, result needs to be moved to dest_asm.

        if dest_asm == op1_asm:
            asm_lines.append(f"ADD {dest_asm}, {op2_asm}")
            self.logger.debug(f"  ADD {tac_instruction.dest} := {tac_instruction.op1} + {tac_instruction.op2} -> ADD {dest_asm}, {op2_asm}")
        else:
            asm_lines.append(f"MOV AX, {op1_asm}")
            asm_lines.append(f"ADD AX, {op2_asm}")
            asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"  ADD {tac_instruction.dest} := {tac_instruction.op1} + {tac_instruction.op2} -> MOV AX, {op1_asm}; ADD AX, {op2_asm}; MOV {dest_asm}, AX")
        return asm_lines

    def _translate_program_start(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROGRAM_START: Marks the beginning of the main user procedure."""
        proc_name = tac_instruction.dest
        if not proc_name:
            self.logger.error(f"PROGRAM_START TAC at line {tac_instruction.line_number} is missing procedure name (dest operand).")
            return [f"; ERROR: Malformed PROGRAM_START TAC at line {tac_instruction.line_number}"]

        # Proc entry should be set as current_procedure_context by ASMGenerator
        proc_entry = self.asm_generator.current_procedure_context
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.error(f"PROGRAM_START for '{proc_name}', but current_procedure_context is for '{proc_entry.name if proc_entry else 'None'}'. Mismatch!")
            # Attempt to look it up if context is wrong, though this indicates a logic flaw in ASMGenerator
            proc_entry = self.asm_generator.symbol_table.lookup_globally(proc_name)
            if not proc_entry:
                return [f"; ERROR: SymbolTableEntry for main procedure '{proc_name}' not found."]
        
        asm_lines = []
        asm_lines.append(f"{proc_name} PROC") # Using NEAR by default
        asm_lines.append(f"    PUSH BP")
        asm_lines.append(f"    MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_vars_total_size', 0)
        if local_var_size > 0:
            asm_lines.append(f"    SUB SP, {local_var_size}")
            self.logger.debug(f"  PROGRAM_START {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"  PROGRAM_START {proc_name}: No local variable space allocated (size 0).")
            
        return asm_lines

    def _translate_proc_begin(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_BEGIN: Marks the beginning of a sub-procedure."""
        proc_name = tac_instruction.dest
        if not proc_name:
            self.logger.error(f"PROC_BEGIN TAC at line {tac_instruction.line_number} is missing procedure name (dest operand).")
            return [f"; ERROR: Malformed PROC_BEGIN TAC at line {tac_instruction.line_number}"]

        proc_entry = self.asm_generator.current_procedure_context
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.error(f"PROC_BEGIN for '{proc_name}', but current_procedure_context is for '{proc_entry.name if proc_entry else 'None'}'. Mismatch or context not set.")
            proc_entry = self.asm_generator.symbol_table.lookup_globally(proc_name)
            if not proc_entry:
                return [f"; ERROR: SymbolTableEntry for procedure '{proc_name}' not found."]

        asm_lines = []
        asm_lines.append(f"{proc_name} PROC")
        asm_lines.append(f"    PUSH BP")
        asm_lines.append(f"    MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_vars_total_size', 0)
        if local_var_size > 0:
            asm_lines.append(f"    SUB SP, {local_var_size}")
            self.logger.debug(f"  PROC_BEGIN {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"  PROC_BEGIN {proc_name}: No local variable space allocated (size 0).")

        return asm_lines

    def _translate_proc_end(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PROC_END: Marks the end of a procedure."""
        proc_name = tac_instruction.dest
        if not proc_name:
            self.logger.error(f"PROC_END TAC at line {tac_instruction.line_number} is missing procedure name (dest operand).")
            return [f"; ERROR: Malformed PROC_END TAC at line {tac_instruction.line_number}"]

        # Verify context matches, though it's less critical here than for reading local_var_size
        proc_entry = self.asm_generator.current_procedure_context
        if not proc_entry or proc_entry.name != proc_name:
            self.logger.warning(f"PROC_END for '{proc_name}', but current_procedure_context is for '{proc_entry.name if proc_entry else 'None'}'. Context might have been cleared early or mismatch.")
            # We don't strictly need proc_entry for the ENDP line itself, but good to note.

        asm_lines = []
        # Deallocate local variables and restore BP. This must happen before RET.
        # If there's a RETURN TAC, it will generate RET. If not (e.g. fall-through end of procedure),
        # a RET is still needed if it's not the main program's end.
        # The SymTable entry for the proc that is ending here should have local_vars_total_size.
        # This implies current_procedure_context should still be valid when _translate_proc_end is called.
        if proc_entry and getattr(proc_entry, 'local_vars_total_size', 0) > 0:
            asm_lines.append(f"    MOV SP, BP") # Deallocate locals
        asm_lines.append(f"    POP BP")       # Restore caller's BP
        
        # If this PROC_END corresponds to the main procedure (originally from PROGRAM_START),
        # the actual program termination (INT 21h) is handled by the DOS shell ('start' proc).
        # So, for the user's main procedure, the PROC_END should be followed by its ENDP,
        # and the CALL to it from 'start' will return, then 'start' will exit.
        # For sub-procedures, a RET is typically expected after stack cleanup unless specific fall-through logic.
        # However, the explicit RETURN TAC should generate the RET. So PROC_END only cleans up and labels.
        # If a procedure implicitly ends without a RETURN TAC, a RET instruction might be missing.
        # For now, assuming explicit RETURN TAC is used or fall-through to another block is intended.
        # The A7 TAC generator should be generating explicit RETURNs for procedures.

        asm_lines.append(f"{proc_name} ENDP")
        self.logger.debug(f"  PROC_END {proc_name}: Generated stack cleanup and ENDP.")
        return asm_lines

    def _translate_return(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC RETURN: op1 (optional return value for functions)"""
        asm_lines = []
        
        # If op1 exists, it's a function return value, place it in AX.
        if tac_instruction.op1:
            op1_asm = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)
            # Check if op1_asm is already AX to avoid MOV AX, AX
            if op1_asm.upper() != "AX":
                asm_lines.append(f"    MOV AX, {op1_asm}")
                self.logger.debug(f"  RETURN {tac_instruction.op1} -> MOV AX, {op1_asm}")
            else:
                self.logger.debug(f"  RETURN {tac_instruction.op1}: Value already in AX.")
        else:
            self.logger.debug(f"  RETURN (procedure return, no value)")

        # The stack frame (BP, SP adjustment for locals) is handled by PROC_END.
        # RETURN just issues the RET instruction.
        # This assumes that PROC_END will be called eventually to clean up stack frame before ENDP.
        # If RETURN is the *absolute last* thing before ENDP, the MOV SP,BP; POP BP would occur from PROC_END's translation.
        asm_lines.append(f"    RET")
        return asm_lines

    def _translate_label(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC LABEL: dest_label. The label itself is handled by ASMGenerator."""
        # The ASMGenerator._generate_procedure_asm already handles emitting the label string
        # if tac_instruction.label is present on *any* instruction line.
        # If LABEL is a dedicated TAC opcode (e.g. "LABEL L1"), this handler ensures it doesn't
        # produce redundant output or an error. The actual label string comes from tac_instruction.dest.
        label_name = tac_instruction.dest
        self.logger.debug(f"  LABEL TAC encountered for '{label_name}'. Label emission is handled by ASMGenerator based on any instruction's .label field.")
        # If this method is called, it implies a TAC line like: None LABEL None None L1 (where L1 is dest)
        # or something similar. The critical part is that ASMGenerator's loop already checks instr.label.
        # So, this handler for a standalone LABEL opcode should ideally produce nothing or a comment.
        return [f"; LABEL {label_name} (handled by generator logic)"] # Or simply return []

    def _translate_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC GOTO: target_label (in dest)"""
        target_label = tac_instruction.dest
        if not target_label:
            self.logger.error(f"GOTO TAC at line {tac_instruction.line_number} is missing target label (dest operand).")
            return [f"; ERROR: Malformed GOTO TAC at line {tac_instruction.line_number}"]
        
        self.logger.debug(f"  GOTO {target_label} -> JMP {target_label}")
        return [f"    JMP {target_label}"]

    def _translate_if_false_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_FALSE_GOTO: op1, target_label (in dest)
            If op1 is false (0), goto target_label.
        """
        condition_operand = tac_instruction.op1
        target_label = tac_instruction.dest

        if not condition_operand or not target_label:
            self.logger.error(f"IF_FALSE_GOTO TAC at line {tac_instruction.line_number} is missing condition operand or target label.")
            return [f"; ERROR: Malformed IF_FALSE_GOTO TAC at line {tac_instruction.line_number}"]

        cond_asm = self.asm_generator.get_operand_asm(condition_operand, tac_instruction.opcode)
        
        asm_lines = []
        # Standard way: CMP operand, 0; JE label
        # Ensure cond_asm is not a literal itself if it's the first arg to CMP, unless it's a register.
        # If cond_asm is a memory location, CMP [mem], 0 is fine.
        # If cond_asm is a literal (e.g. from a constant prop.), it's tricky.
        # Assume cond_asm is a variable/register here.
        
        # If cond_asm is a memory location, e.g. [BP-2]
        if cond_asm.startswith("["):
            asm_lines.append(f"    CMP WORD PTR {cond_asm}, 0") # Assuming WORD, adjust if type info available
        else: # Register or global variable name
            asm_lines.append(f"    CMP {cond_asm}, 0")
        
        asm_lines.append(f"    JE {target_label}")
        self.logger.debug(f"  IF_FALSE_GOTO {condition_operand}, {target_label} -> CMP {cond_asm}, 0; JE {target_label}")
        return asm_lines

    def _translate_if_eq_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_EQ_GOTO: op1, op2, target_label (in dest)
            If op1 == op2, goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_EQ_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_EQ_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # CMP op1_asm, op2_asm
        # JE target_label
        # Handle mem-mem comparison via register (AX)
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op2_asm}") # Load one of the memory operands into AX
            asm_lines.append(f"    CMP {op1_asm}, AX")   # Compare the other memory operand with AX
            self.logger.debug(f"  IF_EQ_GOTO {op1}, {op2}, {target_label} -> MOV AX, {op2_asm}; CMP {op1_asm}, AX; JE {target_label}")
        # Handle immediate-memory comparison: CMP mem, imm (allowed)
        elif op1_asm.startswith("[") and not op2_asm.startswith("["):
            try: # Check if op2_asm is a literal number
                int(op2_asm)
                asm_lines.append(f"    CMP WORD PTR {op1_asm}, {op2_asm}") # Assuming WORD
                self.logger.debug(f"  IF_EQ_GOTO {op1}, {op2}, {target_label} -> CMP WORD PTR {op1_asm}, {op2_asm}; JE {target_label}")
            except ValueError: # op2_asm is a register or global name
                asm_lines.append(f"    MOV AX, {op2_asm}") 
                asm_lines.append(f"    CMP {op1_asm}, AX")
                self.logger.debug(f"  IF_EQ_GOTO {op1}, {op2}, {target_label} -> MOV AX, {op2_asm}; CMP {op1_asm}, AX; JE {target_label}")
        else: # reg/global vs reg/global/literal
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"  IF_EQ_GOTO {op1}, {op2}, {target_label} -> CMP {op1_asm}, {op2_asm}; JE {target_label}")

        asm_lines.append(f"    JE {target_label}")
        return asm_lines

    def _translate_sub(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC SUB: dest := op1 - op2"""
        dest = tac_instruction.dest
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2

        if not dest or not op1 or not op2:
            self.logger.error(f"SUB TAC at line {tac_instruction.line_number} is missing operands.")
            return [f"; ERROR: Malformed SUB TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(dest, tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # Generic approach: MOV AX, op1; SUB AX, op2; MOV dest, AX
        # Avoid MOV AX, AX if op1_asm is AX
        if op1_asm.upper() != "AX":
            asm_lines.append(f"    MOV AX, {op1_asm}")
        
        # SUB AX, op2_asm
        asm_lines.append(f"    SUB AX, {op2_asm}")
        
        # Avoid MOV dest, AX if dest_asm is AX
        if dest_asm.upper() != "AX":
            asm_lines.append(f"    MOV {dest_asm}, AX")
        
        self.logger.debug(f"  SUB {dest} := {op1} - {op2} -> MOV AX, {op1_asm}; SUB AX, {op2_asm}; MOV {dest_asm}, AX (optimized for AX moves)")
        return asm_lines

    def _translate_if_ne_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC IF_NE_GOTO: op1, op2, target_label (in dest)
            If op1 != op2, goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_NE_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_NE_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # CMP op1_asm, op2_asm; JNE target_label
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op2_asm}")
            asm_lines.append(f"    CMP {op1_asm}, AX")
        elif op1_asm.startswith("[") and not op2_asm.startswith("["):
            try: 
                int(op2_asm)
                asm_lines.append(f"    CMP WORD PTR {op1_asm}, {op2_asm}")
            except ValueError: 
                asm_lines.append(f"    MOV AX, {op2_asm}") 
                asm_lines.append(f"    CMP {op1_asm}, AX")
        else: 
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")

        asm_lines.append(f"    JNE {target_label}")
        self.logger.debug(f"  IF_NE_GOTO {op1}, {op2}, {target_label} -> CMP ..., JNE {target_label}")
        return asm_lines

    def _translate_if_lt_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_LT_GOTO: op1, op2, target_label (in dest)
            If op1 < op2 (signed), goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_LT_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_LT_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op1_asm}") # Load op1 into AX for CMP AX, [mem]
            asm_lines.append(f"    CMP AX, {op2_asm}")
        elif not op1_asm.startswith("[") and op2_asm.startswith("["):
            # CMP reg/global, [mem] is fine
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")
        elif op1_asm.startswith("[") and not op2_asm.startswith("["):
            # CMP [mem], reg/global/literal
            # If op2_asm is literal, CMP [mem], literal is fine.
            # If op2_asm is reg/global, CMP [mem], reg/global is fine.
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")
        else: # reg/global vs reg/global/literal
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")

        asm_lines.append(f"    JL {target_label}") # Jump if Less (signed)
        self.logger.debug(f"  IF_LT_GOTO {op1}, {op2}, {target_label} -> CMP ..., JL {target_label}")
        return asm_lines

    def _translate_if_le_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_LE_GOTO: op1, op2, target_label (in dest)
            If op1 <= op2 (signed), goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_LE_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_LE_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # CMP logic similar to _translate_if_lt_goto
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op1_asm}") 
            asm_lines.append(f"    CMP AX, {op2_asm}")
        else:
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")

        asm_lines.append(f"    JLE {target_label}") # Jump if Less or Equal (signed)
        self.logger.debug(f"  IF_LE_GOTO {op1}, {op2}, {target_label} -> CMP ..., JLE {target_label}")
        return asm_lines

    def _translate_if_gt_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_GT_GOTO: op1, op2, target_label (in dest)
            If op1 > op2 (signed), goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_GT_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_GT_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # CMP logic similar to _translate_if_lt_goto
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op1_asm}") 
            asm_lines.append(f"    CMP AX, {op2_asm}")
        else:
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")

        asm_lines.append(f"    JG {target_label}") # Jump if Greater (signed)
        self.logger.debug(f"  IF_GT_GOTO {op1}, {op2}, {target_label} -> CMP ..., JG {target_label}")
        return asm_lines

    def _translate_if_ge_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_GE_GOTO: op1, op2, target_label (in dest)
            If op1 >= op2 (signed), goto target_label.
        """
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2
        target_label = tac_instruction.dest

        if not op1 or not op2 or not target_label:
            self.logger.error(f"IF_GE_GOTO TAC at line {tac_instruction.line_number} is missing operands or target label.")
            return [f"; ERROR: Malformed IF_GE_GOTO TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        # CMP logic similar to _translate_if_lt_goto
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"    MOV AX, {op1_asm}") 
            asm_lines.append(f"    CMP AX, {op2_asm}")
        else:
            asm_lines.append(f"    CMP {op1_asm}, {op2_asm}")

        asm_lines.append(f"    JGE {target_label}") # Jump if Greater or Equal (signed)
        self.logger.debug(f"  IF_GE_GOTO {op1}, {op2}, {target_label} -> CMP ..., JGE {target_label}")
        return asm_lines


# Future methods like:
# def _translate_assign(self, tac_instruction: ParsedTACInstruction) -> str: