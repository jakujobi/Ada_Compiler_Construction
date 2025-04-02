procedure Test2 is
    x, y : integer;     -- Two integers
    a, b, c : float;    -- Three floats
    letter : char;  -- Character variable
begin
    -- Empty body
end Test2;

-- EXPECTED OUTPUT
    -- Lexeme: a
      -- Type: FLOAT
    -- Offset: 4		// My Output: 12
      -- Size: 4
     -- Depth: 1

    -- Lexeme: b
      -- Type: FLOAT
    -- Offset: 8		// My Output: 8
      -- Size: 4
     -- Depth: 1

    -- Lexeme: c
      -- Type: FLOAT
    -- Offset: 12		// My Output: 4
      -- Size: 4
     -- Depth: 1

    -- Lexeme: x
      -- Type: INT
    -- Offset: 0		// My Output: 2
      -- Size: 2
     -- Depth: 1

    -- Lexeme: y
      -- Type: INT
    -- Offset: 2		// My Output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: letter
      -- Type: CHAR
    -- Offset: 16		// My Output: 16
      -- Size: 1
     -- Depth: 1

    -- Lexeme: Test2
      -- Type: PROC
    -- Locals: 6
-- Paramaters: (0)
     -- Depth: 0