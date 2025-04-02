procedure Test10(in a :  integer; out b : float; inout  c : char) is
    local_var : integer;
begin
    -- Empty body
end Test10;

-- EXPECTED OUTPUT
    -- Lexeme: local_var
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: a
      -- Type: INT
    -- Offset: 5		// My Output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: b
      -- Type: FLOAT
    -- Offset: 1		// My Output: 2
      -- Size: 4
     -- Depth: 1

    -- Lexeme: c
      -- Type: CHAR
    -- Offset: 0		// My Output: 6
      -- Size: 1
     -- Depth: 1

    -- Lexeme: Test10
      -- Type: PROC
    -- Locals: 1
-- Paramaters: IN INT, OUT FLOAT, INOUT CHAR, (3)
     -- Depth: 0