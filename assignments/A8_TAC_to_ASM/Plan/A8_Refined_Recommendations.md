# A8_TAC_to_ASM Refined Recommendations

This document summarizes the refined recommendations for the TAC to Assembly generation phase (Assignment 8), based on code review, analysis of `test81_exp.asm`, and discussions.

**A. Overall Project Structure & Driver (`JohnA8.py`)**
    1.  **Integrate ASMGenerator:** `JohnA8.py`'s pipeline must call `ASMGenerator` after `TACGenerator`. It needs to pass the TAC file path, the populated `SymbolTable`, and a map of string literals (see point G).

**B. TAC Processing (`tac_instruction.py`)**
    1.  **ParsedTACInstruction Class:** Define attributes for `label` (optional, if labels are stored directly on instructions), `opcode` (TACOpcode enum), `destination`, `operand1`, `operand2` (TACOperand type).
    2.  **parse_tac_line Function:** Robustly parse lines from the `.tac` file into `ParsedTACInstruction` objects, handling comments, empty lines, labels, and various instruction formats. Labels might be handled by `TACParser` and associated with instructions separately.

**C. Assembly Memory Model (PREFERRED)**
    1.  **Stack-Based for Locals/Temporaries/Parameters:**
        *   **Parameters:** Accessed via `[BP+offset]` (e.g., `[BP+4]`, `[BP+6]`). Offsets are positive, starting from `BP+4` (after return address and old BP).
        *   **Local Variables & Compiler Temporaries (`_tN`):** Accessed via `[BP-offset]` (e.g., `[BP-2]`, `[BP-4]`). Offsets are negative.
        *   `ASMGenerator` calculates total space needed on stack for locals and temps for `SUB SP, size` in procedure prologue.
    2.  **Global Variables:** Declared in `.data` segment, accessed by label.
    3.  **String Literals:** Declared in `.data` segment (e.g., `_S0 DB "message$"`), accessed by label. (`$`-termination for `io.asm`).

**D. Register Allocation Strategy**
    1.  **Simple & On-Demand:**
        *   `AX`: Primary accumulator, first operand for binary ops, `writeint` argument.
        *   `BX`: Second operand for binary ops if needed, general-purpose, `readint` return value.
        *   `CX`: Loop counters (if any explicit loops in ASM), potentially for string lengths if `io.asm` requires.
        *   `DX`: High-word for `MUL`/`DIV` (product/dividend), remainder for `DIV`, `OFFSET` for string addresses for `io.asm` calls.
        *   No complex inter-statement register optimization. Load operands before use, store results immediately.

**E. ASMGenerator Module (`asm_generator.py`)** 
    1.  **Orchestration Class ASMGenerator:**
        *   **Initialization:** Takes TAC file path, output ASM file path, `SymbolTable`, and string literal map.
        *   **Responsibilities:**
            *   Parses `.tac` file using `tac_parser.py` (instance of `TACParser`).
            *   Manages `.data` segment: Gathers and declares global variables and string literals.
            *   Manages `.code` segment:
                *   Iterates parsed TAC instructions.
                *   Calls `ASMInstructionMapper` for instruction translation.
                *   Generates procedure prologues/epilogues (`PROC P`, `push bp`, `mov bp, sp`, `sub sp, <locals_temps_size>`, ..., `mov sp, bp`, `pop bp`, `ret <params_size_bytes>`, `ENDP P`).
                *   Generates `main` program structure, including `DS` setup and program termination.
            *   Delegates operand formatting to an instance of `ASMOperandFormatter`, which translates TAC operand strings (e.g., variable name, `_tN`, literal) to their assembly representation (e.g., `myGlobal`, `[bp-2]`, `[bp+4]`, `123`), using symbol table context.

**F. ASMInstructionMapper Module (`asm_instruction_mapper.py`)** 
    1.  **Dedicated Mapping Class ASMInstructionMapper:**
        *   Takes a `ParsedTACInstruction` and context (e.g., from `ASMGenerator`).
        *   Methods per TAC opcode category (e.g., `map_assignment`, `map_binary_op`, `map_call`, `map_jump`).
        *   Returns a list of assembly instruction strings for each TAC instruction.
        *   Adheres to the defined register allocation (D) and memory model (C).
    2.  **`TACGenerator` Responsibility:**
        *   `TACGenerator` should identify all unique string literals during TAC generation.
        *   It should assign a unique label to each (e.g., `_S0`, `_S1`).
        *   It should maintain a map: `Dict[str_label, str_value]` (e.g., `{"_S0": "Hello, World!"}` - the value should NOT include the `$` terminator here; `ASMGenerator` or `DataSegmentManager` adds it).
    2.  **Passing to ASMGenerator:** `JohnA8.py` retrieves this string map from the `TACGenerator` instance (e.g., `tac_generator.string_definitions`) and passes it to the `ASMGenerator` instance.
    3.  `ASMGenerator` uses this map to declare strings in the `.data` segment, adding the `$` terminator.

**G. Handling of String Literals**
    1.  **TACGenerator Responsibility:**
        *   `TACGenerator` should identify all unique string literals during TAC generation.
        *   It should assign a unique label to each (e.g., `_S0`, `_S1`).
        *   It should maintain a map: `Dict[str_label, str_value]` (e.g., `{"_S0": "Hello, World!"}`).
    2.  **Passing to ASMGenerator:** `JohnA8.py` retrieves this string map from the `TACGenerator` instance and passes it to the `ASMGenerator` instance.
    3.  `ASMGenerator` uses this map to declare strings in the `.data` segment.

**H. io.asm Interface Assumptions**
    1.  **readint:** Reads integer, returns value in `BX`.
    2.  **writeint:** Writes integer value from `AX`.
    3.  **wrs (WriteString):** Writes `$`-terminated string. `DX` should contain `OFFSET string_label`.
    4.  **wrln (WriteLine):** Writes a newline character.
    5.  *(Conventions confirmed with actual `io.asm`)*.
