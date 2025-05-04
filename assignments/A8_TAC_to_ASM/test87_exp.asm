        %include "io.asm"

section .data
; --- String Literals (None in this case) ---

section .bss
; --- Uninitialized Variables ---
test87.A: resw 1       ; Offset -2
test87.B: resw 1       ; Offset -4

section .text
global _start
_start:
        call    test87
        mov     eax, 1          ; exit
        xor     ebx, ebx
        int     0x80

; --- Procedure: test87 ---
; SizeOfLocals: 4 (A, B)
; SizeOfParams: 0
test87:
        push    ebp
        mov     ebp, esp
        sub     esp, 4          ; Allocate space for locals A, B

; -- GET(A);
        mov     eax, ebp        ; Get address for A (_BP-2)
        sub     eax, 2
        push    eax             ; Push address of A
        call    readint         ; Read integer into BX
        pop     eax             ; Pop address of A
        mov     [eax], bx       ; Store read value into A

; -- B := A + 5;
        mov     ax, [ebp-2]     ; Load A into AX
        add     ax, 5           ; Add 5
        mov     [ebp-4], ax     ; Store result in B

; -- PUT(B);
        mov     ax, [ebp-4]     ; Load B into AX
        call    writeint        ; Write integer in AX

; -- PUT(A);
        mov     ax, [ebp-2]     ; Load A into AX
        call    writeint        ; Write integer in AX

; -- End of procedure
        mov     esp, ebp        ; Deallocate locals
        pop     ebp
        ret 