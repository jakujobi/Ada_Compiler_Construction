.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: two
    CALL two

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc two
two PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: A = 10
     mov ax, 10    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: B = 5
     mov ax, 5    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: _t1 = A * B
     mov ax, [BP-2]    ; Load op1 into AX
     imul [BP-4]     ; Multiply AX by op2
     mov [BP-8], ax   ; Store result (lower word) into destination
    ; TAC: CC = _t1
     mov ax, [BP-8]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-6], ax   ; Store AX into destination
    ; TAC: endp two
    POP BP
two ENDP

END start
