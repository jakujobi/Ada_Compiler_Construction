.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: one
    CALL one

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc one
one PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: a = 5
     mov ax, 5    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: b = 10
     mov ax, 10    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: _t1 = a + b
     mov ax, [BP-2]    ; Load op1 into AX
     mov bx, [BP-4]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov <ERROR_TEMP_UNEXPECTED__t1>, ax   ; Store result into destination
    ; TAC: c = _t1
     mov ax, <ERROR_TEMP_UNEXPECTED__t1>    ; Load source value/address into AX
     mov [BP-6], ax   ; Store AX into destination
    ; TAC: endp one
    POP BP
one ENDP

END start
