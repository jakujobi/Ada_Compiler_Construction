-- =====================================
-- File: tf_test4.ada
-- Test Type: Semantic
-- Description: Checks nested procedure behavior and variable shadowing between outer and inner scopes.
-- Expected: Analyzer differentiates outer 'var1' from the inner 'var1'; semantic rules correctly applied.
-- =====================================

procedure tf_test4 is
    var1 : integer;  -- Outer variable declaration

    procedure InnerProc is
        var1 : float;    -- Inner variable shadows outer variable
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end tf_test4;