# Project_Description

ASSIGN #7

HAMER

DUE: 4-18-25

Add the appropriate actions to your parser to translate a source program into Three Address Code.

For all variables declared at a depth of 1 use the actual variable name in the three address statement.

For variables declared at depths higher than 1 you must use offset notation. The outer most procedure starts at depth = 0.

Variables at depths greater than 1 will have offsets starting at 0 and increasing based on the size of the variable.

**Example:**

```text
num, sum: integer;  
ave, limit: float;

num  offset = 0  
sum  offset = 2  
ave  offset = 4  
limit offset = 8
```

Constants’ value will be substituted directly into the three-address code.

In three address code the variable `limit` would be referred to as `_BP-8`, however you may start your offsets at 2 as discussed in class if you like.

Parameters to functions will be  **referred to using positive offsets** , for example:

```text
procedure proc ( num1: integer; num2: integer )
```

`num1` would have offset 6 and `num2` would have offset 4 and `num1` would be referred to by `_BP+6` as discussed in class. The Pascal style will be used and pushes parameters from left to right.

Add the `pseudo` instruction to the end of your **three address** code file:

```
START name
```

The name used here needs to be the name of your program's outer most procedure.

Use the same name for the **three address** code file as the program’s name only **change** the extension to `.TAC`.

For example: if the input file is `TEST15.ADA` the TAC file would have the name `TEST15.TAC`.

---

You will need to add the following productions to your  **parser** :

```text
AssignStat -> idt := Expr | ProcCall  
ProcCall   -> idt ( Params )  
Params     -> idt ParamsTail | num ParamsTail | ε  
ParamsTail -> , idt ParamsTail | , num ParamsTail | ε
```

The statement:

```text
Proc(x,y);
```

Will result in the Three Address Statements:

```text
push x  
push y  
call Proc
```

If both `x` and `y` are passed by value and will be as follows assuming both are **pass** by reference (**inout** or **out** mode):

```text
push @x  
push @y  
call Proc
```

---
