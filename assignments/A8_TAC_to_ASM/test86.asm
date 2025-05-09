.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: six
    CALL six

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc six
six PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: A = 1
     mov ax, 1    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: B = 2
     mov ax, 2    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: D = 3
     mov ax, 3    ; Load source value/address into AX
     mov [BP-8], ax   ; Store AX into destination
    ; TAC: E = 4
     mov ax, 4    ; Load source value/address into AX
     mov [BP-10], ax   ; Store AX into destination
    ; TAC: _t1 = A + B
     mov ax, [BP-2]    ; Load op1 into AX
     mov bx, [BP-4]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-12], ax   ; Store result into destination
    ; TAC: _t2 = E + D
     mov ax, [BP-10]    ; Load op1 into AX
     mov bx, [BP-8]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-14], ax   ; Store result into destination
    ; TAC: _t3 = _t1 + _t2
     mov ax, [BP-12]    ; Load op1 into AX
     mov bx, [BP-14]    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-16], ax   ; Store result into destination
    ; TAC: CC = _t3
     mov ax, [BP-16]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-6], ax   ; Store AX into destination
    ; TAC: endp six
    POP BP
six ENDP

END start
