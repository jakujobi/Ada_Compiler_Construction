PROC 	one 
		a		=		5
		b		=		10
		_bp-4	=		20				-- Assign to d (offset -4)
		_t1		=		a 	*	b 		-- Temp for a*b
		_t2		=		_bp-4	+ 	_t1		-- Temp for d + (a*b)
		_bp-2	=		_t2				-- Assign result to c (offset -2)
ENDP	one
PROC 	four
		call one
ENDP	four
START	PROC	four 