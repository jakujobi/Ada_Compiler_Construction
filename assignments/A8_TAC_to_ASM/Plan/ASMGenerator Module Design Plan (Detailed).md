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

* **File:** `tac_instruction.py`
* **Purpose:** A structured container for a single parsed TAC instruction line.
* **Implementation:** Python `@dataclass` (`ParsedTACInstruction`)
* **Attributes (matching `ParsedTACInstruction`):**
  * `line_number: int` (For error reporting)
  * `raw_line: str` (Original raw line from TAC file)
  * `label: Optional[str]` (Optional label associated with the instruction, e.g., "L1")
  * `opcode: Union[TACOpcode, str]` (The operation, preferably `TACOpcode` enum)
  * `destination: Optional[TACOperand]` (e.g., for `ASSIGN`, `READ_INT`, jump targets)
  * `operand1: Optional[TACOperand]` (e.g., for `ASSIGN`, binary ops, `WRITE_INT`, `PARAM`)
  * `operand2: Optional[TACOperand]` (e.g., for binary ops, `CALL` num_params)
* **Methods:**
  * `__init__` (as defined in `ParsedTACInstruction`)
  * `@staticmethod TACOpcode.from_string(s: str) -> TACOpcode`: Used by parser to map string opcodes.
  * The parsing logic itself (`from_tac_line`) resides in `TACParser.py`.
    * **Crucial Parsing Aspects (handled by `TACParser`):**
      1. Strip leading/trailing whitespace, handle comments.
      2. Extract leading labels (e.g., `L1:`).
      3. Split remaining string into components based on observed TAC format.
      4. Identify opcode string, convert to `TACOpcode` enum.
      5. Map remaining components to `destination`, `operand1`, `operand2` as `TACOperand` objects, based on the opcode.
      6. Handle instructions with varying numbers of operands.

### **2.2. TACParser Class**

* **File:** `tac_parser.py`
* **Purpose:** Read the entire .tac file and produce a list of `ParsedTACInstruction` objects.
* **Attributes:**
  * tac_filepath: str
* **Methods:**
  * ``__init__``(self, tac_filepath: str): Stores file path.
  * parse(self) -> List[ParsedTACInstruction]:
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

* **File:** `data_segment_manager.py`
* **Purpose:** Collect definitions for the .data segment (globals, strings) by analyzing the symbol table and the provided string literals map. Generate the final .data section assembly code.
* **Attributes:**
  * `symbol_table: SymbolTable`
  * `global_vars: Dict[str, Symbol]` (Stores unique global variable Symbols of depth 1)
  * `string_literals_map: Dict[str, str]` (Provided map: label like _S0 to raw string value like "Prompt")
* **Methods:**
  * `__init__(self, symbol_table: SymbolTable, string_literals_map: Dict[str, str])`: Stores references.
  * `collect_definitions(self)`: (Renamed from `collect_definitions_from_tac` in actual code for simplicity here)
    * **Action:**
      1. Iterate through `self.symbol_table` for entries with `depth == 1` and `entry_type == EntryType.VARIABLE` (or other global data types). Add to `self.global_vars`.
      2. String literals are already provided via `self.string_literals_map`.
  * `get_data_section_asm(self) -> List[str]:`
    * **Action:**
      1. Initialize `asm_lines = [".DATA"]`.
      2. For `var_name`, `symbol_entry` in sorted `self.global_vars.items()`:
         * Handle `c` -> `cc` rename if `var_name == 'c'`.
         * Append `f"    {renamed_var_name:<8} DW ?"`.
      3. For `label`, `raw_value` in sorted `self.string_literals_map.items()`:
         * Append `f"    {label:<8} DB \"{raw_value}$\""`. (Ensures `$` termination)

### **2.4. ASMOperandFormatter Class**

* **File:** `asm_operand_formatter.py`
* **Purpose:** The critical translator for converting a single TAC operand string into its final 8086 assembly representation.
* **Attributes:**
  * `symbol_table: SymbolTable`
* **Methods:**
  * `__init__(self, symbol_table: SymbolTable)`: Stores symbol table reference.
  * `format_operand(self, tac_operand: Optional[str], context_opcode: Optional[TACOpcode] = None) -> str:`
    * **Input:** TAC operand string, optional `TACOpcode` for context (e.g., `WRITE_STR`).
    * **Action (Detailed Logic):**
      1. **Handle None/Empty:** If tac_operand is None or empty, return empty string or raise error.
      2. **Immediate Check:** Use try-except or regex to check if tac_operand is an integer literal. If yes, return it as a string.
      3. **BP-Relative Check:** Handles if `tac_operand` is already `[bp+/-X]`.
      4. **String Label Check:** If `tac_operand` matches `_S<num>`:
         * If `context_opcode == TACOpcode.WRITE_STR`, return `f"OFFSET {tac_operand}"`.
         * Else, return `tac_operand` (as other contexts might need just the label).
      5. **Identifier/Temp Lookup:** (Using `symbol_table.lookup`)
         * Apply `c` -> `cc` rename.
         * If `entry.depth == 1` (Global): Return name.
         * If `entry.depth >= 2` (Local/Param/Temp):
           * Retrieve `offset`, `entry_type == EntryType.PARAMETER`.
           * **Translate Internal Offset to 8086 Offset:**
             * If parameter: `asm_offset = internal_offset + 4`. (e.g., internal offset 0 is `[bp+4]`)
             * Else (local/temp): `asm_offset = -(internal_offset + 2)`. (e.g., internal offset 0 is `[bp-2]`)
           * Return formatted `f"[bp{sign}{asm_offset}]"`.
      6. **Error:** If lookup fails or type is unexpected, raise an informative error including the tac_operand and line_number (if available).
    * **Output:** The assembly operand string (e.g., "10", "[bp-4]", "[bp+6]", "myGlobal", "OFFSET _S0", "cc").

### **2.5. ASMInstructionMapper Class**

* **File:** `asm_instruction_mapper.py`
* **Purpose:** Provides the specific 8086 assembly instruction sequences (templates) for each TAC opcode.
* **Attributes:**
  * `symbol_table: SymbolTable`
  * `formatter: ASMOperandFormatter`
  * `generator: ASMGenerator` (or its relevant helper methods/properties, for `is_immediate`, `is_param_address`, etc.)
* **Methods:**
  * `__init__(self, symbol_table: SymbolTable, logger_instance: Logger, asm_generator_instance: ASMGenerator)`: Initializes attributes, including `self.formatter`.
  * **`translate_*(self, instr: ParsedTACInstruction) -> List[str]:`** (One per opcode, takes `ParsedTACInstruction`)
    * Operands are accessed from `instr.destination`, `instr.operand1`, `instr.operand2`.
    * Formatting uses `self.formatter.format_operand(str(operand.value), instr.opcode)`.
    * **`_translate_assign`:** (Conceptual) `mov ax, formatted_src; mov formatted_dest, ax`. Actual implementation in `DataMovTranslators` handles dereferencing for ref params (using `_is_param_address` helper from `generator` and `bx`) and mem-to-mem.
    * **`_translate_add`, `_translate_mul`:** (Conceptual) `mov ax, op1; op ax, op2; mov dest, ax`. Actual implementation in `ArithmeticTranslators` handles dereferencing.
    * **`_translate_proc_begin` (for `PROC_BEGIN Name`):**
      * `proc_name = instr.destination.value`
      * `proc_info = self.symbol_table.lookup_globally(proc_name)`
      * `size_locals = proc_info.total_locals_size` (Must include temps)
      * Return `[f"{proc_name} PROC NEAR", "PUSH BP", "MOV BP, SP", f"SUB SP, {size_locals}"]` (if size_locals > 0)
    * **`_translate_proc_end` (for `PROC_END Name`):**
      * `proc_name = instr.destination.value`
      * `proc_info = self.symbol_table.lookup_globally(proc_name)`
      * `size_locals = proc_info.total_locals_size`
      * `size_params_bytes = proc_info.total_params_size`
      * Return `["MOV SP, BP" (if size_locals > 0), "POP BP", f"RET {size_params_bytes}", f"{proc_name} ENDP"]`
    * **`_translate_call` (for `CALL ProcName, NumParams`):**
      * `proc_name = instr.operand1.value`
      * `num_params_val = int(instr.operand2.value)`
      * Assembly: `CALL {proc_name}` followed by `ADD SP, {num_params_val * 2}` if `num_params_val > 0`.
    * **`_translate_param` (for `PARAM Operand`):**
        * `param_operand_str = str(instr.operand1.value)`
        * `is_address_of = instr.operand1.is_address_of`
        * If `is_address_of`:
            * Look up `param_operand_str`. If global: `push OFFSET {global_name}`.
            * If local: `lea ax, {formatted_local_addr}; push ax`.
        * Else (pass by value):
            * `value_op_asm = self.formatter.format_operand(param_operand_str, instr.opcode)`
            * `push {value_op_asm}` (Direct push of value/memory location).
    * **`_translate_write_str` (for `WRITE_STR Label`):**
      * `label_op = self.formatter.format_operand(str(instr.operand1.value), instr.opcode)` (should return "OFFSET _S0")
      * Return `[f"MOV DX, {label_op}", "CALL writestr"]`
    * **`_translate_write_int` (for `WRITE_INT Value`):**
      * `value_asm = self.formatter.format_operand(str(instr.operand1.value), instr.opcode)`
      * Return `[f"MOV AX, {value_asm}", "CALL writeint"]` (Value in `AX`)
    * **`_translate_read_int` (for `READ_INT Dest`):**
      * `dest_asm = self.formatter.format_operand(str(instr.destination.value), instr.opcode)`
      * Return `["CALL readint", f"MOV {dest_asm}, BX"]` (Result from `BX`)
    * **`_translate_write_newline` (for `WRITE_NEWLINE`):**
      * Return `["CALL writeln"]`

### **2.6. ASMGenerator Class (Orchestrator)**

* **File:** `asm_generator.py`
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
         * Handles labels (e.g., `code_lines.append(f"{instr.label}:")` if `instr.label` exists).
         * Handles `PROGRAM_START` (stores `instr.destination.value` in `self.user_main_procedure_name`).
         * Handles `PROC_BEGIN` (sets `current_procedure_context`, calls `mapper._translate_proc_begin`).
         * Handles `PROC_END` (calls `mapper._translate_proc_end`, clears `current_procedure_context`).
         * For all other opcodes, calls `self.instruction_mapper.translate(instr)`. Appends results to `code_lines`.
      7. Calls `self._generate_dos_program_shell()` to get main ASM entry.
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
    * Includes a crucial helper method `get_operand_asm` (now `ASMOperandFormatter.format_operand`) to translate TAC operands into their correct assembly address string.
    * (Ref: `A8_Refined_Recommendations.md` - Point E)

4. **Interaction with `ASMInstructionMapper`:**
    * `ASMGenerator` iterates through parsed TAC instructions (`ParsedTACInstruction` objects).
    * For each `ParsedTACInstruction`, it invokes the appropriate mapping method on an `ASMInstructionMapper` instance.
    * `ASMInstructionMapper` returns a list of ASM instruction strings, which `ASMGenerator` appends to the `.code` segment output.
    * `ASMGenerator` receives a map of string labels to string values (e.g., `{"_S0": "Hello"}` - raw value without `$`) from its caller (`JohnA8.py`).
    * It uses this map (passing it to `DataSegmentManager`) to generate `DB` directives in the `.data` segment (e.g., `_S0 DB "Hello$"` - `$` added during generation).
    * (Ref: `A8_Refined_Recommendations.md` - Point G)
