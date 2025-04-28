# Assignment 7 - Phase 2: Basic Statements & Expressions TAC Generation

This document outlines the plan for implementing Three-Address Code (TAC) generation for basic assignment statements and simple expressions in the Ada compiler.

## Phase Goal

Modify the parser (`RDParserA7.py`) and TAC generator (`TACGenerator.py`) to handle assignment statements (`:=`) and simple arithmetic expressions involving constants, global variables, local variables, and parameters, generating correct TAC instructions.

## Increments

### Increment 2a: Constants & Globals (test71.ada)

**Goal:** Handle simple assignments where LHS is a global variable and RHS is either an integer/float literal or another global variable. Ensure correct `place` representation (literal value for constants, variable name for globals).

**Target Test File:** `test71.ada`

**Detailed Plan:**

1.  **Modify `parseSeqOfStatements` (`RDParserA7.py`):**
    *   Implement loop to parse statements between `BEGIN` and `END`.
    *   **Assignment Recognition:**
        *   If `current_token` is `ID`, look ahead one token.
        *   If next token is `ASSIGN`, identify as an assignment statement.
    *   **Delegation (Non-Tree Mode):** If assignment found and `build_parse_tree` is `False`, call `parseAssignStat_tac()`.
    *   **Tree Mode:** (Future work/Verify existing logic).
    *   Match trailing `SEMICOLON` after each statement.

2.  **Create TAC Helper Functions (`RDParserA7.py`, Non-Tree Mode Only):**
    *   **`parseAssignStat_tac()`:**
        *   Consumes `ID` (LHS).
        *   Looks up LHS symbol (`symbol_table.lookup`).
        *   Gets `dest_place` (`tac_gen.getPlace(lhs_symbol)`).
        *   Matches `ASSIGN`.
        *   Calls `parseExpr_tac()` to get `src_place`.
        *   Emits TAC (`tac_gen.emitAssignment(dest_place, src_place)`).
    *   **`parseExpr_tac()`:**
        *   Calls `parseTerm_tac()` (or `parseSimpleExpr_tac`).
        *   Returns the `place` string received.
    *   **`parseTerm_tac()`:**
        *   Calls `parseFactor_tac()`.
        *   Returns the `place` string received.
    *   **`parseFactor_tac()`:**
        *   If `ID`: Match, lookup symbol, `place = tac_gen.getPlace(symbol)`, return `place`.
        *   If `NUM` or `REAL`: Match, get lexeme, `place = tac_gen.getPlace(lexeme)`, return `place`.
        *   Other cases (e.g., `(`): Report error or return placeholder.

3.  **Verify `getPlace` (`TACGenerator.py`):**
    *   Ensure it correctly returns the literal string for numbers passed as strings (e.g., `"5"`).
    *   Ensure it correctly returns the variable name for global symbols (depth 1).

4.  **Verify `emitAssignment` (`TACGenerator.py`):**
    *   Ensure it generates the correct `dest = source` TAC instruction.

5.  **Testing:**
    *   Run `python JohnA7.py assignments/A7_3_Address_Code/test71.ada`.
    *   Compare `test71.tac` with `exp_test71.tac`.

---

### Increment 2b: Locals & Parameters in Expressions (test72.ada)

**Goal:** Extend `parseFactor_tac` and `getPlace` to handle local variables and parameters, using the correct `_BP-offset` and `_BP+offset` notation.

**Target Test File:** `test72.ada`

**Detailed Plan:**

*   **(Modify `parseFactor_tac`):** No code changes likely needed here, as it already calls `getPlace` for identifiers.
*   **(Modify `getPlace` in `TACGenerator.py`):**
    *   When handling an `IDENTIFIER` symbol:
        *   If `symbol.depth > 1` and `symbol.is_parameter` is `True`, return `f"_BP+{symbol.offset}"`.
        *   If `symbol.depth > 1` and `symbol.is_parameter` is `False`, return `f"_BP{symbol.offset}"` (offset is already negative).
*   **(Testing):** Run `test72.ada`, compare output TAC with expected TAC.

---

### Increment 2c: Basic Arithmetic Expressions (test73.ada)

**Goal:** Implement TAC generation for simple expressions involving `+`, `-` operators (at the `SimpleExpr` level) using temporary variables.

**Target Test File:** `test73.ada`

**Detailed Plan:**

*   **(Modify `parseExpr_tac` / Implement `parseSimpleExpr_tac`):**
    *   Parse the first `Term` using `parseTerm_tac()` to get `left_place`.
    *   Loop while `current_token` is `ADDOP` (`+` or `-`):
        *   Save the operator (`op`).
        *   Match the `ADDOP`.
        *   Parse the next `Term` using `parseTerm_tac()` to get `right_place`.
        *   Generate a new temporary variable name: `temp_place = tac_gen.newTemp()`.
        *   Emit the arithmetic TAC: `tac_gen.emitOperation(temp_place, left_place, op, right_place)`.
        *   Update `left_place = temp_place` for the next iteration.
    *   Return the final `left_place`.
*   **(Implement `newTemp` in `TACGenerator.py`):**
    *   Maintain a counter.
    *   Return strings like `"_t1"`, `"_t2"`, etc.
*   **(Implement `emitOperation` in `TACGenerator.py`):**
    *   Generate the TAC instruction `result = operand1 op operand2`.
*   **(Testing):** Run `test73.ada`, compare output TAC.

---

### Increment 2d: Multiplication/Division (test74.ada, test75.ada)

**Goal:** Implement TAC generation for `*` and `/` operators (at the `Term` level).

**Target Test Files:** `test74.ada`, `test75.ada`

**Detailed Plan:**

*   **(Modify `parseTerm_tac`):**
    *   Similar structure to `parseSimpleExpr_tac`.
    *   Parse the first `Factor` using `parseFactor_tac()` to get `left_place`.
    *   Loop while `current_token` is `MULOP` (`*` or `/`):
        *   Save the operator (`op`).
        *   Match the `MULOP`.
        *   Parse the next `Factor` using `parseFactor_tac()` to get `right_place`.
        *   Generate temporary: `temp_place = tac_gen.newTemp()`.
        *   Emit TAC: `tac_gen.emitOperation(temp_place, left_place, op, right_place)`.
        *   Update `left_place = temp_place`.
    *   Return the final `left_place`.
*   **(Testing):** Run `test74.ada` and `test75.ada`, compare output TAC.

---

### Increment 2e: Parenthesized Expressions

**Goal:** Ensure `parseFactor_tac` correctly handles parenthesized expressions `( Expr )`.

**Detailed Plan:**

*   **(Modify `parseFactor_tac`):**
    *   If `current_token` is `LPAREN`:
        *   Match `LPAREN`.
        *   Call `parseExpr_tac()` to get the `place` of the inner expression.
        *   Match `RPAREN`.
        *   Return the `place` received from `parseExpr_tac()`.
*   **(Testing):** Use existing or create new test cases with parentheses.

---

### Increment 2f: Procedure Calls (Initial - differentiating from assignment)

**Goal:** Update `parseSeqOfStatements` to differentiate between an assignment (`ID := ...`) and a simple procedure call (`ID;` or `ID(...);`). For now, just correctly identify the procedure call and *skip* generating TAC for it.

**Detailed Plan:**

*   **(Modify `parseSeqOfStatements`):**
    *   When an `ID` is encountered:
        *   Look ahead: If next token is `ASSIGN`, handle as assignment (call `parseAssignStat_tac`).
        *   Look ahead: If next token is `SEMICOLON` or `LPAREN`, identify as a procedure call.
        *   **Procedure Call Handling (Non-Tree):**
            *   Consume the `ID`.
            *   If `LPAREN`, call a (potentially dummy for now) `parseProcCallArgs_tac()` to consume arguments and `RPAREN`.
            *   Do *not* emit any TAC for the call itself in this increment.
            *   Ensure the final `SEMICOLON` of the statement is matched in the main loop.
*   **(Testing):** Use `test75.ada` which contains procedure calls. Ensure no TAC is generated *for the call itself* yet, but the rest of the TAC (assignments) is correct.