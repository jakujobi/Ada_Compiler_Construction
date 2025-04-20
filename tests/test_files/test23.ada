PROCEDURE comment IS -- ignore
count:CONSTANT:=5;
-- ignore
PROCEDURE eight( --ignore
x:INTEGER; y:INTEGER) IS
BEGIN 
-- ignore
END eight;
BEGIN --ignore
END comment;
-- EXPECTED OUTPUT
    -- Lexeme: x
      -- Type: INT
    -- Offset: 2		// My output: 0
      -- Size: 2
     -- Depth: 2

    -- Lexeme: y
      -- Type: INT
    -- Offset: 0		// My output: 2
      -- Size: 2
     -- Depth: 2

    -- Lexeme: eight
      -- Type: PROC
    -- Locals: 0
-- Paramaters: IN INT, IN INT, (2)
     -- Depth: 1

    -- Lexeme: count
      -- Type: CONST_INT
     -- Value: 5
     -- Depth: 1

    -- Lexeme: comment
      -- Type: PROC
    -- Locals: 2
-- Paramaters: (0)
     -- Depth: 0