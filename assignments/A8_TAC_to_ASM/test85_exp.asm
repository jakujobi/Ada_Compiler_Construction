.model small
.586
.stack 100h

.data
A        DW ?  ; Global A
B        DW ?  ; Global B
D        DW ?  ; Global D (unused)
_t2      DW ?
_t3      DW ?

.code
include io.asm

fun PROC ; Inner procedure (depth 2)
    ; Params: ParamA at [bp+6], ParamB at [bp+4]
    ; Local: LocalC at [bp-2]
    ; Temp: _t1 at [bp-4]
    push bp
    mov bp, sp
    sub sp, 4         ; Allocate space for LocalC and _t1 (2 words = 4 bytes)

    ; TAC: _t1 = [bp+6] * [bp+4]
    mov ax, [bp+6]    ; Load parameter ParamA
    mov bx, [bp+4]    ; Load parameter ParamB
    imul bx           ; AX = ParamA * ParamB
    mov [bp-4], ax    ; Store result in temp _t1

    ; TAC: [bp-2] = _t1
    mov ax, [bp-4]
    mov [bp-2], ax    ; Store into local LocalC

    add sp, 4         ; Deallocate LocalC and _t1
    pop bp
    ret 4             ; Clean up 2 parameters (ParamA, ParamB) = 4 bytes
fun ENDP

five PROC ; Outer procedure (depth 1)
    push bp
    mov bp, sp
    sub sp, 0         ; No locals in 'five'

    ; TAC: _t2 = 7, A = _t2
    mov ax, 7
    mov _t2, ax
    mov ax, _t2
    mov A, ax

    ; TAC: _t3 = 6, B = _t3
    mov ax, 6
    mov _t3, ax
    mov ax, _t3
    mov B, ax

    ; TAC: push A
    mov ax, A
    push ax
    ; TAC: push B
    mov ax, B
    push ax
    ; TAC: call fun
    call fun
    ; Note: Caller does NOT clean stack (ret 4 does it)

    add sp, 0
    pop bp
    ret 0             ; No parameters for 'five'
five ENDP

main PROC
    mov ax, @data
    mov ds, ax
    call five         ; Call the main user procedure 'five'
    mov ah, 4Ch
    mov al, 0
    int 21h
main ENDP
END main
