# A8 Support: Plan for Updating Existing Compiler Modules

## 1. Introduction & Strategy

* **Purpose:** This document outlines the specific modifications required within the existing compiler modules (`Definitions.py`, `LexicalAnalyzer.py`, `RDParserExtExt.py`, `TACGenerator.py`, `NewSemanticAnalyzer.py`, `SymTable.py`, `Driver.py`) to fully support the requirements of Assignment 8 (TAC to 8086 Assembly Generation). It also details how to verify these changes.
* **Integration:** Assignment 8 builds directly upon the output (TAC file and Symbol Table state) of the preceding compiler phases. Therefore, ensuring these components correctly handle new grammar, generate appropriate TAC, and store necessary information is crucial *before* or *concurrently with* implementing the `ASMGenerator`.
* **Recommended Implementation Strategy:** Use **Git branching**. Create a dedicated branch (e.g., `assignment-8`) from your working Assignment 7 commit. All modifications described below should be made on this branch to isolate changes and protect the working state of previous assignments. Add the new `ASMGenerator` components to this branch as well.

## 2. Module: `Definitions.py`

### Changes Needed:
    * **Add New Token:** Ensure the `TokenType` enumeration includes `PUTLN` (assuming `GET` and `PUT` already exist from previous assignments).
        ```python
        # Example addition to TokenType enum members list
        'PUTLN',
        ```
    * **Add Reserved Words:** Add `"PUTLN"` to the `reserved_words` dictionary, mapping it to `self.TokenType.PUTLN`. Ensure `"GET"` and `"PUT"` are already mapped correctly to `self.TokenType.GET` and `self.TokenType.PUT`.
        ```python
        # Example addition to reserved_words dictionary
        "GET": self.TokenType.GET,
        "PUT": self.TokenType.PUT,
        "PUTLN": self.TokenType.PUTLN,
        ```

### Verification:
    * Run existing unit tests for `Definitions.py` (if any) or manually inspect the `reserved_words` dictionary and `TokenType` enum to confirm setup.
    * Run the updated `LexicalAnalyzer` (see below) on source code containing `get`, `put`, `putln` and verify they are tokenized correctly with `TokenType.GET`, `TokenType.PUT`, `TokenType.PUTLN`, not as identifiers (`TK_IDENTIFIER`).

### Module: `LexicalAnalyzer.py`

* **Changes Needed:** No direct code changes are likely needed within `LexicalAnalyzer.py` itself, as its behavior is driven by the data in `Definitions.py`. It will automatically recognize the new keywords once they are added to the `reserved_words` dictionary in `Definitions.py`.
* **Verification:**
    * Execute the Lexical Analyzer phase (e.g., via the Driver or standalone tests) on Ada source files containing `get`, `put`, and `putln` statements.
    * Verify the output token stream correctly identifies these words with their specific TokenTypes (e.g., `TK_GET`, `TK_PUT`, `TK_PUTLN`) instead of `TK_IDENTIFIER`.

### Module: Parser (`RDParserExtExt.py` & Mixins - likely `rd_parser_mixins_statements.py`)

### Changes Needed:
    * **Implement I/O Grammar Rules:** Create new parsing methods corresponding to the BNF productions for `IO_Stat`, `In_Stat`, `Out_Stat`, `Id_List`, `Write_List`, `Write_Token`, etc. These methods will handle matching the expected tokens (`TokenType.GET`, `TokenType.PUT`, `TokenType.PUTLN`, `TokenType.LPAREN`, etc.).
    * **Integrate I/O Parsing:** Modify the existing `Parse_Statement` (or equivalent) method to recognize the start of an I/O statement (e.g., seeing `TokenType.GET`, `TokenType.PUT`, `TokenType.PUTLN`) and dispatch to the new `Parse_IO_Stat` method.
    * **Semantic Action Calls:** Within the new I/O parsing methods, insert calls to the `TACGenerator` to emit the appropriate I/O TAC instructions (`rdi`, `wrs`, `wri`, `wrln`). This includes:
        * Passing the target variable's address/operand string for `rdi`.
        * Passing the correct operand string (variable address, numeric literal representation, or *string label*) for `wri` or `wrs`.
        * Handling the list structure for `get`/`put`/`putln` (generating multiple `rdi`/`wri`/`wrs` calls if needed).
        * Calling the `wrln` emission after processing the list for `putln`.
        * **String Literal Handling:** When a `TK_STRINGLIT` is encountered in `Write_Token`, the parser (or a called semantic action) must:
            1.  Get the string value from the token.
            2.  Interface with the `SymbolTable` (or a dedicated manager) to store this literal and obtain a unique label (e.g., `_S0`).
            3.  Pass this *label* to the `TACGenerator` for the `wrs` instruction.
        * **Pass-by-Reference for Procedure Calls:** When parsing a procedure call (`CALL ProcName(Arg1, Arg2, ...)`), for each argument corresponding to a parameter declared as `OUT` or `IN OUT` in `ProcName`'s signature (information retrieved from the Symbol Table entry for `ProcName`), the parser/semantic action must signal the `TACGenerator` to emit `push @Arg` (pushing the *address* of the argument variable) instead of `push Arg` (pushing the value).

### Verification:
    * Create Ada test files containing various valid `get`, `put`, and `putln` statements (with single/multiple arguments, different argument types).
    * Run the Parser phase. Verify it parses these statements without syntax errors.
    * Enable TAC generation and verify the *correct sequence* of `rdi`, `wrs`, `wri`, `wrln` instructions are generated in the `.tac` file for each I/O statement.
    * Specifically check that string literals in `put`/`putln` result in `wrs _SLabel` TAC, and that appropriate labels (`_S0`, `_S1`...) are used.
    * Check that `get(Var)` results in `rdi VarAddress` TAC.
    * Check that `putln` results in appropriate `wrs`/`wri` calls followed by `wrln`.

### Module: `TACGenerator.py`

### Changes Needed:
    * **New Emission Methods:** Add methods like `emit_read_int(dest_operand)`, `emit_write_int(src_operand)`, `emit_write_string(label_operand)`, `emit_write_newline()`. These methods will format and append the corresponding TAC lines (`rdi ...`, `wri ...`, `wrs ...`, `wrln`) to the TAC output.
    * **Handle `push @Var`:** Ensure the existing `emit_push` (or similar) method can distinguish between pushing a value and pushing an address (reference). It might need an extra argument or a separate method `emit_push_reference(address_operand)` that prepends the `@` symbol or uses a distinct internal representation recognized by the `ASMGenerator`. The *caller* (semantic action in Parser/Analyzer) determines when to call the reference version.

### Verification:
    * Unit test the new `emit_` methods to ensure they produce the correctly formatted TAC strings.
    * Perform integration testing by running the full Parser->TACGenerator pipeline with the updated Parser actions calling these new methods. Verify the output `.tac` file contains the expected I/O instructions with correct operands.
    * Test the pass-by-reference push mechanism by creating a scenario requiring `push @Var` and verifying the TAC output.

### Module: `NewSemanticAnalyzer.py`

### Changes Needed:
    * **Calculate & Store Procedure Sizes:** When analyzing a procedure declaration (`PROCEDURE Name ... IS ... BEGIN ... END Name;`), traverse the declarations and the body:
        1.  Sum the `size` of all declared local variables.
        2.  Track the maximum number/size of temporary variables generated by the `TACGenerator` during expression/statement processing within this procedure.
        3.  Sum the `size` of all declared parameters.
        4.  Store the total calculated `SizeOfLocals` (sum of declared locals **plus** space for temps) and `SizeOfParams` as attributes in the `SymbolTable` entry for `Name`.
    * **Initiate String Literal Handling:** While parsing `put`/`putln` arguments (or during semantic checks on them), if a string literal is identified, this module (or the Parser action calling it) should invoke the mechanism to store the literal and get its label from the `SymbolTable`. This ensures the label is available when the `TACGenerator` is called.

### Verification:
    * After running the Semantic Analysis phase on code with procedures having various numbers of parameters and local variables/temps, inspect the `SymbolTable` dump or use debugger/unit tests.
    * Verify that the `SymbolTable` entries for procedures correctly store the calculated `SizeOfLocals` and `SizeOfParams`.
    * Verify that processing `put` statements with string literals results in appropriate entries being created in the `SymbolTable` (or string table) mapping labels to `$`-terminated values.

### Module: `SymbolTable.py`

### Changes Needed (Implementation & Verification):
    * **Implement/Verify Procedure Size Fields:** Ensure the data structure for procedure entries includes fields for `size_of_locals: int` (total bytes for locals + temps) and `size_of_params: int` (total bytes). Add these fields if they do not exist.
    * **Implement/Verify String Literal Storage:** Ensure a mechanism exists to store string literals associated with labels (e.g., a specific `EntryType` like `STRING_LITERAL_ENTRY`, or as part of a `CONSTANT` entry). Add this capability if missing. Ensure `lookup` can retrieve the string value given the label.
    * **Implement/Verify Parameter Flag:** Ensure a clear way exists (e.g., `is_parameter: bool` field) to distinguish parameters from local variables at the same scope/depth. Add this flag if missing.
    * **Verify Offset Representation:** Review how offsets are currently stored. Ensure the stored value, combined with the `isParameter` flag and `depth`, provides enough information for the `ASMOperandFormatter` to calculate the correct `[bp+/-X]` string.
### Verification:
    * Write comprehensive unit tests for `SymbolTable.py`.
    * Test inserting and retrieving procedure entries, specifically checking if `size_of_locals` and `size_of_params` can be stored and read back correctly.
    * Test inserting and retrieving string literal entries, checking if the label maps correctly to the original string value.
    * Test lookup for parameters vs. locals to ensure the `isParameter` flag (or equivalent) is set and retrieved correctly.

### Module: `Driver.py` (and specific `JohnA8.py`)

### Changes Needed:
    * Modify the main execution flow in the driver script (`JohnA8.py` or the class it inherits from `Driver.py`).
    * After the existing call to generate TAC (likely involving `LexicalAnalyzer`, `RDParserExtExt`, `NewSemanticAnalyzer`, `TACGenerator`), add a new step:
        1.  Instantiate the `ASMGenerator` (and its sub-components if using the split design). Pass the path to the generated `.tac` file, the desired output `.asm` file path, and the fully populated `SymbolTable` object instance to its constructor.
        2.  Call the main generation method (e.g., `asm_generator.generate_asm()`).
### Verification:
    * Run the complete driver (`python JohnA8.py sourcefile.ada`).
    * Verify that after successful execution (no crashes), both the `.tac` file and the `.asm` file exist.
    * Confirm the driver correctly passes the necessary inputs (file paths, symbol table) to the `ASMGenerator`.

### 9. Overall Testing & Integration Strategy

* **Unit Testing:** Test changes within each modified module using specific unit tests (as described above) and mocks where necessary.
* **Incremental Integration Testing:** After modifying interdependent modules (e.g., Parser and TACGenerator for I/O), run the compiler pipeline up to the point of the change. For example, after updating Parser and TACGenerator, run Ada -> TAC and verify the `.tac` output contains correct I/O instructions and string labels. After updating Semantic Analyzer and Symbol Table, verify procedure sizes and string literal storage.
* **End-to-End Testing (A8 Context):** Once the `ASMGenerator` is partially or fully implemented *and* the necessary updates above are done, run the *full* pipeline (Ada -> ASM) on targeted test cases. Start with simple cases testing specific features (globals, then procedures, then locals, then I/O, then params) before moving to the official A8 test files.

---