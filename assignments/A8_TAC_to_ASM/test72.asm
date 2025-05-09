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
    ; TAC: a = 5
     mov ax, 5    ; Load source value/address into AX
     mov <ERROR_UNEXPECTED_FORMAT_a>, ax   ; Store AX into destination
    ; TAC: b = 10
     mov ax, 10    ; Load source value/address into AX
     mov <ERROR_UNEXPECTED_FORMAT_b>, ax   ; Store AX into destination
    ; TAC: _t1 = a * b
     mov ax, <ERROR_UNEXPECTED_FORMAT_a>    ; Load op1 into AX
     imul <ERROR_UNEXPECTED_FORMAT_b>     ; Multiply AX by op2
     mov <ERROR_TEMP_UNEXPECTED__t1>, ax   ; Store result (lower word) into destination
    ; TAC: c = _t1
     mov ax, <ERROR_TEMP_UNEXPECTED__t1>    ; Load source value/address into AX
     mov <ERROR_UNEXPECTED_FORMAT_c>, ax   ; Store AX into destination
    ; TAC: endp two
    POP BP
two ENDP

END start
