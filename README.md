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

- **A1 - Lexical Analyzer**: Tokenizes Ada source code
- **A3_Recursive_Parser**: Parses tokens using recursive descent
- **A4_Ada_Symbol_Table**: Implements symbol table management
- **A5_Semantic_Analyzer**: Performs semantic analysis
- **A6_Grammar_Rules_to_Paser**: Handles enhanced grammar rules and supports multiple procedures
- **Modules**: Common modules used across different compiler phases
- **test_files**: Test cases for different compiler features

## Testing

The project includes a test runner that makes it easier to run different compiler phases with various test files. For detailed usage, see [README-test-runner.md](./README-test-runner.md).

### Sample Commands

```bash
# Interactive mode
python test_runner.py

# Batch mode: run all tests with a specific driver
python test_runner.py --driver JohnA6 --all-tests
```

## Getting Started

1. Clone the repository
2. Navigate to the Ada_Compiler_Construction directory
3. Run individual driver files or use the test runner:

```bash
# Run a specific driver on a test file
python A1\ -\ Lexical\ Analyzer/JohnA1.py test_files/tf_add.ada

# Use the test runner
python test_runner.py
```

## Author

John Akujobi  
GitHub: [jakujobi](https://github.com/jakujobi/Ada_Compiler_Construction) 