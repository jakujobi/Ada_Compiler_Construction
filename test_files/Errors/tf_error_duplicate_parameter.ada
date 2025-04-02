-- Suggested file name: tf_error_duplicate_parameter.ada
-- Test Type: semantic – should fail due to duplicate formal parameters in the nested procedure.
-- Expected error: Duplicate formal parameter "Value" in procedure Compute
procedure tf_error_duplicate_parameter is
   procedure Compute(in Value : Integer; out Value : Float) is
      Temp : Float;
   begin
      -- Body of Compute
   end Compute;

begin
   -- Body of tf_error_duplicate_parameter
end tf_error_duplicate_parameter;