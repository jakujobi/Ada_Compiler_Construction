-- =================================================================
-- COMBINED ERROR TEST CASES FOR ADA COMPILER
-- =================================================================
-- Author: John Akujobi
-- GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
-- 
-- Description:
-- This file contains multiple error test cases to verify the compiler's 
-- error detection capabilities. Each test case produces a specific error
-- that the compiler should detect and report appropriately.
-- =================================================================

-- TEST CASE 1: END IDENTIFIER MISMATCH
-- -----------------------------------
-- Error type: Semantic Error
-- Expected outcome: Compiler should detect that the end identifier 
-- doesn't match the procedure name.
procedure Error1_EndMismatch is
begin
    -- Empty procedure body
end Error1_EndMismatch_Wrong;  -- Error: Should be "Error1_EndMismatch"


-- TEST CASE 2: DUPLICATE FORMAL PARAMETER
-- --------------------------------------
-- Error type: Semantic Error
-- Expected outcome: Compiler should detect duplicate parameter names
-- in the formal parameter list.
procedure Error2_DuplicateParam is
   procedure Compute(in Value1 : Integer; out Value1 : Float) is
      -- Error: "Value1" is used twice in parameter list
      Temp : Float;
   begin
      -- Body of Compute
   end Compute;

begin
   -- Body of main procedure
end Error2_DuplicateParam;


-- TEST CASE 3: DUPLICATE IDENTIFIERS IN DECLARATION
-- ------------------------------------------------
-- Error type: Semantic Error
-- Expected outcome: Compiler should detect when multiple variables 
-- with the same name are declared in the same declaration list.
procedure Error3_DuplicateDeclaration is
   x, x : integer;  -- Error: "x" appears twice in the same declaration
begin
   -- Empty procedure body
end Error3_DuplicateDeclaration;


-- TEST CASE 4: MULTIPLE DECLARATION OF THE SAME IDENTIFIER
-- -------------------------------------------------------
-- Error type: Semantic Error
-- Expected outcome: Compiler should detect when the same identifier 
-- is declared multiple times at the same scope.
procedure Error4_MultipleDeclaration is
    num : integer;         -- First declaration
    num : float;           -- Error: Duplicate declaration of "num"
    val : character;       -- Another variable
begin
    -- Empty body
end Error4_MultipleDeclaration;


-- TEST CASE 5: MISSING SEMICOLON
-- -----------------------------
-- Error type: Syntax Error
-- Expected outcome: Compiler should detect missing semicolon after declaration.
procedure Error5_MissingSemicolon is
    A : Integer           -- Error: Missing semicolon
begin
    A := 100;
    Put(A);
end Error5_MissingSemicolon;


-- TEST CASE 6: INVALID IDENTIFIER
-- ------------------------------
-- Error type: Lexical Error
-- Expected outcome: Compiler should detect invalid character in identifier.
procedure Error6_InvalidIdentifier is
    A@ : Integer;          -- Error: Invalid character '@' in identifier
begin
    A@ := 5;               -- Error: Same invalid identifier
    Put(A@);               -- Error: Same invalid identifier
end Error6_InvalidIdentifier;

-- END OF TEST CASES
