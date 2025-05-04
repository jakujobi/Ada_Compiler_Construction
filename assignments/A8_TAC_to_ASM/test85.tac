proc five
proc fun
_t1 = ParamA * ParamB
LocalC = _t1
endp fun
A = 7
B = 6
push B
push A
call fun
endp five
START PROC five
