procedure Test8 is
    global_var : integer;

    procedure InnerProc is
        local_var1 : float;
        local_var2 : integer;
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end Test8;
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