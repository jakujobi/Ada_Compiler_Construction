# Assignment 8: Full Implementation Plan (including Module Updates)

*(Current Date: May 2, 2025)*

## 0. Prerequisites & Setup

1. **Git Branching Strategy:**
   * **Action:** Before making *any* changes for Assignment 8, ensure your current working A7 code is committed to a stable branch (e.g., `main` or `assignment-7`).
   * Create a new branch specifically for Assignment 8: `git checkout -b assignment-8`.
   * **All subsequent modifications** (to existing modules and addition of new ones) will be performed  **on this `assignment-8` branch** . This isolates A8 development and preserves the working state of previous assignments.
2. **Confirm A7 TAC Format:**
    * **Action:** Before implementing `TACParser`, review the output of your A7 `TACGenerator` for a few key test cases. Note the exact format (delimiters, operand order for different opcodes) to guide the parsing logic in `TACInstruction.from_tac_line`.
3. **Existing Module Updates (Perform on `assignment-8` branch):**
   * **Goal:** Modify existing compiler components to support A8 features (I/O, required symbol table info).
   * **Sub-Plan & Verification:**
     * **`Definitions.py`:**
       * **Change:** Add `TokenType` enums (e.g., `TK_GET`, `TK_PUT`, `TK_PUTLN`) and corresponding entries in the `reserved_words` dictionary (`"get": TokenType.TK_GET`, etc.).
       * **Verification:** Run Lexer on Ada code with `get`/`put`/`putln`; verify correct token types are generated.
     * **`LexicalAnalyzer.py`:**
       * **Change:** None likely needed (relies on `Definitions.py`).
       * **Verification:** (Covered by `Definitions.py` verification).
     * **Parser (`RDParserExtExt.py` / Mixins):**
       * **Change:** Implement new parsing methods for A8 I/O BNF rules (`IO_Stat`, `In_Stat`, `Out_Stat`, etc.). Integrate calls into `Parse_Statement`. Add semantic action calls to `TACGenerator` for `rdi`, `wrs`, `wri`, `wrln`. Implement string literal handling (get label from SymTable, pass label to TACGenerator). Ensure pass-by-reference (`push @Var`) TAC is triggered correctly for relevant parameters (e.g., OUT params if supported, or conceptual handling for `get`).
       * **Verification:** Parse Ada code with various I/O statements. Check for syntax errors. Verify correct I/O TAC sequence (including `wrs Label`, `rdi Addr`, `wrln`) is generated in the `.tac` file.
     * **`TACGenerator.py`:**
       * **Change:** Add methods (`emit_read_int`, `emit_write_string`, etc.) to format and output `rdi`, `wrs`, `wri`, `wrln` TAC lines. Ensure `emit_push` (or new `emit_push_reference`) correctly handles `push @Var` syntax/logic when called for reference parameters.
       * **Verification:** Unit test new emit methods. Integration test by running Ada -> TAC pipeline; verify `.tac` file contains correctly formatted I/O instructions.
     * **`NewSemanticAnalyzer.py`:**
       * **Change:** Verify/implement logic to calculate total `SizeOfLocals` (including temps) and `SizeOfParams` for each procedure. Store these values in the procedure's `SymbolTable` entry. Verify/implement logic to identify string literals during `put`/`putln` analysis, interface with `SymbolTable` to store the literal and get its unique label (e.g., `_S0`).
       * **Verification:** After semantic analysis, inspect `SymbolTable` dump/state for procedures; verify `SizeOfLocals` and `SizeOfParams` are present and correct. Verify string literals result in labeled entries in the `SymbolTable`.
     * **`SymTable.py`:**
       * **Change:** **CRITICAL.** Ensure the `SymbolTable` implementation **supports** (adding if necessary) fields in procedure entries for `size_of_locals: int` and `size_of_params: int`. Implement a mechanism to store string literal values mapped to unique labels (e.g., new entry type or field in constant entry). Ensure an `is_parameter: bool` flag (or equivalent) exists to distinguish parameters from locals. Verify that `offset` storage provides sufficient info for `ASMOperandFormatter` to calculate final `[bp+/-X]`.
       * **Verification:** Write/run unit tests specifically validating storage and retrieval of procedure sizes, string literal values by label, and the parameter flag.
     * **`Driver.py` / `JohnA8.py`:**
       * **Change:** Add the ASM generation phase after TAC generation. Instantiate `ASMGenerator`, pass necessary inputs (TAC path, ASM path, populated `SymbolTable`), and call `asm_generator.generate_asm()`.
       * **Verification:** Run the full driver; verify it proceeds through all phases including ASM generation without crashing. Check that `.tac` and `.asm` files are produced.
4. **`io.asm`:** Place `io.asm` in an accessible location (e.g., project root or output directory).
5. **Verify `io.asm` Conventions:** Open `io.asm` source. Confirm and document register usage:
   * `readint`: Returns value in `BX`. (Confirmed)
   * `writeint`: Expects value in **`AX`** or  **`DX`** ?  **(Action: Verify & Document findings clearly below or in Comp_Findings_A8.md)**.
     * *Verified `writeint` register: [Enter Register Here, e.g., AX]*
   * `writestr`: Expects offset in `DX`. (Confirmed)
6. **Tooling:** Confirm MASM/TASM and DOSBox installation and operation.
7. **Symbol Table Access:** Ensure the `Driver` correctly passes the *populated* `SymbolTable` instance to the `ASMGenerator`.

## 1. Phase 0: Foundational ASM Generator Components & Verification

* **Goal:** Implement basic data structures for TAC representation, TAC file parsing, and re-verify `SymbolTable` readiness based on A8 needs identified in Prerequisite step 2.
* **Steps:**
  1. **`tac_instruction.py`:** Implement `TACInstruction` data class (`@dataclass`) with `line_number`, `label`, `opcode`, `op1`, `op2`, `dest` (all `Optional[str]` except `line_number`). Implement `TACInstruction.from_tac_line(line, line_num)` to parse various TAC line formats robustly.
     * **Verification:** Unit test `from_tac_line` with diverse valid/invalid TAC lines.
  2. **`tac_parser.py`:** Implement `TACParser` class (`__init__`, `parse() -> List[TACInstruction]`) using `TACInstruction.from_tac_line`. Handle file errors.
     * **Verification:** Unit test `TACParser.parse` with sample `.tac` files. Check returned list correctness and error handling.
  3. **Re-Verify `SymbolTable` Interface:** Based on Prerequisite step 2, ensure all necessary data (proc sizes, string storage, param flag, offsets) is accessible via the `SymbolTable`'s interface.
     * **Verification:** Run targeted unit tests against `SymbolTable.py`.

## 2. Phase 1: Skeleton Generation & Data Collection Setup

* **Goal:** Create the main orchestrator (`ASMGenerator`) and supporting classes (`DataSegmentManager`, `ASMOperandFormatter`) to generate the basic `.asm` file structure and collect necessary data definitions.
* **Steps:**
  1. **`data_segment_manager.py`:** Implement `DataSegmentManager` (`__init__`, `collect_definitions`, `get_data_section_asm`). `collect_definitions` identifies globals and string labels via `SymbolTable` lookups. `get_data_section_asm` formats the `.data` section list (`DW ?`, `DB "..." , '$'`).
     * **Verification:** Unit test `DataSegmentManager` with mock data. Verify correct `.data` section formatting.
  2. **`asm_operand_formatter.py`:** Implement `ASMOperandFormatter` (`__init__`, `format_operand`). Implement basic logic for immediate values and global variable names (depth 1 lookup, `c`->`cc` rename).
     * **Verification:** Unit test `format_operand` for immediate and global cases.
  3. **`asm_generator.py`:** Implement `ASMGenerator` (`__init__`, `generate_asm`, `_generate_main_entry`). `generate_asm` uses `TACParser`, `DataSegmentManager` to write boilerplate, the generated `.data` section, `.code`, `include`, a *static minimal* `main PROC`, and `END main`.
* **Verification (Integration):** Run Driver on simple Ada -> TAC -> ASM. Verify output `.asm` has correct boilerplate, `.data` (with globals), minimal `main`, and *assembles* via MASM. (Covers R2, R3, R4.1 partially, R5, R6 partially).

## 3. Phase 2: Basic Procedures & Global Assignments

* **Goal:** Translate procedure boundaries (`proc`/`endp`), calls (`call`), and simple assignments (`=`) involving only globals and immediates.
* **Steps:**
  1. **`asm_instruction_mapper.py`:** Implement `ASMInstructionMapper` class (`__init__`).
  2. **Implement `translate_proc` / `translate_endp`:** Fetch `SizeOfLocals`/`SizeOfParams` from `SymbolTable`. Generate correct prologue/epilogue ASM lines.
  3. **Implement `translate_assign`:** Use current `ASMOperandFormatter`. Generate `mov ax, src; mov dest, ax` or `mov dest, immediate`.
  4. **Implement `translate_call`:** Generate `call ProcName`.
  5. **Enhance `ASMGenerator.generate_asm`:**
     * Instantiate `ASMInstructionMapper`.
     * Modify main loop: Detect `start`, `proc`, `endp`, `=`, `call` TACs. Call corresponding `mapper.translate_*`. Track `current_proc_context`.
     * Implement `_generate_main_entry` using collected `start_proc_name`.
     * Assemble full output.
* **Verification:** Unit test `translate_proc`/`endp`/`assign`/`call`. Integration test using TAC with empty procedures, calls, global assignments, `start`. Inspect `.asm` for correct `PROC`/`ENDP`, prologues/epilogues (verify sizes!), `call`, assignments. Assemble and run (Test Case 1 equivalent). (Covers R6 fully, R7, R8, R10 partially, R12).

## 4. Phase 3: Locals, Temps & Arithmetic

* **Goal:** Implement stack variable addressing (`[bp+/-X]`) and arithmetic translation (`+`, `*`).
* **Steps:**
  1. **Enhance `ASMOperandFormatter.format_operand`:** Implement full logic for depth >= 2 operands. Retrieve `offset`, `isParameter` from `SymbolTable`. Calculate final 8086 offset (e.g., local offset 0 -> -2, param offset 0 -> +4). Return formatted `[bp+/-X]` string. Handle `c`->`cc` rename.
  2. **Enhance `ASMInstructionMapper`:** Implement `translate_add` and `translate_mul`. Ensure they use the formatter correctly. Update `translate_assign` for stack variables.
* **Verification:** Unit test `ASMOperandFormatter` extensively for `[bp+/-X]` cases. Unit test `translate_add`/`mul`. Integration test using TAC with locals, temps, arithmetic. Inspect `.asm` for correct `[bp-...]` addressing and arithmetic sequences. Assemble and run (may need simple I/O or debugger). (Covers R9.2, R10 fully, R11, R18).

## 5. Phase 4: String Output & Literals

* **Goal:** Implement string literal handling (`.data` section) and translation for `wrs`, `wrln`.
* **Steps:**
  1. **Verify Prerequisite:** Ensure earlier phases store `Label -> Value$` pairs (via `SymbolTable`) and emit `wrs Label` TAC.
  2. **Enhance `DataSegmentManager`:** Ensure `collect_definitions` retrieves string values and `get_data_section_asm` generates correct `Label DB "Value$"` lines.
  3. **Enhance `ASMOperandFormatter.format_operand`:** Ensure it translates `_SLabel` operands to `OFFSET _SLabel`.
  4. **Implement `ASMInstructionMapper.translate_wrs`:** Generate `mov dx, OFFSET Label; call writestr`.
  5. **Implement `ASMInstructionMapper.translate_wrln`:** Generate `call writeln`.
* **Verification:** Unit test relevant methods. Integration test with TAC using `put`/`putln` with strings. Inspect `.data` and `.code`. Assemble, run, verify string output and newlines. (Covers R4.2, R9.4, R15.1, R15.4).

## 6. Phase 5: Parameter Passing (Value) & Integer Output

* **Goal:** Implement pass-by-value (`push`) and integer output (`wri`).
* **Steps:**
  1. **Implement `ASMInstructionMapper.translate_push`:** Generate `mov ax, ValueOperand; push ax` (or `push Immediate`).
  2. Ensure `translate_endp` uses correct `SizeOfParams` in `ret N`.
  3. Ensure `ASMOperandFormatter` correctly formats parameter operands (`[bp+X]`).
  4. **Implement `ASMInstructionMapper.translate_wri`:** Generate `mov REG, ValueOperand; call writeint`.  **Use the register confirmed from `io.asm` verification** .
* **Verification:** Unit test `translate_push`/`wri`. Integration test using Test Case 3 equivalent. Inspect `push`, `ret N`, `[bp+X]` access, `wri` translation. Assemble, run, verify parameter passing and integer output. (Covers R13, R15.2).

## 7. Phase 6: Integer Input & Pass-by-Reference

* **Goal:** Implement integer input (`rdi`) and pass-by-reference (`push @`, dereferencing).
* **Steps:**
  1. **Implement `ASMInstructionMapper.translate_rdi`:** Generate `call readint; mov AddressOperand, bx`. Ensure `AddressOperand` is correctly formatted (e.g., `[bp-2]`).
  2. **Implement `ASMInstructionMapper.translate_push_ref`:** Generate `mov ax, offset VarName; push ax`.
  3. **Enhance `ASMOperandFormatter` / `ASMInstructionMapper` (Dereferencing):** Implement logic for accessing/modifying via reference parameters using `BX` register (load address `mov bx, [bp+N]`, then use `[bx]`).
* **Verification:** Unit test `translate_rdi`/`push_ref`. Integration test using Test Case 5 equivalent. Inspect `push offset`, `ret N`, `call readint`, `mov bx, [bp+N]`, `mov [bx], bx` (or `ax`), and assignment *to* reference params. Assemble, run, provide input, verify variable update in caller scope. (Covers R14, R15.3).

## 8. Phase 7: Final Integration, Testing & Refinement

* **Goal:** Ensure end-to-end correctness and meet all requirements.
* **Steps:**
  1. **Execute Full Pipeline:** Run the `Driver` (`JohnA8.py`) on all official A8 test files.
  2. **Assemble:** Use MASM/TASM on each generated `.asm` file. Resolve errors.
  3. **Run:** Execute each `.exe` in DOSBox.
  4. **Verify Output:** Compare actual output/behavior against expected results.
  5. **Debug:** Trace errors back through components as needed.
  6. **Code Review:** Final review for clarity, correctness, comments.
* **Verification:** All official A8 test cases compile, assemble, and run correctly. All requirements (R1-R18 from Requirements Plan) are met.

## 9. Overall Considerations

* **Error Handling:** Implement robust `try...except` blocks and custom exceptions.
* **Logging:** Use `Logger.py` for DEBUG and INFO level messages.
* **Testing Strategy:** Combine unit, incremental integration, and final system tests.
* **Code Quality:** Follow PEP 8, use type hints, write docstrings and comments.

