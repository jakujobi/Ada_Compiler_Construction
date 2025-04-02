-- Suggested file name: tf_error_invalid_identifier.ada
-- Test Type: lexical/analyzer – should fail due to illegal character '@' in identifier.
-- Expected error: Illegal character in identifier "A@"
procedure invalid_ident is
    A@ : Integer;  -- invalid identifier: '@' is not allowed
begin
    A@ := 5;
    Put(A@);
end invalid_ident;