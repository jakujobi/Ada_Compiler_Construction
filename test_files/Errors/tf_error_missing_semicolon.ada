-- Suggested file name: tf_error_missing_semicolon.ada
-- Test Type: analyzer/semantic – should fail due to a missing semicolon.
-- Expected error: Syntax error at variable declaration (missing semicolon)

procedure tf_error_missing_semicolon is
    A : Integer  -- missing semicolon here
begin
    A := 100;
    Put(A);
end tf_error_missing_semicolon;