-- Test File for Ada Lexical Analyzer
-- This file is designed to exercise most aspects of the lexer.

MODULE TestProgram;
PROCEDURE Main IS;
    CONSTANT greeting : INTEGER := 0;  -- Dummy constant for testing
BEGIN
    -- Valid string literals
    PUT("Hello, Ada!");  
    PUT("She said, ""Hello"" to me");  

    -- Unterminated string literal (error expected)
    PUT("This literal is unterminated);

    -- Character literal tests
    C := 'A';
    D := 'B';  -- Represents the character: B

    -- Numeric tests
    X := 42;
    Y := 3.14159;
    Z := 42 * 2 + 10 - 3;

    -- Conditional statement with relational operators
    IF X < Y THEN
        PUT("X is less than Y");
    ELSIF X = Y THEN
        PUT("X equals Y");
    ELSE
        PUT("X is greater than Y");
    END IF;

    -- Loop test
    WHILE X /= Y LOOP
        X := X + 1;
    END LOOP;

    -- Inner procedure test
    PROCEDURE Inner IS;
    BEGIN
        PUT("Inside inner procedure");
    END Inner;

    Inner;

    -- Test combined relational and boolean operators
    IF (X <= Y) and (Y >= X) then
        PUT("Relational test passed");
    END IF;

    -- Identifier length tests:
    -- Valid identifier (17 characters maximum)
    ValidIdent1234567 := 100;  -- Exactly 16 characters? (adjust as needed)
    -- Identifier too long (should trigger an error)
    IdentifierTooLongForAdaCompiler := 200;

    -- Test additional operators (or, rem, mod, and)
    IF X mod 2 = 0 or X rem 3 = 1 then
        PUT("Operator test");
    END IF;

    -- Test concatenation and additive operators with string literals
    PUT("Final value: " & " X = " & X & ", Y = " & Y);

    -- End of procedure body.
END Main;