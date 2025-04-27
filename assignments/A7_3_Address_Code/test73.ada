procedure three is
 a,b,cc,d:integer;
begin
   a:= 5;
   b:= 10;
   d:= 20;
   cc:= d + a * b;
end three;
TAC file Name is test83.ada
PROC 	three
		a		=	5
		b 		=	10
		d		=	20
		_t1		=	a	*	b 
		_t2		=	d	+	_t1
		cc		=	_t2
ENDP	three
START 	PROC	three 
		