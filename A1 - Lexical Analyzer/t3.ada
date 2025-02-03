MODULE ComplexExample;
PROCEDURE Main IS
    -- This is a comment
    CONSTANT Pi : FLOAT := 3.14159;
    X, Y : INTEGER;
BEGIN
    X := 10;
    Y := X * 2 + 5;
    -- lalalalalala
    
    WHILE Y > X LOOP
        IF Y mod 2 = 0 THEN
            PUT("Even Number: " & Y);
        ELSE
            PUT("Odd Number: " & Y);
        END IF;
        Y := Y - 1;
    END LOOP;

    PROCEDURE InnerProcedure IS
        Z : INTEGER := 100;
    BEGIN
        Z := Z / 2;
        PUT("Inner Z Value: " & Z);
    END InnerProcedure;
    
    InnerProcedure;
    
    PUT("Final Values: X=" & X & ", Y=" & Y);
END Main;