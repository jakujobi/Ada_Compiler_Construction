_S0: .ASCIZ "Hello, Compiler!"
_S1: .ASCIZ "This is a test."
_S2: .ASCIZ "Another line..."
_S3: .ASCIZ ""
_S4: .ASCIZ "End of test."

proc Test_Strings
wrs _S0
wrs _S1
wrln
wrs _S2
wrs _S3
wrln
wrs _S4
wrln
endp Test_Strings
START PROC Test_Strings
