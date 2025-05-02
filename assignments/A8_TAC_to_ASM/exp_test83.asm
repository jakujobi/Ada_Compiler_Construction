.model small
.586
.stack 100h

.data
A        DW ?
B        DW ?
CC       DW ?
D        DW ?
_t1      DW ?
_t2      DW ?
_t3      DW ?
_t4      DW ?  ; Temp for B * D
_t5      DW ?  ; Temp for A + _t4

.code
include io.asm

three PROC
    push bp
    mov bp, sp
    sub sp, 0         ; No locals/temps inside 'three'

    ; TAC: _t1 = 5, A = _t1
    mov ax, 5
    mov _t1, ax
    mov ax, _t1
    mov A, ax

    ; TAC: _t2 = 10, B = _t2
    mov ax, 10
    mov _t2, ax
    mov ax, _t2
    mov B, ax

    ; TAC: _t3 = 4, D = _t3
    mov ax, 4
    mov _t3, ax
    mov ax, _t3
    mov D, ax

    ; TAC: _t4 = B * D
    mov ax, B
    mov bx, D
    imul bx
    mov _t4, ax

    ; TAC: _t5 = A + _t4
    mov ax, A
    add ax, _t4
    mov _t5, ax

    ; TAC: CC = _t5
    mov ax, _t5
    mov CC, ax

    add sp, 0
    pop bp
    ret 0             ; No parameters
three ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call three        ; Call the main procedure
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
