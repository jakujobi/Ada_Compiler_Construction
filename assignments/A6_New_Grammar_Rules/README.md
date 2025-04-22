# Assignment 6: Ada Compiler - Semantic Analysis

## Installation and Usage

To install the `jakadac` package and make drivers available:
```bash
cd <project-root>
pip install -e .
```

To run the A6 compiler driver on an Ada source file:
```bash
python assignments/A6_New_Grammar_Rules/JohnA6.py <source_file.ada>
```

Or use the central test runner for batch/interactive mode:
```bash
python tests/test_runner/test_runner.py --driver JohnA6 [--all-tests]
```

## Overview

This assignment extends the Ada compiler with semantic analysis capabilities, focusing on type checking, symbol table management, and constant declaration handling. The compiler now performs a three-stage process: lexical analysis, syntax analysis, and semantic analysis.

## Features Implemented

### 1. Multiple Procedure Support

- Extended parser handles `ProgramList` root, allowing multiple top-level procedures in one source file.

### 2. Semantic Analysis

- Type checking for variable and constant declarations
- Symbol table management for tracking identifiers and their types
- Proper handling of constant declarations with type inference
- Scope management for nested procedures
- Parameter mode handling (IN, OUT, INOUT)

### 3. Constant Declaration Handling

- Type inference from assigned values
- Proper registration in the symbol table
- Error reporting for invalid constant declarations

### 4. Symbol Table

- Tracks variables, constants, and procedures
- Maintains type information
- Supports nested scopes
- Records parameter modes for procedure arguments

## Project Structure

- `JohnA6.py`: Main compiler driver for Assignment A6 (lexical, syntax, and semantic phases)
- `src/jakadac/modules/`: Core compiler components
  - `LexicalAnalyzer.py`: Tokenizes the Ada source code
  - `RDParserExtended.py`: Extended recursive-descent parser supporting new grammar rules
  - `NewSemanticAnalyzer.py`: Semantic analyzer, performing symbol-table insertion, type checking, and undeclared-identifier checks
  - `SymTable.py`: Symbol table implementation (nested scopes, insertion, lookup)
  - `Driver.py`: Base driver class with shared compilation phases
  - `Logger.py`: Configurable logging facility
  - `Token.py`: Definition of the `Token` class used by the parser
  - `Definitions.py`: Token-type enumeration and reserved-word mappings
  - `FileHandler.py`: Utility for reading and writing files

## Usage

Run the compiler on an Ada source file (semantic analysis will follow syntax):

```bash
python JohnA6.py <source_file.ada> [output_file]
``` 

- After parsing you will be prompted: `Proceed to semantic analysis? [Y/n]`.
- To enable more verbose semantic debugging, adjust the log level in code (e.g. set console level to `DEBUG` in `JohnA6.py`).

## Example

```bash
python JohnA6.py t55.ada
```

This will:

1. Perform lexical analysis to tokenize the source code
2. Parse the tokens to build a parse tree
3. Perform semantic analysis to check for type errors
4. Display a compilation summary

## Test Files

- `t53.ada`: Basic procedure declarations and parameter handling
- `t54.ada`: Procedures with `INOUT` parameters
- `t55.ada`: Constant declarations with type inference

## Recent Improvements

- Fixed constant declaration handling to properly infer types from assigned values
- Improved error reporting for invalid constant declarations
- Enhanced logging configuration to reduce console clutter
- Added multiple procedure support in parser (ProgramList root)

## Compilation Process

1. **Lexical Analysis**: Converts source code into tokens
2. **Syntax Analysis**: Parses tokens into a parse tree using recursive descent parsing
3. **Semantic Analysis**: Analyzes the parse tree for semantic correctness, including:
   - Type checking
   - Symbol table management
   - Constant declaration handling
   - Scope management

## Error Handling

The compiler reports three types of errors:

- Lexical errors: Invalid tokens in the source code
- Syntax errors: Invalid syntax structure
- Semantic errors: Type mismatches, undeclared variables, etc.

A detailed error report is provided at the end of compilation.
