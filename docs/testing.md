# Testing Guide

This document provides information about the test suite for the Ada Compiler Construction project.

## Test Directory Structure

The project includes several test files organized as follows:

- `tests/`: Main test directory
  - `test_file_handler.py`: Tests for the FileHandler module
  - `test_john_a1.py`: Tests for Assignment 1 (Lexical Analyzer)
  - `test_lexical_analyzer.py`: Tests for the LexicalAnalyzer module
  - `test_logger.py`: Tests for the Logger module
  - `test_token.py`: Tests for the Token module
- `A4_Ada_Symbol_Table/`: Symbol table tests
  - `TestSymbolTable.py`: Unit tests for the AdaSymbolTable module
  - `IntegrationTest.py`: Integration tests for the symbol table

## Running Tests

### Running All Tests

To run all tests in the `tests/` directory:

```bash
python -m unittest discover -s tests
```

### Running Specific Test Files

To run a specific test file:

```bash
python -m unittest tests/test_lexical_analyzer.py
```

### Running Symbol Table Tests

To run the symbol table tests:

```bash
python A4_Ada_Symbol_Table/TestSymbolTable.py
```

To run the integration tests:

```bash
python A4_Ada_Symbol_Table/IntegrationTest.py
```

## Test Files

### test_file_handler.py

Tests for the FileHandler module, including:

- Reading files
- Writing files
- Ensuring directories exist
- Handling file errors

### test_john_a1.py

Tests for Assignment 1 (Lexical Analyzer), including:

- Command-line argument parsing
- File processing
- Token generation
- Output formatting

### test_lexical_analyzer.py

Tests for the LexicalAnalyzer module, including:

- Token recognition for all token types
- Handling of reserved words
- Error detection and reporting
- Edge cases like empty files and invalid characters

### test_logger.py

Tests for the Logger module, including:

- Log message formatting
- Log level filtering
- File output
- Console output

### test_token.py

Tests for the Token module, including:

- Token creation
- String representation
- Dictionary conversion

### TestSymbolTable.py

Comprehensive unit tests for the AdaSymbolTable module, including:

- Symbol table creation
- Entry insertion
- Entry lookup (with and without depth specification)
- Depth deletion
- Hash function behavior
- Collision handling
- Variable, constant, and procedure entries
- Error handling

### IntegrationTest.py

Integration tests showing how the symbol table works with other compiler components:

- Integration with lexical analyzer
- Integration with semantic analyzer
- Integration with code generator
- Error handling across components

## Test Data

The project includes several Ada source files for testing:

- `A1 - Lexical Analyzer/t1.ada`, `t2.ada`, etc.: Test files for lexical analysis
- `A2 - Parser/A2Code.ada`: Test file for parsing
- Various other `.ada` files throughout the project

## Writing New Tests

When writing new tests, follow these guidelines:

1. Use the Python `unittest` framework
2. Create a new test class that inherits from `unittest.TestCase`
3. Write test methods that start with `test_`
4. Use assertions to verify expected behavior
5. Include setup and teardown methods if needed
6. Add docstrings to explain what each test is checking

Example:

```python
import unittest
from Modules.Token import Token
from Modules.Definitions import Definitions

class TestToken(unittest.TestCase):
    def setUp(self):
        self.definitions = Definitions()
        
    def test_token_creation(self):
        """Test that tokens are created correctly."""
        token = Token(self.definitions.TokenType.ID, "variable", 1, 5)
        self.assertEqual(token.token_type, self.definitions.TokenType.ID)
        self.assertEqual(token.lexeme, "variable")
        self.assertEqual(token.line, 1)
        self.assertEqual(token.column, 5)
        
    def test_token_string_representation(self):
        """Test the string representation of tokens."""
        token = Token(self.definitions.TokenType.ID, "variable", 1, 5)
        self.assertEqual(str(token), "Token(ID, 'variable', line=1, column=5)")
        
if __name__ == "__main__":
    unittest.main()
```
