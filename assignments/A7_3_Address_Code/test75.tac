proc five
proc fun
_t1 = _BP+4 * _BP+2
c = _t1
endp fun
_t2 = 5
a = _t2
_t3 = 10
b = _t3
_t4 = 20
d = _t4
_t5 = a * b
_t6 = d + _t5
c = _t6
push a
push b
call fun
endp five
START	PROC	five
