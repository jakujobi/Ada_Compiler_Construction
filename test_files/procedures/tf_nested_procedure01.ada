-- Suggested file name: tf_nested_procedure01.ada
-- Test Type: semantic (nested procedures and parameter passing correctness)
-- Expected when run: No output; compilation should succeed verifying proper procedure scopes.

procedure tf_nested_procedure01 is
   -- Declare integer variables used within the procedure
   a, b, c, d : integer;

   -- A nested procedure 'fun' with an 'out' parameter b
   procedure fun(a : integer; out b : integer) is
      -- Local variable declaration for procedure 'fun'
      c : integer;
   begin
      -- Implementation could check assignment to out parameters
   end fun;

begin
   -- Main procedure body
end tf_nested_procedure01;