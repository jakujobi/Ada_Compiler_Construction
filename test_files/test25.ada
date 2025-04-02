procedure FullTest (in X, Y : Integer; out Z : Float; inout W : Char) is
   A, B, C : Integer;
   D : constant := 3.14;
   E : constant := 3;
   
   procedure NestedProc (inout W : Integer) is
      E : Char;
   begin
   end NestedProc;

begin
end FullTest;
--    Lexeme: E
--      Type: CHAR
--    Offset: 0		// My output: 0
--      Size: 1
--     Depth: 2
--
--    Lexeme: W
--      Type: INT
--    Offset: 0
--      Size: 2
--     Depth: 2
--
--    Lexeme: NestedProc
--      Type: PROC
--    Locals: 1
--Paramaters: INOUT INT, (1)
--     Depth: 1
--
--    Lexeme: A
--      Type: INT
--    Offset: 0		// My output: 4
--      Size: 2
--     Depth: 1
--
--    Lexeme: B
--      Type: INT
--    Offset: 2
--      Size: 2
--     Depth: 1
--
--    Lexeme: C
--      Type: INT
--    Offset: 4		// My output: 0
--    Size: 2
--   Depth: 1
--
--  Lexeme: D
--    Type: CONST_FLOAT
--   Value: 3.14
--   Depth: 1
--
--  Lexeme: E
--    Type: CONST_INT
--   Value: 3
--   Depth: 1
--
--  Lexeme: W
--    Type: CHAR
--  Offset: 0		// My output: 8
--    Size: 1
--   Depth: 1
--
--  Lexeme: X
--    Type: INT
--  Offset: 7		// My output: 2
--    Size: 2
--   Depth: 1
--
--  Lexeme: Y
--    Type: INT
--  Offset: 5		// My output: 0
--    Size: 2
--   Depth: 1
--
--  Lexeme: Z
--    Type: FLOAT
--  Offset: 1		// My output: 4
--    Size: 4
--   Depth: 1
--
--  Lexeme: FullTest
--    Type: PROC
--  Locals: 6
--Paramaters: IN INT, IN INT, OUT FLOAT, INOUT CHAR, (4)
--   Depth: 0