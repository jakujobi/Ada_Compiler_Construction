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

one PROC
    push bp
    mov bp, sp
    sub sp, 0         ; No locals/temps inside 'one'

    ; TAC: _t1 = 10
    mov ax, 10
    mov _t1, ax
    ; TAC: A = _t1
    mov ax, _t1
    mov A, ax

    ; TAC: _t2 = 40
    mov ax, 40
    mov _t2, ax
    ; TAC: B = _t2
    mov ax, _t2
    mov B, ax

    ; TAC: _t3 = A + B
    mov ax, A         ; Load global A
    add ax, B         ; Add global B
    mov _t3, ax       ; Store result in global temp _t3

    ; TAC: CC = _t3
    mov ax, _t3       ; Load global temp _t3
    mov CC, ax        ; Store into global CC

    add sp, 0
    pop bp
    ret 0             ; No parameters
one ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call one          ; Call the main procedure
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
