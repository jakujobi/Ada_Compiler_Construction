-- =====================================
-- File: tf_test5.ada
-- Test Type: Analyzer, Semantic
-- Description: Verifies correct handling of procedure parameter modes and local variable declarations.
-- Expected: Analyzer confirms proper use of in, out, and inout; semantic rules are enforced.
-- =====================================
procedure tf_test5(in a : integer; out b : float; inout c : char) is
    local_var : integer;  -- Local variable for internal computation
begin
    -- Empty body
end tf_test5;