# Ada Compiler Construction

This project implements a compiler for a subset of the Ada programming language, developed as part of CSC 446 - Compiler Construction.

## Overview

The compiler consists of several phases, implemented across multiple assignments:

1. **Lexical Analysis (A1)** - Scans the source code and produces tokens
2. **Recursive Descent Parser (A3)** - Parses tokens to verify syntax and builds a parse tree
3. **Symbol Table (A4)** - Manages symbol information and scopes
4. **Semantic Analysis (A5)** - Performs type checking and semantic validation
5. **Advanced Grammar Parsing (A6)** - Handles enhanced grammar rules and supports multiple procedures

## Recent Improvements

The codebase has undergone several significant improvements:

- **Type Safety**: Added proper type annotations and Optional types
- **Null Safety**: Implemented comprehensive null checks to prevent runtime errors
- **Documentation**: Enhanced documentation with detailed docstrings
- **Test Runner**: Created a robust test runner to simplify testing process

For detailed information about the code improvements, see [IMPROVEMENTS.md](./IMPROVEMENTS.md).

## Project Structure

- **src**: The `jakadac` package containing all compiler modules (lexer, parser, semantic analyzer, etc.)
- **assignments**: Driver scripts and test files for each assignment phase
- **tests**: Unit tests and the test runner tool
- **docs**: Additional documentation (IMPROVEMENTS.md)
- **requirements.txt**: Runtime dependencies
- **pyproject.toml**: Build and project metadata

## Installation

Go to the root of the repository

```bash
cd Ada_Compiler_Construction
```

To install the package in editable (development) mode:

```bash
pip install -e .
```

## Getting Started

After installation, you can run individual drivers or use the test runner from the project root.

```bash
# Run a specific driver on a test file
python assignments/A1\ -\ Lexical\ Analyzer/JohnA1.py tests/test_files/tf_add.ada

# Run the test runner tool
python tests/test_runner/test_runner.py
```

## Testing

You can also use the test runner in batch mode:

```bash
python tests/test_runner/test_runner.py --driver JohnA6 --all-tests
```

## Author

John Akujobi
GitHub: [jakujobi](https://github.com/jakujobi/Ada_Compiler_Construction)
