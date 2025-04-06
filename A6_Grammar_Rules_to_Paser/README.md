# Assignment 6: Ada Compiler - Semantic Analysis

## Overview

This assignment extends the Ada compiler with semantic analysis capabilities, focusing on type checking, symbol table management, and constant declaration handling. The compiler now performs a three-stage process: lexical analysis, syntax analysis, and semantic analysis.

## Features Implemented

### 1. Semantic Analysis

- Type checking for variable and constant declarations
- Symbol table management for tracking identifiers and their types
- Proper handling of constant declarations with type inference
- Scope management for nested procedures
- Parameter mode handling (IN, OUT, INOUT)

### 2. Constant Declaration Handling

- Type inference from assigned values
- Proper registration in the symbol table
- Error reporting for invalid constant declarations

### 3. Symbol Table

- Tracks variables, constants, and procedures
- Maintains type information
- Supports nested scopes
- Records parameter modes for procedure arguments

## Project Structure

- `JohnA6.py`: Main compiler driver that orchestrates the three stages
- `Modules/`: Contains the core compiler components
  - `LexicalAnalyzer.py`: Tokenizes the source code
  - `RDParserExtended.py`: Performs syntax analysis and builds the parse tree
  - `SemanticAnalyzer.py`: Performs semantic analysis on the parse tree
  - `AdaSymbolTable.py`: Manages the symbol table for tracking identifiers
  - `Token.py`: Defines token structure
  - `Definitions.py`: Contains shared definitions and constants
  - `Logger.py`: Handles logging throughout the compiler
  - `FileHandler.py`: Manages file I/O operations

## Usage

Run the compiler with an Ada source file:

```bash
python JohnA6.py <source_file.ada>
```

### Command Line Options

- `--output` or `-o`: Specify output file for token list
- `--debug` or `-d`: Enable debug output
- `--no-tree`: Disable parse tree printing

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

- `t53.ada`: Tests basic procedure declarations and parameter handling
- `t54.ada`: Tests procedure declarations with INOUT parameters
- `t55.ada`: Tests constant declarations with type inference

## Recent Improvements

- Fixed constant declaration handling to properly infer types from assigned values
- Improved error reporting for invalid constant declarations
- Enhanced logging configuration to reduce console clutter

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
