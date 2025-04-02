-- Suggested file name: tf_nested_procedure02.ada
-- Test Type: semantic (constant and parameter validation in nested procedures)

PROCEDURE tf_nested_procedure02 IS
   -- A constant declaration to be validated
   count : CONSTANT := 5;
   a, b : INTEGER;

   -- Nested procedure 'eight' taking two integer parameters
   PROCEDURE eight(x : INTEGER; y : INTEGER) IS
   BEGIN
   END eight;
BEGIN

-- The above code defines a procedure named 'tf_nested_procedure02' that contains a nested procedure 'eight'.
END tf_nested_procedure02;