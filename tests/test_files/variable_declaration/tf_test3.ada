-- =====================================
-- File: tf_test3.ada
-- Test Type: Lexical, Analyzer, Semantic
-- Description: Evaluates proper scoping and parsing of nested procedures and variable declarations.
-- Expected: Both global and nested scope declarations correctly identified and processed.
-- =====================================

procedure tf_test3 is        -- Procedure entry point
    global_var : integer;         -- Global variable declaration

    procedure InnerProc is       -- Nested procedure definition
        local_var1 : float;
        local_var2 : integer;
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end tf_test3;


-- EXPECTED OUTPUT
    -- Lexeme: local_var1
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 2

    -- Lexeme: local_var2
      -- Type: FLOAT
    -- Offset: 2
      -- Size: 4
     -- Depth: 2

    -- Lexeme: main_var
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: NestedProc
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 1

    -- Lexeme: Test3
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 0