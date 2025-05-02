.model small
.586
.stack 100h

.data
A        DW ?  ; Global
B        DW ?  ; Global

.code
include io.asm

one PROC ; Inner procedure (depth 2)
    ; Locals: C at [bp-2], D at [bp-4]
    ; Temps: _t1 at [bp-6], _t2 at [bp-8], _t3 at [bp-10]
    push bp
    mov bp, sp
    sub sp, 10        ; Allocate space for C, D, _t1, _t2, _t3 (5 words = 10 bytes)

    ; TAC: _t1 = 5
    mov ax, 5
    mov [bp-6], ax    ; Store 5 in _t1
    ; TAC: [bp-2] = _t1 (C = _t1)
    mov ax, [bp-6]
    mov [bp-2], ax    ; Store into C

    ; TAC: _t2 = 10
    mov ax, 10
    mov [bp-8], ax    ; Store 10 in _t2
    ; TAC: [bp-4] = _t2 (D = _t2)
    mov ax, [bp-8]
    mov [bp-4], ax    ; Store into D

    ; TAC: _t3 = A + B
    mov ax, A         ; Access global A
    add ax, B         ; Access global B
    mov [bp-10], ax   ; Store result in _t3
    ; TAC: [bp-4] = _t3 (D = _t3)
    mov ax, [bp-10]
    mov [bp-4], ax    ; Store into D

    add sp, 10        ; Deallocate locals/temps (C, D, _t1, _t2, _t3)
    pop bp
    ret 0             ; No parameters for 'one'
one ENDP

four PROC ; Outer procedure (depth 1)
    push bp
    mov bp, sp
    sub sp, 0         ; No locals in 'four'

    ; TAC: _t4 = 1
    mov ax, 1
    ; TAC: A = _t4
    mov A, ax         ; Assign to global A

    ; TAC: _t5 = 2
    mov ax, 2
    ; TAC: B = _t5
    mov B, ax         ; Assign to global B

    ; TAC: call one
    call one

    add sp, 0
    pop bp
    ret 0             ; No parameters for 'four'
four ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call four         ; Call the main user procedure 'four'
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
