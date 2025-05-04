# CSC 446 Assign #8

* Hamer
* Early Due: 4/2/25
* Grace period expires on 5/9/21 @ 4:00 PM

Write a simple code generator for the Ada subset language. Translate your Three Address Code into 8086 assembly language.

---

## IOStatment productions

You will need to add the IOStatment productions to your parser

```bnf
IO_Stat         -> In_Stat | Out_Stat
In_Stat         -> get(Id_List)
Id_List         -> idt Id_List_Tail
Id_List_Tail    -> , idt Id_List_Tail | ε
Out_Stat        -> put(Write_List) | putln(Write_List)
Write_List      -> Write_Token Write_List_Tail
Write_List_Tail -> , Write_Token Write_List_Tail | ε
Write_Token     -> idt | numt | literal
```

---

## Intermediate I/O instructions

Use the intermediate instruction `wr#` for all write’s in your program and `rd#` for all read’s. The `#` is replaced by either the letter `i` (integer) or `s` (string). For a writeln, use the appropriate number of `wr#` and then issue a final `wrln` instruction. You may need to add a new class to your symbol table to handle string literals.

---

## Provided assembly procedures (`io.asm`)

The file `io.asm` is on the class web page and may be copied to your data disk for use in this assignment. It contains the assembly procedures

* `writech`   – write a single ASCII char
* `writeint`  – write an integer value
* `writestr`  – write a `$` delimited string
* `writeln`  – write a newline
* `readch`    – read a single character
* `readint`   – read an integer value

---

## Procedure template

The template for all procedures will be as follows

```assembly
procname    PROC
    push bp
    mov bp,sp
    sub sp, SIZE OF LOCALS FROM SYM TABLE

    ; translated code

    add sp, SIZE OF LOCALS FROM SYM TABLE
    pop bp
    ret SIZE OF PARAMETERS FROM SYM TABLE
procname    ENDP
```

---

## Local variables and stack offsets

Variables in functions at depth > 1 will be stored in the stack. You will have to convert your offsets to the appropriate 8086 offsets if you have not done so already. The 8086 uses negative offsets. Your first variable (`_BP+0`) would occur at `[BP-2]` in assembly. The instruction

```assembly
mov ax, [BP-2]
```

would copy your first local variable into the AX register. Remember that you cannot do a memory to memory move in 8086 assembly.

---

## Generated `main` procedure

Your code generator needs to generate the following main procedure

```assembly
main    PROC
    mov ax, @data
    mov ds, ax

    call PROC NAME FROM START STATEMENT

    mov ah, 04ch
    int 21h
main    ENDP
END     main
```

---

## Program skeleton

The program beginning is as follows:

```assembly
.model small
.586
.stack 100h

.data
    VAR1    DW  ?          ; for integer variables at depth 1
    VAR2    DW  ?          ; for integer variables at depth 1
    _S0     DB  "String","$"   ; for strings with appended $
.code
include io.asm
```

The following will be from your three address code file:

```assembly
one     PROC
one     ENDP
etc...
main    PROC    ; as above
main    ENDP

END     main
```

The class web site contains a link to DOSBOX from CSc 314 under which you can run your code.
