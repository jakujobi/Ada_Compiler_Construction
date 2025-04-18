-- test_tac.ada
-- Test file to demonstrate Three Address Code generation
-- This file includes various features like:
-- * Variable declarations at different depths
-- * Arithmetic expressions
-- * Procedure calls with parameters
-- * Nested procedure definitions

procedure MainProc is
    -- Global variables (depth 1)
    a, b : integer;
    c : float;
    flag : boolean := true;
    
    -- Nested procedure with parameters
    procedure NestedProc(x : integer; y : integer; out result : integer) is
        -- Local variables (depth > 1)
        temp : integer;
        factor : integer := 2;
    begin
        -- Assignment with expression
        temp := x + y * factor;
        
        -- Assignment using variables at different depths
        result := temp - a;
    end NestedProc;
    
    -- Another nested procedure with expression 
    procedure Calculate is
        -- More local variables
        val1 : integer := 10;
        val2 : integer := 5;
        sum : integer;
    begin
        -- Assignment with complex expression
        sum := val1 + val2 * (a - b) / 2;
        
        -- Procedure call with parameters
        NestedProc(sum, val2, a);
    end Calculate;
    
begin
    -- Main procedure body
    a := 5;
    b := 10;
    c := 2.5;
    
    -- Simple expression
    a := a + b;
    
    -- Procedure call
    Calculate;
    
    -- Assignment with expression using variables at different depths
    b := a * 2;
end MainProc;
