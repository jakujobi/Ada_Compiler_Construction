## 1. Overview
- **Project Goal:**  
    Enhance the Ada compiler by integrating semantic analysis as a separate module (`Semantic_Analyzer.py`). This module will process the abstract syntax tree (AST) or the relevant parse results from `RDParser.py` and update the existing symbol table (`AdaSymbolTable`) with the necessary semantic actions.
- **Integration Strategy:**
    - **RDParser.py:** Responsible solely for syntax analysis and parse tree generation.
    - **Semantic_Analyzer.py:** Performs semantic actions such as inserting constants, variables, and procedures into the symbol table, checking for duplicate declarations, computing variable offsets, and handling procedure parameters.
    - **Existing Modules:**
        - **AdaSymbolTable:** Used for symbol management (insert, lookup, delete, and write table).
        - **Logger:** Used for error reporting and tracing actions.
        - **Definitions, LexicalAnalyzer, and Token:** Supply token and type information required during semantic analysis.

---

## 2. Functional Requirements
### 2.1. Semantic Analyzer Module (`Semantic_Analyzer.py`)
#### Primary Responsibilities
- **Semantic Actions:**
    - Process the parse tree or intermediate representation produced by the parser.
    - Insert constants, variables, and procedures into the symbol table.
- **Field Initialization:**
    - **Constants:**
        - Insert with the correct lexeme, token type, and scope depth.
        - Set constant value using `set_constant_info(const_type, value)`.
    - **Variables:**
        - Insert with type, size, and compute offset based on scope.
        - Update the offset per scope: first variable starts at offset 0; subsequent variables use the previous offset plus the variable’s size.
        - Set variable details using `set_variable_info(var_type, offset, size)`.
    - **Procedures:**
        - Insert procedures and their formal parameters.
        - For procedures, record local variable size, number of formal parameters, and parameter details.
        - Use `set_procedure_info(local_size, param_count, return_type, param_list)` to record procedure-specific attributes.
- **Duplicate Declaration Detection:**
    - Prior to insertion, perform a lookup (using `AdaSymbolTable.lookup(lexeme, depth)`) to check for duplicate declarations.
    - If a duplicate is detected, log an error using the Logger and skip insertion.
- **Scope Exit Handling:**
    - On exiting a procedure or a block, report the contents of the symbol table for the current scope using `writeTable(depth)`.
    - Clean up symbols using `deleteDepth(depth)` if necessary.

#### Interface with RDParser:
- **Input:**
    - Accept the parse tree or an intermediate representation that includes semantic annotations.
    - The parse tree may be enhanced with additional fields (such as a `semantic_info` dictionary) to store computed types, offsets, and other semantic attributes.
- **Output:**
    - Updated symbol table entries.
    - A summary report of semantic errors (if any), logged via the Logger.

---
## 3. Non-Functional Requirements
- **Separation of Concerns:**
    - The semantic analysis is isolated in its own module, ensuring that parsing and semantic validation are decoupled.
- **Maintainability:**
    - With a dedicated semantic analyzer, changes to semantic rules or the symbol table logic are confined to one module.
- **Reliability:**
    - Error reporting and duplicate detection are handled consistently using the Logger, which is already integrated across the project.
- **Testability:**
    - Unit tests can target the semantic analyzer independently from the parser. This improves the ease of debugging semantic issues.

---
## 4. System Architecture
### 4.1. Module Overview
- **RDParser.py:**
    - Generates a parse tree based on the Ada grammar.
    - Passes the parse tree (or relevant parts of it) to the Semantic Analyzer for further processing.
- **Semantic_Analyzer.py (New Module):**
    - Traverses the parse tree.
    - Applies semantic actions to update the symbol table.
    - Checks for duplicate declarations, computes memory offsets, and inserts procedure information.
    - Performs type compatibility checks (see Section 5.2).
    - Logs errors and diagnostic information using the Logger.
- **AdaSymbolTable.py:**
    - Stores symbols with details (variables, constants, procedures).
    - Provides functions for insertion, lookup, deletion, and reporting.
- **Logger.py:**
    - Centralizes error and diagnostic message logging.
    - Used across RDParser, LexicalAnalyzer, and Semantic Analyzer.

### 4.2. Data Flow
1. **Lexical Analysis:**
    - `LexicalAnalyzer` tokenizes the source code.
2. **Syntax Analysis:**
    - `RDParser` processes the token list to build a parse tree.
3. **Semantic Analysis:**
    - `Semantic_Analyzer` traverses the parse tree.
    - Performs semantic checks, updates the symbol table, and validates type compatibility.
    - Uses `AdaSymbolTable` for symbol insertion and management.
4. **Error Reporting:**
    - All errors and warnings are logged via the `Logger` module.

---
## 5. Semantic Analysis Workflow
### 5.1. Processing Declarations
- **Constants:**
    - On encountering a constant declaration, extract the value from the token.
    - Check for duplicate declarations.
    - Insert into the symbol table and set the constant’s attributes.
- **Variables:**
    - For each variable declaration:
        - Check for duplicates within the current scope.
        - Calculate and update the offset (first variable: offset 0; subsequent variables: previous offset + size).
        - Insert into the symbol table with the appropriate type and size.
- **Procedures:**
    - When processing a procedure:
        - Insert the procedure entry with its lexeme, token type, and depth.
        - Process formal parameters by inserting each into the symbol table.
        - Record additional procedure information (e.g., local variable size, parameter list).

### 5.2. Type Compatibility Checks
- **Annotation:**
    - During semantic analysis, annotate relevant parse tree nodes with computed type information.
- **Operations:**
    - For assignments and expressions, ensure that the left-hand side type is compatible with the right-hand side.
    - For procedure calls, verify that actual argument types match the formal parameter types.
    - Include checks for arithmetic operations where type coercion might be allowed (e.g., implicit conversion from integer to float).
- **Error Reporting:**
    - Log any type mismatches with detailed location information (line and column) using the Logger.
- **Integration:**
    - Extend semantic processing routines to invoke helper functions for comparing types and verifying compatibility.

### 5.3. Exiting a Scope
- **Symbol Table Reporting:**
    - Upon exiting a procedure or block:
        - Retrieve and log the symbol table entries for that scope using `writeTable(depth)`.
- **Scope Cleanup:**
    - Remove all entries for that scope using `deleteDepth(depth)` to maintain proper memory and symbol management.

---
## 6. Testing and Validation
### 6.1. Unit Tests for Semantic_Analyzer
- **Valid Declarations:**
    - Test proper insertion of variables, constants, and procedures.
    - Verify that offsets and type annotations are computed correctly.
- **Duplicate Declarations:**
    - Ensure that duplicate identifiers at the same depth are detected and logged.
- **Procedure Declarations:**
    - Validate that procedures and their formal parameters are processed correctly.
- **Type Compatibility:**
    - Test cases where types are compatible and incompatible, ensuring that errors are correctly reported.
### 6.2. Integration Tests
- **Module Interaction:**
    - Confirm that the `Semantic_Analyzer` receives the correct parse tree from `RDParser` and updates the symbol table accordingly.
- **Error Logging:**
    - Check that all syntactic and semantic errors are logged with accurate line and column information.
- **Output Formatting:**
    - Validate that symbol table outputs and error summaries are well formatted using ASCII tables.

---



---