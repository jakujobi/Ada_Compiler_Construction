-- =====================================
-- Combined Test File: tf_variable_declarations.ada
-- =====================================
-- File: tf_variable_declarations.ada
-- Description: This file aggregates several Ada test procedures originally split across
--              multiple files (tf_test1.ada, tf_test2.ada, tf_test3.ada, tf_test4.ada, tf_test5.ada).
-- Test Types:
--   tf_test1: Lexical, Analyzer, Semantic
--             -> Tests basic variable and constant declarations.
--   tf_test2: Analyzer, Semantic
--             -> Tests simultaneous variable declarations and type consistency.
--   tf_test3: Lexical, Analyzer, Semantic
--             -> Evaluates proper scoping and parsing with nested procedures.
--   tf_test4: Semantic
--             -> Checks nested procedure behavior and variable shadowing.
--   tf_test5: Analyzer, Semantic
--             -> Verifies correct handling of procedure parameter modes.
-- Expected: Each procedure should pass its respective checks successfully.
-- =====================================

-- Test 1: Basic variable and constant declarations (from tf_test1.ada)
procedure tf_test1 is
    num : integer;          -- Single integer variable
    ch  : char;             -- Single character variable
    rate : float;           -- Single float variable
    max_value : constant := 100;   -- Constant declaration
begin
    null;  -- Empty body
end tf_test1;
-- ...End of tf_test1...

-- Test 2: Multiple variable declarations with type consistency (from tf_test2.ada)
procedure tf_test2 is
    x, y : integer;         -- Declaration of two integer variables
    a, b, c : float;        -- Declaration of three float variables
    letter : char;          -- Single character variable
begin
    null;  -- Empty body
end tf_test2;
-- ...End of tf_test2...

-- Test 3: Nested procedure demonstrating proper scoping (from tf_test3.ada)
procedure tf_test3 is
    global_var : integer;   -- Global variable declaration
    procedure InnerProc is -- Nested procedure definition
        local_var1 : float; -- Local float variable
        local_var2 : integer; -- Local integer variable
    begin
        null;  -- Empty body
    end InnerProc;
begin
    null;  -- Empty body
end tf_test3;
-- ...End of tf_test3...

-- Test 4: Nested procedure with variable shadowing (from tf_test4.ada)
procedure tf_test4 is
    var1 : integer;         -- Outer variable declaration
    procedure InnerProc is
        var1 : float;       -- Inner variable shadows outer variable
    begin
        null;  -- Empty body
    end InnerProc;
begin
    null;  -- Empty body
end tf_test4;
-- ...End of tf_test4...

-- Test 5: Procedure parameter modes and local variable usage (from tf_test5.ada)
procedure tf_test5(in a : integer; out b : float; inout c : char) is
    local_var : integer;    -- Local variable for internal operations
begin
    null;  -- Empty body
end tf_test5;
-- ...End of tf_test5...
