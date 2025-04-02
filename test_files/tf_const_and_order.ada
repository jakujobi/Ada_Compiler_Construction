-- tf_const_and_order.ada
-- Test Type: Semantic Analysis
-- Description: Tests a procedure (Test7) that declares constants and variables.
--  Verifies that constant values, variable offsets, sizes, and scope depths are handled correctly.
 

procedure const_and_order is
     PI : constant := 3.14159;
     E  : constant  := 2.71828;
    var1, var2  : integer;
    var3        : char;
begin
    -- Empty body
end const_and_order;

-- EXPECTED OUTPUT
    -- Lexeme: PI
      -- Type: CONST_FLOAT
     -- Value: 3.14159
     -- Depth: 1

    -- Lexeme: E
      -- Type: CONST_FLOAT
     -- Value: 2.71828
     -- Depth: 1

    -- Lexeme: var1
      -- Type: INT
    -- Offset: 0		// My Output: 2
      -- Size: 2
     -- Depth: 1

    -- Lexeme: var2
      -- Type: INT
    -- Offset: 2		// My Output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: var3
      -- Type: CHAR
    -- Offset: 4
      -- Size: 1
     -- Depth: 1

    -- Lexeme: Test7
      -- Type: PROC
    -- Locals: 5
-- Paramaters: (0)
     -- Depth: 0