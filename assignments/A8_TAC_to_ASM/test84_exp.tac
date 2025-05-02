proc one
    _t1 = 5
    [bp-2] = _t1   ; Local C at [bp-2]
    _t2 = 10
    [bp-4] = _t2   ; Local D at [bp-4]
    _t3 = A + B    ; Access globals A, B. Temp _t3 at [bp-6]
    [bp-4] = _t3   ; Assign result to local D
endp one
proc four
    _t4 = 1
    A = _t4        ; Assign to global A
    _t5 = 2
    B = _t5        ; Assign to global B
    call one
endp four
start proc four
