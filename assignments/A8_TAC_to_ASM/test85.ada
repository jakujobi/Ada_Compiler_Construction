PROCEDURE five IS
   A, B, D : INTEGER; -- Globals (Depth 1)

   PROCEDURE fun(ParamA : INTEGER; ParamB : INTEGER) IS -- Params (Depth 2)
      LocalC : INTEGER; -- Local (Depth 2)
   BEGIN
      LocalC := ParamA * ParamB;
   END fun;

BEGIN -- Body of five
   A := 7;  -- Init globals
   B := 6;
   fun(A, B); -- Call with globals passed by value
END five;
