        %include "io.asm"

section .data
_S0:    db      ""$             ; Empty string for writeln

section .bss
test89.X: resw 1          ; Offset -2
test89.Y: resw 1          ; Offset -4
test89.Z: resw 1          ; Offset -6

section .text
global _start
_start:
        call    test89
        mov     eax, 1          ; exit
        xor     ebx, ebx
        int     0x80

; --- Procedure: MixParams ---
; A (in):  [bp+8]
; B (out): [bp+6] -> address of Y
; C (in out): [bp+4] -> address of Z
; SizeOfLocals: 0 (temps dont count here yet)
; SizeOfParams: 6 (2+2+2)
MixParams:
        push    ebp
        mov     ebp, esp
        sub     esp, 0          ; No locals for MixParams

; -- B := A + 1;
        mov     ax, [ebp+8]     ; Load A (value)
        add     ax, 1           ; A + 1
        mov     bx, [ebp+6]     ; Load address of B (which is address of Y)
        mov     [bx], ax        ; Store result into address pointed by B

; -- C := C + A + B;
        mov     bx, [ebp+4]     ; Load address of C (which is address of Z)
        mov     cx, [bx]        ; Dereference C to get its current value
        add     cx, [ebp+8]     ; Add A (value)
        mov     bx, [ebp+6]     ; Load address of B (which is address of Y)
        add     cx, [bx]        ; Add B (value) - B was just updated
        mov     bx, [ebp+4]     ; Load address of C again
        mov     [bx], cx        ; Store final result into address pointed by C

; -- End of procedure MixParams
        mov     esp, ebp
        pop     ebp
        ret     6               ; Pop 6 bytes of params (3 words)

; --- Procedure: test89 ---
; SizeOfLocals: 6 (X, Y, Z)
; SizeOfParams: 0
test89:
        push    ebp
        mov     ebp, esp
        sub     esp, 6          ; Allocate space for locals X, Y, Z

; -- X := 1; Y := 2; Z := 3;
        mov     word [ebp-2], 1 ; X
        mov     word [ebp-4], 2 ; Y
        mov     word [ebp-6], 3 ; Z

; -- PUT(X); PUT(Y); PUT(Z); PUTLN("");
        mov     ax, [ebp-2]     ; PUT(X)
        call    writeint
        mov     ax, [ebp-4]     ; PUT(Y)
        call    writeint
        mov     ax, [ebp-6]     ; PUT(Z)
        call    writeint
        mov     edx, _S0        ; PUTLN("")
        call    writestr
        call    writeln

; -- MixParams(X, Y, Z);
        ; Push C (Z) - in out - push address
        mov     eax, ebp
        sub     eax, 6
        push    eax             ; push address of Z
        ; Push B (Y) - out - push address
        mov     eax, ebp
        sub     eax, 4
        push    eax             ; push address of Y
        ; Push A (X) - in - push value
        push    word [ebp-2]    ; push value of X

        call    MixParams       ; Call procedure

; -- PUT(X); PUT(Y); PUT(Z); PUTLN("");
        mov     ax, [ebp-2]     ; PUT(X)
        call    writeint
        mov     ax, [ebp-4]     ; PUT(Y)
        call    writeint
        mov     ax, [ebp-6]     ; PUT(Z)
        call    writeint
        mov     edx, _S0        ; PUTLN("")
        call    writestr
        call    writeln

; -- End of procedure test89
        mov     esp, ebp        ; Deallocate locals
        pop     ebp
        ret 