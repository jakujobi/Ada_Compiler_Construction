.model small
.586
.stack 100h

.data
A        DW ?
B        DW ?
CC       DW ?
_t1      DW ?
_t2      DW ?
_t3      DW ?

.code
include io.asm

two PROC
    push bp
    mov bp, sp
    sub sp, 0         ; No locals/temps inside 'two'

    ; TAC: _t1 = 10
    mov ax, 10
    mov _t1, ax
    ; TAC: A = _t1
    mov ax, _t1
    mov A, ax

    ; TAC: _t2 = 5
    mov ax, 5
    mov _t2, ax
    ; TAC: B = _t2
    mov ax, _t2
    mov B, ax

    ; TAC: _t3 = A * B
    mov ax, A         ; Load global A
    mov bx, B         ; Load global B into BX for multiply
    imul bx           ; AX = AX * BX (result in AX)
    mov _t3, ax       ; Store result in global temp _t3

    ; TAC: CC = _t3
    mov ax, _t3       ; Load global temp _t3
    mov CC, ax        ; Store into global CC

    add sp, 0
    pop bp
    ret 0             ; No parameters
two ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call two          ; Call the main procedure
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
