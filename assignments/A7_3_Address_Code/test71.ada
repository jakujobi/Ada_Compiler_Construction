procedure one is
 a,b,c:integer;
begin
   a:= 5;
   b:= 10;
   c:= a + b;
end one;
TAC File should be named test71.tac
proc 	one
		_t1		=	5
		a		=	_t1
		OR
		a		=	5
		
		b		=	10
		
		_t2		=	a	+	b
		c		=	_t2
endp	one
start 	proc	one