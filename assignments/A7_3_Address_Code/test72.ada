procedure two is
 a,b,c:integr;
begin
   a:= 5;
   b:= 10;
   c:= a * b;
end two;
TAC File should be named test72.tac
proc 	two
		_t1		=	5
		a		=	_t1
		OR
		a		=	5
		
		b		=	10
		
		_t2		=	a	*	b
		c		=	_t2
endp	two
start 	proc	two