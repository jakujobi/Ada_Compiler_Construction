# Assignment 7: Ada Compiler - Three Address Code Generation

**Author:** John Akujobi
**Course:** CSC 446 - Compiler Construction
**GitHub:** https://github.com/jakujobi/Ada_Compiler_Construction

## Description

This project implements the frontend stages of an Ada compiler, focusing specifically on generating Three Address Code (TAC) as specified in Assignment 7. It processes a subset of the Ada language, performing lexical analysis, syntax analysis (using a recursive descent parser), semantic analysis (including symbol table management), and finally generating TAC instructions.

## Features

*   **Lexical Analysis:** Tokenizes Ada source code based on defined language rules.
*   **Syntax Analysis:** Parses the token stream using a recursive descent parser (`RDParserExtExt`) to validate the program structure according to the Ada grammar subset.
*   **Symbol Table:** Manages identifiers, their types, scopes, and other attributes for semantic analysis.
*   **Three Address Code (TAC) Generation:** Generates intermediate representation (TAC) during parsing for simple assignments, arithmetic expressions, and basic control flow (procedure calls).
*   **Error Reporting:** Provides informative messages for lexical, syntax, semantic, and TAC generation errors, including line and column numbers where available.
*   **Debug Logging:** Offers detailed logging for tracing the compilation process.

## Project Structure

*   `JohnA7.py`: The main driver script for Assignment 7.
*   `testXX.ada`: Input Ada source files for testing.
*   `testXX.tac`: Expected output TAC files for corresponding test cases.
*   `src/jakadac/modules/`: Contains the core compiler modules:
    *   `Driver.py`: Base driver class handling pipeline execution.
    *   `LexicalAnalyzer.py`: Performs lexical analysis.
    *   `RDParserExtExt.py`: Recursive descent parser extended for TAC generation.
    *   `TACGenerator.py`: Handles generation and output of TAC instructions.
    *   `SymTable.py`: Implements the Symbol Table.
    *   `Token.py`, `Definitions.py`, `Logger.py`, `FileHandler.py`, etc.: Supporting modules.

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

## Testing

Test files (`test71.ada` through `test75.ada`) are provided in the `assignments/A7_3_Address_Code/` directory. Run the compiler against these files and compare the generated `.tac` files with the provided examples to verify correctness.

```bash
# Example test run
python ./Ada_Compiler_Construction/assignments/A7_3_Address_Code/JohnA7.py ./Ada_Compiler_Construction/assignments/A7_3_Address_Code/test74.ada -o ./Ada_Compiler_Construction/assignments/A7_3_Address_Code/test74_output.tac -d
```
