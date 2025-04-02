-- =================================================================
-- BASIC ADA CONSTRUCTS TEST CASES
-- =================================================================
-- Author: John Akujobi
-- GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
-- 
-- Description:
-- This file contains test cases for basic Ada language constructs
-- including simple procedures, nested procedures, constants, and
-- parameter passing. Each test case demonstrates a different aspect
-- of the Ada language that the compiler should handle correctly.
-- =================================================================

-- TEST CASE 1: SIMPLE PROCEDURE
-- ----------------------------
-- Tests: Basic procedure declaration and structure
PROCEDURE SimpleProc IS
BEGIN
    -- Empty procedure body
END SimpleProc;


-- TEST CASE 2: NESTED PROCEDURE
-- ----------------------------
-- Tests: Nested procedure declaration and scope handling
PROCEDURE OuterProc IS

    PROCEDURE InnerProc IS
    BEGIN
        -- Inner procedure body
    END InnerProc;

BEGIN
    -- Outer procedure body
END OuterProc;


-- TEST CASE 3: CONSTANTS AND NESTED PROCEDURE
-- -----------------------------------------
-- Tests: Constant declarations, multiple variable declarations,
-- and nested procedures with parameters
PROCEDURE ConstantAndNested IS
    count : CONSTANT := 5;  -- Constant declaration
    a, b : INTEGER;         -- Multiple variable declaration
    
    PROCEDURE NestedWithParams(x : INTEGER; y : INTEGER) IS
    BEGIN
        -- Nested procedure with parameters
    END NestedWithParams;
    
BEGIN
    -- Main procedure body
END ConstantAndNested;


-- TEST CASE 4: PROCEDURES WITH IN/OUT PARAMETERS
-- --------------------------------------------
-- Tests: Parameter modes (in, out) and scoping of variables
PROCEDURE ParameterModes IS
    a, b, c, d : INTEGER;  -- Multiple variable declaration
    
    PROCEDURE Calculation(a : INTEGER; OUT b : INTEGER) IS
        c : INTEGER;       -- Local variable with same name as outer scope
    BEGIN
        -- Procedure with in and out parameters
    END Calculation;
    
BEGIN
    -- Main procedure body
END ParameterModes;

-- END OF BASIC CONSTRUCT TESTS
