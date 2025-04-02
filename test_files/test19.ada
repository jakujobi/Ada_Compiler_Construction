procedure Test9 is
    var1 : integer;

    procedure InnerProc is
        var1 : float;    -- Same name, different depth
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end Test9;
-- EXPECTED OUTPUT
    -- Lexeme: var1
      -- Type: FLOAT
    -- Offset: 0
      -- Size: 4
     -- Depth: 2

    -- Lexeme: InnerProc
      -- Type: PROC
    -- Locals: 1
-- Paramaters: (0)
     -- Depth: 1

    -- Lexeme: var1
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: Test9
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 0