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
    ; TAC: A = 7
     mov ax, 7    ; Load source value/address into AX
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: B = 6
     mov ax, 6    ; Load source value/address into AX
     mov [BP-4], ax   ; Store AX into destination
    ; TAC: push B
    PUSH [BP-4]
    ; TAC: push A
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
    ; TAC: _t1 = ParamA * ParamB
     mov ax, [BP+4]    ; Load op1 into AX
     imul [BP+2]     ; Multiply AX by op2
     mov [BP-4], ax   ; Store result (lower word) into destination
    ; TAC: LocalC = _t1
     mov ax, [BP-4]    ; Load source into AX (mem-to-mem workaround)
     mov [BP-2], ax   ; Store AX into destination
    ; TAC: endp fun
    POP BP
fun ENDP

END start
