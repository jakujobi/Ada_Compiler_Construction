# Assignment 7 - Phase 1 Implementation Plan: Offset Calculation

**Version:** 2025-04-27

**Goal:** Implement the logic within `RDParserA7.py` to calculate and store byte offsets and sizes for local variables and parameters in the `SymbolTable`, populating the `offset`, `size`, `var_type`, and `param_mode` attributes of `Symbol` objects as required by the main plan (`A7_Main_plan.md`).

## 1. Prerequisite: Define Data Type Sizes

*   **Action:** Add a constant dictionary mapping `VarType` enums to their byte sizes in `RDParserA7.py`.
*   **Location:** Near the top of `src/jakadac/modules/RDParserA7.py`.
*   **Code:**
    ```python
    from .SymTable import VarType # Ensure VarType is imported

    TYPE_SIZES = {
        VarType.INT: 2,
        VarType.FLOAT: 4,  # Assuming REAL is alias for FLOAT
        VarType.BOOLEAN: 1, # Standard assumption
        VarType.CHAR: 1     # Standard assumption
        # Add other types if they become necessary
    }
    ```
*   **Verification:** Ensure all types used in test cases (`test71.ada` - `test75.ada`) are included.

## 2. Implement Local Variable Offset Calculation

*   **Target Function:** `RDParserA7.parseDeclarativePart()`
*   **Supporting Function:** `RDParserA7.parseProg()`
*   **State Tracking:**
    *   Add an instance variable `self.current_local_offset: int` to `RDParserA7`.
    *   In `parseProg`, **before** calling `parseDeclarativePart` for a procedure, initialize `self.current_local_offset = -2`.
*   **Logic Modification in `parseDeclarativePart`:**
    1.  **After** parsing `IdentifierList` and `TypeMark`:
        *   Get the `var_type: VarType` returned by `parseTypeMark`. Handle potential errors if `parseTypeMark` fails or returns an unsupported type.
        *   Get the `size: int = TYPE_SIZES.get(var_type)`. Handle potential errors if `var_type` is not in `TYPE_SIZES`.
        *   Iterate through each identifier token (`id_leaf`) in the `IdentifierList`:
            *   Look up the corresponding symbol (which should have just been inserted): `symbol = self.symbol_table.lookup(id_leaf.token.lexeme, lookup_current_scope_only=True)`. Handle potential `SymbolNotFoundError`.
            *   Update the symbol's attributes:
                *   `symbol.var_type = var_type`
                *   `symbol.size = size`
                *   `symbol.offset = self.current_local_offset`
            *   Decrement the offset for the next local variable: `self.current_local_offset -= size`.
*   **Logic Modification in `parseProg`:**
    1.  Get the procedure's `Symbol` object (`proc_symbol`) after parsing the procedure name.
    2.  **After** the `parseDeclarativePart` call completes:
        *   Calculate the total size: `total_local_size = abs(self.current_local_offset) - 2` (since it starts at -2).
        *   Store the size on the procedure symbol: `proc_symbol.local_size = total_local_size`.

## 3. Implement Parameter Offset Calculation

*   **Target Function:** `RDParserA7.parseArgs()` (and its potential helper/sub-rules)
*   **Supporting Function:** `RDParserA7.parseProg()`
*   **State Tracking:**
    *   Add an instance variable `self.current_param_offset: int` to `RDParserA7`.
    *   In `parseProg`, **before** calling `parseArgs`, initialize `self.current_param_offset = +4`.
*   **Logic Modification in `parseArgs` (Two-Phase Approach):**
    1.  **Phase 1: Collection:**
        *   Modify the parsing logic to collect all parameter specifications into a temporary list. Each entry should store `(name_token: Token, mode: ParameterMode, var_type: VarType)`.
        *   **During collection:** Insert the `Symbol` for each parameter into the `SymbolTable` (setting `EntryType.PARAMETER` and `depth`). This allows for duplicate checks within the parameter list.
    2.  **Phase 2: Offset Assignment (Reverse Iteration):**
        *   **After** the entire parameter list has been parsed and collected:
        *   Iterate through the `collected_params` list **in reverse order**.
        *   For each `(name_token, mode, var_type)`:
            *   Get the `size: int = TYPE_SIZES.get(var_type)`. Handle potential errors.
            *   Look up the corresponding symbol: `symbol = self.symbol_table.lookup(name_token.lexeme, lookup_current_scope_only=True)`. Handle potential `SymbolNotFoundError`.
            *   Update the symbol's attributes:
                *   `symbol.size = size`
                *   `symbol.offset = self.current_param_offset`
                *   `symbol.param_mode = mode` (Ensure `ParameterMode` enum is imported/accessible).
                *   `symbol.var_type = var_type` (Ensure this is set if not done during collection).
            *   Increment the offset for the *next* parameter (which is previous in the declaration list): `self.current_param_offset += size`.
*   **Logic Modification in `parseProg`:**
    1.  Get the procedure's `Symbol` object (`proc_symbol`).
    2.  **After** the `parseArgs` call completes:
        *   Calculate the total size: `total_param_size = self.current_param_offset - 4`.
        *   Store the size on the procedure symbol: `proc_symbol.param_size = total_param_size`.

## 4. Verification (Manual & Automated)

*   **Manual:** Use logging (`logger.debug`) within the offset calculation logic to trace assigned offsets and sizes for variables and parameters. Manually inspect the `SymbolTable` state after parsing procedures with locals and parameters. Create stack diagrams as suggested in `A7_Main_plan.md`.
*   **Automated:** Run end-to-end tests (`test74.ada`, `test75.ada`) which involve locals and parameters. While the TAC output won't be fully correct yet, use `TACGenerator.getPlace()` calls (even if just logged for now) to verify that the correct `_BP+N` and `_BP-N` representations are generated based on the calculated offsets.

## 5. Phase 1 Test Plan

**Goal:** Verify that `Symbol.offset`, `Symbol.size`, `Symbol.var_type`, `Symbol.param_mode`, `Symbol.local_size`, and `Symbol.param_size` are correctly calculated and populated by the parser before TAC generation relies heavily on them.

*   **Logging/Instrumentation:**
    *   Add `logger.debug` statements within `parseDeclarativePart` immediately after updating a local variable symbol. Log: `Symbol Name`, `VarType`, `Assigned Size`, `Assigned Offset`.
    *   Add `logger.debug` statements within the second phase (reverse iteration) of `parseArgs` immediately after updating a parameter symbol. Log: `Symbol Name`, `VarType`, `ParamMode`, `Assigned Size`, `Assigned Offset`.
    *   Add `logger.debug` statements in `parseProg` after calling `parseArgs` and `parseDeclarativePart` to log the procedure symbol's calculated `local_size` and `param_size`.

*   **Manual Log Inspection:**
    *   Run the parser (`JohnA7.py` driver, perhaps with a flag to stop after parsing or just focus on logs) on test files containing locals and parameters (e.g., `test74.ada`, `test75.ada`). Create simpler, targeted test cases if needed.
    *   Examine the debug logs carefully:
        *   Verify local variable offsets start at `-2` and decrease according to `TYPE_SIZES` (e.g., INT: -2, next INT: -4; INT: -2, next FLOAT: -6).
        *   Verify parameter offsets start at `+4` and increase according to `TYPE_SIZES`, *reflecting the reverse assignment order* (e.g., for `P1: INT; P2: FLOAT`, P2 gets offset +4, P1 gets offset +8).
        *   Verify `var_type` and `param_mode` match the source code declarations.
        *   Verify the final `local_size` and `param_size` logged for the procedure symbol correctly sum the sizes of all locals and parameters, respectively.

*   **Stack Diagram Verification:**
    *   For a non-trivial procedure (like `ProcParams` in `test75.ada`), manually draw the activation record layout showing the return address, static link (if applicable, though likely not needed for A7), dynamic link (BP), parameters (P3, P2, P1 starting at BP+4 upwards), and local variables (L1, L2, L3 starting at BP-2 downwards).
    *   Compare the offsets in the diagram to the offsets reported in the logs.

*   **Early `getPlace` Testing (Optional but Recommended):**
    *   If the `TACGenerator` instance is available in the parser (`self.tac_generator`), temporarily add calls like `place = self.tac_generator.getPlace(symbol)` after assigning offsets in `parseDeclarativePart` and `parseArgs`.
    *   Log the resulting `place` string.
    *   Verify that the string format matches the requirements (`_BP-N`, `_BP+N`, or `GlobalName`) based on the symbol's depth and newly assigned offset.