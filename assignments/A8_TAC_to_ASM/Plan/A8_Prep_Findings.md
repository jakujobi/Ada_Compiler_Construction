# Assignment 8 - Prerequisite Findings

This document records findings from the initial prerequisite checks.

## 1. io.asm Register Conventions

Based on review of `Ada_Compiler_Construction/assignments/A8_TAC_to_ASM/io.asm`:

*   **`readint`**: Reads an integer from the keyboard, returns the value in register **`BX`**.
*   **`writeint`**: Expects the integer to be written in register **`AX`**.
*   **`writestr`**: Expects the **offset** of a '$'-terminated string in register **`DX`**.
*   **`writeln`**: Writes CR/LF, does not expect input in specific registers (uses AX, DX internally).

## 2. Observed TAC Format (from test7*.tac, test8*_exp.tac)

*   **General:** Line-based instructions. Whitespace (tabs/spaces) separates components. Comments start with `;`.
*   **Labels:** Not observed in examples, but assumed format is `Label:` at line start.
*   **Common Instructions & Operand Order:**
    *   Procedure Def: `proc <Name>` -> `opcode=proc`, `dest=<Name>`
    *   Procedure End: `endp <Name>` -> `opcode=endp`, `dest=<Name>`
    *   Assignment (Value): `<Dest> = <Source>` -> `dest=<Dest>`, `opcode==`, `op1=<Source>`
    *   Assignment (Binary Op): `<Dest> = <Op1> <Op> <Op2>` -> `dest=<Dest>`, `opcode==`, `op1=<Op1>`, `op2=<Op>`, `op3=<Op2>`
    *   Procedure Call: `call <Name>` -> `opcode=call`, `op1=<Name>`
    *   Push (Value): `push <Operand>` -> `opcode=push`, `op1=<Operand>`
    *   Push (Reference): *(Expected)* `push @<VarName>` -> `opcode=push`, `op1=@<VarName>`
    *   Read Integer: *(Expected)* `rdi <Address>` -> `opcode=rdi`, `dest=<Address>`
    *   Write Integer: *(Expected)* `wri <Value>` -> `opcode=wri`, `op1=<Value>`
    *   Write String: *(Expected)* `wrs <Label>` -> `opcode=wrs`, `op1=<Label>`
    *   Write Newline: *(Expected)* `wrln` -> `opcode=wrln`
    *   Program Start: `START\tPROC\t<Name>` -> Treat as `opcode=STARTPROC`, `op1=<Name>`.
*   **Operand Representation:**
    *   Globals: By name (e.g., `A`, `CC`).
    *   Locals/Params: **Inconsistent!** Seen as `_BP-4` (`test74.tac`) and `[bp-2]`/`[bp+6]` (`test84/85_exp.tac`). **Decision: Target `[bp+/-N]` format for parsing and generation.** The `TACGenerator` might need fixing if it produces `_BP-N`.
    *   Temporaries: `_t<Number>` (e.g., `_t1`).
    *   Immediates: Literal numbers (e.g., `5`, `10`).
    *   String Labels: *(Expected)* `_S<Number>`.
*   **Parsing Considerations:**
    *   The `TACInstruction.from_tac_line` method needs robust logic to handle different numbers of operands based on the opcode.
    *   Must handle the specific `START PROC Name` format.
    *   Must normalize or handle the inconsistent `_BP-N` vs `[bp-N]` representation if both can occur in input TAC (ideally, fix the generator). 