procedure five is
a,b,c,d:integer;
procedure fun(a:integer; out b:integer) is
c:integer;
begin
end fun;
begin
end five;
-- EXPECTED OUTPUT
    -- Lexeme: a
      -- Type: INT
    -- Offset: 2		// My output: 0
      -- Size: 2
     -- Depth: 2

    -- Lexeme: b
      -- Type: INT
    -- Offset: 0		// My output: 2
      -- Size: 2
     -- Depth: 2

    -- Lexeme: c
      -- Type: INT
    -- Offset: 0
      -- Size: 2
     -- Depth: 2

    -- Lexeme: a
      -- Type: INT
    -- Offset: 0		// My output: 6
      -- Size: 2
     -- Depth: 1

    -- Lexeme: b
      -- Type: INT
    -- Offset: 2		// My output: 4
      -- Size: 2
     -- Depth: 1

    -- Lexeme: c
      -- Type: INT
    -- Offset: 4		// My output: 2
      -- Size: 2
     -- Depth: 1

    -- Lexeme: d
      -- Type: INT
    -- Offset: 6		// My output: 0
      -- Size: 2
     -- Depth: 1

    -- Lexeme: fun
      -- Type: PROC
    -- Locals: 1
-- Paramaters: IN INT, OUT INT, (2)
     -- Depth: 1

    -- Lexeme: five
      -- Type: PROC
    -- Locals: 4
-- Paramaters: (0)
     -- Depth: 0