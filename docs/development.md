# Development Guide

This document provides guidelines for contributing to the Ada Compiler Construction project.

## Project Structure

The project follows a modular architecture with clear separation of concerns:

- `Modules/`: Core compiler components
- `A1 - Lexical Analyzer/`, `A2 - Parser/`, etc.: Assignment implementations
- `tests/`: Unit tests
- `docs/`: Documentation

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 100 characters
- Use meaningful variable and function names
- Use docstrings for all modules, classes, and functions

### Docstring Format

Use the following format for docstrings:

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of the function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When and why this exception is raised
    """
```

### Type Annotations

Use type annotations for all function parameters and return values:

```python
def process_token(token: Token) -> bool:
    # Function implementation
```

## Version Control

### Branching Strategy

- `main`: Stable, production-ready code
- `develop`: Integration branch for new features
- `feature/feature-name`: Feature branches for new development
- `bugfix/bug-description`: Bug fix branches

### Commit Messages

Follow these guidelines for commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- First line is a summary (50 chars or less)
- Followed by a blank line
- Followed by a more detailed explanation if necessary
- Reference issue numbers when relevant

Example:
```
Add symbol table depth parameter to lookup method

- Enhances lookup to find entries at specific scope depths
- Maintains backward compatibility with default behavior
- Adds comprehensive tests for the new functionality

Fixes #123
```

## Testing

### Test Coverage

- Aim for at least 80% code coverage
- Write unit tests for all new functionality
- Include edge cases and error conditions

### Running Tests

Run tests before submitting changes:

```bash
python -m unittest discover -s tests
```

## Documentation

### Code Documentation

- Add docstrings to all new modules, classes, and functions
- Update existing docstrings when changing functionality
- Include examples for complex functionality

### Project Documentation

- Update relevant documentation files in the `docs/` directory
- Keep the README up to date
- Document major design decisions

## Error Handling

### Guidelines

- Use exceptions for exceptional conditions
- Provide meaningful error messages
- Include context in error messages (line numbers, token values, etc.)
- Handle errors at the appropriate level

### Example

```python
def lookup(self, lexeme: str, depth: Optional[int] = None) -> Optional[TableEntry]:
    """Look up an entry in the symbol table."""
    if not lexeme:
        raise ValueError("Cannot lookup an empty lexeme")
        
    if depth is not None and depth < 0:
        raise ValueError("Depth cannot be negative")
    
    # Implementation
```

## Performance Considerations

### Symbol Table

- Use an efficient hash function
- Consider the table size for expected program sizes
- Optimize lookup operations for frequently accessed symbols

### Lexical Analyzer

- Minimize string copying
- Use compiled regular expressions
- Consider buffering for large files

### Parser

- Optimize recursive calls
- Consider memoization for repeated subexpressions
- Balance between memory usage and parsing speed

## Future Development

### Planned Features

1. **Semantic Analyzer**
   - Type checking
   - Symbol resolution
   - Constant folding

2. **Code Generator**
   - Target architecture selection
   - Optimization passes
   - Assembly or bytecode generation

3. **Interpreter**
   - Runtime environment
   - Memory management
   - I/O handling

### Integration Points

When developing new components, consider these integration points:

- Lexical Analyzer → Parser: Token stream
- Parser → Semantic Analyzer: Parse tree
- Semantic Analyzer → Symbol Table: Symbol information
- Semantic Analyzer → Code Generator: Annotated parse tree
- Code Generator → Output: Assembly or bytecode
