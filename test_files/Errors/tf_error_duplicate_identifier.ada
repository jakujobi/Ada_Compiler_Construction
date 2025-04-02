-- Suggested file name: tf_error_duplicate_identifier.ada
-- Test Type: semantic – should fail because of duplicate identifiers in the declaration.
-- Expected error: Duplicate identifier "x" in the same declaration list

procedure dup_identifier is
   x, x : integer;  -- duplicate identifier in declaration
begin
   null;  -- added a null statement to avoid empty block
end dup_identifier;