-- line one of comment
-- line two of comment
procedure test4 is
 x,y,z:integer;
 a,b,c,d:integer;
 procedure summit (inout sum:integer; x,y:integer) is
  begin
	sum := (x*y) mod 3;
  end summit;
begin
end test4;
