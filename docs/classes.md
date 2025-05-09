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

## Parser Extensions

### RDParserExtended

**Module**: `Modules/RDParserExtended.py`

**Description**: Extension of `RDParser` adding full Ada statements and expressions support, multiple top-level procedures, panic-mode recovery, parse-tree hooks, and debug logging for mismatches.

## Three-Address Code Classes

### TACInstruction

**Module**: `Modules/TACGenerator.py`

**Description**: Represents a single three-address code instruction (operation, operands, result).

**Attributes**:
- `op`: Operation code (e.g., ADD, SUB, LOAD)
- `arg1`, `arg2`: Source operands
- `result`: Destination or temporary

### TACProgram

**Module**: `Modules/TACGenerator.py`

**Description**: Container for a list of `TACInstruction` instances, representing the IR for the program.

**Methods**:
- `add_instruction(instr: TACInstruction)`: Appends an instruction
- `to_list() -> List[TACInstruction]`: Returns the instruction list

### ThreeAddressCodeGenerator

**Module**: `Modules/TACGenerator.py`

**Description**: Walks the semantically-annotated parse tree and generates `TACInstruction`s and a `TACProgram` IR using depth-based addressing and constant substitution.

## Utility Classes

### Logger

**Module**: `Modules/Logger.py`

**Description**: Centralized logging utility with configurable levels, timestamps, and multiple outputs (console/file).

### FileHandler

**Module**: `Modules/FileHandler.py`

**Description**: Provides file I/O helpers, including reading/writing source and IR files, and directory management.

### TypeUtils

**Module**: `Modules/TypeUtils.py`

**Description**: Utility functions for mapping token types to variable types (`VarType`), computing type sizes, and other type-related helpers.

### BaseDriver

**Module**: `Modules/Driver.py`

**Description**: Abstract driver orchestrating compilation phases (lexical, syntax, semantic, code generation), CLI handling, logging setup, and result output.

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

## Semantic Analyzer Classes

### NewSemanticAnalyzer

**Module**: `src/jakadac/modules/NewSemanticAnalyzer.py`

**Description**: Traverses the parse tree to perform semantic checks, populate the symbol table, and calculate offsets.

**Constructor**:
```python
def __init__(self, symtab: SymbolTable, root: ParseTreeNode, defs: Definitions, logger: Logger, error_manager: ErrorManager)
```

**Attributes**:
- `symtab`: Instance of `SymbolTable`.
- `root_node`: Root of the `ParseTree`.
- `current_scope_level`: Tracks the current lexical depth.
- `current_offset`: Tracks memory offset for local variables/parameters within a scope.
- `current_procedure_entry`: Holds the `Symbol` entry for the procedure currently being analyzed.

**Methods**:
- `analyze() -> bool`: Starts the semantic analysis process.
- Visitor methods (`_visit_program`, `_visit_procedure_body`, `_visit_declarative_part`, `_visit_assign_stat`, etc.) for different node types in the parse tree.
- `_enter_scope()`, `_exit_scope()`: Manages symbol table scope.
- `_insert_symbol(...)`, `_lookup_symbol(...)`: Wrapper methods for symbol table operations with error handling.

## TAC Generator Classes

### TACGenerator

**Module**: `src/jakadac/modules/TACGenerator.py`

**Description**: Generates Three-Address Code (TAC) by traversing the parse tree after semantic analysis.

**Constructor**:
```python
def __init__(self, symbol_table: SymbolTable, logger: Logger)
```

**Attributes**:
- `symbol_table`: Populated `SymbolTable` instance.
- `tac_instructions`: List to store generated `ParsedTACInstruction` objects.
- `temp_var_count`: Counter for generating unique temporary variable names.
- `string_literal_count`: Counter for generating unique string literal labels.
- `string_definitions`: Dictionary to store `label -> value` for string literals.

**Methods**:
- `generate(root_node: ParseTreeNode) -> Tuple[List[ParsedTACInstruction], Dict[str, str]]`: Main method to start TAC generation.
- `emit(opcode: TACOpcode, dest: Optional[TACOperand] = None, op1: Optional[TACOperand] = None, op2: Optional[TACOperand] = None, label: Optional[str] = None) -> None`: Creates and appends a `ParsedTACInstruction`.
- `_new_temp() -> TACOperand`: Generates a new temporary variable.
- `_new_string_label(value: str) -> TACOperand`: Generates a new label for a string literal and stores it.
- Visitor methods for different parse tree nodes (`_visit_assign_stat`, `_visit_expr`, etc.) that generate the corresponding TAC instructions.

### ParsedTACInstruction (Data Class)

**Module**: `src/jakadac/modules/tac_instruction.py` (often used by TACGenerator and ASMGenerator package)

**Description**: A data class representing a single parsed Three-Address Code instruction.

**Attributes**:
- `line_number: int`: Original line number from the TAC source (if applicable).
- `raw_line: str`: The raw string of the TAC line (if applicable).
- `label: Optional[str]`: An optional label preceding the instruction (e.g., "L1").
- `opcode: Union[TACOpcode, str]`: The operation code (e.g., `ASSIGN`, `ADD`, `GOTO`). Preferably a `TACOpcode` enum member.
- `destination: Optional[TACOperand]`: The destination operand (e.g., a variable, temporary, or label for jumps).
- `operand1: Optional[TACOperand]`: The first source operand.
- `operand2: Optional[TACOperand]`: The second source operand (for binary operations or e.g. number of params for CALL).

### TACOperand (Data Class)

**Module**: `src/jakadac/modules/tac_instruction.py`

**Description**: A data class representing an operand in a TAC instruction.

**Attributes**:
- `value: Union[str, int, float]`: The actual value or name of the operand (e.g., variable name, temporary name, numeric literal, string label).
- `operand_type: TACOperandType`: An enum indicating the type of the operand (e.g., `IDENTIFIER`, `TEMPORARY`, `INTEGER_LITERAL`, `STRING_LABEL`).
- `is_address_of: bool`: A flag indicating if this operand represents the address of a variable (e.g., for pass-by-reference `PARAM @var`).

### Enums (TACOpcode, TACOperandType)

**Module**: `src/jakadac/modules/tac_instruction.py`

- `TACOpcode`: Enum for all supported Three-Address Code operations (e.g., `ASSIGN`, `ADD`, `SUB`, `MUL`, `GOTO`, `IF_FALSE_GOTO`, `PARAM`, `CALL`, `PROC_BEGIN`, `PROC_END`, `READ_INT`, `WRITE_INT`, `WRITE_STR`, `WRITE_NEWLINE`, `PROGRAM_START`).
- `TACOperandType`: Enum for classifying TAC operands (e.g., `IDENTIFIER`, `TEMPORARY`, `INTEGER_LITERAL`, `REAL_LITERAL`, `STRING_LABEL`, `PROCEDURE_NAME`, `PROGRAM_NAME`).

## ASM Generator Classes

These classes are part of the `src.jakadac.modules.asm_gen` package.

### ASMGenerator

**Module**: `asm_generator.py`

**Description**: Orchestrates the translation of Three-Address Code (TAC) to 8086 assembly language.

**Constructor**:
```python
def __init__(self, tac_file_path: str, asm_file_path: str, symbol_table: SymbolTable, string_definitions: Dict[str, str], logger: Logger)
```

**Attributes**:
- `tac_file_path`: Path to the input `.tac` file.
- `asm_file_path`: Path for the output `.asm` file.
- `symbol_table`: A populated `SymbolTable` instance.
- `string_definitions`: A dictionary mapping string labels (e.g., `_S0`) to their actual string values (e.g., `"Hello"`).
- `logger`: Instance of the `Logger`.
- `tac_parser`: Instance of `TACParser`.
- `data_manager`: Instance of `DataSegmentManager`.
- `formatter`: Instance of `ASMOperandFormatter`.
- `instruction_mapper`: Instance of `ASMInstructionMapper`.
- `parsed_tac_instructions`: List of `ParsedTACInstruction` objects from the TAC file.
- `user_main_procedure_name`: Name of the user's main procedure, extracted from `PROGRAM_START` TAC.

**Methods**:
- `generate_asm() -> None`: The main method that drives the assembly generation process. It reads TAC, collects data definitions, generates code for instructions, and writes the final `.asm` file.
- `_generate_dos_program_shell() -> List[str]`: Generates the assembly code for the DOS program entry point (`main PROC`).
- `_is_param_address(asm_operand: str) -> bool`: Helper to check if a formatted assembly operand represents a parameter passed by reference (e.g., `[bp+X]`).
- `_is_immediate_operand(tac_operand: Optional[TACOperand]) -> bool`: Helper to check if a TAC operand is an immediate value.

### TACParser (ASM Generator specific)

**Module**: `asm_gen.tac_parser.py`

**Description**: Parses a `.tac` file into a list of `ParsedTACInstruction` objects for the ASM generator.

**Constructor**:
```python
def __init__(self, tac_filepath: str, logger: Logger)
```

**Methods**:
- `parse() -> List[ParsedTACInstruction]`: Reads the TAC file and converts each line into a `ParsedTACInstruction`.

### DataSegmentManager

**Module**: `asm_gen.data_segment_manager.py`

**Description**: Manages the collection of global variable and string literal definitions for the `.data` segment of the assembly file.

**Constructor**:
```python
def __init__(self, symbol_table: SymbolTable, string_literals_map: Dict[str, str], logger: Logger)
```

**Methods**:
- `collect_definitions() -> None`: Iterates through the symbol table to find global variables (depth 1) and uses the provided `string_literals_map`.
- `get_data_section_asm() -> List[str]`: Returns a list of assembly instruction strings for the `.data` section (e.g., `myGlobal DW ?`, `_S0 DB "text$"`).

### ASMOperandFormatter

**Module**: `asm_gen.asm_operand_formatter.py`

**Description**: Converts TAC operands (from `ParsedTACInstruction`) into their 8086 assembly string representations.

**Constructor**:
```python
def __init__(self, symbol_table: SymbolTable, logger: Logger)
```

**Methods**:
- `format_operand(tac_operand: Optional[TACOperand], context_opcode: Optional[TACOpcode] = None) -> str`: The core method that takes a `TACOperand` and returns its assembly string. Handles:
    - Immediate numeric values.
    - Global variables (direct name, e.g., `myVar`, `cc` for `c`).
    - Local variables and temporaries (e.g., `[bp-2]`, `[bp-4]`).
    - Parameters (e.g., `[bp+4]`, `[bp+6]`).
    - String labels for `WRITE_STR` (e.g., `OFFSET _S0`).
    - Procedure names for `CALL`.

### ASMInstructionMapper

**Module**: `asm_gen.asm_instruction_mapper.py`

**Description**: Maps `ParsedTACInstruction` objects to corresponding sequences of 8086 assembly instructions. It acts as a dispatcher to various translator methods, often organized in mixin classes.

**Constructor**:
```python
def __init__(self, symbol_table: SymbolTable, formatter: ASMOperandFormatter, logger: Logger, asm_generator_instance: 'ASMGenerator')
```

**Methods**:
- `translate(instr: ParsedTACInstruction) -> List[str]`: Takes a `ParsedTACInstruction` and returns a list of assembly instruction strings. It identifies the opcode and calls the appropriate `_translate_...` method (e.g., `_translate_assign`, `_translate_add`).
- Specific translator methods (like `_translate_assign`, `_translate_add`, `_translate_sub`, `_translate_mul`, `_translate_uminus`, `_translate_not_op`, `_translate_proc_begin`, `_translate_proc_end`, `_translate_call`, `_translate_param`, `_translate_write_str`, `_translate_write_int`, `_translate_read_int`, `_translate_write_newline`, etc.) are typically defined in separate translator mixin modules (e.g., `ASMMovTranslatorsMixin`, `ASMArithmeticTranslatorsMixin`) and are bound to this class.

### Instruction Translator Mixin Classes (Conceptual)

**Modules**: Reside in `asm_gen.instruction_translators/` (e.g., `asm_im_data_mov_translators.py`, `asm_im_arithmetic_translators.py`)

**Description**: These modules contain classes (often designed as mixins) that provide the specific assembly translation logic for groups of TAC opcodes. For instance, `ASMMovTranslatorsMixin` would contain `_translate_assign`, and `ASMArithmeticTranslatorsMixin` would contain `_translate_add`, `_translate_sub`, etc. These methods implement the detailed logic, including operand formatting, register allocation, and handling of pass-by-reference dereferencing.

**Example Methods (defined within these mixins and used by `ASMInstructionMapper`):**
- `_translate_assign(instr: ParsedTACInstruction) -> List[str]`: Translates `ASSIGN` TAC. Handles memory-to-memory avoidance and dereferencing of reference parameters.
- `_translate_add(instr: ParsedTACInstruction) -> List[str]`: Translates `ADD` TAC. Handles dereferencing of reference parameters.
