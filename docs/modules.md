# Module Reference

This document provides detailed information about all modules in the Ada Compiler Construction project.

---

## Definitions Module

**File**: `src/jakadac/modules/Definitions.py`

**Purpose**: Centralized definitions for token types, reserved words, and regex patterns.

### Class: Definitions

- `__init__()` : Builds the `TokenType` enum, `reserved_words` mapping, and `token_patterns` dictionary.
- `is_reserved(word: str) -> bool` : Returns `True` if the given word (case-insensitive) is an Ada keyword.
- `get_reserved_token(word: str) -> Optional[Enum]` : Retrieves the `TokenType` for a reserved word.
- `get_token_type(token_type_str: str) -> Optional[Enum]` : Looks up a `TokenType` by its name.

---

## Token Module

**File**: `src/jakadac/modules/Token.py`

**Purpose**: Represents lexical tokens produced by the lexer.

### Class: Token

- `__init__(token_type, lexeme, line_number, column_number, value=None, real_value=None, literal_value=None)` : Initializes a token.
- `__repr__() -> str` : Debug representation showing type, lexeme, value, and position.
- `__str__() -> str` : User-friendly representation `<token_type, lexeme>`.

---

## LexicalAnalyzer Module

**File**: `src/jakadac/modules/LexicalAnalyzer.py`

**Purpose**: Scans Ada source text and breaks it into `Token` objects.

### Class: LexicalAnalyzer

- `__init__(stop_on_error: bool = False)` : Sets up `Definitions`, `Logger`, and error mode.
- `analyze(source_code: str) -> List[Token]` : Main entry for tokenization; returns list ending with EOF.
- `_skip_whitespace(source, pos, line, column) -> (pos, line, column)` : Skips spaces/tabs/newlines.
- `_skip_comment(source, pos, line, column) -> (pos, line, column)` : Skips Ada comments (`--` to end-of-line).
- `_match_token(source, pos, line, column) -> (Token|SKIP|None, new_pos, new_line, new_column)` : Applies regex patterns to match tokens.

---

## Symbol Table Module

**File**: `src/jakadac/modules/SymTable.py`

**Purpose**: Implements scoped symbol table for semantic analysis.

### Enums:
- `VarType` : Data types (`CHAR`, `INT`, `FLOAT`, `REAL`, `BOOLEAN`).
- `EntryType` : Entry categories (`VARIABLE`, `CONSTANT`, `PROCEDURE`, `FUNCTION`, `TYPE`, `PARAMETER`).
- `ParameterMode` : Parameter passing modes (`IN`, `OUT`, `INOUT`).

### Class: Symbol
- `__init__(name: str, token: Token, entry_type: EntryType, depth: int)` : Creates symbol.
- `set_variable_info(var_type: VarType, offset: int, size: int)` : Assigns var/param metadata.
- `set_constant_info(const_type: VarType, value: Any)` : Assigns constant metadata.
- `set_procedure_info(param_list, param_modes, local_size)` : Stores procedure info.
- `set_function_info(return_type, param_list, param_modes, local_size)` : Stores function info.
- `__str__()`, `__repr__()` : String formats.

### Exceptions:
- `SymbolTableError` : Base exception.
- `SymbolNotFoundError(name)` : Lookup failure.
- `DuplicateSymbolError(name, depth)` : Redeclaration in scope.

### Class: SymbolTable
- `__init__()` : Initializes global scope.
- `enter_scope()` : Pushes a new scope.
- `exit_scope()` : Pops current scope.
- `insert(symbol: Symbol)` : Inserts symbol, enforcing unique names per scope.
- `lookup(name: str, lookup_current_scope_only: bool = False) -> Symbol` : Finds symbol across scopes.
- `get_current_scope_symbols() -> Dict[str, Symbol]` : Retrieves symbols in active scope.
- `__str__()` : Formatted view of current scope.

---

## ParseTree Module

**File**: `src/jakadac/modules/ParseTree.py`

**Purpose**: Defines tree structures for syntax representation.

### Class: ParseTreeNode
- `__init__(name: str, token: Optional[Token] = None)` : Node label and optional token.
- `add_child(child)` : Adds subtree.
- `__str__()`, `__repr__()` : Node display.

### Class: ParseTree
- `__init__()` : Initializes empty tree.
- `root` : Holds root node.

### Class: ParseTreePrinter
- `print_tree(node, indent: int = 0)` : Recursively prints the tree structure.

---

## Logger Module

**File**: `src/jakadac/modules/Logger.py`

**Purpose**: Centralized logging with file/console handlers, filters, and formatters.

### Class: CallerFilter
- `filter(record)` : Attaches `caller_class` to log records.

### Class: ColoredFormatter
- `__init__(fmt, datefmt=None, use_color=True)` : Sets up ANSI color codes for levels.
- `format(record)` : Inserts color codes if enabled.

### Class: Logger
- `__new__()`, `__init__(...)` : Singleton setup of file and console handlers.
- `debug(msg, ...)`, `info(msg, ...)`, `warning(msg, ...)`, `error(msg, ...)`, `critical(msg, ...)` : Logging methods.
- `set_level(level, handler_type='both')` : Adjusts logging thresholds.

---

## FileHandler Module

**File**: `src/jakadac/modules/FileHandler.py`

**Purpose**: Utility for robust file I/O and user prompts.

### Class: FileHandler
- `__init__()` : Initializes logger.
- `process_file(file_name: str) -> List[str] | None` : Reads and cleans lines.
- `process_arg_file(file_name: str)` : Handles CLI file args.
- `find_file(file_name, create_if_missing=False) -> Optional[str]` : Locates or creates file.
- `prompt_for_file(...)`, `use_system_explorer()` : Interactive selection.
- `open_file(file_path)` : Generator for file lines.
- `read_file(file_gen) -> List[str]` : Cleans and returns lines.
- `read_file_raw(file_name) -> List[str]` : Raw read.
- `process_file_char_stream(file_name)` : Char-by-char read.
- `read_file_as_string(file_name) -> str` : Full content.
- `read_line_from_file(line) -> str` : Cleans individual line.
- `write_file(file_name, lines)` : Overwrites with lines.
- `write_string_to_file(file_name, content)` : Writes string.
- `append_to_file(file_name, lines)` : Appends lines.
- `file_exists(file_name) -> bool` : Existence check.

---

## RDParser Module

**File**: `src/jakadac/modules/RDParser.py`

**Purpose**: Recursive-descent syntax analyzer for core Ada grammar.

### Class: RDParser
- `__init__(tokens, defs, stop_on_error=False, panic_mode_recover=False, build_parse_tree=False)` : Sets up parser state.
- `parse() -> bool` : Entry point; applies grammar and checks EOF.
- `advance()` : Moves to next token.
- `match(expected_token_type)` : Verifies token type or records error.
- `match_leaf(expected_token_type, parent_node)` : Builds parse tree leaf.
- `report_error(message)` : Logs syntax errors.
- `panic_recovery(sync_set: Set)` : Skip tokens to recover.
- `print_summary()` : Reports error count.
- `print_parse_tree()` / `_print_tree(...)` : Renders tree.
- Grammar methods: `parseProg()`, `parseDeclarativePart()`, `parseProcedures()`, `parseArgs()`, `parseSeqOfStatements()`, etc.

---

## RDParserExtended Module

**File**: `src/jakadac/modules/RDParserExtended.py`

**Purpose**: Extends `RDParser` with Ada statements and expressions.

### Class: RDParserExtended
- Extends core parser: adds `symbol_table` and semantic checks.
- `__init__(...)` : Inherits and extends parser initialization.
- `parseProg()` : Overrides to enforce matching procedure names.
- `parseSeqOfStatements()`, `parseStatTail()`, `parseStatement()`, `parseAssignStat()`, `parseIOStat()`, `parseExpr()`, etc.
- Semantic error reporting via `report_error` and a new `semantic_errors` list.

---

## NewSemanticAnalyzer Module

**File**: `src/jakadac/modules/NewSemanticAnalyzer.py`

**Purpose**: Performs semantic analysis on the parse tree.

### Class: NewSemanticAnalyzer
- `__init__(symtab, root, defs)` : Links symbol table and parse tree.
- `analyze() -> bool` : Drives symbol insertion and scope dumps.
- `_visit_program(node)` : Inserts program symbol and enters scope.
- `_visit_formals(node)` : Inserts parameters with offsets and modes.
- `_visit_declarative_part(node)` : Processes constant/variable declarations.
- `_insert_constants(...)` / `_insert_variables(...)` : Handle symbol creation.
- `_map_typemark_to_vartype(type_mark) -> VarType` : Type mapping.
- `_visit_statements(node)` / `_visit_statement(node)` : Checks undeclared IDs.
- `_dump_scope(depth)` : Pretty-prints symbols using table layout.
- `_error(message)` : Records semantic errors.

---

## TACGenerator Module

**File**: `src/jakadac/modules/TACGenerator.py`

**Purpose**: Generates three-address code (TAC) from parse tree.

### Class: TACInstruction
- `__init__(op: str, arg1: str, arg2: Optional[str], result: Optional[str])` : Defines an IR instruction.
- `__str__() -> str` : Formats instruction for output.

### Class: TACProgram
- `__init__()` : Initializes instruction list.
- `add_instruction(instr: TACInstruction)` : Appends to program.
- `__iter__()`, `__str__()` : Iteration and full program print.

### Class: ThreeAddressCodeGenerator
- `__init__(parse_tree, symtab)` : Sets IR inputs.
- `generate()` : Walks parse tree and emits TAC.
- Internal helpers: `_gen_procedure`, `_gen_statement`, `_gen_expression`, etc.
- Implements depth-based addressing and constant substitution.

---

## TypeUtils Module

**File**: `src/jakadac/modules/TypeUtils.py`

**Purpose**: Utility for mapping token types to variable types and computing sizes.

### Class: TypeUtils
- `token_type_to_var_type(token_type: str) -> VarType` : Maps lexeme type to `VarType`.
- `get_type_size(var_type: VarType) -> int` : Returns byte size of type.
- `parse_value_from_token(token_type: str, lexeme: str) -> Tuple[VarType, Any]` : Parses literal values.

---

## Driver Module

**File**: `src/jakadac/modules/Driver.py`

**Purpose**: Base driver orchestrating compilation phases and I/O.

### Class: BaseDriver
- `__init__(input_file_name: str, output_file_name: Optional[str] = None, debug: bool = False, logger: Optional[Logger] = None)` : Initializes phases and paths.
- `get_source_code_from_file() -> None` : Reads input file.
- `print_source_code() -> None` : Prints source to console.
- `process_tokens() -> None` : Runs lexical analysis.
- `format_and_output_tokens() -> None` : Formats and writes token table.
- `write_output_to_file(output_file_name, content) -> bool` : Writes text to file.
- `print_tokens() -> None` : Prints raw tokens.
- `get_processing_status() -> Dict[str, Any]` : Reports counts and error tallies.
- `print_compilation_summary() -> None` : Prints overall summary.
