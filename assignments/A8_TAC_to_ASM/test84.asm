.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: four
    CALL four

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc four
four PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: A = 1
     mov ax, 1    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: B = 2
     mov ax, 2    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: call one
    CALL one
    ; TAC: endp four
    POP BP
four ENDP

    ; TAC: proc one
one PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: C = 5
     mov ax, 5    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: D = 10
     mov ax, 10    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: _t1 = A + B
     mov ax, [BP-2]    ; Load op1 into AX
     mov bx, [BP-4]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-6], ax   ; Store result into destination
    ; TAC: D = _t1
     mov ax, [BP-6]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: endp one
    POP BP
one ENDP

END start
