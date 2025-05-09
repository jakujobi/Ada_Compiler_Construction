_S0: .ASCIZ "Hello There!"
_S1: .ASCIZ "This has \"quotes\" inside."
_S2: .ASCIZ ""

proc test88
wrs _S0
wrln
wrs _S1
wrln
wrs _S2
wrln
endp test88
START PROC test88
