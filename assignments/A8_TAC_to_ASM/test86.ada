PROCEDURE six IS
   A, B, CC, D, E : INTEGER; -- Globals (Depth 1), Renamed C to CC
BEGIN
   A := 1; B := 2; D := 3; E := 4; -- Init
   CC := (A + B) + (E + D);
END six;
