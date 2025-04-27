procedure five is
 a,b,c,d:integer;
 procedure fun(a:integer; b:integer) is -- Params: a@BP+6, b@BP+4 (Assuming INT size 2)
  c:integer; -- Local: c@BP-2
 begin
  c:=a*b;
 end fun;
begin
  a:=5;
  b:= 10;
  d:= 20;
  c:= d + a * b;

  fun(a,b);
end five;
TAC file name is test75.tac
PROC	fun
		_bp-2	=	_bp+2	*	_bp+4	or	_bp-4	=	_bp+6	*	_bp+4
		_bp-0	=	_bp-2 				or	_bp-2	=	_bp-4
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