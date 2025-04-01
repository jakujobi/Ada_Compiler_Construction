# Class Reference

This document provides detailed information about all classes in the Ada Compiler Construction project, organized by their functionality.

## Lexical Analysis Classes

### Token

**Module**: `Modules/Token.py`

**Description**: Represents a token identified by the lexical analyzer.

**Constructor**:
```python
def __init__(self, token_type, lexeme, line, column)
```

**Parameters**:
- `token_type`: The type of token (from Definitions.TokenType)
- `lexeme`: The actual text of the token
- `line`: Line number where the token appears
- `column`: Column number where the token starts

**Attributes**:
- `token_type`: The type of token
- `lexeme`: The actual text of the token
- `line`: Line number where the token appears
- `column`: Column number where the token starts

**Methods**:
- `__str__() -> str`: Returns a string representation of the token
- `to_dict() -> dict`: Converts the token to a dictionary format for serialization

**Example**:
```python
from Modules.Token import Token
from Modules.Definitions import Definitions

definitions = Definitions()
token = Token(definitions.TokenType.ID, "counter", 1, 10)
print(token)  # Output: Token(ID, 'counter', line=1, column=10)
```

### LexicalAnalyzer

**Module**: `Modules/LexicalAnalyzer.py`

**Description**: Analyzes source code and breaks it down into tokens.

**Constructor**:
```python
def __init__(self)
```

**Attributes**:
- `definitions`: Instance of Definitions class
- `logger`: Logger for recording analysis information

**Methods**:
- `analyze_file(file_path: str) -> List[Token]`: Analyzes a file and returns a list of tokens
- `analyze_string(source: str) -> List[Token]`: Analyzes a string and returns a list of tokens
- `tokenize(source: str) -> List[Token]`: Breaks source code into tokens

**Example**:
```python
from Modules.LexicalAnalyzer import LexicalAnalyzer

lexer = LexicalAnalyzer()
tokens = lexer.analyze_file("path/to/source.ada")
for token in tokens:
    print(token)
```

## Symbol Table Classes

### Parameter

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Represents a procedure parameter.

**Constructor**:
```python
def __init__(self, param_type: VarType, mode: ParameterMode)
```

**Parameters**:
- `param_type`: The parameter type (from VarType enum)
- `mode`: The parameter passing mode (from ParameterMode enum)

**Attributes**:
- `param_type`: The parameter type
- `mode`: The parameter passing mode

**Methods**:
- `__str__() -> str`: Returns a string representation of the parameter

**Example**:
```python
from Modules.AdaSymbolTable import Parameter, VarType, ParameterMode

param = Parameter(VarType.INT, ParameterMode.IN)
print(param)  # Output: IN:INT
```

### TableEntry

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Represents an entry in the symbol table.

**Constructor**:
```python
def __init__(self, lexeme: str, token_type: Any, depth: int)
```

**Parameters**:
- `lexeme`: The identifier name
- `token_type`: Token type from lexical analyzer
- `depth`: Lexical scope depth

**Attributes**:
- `lexeme`: The identifier name
- `token_type`: Token type from lexical analyzer
- `depth`: Lexical scope depth
- `entry_type`: Type of entry (variable, constant, procedure)
- `var_type`: Type for variables and constants
- `offset`: Memory offset for variables
- `size`: Memory size for variables
- `const_value`: Value for constants
- `local_var_size`: Local variable size for procedures
- `param_count`: Parameter count for procedures
- `return_type`: Return type for procedures
- `param_list`: Parameter list for procedures
- `next`: Next entry in the chain (for collision resolution)

**Methods**:
- `set_variable_info(var_type: VarType, offset: int, size: int) -> None`: Sets variable information
- `set_constant_info(const_type: VarType, const_value: Any) -> None`: Sets constant information
- `set_procedure_info(local_size: int, param_count: int, return_type: VarType, param_list: List[Parameter]) -> None`: Sets procedure information
- `__str__() -> str`: Returns a string representation of the entry

**Example**:
```python
from Modules.AdaSymbolTable import TableEntry, VarType, EntryType

entry = TableEntry("counter", "ID", 1)
entry.set_variable_info(VarType.INT, 0, 4)
print(entry)  # Output: Entry(lexeme='counter', depth=1, type=VARIABLE, var_type=INT)
```

### AdaSymbolTable

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Symbol table implementation using a hash table with chaining.

**Constructor**:
```python
def __init__(self, table_size: int = 211)
```

**Parameters**:
- `table_size`: Size of the hash table (default is 211)

**Attributes**:
- `table_size`: Size of the hash table
- `table`: The hash table array

**Methods**:
- `_hash(lexeme: str) -> int`: Hash function for lexemes
- `insert(lexeme: str, token_type: Any, depth: int) -> TableEntry`: Inserts a new entry
- `lookup(lexeme: str, depth: Optional[int] = None) -> Optional[TableEntry]`: Looks up an entry
- `deleteDepth(depth: int) -> None`: Deletes all entries at a specific depth
- `writeTable(depth: int) -> Dict[str, TableEntry]`: Returns all entries at a specific depth

**Example**:
```python
from Modules.AdaSymbolTable import AdaSymbolTable, VarType

symbol_table = AdaSymbolTable()
entry = symbol_table.insert("counter", "ID", 1)
entry.set_variable_info(VarType.INT, 0, 4)

found = symbol_table.lookup("counter")
print(found)  # Output: Entry(lexeme='counter', depth=1, type=VARIABLE, var_type=INT)

# Look up with specific depth
found_at_depth = symbol_table.lookup("counter", 1)
print(found_at_depth)  # Output: Entry(lexeme='counter', depth=1, type=VARIABLE, var_type=INT)

# Delete entries at depth 1
symbol_table.deleteDepth(1)
```

## Parser Classes

### ParseTreeNode

**Module**: `Modules/ParseTree.py`

**Description**: Represents a node in the parse tree.

**Constructor**:
```python
def __init__(self, type: str, value: Any = None)
```

**Parameters**:
- `type`: Node type
- `value`: Node value (optional)

**Attributes**:
- `type`: Node type
- `value`: Node value
- `children`: List of child nodes

**Methods**:
- `add_child(node: 'ParseTreeNode') -> None`: Adds a child node
- `to_dict() -> dict`: Converts node to dictionary format

**Example**:
```python
from Modules.ParseTree import ParseTreeNode

node = ParseTreeNode("program")
child = ParseTreeNode("declaration", "variable")
node.add_child(child)
```

### ParseTree

**Module**: `Modules/ParseTree.py`

**Description**: Represents the entire parse tree.

**Constructor**:
```python
def __init__(self, root: ParseTreeNode = None)
```

**Parameters**:
- `root`: Root node of the tree (optional)

**Attributes**:
- `root`: Root node of the tree

**Methods**:
- `set_root(node: ParseTreeNode) -> None`: Sets the root node
- `to_dict() -> dict`: Converts tree to dictionary format

**Example**:
```python
from Modules.ParseTree import ParseTree, ParseTreeNode

root = ParseTreeNode("program")
tree = ParseTree(root)
print(tree.to_dict())
```

### RDParser

**Module**: `Modules/RDParser.py`

**Description**: Recursive descent parser for Ada syntax analysis.

**Constructor**:
```python
def __init__(self, tokens: List[Token])
```

**Parameters**:
- `tokens`: List of tokens from lexical analyzer

**Attributes**:
- `tokens`: List of tokens from lexical analyzer
- `current_token_index`: Index of the current token being processed
- `parse_tree`: The resulting parse tree

**Methods**:
- `parse() -> ParseTree`: Parses the tokens and returns a parse tree
- Various parsing methods for different grammar rules

**Example**:
```python
from Modules.LexicalAnalyzer import LexicalAnalyzer
from Modules.RDParser import RDParser

lexer = LexicalAnalyzer()
tokens = lexer.analyze_file("path/to/source.ada")

parser = RDParser(tokens)
parse_tree = parser.parse()
```

## Utility Classes

### Definitions

**Module**: `Modules/Definitions.py`

**Description**: Holds all static definitions used by the compiler.

**Constructor**:
```python
def __init__(self)
```

**Attributes**:
- `TokenType`: Enumeration of all possible token types
- `reserved_words`: Dictionary mapping reserved words to their token types
- `token_patterns`: Dictionary mapping token names to regex patterns

**Methods**:
- `is_reserved(word: str) -> bool`: Checks if a word is a reserved word
- `get_reserved_token(word: str) -> Optional[Enum]`: Returns the token type for a reserved word
- `get_token_type(token_type_str: str) -> Optional[Enum]`: Gets token type from string

**Example**:
```python
from Modules.Definitions import Definitions

definitions = Definitions()
if definitions.is_reserved("BEGIN"):
    print("BEGIN is a reserved word")
```

### ErrorHandler

**Module**: `Modules/ErrorHandler.py`

**Description**: Handles and reports compiler errors.

**Constructor**:
```python
def __init__(self)
```

**Attributes**:
- `errors`: List of errors encountered

**Methods**:
- `add_error(message: str, line: int, column: int) -> None`: Adds an error
- `has_errors() -> bool`: Checks if there are any errors
- `get_errors() -> List[Dict]`: Returns all errors
- `print_errors() -> None`: Prints all errors

**Example**:
```python
from Modules.ErrorHandler import ErrorHandler

error_handler = ErrorHandler()
error_handler.add_error("Undefined variable", 10, 15)
if error_handler.has_errors():
    error_handler.print_errors()
```

### FileHandler

**Module**: `Modules/FileHandler.py`

**Description**: Handles file operations for the compiler.

**Methods**:
- `read_file(file_path: str) -> str`: Reads a file and returns its contents
- `write_file(file_path: str, content: str) -> bool`: Writes content to a file
- `ensure_directory(directory_path: str) -> bool`: Ensures a directory exists

**Example**:
```python
from Modules.FileHandler import FileHandler

file_handler = FileHandler()
content = file_handler.read_file("path/to/source.ada")
file_handler.write_file("path/to/output.txt", "Compilation successful")
```

### Logger

**Module**: `Modules/Logger.py`

**Description**: Handles logging for the compiler.

**Constructor**:
```python
def __init__(self, name: str, log_file: str = None)
```

**Parameters**:
- `name`: Logger name
- `log_file`: Log file path (optional)

**Attributes**:
- `logger`: Python logger instance

**Methods**:
- `debug(message: str) -> None`: Logs a debug message
- `info(message: str) -> None`: Logs an info message
- `warning(message: str) -> None`: Logs a warning message
- `error(message: str) -> None`: Logs an error message
- `critical(message: str) -> None`: Logs a critical message

**Example**:
```python
from Modules.Logger import Logger

logger = Logger("compiler", "logs/compiler.log")
logger.info("Starting compilation")
logger.debug("Processing token: ID")
```

## Enumerations

### VarType (Enum)

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Enumeration of variable types.

**Values**:
- `INT`: Integer type
- `FLOAT`: Floating-point type
- `CHAR`: Character type

### EntryType (Enum)

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Enumeration of symbol table entry types.

**Values**:
- `VARIABLE`: Variable entry
- `CONSTANT`: Constant entry
- `PROCEDURE`: Procedure entry

### ParameterMode (Enum)

**Module**: `Modules/AdaSymbolTable.py`

**Description**: Enumeration of parameter passing modes.

**Values**:
- `IN`: Input parameter
- `OUT`: Output parameter
- `INOUT`: Input/output parameter
