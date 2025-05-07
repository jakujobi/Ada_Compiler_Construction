procedure test89 is
  X : Integer := 1;
  Y : Integer := 2;
  Z : Integer := 3;

  procedure MixParams (A : in Integer; B : out Integer; C : in out Integer) is
  begin
    B := A + 1;
    C := C + A + B;
  end MixParams;

begin
  PUT(X); PUT(Y); PUT(Z); PUTLN(""); -- Initial: 1 2 3
  MixParams(X, Y, Z); -- Pass X by value, Y by ref (out), Z by ref (in out)
  PUT(X); PUT(Y); PUT(Z); PUTLN(""); -- Expected: 1 2 6
end test89; 