# John Akujobi
# Questions
### CSC 446
### Assignment #2

**Instructor:** Hamer  
**Due Date:** Monday, February 10

## Grammar Rules
### Given Grammar for a Subset of Ada
```
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

---
## Programs
### Instructions
Draw the parse trees for the following programs. **Underline all tokens.**


#### **(a)**
```ada
procedure one is
    two : integer;
begin

end one;
```

#### **(b)**

```ada
procedure two is
    three, four : integer;
    procedure five is
    begin

    end five;
begin

end two;
```

#### **(c)**

```ada
procedure three is
    four, five : integer;
    procedure six ( in seven : integer ; eight : integer ) is
    begin

    end six;
begin

end three;
```

---

### **Hint:**

You may want to use your paper sideways for drawing the parse trees.

**Note:** Save this grammar as it will be used in the next assignment.

---
# Program 1
```pascal
procedure one is
    two : integer;
begin

end one;
```

First broke it into this production
``Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt ;``

### Mermaid Code
I've used mermaid code for previous projects, and i used it's html properties to add the underlining.

```mermaidcode
flowchart TD
%% Top-level node for Program (a):
    A[Prog]
    A1[<u>procedure</u>]
    A2[idt: <u>one</u>]
    A3[Args: ε]
    A4[<u>is</u>]
    A5[DeclarativePart]
    A6[Procedures: ε]
    A7[<u>begin</u>]
    A8[SeqOfStatements: ε]
    A9[<u>end</u>]
    A10[idt: <u>one</u>]
    A11[<u>;</u>]

    A --> A1
    A --> A2
    A --> A3
    A --> A4
    A --> A5
    A --> A6
    A --> A7
    A --> A8
    A --> A9
    A --> A10
    A --> A11

    %% DeclarativePart subtree:
    A5 --> DP1[IdentifierList]
    DP1 --> DP2[idt: <u>two</u>]
    DP1 --> DP3[<u>:</u>]
    DP3 --> DP4[TypeMark]
    DP4 --> DP5[integert: <u>integer</u>]
    DP5 --> DP6[<u>;</u>]
    DP6 --> DP7[DeclarativePart: ε]

```

### First Visualization


Then i visualized it using MermaidChart

```cardlink
url: https://www.mermaidchart.com/
title: "Mermaid Chart - Create complex, visual diagrams with text. A smarter way of creating diagrams."
host: www.mermaidchart.com
favicon: https://www.mermaidchart.com/img/favicon.ico
```

![](Program%20A%20-%20A2%20Parser-2025-02-10-064006.svg)



---
# 