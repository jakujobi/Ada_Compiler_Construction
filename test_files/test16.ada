procedure Test6 is

    procedure Level1 is
        var1 : integer;
        var2 : char;
        
        procedure Level2 is
            var3 : float;
        begin
            -- Empty body
        end Level2;

    begin
        -- Empty body
    end Level1;

begin
    -- Empty body
end Test6;

-- EXPECTED OUTPUT
    -- Lexeme: var3
      -- Type: FLOAT
    -- Offset: 0
      -- Size: 4
     -- Depth: 3

    -- Lexeme: Level2
      -- Type: PROC
    -- Locals: 1
-- Paramaters: (0)
     -- Depth: 2

    -- Lexeme: var1
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 2

    -- Lexeme: var2
      -- Type: CHAR
    -- Offset: 2
      -- Size: 1
     -- Depth: 2

    -- Lexeme: Level1
      -- Type: PROC
    -- Locals: 3
-- Paramaters: (0)
     -- Depth: 1

    -- Lexeme: Test6
      -- Type: PROC
    -- Locals: 1
-- Paramaters: (0)
     -- Depth: 0