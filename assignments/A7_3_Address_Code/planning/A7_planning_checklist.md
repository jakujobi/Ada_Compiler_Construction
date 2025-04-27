# Assignment 7 – Three-Address Code (TAC)
## Master Planning Checklist  
*Version: 2025-04-26*

> This document captures **all planning artefacts** we need **before any implementation work**. Treat each numbered section as a lightweight sub-plan.  Keep it updated as we discover new information.

| # | Plan / Section | Purpose | Must Contain |
|---|----------------|---------|--------------|
| 1 | **Requirements Clarification** | Record exactly what the instructor / assignment demands | • Bullet list of every rule (addressing, `START`, temp naming, file naming, etc.)  <br>• Any implicit rule pulled from lecture or notes  <br>• Open questions & who will resolve them |
| 2 | **Glossary & Conventions** | Single source of naming truth | • Definitions for *depth*, *offset*, *ARG*, etc.  <br>• Naming conventions for files, temps (`_t1…`), labels, procedures |
| 3 | **Architecture Diagram** | Visual of pipeline & artefact flow | • Boxes for phases (Lexer → Parser → SymTable → SemAnalyzer → TACGen → Driver)  <br>• Arrows labelled with produced artefacts (Tokens, ParseTree, SymbolTable, TAC) |
| 4 | **Component Design Specs** | Mini-spec for each source file | For every component to build / edit:  <br>• Role description  <br>• Public API / key method signatures  <br>• Internal helpers  <br>• Error-handling strategy |
| 5 | **Data-Structure Spec** | Prevent cross-phase mismatch | • `ParseTree` node kinds & fields  <br>• `SymbolTableEntry` layout (`name, kind, depth, offset, literal_value …`)  <br>• `TACInstruction` schema |
| 6 | **Algorithm Flowcharts / Pseudocode** | Nail tricky logic early | • Expression visitor temp algorithm  <br>• Procedure-call TAC emission  <br>• Offset calculation rules |
| 7 | **Work-Breakdown Structure (WBS)** | Detailed task list & owners | • Task → Sub-tasks → Estimated hours  <br>• Dependencies / critical path notes |
| 8 | **Timeline / Milestones** | Keep delivery on track | • Calendar dates or sprint numbers  <br>• Checkpoints: parser green, first TAC file generated, full test suite passes |
| 9 | **Risk & Mitigation Log** | Surface issues proactively | • Risk description  <br>• Likelihood / impact rating  <br>• Mitigation or contingency plan |
|10 | **Test Plan** | Define done-ness objectively | • Unit tests per phase  <br>• Integration cases (5 key Ada programs)  <br>• Expected `.TAC` outputs  <br>• Pass/fail criteria |
|11 | **Code-Review Checklist** | Gate quality before merge | • Style guide adherence  <br>• Offset/address correctness  <br>• Exception handling  <br>• Unit-test coverage ≥ agreed threshold |
|12 | **Documentation & Delivery** | Smooth hand-off to graders & future assignments | • README updates  <br>• Exactly how to run driver & tests  <br>• Locations of generated `.TAC` files  <br>• Any dev-environment notes |

---

### How to Use This File
1. Create a sub-heading for each item above and start filling details.
2. Keep table as high-level index; deeper notes live under headings below.
3. When a section is *ready*, mark the checkbox ✓ in the table row.

---

<!-- Below are the blank section stubs. Expand as the project evolves. -->

## 1. Requirements Clarification  
*(Fill in bullet list of explicit and implicit rules)*

## 2. Glossary & Conventions

## 3. Architecture Diagram

## 4. Component Design Specs

### RDParserExtended.py

*   **Objective**: Update the parser to handle the extended grammar including procedure calls alongside assignments.
*   **Tasks**:
    *   Modify `parseAssignStat`: Implement lookahead (e.g., check if the token after an `idt` is `:=` or `(`) to differentiate between assignments (`idt := Expr`) and procedure calls (`idt ( Params )`). Route parsing accordingly.
    *   Implement New Parsing Methods: Create `parseProcCall`, `parseParams`, and `parseParamsTail` to handle the structure of procedure calls and their arguments. Preserve argument order.
    *   Update Parse Tree: Ensure the `ParseTree` nodes clearly distinguish between `ASSIGN_STAT` and `PROC_CALL` node types. Parameters within `Params` should also be represented appropriately in the tree (`ACTUAL_PARAM` nodes).
*   **Rationale**: Essential groundwork to correctly recognize and structure the syntax involving procedure calls before semantic analysis or TAC generation.

### NewSemanticAnalyzer.py

*   **Objective**: Ensure the semantic analyzer accurately captures and stores all necessary information (depths, offsets, types, constant values) in the `SymbolTable` for the TAC generator.
*   **Tasks**:
    *   Verify Offsets:
        *   Confirm `_insert_variables` correctly calculates and stores `offset` in `SymbolTableEntry`: actual name for depth 1, negative `_BP-offset` (e.g., -2, -4) for depth > 1.
        *   Confirm `_visit_formals` correctly calculates and stores positive `_BP+offset` (e.g., +4, +6) for parameters.
    *   Add Helper: `addr_repr(entry)` → returns correct textual form (`x`, `_BP-2`, `_BP+4`).
    *   Verify Constants: Ensure `_insert_constants` makes the literal value of constants readily accessible.
    *   Procedure Call Semantics: Add semantic checks within the logic that processes `PROC_CALL` nodes (likely a new visitor method):
        *   Verify the called identifier exists in the symbol table and is of `Kind.PROCEDURE`.
        *   Check if the number of actual parameters matches the expected number for the procedure.
    *   Add Warning: Emit warning if a variable is named exactly `c` (MASM conflict).
*   **Rationale**: The TAC generator completely relies on the symbol table being accurate. Correct offsets and readily available constant values are crucial.

### TACGenerator.py

*   **Objective**: Create the module that traverses the annotated `ParseTree` and generates the list of TAC instructions.
*   **Tasks**:
    *   Define Core Structures:
        *   `TACInstruction`: Class to represent a single TAC instruction (fields like `op`, `result`, `arg1`, `arg2`). Use opcodes: `ASSIGN`, `ADD`, `SUB`, `MUL`, `DIV`, `UMINUS`, `ARG`, `CALL`, `START`.
        *   `TACProgram`: Class to hold the sequence of `TACInstruction` objects. Include methods like `add_instruction()`, `emit_start(prog_name)`, `new_temp()`, and `to_string()`.
    *   Implement `ThreeAddressCodeGenerator`:
        *   Visitor Pattern: Use methods like `visit_Program`, `visit_AssignStat`, `visit_ProcCall`, `visit_Expr`, etc.
        *   Temporary Variable Generator: Implement `_new_temp()`: Returns a unique temporary variable name (`_t1`, `_t2`, ...) and resets counter per procedure.
        *   Expression Evaluation: Recursively visit children, get results, generate new temporary (`temp_result`), generate TAC instruction (`ADD`, `SUB`, etc.), return `temp_result`.
        *   Variable/Constant Handling: `visit_Identifier` uses `addr_repr(entry)`. `visit_Number` returns literal lexeme.
        *   Assignment Handling: Visit `Expr` (gets `expr_result`), visit `idt` (gets `dest_repr`), generate `ASSIGN` TAC.
        *   Procedure Call Handling: Visit each actual parameter (`Expr`), generate TAC for evaluation (`param_result`), emit `ARG param_result`. Emit `CALL proc_name, num_params`.
        *   Program Start: `visit_Program` calls `self.program.emit_start(program_name)` and resets temp counter.
*   **Rationale**: Performs the core translation logic, converting parsed/analyzed structures into the required TAC format.

### JohnA7.py (Driver)

*   **Objective**: Orchestrate the full compilation pipeline from source code to `.TAC` file.
*   **Tasks**:
    *   Instantiate all compiler phase objects.
    *   Execute phases sequentially: `lexer -> parser -> semantic_analyzer -> tac_generator`.
    *   Extract the program name from the global symbol table (first `Kind.PROCEDURE`).
    *   Generate the output filename (`<input_name>.tac`).
    *   Call `tac_program.to_string()` to get the formatted TAC.
    *   Write the string to the output file, ensuring `START program_name` is the first line.
    *   Exit with non-zero code on any phase error.
*   **Rationale**: Provides the end-to-end workflow and produces the final required artifact.

## 5. Data-Structure Spec

*   `ParseTree` Nodes: Include `ASSIGN_STAT`, `PROC_CALL`, `ACTUAL_PARAM`.
*   `SymbolTableEntry`: Fields for `name, kind, depth, offset, literal_value, var_type`, potentially `param_mode`.
*   `TACInstruction`: Schema `(op: str, result: Optional[str], arg1: Optional[str], arg2: Optional[str])`. Use opcodes from `TACGenerator.py` spec.

## 6. Algorithm Flowcharts / Pseudocode

*(To be filled with details, e.g., for expression evaluation logic)*

## 7. Work-Breakdown Structure (WBS)

| Task | Sub-tasks | Est. hrs |
|------|-----------|----------|
| **Parser Update** | Add productions, implement `parseProcCall/Params`, 3 unit tests | 1.25 |
| **Semantic Tweaks** | `addr_repr` helper, warning for `c`, arg-count validation, run semantic tests | 1.0 |
| **TAC Scaffolding + Expr/Assign** | Create `TACInstruction`, `TACProgram`, temp helper, implement visitor for expressions & assignments | 1.5 |
| **Procedure Calls** | `ARG` emission, `CALL`, temp-reset logic, tests with 1 & 3 params | 1.5 |
| **Driver Integration** | Wire phases, write `.TAC`, non-zero exit on error | 0.75 |
| **Testing & Fixes** | Run 5-program matrix, diff results, bug fixes | 1.5 |
| **Buffer / Docs / Review** | Self-review, README, final commit | 1.0 |
| **Total** | — | **8.5** |

## 8. Timeline / Milestones

| Time-block | Deliverable | Activities | Buffer |
|------------|-------------|------------|--------|
| 08:00–08:30 | Env ready | Pull latest, open IDE, verify tests run | 0:10 |
| 08:30–09:45 | Parser updated + unit tests green | Implement grammar & tests | 0:15 |
| 10:00–11:00 | Semantic tweaks complete | Offsets helper, warning, validations | 0:15 |
| 11:15–12:45 | TAC scaffold + expr/assign visitor working | Basic `.TAC` for `a := 1+2` | 0:15 |
| 12:45–13:30 | Lunch | — | — |
| 13:30–15:00 | Proc-call visitor done | `ARG` + `CALL` TAC, multi-param test | 0:15 |
| 15:15–16:00 | Driver wired | Full pipeline writes `.TAC` | 0:15 |
| 16:00–17:30 | Test matrix run | Execute five Ada programs, fix defects | 0:30 |
| 17:30–18:00 | Code review & commit | Checklist pass, push | 0:10 |
| 18:00–19:00 | Final buffer | Unexpected issues, README polish | — |

<!-- Mark ✓ next to a block as it completes -->

## 9. Risk & Mitigation Log

## 10. Test Plan

*   **Objective**: Ensure the generated TAC is correct according to assignment specifications for various inputs.
*   **Unit Tests**: Add tests for `parseProcCall`, `addr_repr`, `_new_temp`, expression TAC generation snippets.
*   **Integration Tests / Acceptance Cases**:
    *   Utilize provided test files (`test7_*.ada`, examples from notes).
    *   Create targeted tests for:
        *   Assignments to/from depth 1 variables.
        *   Assignments to/from depth > 1 variables (`_BP-offset`).
        *   Usage of parameters (`_BP+offset`) within expressions.
        *   Expressions with various operators and constants.
        *   Procedure calls with zero, one, and multiple parameters (using variables/constants as actuals).
        *   Variable named `c` (check for warning).
        *   Nested procedure referencing outer variable.
*   **Verification**: Manually inspect generated `.TAC` files for correctness against the rules (addressing, temporaries, instruction sequence, `START` line, filename). Compare against hand-derived expected outputs.
*   **Rationale**: Confirms the implementation meets all functional requirements and handles different language constructs accurately.

## 11. Code-Review Checklist

## 12. Documentation & Delivery Plan
