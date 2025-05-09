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

## RDParserExtExt Module

**File**: `src/jakadac/modules/RDParserExtExt.py`

**Purpose**: Further extends `RDParserExtended` to integrate Three-Address Code generation and enhanced semantic validation.

### Class: RDParserExtExt
- Combines parser functionality with integrated TAC generation.
- Uses mixins architecture to organize grammar rules.
- `__init__(...)` : Sets up TACGenerator and connects symbol table.
- `parseProg()` : Updates procedure symbol's parameter list after parsing arguments to ensure correct parameter validation.
- Recently fixed parameter count validation for procedure calls.

---

## Parser Mixin Modules

### DeclarationsMixin
**File**: `src/jakadac/modules/rd_parser_mixins_declarations.py`

**Purpose**: Implements declaration-related grammar rules for the parser.

- `parseDeclarativePart()` : Handles variable and constant declarations.
- `parseArgs()` : Parses procedure arguments and inserts them into symbol table.
- `parseDecl()` : Processes individual declarations.
- `parseDefPart()` : Handles variable definition.

### StatementsMixin
**File**: `src/jakadac/modules/rd_parser_mixins_statements.py`

**Purpose**: Implements statement-related grammar rules for the parser.

- `parseSeqOfStatements()` : Processes sequence of statements.
- `parseStatement()` : Dispatches to specific statement parsers.
- `parseAssignStat()` : Handles assignment statements.
- `parseIOStat()` : Processes input/output statements.
- `parseProcCall()` : Processes procedure calls with parameter validation.
- `parseParams()` : Parses actual parameters in procedure calls.

### ExpressionsMixin
**File**: `src/jakadac/modules/rd_parser_mixins_expressions.py`

**Purpose**: Implements expression-related grammar rules for the parser.

- `parseExpr()` : Entry point for expression parsing.
- `parseTerm()` : Handles terms in expressions.
- `parseFactor()` : Processes factors in terms.

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

**Purpose**: Generates Three-Address Code (TAC) from the parse tree and semantic information.

### Class: TACGenerator
- `__init__(symbol_table: SymbolTable, logger: Logger)`: Initializes with symbol table and logger.
- `generate(root_node: ParseTreeNode)`: Main entry point to traverse parse tree and emit TAC.
- `emit(...)`: Adds a TAC instruction to the list.
- Visitor methods (`_visit_program`, `_visit_procedure_body`, `_visit_assign_stat`, etc.) for different parse tree nodes to generate corresponding TAC instructions.
- Manages temporary variables (`_new_temp`).
- Handles constant substitution and string literal management (creating labels like `_S0`).

---

## ASM Generator Package (`asm_gen`)

**Location**: `src/jakadac/modules/asm_gen/`

**Purpose**: This package is responsible for translating Three-Address Code (TAC) into 8086 assembly language.

### Module: `ASMGenerator`

**File**: `src/jakadac/modules/asm_gen/asm_generator.py`

**Purpose**: Orchestrates the TAC to ASM translation process.

#### Class: `ASMGenerator`
- `__init__(self, tac_file_path, asm_file_path, symbol_table, string_definitions, logger)`: Initializes paths, symbol table, string definitions map, and internal components like `TACParser`, `DataSegmentManager`, `ASMOperandFormatter`, and `ASMInstructionMapper`.
- `generate_asm(self)`: Main method to perform the two-pass assembly generation. 
    1.  Parses the TAC file.
    2.  Collects definitions for the `.data` segment (globals and strings).
    3.  Generates assembly code for each TAC instruction by delegating to `ASMInstructionMapper`.
    4.  Constructs the final `.asm` file including boilerplate, `.data` section, `.code` section (with `include io.asm`), translated instructions, and the main program entry point.
- `_generate_dos_program_shell(self)`: Generates the main entry procedure (`main PROC`) for the 8086 program, which initializes the data segment and calls the user's main procedure.
- Helper methods like `_is_param_address` and `_is_immediate_operand` to assist instruction translators.

### Module: `TACParser`

**File**: `src/jakadac/modules/asm_gen/tac_parser.py`

**Purpose**: Parses a `.tac` file into a list of structured `ParsedTACInstruction` objects.

#### Class: `TACParser`
- `__init__(self, tac_filepath: str, logger: Logger)`: Initializes with the TAC file path.
- `parse(self) -> List[ParsedTACInstruction]`: Reads the TAC file line by line, parsing each into a `ParsedTACInstruction` object. Handles labels, opcodes, and operands.

### Module: `DataSegmentManager`

**File**: `src/jakadac/modules/asm_gen/data_segment_manager.py`

**Purpose**: Manages the generation of the `.data` segment in the assembly file.

#### Class: `DataSegmentManager`
- `__init__(self, symbol_table: SymbolTable, string_literals_map: Dict[str, str], logger: Logger)`: Initializes with the symbol table and a map of string literal labels to their values.
- `collect_definitions(self)`: Identifies global variables (depth 1) from the symbol table.
- `get_data_section_asm(self) -> List[str]`: Generates the assembly lines for the `.data` section, including `DW ?` for global variables and `DB "string$"` for string literals.

### Module: `ASMOperandFormatter`

**File**: `src/jakadac/modules/asm_gen/asm_operand_formatter.py`

**Purpose**: Translates TAC operands into their 8086 assembly representation.

#### Class: `ASMOperandFormatter`
- `__init__(self, symbol_table: SymbolTable, logger: Logger)`: Initializes with the symbol table.
- `format_operand(self, tac_operand: Optional[TACOperand], context_opcode: Optional[TACOpcode] = None) -> str`: Converts a `TACOperand` (which can be an identifier, temporary, literal, or label) into its assembly string form. 
    - Handles immediate values.
    - Looks up identifiers in the symbol table to determine if they are global, local, or parameters.
    - Formats global variables by name (mangling `c` to `cc`).
    - Formats local variables/temporaries as `[bp-X]` (e.g., `[bp-2]`).
    - Formats parameters as `[bp+X]` (e.g., `[bp+4]`).
    - Formats string literal labels as `OFFSET _SLabel` for `WRS` instructions.

### Module: `ASMInstructionMapper`

**File**: `src/jakadac/modules/asm_gen/asm_instruction_mapper.py`

**Purpose**: Maps TAC instructions to sequences of 8086 assembly instructions.

#### Class: `ASMInstructionMapper`
- `__init__(self, symbol_table: SymbolTable, formatter: ASMOperandFormatter, logger: Logger, asm_generator_instance)`: Initializes with symbol table, operand formatter, logger, and a reference to the `ASMGenerator` (for helper methods).
- `translate(self, instr: ParsedTACInstruction) -> List[str]`: Main dispatch method that calls specific `_translate_OPCODE` methods based on the TAC instruction's opcode.
- Contains various private `_translate_OPCODE` methods (e.g., `_translate_assign`, `_translate_add`, `_translate_call`, `_translate_param`, `_translate_wrs`, etc.) which are implemented in separate translator modules.

### Sub-package: `instruction_translators`

**Location**: `src/jakadac/modules/asm_gen/instruction_translators/`

**Purpose**: Contains mixin classes that provide the actual translation logic for different categories of TAC opcodes. These methods are typically bound to `ASMInstructionMapper`.

#### Module: `asm_im_data_mov_translators.py`
- Contains translators for data movement TAC opcodes like `ASSIGN`.
- Implements `_translate_assign`, handling direct assignments, and dereferencing for pass-by-reference parameters (loading address to `BX`, then using `[BX]`). Ensures memory-to-memory moves are avoided using `AX` as an intermediary.

#### Module: `asm_im_arithmetic_translators.py`
- Contains translators for arithmetic TAC opcodes like `ADD`, `SUB`, `MUL`, `UMINUS`, `NOT`.
- Implements `_translate_add`, `_translate_sub`, etc., handling dereferencing for pass-by-reference operands and destinations. Uses `AX`, `BX`, `CX` for operand loading and computation, storing the result from `AX`.

#### (Other translator modules for I/O, control flow, procedures would also be listed here as they are developed)

---

## TypeUtils Module

**File**: `