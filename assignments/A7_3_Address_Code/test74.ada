procedure four is
 a,b:integer;		-- a and b are global aka depth == 1
 procedure one is
  c,d:integer;		-- c and d are local to one, so offsets will be used
 begin				-- c is at offset 0, d is at offset 2
   a:= 5;
   b:= 10;
   d:= 20;
   c:= d + a * b;
 end one;
begin
  one();
end four;
TAC file name is test74.ada
PROC 	one 
		a		=		5
		b		=		10
		_bp-2	=		20				or	_bp-4	=		20
		_bp-4	=		a 	*	b 		or	_bp-6	=		a 	*	b
		_bp-6	=		_bp-2	+ _bp-4 or  _bp-8	=		_bp-4	+ _bp-6
		c		=		_bp-6			or 	c	=	_bp-8
ENDP	one
PROC 	four
		call one
ENDP	four
START	PROC	four
		