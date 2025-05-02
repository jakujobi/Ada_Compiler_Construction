proc three
    _t1 = 5
    A = _t1
    _t2 = 10
    B = _t2
    _t3 = 4
    D = _t3
    _t4 = B * D   ; Temp for B * D (precedence)
    _t5 = A + _t4 ; Temp for A + result
    CC = _t5      ; Assign final result
endp three
start proc three
