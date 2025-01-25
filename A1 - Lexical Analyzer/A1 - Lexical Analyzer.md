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

---

## Token Notation

### Comments
- Comments begin with the symbol `--` and continue to the end of the line.
- Comments may appear after any token.

### Blanks
- Blanks between tokens are optional, with the exception of reserved words.
- Reserved words must be separated by blanks, newlines, the beginning of the program, or the final semicolon.

### Identifiers
- Token `id` for identifiers matches a letter followed by letters, underscores, and/or digits.
- Maximum length: 17 characters.
- Ada identifiers are **not case sensitive**.
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

### Arithmetic Operators

#### Additive Operators (`addop`):
`+`, `-`, `or`

#### Multiplicative Operators (`mulop`):
`*`, `/`, `rem`, `mod`, `and`

### Assignment Operator
- The assignment operator is `:=`.

### Other Symbols
The following symbols are allowed:  
`( ) , : ; . "`

---

## Rules for the Ada Subset

1. **Procedure Declarations**:
    - Parameterless procedure declarations start the program.
    - Procedures are begun with the reserved word `PROCEDURE`, followed by an `id`, the word `IS`, and then a semicolon.
2. **Procedure Body**:
    - The body of a procedure starts with the reserved word `BEGIN`.
    - It terminates with the reserved word `END`, followed by the name of the procedure and a semicolon.

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