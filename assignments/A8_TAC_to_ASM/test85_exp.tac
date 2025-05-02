proc fun
    _t1 = [bp+6] * [bp+4]  ; Temp _t1=[bp-4] = ParamA * ParamB
    [bp-2] = _t1           ; LocalC=[bp-2] = Temp
endp fun
proc five
    _t2 = 7
    A = _t2
    _t3 = 6
    B = _t3
    push A                 ; Push global A (value)
    push B                 ; Push global B (value)
    call fun
endp five
start proc five
