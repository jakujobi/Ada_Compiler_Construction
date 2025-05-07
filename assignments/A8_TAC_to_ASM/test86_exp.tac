proc six
    _t1 = 1
    A = _t1
    _t2 = 2
    B = _t2
    _t3 = 3
    D = _t3
    _t4 = 4
    E = _t4
    _t5 = A + B   ; Temp for (A + B)
    _t6 = E + D   ; Temp for (E + D)
    _t7 = _t5 + _t6 ; Temp for final addition
    CC = _t7      ; Assign result
endp six
start proc six
