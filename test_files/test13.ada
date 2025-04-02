procedure Test3 is
	main_var : integer;
    procedure NestedProc is
        local_var1 : integer;
        local_var2 : float;
    begin
        -- Empty body
    end NestedProc;

    
begin
    -- Empty body
end Test3;
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