# Ada Compiler Construction – Professional Overview

## Project Name  
**Ada Compiler Construction Portfolio**

## Summary  
A complete Python-based compiler for a meaningful subset of Ada, built as part of CSC 446 (Compiler Construction). It spans all major compilation phases—lexical analysis, syntax analysis (extended recursive-descent), semantic analysis, and three-address code generation—producing `.TAC` IR files. Designed for robustness, clarity, and extensibility, with full debug logging and modular architecture.

---

## Key Contributions  
- **Modular Driver (JohnA7)**  
  • Refactored a `BaseDriver` to orchestrate all phases.  
  • Command-line interface handling input/output, debug flags, and parse-tree printing.

- **Lexical Analysis**  
  • `LexicalAnalyzer` harnessing `Definitions` with regex patterns for Ada tokens (identifiers, numbers, literals, comments, operators).  
  • Whitespace/comment skipping, length checks, error logging, and guaranteed EOF token.

- **Syntax Analysis**  
  • `RDParserExtended` extending a core `RDParser` to support multiple top-level procedures and Ada statement/expression grammar.  
  • Panic-mode recovery, semantic hooks during parsing, parse-tree construction, and detailed debug output on mismatches or “extra tokens.”

- **Semantic Analysis**  
  • `SemanticAnalyzer` walking the parse tree to build a depth-aware symbol table.  
  • Handled variable/constant/procedure insertion, scoping, duplicate-declaration checks, type mapping, offset tracking, and PrettyTable dumps per scope.  
  • Reported semantic errors without halting the whole build.

- **Three-Address Code Generation**  
  • `ThreeAddressCodeGenerator` producing `TACInstruction` sequences and `TACProgram` IR.  
  • Addressing rules: depth 1 uses variable names; deeper scopes compute `_BP–offset`; parameters `_BP+offset`; direct constant substitution.  
  • Output to `.TAC` file for backend or VM consumption.

- **Testing & Debugging**  
  • Minimal, simple, and comprehensive Ada test suites (`minimal_test.ada`, `simple_test.ada`, `test_tac.ada`).  
  • Integrated logger with timestamped, leveled messages across phases.  
  • Added targeted debug statements pinpointing unexpected tokens, mismatches, and semantic violations.

---

## Technologies & Tools  
- **Language:** Python 3  
- **Libraries:** `re` (regex), `enum`, `prettytable`, `argparse`, custom `Logger`  
- **Design Patterns:** Modular package structure, clear separation of concerns, driver/worker pattern  
- **Version Control:** Git (GitHub)  
- **Testing:** Hand-crafted `.ada` test files and parse-tree inspections  

---

## Resume Entry  
**Software Developer – Ada Compiler Construction**  
CSC 446 (Compiler Construction), San Diego State University — Apr 2025  
- Engineered a full compilation pipeline in Python, covering lexical analysis, extended recursive-descent parsing, semantic analysis, and three-address code IR generation.  
- Designed a robust symbol-table with nested scopes, type/offset management, and PrettyTable-based diagnostics.  
- Built an extensible RD parser with panic-mode recovery, parse-tree building, and detailed debug logging of unexpected tokens.  
- Implemented a three-address code generator with correctness rules for variable addressing and immediate constant propagation.  
- Demonstrated modular architecture and clean code practices, delivering maintainable, testable, and documented compiler software.
