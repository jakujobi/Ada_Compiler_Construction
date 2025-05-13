.MODEL SMALL
.STACK 100H

INCLUDE io.asm

start PROC
    ; Initialize DS
    MOV AX, @DATA
    MOV DS, AX

    ; Call the user's main procedure: test87
    CALL test87

    ; Exit program
    MOV AH, 4CH
    INT 21H
start ENDP

.DATA
.CODE
    ; TAC: proc test87
test87 PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: rdi A
    CALL READINT
    MOV [BP-2], BX
    ; TAC: _t1 = A + 5
     mov ax, [BP-2]    ; Load op1 into AX
     mov bx, 5    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov [BP-6], ax   ; Store result into destination
    ; TAC: B = _t1
     mov ax, [BP-6]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: wri B
    MOV AX, [BP-4]
    CALL WRITEINT
    CALL NEWLINE
    ; TAC: wri A
    MOV AX, [BP-2]
    CALL WRITEINT
    CALL NEWLINE
    ; TAC: endp test87
    POP BP
test87 ENDP

END start
