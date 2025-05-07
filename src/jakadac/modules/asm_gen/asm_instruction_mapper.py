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
            # Use the enum member's name (e.g., "ADD", "IF_EQ_GOTO"), converted to lowercase,
            # to match handler methods like _translate_add, _translate_if_eq_goto.
            opcode_value_str = tac_instruction.opcode.name.lower()
            log_opcode_repr = tac_instruction.opcode.name   # For logging, use the original enum name (e.g., 'ASSIGN', 'ADD')
        elif isinstance(tac_instruction.opcode, str):
            # If opcode is already a string (e.g., from a malformed TAC or direct usage),
            # convert to lowercase for handler lookup.
            opcode_value_str = tac_instruction.opcode.lower()
            log_opcode_repr = tac_instruction.opcode # Use the string itself for logging
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
        opcode_name = tac_instruction.opcode.name if hasattr(tac_instruction.opcode, 'name') else str(tac_instruction.opcode)
        dest_str = str(tac_instruction.dest) if tac_instruction.dest and hasattr(tac_instruction.dest, 'value') else "None"
        op1_str = str(tac_instruction.op1) if tac_instruction.op1 and hasattr(tac_instruction.op1, 'value') else "None"
        op2_str = str(tac_instruction.op2) if tac_instruction.op2 and hasattr(tac_instruction.op2, 'value') else "None"
        line_num = tac_instruction.line_number if hasattr(tac_instruction, 'line_number') else 'N/A'
        
        # Match the log format from test_translate_unknown_opcode
        self.logger.warning(f"No specific translator for TAC opcode: {opcode_name} at line {line_num}")
        
        # Match the return string format from test_translate_unknown_opcode
        return [f"; UNHANDLED TAC Opcode: {opcode_name} (Operands: D:{dest_str}, O1:{op1_str}, O2:{op2_str})"]

    # --- Specific TAC Opcode Translators ---

    def _translate_assign(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ASSIGN: dest := op1"""
        if tac_instruction.dest is None or tac_instruction.op1 is None:
            self.logger.error(f"ASSIGN TAC at line {tac_instruction.line_number} is missing destination or source operand.")
            return [f"; ERROR: Malformed ASSIGN TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(tac_instruction.dest, tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)

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
            self.logger.debug(f"ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV AX, {op1_asm}; MOV {dest_asm}, AX")
        elif dest_asm.startswith("[") and is_op1_literal:
            # Literal to Memory: MOV mem, literal (allowed)
            asm_lines.append(f"MOV WORD PTR {dest_asm}, {op1_asm}") # Assuming WORD for now, could be BYTE
            self.logger.debug(f"ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV WORD PTR {dest_asm}, {op1_asm}")
        else:
            # Register to Memory, Memory to Register, Register to Register, Literal to Register
            asm_lines.append(f"MOV {dest_asm}, {op1_asm}")
            self.logger.debug(f"ASSIGN {tac_instruction.dest} := {tac_instruction.op1} -> MOV {dest_asm}, {op1_asm}")
            
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
            self.logger.debug(f"ADD {tac_instruction.dest} := {tac_instruction.op1} + {tac_instruction.op2} -> ADD {dest_asm}, {op2_asm}")
        else:
            asm_lines.append(f"MOV AX, {op1_asm}")
            asm_lines.append(f"ADD AX, {op2_asm}")
            asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"ADD {tac_instruction.dest} := {tac_instruction.op1} + {tac_instruction.op2} -> MOV AX, {op1_asm}; ADD AX, {op2_asm}; MOV {dest_asm}, AX")
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
        asm_lines.append(f"{proc_name}:") # Using NEAR by default
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_vars_total_size', 0)
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROGRAM_START {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROGRAM_START {proc_name}: No local variable space allocated (size 0).")
            
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
        asm_lines.append(f"{proc_name}:")
        asm_lines.append(f"PUSH BP")
        asm_lines.append(f"MOV BP, SP")

        local_var_size = getattr(proc_entry, 'local_vars_total_size', 0)
        if local_var_size > 0:
            asm_lines.append(f"SUB SP, {local_var_size}")
            self.logger.debug(f"PROC_BEGIN {proc_name}: Allocated {local_var_size} bytes for locals.")
        else:
            self.logger.debug(f"PROC_BEGIN {proc_name}: No local variable space allocated (size 0).")

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
            asm_lines.append(f"MOV SP, BP") # Deallocate locals
        asm_lines.append(f"POP BP")       # Restore caller's BP
        
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
        self.logger.debug(f"PROC_END {proc_name}: Generated stack cleanup and ENDP.")
        return asm_lines

    def _translate_return(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC RETURN: op1 (optional return value for functions)"""
        asm_lines = []
        
        # If op1 exists, it's a function return value, place it in AX.
        if tac_instruction.op1:
            op1_asm = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)
            # Check if op1_asm is already AX to avoid MOV AX, AX
            if op1_asm.upper() != "AX":
                asm_lines.append(f"MOV AX, {op1_asm}")
                self.logger.debug(f"RETURN {tac_instruction.op1} -> MOV AX, {op1_asm}")
            else:
                self.logger.debug(f"RETURN {tac_instruction.op1}: Value already in AX.")
        else:
            self.logger.debug(f"RETURN (procedure return, no value)")

        # The stack frame (BP, SP adjustment for locals) is handled by PROC_END.
        # RETURN just issues the RET instruction.
        # This assumes that PROC_END will be called eventually to clean up stack frame before ENDP.
        # If RETURN is the *absolute last* thing before ENDP, the MOV SP,BP; POP BP would occur from PROC_END's translation.
        asm_lines.append(f"RET")
        return asm_lines

    def _translate_label(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC LABEL: dest_label."""
        target_label = tac_instruction.dest
        if target_label:
            # self.logger.debug(f"LABEL {target_label} -> {target_label}:")
            return [f"{target_label}:"]
        else:
            self.logger.error(f"LABEL TAC at line {tac_instruction.line_number} is missing label name (dest operand).")
            return [f"; ERROR: Malformed LABEL TAC at line {tac_instruction.line_number} - Missing label name."]

    def _translate_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC GOTO: target_label (in dest)"""
        target_label = tac_instruction.dest
        if not target_label:
            self.logger.error(f"GOTO TAC at line {tac_instruction.line_number} is missing target label (dest operand).")
            return [f"; ERROR: Malformed GOTO TAC at line {tac_instruction.line_number}"]
        
        self.logger.debug(f"GOTO {target_label} -> JMP {target_label}")
        return [f"JMP {target_label}"]

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
            asm_lines.append(f"CMP WORD PTR {cond_asm}, 0") # Assuming WORD, adjust if type info available
        else: # Register or global variable name
            asm_lines.append(f"CMP {cond_asm}, 0")
        
        asm_lines.append(f"JE {target_label}")
        self.logger.debug(f"IF_FALSE_GOTO {cond_asm}, {target_label} -> CMP {cond_asm}, 0; JE {target_label}")
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
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_EQ_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JE {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_EQ_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JE {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_EQ_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JE {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_EQ_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JE {target_label}")

        asm_lines.append(f"JE {target_label}") # Jump if Equal
        return asm_lines

    def _translate_if_ne_goto(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """
            Translates TAC IF_NE_GOTO: op1, op2, target_label (in dest)
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
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_NE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JNE {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_NE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JNE {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_NE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JNE {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_NE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JNE {target_label}")

        asm_lines.append(f"JNE {target_label}") # Jump if Not Equal
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
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_LT_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JL {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_LT_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JL {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_LT_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JL {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_LT_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JL {target_label}")

        asm_lines.append(f"JL {target_label}") # Jump if Less (signed)
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
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_LE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JLE {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_LE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JLE {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_LE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JLE {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_LE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JLE {target_label}")

        asm_lines.append(f"JLE {target_label}") # Jump if Less or Equal (signed)
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
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_GT_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JG {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_GT_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JG {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_GT_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JG {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_GT_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JG {target_label}")

        asm_lines.append(f"JG {target_label}") # Jump if Greater (signed)
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
        if op1_asm.startswith("[") and op2_asm.startswith("["):
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_GE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JGE {target_label}")
        elif op1_asm.isdigit() and op2_asm.startswith("["):
            asm_lines.append(f"CMP {op2_asm}, {op1_asm}") # CMP [mem], imm
            self.logger.debug(f"IF_GE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op2_asm}, {op1_asm}; JGE {target_label}")
        elif op1_asm.startswith("[") and op2_asm.isdigit():
            asm_lines.append(f"MOV AX, {op1_asm}") 
            asm_lines.append(f"CMP AX, {op2_asm}")
            self.logger.debug(f"IF_GE_GOTO {op1_asm}, {op2_asm}, {target_label} -> MOV AX, {op1_asm}; CMP AX, {op2_asm}; JGE {target_label}")
        else:
            asm_lines.append(f"CMP {op1_asm}, {op2_asm}")
            self.logger.debug(f"IF_GE_GOTO {op1_asm}, {op2_asm}, {target_label} -> CMP {op1_asm}, {op2_asm}; JGE {target_label}")

        asm_lines.append(f"JGE {target_label}") # Jump if Greater or Equal (signed)
        return asm_lines


    def _translate_conditional_jump(self, tac_instruction: ParsedTACInstruction, jump_instruction: str) -> List[str]:
        asm_lines = []
        op1_asm_val = self.asm_generator.get_operand_asm(tac_instruction.op1, tac_instruction.opcode)
        op2_asm_val = self.asm_generator.get_operand_asm(tac_instruction.op2, tac_instruction.opcode) 
        label_asm = self.asm_generator.get_operand_asm(tac_instruction.dest, tac_instruction.opcode) # Label is in dest

        # Optimization: if op1 is immediate and op2 is register/memory, 
        # prefer 'CMP reg/mem, imm' and invert jump condition.
        if self.asm_generator.is_immediate(op1_asm_val) and \
           not self.asm_generator.is_immediate(op2_asm_val) and \
           (self.asm_generator.is_register(op2_asm_val) or op2_asm_val.startswith("[")):
            
            self.logger.debug(f"Comparing immediate {op1_asm_val} with memory/register {op2_asm_val}, swapping for optimal CMP and inverting jump.")
            asm_lines.append(f"CMP {op2_asm_val}, {op1_asm_val}")

            opposite_jump_map = {
                "JE": "JE", "JNE": "JNE",   # Equal/Not Equal are symmetric
                "JL": "JG",                 # op1 < op2  (tac_instruction) -> op2 > op1 (CMP operands swapped)
                "JLE": "JGE",               # op1 <= op2 (tac_instruction) -> op2 >= op1 (CMP operands swapped)
                "JG": "JL",                 # op1 > op2  (tac_instruction) -> op2 < op1 (CMP operands swapped)
                "JGE": "JLE"                # op1 >= op2 (tac_instruction) -> op2 <= op1 (CMP operands swapped)
            }
            actual_jump_instruction = opposite_jump_map.get(jump_instruction)

            if not actual_jump_instruction:
                self.logger.warning(f"Could not find opposite jump for {jump_instruction} during optimization of {tac_instruction}, falling back.")
                # Fallback to original non-optimized behavior for this specific sub-case if map fails
                asm_lines = [f"MOV AX, {op1_asm_val}", f"CMP AX, {op2_asm_val}"] # Re-initialize asm_lines
                actual_jump_instruction = jump_instruction
            
            asm_lines.append(f"{actual_jump_instruction} {label_asm}")

        elif not self.asm_generator.is_immediate(op1_asm_val) and self.asm_generator.is_immediate(op2_asm_val):
            # op1 is not immediate, op2 is. This is the preferred 'CMP reg/mem, imm'
            asm_lines.append(f"CMP {op1_asm_val}, {op2_asm_val}")
            asm_lines.append(f"{jump_instruction} {label_asm}")
        elif self.asm_generator.is_immediate(op1_asm_val) and self.asm_generator.is_immediate(op2_asm_val):
            # Both are immediate. MOV op1 to AX, then CMP AX, op2
            asm_lines.append(f"MOV AX, {op1_asm_val}")
            asm_lines.append(f"CMP AX, {op2_asm_val}")
            asm_lines.append(f"{jump_instruction} {label_asm}")
        else:
            # Neither is immediate (e.g. reg, reg or mem, mem or reg, mem or mem, reg)
            # Or op1 is immediate, but op2 is not suitable for direct CMP (e.g. complex expression not starting with '[')
            # Standard: MOV AX, op1_asm_val; CMP AX, op2_asm_val unless one is already AX
            if op1_asm_val == "AX":
                asm_lines.append(f"CMP AX, {op2_asm_val}")
            elif op2_asm_val == "AX": # Should be CMP op1, AX
                asm_lines.append(f"CMP {op1_asm_val}, AX")
            else: # Default general case
                asm_lines.append(f"MOV AX, {op1_asm_val}")
                asm_lines.append(f"CMP AX, {op2_asm_val}")
            asm_lines.append(f"{jump_instruction} {label_asm}")
        
        self.logger.debug(f"Translated conditional jump {tac_instruction.opcode.name if hasattr(tac_instruction.opcode, 'name') else tac_instruction.opcode}: {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_mul(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC MUL: dest := op1 * op2"""
        dest = tac_instruction.dest
        op1 = tac_instruction.op1
        op2 = tac_instruction.op2

        if not dest or not op1 or not op2:
            self.logger.error(f"MUL TAC at line {tac_instruction.line_number} is missing operands.")
            return [f"; ERROR: Malformed MUL TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(dest, tac_instruction.opcode)
        op1_asm = self.asm_generator.get_operand_asm(op1, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2, tac_instruction.opcode)

        asm_lines = []
        asm_lines.append(f"MOV AX, {op1_asm}")
        # MUL instruction in 8086/8088 typically uses AX as one implicit operand 
        # and the source operand (register or memory) specified. 
        # If op2 is a memory location or immediate, it's fine. If op2 is another register,
        # and op1 was also a memory location that needed AX, care must be taken.
        # Assuming op2_asm can be directly used with MUL (e.g. BX, CX, DX, or memory_ref)
        # If op2_asm is an immediate, it must be moved to a register first.
        # For simplicity here, we'll assume op2_asm is suitable or move to BX.
        if op2_asm.upper() == "AX": # Avoid MUL AX if op2 is AX
            asm_lines.append(f"MOV BX, {op2_asm}") # Should actually be op1 if op2 is AX, or a temp if both are AX
            asm_lines.append(f"MUL BX")
        elif op2.isdigit() or (op2.startswith("'") and op2.endswith("'")): # Immediate value
             asm_lines.append(f"MOV BX, {op2_asm}")
             asm_lines.append(f"MUL BX")
        else:
            asm_lines.append(f"MUL {op2_asm}") # e.g., MUL BX or MUL [var2]
        
        asm_lines.append(f"MOV {dest_asm}, AX")

        self.logger.debug(f"MUL {dest}, {op1}, {op2} -> Generated MUL sequence, result in AX to {dest_asm}")
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
            asm_lines.append(f"MOV AX, {op1_asm}")
        
        # SUB AX, op2_asm
        asm_lines.append(f"SUB AX, {op2_asm}")
        
        # Avoid MOV dest, AX if dest_asm is AX
        if dest_asm.upper() != "AX":
            asm_lines.append(f"MOV {dest_asm}, AX")
        
        self.logger.debug(f"SUB {dest} := {op1} - {op2} -> MOV AX, {op1_asm}; SUB AX, {op2_asm}; MOV {dest_asm}, AX (optimized for AX moves)")
        return asm_lines

    def _translate_div(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC DIV: dest := op1 / op2"""
        dest_operand = tac_instruction.dest
        op1_operand = tac_instruction.op1
        op2_operand = tac_instruction.op2
        asm_lines = []

        if not dest_operand or not op1_operand or not op2_operand or \
           not hasattr(dest_operand, 'value') or \
           not hasattr(op1_operand, 'value') or \
           not hasattr(op2_operand, 'value'):
            self.logger.error(f"DIV TAC at line {tac_instruction.line_number} is missing operands or destination.")
            return [f"; ERROR: Malformed DIV TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(dest_operand, tac_instruction.opcode, is_destination=True)
        op1_asm = self.asm_generator.get_operand_asm(op1_operand, tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(op2_operand, tac_instruction.opcode)

        # Load dividend (op1) into AX
        if op1_asm != "AX":
            asm_lines.append(f"MOV AX, {op1_asm}")
        
        # Load divisor (op2) into a register (BX by default)
        # Ensure op2 is not AX if op1 was AX. If op2 is AX, this implies op1 was not AX.
        # If op2_asm is already a register other than AX, use it.
        # If op2_asm is memory or immediate, load to BX.
        # If op2_asm is AX (meaning op1 was not AX and already moved to AX), then we're good.
        
        divisor_reg = "BX" # Default register for divisor
        if self.asm_generator.is_register(op2_asm):
            if op2_asm == "AX": # op1 was moved to AX earlier. Now op2 is also AX.
                                # This shouldn't happen if op1 was AX to begin with. 
                                # But if op1 was moved to AX, and op2_asm is AX then we need to move op2 out of AX.
                asm_lines.append(f"MOV {divisor_reg}, AX") # Use BX for op2_asm
            else:
                divisor_reg = op2_asm # op2_asm is already a suitable register (e.g. BX, CX, DX)
        else: # op2_asm is memory or immediate
            asm_lines.append(f"MOV {divisor_reg}, {op2_asm}")

        # Prepare DX:AX for division (DX must be zero for unsigned 16-bit dividend in AX)
        asm_lines.append("XOR DX, DX")
        
        # Perform division
        asm_lines.append(f"DIV {divisor_reg}")
        
        # Store quotient (in AX) to destination
        if dest_asm != "AX":
            asm_lines.append(f"MOV {dest_asm}, AX")
        elif dest_operand.value != "AX": # If dest is 'AX' (string) but not actually the AX register in assembly form
             asm_lines.append(f"MOV {dest_asm}, AX")

        self.logger.debug(f"Translated DIV {tac_instruction} -> {asm_lines}")    
        return asm_lines

    def _translate_call(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC CALL: dest := CALL proc_label, num_params"""
        asm_lines = []
        proc_label_operand = tac_instruction.op1
        num_params_operand = tac_instruction.op2 # This is TACOperand(value=count)
        return_dest_operand = tac_instruction.dest

        if not proc_label_operand or not hasattr(proc_label_operand, 'value'):
            self.logger.error(f"CALL TAC at line {tac_instruction.line_number} is missing procedure label.")
            return [f"; ERROR: Malformed CALL TAC (missing label) at line {tac_instruction.line_number}"]

        proc_label_asm = str(proc_label_operand.value) # Labels are typically direct strings

        asm_lines.append(f"CALL {proc_label_asm}")

        num_params = 0
        if num_params_operand and hasattr(num_params_operand, 'value') and isinstance(num_params_operand.value, int):
            num_params = num_params_operand.value
        
        if num_params > 0:
            # Clean up stack after call if there were parameters
            # Each parameter is assumed to be a word (2 bytes)
            stack_cleanup_bytes = num_params * 2 
            asm_lines.append(f"ADD SP, {stack_cleanup_bytes}")

        if return_dest_operand and hasattr(return_dest_operand, 'value'):
            dest_asm = self.asm_generator.get_operand_asm(return_dest_operand, tac_instruction.opcode, is_destination=True)
            asm_lines.append(f"MOV {dest_asm}, AX")
            self.logger.debug(f"CALL to {proc_label_asm} with {num_params} params, returning to {dest_asm}")
        else:
            self.logger.debug(f"CALL to {proc_label_asm} with {num_params} params, no return value assigned.")

        self.logger.debug(f"Translated CALL {tac_instruction} -> {asm_lines}")    
        return asm_lines

    def _translate_param(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC PARAM: op1"""
        param_operand = tac_instruction.op1
        asm_lines = []

        if not param_operand or not hasattr(param_operand, 'value'):
            self.logger.error(f"PARAM TAC at line {tac_instruction.line_number} is missing operand.")
            return [f"; ERROR: Malformed PARAM TAC at line {tac_instruction.line_number}"]

        param_asm = self.asm_generator.get_operand_asm(param_operand, tac_instruction.opcode)
        asm_lines.append(f"PUSH {param_asm}")
        
        self.logger.debug(f"Translated PARAM {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_array_assign_from(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ARRAY_ASSIGN_FROM: dest_array_base[index_op] := source_op"""
        # TAC: dest=array_base, op1=index, op2=source_value
        array_base_operand = tac_instruction.dest
        index_operand = tac_instruction.op1
        source_value_operand = tac_instruction.op2
        asm_lines = []

        if not (array_base_operand and hasattr(array_base_operand, 'value') and 
                index_operand and hasattr(index_operand, 'value') and 
                source_value_operand and hasattr(source_value_operand, 'value')):
            self.logger.error(f"ARRAY_ASSIGN_FROM TAC at line {tac_instruction.line_number} is missing operands.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_FROM TAC at line {tac_instruction.line_number}"]

        array_base_asm = self.asm_generator.get_operand_asm(array_base_operand, tac_instruction.opcode, is_destination=False) # Base address is a source for addressing
        index_asm = self.asm_generator.get_operand_asm(index_operand, tac_instruction.opcode, is_destination=False)
        source_value_asm = self.asm_generator.get_operand_asm(source_value_operand, tac_instruction.opcode, is_destination=False)

        # ASM: MOV AX, idx_asm; MOV BX, src_val_asm; MOV [arr_base_asm+AX], BX
        # Assuming idx_asm needs to be in AX for addressing, and src_val_asm in BX.
        # No explicit scaling of index_asm here, as per test expectations.
        
        if index_asm != "AX":
            asm_lines.append(f"MOV AX, {index_asm}")
        # If index_asm is already AX, this MOV is skipped (minor optimization)
        
        if source_value_asm != "BX":
            asm_lines.append(f"MOV BX, {source_value_asm}")
        # If source_value_asm is already BX, this MOV is skipped.

        asm_lines.append(f"MOV [{array_base_asm}+AX], BX")

        self.logger.debug(f"Translated ARRAY_ASSIGN_FROM {tac_instruction} -> {asm_lines}")
        return asm_lines

    def _translate_array_assign_to(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC ARRAY_ASSIGN_TO: dest_op := source_array_base[index_op]"""
        # TAC: dest=dest_var, op1=array_base, op2=index
        dest_operand = tac_instruction.dest
        array_base_operand = tac_instruction.op1
        index_operand = tac_instruction.op2
        asm_lines = []

        if not (dest_operand and hasattr(dest_operand, 'value') and 
                array_base_operand and hasattr(array_base_operand, 'value') and 
                index_operand and hasattr(index_operand, 'value')):
            self.logger.error(f"ARRAY_ASSIGN_TO TAC at line {tac_instruction.line_number} is missing operands.")
            return [f"; ERROR: Malformed ARRAY_ASSIGN_TO TAC at line {tac_instruction.line_number}"]

        dest_asm = self.asm_generator.get_operand_asm(dest_operand, tac_instruction.opcode, is_destination=True)
        array_base_asm = self.asm_generator.get_operand_asm(array_base_operand, tac_instruction.opcode, is_destination=False)
        index_asm = self.asm_generator.get_operand_asm(index_operand, tac_instruction.opcode, is_destination=False)

        # ASM: MOV AX, idx_asm; MOV BX, [arr_base_asm+AX]; MOV dest_var_asm, BX
        # Assuming idx_asm needs to be in AX for addressing.
        # The value from memory will be loaded into BX.
        
        if index_asm != "AX":
            asm_lines.append(f"MOV AX, {index_asm}")
        
        asm_lines.append(f"MOV BX, [{array_base_asm}+AX]")
        
        if dest_asm != "BX":
            asm_lines.append(f"MOV {dest_asm}, BX")
        # If dest_asm is already BX, this MOV is skipped.

        self.logger.debug(f"Translated ARRAY_ASSIGN_TO {tac_instruction} -> {asm_lines}")
        return asm_lines
    
    #endregion

    #region Unhandled/Error
    def _translate_mod(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        """Translates TAC MOD: dest := op1 % op2"""
        self.logger.error(f"MOD TAC at line {tac_instruction.line_number} is not implemented.")
        return [f"; ERROR: MOD TAC at line {tac_instruction.line_number} is not implemented."]

    #endregion

    #region Unhandled/Error
    def _translate_unknown(self, tac_instruction: ParsedTACInstruction) -> List[str]:
        opcode_name = tac_instruction.opcode.name if hasattr(tac_instruction.opcode, 'name') else str(tac_instruction.opcode)
        dest_str = str(tac_instruction.dest) if tac_instruction.dest and hasattr(tac_instruction.dest, 'value') else "None"
        op1_str = str(tac_instruction.op1) if tac_instruction.op1 and hasattr(tac_instruction.op1, 'value') else "None"
        op2_str = str(tac_instruction.op2) if tac_instruction.op2 and hasattr(tac_instruction.op2, 'value') else "None"
        line_num = tac_instruction.line_number if hasattr(tac_instruction, 'line_number') else 'N/A'
        
        # Match the log format from test_translate_unknown_opcode
        self.logger.warning(f"No specific translator for TAC opcode: {opcode_name} at line {line_num}")
        
        # Match the return string format from test_translate_unknown_opcode
        return [f"; UNHANDLED TAC Opcode: {opcode_name} (Operands: D:{dest_str}, O1:{op1_str}, O2:{op2_str})"]

    #endregion

# Future methods like:
# def _translate_assign(self, tac_instruction: ParsedTACInstruction) -> str: