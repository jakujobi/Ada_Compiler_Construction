proc five
proc fun
_t1 = a * b
c = _t1
endp fun
a = 5
b = 10
d = 20
_t2 = a * b
_t3 = d + _t2
c = _t3
push b
push a
call fun
endp five
START PROC five
