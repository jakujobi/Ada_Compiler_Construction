procedure four is
 a,b:integer;		-- a and b are global aka depth == 1
 procedure one is
  c,d:integer;		-- c and d are local to one, so offsets will be used
 begin				-- c is at offset -2, d is at offset -4 (Assuming INT size 2)
   a:= 5;
   b:= 10;
   d:= 20;
   c:= d + a * b;
 end one;
begin
  one();
end four;
		