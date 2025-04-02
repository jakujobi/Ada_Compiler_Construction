-- tf_inner_proc_local_vars.ada
-- Test Type: Semantic Analysis (Scoping & Offset Management)
-- Description: Tests a procedure with a global variable
--   and an inner procedure containing two local variables.
--   Checks that offsets and type sizes are correctly computed.
 

procedure inner_local_vars is
    global_var : integer;

    procedure InnerProc is
        local_var1 : float;
        local_var2 : integer;
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end inner_local_vars;


-- EXPECTED OUTPUT
    -- Lexeme: local_var1
      -- Type: FLOAT
    -- Offset: 0
      -- Size: 4
     -- Depth: 2

    -- Lexeme: local_var2
      -- Type: INT
    -- Offset: 4
      -- Size: 2
     -- Depth: 2

    -- Lexeme: global_var
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: InnerProc
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 1

    -- Lexeme: Test8
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 0