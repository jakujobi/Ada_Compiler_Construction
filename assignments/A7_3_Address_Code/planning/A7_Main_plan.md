# Assignment 7 – Three-Address Code (TAC) - Master Plan
*Version: 2024-04-26*

> This document captures **all planning artefacts** needed for Assignment 7. Treat each numbered section as a lightweight sub-plan. Keep it updated as we discover new information.

| # | Plan / Section                   | Purpose                                         | Status         |
|---|----------------------------------|-------------------------------------------------|----------------|
| 0 | **Implementation Strategy**      | Define the overall development approach         | Done           |
| 1 | **Requirements Clarification**   | Record exactly what the assignment demands      | **Enhanced**   |
| 2 | **Glossary & Conventions**       | Single source of naming truth                   | **Enhanced**   |
| 3 | **Architecture Diagram**         | Visual of pipeline & artefact flow              | Done           |
| 4 | **Component Design Specs**       | Mini-spec for each source file to modify/create | In Progress    |
| 5 | **Data-Structure Spec**          | Prevent cross-phase mismatch                    | **Enhanced**   |
| 6 | **Algorithm Flowcharts/Pseudocode**| Nail tricky logic early                         | **Enhanced**   |
| 7 | **Work-Breakdown Structure (WBS)**| Detailed task list & owners                   | Done (Initial) |
| 8 | **Timeline / Milestones**        | Keep delivery on track                          | Done (Initial) |
| 9 | **Risk & Mitigation Log**        | Surface issues proactively                      | **Enhanced**   |
| 10| **Test Plan**                    | Define done-ness objectively                    | **Enhanced**   |
| 11| **Code-Review Checklist**        | Gate quality before merge                       | To Do          |
| 12| **Documentation & Delivery**     | Smooth hand-off to graders & future assignments | To Do          |

---

## 0. Implementation Strategy: Test-Supported Incremental Development

This approach combines unit testing for core components with incremental feature implementation verified by end-to-end tests.

1.  **Phase 0: Setup & Foundation (TDD Focus)**
    *   Implement `TACGenerator.py` class structure.
    *   Write unit tests for `TACGenerator` methods (`newTemp`, `getPlace`, `emit*` variations) first, then implement methods to pass tests.
    *   Define type sizes/helpers in `SymTable.py` (with unit tests if applicable).
    *   Set up basic end-to-end test harness (run script -> compare `.tac` output).
    *   *Rationale:* Builds a reliable, testable `TACGenerator` foundation before complex integration.

2.  **Phase 1: Offset Calculation (Integration Testing Focus)**
    *   Implement offset calculation logic in `RDParserA7.py` (declarations/parameters), populating `Symbol.offset` and `Symbol.size`.
    *   Run end-to-end tests with locals/params (e.g., `test74`, `test75`).
    *   Debug using logging (`Logger`) to verify symbol table state and `getPlace` output in the generated TAC.
    *   Create visual stack frame diagrams to validate offset calculation.
    *   Add validation checks that verify offsets follow expected patterns.
    *   *Rationale:* Tackles complex Parser-SymTable interaction early, verifies result via TAC output.

3.  **Verification Checkpoint After Phase 1**
    *   Create and run specific tests just for offset calculation correctness.
    *   Verify through logging that locals start at BP-2 and decrease, while parameters start at BP+4 and increase.
    *   Create a visualization of at least one complex procedure's stack frame layout.
    *   *Rationale:* Ensures offset calculation is correct before proceeding to expression handling.

4.  **Phase 2: Basic Statements & Expressions (Incremental + End-to-End Testing)**
    *   **Increment 2a (Constants & Globals):** Modify `parseFactor`/`parseAssignStat`. Test `A := 5; B := A;`. Verify TAC.
    *   **Increment 2b (Locals/Params in Factor):** Ensure `parseFactor` uses `getPlace`. Test `_BP-2 := _BP+4;`. Verify TAC.
    *   **Increment 2c (Simple Binary Ops):** Add `+`/`-` logic. Test `test71.ada`. Verify temp usage.
    *   **Increment 2d (Other Ops/Precedence):** Add `*`, `/`, unary ops. Test `test72`, `test73`, complex expressions. Verify precedence via TAC.
    *   *Rationale:* Builds expression complexity incrementally, verifying each step with targeted tests.

5.  **Phase 3: Procedure Calls (Grammar + Integration Testing)**
    *   Implement procedure call grammar (`parseProcCall`, etc.) and `AssignStat` lookahead in parser.
    *   Integrate `emitPush` (checking mode) and `emitCall` actions.
    *   Add validation in `emitPush` to verify mode matches expected format.
    *   Create trace logs showing each parameter's resolved mode.
    *   Test with `test74`, `test75`, and additional mode-specific tests. Verify `push`/`push @`/`call` sequence.
    *   *Rationale:* Adds the final major syntax and TAC generation feature.

6.  **Phase 4: Finalization (End-to-End Testing)**
    *   Implement `emitProgramStart` logic and update driver (`JohnA7.py`).
    *   Run *all* test cases (`test71-75` plus additional edge case tests).
    *   Perform `diff` comparisons of generated vs. expected `.tac` files. Debug remaining issues.
    *   *Rationale:* Ensures all requirements are met across the full test suite.

**Benefits:** Balances TDD rigor for critical components with practical integration testing, manages complexity, provides early feedback, and reduces risk.

---

## 1. Requirements Clarification

**(Enhanced)**

*   **Source:** Derived primarily from `<a7>` description and clarified by examples/notes.
*   **Input:** Ada source file (`.ada`).
*   **Output:** Three-Address Code file (`<input_base>.tac`).
*   **File Naming:** `input.ada` -> `<input_base>.tac`.
*   **Variable Representation:**
    *   Depth 1 (Globals): Use the actual variable name (e.g., `A`). *Source: `<a7>`*.
    *   Depth > 1 (Locals/Params): Use Base Pointer (BP) offset notation (e.g., `_BP-2`, `_BP+4`). *Source: `<a7>`*.
*   **Offset Calculation:**
    *   Locals: Negative offsets (`_BP-offset`). Start at `_BP-2`, decreasing based on variable size. *Source: `<a7>` example interpretation, standard practice*.
    *   Parameters: Positive offsets (`_BP+offset`). Start at `_BP+4` for the *last* parameter pushed (corresponding to the first parameter declared due to Pascal L->R push). *Source: `<a7>` description & Pascal convention*.
    *   Base Address: `_BP` conceptually points to the saved Old BP location on the stack frame. *Source: Standard stack frame convention*.
    *   Variable Sizes: Assume sizes based on type (e.g., INT=2 bytes, FLOAT=4 bytes). *Assumption - Verify if specified elsewhere*.
*   **Constants:** Substitute literal values directly into TAC (e.g., `_t1 = 5`, `_t2 = B + 10`). *Source: `<a7>`*.
*   **Procedure Structure:** Enclose TAC for each procedure within `proc <name>` and `endp <name>` lines. *Source: Examples/Notes*.
*   **Program Start Directive:** The *last* line of the `.tac` file must be `start <outermost_proc_name>`. *Source: `<a7>`*.
*   **Procedure Calls:**
    *   New Grammar: Add productions for `AssignStat` (split), `ProcCall`, `Params`, `ParamsTail`. *Source: `<a7>`*.
    *   Parameter Passing: Push parameters onto stack left-to-right (as declared). *Source: `<a7>`*.
        *   `push <place>` for pass-by-value (`in` mode). *Source: `<a7>`*.
        *   `push @<place>` for pass-by-reference (`out`, `inout` modes). `@` signifies address. *Source: `<a7>`*.
    *   Call Instruction: Follow pushes with `call <procName>`. *Source: `<a7>`*.
*   **Temporaries:**
    *   Generate unique names (e.g., `_t1`, `_t2`, ...). *Source: Examples/Standard Practice*.
    *   Reset temporary counter for each procedure. *Source: Examples/Standard Practice*.
*   **MASM Conflict:** Check for and warn if a variable is named exactly `c`. *Source: Notes*.
*   **Operators:** Handle standard Ada expression operators: `+`, `-`, `*`, `/`, `mod`, `rem`, `and`, `or`, `not`, unary `+`, unary `-`. *Implicit requirement*.

---

## 2. Glossary & Conventions

**(Enhanced)**

*   **Depth:** Lexical nesting level.
    *   Depth 0: Conceptually, the level outside any procedure (not used for variables in this assignment).
    *   Depth 1: Global scope; variables declared directly inside the outermost procedure *or* truly global if supported (assume former based on `<a7>`).
    *   Depth >= 2: Locals/parameters declared within nested procedures.
*   **Offset:** Byte displacement from the Base Pointer (`BP`).
    *   Calculated relative to the conceptual location of the saved BP on the stack.
    *   `_BP-N`: N bytes below the saved BP (for locals).
    *   `_BP+N`: N bytes above the saved BP (for parameters).
*   **Place:** String representation of an operand or result location in TAC. Examples:
    *   Global variable: `"GVAR"`
    *   Local variable: `"\_BP-2"`
    *   Parameter: `"\_BP+6"`
    *   Temporary: `"\_t1"`
    *   Integer Constant: `"5"`
    *   Float Constant: `"3.14"` (Verify format if floats needed)
*   **Mode:** Parameter passing mode (`IN`, `OUT`, `INOUT` from `ParameterMode` enum). Determines `push` vs `push @`.
*   **Size:** Assumed byte size of data types: `INTEGER: 2`, `FLOAT: 4`. (Verify these assumptions).
*   **TAC Opcodes:** (Self-explanatory based on name, e.g., `ADD`, `SUB`, `ASSIGN`). `UMINUS` for unary minus. `PUSH` for value push, `PUSHA` for address push (`push @`).
*   **File Naming:** `<input_base>.ada` -> `<input_base>.tac`.
*   **Temporary Naming:** `_tN` where N is a 1-based integer, reset to 1 for each procedure scope.

---

## 3. Architecture Diagram

```mermaid
graph LR
    A[Ada Source (.ada)] --> B(LexicalAnalyzer);
    B --> C{Token Stream};
    C --> D(RDParserA7);
    D -- Accesses / Updates --> E(SymTable);
    D -- Drives --> F(TACGenerator);
    F --> G[TAC File (.tac)];

    subgraph Compiler Core
        B; C; D; E; F;
    end

    H(Driver: JohnA7.py) -.-> B;
    H -.-> D;
    H -.-> F;
    H -.-> G;
```
*(Arrows indicate primary data flow or control)*

---

## 4. Component Design Specs

### `SymTable.py`

*   **Objective**: Ensure the symbol table accurately captures and stores all necessary information (depths, offsets, sizes, types, constant values, modes) for the TAC generator.
*   **Implementation Details**:
    *   **`Symbol` Class:**
        *   Define/confirm byte sizes for `VarType` (e.g., `INT: 2`, `FLOAT: 4`). Store in `Symbol.size`.
        *   Ensure `Symbol.offset` field exists and is usable.
        *   Ensure `Symbol.param_modes` (dict mapping param name to `ParameterMode` on *procedure* symbol) exists.
        *   Ensure `Symbol.local_size` and `Symbol.param_size` fields exist on procedure/function symbols.
    *   **Offset Calculation Logic (to be integrated into `RDParserA7.py` logic):** See Algorithm section below. Key points: locals start at `-2` and decrease, params start at `+4` (for last param) and increase. Store `total_local_size` and `total_param_size`.
    *   **Constants:** Ensure `Symbol.const_value` stores the actual value for constants.
*   **Rationale**: TAC generation relies entirely on accurate symbol table info.

### `RDParserA7.py`

*   **Objective**: Update the parser to handle the extended grammar (including procedure calls), integrate offset calculation, and embed semantic actions to drive TAC generation.
*   **Implementation Details**:
    *   **Grammar Implementation:**
        *   Modify `parseAssignStat`: Implement lookahead (check token after `idt` for `:=` vs. `(`) to differentiate assignments and procedure calls.
        *   Implement `parseProcCall`, `parseParams`, `parseParamsTail`.
    *   **Offset Calculation Integration:**
        *   Implement the detailed offset calculation logic (see Algorithm section) within `parseArgs` and `parseDeclarativePart`.
    *   **TAC Generation Integration (Semantic Actions):**
        *   Pass `TACGenerator` instance during initialization or method calls.
        *   **Expression Parsing (`parseExpr`, `parseTerm`, `parseFactor`):** Return the **place** string. See Algorithm section.
        *   **Assignment (`parseAssignStat`):** Get `dest_place`, `source_place`. Call `tac_gen.emitAssignment(dest_place, source_place)`. Check assignability (LHS not constant).
        *   **Procedure Call (`parseProcCall`):** Lookup `proc_symbol`. Parse `Params` -> list of arg places. Get formal modes. Iterate args/modes: call `tac_gen.emitPush(arg_place, mode)`. Call `tac_gen.emitCall(proc_symbol.name)`.
        *   **Procedure Boundaries:** Call `tac_gen.emitProcStart`/`emitProcEnd`.
*   **Rationale**: Connects syntax, semantics (offsets), and TAC generation.

### `TACGenerator.py`

*   **Objective**: Create the module responsible for formatting and writing TAC instructions to the output file.
*   **Implementation Details**:
    *   **Class `TACGenerator`:**
        *   `__init__(self, output_filename)`: Stores filename, initializes `temp_counter = 0`, `tac_lines = []`.
        *   `emit(self, instruction_str)`: Appends formatted string to `tac_lines`.
        *   `_newTempName(self)`: `self.temp_counter += 1; return f\"_t{self.temp_counter}\"`.
        *   `newTemp(self)`: Returns result of `_newTempName()` (just the name).
        *   `getPlace(self, symbol_or_value)`: Returns string representation ("A", "\_BP-4", "\_t1", "5"). Checks symbol type, depth, constant status.
        *   `emitBinaryOp(self, op, dest_place, left_place, right_place)`: Format `dest = left op right`, map Ada ops (e.g., `rem`, `/` vs `div`) if needed, call `self.emit()`.
        *   `emitUnaryOp(self, op, dest_place, operand_place)`: Format `dest = op operand`, use `UMINUS`, call `self.emit()`.
        *   `emitAssignment(self, dest_place, source_place)`: Format `dest = source`, call `self.emit()`.
        *   `emitProcStart(self, proc_name)`: `self.emit(f\"proc {proc_name}\"); self.temp_counter = 0`.
        *   `emitProcEnd(self, proc_name)`: `self.emit(f\"endp {proc_name}\")`.
        *   `emitPush(self, place, mode)`: Emit `push place` or `push @place` based on mode.
        *   `emitCall(self, proc_name)`: Emit `call <proc_name>`.
        *   `emitProgramStart(self, main_proc_name)`: Store this name.
        *   `writeOutput(self)`: Open `output_filename`, write `f\"start {self.start_proc_name}\\n\"`, write all lines from `tac_lines`, close file.
*   **Rationale**: Encapsulates TAC formatting and file output.

### `JohnA7.py` (Driver)

*   **Objective**: Orchestrate the full compilation pipeline from source code to `.TAC` file.
*   **Implementation Details**:
    *   Construct output filename: `Path(input_file).with_suffix('.tac')`.
    *   Instantiate `LexicalAnalyzer`, `Definitions`, `SymTable`, `TACGenerator(output_filename)`.
    *   Instantiate `RDParserA7(tokens, defs, symbol_table, tac_generator=tac_gen)`.
    *   Call `parser.parse()`. Check for errors. Store/retrieve outermost procedure name (`start_proc_name`).
    *   Call `tac_gen.emitProgramStart(start_proc_name)`.
    *   Call `tac_gen.writeOutput()`.
    *   Handle exceptions, exit codes.
*   **Rationale**: End-to-end workflow execution.

---

## 5. Data-Structure Spec

**(Enhanced)**

*   **`SymTable.py` - `Symbol` Class Fields:**
    *   `name: str`
    *   `token: Token`
    *   `entry_type: EntryType` (VARIABLE, CONSTANT, PROCEDURE, PARAMETER, FUNCTION, TYPE)
    *   `depth: int`
    *   `var_type: Optional[VarType]` (INT, FLOAT, CHAR, BOOLEAN, etc.)
    *   `offset: Optional[int]` (Byte offset from BP for depth > 1)
    *   `size: Optional[int]` (Byte size, e.g., 2 for INT)
    *   `const_value: Any` (Actual value if constant)
    *   `param_list: Optional[List['Symbol']]` (For procedures/functions)
    *   `param_modes: Optional[Dict[str, ParameterMode]]` (Modes for params, stored on proc/func symbol)
    *   `return_type: Optional[VarType]` (For functions)
    *   `local_size: Optional[int]` (Total bytes of locals in proc/func)
    *   `param_size: Optional[int]` (Total bytes of params in proc/func)
*   **TAC Instruction Representation (Internal to `TACGenerator`):** Primarily strings. Consider a structured tuple `(opcode, dest, arg1, arg2)` only if complex manipulation is needed before emitting. Opcodes defined in Glossary.

---

## 6. Algorithm Flowcharts / Pseudocode

**(Enhanced)**

### Expression Evaluation (Conceptual - in Parser)

```python
# Returns the 'place' string where the result is stored
def parseExpr(self) -> str:
    # Handle unary +/- (if applicable at this level)
    # ...
    left_place = self.parseTerm()
    while current_token is addop: # Includes +, -, or
        op_token = self.current_token
        self.match(addop)
        right_place = self.parseTerm()
        result_place = self.tac_gen.newTemp() # Gets "_tN"
        # Map Ada op (op_token.lexeme) to TAC op if needed
        tac_op = map_ada_op_to_tac(op_token.lexeme)
        self.tac_gen.emitBinaryOp(tac_op, result_place, left_place, right_place)
        left_place = result_place # Result for next iteration
    return left_place

def parseFactor(self) -> str:
    if token is idt:
        symbol = symtable.lookup(lexeme)
        # Check if symbol found
        if symbol.entry_type == EntryType.CONSTANT:
             return str(symbol.const_value) # Substitute constant value
        else:
             return self.tac_gen.getPlace(symbol) # Returns name or _BP+/-offset
    elif token is numt:
        return lexeme # Literal number
    elif token is '(':
        self.match('(')
        place = self.parseExpr()
        self.match(')')
        return place
    elif token is nott:
        self.match(nott)
        operand_place = self.parseFactor()
        result_place = self.tac_gen.newTemp()
        self.tac_gen.emitUnaryOp("NOT", result_place, operand_place)
        return result_place
    elif token is signopt: # Unary +/-
        op = lexeme
        self.match(signopt)
        operand_place = self.parseFactor()
        result_place = self.tac_gen.newTemp()
        tac_op = "UMINUS" if op == '-' else "UPLUS" # Or handle UPLUS by omitting op
        if tac_op == "UPLUS":
             # Optimization: `+X` is just `X`
             return operand_place
        else:
             self.tac_gen.emitUnaryOp(tac_op, result_place, operand_place)
             return result_place
    # ... error handling ...
```

### Offset Calculation (Conceptual - in Parser during Declaration)

```python
# Within parseArgs, after collecting parameter_info_list = [(name, token, type, mode), ...]
proc_symbol = symtable.lookup(procedure_name)
proc_symbol.param_modes = {} # Initialize dict
next_param_offset = 4
total_param_size = 0
parameter_symbols = [] # Store created symbols if needed elsewhere

for param_name, param_token, param_type, param_mode in reversed(parameter_info_list):
    size = get_data_type_size(param_type) # Assume helper function
    param_symbol = Symbol(param_name, param_token, EntryType.PARAMETER, self.current_depth)
    param_symbol.set_variable_info(param_type, next_param_offset, size)
    try:
        self.symbol_table.insert(param_symbol)
        proc_symbol.param_modes[param_name] = param_mode # Store mode on proc symbol
        parameter_symbols.append(param_symbol)
        next_param_offset += size
    except DuplicateSymbolError as e:
        self.report_error(e) # Or semantic error
proc_symbol.param_size = next_param_offset - 4
proc_symbol.param_list = parameter_symbols # Store refs to param symbols

# Within parseDeclarativePart
proc_symbol = symtable.lookup(procedure_name) # Or get from context
next_local_offset = -2
total_local_size = 0
for local_name, local_token, local_type in locals_list:
    size = get_data_type_size(local_type)
    local_symbol = Symbol(local_name, local_token, EntryType.VARIABLE, self.current_depth)
    local_symbol.set_variable_info(local_type, next_local_offset, size)
    try:
        self.symbol_table.insert(local_symbol)
        next_local_offset -= size
        total_local_size += size
    except DuplicateSymbolError as e:
        self.report_error(e)
proc_symbol.local_size = total_local_size
# Store starting offset for temps if needed: proc_symbol.temp_start_offset = next_local_offset
```

---

## 7. Work-Breakdown Structure (WBS)

*(Estimates remain unchanged, Status updated)*

| Task                              | Sub-tasks                                                                | Est. hrs | Status  |
|-----------------------------------|--------------------------------------------------------------------------|----------|---------|
| **SymTable Prep**                 | Verify/add offset/size fields, Define type sizes                         | 0.5      | To Do   |
| **Parser: Offset Calc**           | Implement local & param offset logic in decl/arg parsing                 | 1.5      | To Do   |
| **Parser: Grammar Update**        | Add `ProcCall/Params` productions, handle `AssignStat` ambiguity           | 1.0      | To Do   |
| **TACGenerator: Core**            | Implement class, `emit`, `getPlace`, `newTemp`, file handling            | 1.5      | To Do   |
| **TACGenerator: Ops**             | Implement `emitBinaryOp`, `emitUnaryOp`, `emitAssignment`                | 1.0      | To Do   |
| **TACGenerator: Procs/Calls**     | Implement `emitProcStart/End`, `emitPush`, `emitCall`, `emitProgramStart`| 1.0      | To Do   |
| **Parser: Expr TAC Actions**      | Integrate TAC calls into `parseFactor`, `parseTerm`, `parseExpr`         | 1.5      | To Do   |
| **Parser: Statement TAC Actions** | Integrate TAC calls into `parseAssignStat`, `parseProcCall`                | 1.0      | To Do   |
| **Driver Integration**            | Instantiate TACGen, modify pipeline call, output handling                  | 0.5      | To Do   |
| **Testing & Debugging**           | Run tests `test71-75`, compare output, fix bugs                           | 2.0      | To Do   |
| **Docs & Cleanup**                | Update README, final review                                              | 0.5      | To Do   |
| **Total**                         |                                                                          | **12.0** |         |

---

## 8. Timeline / Milestones

*(Timeline remains a plausible target)*

*   **Day 1 AM:** SymTable Prep, Parser Offset Calc Logic.
*   **Day 1 PM:** Parser Grammar Update, TACGenerator Core implementation.
*   **Day 2 AM:** TACGenerator Ops & Proc/Call methods.
*   **Day 2 PM:** Parser Expr TAC Actions.
*   **Day 3 AM:** Parser Statement TAC Actions, Driver Integration.
*   **Day 3 PM:** Initial Testing (test71-73), Debugging.
*   **Day 4 AM:** Advanced Testing (test74-75, calls), Debugging.
*   **Day 4 PM:** Final Review, Docs & Cleanup.

---

## 9. Risk & Mitigation Log

**(Enhanced)**

| Risk                                   | Likelihood | Impact | Mitigation                                                                          | Status |
|----------------------------------------|------------|--------|-------------------------------------------------------------------------------------|--------|
| Incorrect Offset Calculation (Locals/Params)| Medium     | High   | Implement carefully per spec. Add debug logging. Create visual stack frame diagrams during implementation. Implement validation checks that verify offsets follow expected patterns (-2 decreasing for locals, +4 increasing for params). Add runtime assertions to catch invalid offsets. Compare with examples from Ada_Examples.md. | Open   |
| Incorrect "Place" Propagation in Expr  | Medium     | High   | Clear return value contracts for parse functions. Trace values during debugging. Create unit tests specifically for expression result propagation. Implement contract verification that checks place values match expected patterns. Add a helper function to validate place strings. | Open   |
| Handling `push @` vs `push` incorrectly| Medium     | Medium | Retrieve `mode` from `proc_symbol.param_modes` in `parseProcCall`. Pass mode to `tac_gen.emitPush`. Create specific test files for each parameter mode (IN/OUT/INOUT). Add validation in emitPush to verify mode matches expected format. Create a trace log showing each parameter's resolved mode. | Open   |
| Off-by-one errors in offsets/loops     | Medium     | Medium | Double-check start/end conditions (-2, +4). Test cases with 0, 1, N locals/params. | Open   |
| MASM reserved word conflict (`c`)      | Low        | Low    | Add check during `SymTable.insert` or parser declaration; emit warning log message. | Open   |
| Underestimating Debug Time           | High       | Medium | Allocate buffer time. Use `Logger` module extensively for tracing parser state, symbol lookups, and emitted TAC. | Open   |
| Ambiguity `idt :=` vs `idt (` not handled | Medium     | High   | Implement 1-token lookahead in `parseAssignStat` before consuming `idt`.          | Open   |
| Type size assumptions incorrect        | Low        | Medium | Verify type sizes if specified by course materials, else document assumptions clearly. | Open   |

---

## 10. Test Plan

**(Enhanced)**

*   **Objective**: Ensure the generated TAC adheres strictly to assignment specifications for correctness, formatting, and handling of various Ada constructs. Verify using unit tests for core components and integration tests for the end-to-end pipeline.
*   **Strategy**: Follow the "Test-Supported Incremental Development" strategy. Use `pytest` (or Python's `unittest`) for unit tests. Use file comparison (`diff` or Python `filecmp`) for end-to-end tests. Leverage the `Logger` for debugging integration issues.

*   **Unit Tests (Targeting `TACGenerator` and Helpers):**
    *   **`TACGenerator.newTemp()` / Reset:**
        *   Test: Call `newTemp()` multiple times -> Assert returns "_t1", "_t2", ...
        *   Test: Call `emitProcStart()`, then `newTemp()` -> Assert returns "_t1" (counter reset).
    *   **`TACGenerator.getPlace()`:**
        *   Setup: Create mock `Symbol` objects with varying `depth`, `entry_type`, `offset`, `name`, `const_value`.
        *   Test (Constant): `getPlace(5)` -> Assert returns `"5"`.
        *   Test (Global Var): `getPlace(Symbol(name='G', depth=1, type=VAR))` -> Assert returns `"G"`.
        *   Test (Global Const): `getPlace(Symbol(name='GC', depth=1, type=CONST, const_value=10))` -> Assert returns `"10"`.
        *   Test (Local Var): `getPlace(Symbol(name='L', depth=2, type=VAR, offset=-4))` -> Assert returns `"\_BP-4"`.
        *   Test (Param): `getPlace(Symbol(name='P', depth=2, type=PARAM, offset=6))` -> Assert returns `"\_BP+6"`.
        *   Test (Temp Name): `getPlace("_t3")` -> Assert returns `"\_t3"`. *(Confirm if temps are ever passed as Symbols)*.
        *   Test (Error Case): `getPlace(Symbol(name='Bad', depth=2, type=VAR, offset=None))` -> Assert raises appropriate error or returns error string.
        *   Test (Place Validation): Create a comprehensive test that examines all possible place string formats and verifies they match expected patterns.
    *   **`TACGenerator.emit<Op/Assign/Push/Call/Proc/etc.>()` Methods:**
        *   Setup: Instantiate `TACGenerator` potentially with a mock file/list for `emit`.
        *   Test (Binary): `emitBinaryOp("ADD", "_t1", "A", "_BP-2")` -> Assert internal `emit` was called with `"\_t1 = A ADD \_BP-2"` (or similar formatted string). Check Ada op mapping (e.g., `rem` -> `MOD`).
        *   Test (Unary): `emitUnaryOp("UMINUS", "_t2", "_BP+4")` -> Assert `emit` called with `"\_t2 = UMINUS \_BP+4"`.
        *   Test (Assign): `emitAssignment("_BP-6", "5")` -> Assert `emit` called with `"\_BP-6 = 5"`.
        *   Test (Push Value): `emitPush("A", ParameterMode.IN)` -> Assert `emit` called with `"push A"`.
        *   Test (Push Address): `emitPush("_BP-8", ParameterMode.OUT)` -> Assert `emit` called with `"push @\_BP-8"`.
        *   Test (Call): `emitCall("MyProc")` -> Assert `emit` called with `"call MyProc"`.
        *   Test (Proc/Endp): Verify correct `proc`/`endp` strings.
    *   **Offset Calculation Helpers (if created separately):**
        *   Unit test any isolated helper functions used for calculating offsets or determining type sizes.
        *   Test with 0, 1, and multiple parameters/locals to catch off-by-one errors.
        *   Verify through assertions that offsets follow expected patterns.

*   **Integration Tests / End-to-End Acceptance Cases (Using `.ada` -> `.tac`):**
    *   **Framework:** A script (or manual process) that:
        1.  Takes an input `.ada` file path.
        2.  Takes an expected output `.tac` file path.
        3.  Runs `JohnA7.py <input.ada>`.
        4.  Compares the generated `<input_base>.tac` with the expected file.
        5.  Reports PASS/FAIL.
    *   **Test Suite (`test71.ada` - `test75.ada` minimum):**
        *   **`test71.ada` (Simple Add, Globals):** Expected: `proc`, `endp`, `start`. Correct global names. `_t1 = B + C`, `A = _t1`.
        *   **`test72.ada` (Simple Mul, Globals):** Expected: Similar, but `_t1 = B * C`, `A = _t1`.
        *   **`test73.ada` (Mixed Precedence):** Expected: `_t1 = C * D`, `_t2 = B + _t1`, `A = _t2`. Verifies `*` before `+`.
        *   **`test74.ada` (Nested Proc, Calls, Locals/Globals/Params):** Expected: Correct `proc`/`endp` for both. `start fun`. Correct offsets for `inner`'s locals (`E`) and params (`C`, `D`). Correct use of globals (`A`, `B`) within `inner`. `push 10`, `push 20`, `call inner` sequence within `fun`. Temps reset for `inner`.
        *   **`test75.ada` (Params - Value/Ref):** Expected: Correct `_BP+` offsets. Correct `push <place>` vs `push @<place>` based on inferred parameter modes (`IN` vs `OUT`/`INOUT`). Correct usage of params/locals within the procedure.
    *   **Additional Integration Test Cases (Create if needed):**
        *   **Constants:** `A := 5; B := A + 10;` -> Verify constant substitution and usage.
        *   **Unary Ops:** `A := -B; C := not A;` -> Verify `UMINUS`/`NOT` op generation.
        *   **All Ops:** Specific tests for `mod`, `rem`, `and`, `or`.
        *   **Procedure Call (No Params):** `ProcZ();` -> Verify `call ProcZ`.
        *   **Procedure Call (Complex Args):** `ProcX(A+B, 5);` -> Verify expression for arg is evaluated into a temp first, then `push _tN` / `push 5`.
        *   **MASM Conflict (`c`):** File containing `c : integer;` -> Check log output for warning (no specific TAC change expected).
        *   **Additional Targeted Test Cases:**
            *   **Offset Validation (`test76.ada`):** Test procedures with 0, 1, and many parameters/locals to verify correct offsets.
            *   **Parameter Mode Coverage (`test77.ada`):** Create test with full coverage of IN/OUT/INOUT modes.
            *   **Expression Tree Validation (`test78.ada`):** Test with complex nested expressions to verify accurate TAC generation.
            *   **Edge Cases (`test79.ada`):** Empty procedure, procedure with only declaration/no statements.
*   **Verification**: Primarily automated file comparison. Manual inspection for specific formatting rules or subtle issues. Log files essential for debugging failures.

---

## 11. Code-Review Checklist

*   Offsets calculated correctly for locals (-2 downward) and params (+4 upward, reverse order)?
*   Variable places represented correctly (name for depth 1, `_BP+/-offset` for depth > 1)?
*   Constants (`Symbol.const_value`) substituted directly in TAC?
*   Temporaries (`_tN`) generated correctly and counter reset per `proc`?
*   Arithmetic/logic operators mapped and generated correctly (including precedence)?
*   Unary minus/plus/not handled correctly?
*   Procedure call sequence (`push`/`push @`/`call`) correct based on param modes?
*   `proc`/`endp`/`start` directives present and correct?
*   Output filename `<base>.tac` generated?
*   Lookahead implemented for `AssignStat` vs `ProcCall`?
*   Assumed type sizes documented/verified?
*   Code style consistent and readable?
*   Error handling (e.g., lookup failures) robust within TAC generation phase?

---

## 12. Documentation & Delivery

*   Update `README.md` with specific instructions on how to compile and run Assignment 7 (generating the `.tac` file).
*   Ensure all generated `.tac` files are placed in the specified output location (e.g., same directory as input by default).
*   Provide clean, committed code with appropriate comments.
*   Note any specific Python version or dependency requirements if changed.
*   Briefly document the assumed type sizes (`INT=2`, `FLOAT=4`) in the README or code comments.
