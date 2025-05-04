        %include "io.asm"

section .data
; --- String Literals ---
_S0:    db      "Hello There!$"
_S1:    db      "This has \"quotes\" inside.$" ; Escaped quotes handled
_S2:    db      "$" ; Empty string results in just terminator

section .bss
; --- Uninitialized Variables (None) ---

section .text
global _start
_start:
        call    test88
        mov     eax, 1          ; exit
        xor     ebx, ebx
        int     0x80

; --- Procedure: test88 ---
; SizeOfLocals: 0
; SizeOfParams: 0
test88:
        push    ebp
        mov     ebp, esp
        sub     esp, 0          ; No locals

; -- PUTLN("Hello There!");
        mov     edx, _S0        ; Load string address
        call    writestr
        call    writeln

; -- PUTLN("This has ""quotes"" inside.");
        mov     edx, _S1
        call    writestr
        call    writeln

; -- PUTLN("");
        mov     edx, _S2
        call    writestr
        call    writeln

; -- End of procedure
        mov     esp, ebp        ; Deallocate locals (0)
        pop     ebp
        ret 