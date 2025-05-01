# Assignment 7: Ada Compiler - Three Address Code Generation

**Author:** John Akujobi  
**Course:** CSC 446 - Compiler Construction  
**GitHub:** https://github.com/jakujobi/Ada_Compiler_Construction  
**Last Updated:** May 1, 2025

## Description

This project implements the frontend stages of an Ada compiler, focusing specifically on generating Three Address Code (TAC) as specified in Assignment 7. It processes a subset of the Ada language, performing lexical analysis, syntax analysis (using a recursive descent parser), semantic analysis (including symbol table management), and finally generating TAC instructions. The compiler handles variables, arithmetic operations, procedure declarations, and procedure calls with parameters.

## Features

* **Lexical Analysis:** Tokenizes Ada source code based on defined language rules
* **Syntax Analysis:** Parses the token stream using a recursive descent parser (`RDParserExtExt`) to validate the program structure according to the Ada grammar subset
* **Symbol Table:** Manages identifiers, their types, scopes, and other attributes for semantic analysis
* **Semantic Analysis:** Performs type checking, parameter validation, and other semantic validations
* **Three Address Code (TAC) Generation:** Generates intermediate representation (TAC) including:
  * Variable declarations and assignments
  * Arithmetic operations (addition, multiplication, etc.)
  * Procedure declarations with formal parameters
  * Procedure calls with parameter passing
  * Proper memory addressing using base pointer (BP) offsets
* **Error Reporting:** Provides informative messages for lexical, syntax, semantic, and TAC generation errors, including line and column numbers where available
* **Debug Logging:** Offers detailed logging for tracing the compilation process

## Project Structure

* `JohnA7.py`: The main driver script for Assignment 7
* `testXX.ada`: Input Ada source files for testing
* `exp_testXX.tac`: Expected output TAC files for corresponding test cases
* `testXX.tac`: Generated TAC output files
* `src/jakadac/modules/`: Contains the core compiler modules:
  * `Driver.py`: Base driver class handling pipeline execution
  * `LexicalAnalyzer.py`: Performs lexical analysis
  * `RDParserExtExt.py`: Recursive descent parser extended for TAC generation
  * `rd_parser_mixins_declarations.py`: Parser mixin for handling declarations
  * `rd_parser_mixins_statements.py`: Parser mixin for handling statements
  * `rd_parser_mixins_expressions.py`: Parser mixin for handling expressions
  * `TACGenerator.py`: Handles generation and output of TAC instructions
  * `SymTable.py`: Implements the Symbol Table
  * `NewSemanticAnalyzer.py`: Performs semantic analysis
  * `Token.py`, `Definitions.py`, `Logger.py`, `FileHandler.py`, etc.: Supporting modules

## Requirements

*   Python 3.8+

## How to Run

First, navigate to the assignment directory from the workspace root (`CSC 446 - Compiler Construction`):

```bash
cd ./Ada_Compiler_Construction/assignments/A7_3_Address_Code/
```

Then, execute the compiler using the `JohnA7.py` script:

**Basic Usage:**

```bash
python JohnA7.py <input_ada_file>
```
Example:
```bash
python JohnA7.py ./test71.ada
```
This will generate the TAC file in the same directory (`A7_3_Address_Code`) with a `.tac` extension (e.g., `test71.tac`).

**Specify TAC Output File:**

Use the `-o` or `--output` flag to specify a different path/name for the TAC file. The path is relative to the current directory (`A7_3_Address_Code`).

```bash
python JohnA7.py <input_ada_file> -o <output_tac_file>
```
Example:
```bash
python JohnA7.py ./test71.ada -o ./my_test71.tac
```

**Enable Debug Logging:**

Use the `-d` or `--debug` flag to enable detailed debug output to the console.

```bash
python JohnA7.py <input_ada_file> -d
```
Example:
```bash
python JohnA7.py ./test71.ada -d
```

## Input/Output

*   **Input:** `.ada` files containing source code compliant with the subset of Ada defined for the assignment.
*   **Output:**
    *   `.tac` file containing the generated Three Address Code.
    *   Console output showing the compilation summary and any errors encountered.
    *   Optional debug logs if the `-d` flag is used.

## How TAC Generation Works

### Compiler Pipeline

1. **Lexical Analysis**: The input Ada source code is tokenized into a stream of tokens
2. **Syntax Analysis**: The recursive descent parser validates the structure and builds an internal representation
3. **Symbol Table Management**: As parsing proceeds, variables, constants, and procedures are added to the symbol table
4. **TAC Generation**: During parsing, TAC instructions are emitted for various operations
5. **TAC Output**: The final TAC is written to a file

### Memory Model

The Three Address Code uses the following conventions for memory addressing:

* **Global Variables**: Referenced directly by name at depth 1
* **Local Variables**: Referenced using base pointer offsets (`_BP-offset`) for depth > 1
* **Parameters**: Referenced using positive offsets (`_BP+offset`)
* **Constants**: Substituted directly in the code
* **Temporaries**: Generated with names like `_t1`, `_t2`, etc.

### Key TAC Instructions

* `proc <name>` - Procedure declaration start
* `endp <name>` - Procedure declaration end
* `<dest> = <src>` - Assignment operation
* `<dest> = <src1> ADD/MUL/etc <src2>` - Binary operations
* `push <operand>` - Push parameter for procedure call
* `call <proc>` - Call procedure
* `START PROC <name>` - Start of main procedure

### Parameter Handling

The compiler correctly tracks formal parameters during procedure declaration and enforces parameter count validation during procedure calls. Parameters are pushed onto the stack before each procedure call using `push` instructions.

## Testing

Test files (`test71.ada` through `test75.ada`) are provided in the `assignments/A7_3_Address_Code/` directory. Run the compiler against these files and compare the generated `.tac` files with the expected output files (`exp_test71.tac` through `exp_test75.tac`) to verify correctness.

```bash
# Run all test files
python JohnA7.py test71.ada
python JohnA7.py test72.ada
python JohnA7.py test73.ada
python JohnA7.py test74.ada
python JohnA7.py test75.ada
```

## Recent Updates

**May 1, 2025**: Fixed parameter count validation for procedure calls. The compiler now correctly updates procedure symbols with their formal parameters after parsing arguments, ensuring proper validation during procedure calls.

## Implementation Details

### Symbol Table

The `SymbolTable` class implements a stack-based approach to track lexical scopes. When entering a procedure, a new scope is created, and when exiting, the scope is popped. This allows proper handling of variable shadowing and scope resolution.

* **Symbol Types**: Variable, Constant, Procedure, Parameter
* **Symbol Information**: Each symbol stores type, offset, size, and for procedures, parameter information

### Parser Structure

The parser uses a mixin-based approach to organize the grammar rules:

* **DeclarationsMixin**: Handles procedure declarations, variable declarations, and formal parameters
* **StatementsMixin**: Handles statements, assignments, procedure calls, and I/O operations
* **ExpressionsMixin**: Handles expressions, terms, factors, and related grammar rules

### TAC Generation Integration

TAC generation is integrated directly into the parsing process. As the parser recognizes constructs, it emits the corresponding TAC instructions through the `TACGenerator` instance.

The parser maintains a current procedure context to ensure proper tracking of local variables and parameters, assigning correct memory offsets based on scope depth.

## Limitations

* Only a subset of Ada is supported (no arrays, records, or packages)
* Limited control flow capabilities (no if/else or loops)
* No type checking beyond basic parameter count validation
* No optimization is performed on the generated TAC

## License

This project is part of academic coursework for CSC 446 - Compiler Construction.
