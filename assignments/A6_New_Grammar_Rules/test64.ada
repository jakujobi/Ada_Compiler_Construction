-- Start of a 2 line
-- comment 
procedure four is
    x,y,z:integer;
    a,b,c,d:integer;
  procedure summit(inout a:integer; x:integer; y:integer) is
      sum:integer; --variable sum
  begin
    sum := (x*y) mod 3;
  end summit;
begin
  x:=a+b/c+d;
  y:= (a - b / 2)*x;
end four;