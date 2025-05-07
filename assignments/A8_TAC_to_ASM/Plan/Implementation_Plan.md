 # Implementation Plan: A8 - TAC to ASM

This document outlines the plan for Assignment 8, focusing on generating x86 Assembly Code from Three-Address Code (TAC).

## Key Refinements and Decisions (May 2025 Review)

This section details critical updates and decisions for the A8 TAC to ASM implementation, based on the review and discussion on May 6th, 2025, and analysis of `test81_exp.asm`. For comprehensive details on each point, please refer to the **`A8_Refined_Recommendations.md`** document located in this same `Plan` directory.

These points clarify and, where conflicting, supersede prior information in this plan regarding:

1. Overall Project Structure & Driver (`JohnA8.py`):
    * Integration of `ASMGenerator` post-`TACGenerator`, including passing the `SymbolTable` and string literal map. (Ref: `A8_Refined_Recommendations.md` - Point A)

2. TAC Processing (`tac_instruction.py`):
    * Definition and implementation of `ParsedTACInstruction` class and the `parse_tac_line` function. (Ref: `A8_Refined_Recommendations.md` - Point B)

3. Assembly Memory Model (Chosen Approach):
    * Stack-Based: Parameters (`[BP+offset]`), local variables, and compiler temporaries (`_tN`) (`[BP-offset]`).
    * Data Segment: Global variables and string literals (null-terminated).
    * `ASMGenerator` to calculate stack space for `SUB SP, size`.
    * (Ref: `A8_Refined_Recommendations.md` - Point C)

4. Register Allocation Strategy:
    * Simple, on-demand use of `AX` (primary), `BX` (secondary/operand), `CX` (counters), `DX` (mul/div, string offsets).
    * No cross-statement optimizations.
    * (Ref: `A8_Refined_Recommendations.md` - Point D)

5. `ASMGenerator` Module (`asm_generator.py`):
    * Key responsibilities include TAC parsing orchestration, `.data`/`.code` segment management, procedure prologue/epilogue generation, and providing an `get_operand_asm` helper.
    * (Ref: `A8_Refined_Recommendations.md` - Point E)

6. `ASMInstructionMapper` Module (`asm_instruction_mapper.py`):
    * Dedicated class with methods per TAC opcode category, returning ASM instruction strings.
    * (Ref: `A8_Refined_Recommendations.md` - Point F)

7. String Literal Handling:
    * `TACGenerator` identifies literals, assigns labels, creates a map (`Dict[str_label, str_value]`).
    * `JohnA8.py` passes this map to `ASMGenerator` for declaration in `.data`.
    * (Ref: `A8_Refined_Recommendations.md` - Point G)

8. `io.asm` Interface Assumptions:
    * Specific conventions for `readint`, `writeint`, `wrs` (DX=OFFSET, null-terminated string), and `wrln`.
    * (Ref: `A8_Refined_Recommendations.md` - Point H)