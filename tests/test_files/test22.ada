procedure Add(in A, B: integer;out C: integer) is
begin
	-- C := A + B;
end Add;

-- EXPECTED OUTPUT
    -- Lexeme: A
      -- Type: INT
    -- Offset: 4		// My output: 2
      -- Size: 2
     -- Depth: 1

    -- Lexeme: B
      -- Type: INT
    -- Offset: 2		// My output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: C
      -- Type: INT
    -- Offset: 0		// My output: 4
      -- Size: 2
     -- Depth: 1

    -- Lexeme: Add
      -- Type: PROC
    -- Locals: 0
-- Paramaters: IN INT, IN INT, OUT INT, (3)
     -- Depth: 0