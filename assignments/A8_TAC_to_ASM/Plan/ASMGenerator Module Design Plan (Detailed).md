# **ASMGenerator Module Design Plan (Detailed - Assignment 8)**

## **1. Overview**

This document provides a detailed plan for the 8086 assembly code generation module (ASMGenerator) and its sub-components. It elaborates on the responsibilities, interactions, and implementation details for each part, building upon the initial design.

**Input:**

* A .tac file (output of A7 + A8 I/O extensions).
* A populated SymbolTable object instance (from previous phases).

**Output:**

* A .asm file (MASM/TASM compatible, runnable in DOSBox).

**Core Strategy:**

* **Two-pass approach** orchestrated by ASMGenerator.
* **Modular Design:** Split into TACInstruction, TACParser, DataSegmentManager, ASMOperandFormatter, ASMInstructionMapper, and ASMGenerator.

## **2. Component Details (Expanded)**

### **2.1. TACInstruction (Data Class)**

* **File:** tac_instruction.py
* **Purpose:** A structured container for a single parsed TAC instruction line.
* **Implementation:** Python @dataclass recommended for simplicity and type hinting.
* **Attributes:**
  * line_number: int (For error reporting)
  * label: Optional[str] = None (e.g., "L1")
  * opcode: Optional[str] = None (e.g., "ASSIGN", "ADD", "WRS", "PROC")
  * op1: Optional[str] = None (Source operand 1 / Address / Label)
  * op2: Optional[str] = None (Source operand 2)
  * dest: Optional[str] = None (Destination operand / Procedure Name)
* **Methods:**
  * ``__init__``(self, line_number: int, label: Optional[str] = None, opcode: Optional[str] = None, op1: Optional[str] = None, op2: Optional[str] = None, dest: Optional[str] = None)
  * @staticmethod from_tac_line(line: str, line_num: int) -> 'TACInstruction':
    * **Input:** Raw string line from .tac, line number.
    * **Action:**
      1. Strip leading/trailing whitespace. Ignore empty lines or comment lines (if any defined).
      2. Check for and extract a leading label (e.g., L1:). Store label without the colon.
      3. **(Crucial!)** Based on the **actual, observed format** of your A7 TAC output (delimiters, operand order), split the remaining string into components.
      4. Identify the opcode (usually the first component after the label, or the first component if no label).
      5. Map the remaining components to op1, op2, dest based on the *known format* of the specific opcode. Define expected patterns clearly (e.g., for `dest = op1 op op2`, order might be dest, op1, op2 after `=`; for `wrs Label`, just op1=Label; for `proc Name`, dest=Name).
      6. Handle instructions with varying numbers of operands gracefully (e.g., `wrln` has none, `push @Var` has one, `add` has three).
    * **Output:** Populated TACInstruction instance. Raise an error for unparseable lines.

### **2.2. TACParser Class**

* **File:** tac_parser.py
* **Purpose:** Read the entire .tac file and produce a list of TACInstruction objects.
* **Attributes:**
  * tac_filepath: str
* **Methods:**
  * ``__init__``(self, tac_filepath: str): Stores file path.
  * parse(self) -> List[TACInstruction]:
    * **Action:**
      1. Open tac_filepath for reading. Handle FileNotFoundError.
      2. Initialize an empty list instructions.
      3. Read the file line by line, keeping track of line_number.
      4. For each non-empty line, call TACInstruction.from_tac_line(line, line_number).
      5. Append the resulting TACInstruction object to the instructions list.
      6. Handle potential parsing errors from from_tac_line.
      7. Close the file.
    * **Output:** The complete list of TACInstruction objects representing the program.

### **2.3. DataSegmentManager Class**

* **File:** data_segment_manager.py
* **Purpose:** Collect definitions for the .data segment (globals, strings) by analyzing the TAC and symbol table. Generate the final .data section assembly code.
* **Attributes:**
  * symbol_table: SymbolTable
  * global_vars: Set[str] (Stores unique lexemes of depth 1 variables)
  * string_literals: Dict[str, str] (Maps label like _S0 to string value like "Prompt$")
* **Methods:**
  * ``__init__``(self, symbol_table: SymbolTable): Stores symbol_table, initializes empty global_vars set and string_literals dict.
  * collect_definitions(self, instructions: List[TACInstruction]):
    * **Input:** List of all TACInstruction objects.
    * **Action:**
      1. Iterate through instructions.
      2. For each operand (op1, op2, dest) that is not None and looks like an identifier (not immediate, not [bp...], not _S...):
         * entry = self.symbol_table.lookup(operand) (Need context if names can be reused across scopes, but globals should be unique).
         * If entry found and entry.depth == 1 and it's a variable (not procedure name): Add entry.lexeme to self.global_vars.
      3. If instr.opcode == 'wrs' (or equivalent):
         * Assume instr.op1 is the string label (e.g., _S0).
         * entry = self.symbol_table.lookup(instr.op1)
         * If entry found and represents a stored string literal:
           * Retrieve the actual string value (e.g., from entry.value).
           * Ensure the value includes the $ terminator (this should ideally be added when stored in SymTable during TAC generation).
           * Store self.string_literals[instr.op1] = entry.value.
         * Else: Raise an error (string label not found in symbol table).
  * get_data_section_asm(self) -> List[str]:
    * **Action:**
      1. Initialize asm_lines = [".data"].
      2. For var_name in sorted(list(self.global_vars)): (Sorting provides consistent output order)
         * Handle potential c -> cc rename if needed based on the stored lexeme.
         * Append f" {renamed_var_name:<8} DW ?".
      3. For label, value in sorted(self.string_literals.items()):
         * Append f"{label:<8} DB \"{value}\"".
    * **Output:** List of assembly lines for the .data section.

### **2.4. ASMOperandFormatter Class**

* **File:** asm_operand_formatter.py
* **Purpose:** The critical translator for converting a single TAC operand string into its final 8086 assembly representation.
* **Attributes:**
  * symbol_table: SymbolTable
* **Methods:**
  * ``__init__``(self, symbol_table: SymbolTable): Stores symbol table reference.
  * format_operand(self, tac_operand: str, current_proc_name: Optional[str] = None) -> str:
    * **Input:** TAC operand string, optional name of the procedure currently being processed (for scoped lookups).
    * **Action (Detailed Logic):**
      1. **Handle None/Empty:** If tac_operand is None or empty, return empty string or raise error.
      2. **Immediate Check:** Use try-except or regex to check if tac_operand is an integer literal. If yes, return it as a string.
      3. **BP-Relative Check:** Check if tac_operand starts with "[bp" (or _bp if that's the TAC format). If yes:
         * *If TAC uses internal offsets (e.g., _bp+0, _bp+2):* Parse the offset value. Look up the operand name (if needed, might not be present in TAC) or use context to determine if it was a parameter. Calculate the final offset (e.g., local 0 -> -2, param 2 -> +6). Return formatted f"[bp{sign}{offset}]".
         * *If TAC already uses final offsets (e.g., [bp-2], [bp+6]):* Validate the format and return it directly.
         * **Decision:** Assume TAC uses an internal representation like _bp+Offset or just the variable name, requiring lookup and translation here.
      4. **String Label Check:** If tac_operand matches the string label pattern (e.g., `_S` followed by a number): Return f"OFFSET {tac_operand}".
      5. **Identifier/Temp Lookup:** If none of the above, assume it's a variable or temporary name.
         * entry = self.symbol_table.lookup(tac_operand, context=current_proc_name) (Handle KeyError or equivalent if not found).
         * Apply c -> cc rename if entry.lexeme == 'c'. Store the potentially renamed lexeme.
         * If entry.depth == 1: Return the (potentially renamed) entry.lexeme.
         * If entry.depth >= 2:
           * Retrieve offset = entry.offset and is_param = entry.isParameter.
           * **Translate Internal Offset to 8086 Offset:**
             * *(Verify!)* Cross-reference your specific stack frame documentation (`Notes/Semantic Analysis.md`, `Notes/Symbol Tables.md`) for exact layout.
             * If is_param: asm_offset = offset + 4 (Assuming internal param offsets start at 0, first param is at [bp+4] after RetAddr(+2) and OldBP(+0)). Example: offset 0 -> +4, offset 2 -> +6.
             * Else (local/temp): asm_offset = -(offset + 2) (Assuming internal local/temp offsets start at 0, first local is at [bp-2] after OldBP(+0)). Example: offset 0 -> -2, offset 2 -> -4.
           * Return formatted f"[bp{'+' if asm_offset > 0 else ''}{asm_offset}]".
      6. **Error:** If lookup fails or type is unexpected, raise an informative error including the tac_operand and line_number (if available).
    * **Output:** The assembly operand string (e.g., "10", "[bp-4]", "[bp+6]", "myGlobal", "OFFSET _S0", "cc").

### **2.5. ASMInstructionMapper Class**

* **File:** asm_instruction_mapper.py
* **Purpose:** Provides the specific 8086 assembly instruction sequences (templates) for each TAC opcode.
* **Attributes:**
  * symbol_table: SymbolTable
* **Methods:**
  * ``__init__``(self, symbol_table: SymbolTable): Stores symbol table reference.
  * **translate_*(self, instr: TACInstruction, formatter: ASMOperandFormatter) -> List[str]:** (One per opcode)
    * **translate_assign(self, instr, formatter):**
      * dest = formatter.format_operand(instr.dest, ...)
      * src = formatter.format_operand(instr.op1, ...)
      * Return [f" mov ax, {src}", f" mov {dest}, ax"] (Handle potential immediate source differently if needed: mov {dest}, {src}).
      * **Note on Dereferencing:** If `dest` corresponds to a reference parameter (e.g., looks like `[bp+N]` from formatter), the sequence should be: `mov bx, dest_address_from_[bp+N]; mov ax, src; mov [bx], ax`. Similarly, if `src` is a reference parameter: `mov bx, src_address_from_[bp+N]; mov ax, [bx]; mov dest, ax`.
    * **translate_add(self, instr, formatter):**
      * dest = formatter.format_operand(instr.dest, ...)
      * op1 = formatter.format_operand(instr.op1, ...)
      * op2 = formatter.format_operand(instr.op2, ...)
      * Return [f" mov ax, {op1}", f" add ax, {op2}", f" mov {dest}, ax"]
      * **Note on Dereferencing:** Similar logic applies if operands or destination are reference parameters (load address to BX, use `[bx]` for operation, store result via `[bx]` if dest is reference).
    * **translate_mul(self, instr, formatter):** (Similar to add, using mov bx, op2, imul bx, apply dereferencing logic)
    * **translate_proc(self, instr, formatter):**
      * proc_name = instr.dest
      * proc_info = self.symbol_table.lookup(proc_name)
      * size_locals = proc_info.size_of_locals
      * Return [f"{proc_name} PROC", f" push bp", f" mov bp, sp", f" sub sp, {size_locals}"]
    * **translate_endp(self, instr, formatter):**
      * proc_name = instr.dest
      * proc_info = self.symbol_table.lookup(proc_name)
      * size_locals = proc_info.size_of_locals
      * size_params = proc_info.size_of_params
      * Return [f" add sp, {size_locals}", f" pop bp", f" ret {size_params}", f"{proc_name} ENDP"]
    * **translate_call(self, instr, formatter):**
      * proc_name = instr.dest (or op1 depending on TAC format)
      * Return [f" call {proc_name}"]
    * **translate_push(self, instr, formatter):** (Pass by Value)
      * value_op = formatter.format_operand(instr.op1, ...)
      * Return [f" mov ax, {value_op}", f" push ax"] (Handle immediate push directly: push {value_op})
    * **translate_push_ref(self, instr, formatter):** (Pass by Reference)
      * var_name = instr.op1 # Assumes op1 is the variable *name* before formatting
      * address_op = f"offset {var_name}" # Generate OFFSET format directly
      * Return [f" mov ax, {address_op}", f" push ax"]
    * **translate_wrs(self, instr, formatter):**
      * label_op = formatter.format_operand(instr.op1, ...) # Should return "OFFSET _S0"
      * Return [f" mov dx, {label_op}", f" call writestr"]
    * **translate_wri(self, instr, formatter):**
      * address_op = formatter.format_operand(instr.op1, ...) # e.g., "[bp-6]"
      * register = "dx" # **Confirm this from io.asm!** Assume DX for now.
      * Return [f" mov {register}, {address_op}", f" call writeint"]
    * **translate_rdi(self, instr, formatter):**
      * address_op = formatter.format_operand(instr.dest, ...) # e.g., "[bp-2]"
      * Return [f" call readint", f" mov {address_op}, bx"] # readint returns in BX
    * **translate_wrln(self, instr, formatter):**
      * Return [f" call writeln"]
    * *(Add methods for other ops like SUB, potentially control flow if needed)*

### **2.6. ASMGenerator Class (Orchestrator)**

* **File:** asm_generator.py
* **Purpose:** Coordinates the entire process, uses the other components.
* **Attributes:** As defined previously (paths, symbol table, instances of other components, start proc name).
* **Methods:**
  * ``__init__``(...): Initializes attributes and instantiates components.
  * generate_asm(self):
    * **Action:** Executes the two-pass strategy:
      1. Calls parser.parse() to get instructions.
      2. Calls data_manager.collect_definitions(instructions).
      3. Calls data_manager.get_data_section_asm() to get data_lines.
      4. Initializes code_lines = [].
      5. Sets current_proc_context = None.
      6. Iterates through instructions:
         * Handles labels (code_lines.append(f"{instr.label}:")).
         * Handles start directive (stores instr.op1 in self.start_proc_name).
         * Handles proc (sets current_proc_context, calls mapper.translate_proc).
         * Handles endp (calls mapper.translate_endp, clears current_proc_context).
         * For all other opcodes, looks up the appropriate mapper.translate_* method (e.g., using getattr or a dispatch dictionary) and calls it, passing instr and self.formatter. Appends results to code_lines.
      7. Calls self._generate_main_entry() to get main_lines.
      8. Assembles the final list of strings: Boilerplate + data_lines + .code + include io.asm + code_lines + main_lines + END main_label.
      9. Writes the result to self.asm_filepath.
  * _generate_main_entry(self) -> List[str]:
    * **Action:** Returns the list of strings for the standard main PROC block, ensuring call {self.start_proc_name} uses the name collected during the loop. Includes error handling if start_proc_name is missing.

## **3. Error Handling & Logging**

* Implement specific and informative error messages throughout all components (e.g., "Invalid TAC format on line {line_num}: {line}", "SymbolTable lookup failed for identifier '{operand}' in procedure '{proc_name}' during TAC line {line_num}", "Missing required procedure size information for '{proc_name}' in SymbolTable").
* Utilize the existing `Logger` for debug tracing and informational messages.

## Key Design Refinements (May 2025 Review)

This section details critical updates to the `ASMGenerator` module design and its interactions, based on the review and discussion on May 6th, 2025. For comprehensive details on each point, please refer to the **`A8_Refined_Recommendations.md`** document located in this same `Plan` directory.

These decisions clarify and, where conflicting, supersede prior design details within this document regarding:

1. **Assembly Memory Model (Implemented by `ASMGenerator`):**
    * **Parameters:** Accessed via `[BP+offset]` (e.g., `[BP+4]`). `ASMGenerator` calculates parameter block size for `RET` instruction.
    * **Local Variables & Compiler Temporaries (`_tN`):** Accessed via `[BP-offset]` (e.g., `[BP-2]`). `ASMGenerator` calculates total space for these to adjust `SP` in procedure prologue (`SUB SP, size`).
    * **Global Variables & String Literals:** Declared in the `.data` segment by `ASMGenerator`.
    * (Ref: `A8_Refined_Recommendations.md` - Point C)

2. **Register Allocation Strategy (Followed by `ASMInstructionMapper` and `ASMGenerator`):**
    * `AX` as primary accumulator/return value.
    * `BX` for secondary operands or general use.
    * `CX` for potential counters.
    * `DX` for multiplication/division overflow/remainder and string `OFFSET`s for `io.asm`.
    * Operations are generally load-compute-store, with no complex register state preservation across TAC instructions beyond what's necessary for a single TAC to ASM mapping.
    * (Ref: `A8_Refined_Recommendations.md` - Point D)

3. **`ASMGenerator` Core Responsibilities & Helpers:**
    * Orchestrates the entire TAC to ASM conversion process.
    * Manages construction of `.data` (globals, strings) and `.code` segments.
    * Generates full procedure prologues (including `PUSH BP; MOV BP, SP; SUB SP, <size>`) and epilogues (`MOV SP, BP; POP BP; RET <param_bytes>`).
    * Includes a crucial helper method: `get_operand_asm(tac_operand_str, current_procedure_symbol_table_entry)` to translate TAC operands (variables, temporaries, literals, `_BP` offsets) into their correct assembly address string (e.g., `var_label`, `[BP-4]`, `[BP+6]`, `123`). This requires access to symbol table information to determine scope and type.
    * (Ref: `A8_Refined_Recommendations.md` - Point E)

4. **Interaction with `ASMInstructionMapper`:**
    * `ASMGenerator` iterates through parsed TAC instructions.
    * For each `ParsedTACInstruction`, it invokes the appropriate mapping method on an `ASMInstructionMapper` instance.
    * `ASMInstructionMapper` returns a list of ASM instruction strings, which `ASMGenerator` appends to the `.code` segment output.
    * (Ref: `A8_Refined_Recommendations.md` - Point F)

5. **Handling of String Literals:**
    * `ASMGenerator` receives a map of string labels to string values (e.g., `{"_S0": "Hello"}`) from its caller (`JohnA8.py`).
    * It uses this map to generate `DB` directives in the `.data` segment (e.g., `_S0 DB "Hello",0`).
    * (Ref: `A8_Refined_Recommendations.md` - Point G)
