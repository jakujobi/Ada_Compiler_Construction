proc five
proc fun
_t1 = _BP+4 * _BP+2
LocalC = _t1
endp fun
_t2 = 7
A = _t2
_t3 = 6
B = _t3
push A
push B
call fun
endp five
START	PROC	five
