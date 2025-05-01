proc four
proc one
_t1 = 5
a = _t1
_t2 = 10
b = _t2
_t3 = 20
d = _t3
_t4 = a MUL b
_t5 = _BP-4 ADD _t4
c = _t5
endp one
call one
endp four
START	PROC	four
