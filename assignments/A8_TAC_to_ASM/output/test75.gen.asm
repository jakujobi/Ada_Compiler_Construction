.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: five
    CALL five

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc five
five PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: a = 5
     mov ax, 5    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: b = 10
     mov ax, 10    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: d = 20
     mov ax, 20    ; Load source value/address into AX
     mov [BP-8], ax   ; Store AX into destination
    ; TAC: _t2 = a * b
     mov ax, [BP-2]    ; Load op1 into AX
     imul [BP-4]     ; Multiply AX by op2
     mov [BP-6], ax   ; Store result (lower word) into destination
    ; TAC: _t3 = d + _t2
     mov ax, [BP-8]    ; Load op1 into AX
     mov bx, [BP-6]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-8], ax   ; Store result into destination
    ; TAC: c = _t3
     mov ax, [BP-8]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-6], ax   ; Store AX into destination
    ; TAC: push b
    PUSH [BP-4]
    ; TAC: push a
    PUSH [BP-2]
    ; TAC: call fun
    CALL fun
    ; TAC: endp five
    POP BP
five ENDP

    ; TAC: proc fun
fun PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: _t1 = a * b
     mov ax, [BP+4]    ; Load op1 into AX
     imul [BP+2]     ; Multiply AX by op2
     mov [BP-4], ax   ; Store result (lower word) into destination
    ; TAC: c = _t1
     mov ax, [BP-4]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: endp fun
    POP BP
fun ENDP

END start
