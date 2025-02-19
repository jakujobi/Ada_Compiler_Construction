# Assignment Req
CSC 446

Assign #3  
Hamer  
Due: Feb 19, 2025

---
Create a recursive descent parser for the CFG given below

You may use the test programs given in the previous assignment and those included at the end to test your parser. Be sure to realize that this is not an exhaustive test of your parser and you should develop as many test cases as you can think of.

To turn in your assignment submit both your lexical analyzer and parser programs in a zip file placed into the Assign 3 dropbox on D2L. Submit all parts of your assignment. Use proper data abstraction techniques when you write your program. This means that the parser and lexical analyzers need to be in separate source files. Include any other needed programs so that they will compile without modification.

To ensure that the program is indeed legal your parser must terminate with the end of file token!

### Grammar Rules

```ada
Prog           ->  procedure idt Args is
                   DeclarativePart
                   Procedures
                   begin
                   SeqOfStatements
                   end idt;

DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε

IdentifierList  -> idt | IdentifierList , idt

TypeMark       -> integert | realt | chart | const assignop Value 

Value          -> NumericalLiteral

Procedures     -> Prog Procedures | ε

Args           -> ( ArgList ) | ε

ArgList        -> Mode IdentifierList : TypeMark MoreArgs

MoreArgs       -> ; ArgList | ε

Mode           -> in | out | inout | ε

SeqOfStatements -> ε
```

## Test Programs
The simplest Ada program is then:
``` pascal A3T1.ada
PROCEDURE one IS
	BEGIN
	END one;
```

A more typical program would be
```pascal A3T2.ada
PROCEDURE MAIN IS

PROCEDURE PROC1 IS
	BEGIN
	END PROC1;

BEGIN
END MAIN;
```

A more complicated program would look like

```pascal A3T3.ada
PROCEDURE seven IS
	count:CONSTANT:=5;
	a,b:INTEGER;
PROCEDURE eight(x:INTEGER; y:INTEGER) IS
	BEGIN
	END eight;
BEGIN
END seven;
```

Finally, you could use this program too!

```pascal A3T4.ada
procedure five is
	a,b,c,d:integer;
procedure fun(a:integer; out b:integer) is
	c:integer;
	begin
	end fun;
begin
end five;
```

---
# Prework notes
- I will use python to write my program
- I already have modules for
	- Logger - provided logging
	- LexicalAnalyzer - Provides a list of tokens
	- Provide
It must be able to fix left recursive grammar rules
Your parser should **detect errors and provide useful messages**

### No output
It should logg everything and show
It should detect errors and report them well
IT no errors, it should say no errors found


----

# Plan
> [!info]
> 
Muahahahaha
### Modules and Their Responsibilities
1. **Lexical Analyzer Modules (Provided)**
    - **Definitions:**  
        Stores token types, reserved words, and regex patterns.
    - **Token:**  
        Represents a token (with lexeme, type, line, column, etc.).
    - **Logger:**  
        Centralized logging.
    - **LexicalAnalyzer:**  
        Converts source code into a list of tokens.
2. **Parser Modules (New)**
    - **RDParser:**  
        Implements the recursive descent parser for the Ada subset. It checks syntactic correctness, supports configurable error handling (via `stop_on_error` and `panic_mode_recover`), and later can build an explicit parse tree.
    - **ParseTree (Optional, Future Extension):**  
        Contains classes for parse tree nodes.
    - **ParseTreePrinter (Optional, Future Extension):**  
        Utility to print the parse tree.
3. **Driver Module**
    - **JohnA3.py:**  
        Reads the source file, calls the lexical analyzer, passes the token list to the RDParser, and later invokes the ParseTreePrinter.

---

## RDParser Module – Class and Methods
### Class: RDParser
**Attributes:**
- `tokens: List[Token]`  
    The list of tokens provided by the driver.
- `current_index: int`  
    The current position in the token list.
- `current_token: Token`  
    The token at the current index.
- `stop_on_error: bool`  
    If set to true, the parser stops on error and prompts the user.
- `panic_mode_recover: bool`  
    If true, the parser attempts panic-mode recovery.
- `errors: List[str]`  
    A list of error messages encountered during parsing.
- `parse_tree_root: Optional[ParseTreeNode]`  
    (Future extension) The root of the constructed parse tree.
- `logger: Logger`  
    A singleton logger instance.

**Constructor:**
```python
def __init__(self, tokens, stop_on_error=False, panic_mode_recover=False):
    self.tokens = tokens
    self.current_index = 0
    self.current_token = tokens[0] if tokens else None
    self.stop_on_error = stop_on_error
    self.panic_mode_recover = panic_mode_recover
    self.errors = []
    self.parse_tree_root = None  # For future parse tree construction
    self.logger = Logger()       # Singleton instance from your Logger module
```

**Core Methods:**
- **`parse() -> bool`**  
    Begins parsing by invoking the start symbol and then checks for EOF.
    
- **`advance()`**  
    Moves the current token pointer forward.
    
- **`match(expected_token_type)`**  
    Compares the current token to the expected token type and advances if it matches.
    
- **`report_error(message: str)`**  
    Logs an error message and, if configured, stops and prompts the user.
    
- **`panic_recovery(sync_set: set)`**  
    Implements panic-mode recovery by skipping tokens until a synchronization token is reached.
    
- **`print_summary()`**  
    Prints a summary report at the end of parsing.
---

### Nonterminal Methods (Based on the CFG)

Below are the methods corresponding to each production in your CFG.

#### 1. `Prog → procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;`

#### 2. `DeclarativePart → IdentifierList : TypeMark ; DeclarativePart | ε`

#### 3. `IdentifierList → idt | IdentifierList , idt`

#### 4. `TypeMark → integert | realt | chart | const assignop Value`

#### 5. `Value → NumericalLiteral`

#### 6. `Procedures → Prog Procedures | ε`

#### 7. `Args → ( ArgList ) | ε`

#### 8. `ArgList → Mode IdentifierList : TypeMark MoreArgs`

#### 9. `MoreArgs → ; ArgList | ε`

#### 10. `Mode → in | out | inout | ε`

#### 11. `SeqOfStatements → ε`

---

## Easterrr Eggg: Parse Tree Classes (Will work more on this later)

### Class: ParseTreeNode
```python
class ParseTreeNode:
    def __init__(self, name, token=None):
        self.name = name          # Name of the nonterminal or token
        self.token = token        # Associated token for terminal nodes
        self.children = []        # List of child nodes

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        if self.token:
            return f"{self.name} -> {self.token.lexeme}"
        return self.name
```

### Class: ParseTreePrinter
```python
class ParseTreePrinter:
    def print_tree(self, node, indent=0):
        print("  " * indent + str(node))
        for child in node.children:
            self.print_tree(child, indent + 1)
```

