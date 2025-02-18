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

---
## Test Programs
The simplest Ada program is then:
``` pascal
PROCEDURE one IS
	BEGIN
	END one;
```

A more typical program would be

```pascal
PROCEDURE MAIN IS

PROCEDURE PROC1 IS
	BEGIN
	END PROC1;

BEGIN
END MAIN;
```

A more complicated program would look like

```pascal
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

```pascal
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