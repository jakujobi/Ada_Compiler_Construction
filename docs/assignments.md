# Assignment Implementations

This document provides detailed information about the assignment-specific implementations in the Ada Compiler Construction project.

## Assignment 1: Lexical Analyzer

**Directory**: `A1 - Lexical Analyzer/`

**Main File**: `JohnA1.py`

**Description**: Implementation of a lexical analyzer for Ada, which tokenizes Ada source code according to the language specification.

### Implementation Details

The lexical analyzer reads Ada source code and converts it into a sequence of tokens. It handles:

- Reserved words (e.g., PROCEDURE, BEGIN, END)
- Identifiers
- Numbers (integers and floating-point)
- String literals
- Character literals
- Operators
- Punctuation

### Usage

```python
python JohnA1.py <input_file> [output_file]
```

**Parameters**:
- `input_file`: Path to the Ada source file
- `output_file` (optional): Path to output the tokens (defaults to `<input_file>_tokens.txt`)

### Example

```bash
python JohnA1.py t1.ada
```

This will analyze `t1.ada` and output the tokens to `t1_tokens.txt`.

## Assignment 2: Parser

**Directory**: `A2 - Parser/`

**Description**: Implementation of a parser for Ada, which analyzes the syntactic structure of the program.

### Implementation Details

The parser takes tokens from the lexical analyzer and builds a parse tree according to the Ada grammar. It implements:

- Recursive descent parsing
- Error recovery
- Syntax tree construction

### Documentation

The parser implementation includes detailed documentation of the Ada grammar in both text and diagram formats:

- `A2 - Parser.md`: Text documentation of the grammar
- `Program A - A2 Parser-2025-02-10-064026.png`: Visual diagram of the grammar

## Assignment 3: Recursive Parser

**Directory**: `A3_Recursive_Parser/`

**Main File**: `JohnA3.py`

**Description**: Implementation of a recursive descent parser for Ada, which builds on the previous parser with improved error handling and tree construction.

### Implementation Details

The recursive parser implements:

- Full recursive descent parsing for Ada grammar
- Comprehensive error handling and reporting
- Detailed parse tree construction
- Integration with the lexical analyzer

### Usage

```python
python JohnA3.py <input_file>
```

**Parameters**:
- `input_file`: Path to the Ada source file

## Assignment 4: Ada Symbol Table

**Directory**: `A4_Ada_Symbol_Table/`

**Main Files**:
- `JohnA4.py`: Demonstration of symbol table functionality
- `TestSymbolTable.py`: Unit tests for the symbol table
- `IntegrationTest.py`: Integration tests with other compiler components

**Description**: Implementation of a symbol table for Ada, which manages identifiers and their attributes during compilation.

### Implementation Details

The symbol table implementation includes:

- Hash table with chaining for efficient lookup
- Scope management with depth tracking
- Support for variables, constants, and procedures
- Type checking and semantic analysis
- Error handling for undefined identifiers and type mismatches

### Key Classes

- `AdaSymbolTable`: The main symbol table class
- `TableEntry`: Represents an entry in the symbol table
- `Parameter`: Represents a procedure parameter

### Usage

#### Basic Symbol Table Operations

```python
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType

# Create a symbol table
symbol_table = AdaSymbolTable()

# Insert a variable
var_entry = symbol_table.insert("counter", "ID", 1)
var_entry.set_variable_info(VarType.INT, 0, 4)

# Look up a variable
found = symbol_table.lookup("counter")
if found:
    print(f"Found: {found}")
    
# Look up a variable at a specific depth
found_at_depth = symbol_table.lookup("counter", 1)
if found_at_depth:
    print(f"Found at depth 1: {found_at_depth}")

# Delete all entries at depth 1
symbol_table.deleteDepth(1)
```

#### Running the Demonstration

```bash
python JohnA4.py
```

This will run a demonstration of the symbol table functionality, including insertion, lookup, and deletion operations.

#### Running the Tests

```bash
python TestSymbolTable.py
```

This will run unit tests for the symbol table, verifying its correctness.

```bash
python IntegrationTest.py
```

This will run integration tests showing how the symbol table works with other compiler components.

## Assignment 5a: Semantic Analyzer
**Directory**: `A5_Semantic_Analyzer/`

**Main File**: `JohnA5.py`

**Description**: Performs semantic analysis on the parse tree, including symbol-table population, type checking, and offset computation.

### Usage
```bash
python JohnA5.py path/to/source.ada
```

## Assignment 5b: New Semantic Analyzer
**Directory**: `A5b_New_Semantic_Analyzer/`

**Main File**: `JohnA5b.py`

**Description**: Enhanced semantic analyzer with PrettyTable dumps per scope, improved error reporting, and continued analysis on non-critical errors.

### Usage
```bash
python JohnA5b.py path/to/source.ada
```

## Assignment 6: Extended Grammar Parser
**Directory**: `A6_New_Grammar_Rules/`

**Main File**: `JohnA6.py`

**Description**: Extends `RDParser` with full support for Ada statements and expressions, panic-mode recovery, and multiple procedures.

### Usage
```bash
python JohnA6.py path/to/source.ada
```

## Assignment 7: Three-Address Code Generation
**Directory**: `A7_3_Address_Code/`

**Main File**: `JohnA7.py`

**Description**: Generates three-address code IR with depth-based addressing rules, parameter offset computation, and constant substitution.

### Usage
```bash
python JohnA7.py path/to/source.ada

```

## Assignment 8: TAC to 8086 Assembly Generation
**Directory**: `A8_TAC_to_ASM/`

**Main File**: `JohnA8.py`

**Description**: Translates Three-Address Code (TAC) into 8086 assembly language compatible with MASM/TASM and DOSBox. This includes handling I/O statements, procedure calls, local/global variables, and pass-by-reference parameters.

### Current Progress & Key Features Implemented:

*   **`JohnA8.py` Integration**: The `ASMGenerator` module is integrated into the `JohnA8.py` pipeline, which now accepts an `--asm_output` command-line argument to specify the output assembly file.
*   **`ASMOperandFormatter` Enhancements**: The formatter now correctly translates internal symbol table offsets into 8086 stack frame addresses:
    *   Parameters (depth >= 2): `[bp+<offset+4>]`
    *   Local Variables/Temporaries (depth >= 2): `[bp-<offset+2>]`
    *   Global variables (depth <= 1) are referenced by name (with `c` mangled to `cc`).
    *   String labels (e.g., `_S0`) are formatted as `OFFSET _S0` in the context of `WRS` TAC instructions.
    *   Unit tests for `ASMOperandFormatter` covering these features have been updated and are passing.
*   **Pass-by-Reference Dereferencing**: Logic to handle dereferencing of pass-by-reference parameters has been implemented in:
    *   `_translate_assign` (for `ASSIGN` TAC opcodes) in `asm_im_data_mov_translators.py`. This involves using an intermediary register (`AX` or `BX`) to load the address of the reference parameter and then accessing the value at that address.
    *   Arithmetic translators (`_translate_add`, `_translate_sub`, `_translate_mul`, `_translate_uminus`, `_translate_not_op`) in `asm_im_arithmetic_translators.py`. Similar dereferencing logic is applied to source operands and for storing results to reference parameter destinations.
*   **Unit Testing**: 
    *   Unit tests for `ASMOperandFormatter` are passing.
    *   Unit tests for `_translate_assign` in `test_asm_im_data_mov_translators.py` have been updated to include pass-by-reference scenarios but are currently failing due to discrepancies in expected vs. actual assembly output (primarily TAC comment formatting and minor instruction differences). Debugging these failures is the next immediate step.
    *   Unit tests for arithmetic translators need to be updated to cover pass-by-reference scenarios.

### Usage

```bash
python JohnA8.py path/to/source.ada --tac_output path/to/output.tac --asm_output path/to/output.asm
```

This will compile the Ada source, generate TAC, and then translate the TAC to an 8086 assembly file.
