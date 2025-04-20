-- tf_error_undeclared_variable.ada
-- Test Type: semantic – should fail due to the use of an undeclared variable.
-- Expected error: Identifier "z" is not declared.
procedure e_undeclared_var is
   x, y : integer;
begin
   z := 10.0;  -- Error: "z" is not declared.
end e_undeclared_var;
