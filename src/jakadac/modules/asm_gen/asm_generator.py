from ..Logger import Logger
from ..SymTable import SymbolTable, Symbol, EntryType
from .tac_parser import TACParser # Assuming this is the correct location and name
from .asm_instruction_mapper import ASMInstructionMapper # Assuming correct location and name
from .tac_instruction import ParsedTACInstruction, TACOpcode # Assuming correct location and name
from typing import List, Tuple, Optional, Dict

class ASMGenerator:
    """
    Orchestrates the conversion of Three-Address Code (TAC) to 8086 Assembly Language.

    The generator takes a TAC file and a symbol table, processes them, and outputs
    an .asm file that can be assembled and run (e.g., in DOSBox with TASM/MASM).
    It handles:
    - Parsing TAC instructions.
    - Managing the .data segment for global variables and string literals.
    - Generating procedure prologues and epilogues.
    - Translating TAC operations to ASM instructions via an ASMInstructionMapper.
    - Formatting operands correctly for ASM (e.g., memory addresses, immediates).
    - Creating a standard DOS program entry point that calls the main Ada procedure.
    """

    def __init__(self,
                 tac_filepath: str,
                 asm_filepath: str,
                 symbol_table: SymbolTable,
                 string_literals_map: Dict[str, str], # e.g., {"_S0": "Hello World"}
                 logger: Logger):
        """
        Initializes the ASMGenerator.

        Args:
            tac_filepath: Path to the input .tac file.
            asm_filepath: Path for the output .asm file.
            symbol_table: The populated symbol table from earlier compiler phases.
            string_literals_map: A dictionary mapping string labels (e.g., "_S0")
                                 to their raw string values (e.g., "Hello World").
                                 The generator will handle null-termination.
            logger: An instance of the Logger for logging messages.
        """
        self.tac_filepath = tac_filepath
        self.asm_filepath = asm_filepath
        self.symbol_table = symbol_table
        self.string_literals_map = string_literals_map
        self.logger = logger

        # Sub-components (to be initialized as needed or passed if they are complex)
        self.tac_parser = TACParser(self.tac_filepath)
        # ASMInstructionMapper will likely need the symbol_table and logger too,
        # and potentially a reference back to this generator for operand formatting.
        self.instruction_mapper = ASMInstructionMapper(self.symbol_table, self.logger, self) # Passing self for get_operand_asm

        self.parsed_tac: List[ParsedTACInstruction] = []
        self.user_main_procedure_name: Optional[str] = None # Name of the procedure marked with PROGRAM_START
        self.program_global_vars: Dict[str, Symbol] = {}
        self.current_procedure_context: Optional[Symbol] = None # ST entry for the proc being processed

    # --- Placeholder for methods to be added ---
    # def generate_asm(self) -> bool:
    #     pass

    def _parse_and_prepare(self) -> bool:
        """
        Parses the TAC file, identifies the main procedure, and groups
        TAC instructions by procedure using a stack to handle nesting.
        Returns True on success, False on failure.
        """
        self.logger.info("Diag: _parse_and_prepare started.") # DIAGNOSTIC
        try:
            self.parsed_tac = self.tac_parser.parse_tac_file()
            if not self.parsed_tac:
                self.logger.error("Diag: Condition: Parsing TAC file yielded no instructions.") # DIAGNOSTIC
                self.logger.error("Parsing TAC file yielded no instructions.")
                return False
        except Exception as e:
            self.logger.error(f"Diag: Exception during TAC parsing: {e}") # DIAGNOSTIC
            self.logger.error(f"Error parsing TAC file '{self.tac_filepath}': {e}")
            return False

        self.logger.info(f"Diag: TAC parsing complete. Number of instructions: {len(self.parsed_tac)}") # DIAGNOSTIC

        # 1. Identify user_main_procedure_name from PROGRAM_START
        self.user_main_procedure_name = None
        self.logger.info("Diag: Starting PROGRAM_START identification loop.") # DIAGNOSTIC
        for instr_idx, instr in enumerate(self.parsed_tac):
            self.logger.debug(f"Diag: Checking instr {instr_idx}: {instr.opcode}, op1: {instr.operand1.value if instr.operand1 else 'N/A'}") # DIAGNOSTIC
            if instr.opcode == TACOpcode.PROGRAM_START:
                self.logger.info(f"Diag: Found PROGRAM_START at instr {instr_idx}.") # DIAGNOSTIC
                if instr.operand1 and isinstance(instr.operand1.value, str):
                    if self.user_main_procedure_name is not None:
                        self.logger.error("Diag: Condition: Multiple PROGRAM_START directives.") # DIAGNOSTIC
                        self.logger.error(f"Multiple PROGRAM_START directives found. First: '{self.user_main_procedure_name}', additional: '{instr.operand1.value}'. This is not supported.")
                        return False
                    self.user_main_procedure_name = instr.operand1.value
                    self.logger.info(f"Diag: user_main_procedure_name set to '{self.user_main_procedure_name}'.") # DIAGNOSTIC
                else:
                    self.logger.error(f"Diag: Condition: PROGRAM_START TAC at line {instr.line_number} missing/invalid operand1.") # DIAGNOSTIC
                    self.logger.error(f"PROGRAM_START TAC at line {instr.line_number} is missing procedure name in operand1.")
                    return False
        
        self.logger.info(f"Diag: PROGRAM_START identification loop finished. user_main_procedure_name: '{self.user_main_procedure_name}'.") # DIAGNOSTIC
                
        if not self.user_main_procedure_name:
            self.logger.error("Diag: Condition: No PROGRAM_START directive found after loop.") # DIAGNOSTIC
            self.logger.error("No PROGRAM_START directive found in TAC file. Cannot determine program entry point.")
            return False
        self.logger.info(f"Identified main Ada procedure: '{self.user_main_procedure_name}'")

        # 2. Group TAC instructions by procedure using a stack
        self.logger.info("Diag: Starting procedure grouping.") # DIAGNOSTIC
        _procedures_tac: Dict[str, List[ParsedTACInstruction]] = {}
        proc_stack: List[str] = []
        active_proc_name: Optional[str] = None

        for instr_idx, instr in enumerate(self.parsed_tac):
            self.logger.debug(f"Diag: Grouping instr {instr_idx}: {instr.raw_line.strip()}") # DIAGNOSTIC
            if instr.opcode == TACOpcode.PROC_BEGIN:
                if not instr.operand1 or not isinstance(instr.operand1.value, str):
                    self.logger.error(f"Diag: Condition: PROC_BEGIN TAC at line {instr.line_number} missing/invalid operand1.") # DIAGNOSTIC
                    self.logger.error(f"PROC_BEGIN TAC at line {instr.line_number} is missing procedure name in operand1.")
                    return False
                proc_name = instr.operand1.value
                self.logger.debug(f"Diag: PROC_BEGIN for '{proc_name}'.") # DIAGNOSTIC

                if proc_name not in _procedures_tac:
                    _procedures_tac[proc_name] = []
                _procedures_tac[proc_name].append(instr)
                
                proc_stack.append(proc_name)
                active_proc_name = proc_name

            elif instr.opcode == TACOpcode.PROC_END:
                if not instr.operand1 or not isinstance(instr.operand1.value, str):
                    self.logger.error(f"Diag: Condition: PROC_END TAC at line {instr.line_number} missing/invalid operand1.") # DIAGNOSTIC
                    self.logger.error(f"PROC_END TAC at line {instr.line_number} is missing procedure name in operand1.")
                    return False
                proc_name = instr.operand1.value
                self.logger.debug(f"Diag: PROC_END for '{proc_name}'. Stack top: '{proc_stack[-1] if proc_stack else 'EMPTY'}'.") # DIAGNOSTIC

                if not proc_stack or proc_stack[-1] != proc_name:
                    self.logger.error(f"Diag: Condition: PROC_END for '{proc_name}' mismatch/empty stack.") # DIAGNOSTIC
                    self.logger.error(f"PROC_END for '{proc_name}' at line {instr.line_number} found without matching PROC_BEGIN on stack (stack top: '{proc_stack[-1] if proc_stack else None}').")
                    return False 
            
                _procedures_tac[proc_name].append(instr) # Add before popping for completeness of procedure's TAC list
                proc_stack.pop()
                active_proc_name = proc_stack[-1] if proc_stack else None
            
            elif instr.opcode == TACOpcode.PROGRAM_START:
                self.logger.debug(f"Diag: Skipping PROGRAM_START instruction during grouping: {instr.raw_line.strip()}") # DIAGNOSTIC
                continue

            else: # Other instructions (ASSIGN, CALL, GOTO, etc.)
                if active_proc_name:
                    if active_proc_name not in _procedures_tac:
                        self.logger.error(f"Diag: Internal error: active_proc_name '{active_proc_name}' not in _procedures_tac dict during grouping.") # DIAGNOSTIC
                        _procedures_tac[active_proc_name] = [] # Should not happen
                    _procedures_tac[active_proc_name].append(instr)
                    self.logger.debug(f"Diag: Added instruction to '{active_proc_name}': {instr.raw_line.strip()}") # DIAGNOSTIC
                else:
                    self.logger.warning(f"Diag: Instruction '{instr.raw_line.strip()}' at line {instr.line_number} (Opcode: {instr.opcode}) outside active procedure context. IGNORING.") # DIAGNOSTIC

        if proc_stack: # Should be empty if all PROC_BEGINs have matching PROC_ENDs
            self.logger.error(f"Diag: Condition: Unmatched PROC_BEGIN statements at end. Stack: {proc_stack}") # DIAGNOSTIC
            self.logger.error(f"Unmatched PROC_BEGIN statements at end of TAC processing. Stack: {proc_stack}")
            return False
            
        self.logger.info(f"TAC grouped successfully. Procedures found: {list(_procedures_tac.keys())}")
        self._internal_grouped_tac = _procedures_tac 
        self.logger.info("Diag: _parse_and_prepare successfully completed.") # DIAGNOSTIC
        return True

    def _collect_global_vars(self) -> None:
        """Identifies global variables from the symbol table."""
        self.program_global_vars = {}
        
        # Access the global scope (first scope in the stack, typically depth 0 in SymbolTable)
        # The ASMGenerator logic then checks for entry.depth == 1 for its definition of global.
        if not self.symbol_table._scope_stack:
            self.logger.warning("Symbol table scope stack is empty. Cannot collect global variables.")
            return

        global_scope_symbols = self.symbol_table._scope_stack[0]

        for name, entry in global_scope_symbols.items():
            # The ASMGenerator's existing logic expects global vars to be at depth 1.
            # The SymbolTable itself considers the first scope (index 0) to be depth 0.
            # We rely on the entry.depth assigned during parsing and symbol insertion.
            if entry.depth == 1:
                if entry.entry_type not in [EntryType.PROCEDURE, EntryType.FUNCTION]:
                    is_mapped_string_const = (
                        entry.entry_type == EntryType.CONSTANT and 
                        entry.name in self.string_literals_map
                    )
                    if not is_mapped_string_const:
                        self.program_global_vars[entry.name] = entry
                        self.logger.debug(f"Collected global variable: {entry.name} (depth {entry.depth})")
        self.logger.info(f"Collected {len(self.program_global_vars)} global variable(s).")

    def _generate_data_segment(self) -> List[str]:
        """Generates the .DATA segment assembly lines."""
        asm_lines: List[str] = []
        asm_lines.append(".DATA")

        # Add global variable declarations
        # Sort for consistent output, useful for testing
        sorted_global_var_names = sorted(self.program_global_vars.keys())

        for var_name in sorted_global_var_names:
            entry = self.program_global_vars[var_name]
            asm_name = "cc" if entry.name == "c" else entry.name
            # Assuming all globals are WORD for now, adjust if type info is available and used
            asm_lines.append(f"    {asm_name:<8} DW ?") 
            self.logger.debug(f"Added global var to .DATA: {asm_name} DW ?")

        # Add string literal declarations from the map
        # Sort for consistent output
        sorted_string_labels = sorted(self.string_literals_map.keys())

        for label in sorted_string_labels:
            raw_string_value = self.string_literals_map[label]
            # Ensure '$' termination for io.asm compatibility as per memory e4fda710-5186-4fb9-9a64-456b481c9238
            # Escape special characters in string for ASM, e.g., double quotes if string contains them.
            # For simple strings without quotes, this is okay.
            # If string can contain quotes, they need to be doubled or use alternate delimiters.
            # Assuming simple strings for now.
            if not raw_string_value.endswith('$'):
                 processed_string_value = raw_string_value + "$"
            else:
                 processed_string_value = raw_string_value
            
            # Replace special ASM characters like ' with '' if needed, or use different quotes
            # MASM allows strings in single or double quotes. If a string contains one type, use the other.
            # For "He said, ""Hi!""", use: DB 'He said, "Hi!"', '$'
            # For 'It''s mine', use: DB "It's mine", '$'
            # Simplest: assume strings don't contain the quote char used.
            # Let's use double quotes for the string content.
            if '"' in processed_string_value[:-1]: # Check raw string part
                # If raw string contains double quotes, try to use single quotes for ASM
                # or error out if it's too complex for this stage.
                # For now, simple assumption: strings don't contain double quotes.
                 self.logger.warning(f"String literal '{label}' contains double quotes. Assembly might be problematic.")
            
            asm_lines.append(f"    {label:<8} DB \"{processed_string_value}\"") 
            self.logger.debug(f"Added string literal to .DATA: {label} DB \"{processed_string_value}\"")
        
        if not self.program_global_vars and not self.string_literals_map:
            self.logger.info(".DATA segment is empty.")
            # Still return [.DATA] or an empty list if no data is preferred by assembler?
            # Most assemblers are fine with an empty .DATA segment declaration.

        return asm_lines

    def _generate_code_segment(self) -> List[str]:
        """Generates the .CODE segment assembly lines including all procedures."""
        asm_lines: List[str] = []
        asm_lines.append(".CODE")
        self.logger.info("Starting .CODE segment generation.")

        if not self._internal_grouped_tac:
            self.logger.error("No procedures found in TAC to generate code for (self._internal_grouped_tac is empty).")
            asm_lines.append("; ERROR: No procedures found in TAC to generate code for.")
            return asm_lines

        # Generate ASM for each procedure found in the TAC
        # The order might matter if there are specific dependencies or if the TAC generator
        # outputs them in a specific order (e.g., main last).
        # For now, iterate in the order they were parsed and stored.
        
        for proc_name, proc_tac_instructions in self._internal_grouped_tac.items():
            if not proc_tac_instructions:
                self.logger.warning(f"Procedure '{proc_name}' has no TAC instructions. Skipping ASM generation for it.")
                continue
            
            procedure_asm = self._generate_procedure_asm(proc_name, proc_tac_instructions)
            asm_lines.extend(procedure_asm)
            asm_lines.append("") # Add a blank line for readability between procedures

        self.logger.info("Finished .CODE segment generation.")
        return asm_lines

    def _generate_procedure_asm(self, proc_name: str, proc_tac_instructions: List[ParsedTACInstruction]) -> List[str]:
        """
        Generates assembly code for a single procedure.
        Args:
            proc_name: The name of the procedure.
            proc_tac_instructions: The list of TAC instructions for this procedure.
        Returns:
            A list of assembly instruction strings for the procedure.
        """
        asm_lines: List[str] = []
        
        proc_entry = self.symbol_table.get_procedure_definition(proc_name)
        if not proc_entry or proc_entry.entry_type not in [EntryType.PROCEDURE, EntryType.FUNCTION]:
            self.logger.error(f"Symbol table entry for procedure '{proc_name}' not found or not a procedure/function type using get_procedure_definition.")
            asm_lines.append(f"; ERROR: Procedure '{proc_name}' definition not found or invalid type.")
            return asm_lines

        self.current_procedure_context = proc_entry # CRITICAL: Set context for get_operand_asm
        self.logger.info(f"Generating ASM for procedure: {proc_name}")

        # Prologue (Handled by PROC_BEGIN/PROGRAM_START in mapper)
        # Epilogue (Handled by PROC_END in mapper)

        for instr in proc_tac_instructions:
            # Labels are handled first if they exist on a TAC line
            if instr.label:
                asm_lines.append(f"{instr.label}:")
                self.logger.debug(f"  Added label: {instr.label}")

            # Translate the TAC instruction using the mapper
            # The mapper's translate_XYZ methods will call back to get_operand_asm
            # which will use self.current_procedure_context set above.
            mapped_asm = self.instruction_mapper.translate(instr) # Polymorphic call to translate_OPCODE
            
            if mapped_asm:
                for asm_instr_line in mapped_asm:
                    # Add standard indentation for instructions within a procedure
                    # PROC/ENDP and labels are not indented by this logic here.
                    if not asm_instr_line.strip().endswith(":") and \
                       not asm_instr_line.upper().strip().startswith(proc_name.upper() + " PROC") and \
                       not asm_instr_line.upper().strip().startswith(proc_name.upper() + " ENDP"):
                        asm_lines.append(f"    {asm_instr_line}")
                    else:
                        asm_lines.append(asm_instr_line) # No indent for PROC, ENDP, labels
                self.logger.debug(f"  TAC Line {instr.line_number} ({instr.opcode}) -> ASM: {mapped_asm}")
            elif instr.opcode not in [TACOpcode.PROC_BEGIN, TACOpcode.PROC_END, TACOpcode.PROGRAM_START]: # These might return empty if handled by proc shell
                self.logger.warning(f"  TAC Line {instr.line_number} ({instr.opcode}) produced no ASM from mapper.")
        
        self.current_procedure_context = None # CRITICAL: Clear context after processing procedure
        self.logger.info(f"Finished generating ASM for procedure: {proc_name}")
        return asm_lines

    def _generate_dos_program_shell(self, user_main_proc_label: str) -> List[str]:
        """
        Generates the DOS program shell (model, stack, main proc, DS setup, call to user main, exit).
        Args:
            user_main_proc_label: The label of the user's main procedure to be called.
        Returns:
            A list of assembly instruction strings for the program shell.
        """
        asm_lines: List[str] = []

        asm_lines.append(".MODEL SMALL")
        asm_lines.append(".STACK 100H")
        asm_lines.append("") # Blank line for readability

        # Assuming io.asm is always needed or its inclusion is handled by user if specific.
        # For a general purpose generator, it's common to include it.
        # A more advanced check could see if any I/O TAC opcodes were used.
        asm_lines.append("INCLUDE io.asm")
        asm_lines.append("") # Blank line for readability

        # Data segment will be generated and inserted between shell and code by generate_asm()

        # Code segment starts here, but the actual .CODE directive is added by _generate_code_segment
        # This shell focuses on the main procedure that sets up and calls the user's code.
        
        # Define the entry point procedure for the DOS program
        # This 'main' is the ASM entry point, not the user's Ada main procedure.
        # Let's call it 'start' to avoid confusion if user names their Ada main 'main'.
        asm_lines.append("start PROC")
        asm_lines.append("    ; Initialize DS")
        asm_lines.append("    MOV AX, @DATA")
        asm_lines.append("    MOV DS, AX")
        asm_lines.append("")
        asm_lines.append(f"    ; Call the user's main procedure: {user_main_proc_label}")
        asm_lines.append(f"    CALL {user_main_proc_label}")
        asm_lines.append("")
        asm_lines.append("    ; Exit program")
        asm_lines.append("    MOV AH, 4CH")
        asm_lines.append("    INT 21H")
        asm_lines.append("start ENDP")
        asm_lines.append("")

        # The END directive will specify the entry point 'start'.
        # This is typically the last line of the entire ASM file, handled by generate_asm().

        self.logger.info(f"Generated DOS program shell. Entry point: 'start', User main: '{user_main_proc_label}'.")
        return asm_lines

    def generate_asm(self) -> bool:
        """
        Main public method to generate the full ASM file.
        Orchestrates parsing, data/code segment generation, and shell creation.
        Returns True on success, False on failure.
        """
        self.logger.info(f"Starting ASM generation for TAC file: {self.tac_filepath}")

        # 1. Parse TAC and prepare procedure groupings
        if not self._parse_and_prepare():
            self.logger.error("ASM generation failed during TAC parsing and preparation phase.")
            return False
        self.logger.info("TAC parsing and preparation successful.")

        # 2. Collect global variables
        self._collect_global_vars()
        self.logger.info("Global variable collection successful.")

        # 3. Generate the DOS program shell (MODEL, STACK, INCLUDE io.asm, main ASM entry 'start')
        #    This 'start' proc will call the user's main Ada procedure.
        if not self.user_main_procedure_name:
            self.logger.error("Cannot generate DOS shell: User main procedure name not identified from PROGRAM_START.")
            return False
        
        # Ensure the user_main_procedure_name is a valid symbol table entry for a procedure
        self.logger.info(f"Diag: Looking up main procedure '{self.user_main_procedure_name}' in symbol table's persistent definitions.") # DIAGNOSTIC
        main_proc_entry = self.symbol_table.get_procedure_definition(self.user_main_procedure_name)
        
        # --- Start Diagnostic Block ---
        if main_proc_entry:
            self.logger.info(f"Diag: main_proc_entry found: {main_proc_entry}")
            self.logger.info(f"Diag: main_proc_entry.entry_type: {main_proc_entry.entry_type} (id: {id(main_proc_entry.entry_type)})")
            self.logger.info(f"Diag: Literal EntryType.PROCEDURE: {EntryType.PROCEDURE} (id: {id(EntryType.PROCEDURE)})")
            self.logger.info(f"Diag: Literal EntryType.FUNCTION: {EntryType.FUNCTION} (id: {id(EntryType.FUNCTION)})")
            self.logger.info(f"Diag: Is main_proc_entry.entry_type == EntryType.PROCEDURE? {main_proc_entry.entry_type == EntryType.PROCEDURE}")
            self.logger.info(f"Diag: Is main_proc_entry.entry_type is EntryType.PROCEDURE? {main_proc_entry.entry_type is EntryType.PROCEDURE}")
            self.logger.info(f"Diag: Is main_proc_entry.entry_type in [EntryType.PROCEDURE, EntryType.FUNCTION]? {main_proc_entry.entry_type in [EntryType.PROCEDURE, EntryType.FUNCTION]}")
        else:
            self.logger.info("Diag: main_proc_entry is None after get_procedure_definition.")
        # --- End Diagnostic Block ---

        if not main_proc_entry or main_proc_entry.entry_type not in [EntryType.PROCEDURE, EntryType.FUNCTION]:
            self.logger.error(f"User main procedure '{self.user_main_procedure_name}' not found in symbol table (get_procedure_definition) or is not a procedure/function.")
            return False
        
        dos_shell_asm = self._generate_dos_program_shell(self.user_main_procedure_name)
        self.logger.info("DOS program shell generation successful.")

        # 4. Generate .DATA segment (Global variables, String literals)
        data_segment_asm = self._generate_data_segment()
        self.logger.info(".DATA segment generation successful.")

        # 5. Generate .CODE segment (All procedures including user_main_procedure_name)
        code_segment_asm = self._generate_code_segment()
        self.logger.info(".CODE segment generation successful.")

        # 6. Assemble all parts and write to file
        final_asm_lines: List[str] = []
        final_asm_lines.extend(dos_shell_asm)       # .MODEL, .STACK, INCLUDE, start PROC...ENDP
        final_asm_lines.extend(data_segment_asm)    # .DATA, global vars, string literals
        final_asm_lines.extend(code_segment_asm)    # .CODE, all user procedures

        # Add the final END directive, pointing to the 'start' procedure from the DOS shell
        final_asm_lines.append("END start")

        try:
            with open(self.asm_filepath, 'w', encoding='utf-8') as f:
                for line in final_asm_lines:
                    f.write(line + "\n") # Corrected newline character
            self.logger.info(f"ASM file successfully written to: {self.asm_filepath}")
            return True
        except IOError as e:
            self.logger.error(f"Failed to write ASM file '{self.asm_filepath}': {e}")
            return False

    # --- Utility or Helper Methods (Example - can be expanded) ---
    # Potentially, methods for error reporting formatting, etc.

    def is_immediate(self, operand_asm_string: str) -> bool:
        """Checks if the ASM operand string represents an immediate value."""
        if not operand_asm_string:
            return False
        try:
            int(operand_asm_string) # Check for decimal
            return True
        except ValueError:
            try:
                int(operand_asm_string, 16) # Check for hex (e.g., "0FFH")
                if operand_asm_string.upper().endswith("H"):
                    return True
            except ValueError:
                # Check for character literal like 'A'
                if len(operand_asm_string) == 3 and operand_asm_string.startswith("'") and operand_asm_string.endswith("'"):
                    return True
                # Could add checks for binary, octal if needed
                return False
        return False # Should be caught by try-except

    def is_register(self, operand_asm_string: str) -> bool:
        """Checks if the ASM operand string is a known register."""
        if not operand_asm_string:
            return False
        # Common 8086 registers
        regs = {
            "AX", "BX", "CX", "DX", "SI", "DI", "SP", "BP",
            "AL", "AH", "BL", "BH", "CL", "CH", "DL", "DH",
            "CS", "DS", "ES", "SS" # Segment registers (less common as operands in this context)
        }
        return operand_asm_string.upper() in regs

    # We have to handle string labels like _S0 correctly
    # by returning "OFFSET _S0" when the context implies an address is needed (e.g. for WRS).
    # Example snippet for get_operand_asm related to string labels:
    #
    # if tac_operand.startswith("_S") and tac_operand[2:].isdigit():
    #     # For WRS, or if explicitly needing an address (e.g. PUSH @mystring)
    #     if instruction_opcode == TACOpcode.WRITE_STR or \
    #        (instruction_opcode == TACOpcode.PUSH and tac_operand_obj.is_address_of): # Assuming TACOperand object passed
    #         return f"OFFSET {tac_operand}"
    #     # If it's a string constant assigned to a variable, it might just be the label
    #     # or its value depending on how you manage constants.
    #     # For now, this is a simplified check.
    #     # If _S0 is used in an expression like X = _S0, it's more complex.
    #     # This code assumes _S0 is primarily for WRS.