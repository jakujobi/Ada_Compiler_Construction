proc MixParams
_t1 = _BP+8 + 1
[_BP+6] = _t1
_t2 = [_BP+4] + _BP+8
_t3 = _t2 + [_BP+6]
[_BP+4] = _t3
endp MixParams
proc test89
_t4 = 1
_BP-2 = _t4
_t5 = 2
_BP-4 = _t5
_t6 = 3
_BP-6 = _t6
wri _BP-2
wri _BP-4
wri _BP-6
wrln
push _BP-2
push @_BP-4
push @_BP-6
call MixParams
wri _BP-2
wri _BP-4
wri _BP-6
wrln
endp test89
START PROC test89 