.model small
.586
.stack 100h

.data
A        DW ?
B        DW ?
CC       DW ?
D        DW ?
E        DW ?
_t1      DW ?
_t2      DW ?
_t3      DW ?
_t4      DW ?
_t5      DW ? ; Temp for A + B
_t6      DW ? ; Temp for E + D
_t7      DW ? ; Temp for _t5 + _t6

.code
include io.asm

six PROC
    push bp
    mov bp, sp
    sub sp, 0         ; No locals/temps inside 'six'

    ; TAC: Init A, B, D, E
    mov ax, 1
    mov _t1, ax
    mov ax, _t1
    mov A, ax
    mov ax, 2
    mov _t2, ax
    mov ax, _t2
    mov B, ax
    mov ax, 3
    mov _t3, ax
    mov ax, _t3
    mov D, ax
    mov ax, 4
    mov _t4, ax
    mov ax, _t4
    mov E, ax

    ; TAC: _t5 = A + B
    mov ax, A
    add ax, B
    mov _t5, ax

    ; TAC: _t6 = E + D
    mov ax, E
    add ax, D
    mov _t6, ax

    ; TAC: _t7 = _t5 + _t6
    mov ax, _t5
    add ax, _t6
    mov _t7, ax

    ; TAC: CC = _t7
    mov ax, _t7
    mov CC, ax

    add sp, 0
    pop bp
    ret 0             ; No parameters
six ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call six          ; Call the main procedure
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
