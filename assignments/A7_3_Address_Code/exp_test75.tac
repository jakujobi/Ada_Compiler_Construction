PROC	fun
		_t1		=	_bp+4*	_bp+2	-- Temp for param_a * param_b
		_bp-2	=	_t1 				-- Assign result to local_c (offset -2)
ENDP	fun 
PROC	five
		a		=	5
		b 		=	10
		d		=	20
		_t1		=	a	*	b 
		_t2		=	d	+	_t1
		c		=	_t2	

		push	a
		push	b
		call	fun
ENDP	five
START 	PROC	five 