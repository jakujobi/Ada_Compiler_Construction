-- =====================================
-- File: tf_test1.ada
-- Test Type: Lexical, Analyzer, Semantic
-- Description: Tests basic variable and constant declarations.
-- Expected: Successful parsing and semantic analysis.
-- =====================================
procedure tf_test1 is
    num : integer;      -- Single integer variable
    ch  : char;         -- Single character variable
    rate : float;       -- Single float variable
    max_value : constant := 100;   -- Constant declaration
begin
    -- Empty body
end tf_test1;
-- This is a comment line
-- Additional note: Test is accurate and should compile.


-- EXPECTED OUTPUT
    -- Lexeme: max_value
      -- Type: CONST_INT
     -- Value: 100
     -- Depth: 1

    -- Lexeme: num
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: rate
      -- Type: FLOAT
    -- Offset: 3
      -- Size: 4
     -- Depth: 1

    -- Lexeme: ch
      -- Type: CHAR
    -- Offset: 2
      -- Size: 1
     -- Depth: 1

    -- Lexeme: Test1
      -- Type: PROC
    -- Locals: 4
-- Paramaters: (0)
     -- Depth: 0