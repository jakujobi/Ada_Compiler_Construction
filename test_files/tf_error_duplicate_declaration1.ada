-- Suggested file name: tf_error_duplicate_declaration1.ada
-- Test Type: semantic – should fail due to duplicate variable "num" declarations.
-- Expected error: Duplicate identifier "num" declared more than once
procedure dup_declaration1 is
    num : integer;         -- first declaration
    num : float;           -- duplicate declaration (conflict in type and identifier)
    val : character;
begin
    -- Empty body
end dup_declaration1;