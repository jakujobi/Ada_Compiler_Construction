procedure Quadratic(in A, B, C:  Float;
					out Root_1,  Root_2:  Float; out OK:  Integer) is
	D:  Float;
begin
end Quadratic;
-- EXPECTED OUTPUT
    -- Lexeme: Root_1
      -- Type: FLOAT
    -- Offset: 6		// My output: 16
      -- Size: 4
     -- Depth: 1

    -- Lexeme: Root_2
      -- Type: FLOAT
    -- Offset: 2		// My output: 12
      -- Size: 4
     -- Depth: 1

    -- Lexeme: OK
      -- Type: INT
    -- Offset: 0		// My output: 20
      -- Size: 2
     -- Depth: 1

    -- Lexeme: A
      -- Type: FLOAT
    -- Offset: 18		// My output: 8
      -- Size: 4
     -- Depth: 1

    -- Lexeme: B
      -- Type: FLOAT
    -- Offset: 14		// My output: 4
      -- Size: 4
     -- Depth: 1

    -- Lexeme: C
      -- Type: FLOAT
    -- Offset: 10		// My output: 0
      -- Size: 4
     -- Depth: 1

    -- Lexeme: D
      -- Type: FLOAT
    -- Offset: 0
      -- Size: 4
     -- Depth: 1

    -- Lexeme: Quadratic
      -- Type: PROC
    -- Locals: 1
-- Paramaters: IN FLOAT, IN FLOAT, IN FLOAT, OUT FLOAT, OUT FLOAT, OUT INT, (6)
     -- Depth: 0