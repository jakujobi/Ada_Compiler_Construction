PROCEDURE Check IS;
BEGIN
    X := 42;
    IF X > 10 THEN
        PUT("X is greater than 10");
    ELSE
        PUT("X is 10 or less");
    END;
END Check;