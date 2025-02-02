# Assignment Description
**Instructor**: HAMER  
**Assignment #1**  
**Due**: FEB. 5, 2025

---
## Assignment Overview
This project consists of writing a **Lexical Analyzer** for a subset of the Ada programming language. The Lexical Analyzer is to be a module written in the language of your choice that exports the following:

```plaintext
procedure GetNextToken
global variables:
    Token
    Lexeme
    Value     {for integer tokens}
    ValueR    {for real tokens}
    Literal   {for strings}
````

---

## Reserved Words

The following are the reserved words in the language (may be upper or lower case):
`BEGIN, MODULE, CONSTANT, PROCEDURE, IS, IF, THEN, ELSE, ELSIF, WHILE, LOOP, FLOAT, INTEGER, CHAR, GET, PUT, END`

Note: make a simple data structure to store it

---

## Token Notation

### Comments
- Comments begin with the symbol `--` and continue to the end of the line.
- Comments may appear after any token.

### Blanks
- Blanks between tokens are optional, with the exception of reserved words.
- Reserved words must be separated by blanks, newlines, the beginning of the program, or the final semicolon.

### Identifiers (id)
- Token `id` for identifiers matches a letter followed by letters, underscores, and/or digits.
- Maximum length: 17 characters.
- Ada identifiers are **not case sensitive**.
- Must start with a **letter**.
- Can include **letters, digits, and underscores**.
#### Definition:
```plaintext
letter         -> [a-z, A-Z]
digit          -> [0-9]
underscore     -> _
id             -> letter (letter | digit | underscore)*
```

### Numbers
- Token `num` matches unsigned integers or real numbers.
- Attributes:
    - `Value` for integers
    - `ValueR` for real numbers

#### Definition:
```plaintext
digits            -> digit digit*
optional_fraction -> . digits | ε
num               -> digits optional_fraction
```

### String Literals
- Strings begin and end with `"`.
- Strings must start and end on the same line.
- Stored in the `Literal` variable.

### Relational Operators
Token `relop` includes the following:  
`=`, `/=`, `<`, `<=`, `>`, `>=`

### Operators & Special Symbols

#### Additive Operators (`addop`):
`+`, `-`, `or`
#### Multiplicative Operators (`mulop`):
`*`, `/`, `rem`, `mod`, `and`
#### Assignment Operator
- The assignment operator is `:=`.

### Other Symbols
The following symbols are allowed:  
`( ) , : ; . "`

### Comments
- Start with `--` and extend to the **end of the line**.
- **Ignored** by the Lexer.

### Whitespace
- Spaces and tabs **separate tokens** but are **not reported**.

---

## Rules for the Ada Subset
1. **Procedure Declarations**:
    - Parameterless procedure declarations start the program.
    - Procedures are begun with the reserved word `PROCEDURE`, followed by an `id`, the word `IS`, and then a semicolon.
    - Format: `PROCEDURE <id> IS;`
2. **Procedure Body**:
    - The body of a procedure starts with the reserved word `BEGIN`.
    - It terminates with the reserved word `END`, followed by the name of the procedure and a semicolon.
    - Starts with `BEGIN` and ends with `END <procedure_name>;`

---
## Tokens
All possible symbols (or types of symbols) should be declared as an enumerated data type.

---

## Testing Instructions
Write a short program that:
1. Imports (uses) the module `LexicalAnalyzer`.
2. Reads a source program.
3. Outputs the tokens encountered and their associated attributes:
    - `Lexeme` for identifiers and reserved words
    - Numeric `Value` for `num` tokens
    - The symbol itself for all other tokens
---
## Submission Guidelines
- Source code for this and all other assignments must be submitted as a **single zip file**.
- Upload the zip file to the appropriate **D2L Dropbox** on or before the due date.

---
- Do not report
	- space
	- tabs
	- comments

- the identifiers are 17 character long, not by more than 17
	-  if they are, give an error, except for literal strings
- The end of file is saved as eoft or end of file token


---
# Modules
## Token
### Responsibility:  
Define a data structure (class) to represent tokens, along with metadata such as token type, lexeme, line number, column number, and associated values (for numbers or strings).
### Key Features:
- **Data Encapsulation:** Encapsulate all token-related information to be passed around between modules.
- **Readable Representation:** Provide methods to display tokens (using `__str__` or `__repr__`).
### Design Considerations:
- Use of an object-oriented design so that tokens can be extended easily.
- Support for various types of tokens (identifiers, numbers, reserved words, etc.) by including extra attributes (e.g., integer value vs. real value).

---
## Definitions
### Responsibility:  
Store static data that defines the language, including:
- **Token Types:** Enumerated types for reserved words, operators, and symbols.
- **Reserved Words:** A data structure (dictionary or set) mapping Ada reserved words to their corresponding token types.
- **Regular Expressions/Patterns:** Patterns to validate identifiers, numbers, string literals, and operators.
- **Operators and Symbols:** Maps for operators (assignment, relational, additive, multiplicative) and special symbols (parentheses, semicolons, etc.).
### Key Features:
- **Case Insensitivity:** Since Ada is not case sensitive, the module ensures that comparisons for reserved words are done in a normalized form (e.g., uppercase).
- **Extensibility:** Easily add or modify token patterns and reserved words.
### Design Considerations:
- The use of regular expressions or pattern strings in this module centralizes the static aspects of the language definition.
- This module acts as a reference for the Lexical Analyzer when classifying tokens.

---
## ErrorHandler



## JohnA1.py
This is the driver program.
### JohnA1 class
- Create a log file 
- Receives the input file name at initialization as string, and the output file name(optional)
- Confirm if the input file exists
	- Log an error if the input file does not exist
	- 
- Log each step it performs with relevant level of logging
- Get the source code from the file
- Process it with the lexical analyzer and receive a list of tokens
- Format the tokens in to a table
- Print the table
- Write the table to a file
## main
Acquire files:
- If there are 2 arguements,
	- The first one is the name of the input file
	- The second one is the name of the output file
	- It should pass them to the JohnA1 class initialized
- If there is 1 arguement
	- it is the name of the input file
	- Pass it to the JohnA1 class initialized
- If no arguments, it should ask the user to provide the name of the file or exit the program






---
# Testing and Validation Plan

## 1. Test Cases

- **Valid Inputs:**
    - A small Ada procedure with valid tokens (identifiers, numbers, strings, reserved words).
    - Input with varying whitespace and inline comments.
- **Error Conditions:**
    - An identifier longer than 17 characters.
    - An unterminated string literal.
    - Unrecognized symbols (illegal characters).
- **Corner Cases:**
    - Input that starts or ends with whitespace.
    - Sequences that could be confused with multi-character operators (e.g., differentiating between `:` and `:=`).

## 2. Debugging Strategies

- **Module-Level Testing:**
    - Test each module independently (e.g., validate the Definitions module’s reserved word lookup).
    - Create unit tests for helper functions within the Lexical Analyzer.
- **Integration Testing:**
    - Combine the modules to simulate the full lexical analysis process.
    - Use a controlled set of source code inputs and verify that the output token stream matches expectations.