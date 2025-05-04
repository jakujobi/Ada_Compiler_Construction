# **ASMGenerator Module Design Plan (Detailed - Assignment 8)**

## **1. Overview**

This document provides a detailed plan for the 8086 assembly code generation module (`ASMGenerator`) and its sub-components. It elaborates on the responsibilities, interactions, and implementation details for each part, building upon the initial design.

**Input:**

*   A `List[Tuple]` representing the TAC instructions (from `TACGenerator.tac_lines`).
*   A `Dict[str, str]` mapping string labels to their values (from `TACGenerator.get_string_literals()`).
*   A populated `SymbolTable` object instance (from previous phases, containing final scope information, parameter modes, local/param sizes).

**Output:**

*   A `.asm` file (MASM/TASM compatible, runnable in DOSBox).

**Core Strategy:**

*   **Multi-pass approach** orchestrated by `ASMGenerator`.
    *   Pass 1 (or within `ASMGenerator` init): Analyze TAC to determine maximum temporary variable usage per procedure and update `SizeOfLocals` in the `SymbolTable`. Allocate specific stack offsets for temps.
    *   Pass 2: Generate `.data` segment content using `DataSegmentManager`.
    *   Pass 3: Generate `.code` segment content instruction by instruction using `ASMInstructionMapper` and `ASMOperandFormatter`.
*   **Modular Design:** Split into `TACInstruction`, `DataSegmentManager`, `ASMOperandFormatter`, `ASMInstructionMapper`, and `ASMGenerator`. (Removed `TACParser`).

## **2. Component Details (Expanded)**

### **2.1. TACInstruction (Data Class)**

*   **File:** `src/jakadac/asm_generator/tac_instruction.py`
*   **Purpose:** A structured container for a single TAC instruction, parsed from a TAC tuple.
*   **Implementation:** Python `@dataclass`.
*   **Attributes (Based on `from_tuple` implementation):**
    *   `opcode`: str (Normalized, lowercase opcode, e.g., "+", "assign", "proc", "not")
    *   `dest`: Optional\[str\] (Destination register/memory/temp/label)
    *   `op1`: Optional\[str\] (Source operand 1 / Address / Label / Procedure Name)
    *   `op2`: Optional\[str\] (Source operand 2)
    *   `original_tuple`: Optional\[Tuple\] (For debugging)
*   **Methods:**
    *   `@classmethod from_tuple(cls, tac_tuple: Tuple) -> 'TACInstruction'`:
        *   **Input:** Raw tuple from `TACGenerator.tac_lines`.
        *   **Action:** Parses the tuple based on the first element (opcode) and expected tuple structure for that opcode (e.g., binary ops, assignments, unary ops, calls, pushes, I/O). Populates the dataclass fields (`opcode`, `dest`, `op1`, `op2`). Normalizes opcodes (e.g., '=' becomes 'assign', '+' remains '+'). Handles errors for malformed tuples.
        *   **Output:** Populated `TACInstruction` instance.

### **2.2. DataSegmentManager Class**

*   **File:** `src/jakadac/asm_generator/data_segment_manager.py`
*   **Purpose:** Identify global variables from the SymbolTable. Generate the final `.data` section assembly code, including string literals.
*   **Attributes:**
    *   `symbol_table`: SymbolTable
    *   `global_vars`: Set\[str\] (Stores unique lexemes of depth 0 variables)
*   **Methods:**
    *   `__init__(self, symbol_table: SymbolTable)`: Stores symbol table, initializes `global_vars`.
    *   `collect_definitions(self)`:
        *   **Input:** None (uses stored `symbol_table`).
        *   **Action:**
            1.  Iterate through the global scope (depth 0) of the `symbol_table`.
            2.  For each `Symbol` that is an `EntryType.VARIABLE`, add its `name` to `self.global_vars`. (Handle potential `C` -> `CC` rename if necessary based on symbol info).
    *   `get_data_section_asm(self, string_literals: Dict[str, str]) -> List[str]`:
        *   **Input:** The `string_literals` dictionary (label -> value$) provided by the `ASMGenerator` (obtained from `TACGenerator`).
        *   **Action:**
            1.  Initialize `asm_lines = ["section .data"]`.
            2.  Add comment: `; --- String Literals ---`.
            3.  For `label`, `value` in `sorted(string_literals.items())`:
                *   Append formatted line, e.g., `f"{label:<8} db      \"{value}\""` (Ensure quotes are handled correctly if value contains them, though `TACGenerator` should have processed Ada escapes).
            4.  Add comment: `; --- Global Variables ---`.
            5.  For `var_name` in `sorted(list(self.global_vars))`:
                *   Lookup symbol details (like size) if needed for `DW`/`DB`/etc. (Assume `DW` for `Integer`).
                *   Append `f"{var_name:<8} dw      ?"`.
            6.  If no strings or globals, ensure section directive still exists.
        *   **Output:** List of assembly lines for the `.data` section.

### **2.3. ASMOperandFormatter Class**

*   **File:** `src/jakadac/asm_generator/asm_operand_formatter.py`
*   **Purpose:** Convert a TAC operand string (like '_BP-2', 'myGlobal', '_S0', '5', '_t1') into its final 8086 assembly representation (like '[bp-2]', 'myGlobal', '_S0', '5', '[bp-N]'). *Crucially relies on `getPlace` having done the initial symbol->offset/name mapping.*
*   **Attributes:**
    *   `temp_offsets`: Dict\[str, int\] (Maps temporary names like '_t1' to their assigned BP-relative offsets, e.g., -8. Populated by `ASMGenerator`).
*   **Methods:**
    *   `__init__(self, temp_offsets: Dict[str, int])`: Stores the map of temporary variable offsets.
    *   `format_operand(self, tac_operand: str) -> str`:
        *   **Input:** TAC operand string (output of `getPlace` or a literal).
        *   **Action (Simplified Logic):**
            1.  **Handle None/Empty:** Return empty string or raise error.
            2.  **Immediate Check:** Check if `tac_operand` is an integer/float literal. If yes, return as string.
            3.  **BP-Relative Check:** Check if `tac_operand` starts with `_BP+` or `_BP-`. If yes, parse the offset and return `[bp+{offset}]` or `[bp-{offset}]`.
            4.  **String Label Check:** Check if `tac_operand` starts with `_S`. If yes, return the label itself (e.g., `_S0`).
            5.  **Temporary Check:** Check if `tac_operand` starts with `_t`. If yes:
                *   Lookup the offset in `self.temp_offsets`.
                *   Return `[bp-{offset}]` (using the allocated negative offset).
                *   Handle error if temp not found in map.
            6.  **Identifier Check:** If none of the above, assume it's a global/enclosing variable name. Return `tac_operand` directly. (Handle potential `C` -> `CC` rename if needed, though this might be better handled when *generating* the TAC place string).
        *   **Output:** The assembly operand string (e.g., "10", "[bp-4]", "[bp+6]", "myGlobal", "_S0", "[bp-8]").

### **2.4. ASMInstructionMapper Class**

*   **File:** `src/jakadac/asm_generator/asm_instruction_mapper.py`
*   **Purpose:** Provides the specific 8086 assembly instruction sequences (templates) for each TAC opcode, handling operand formatting and dereferencing.
*   **Attributes:**
    *   `formatter`: ASMOperandFormatter (Instance passed during init)
    *   `symbol_table`: SymbolTable (Needed for procedure sizes)
*   **Methods:**
    *   `__init__(self, formatter: ASMOperandFormatter, symbol_table: SymbolTable)`: Stores formatter and symbol table.
    *   **`translate(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:** (Main dispatch method)
        *   Calls the appropriate `_translate_*` method based on `instr.opcode`.
        *   Prepends a comment `"; -- {original TAC tuple} --"` for readability.
    *   **`_translate_assign(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `dest_asm = self.formatter.format_operand(instr.dest)`
        *   `src_asm = self.formatter.format_operand(instr.op1)`
        *   **Dereference Logic:**
            *   If `src_asm` is `[bp+N]` (param by ref): `mov bx, {src_asm} ; mov ax, [bx]` (source value is now in AX)
            *   Else: `mov ax, {src_asm}` (handle immediate `mov ax, {value}` directly if possible)
            *   If `dest_asm` is `[bp+N]` (param by ref): `mov bx, {dest_asm} ; mov [bx], ax`
            *   Else: `mov {dest_asm}, ax`
        *   Return the sequence of ASM instructions.
    *   **`_translate_binary_op(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:** (Handles +, -, *, / etc.)
        *   `dest_asm = self.formatter.format_operand(instr.dest)`
        *   `op1_asm = self.formatter.format_operand(instr.op1)`
        *   `op2_asm = self.formatter.format_operand(instr.op2)`
        *   ASM Sequence (e.g., for ADD):
            *   Load op1 into AX (handle `[bp+N]` dereference for op1: `mov bx, {op1_asm}; mov ax, [bx]`).
            *   Load op2 into BX (handle `[bp+N]` dereference for op2: `mov cx, {op2_asm}; mov bx, [cx]`). Handle immediate op2 directly in ADD/SUB if possible.
            *   Perform operation: `add ax, bx` (or `add ax, {immediate}` or `sub ax, bx` etc.).
            *   Store result from AX to dest (handle `[bp+N]` dereference for dest: `mov bx, {dest_asm}; mov [bx], ax`).
        *   Return ASM sequence. (Handle `MUL`/`DIV` specifics with DX).
    *   **`_translate_unary_op(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:** (Handles `not`, `-` (negation))
        *   `dest_asm = self.formatter.format_operand(instr.dest)`
        *   `op1_asm = self.formatter.format_operand(instr.op1)` # Source operand
        *   ASM Sequence (e.g., for NEG):
            *   Load op1 into AX (handle `[bp+N]` dereference).
            *   `neg ax`
            *   Store result from AX to dest (handle `[bp+N]` dereference).
        *   Return ASM sequence.
    *   **`_translate_proc(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `proc_name = instr.op1`
        *   Lookup `proc_symbol = self.symbol_table.lookup(proc_name)`. Handle error.
        *   `size_locals = proc_symbol.local_size` (Should include space for temps now).
        *   Return `[f"{proc_name}:", f" push bp", f" mov bp, sp", f" sub sp, {size_locals}"]`
    *   **`_translate_endp(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `proc_name = instr.op1`
        *   Lookup `proc_symbol = self.symbol_table.lookup(proc_name)`. Handle error.
        *   `size_params = proc_symbol.param_size`
        *   Return `[f" mov sp, bp", f" pop bp", f" ret {size_params}"]` # Note: Procedure label `ENDP` not used in NASM
    *   **`_translate_call(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `proc_name = instr.op1`
        *   Return `[f" call {proc_name}"]`
    *   **`_translate_push(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `operand = instr.op1` # This is the string from TAC tuple (e.g., "var", "@var", "_BP-2", "@_BP-2")
        *   If operand starts with `'@'`:
            *   `target = operand[1:]`
            *   `target_asm = self.formatter.format_operand(target)` # Format base name/offset
            *   If `target_asm` is `[bp-N]` (local/temp): `lea ax, {target_asm} ; push ax`
            *   If `target_asm` is `[bp+N]` (param by ref -> already an address): `push word {target_asm}`
            *   If `target_asm` is global name: `push OFFSET {target_asm}`
        *   Else (push value):
            *   `val_asm = self.formatter.format_operand(operand)`
            *   If `val_asm` is `[bp+N]` (param by ref): `mov bx, {val_asm} ; mov ax, [bx] ; push ax`
            *   Else: `mov ax, {val_asm} ; push ax` (Handle immediate `push {value}` directly)
        *   Return ASM sequence.
    *   **`_translate_wrs(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `label = self.formatter.format_operand(instr.op1)` # Should return "_S0"
        *   Return `[f" mov dx, OFFSET {label}", f" call writestr"]`
    *   **`_translate_wri(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `src_asm = self.formatter.format_operand(instr.op1)`
        *   ASM Sequence:
            *   Load value into AX (handle `[bp+N]` dereference: `mov bx, {src_asm} ; mov ax, [bx]`).
            *   `call writeint`
        *   Return ASM sequence.
    *   **`_translate_rdi(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   `dest_asm = self.formatter.format_operand(instr.op1)` # TAC uses op1 for dest here
        *   ASM Sequence:
            *   `call readint` (Result in BX)
            *   Store BX into dest (handle `[bp+N]` dereference: `mov bx, {dest_asm} ; mov [bx], dx` <- No, result is in BX. `mov bx, {dest_asm}; mov [bx], bx` is wrong. Use AX as intermediate: `mov bx, {dest_asm}; mov ax, bx ; mov [bx], ax`? Simpler: `mov bx, {dest_asm}; call readint; mov [bx], ax` No, result is in BX. Need `mov bx, {dest_asm}; call readint; mov [bx], bx`. This might still be wrong. Let's use AX: `call readint ; mov ax, bx`. Now store AX. `mov bx, {dest_asm} ; mov [bx], ax`.
        *   Return `[" call readint", " mov ax, bx", f" mov bx, {dest_asm}", " mov [bx], ax"]` (If dest is `[bp+N]`)
        *   Return `[" call readint", f" mov {dest_asm}, bx"]` (If dest is direct `[bp-N]` or global)
    *   **`_translate_wrln(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   Return `[" call writeln"]`
    *   **`_translate_start_proc(self, instr: TACInstruction, current_proc_symbol: Optional[Symbol]) -> List[str]`:**
        *   Return `[]` (This TAC is handled by the main generator loop).

### **2.5. ASMGenerator Class (Orchestrator)**

*   **File:** `src/jakadac/asm_generator/asm_generator.py`
*   **Purpose:** Coordinates the entire ASM generation process.
*   **Attributes:**
    *   `tac_instructions`: List\[Tuple] (Input)
    *   `string_literals`: Dict\[str, str] (Input)
    *   `symbol_table`: SymbolTable (Input)
    *   `asm_filepath`: str (Output path)
    *   `data_manager`: DataSegmentManager
    *   `formatter`: ASMOperandFormatter
    *   `mapper`: ASMInstructionMapper
    *   `start_proc_name`: Optional\[str]
    *   `temp_allocations`: Dict\[str, Dict[str, int]] (Maps proc_name -> temp_name -> offset)
*   **Methods:**
    *   `__init__(self, tac_instructions, string_literals, symbol_table, asm_filepath)`: Store inputs, initialize `temp_allocations`.
    *   `_allocate_temporaries(self)`:
        *   **Action:**
            1.  Iterate through `tac_instructions`.
            2.  Track current procedure scope.
            3.  For each procedure, identify all unique temporary variables (`_tN`) used as `dest`, `op1`, or `op2`.
            4.  Determine the maximum number of temps needed within that procedure.
            5.  Calculate the total extra stack space required for these temps (assuming `DW` per temp).
            6.  Update the `local_size` in the procedure's `Symbol` entry in the `symbol_table`.
            7.  Assign specific negative `bp`-relative offsets to each unique temp within the procedure (e.g., `_t1 -> -8`, `_t2 -> -10`, etc., starting after declared locals). Store this mapping in `self.temp_allocations[proc_name]`.
    *   `generate_asm(self)`:
        *   **Action:**
            1.  Call `self._allocate_temporaries()`.
            2.  Instantiate `self.data_manager = DataSegmentManager(self.symbol_table)`.
            3.  Call `self.data_manager.collect_definitions()`.
            4.  Instantiate `self.formatter = ASMOperandFormatter(self.temp_allocations)` - Pass temp offset map.
            5.  Instantiate `self.mapper = ASMInstructionMapper(self.formatter, self.symbol_table)`.
            6.  `data_lines = self.data_manager.get_data_section_asm(self.string_literals)`.
            7.  Initialize `code_lines = []`.
            8.  `current_proc_symbol = None`.
            9.  Iterate through `tac_tuple` in `self.tac_instructions`:
                *   `instr = TACInstruction.from_tuple(tac_tuple)`
                *   If `instr.opcode == 'proc'`: `current_proc_symbol = self.symbol_table.lookup(instr.op1)`.
                *   If `instr.opcode == 'endp'`: `current_proc_symbol = None`.
                *   If `instr.opcode == 'start_proc'`: `self.start_proc_name = instr.op1`. Continue loop.
                *   `asm_ snippet = self.mapper.translate(instr, current_proc_symbol)`
                *   `code_lines.extend(asm_snippet)`
            10. `main_lines = self._generate_main_entry()`.
            11. Assemble final list: Boilerplate (`%include "io.asm"`, `section .text`, etc.) + `data_lines` + `section .bss` (if needed, from globals) + `code_lines` + `main_lines`.
            12. Write result to `self.asm_filepath`. Handle file I/O errors.
    *   `_generate_main_entry(self) -> List[str]`:
        *   **Action:** Generate standard `_start:` label, `call {self.start_proc_name}`, and exit syscall sequence. Handle error if `start_proc_name` is not set.

## **3. Error Handling & Logging**

*   Implement specific error messages (e.g., "Temp variable '{t}' used in procedure '{p}' not found in allocation map", "Dereference attempt on non-reference operand {op}").
*   Use `Logger` for tracing.

