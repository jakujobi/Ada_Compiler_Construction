-- Nested procedures and expressions
procedure Main is
    X, Y : Integer;
    procedure Nested is
    begin
        X := 5;
        Y := X + 10;
    end Nested;
begin
--    Nested;
--    Put(Y);
end Main;