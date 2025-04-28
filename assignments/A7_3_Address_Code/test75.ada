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