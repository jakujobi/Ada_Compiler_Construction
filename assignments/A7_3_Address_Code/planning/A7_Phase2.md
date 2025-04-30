# Assignment 7 - Phase 2: Basic Statements & Expressions TAC Generation

This document outlines the plan for implementing Three-Address Code (TAC) generation for basic assignment statements and simple expressions in the Ada compiler.

## Phase Goal

Modify the parser (`RDParserA7.py`) and TAC generator (`TACGenerator.py`) to handle assignment statements (`:=`) and simple arithmetic expressions involving constants, global variables, local variables, and parameters, generating correct TAC instructions.

## Code Review Findings

Our analysis of the existing codebase revealed:

1. **Missing Implementation**: `parseSeqOfStatements()` is called in `parseProg()` but is not implemented in either `RDParserA7.py` or `RDParser.py`. This is our primary insertion point.

2. **Existing TAC Generator Functions**: The `TACGenerator` class already has:
   - `getPlace(symbol_or_value)`: Correctly handles global variables, locals, parameters, and literals
   - `emitAssignment(dest_place, source_place)`: Emits assignment TAC
   - `newTemp()`: Generates names for temporary variables
   - `emitBinaryOp(op, dest_place, left_place, right_place)`: Skeleton for arithmetic operations

3. **Execution Flow**: The driver expects TAC to be generated during parsing (not as a separate phase).

## Increments

### Increment 2a: Constants & Globals (test71.ada)

**Goal:** Handle simple assignments where LHS is a global variable and RHS is either an integer/float literal or another global variable.

**Target Test File:** `test71.ada`

**Detailed Plan:**

1. **Implement `parseSeqOfStatements` in `RDParserA7.py`:**
   - Create the function that's currently missing but called in `parseProg()`
   - Implement a loop to parse statements between `BEGIN` and `END`
   - **Assignment Recognition:**
     - If `current_token` is `ID`, look ahead one token
     - If next token is `ASSIGN`, identify as an assignment statement
   - **Delegation (Non-Tree Mode):** If assignment found and `build_parse_tree` is `False`, call `parseAssignStat_tac()`
   - **Tree Mode:** If `build_parse_tree` is `True`, call existing `parseAssignStat()`
   - Match trailing `SEMICOLON` after each statement

2. **Create TAC Helper Functions (`RDParserA7.py`, Non-Tree Mode Only):**
   - **`parseAssignStat_tac()`:**
     - Consumes `ID` (LHS)
     - Looks up LHS symbol (`symbol_table.lookup`)
     - Gets `dest_place` (`tac_gen.getPlace(lhs_symbol)`)
     - Matches `ASSIGN`
     - Calls `parseExpr_tac()` to get `src_place`
     - Emits TAC (`tac_gen.emitAssignment(dest_place, src_place)`)
   - **`parseExpr_tac()`:**
     - Calls `parseTerm_tac()` (or `parseSimpleExpr_tac`)
     - Returns the `place` string received
   - **`parseTerm_tac()`:**
     - Calls `parseFactor_tac()`
     - Returns the `place` string received
   - **`parseFactor_tac()`:**
     - If `ID`: Match, lookup symbol, `place = tac_gen.getPlace(symbol)`, return `place`
     - If `NUM` or `REAL`: Match, get lexeme, `place = tac_gen.getPlace(lexeme)`, return `place`
     - Other cases (e.g., `(`): Report error or return placeholder

3. **Testing:**
   - Run `python JohnA7.py assignments/A7_3_Address_Code/test71.ada`
   - Compare `test71.tac` with `exp_test71.tac`

---

### Increment 2b: Locals & Parameters in Expressions (test72.ada)

**Goal:** Extend TAC generation to handle local variables and parameters with correct offsets.

**Target Test File:** `test72.ada`

**Detailed Plan:**

- **NO CODE CHANGES NEEDED**: The `getPlace()` function in `TACGenerator.py` already correctly handles:
  - Globals (depth 1): returns variable name
  - Locals (depth > 1): returns `_BP{offset}` (offset already negative)
  - Parameters (depth > 1): returns `_BP+{offset}`

- **Testing:** Run `test72.ada`, compare output TAC with expected TAC, verify BP offsets are correct

---

### Increment 2c: Basic Arithmetic Expressions (test73.ada)

**Goal:** Implement TAC generation for simple expressions involving `+`, `-` operators (at the `SimpleExpr` level) using temporary variables.

**Target Test File:** `test73.ada`

**Detailed Plan:**

- **Modify `parseExpr_tac` / Implement `parseSimpleExpr_tac`:**
  - Parse the first `Term` using `parseTerm_tac()` to get `left_place`
  - Loop while `current_token` is `ADDOP` (`+` or `-`):
    - Save the operator (`op`)
    - Match the `ADDOP`
    - Parse the next `Term` using `parseTerm_tac()` to get `right_place`
    - Generate a new temporary variable name: `temp_place = tac_gen.newTemp()`
    - Emit the arithmetic TAC: `tac_gen.emitBinaryOp(op, temp_place, left_place, right_place)`
    - Update `left_place = temp_place` for the next iteration
  - Return the final `left_place`

- **Verify `emitBinaryOp` function works correctly**

- **Testing:** Run `test73.ada`, compare output TAC

---

### Increment 2d: Multiplication/Division (test74.ada, test75.ada)

**Goal:** Implement TAC generation for `*` and `/` operators (at the `Term` level).

**Target Test Files:** `test74.ada`, `test75.ada`

**Detailed Plan:**

- **Modify `parseTerm_tac`:**
  - Similar structure to `parseSimpleExpr_tac`
  - Parse the first `Factor` using `parseFactor_tac()` to get `left_place`
  - Loop while `current_token` is `MULOP` (`*` or `/`):
    - Save the operator (`op`)
    - Match the `MULOP`
    - Parse the next `Factor` using `parseFactor_tac()` to get `right_place`
    - Generate temporary: `temp_place = tac_gen.newTemp()`
    - Emit TAC: `tac_gen.emitBinaryOp(op, temp_place, left_place, right_place)`
    - Update `left_place = temp_place`
  - Return the final `left_place`

- **Testing:** Run `test74.ada` and `test75.ada`, compare output TAC

---

### Increment 2e: Parenthesized Expressions

**Goal:** Ensure `parseFactor_tac` correctly handles parenthesized expressions `( Expr )`.

**Detailed Plan:**

- **Modify `parseFactor_tac`:**
  - If `current_token` is `LPAREN`:
    - Match `LPAREN`
    - Call `parseExpr_tac()` to get the `place` of the inner expression
    - Match `RPAREN`
    - Return the `place` received from `parseExpr_tac()`

- **Testing:** Use test cases with parentheses (several existing test files)

---

### Increment 2f: Procedure Calls (Initial - differentiating from assignment)

**Goal:** Update `parseSeqOfStatements` to differentiate between an assignment (`ID := ...`) and a simple procedure call (`ID;` or `ID(...);`).

**Detailed Plan:**

- **Enhance `parseSeqOfStatements`:**
  - When an `ID` is encountered:
    - Look ahead: If next token is `ASSIGN`, handle as assignment (call `parseAssignStat_tac`)
    - Look ahead: If next token is `SEMICOLON` or `LPAREN`, identify as a procedure call
    - **Procedure Call Handling (Non-Tree):**
      - Consume the `ID`
      - If `LPAREN`, call a (potentially dummy for now) `parseProcCallArgs_tac()` to consume arguments and `RPAREN`
      - Do *not* emit any TAC for the call itself in this increment
      - Ensure the final `SEMICOLON` of the statement is matched

- **Testing:** Use `test75.ada` which contains procedure calls