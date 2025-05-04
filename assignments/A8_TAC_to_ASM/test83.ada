PROCEDURE three IS
   A, B, CC, D : INTEGER; -- Renamed C to CC
BEGIN
   A := 5;  -- Added
   B := 10; -- Added
   D := 4;  -- Added
   CC := A + B * D; -- Should evaluate B*D first
END three;
