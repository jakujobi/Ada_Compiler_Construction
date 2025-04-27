# Ada Compiler Construction Documentation

## Overview

This documentation provides a comprehensive guide to the Ada Compiler Construction project, which implements a compiler for a subset of the Ada programming language. The compiler is structured in multiple phases following standard compiler design principles:

1. **Lexical Analysis**: Tokenizing the source code
2. **Syntax Analysis**: Parsing the tokens into a syntax tree
3. **Semantic Analysis**: Type checking and symbol table management
4. **Code Generation**: Three-address code IR generation

## Project Structure

The project is organized into the following main components:

- **Modules**: Core compiler components (lexical analyzer, parser, symbol table, etc.)
- **Assignment Implementations**: Specific implementations for course assignments
- **Tests**: Unit and integration tests for the compiler components

## Getting Started

To use this compiler, you'll need:

- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Basic Usage

```python
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.RDParser import RDParser
from Modules.AdaSymbolTable import AdaSymbolTable

# Create a lexical analyzer
lexer = LexicalAnalyzer()

# Analyze an Ada source file
tokens = lexer.analyze_file("path/to/source.ada")

# Create a parser
parser = RDParser(tokens)

# Parse the tokens
parse_tree = parser.parse()

# Create a symbol table
symbol_table = AdaSymbolTable()

# Use the compiler components as needed
```

## Documentation Contents

- [Module Reference](modules.md): Detailed documentation of all modules
- [Class Reference](classes.md): Documentation of all classes
- [Assignment Implementations](assignments.md): Documentation of assignment-specific implementations
- [Testing Guide](testing.md): Information about the test suite
- [Development Guide](development.md): Guidelines for contributing to the project
- [Improvements & Roadmap](IMPROVEMENTS.md): Future enhancements and improvement ideas.
