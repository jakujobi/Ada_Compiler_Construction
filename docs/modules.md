# Module Reference

This document provides detailed information about all modules in the Ada Compiler Construction project.

## Core Modules

### Definitions Module

**File**: `Modules/Definitions.py`

The Definitions module provides essential definitions used throughout the compiler, including token types and regular expression patterns.

#### Class: Definitions

**Description**: Holds all static definitions used by the compiler.

**Attributes**:

- `TokenType`: Enumeration of all possible token types
- `reserved_words`: Dictionary mapping reserved words to their token types
- `token_patterns`: Dictionary mapping token names to regex patterns

**Methods**:

- `is_reserved(word: str) -> bool`: Checks if a word is a reserved word
- `get_reserved_token(word: str) -> Optional[Enum]`: Returns the token type for a reserved word
- `get_token_type(token_type_str: str) -> Optional[Enum]`: Gets token type from string

### Token Module

**File**: `Modules/Token.py`

The Token module defines the Token class used to represent lexical tokens in the source code.

#### Class: Token

**Description**: Represents a token identified by the lexical analyzer.

**Attributes**:

- `token_type`: The type of token (from Definitions.TokenType)
- `lexeme`: The actual text of the token
- `line`: Line number where the token appears
- `column`: Column number where the token starts

**Methods**:

- `__init__(token_type, lexeme, line, column)`: Constructor
- `__str__()`: String representation of the token
- `to_dict()`: Converts token to dictionary format

### LexicalAnalyzer Module

**File**: `Modules/LexicalAnalyzer.py`

The LexicalAnalyzer module implements the lexical analysis phase of the compiler.

#### Class: LexicalAnalyzer

**Description**: Analyzes source code and breaks it down into tokens.

**Attributes**:

- `definitions`: Instance of Definitions class
- `logger`: Logger for recording analysis information

**Methods**:

- `analyze_file(file_path: str) -> List[Token]`: Analyzes a file and returns tokens
- `analyze_string(source: str) -> List[Token]`: Analyzes a string and returns tokens
- `tokenize(source: str) -> List[Token]`: Breaks source into tokens

### AdaSymbolTable Module

**File**: `Modules/AdaSymbolTable.py`

The AdaSymbolTable module implements the symbol table for the Ada compiler.

#### Enum: VarType

**Description**: Enumeration of variable types.

**Values**:

- `INT`: Integer type
- `FLOAT`: Floating-point type
- `CHAR`: Character type

#### Enum: EntryType

**Description**: Enumeration of symbol table entry types.

**Values**:

- `VARIABLE`: Variable entry
- `CONSTANT`: Constant entry
- `PROCEDURE`: Procedure entry

#### Enum: ParameterMode

**Description**: Enumeration of parameter passing modes.

**Values**:

- `IN`: Input parameter
- `OUT`: Output parameter
- `INOUT`: Input/output parameter

#### Class: Parameter

**Description**: Represents a procedure parameter.

**Attributes**:

- `param_type`: Parameter type (VarType)
- `mode`: Parameter passing mode (ParameterMode)

**Methods**:

- `__init__(param_type: VarType, mode: ParameterMode)`: Constructor
- `__str__()`: String representation of the parameter

#### Class: TableEntry

**Description**: Represents an entry in the symbol table.

**Attributes**:

- `lexeme`: The identifier name
- `token_type`: Token type from lexical analyzer
- `depth`: Lexical scope depth
- `entry_type`: Type of entry (variable, constant, procedure)
- Various type-specific attributes (var_type, offset, size, etc.)
- `next`: Next entry in the chain (for collision resolution)

**Methods**:

- `__init__(lexeme: str, token_type: Any, depth: int)`: Constructor
- `set_variable_info(var_type: VarType, offset: int, size: int)`: Sets variable info
- `set_constant_info(const_type: VarType, const_value: Any)`: Sets constant info
- `set_procedure_info(local_size: int, param_count: int, return_type: VarType, param_list: List[Parameter])`: Sets procedure info
- `__str__()`: String representation of the entry

#### Class: AdaSymbolTable

**Description**: Symbol table implementation using a hash table with chaining.

**Attributes**:

- `table_size`: Size of the hash table
- `table`: The hash table array

**Methods**:

- `__init__(table_size: int = 211)`: Constructor
- `_hash(lexeme: str) -> int`: Hash function for lexemes
- `insert(lexeme: str, token_type: Any, depth: int) -> TableEntry`: Inserts a new entry
- `lookup(lexeme: str, depth: Optional[int] = None) -> Optional[TableEntry]`: Looks up an entry
- `deleteDepth(depth: int) -> None`: Deletes all entries at a specific depth
- `writeTable(depth: int) -> Dict[str, TableEntry]`: Returns all entries at a specific depth

### RDParser Module

**File**: `Modules/RDParser.py`

The RDParser module implements a recursive descent parser for Ada.

#### Class: RDParser

**Description**: Recursive descent parser for Ada syntax analysis.

**Attributes**:

- `tokens`: List of tokens from lexical analyzer
- `current_token_index`: Index of the current token being processed
- `parse_tree`: The resulting parse tree

**Methods**:

- `__init__(tokens: List[Token])`: Constructor
- `parse() -> ParseTree`: Parses the tokens and returns a parse tree
- Various parsing methods for different grammar rules

### ParseTree Module

**File**: `Modules/ParseTree.py`

The ParseTree module defines the parse tree structure for representing the syntactic structure of the program.

#### Class: ParseTreeNode

**Description**: Represents a node in the parse tree.

**Attributes**:

- `type`: Node type
- `value`: Node value
- `children`: List of child nodes

**Methods**:

- `__init__(type: str, value: Any = None)`: Constructor
- `add_child(node: 'ParseTreeNode')`: Adds a child node
- `to_dict()`: Converts node to dictionary format

#### Class: ParseTree

**Description**: Represents the entire parse tree.

**Attributes**:

- `root`: Root node of the tree

**Methods**:

- `__init__(root: ParseTreeNode = None)`: Constructor
- `set_root(node: ParseTreeNode)`: Sets the root node
- `to_dict()`: Converts tree to dictionary format

### ErrorHandler Module

**File**: `Modules/ErrorHandler.py`

The ErrorHandler module provides error handling functionality for the compiler.

#### Class: ErrorHandler

**Description**: Handles and reports compiler errors.

**Attributes**:

- `errors`: List of errors encountered

**Methods**:

- `__init__()`: Constructor
- `add_error(message: str, line: int, column: int)`: Adds an error
- `has_errors() -> bool`: Checks if there are any errors
- `get_errors() -> List[Dict]`: Returns all errors
- `print_errors()`: Prints all errors

### Logger Module

**File**: `Modules/Logger.py`

Provides a centralized logging facility with configurable levels, timestamps, and output targets (console/file).

### FileHandler Module

**File**: `Modules/FileHandler.py`

Handles file I/O, command-line path parsing, and ensures directory existence for source inputs and outputs.

### RDParserExtended Module

**File**: `Modules/RDParserExtended.py`

Extends the base RDParser with full Ada statement and expression support, multiple top-level procedures, panic-mode recovery, and debug hooks for token mismatches.

### NewSemanticAnalyzer Module

**File**: `Modules/NewSemanticAnalyzer.py`

Traverses the parse tree to perform semantic analyses: symbol-table population, nested scoping, type checking, offset computation, and scope dumps via PrettyTable.

### TACGenerator Module

**File**: `Modules/TACGenerator.py`

Implements `TACInstruction`, `TACProgram`, and `ThreeAddressCodeGenerator` to emit three-address code IR with depth-based addressing and immediate constant propagation.

### TypeUtils Module

**File**: `Modules/TypeUtils.py`

Utility functions for mapping token types to variable types (`VarType`), computing type sizes, and other type-related helpers.

### Driver Module

**File**: `Modules/Driver.py`

Defines `BaseDriver` to orchestrate compilation phases (lexical, syntax, semantic, code generation), parse CLI args, and manage logging and outputs.

## Semantic Analyzer Module

**File**: `Modules/SemanticAnalyzer.py`

The Semantic Analyzer module performs semantic analysis on the parse tree generated by the parser. It inserts constants, variables, and procedures into the symbol table, performs type checking and offset calculations, and reports errors. Notably, its `analyze_arg_list` method has been updated so that it now returns a tuple `(parameter_count, parameter_list)` when the analysis is successful, or returns `None` if a critical error is encountered—thereby propagating error status back to the caller.
