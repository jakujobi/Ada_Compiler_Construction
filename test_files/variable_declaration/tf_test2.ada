-- =====================================
-- File: tf_test2.ada
-- Test Type: Analyzer, Semantic
-- Description: Tests simultaneous variable declarations and type consistency among integer, float, and char types.
-- Expected: Analyzer ensures proper type checking and declaration handling.
-- =====================================
procedure tf_test2 is
    x, y : integer;     -- Declaration of two integer variables
    a, b, c : float;    -- Declaration of three float variables
    letter : char;      -- Single character variable
begin
    -- Empty body
end tf_test2;

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