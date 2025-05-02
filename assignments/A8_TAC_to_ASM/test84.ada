PROCEDURE four IS
  A, B : INTEGER;            -- depth 1 (globals)

  PROCEDURE one IS           -- depth 2
    C, D : INTEGER;          -- depth 2 locals
  BEGIN
    C := 5;                  -- Assign to local C
    D := 10;                 -- Assign to local D
    D := A + B;              -- Assign to local D using globals A, B
  END one;

BEGIN -- Body of four
  A := 1; -- Initialize globals
  B := 2;
  one;                       -- Call inner procedure
END four;
