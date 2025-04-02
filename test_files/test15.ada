procedure Test5(in x :  integer; out y :  float) is
    local1 : integer;
    local2 : float;
begin
    -- Empty body
end Test5;
-- EXPECTED OUTPUT
    -- Lexeme: local1
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: local2
      -- Type: FLOAT
    -- Offset: 2
      -- Size: 4
     -- Depth: 1

    -- Lexeme: x
      -- Type: INT
    -- Offset: 4		// My Output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: y
      -- Type: FLOAT
    -- Offset: 0		// My Output: 2
      -- Size: 4
     -- Depth: 1

    -- Lexeme: Test5
      -- Type: PROC
    -- Locals: 2
-- Paramaters: IN INT, OUT FLOAT, (2)
     -- Depth: 0