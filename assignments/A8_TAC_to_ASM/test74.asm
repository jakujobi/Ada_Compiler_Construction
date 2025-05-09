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
    ; TAC: call one
    CALL <ERROR_FORMATTING_one>
    ; TAC: endp four
    POP BP
four ENDP

    ; TAC: proc one
one PROC NEAR
    PUSH BP
    MOV BP, SP
    ; TAC: a = 5
     mov ax, 5    ; Load source value/address into AX
     mov <ERROR_FORMATTING_a>, ax   ; Store AX into destination
    ; TAC: b = 10
     mov ax, 10    ; Load source value/address into AX
     mov <ERROR_FORMATTING_b>, ax   ; Store AX into destination
    ; TAC: d = 20
     mov ax, 20    ; Load source value/address into AX
     mov <ERROR_FORMATTING_d>, ax   ; Store AX into destination
    ; TAC: _t1 = a * b
     mov ax, <ERROR_FORMATTING_a>    ; Load op1 into AX
     imul <ERROR_FORMATTING_b>     ; Multiply AX by op2
     mov <ERROR_TEMP_UNEXPECTED__t1>, ax   ; Store result (lower word) into destination
    ; TAC: _t2 = d + _t1
     mov ax, <ERROR_FORMATTING_d>    ; Load op1 into AX
     mov bx, <ERROR_TEMP_UNEXPECTED__t1>    ; Load op2 into BX
     add ax, bx        ; Add op2 (from BX) to op1 (in AX)
     mov <ERROR_TEMP_UNEXPECTED__t2>, ax   ; Store result into destination
    ; TAC: c = _t2
     mov ax, <ERROR_TEMP_UNEXPECTED__t2>    ; Load source value/address into AX
     mov <ERROR_FORMATTING_c>, ax   ; Store AX into destination
    ; TAC: endp one
    POP BP
one ENDP

END start
