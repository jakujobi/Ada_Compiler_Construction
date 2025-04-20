-- super_test.ada
-- Comprehensive test file for Ada compiler
-- This file combines features from ALL test cases to test all compiler components:
-- - Lexical analysis
-- - Parsing
-- - Symbol table management
-- - Semantic analysis
-- - Code generation

procedure SuperTest is
    -- SECTION 1: Constant declarations
    PI : constant := 3.14159;  -- Float constant
    MAX_VALUE : constant := 1000;  -- Integer constant
    MIN_VALUE : constant := -1000; -- Negative integer constant
    CHAR_CONST : constant := 'X';  -- Character constant
    TAX_RATE : constant := 0.06;   -- Another float constant
    E : constant := 2.71828;       -- From test17.ada
    
    -- SECTION 2: Basic variable declarations
    count, total : integer;  -- Multiple integer variables
    average, sum, rate : float;  -- Multiple float variables
    letter, symbol : char;  -- Multiple character variables
    var1, var2 : integer;   -- From test17.ada
    var3 : char;            -- From test17.ada
    
    -- SECTION 3: Array declarations
    scores : array (1..10) of integer;  -- Integer array
    temperatures : array (1..7) of float;  -- Float array
    letters : array (1..26) of char;  -- Character array
    matrix : array (1..3, 1..3) of integer;  -- 2D array
    
    -- SECTION 4: Procedure with same-name variables (from test4.ada)
    procedure SameNameTest is
        var1 : float;    -- Same name as global var1, different depth
    begin
        var1 := 3.14;  -- This should reference the local var1
    end SameNameTest;
    
    -- SECTION 5: Test of various parameter combinations (from test5.ada, test15.ada)
    procedure ParamTest1(in param1 : integer; out param2 : float; inout param3 : char) is
        local_var : integer;
    begin
        local_var := param1 + 5;
        param2 := float(local_var) * PI;
    end ParamTest1;
    
    -- SECTION 6: Test with two parameters only (from test15.ada)
    procedure ParamTest2(in x : integer; out y : float) is
        local1 : integer;
        local2 : float;
    begin
        local1 := x + 10;
        local2 := float(local1) * 2.5;
        y := local2;
    end ParamTest2;
    
    -- SECTION 7: Nested procedure with parameters
    procedure Calculate(in a : integer; out b : float; inout c : char) is
        -- Local variables
        temp : integer;
        result : float;
        
        -- Nested procedure (tests nesting and scoping from test3.ada, test13.ada)
        procedure Helper is
            nested_var : integer;
        begin
            nested_var := 10;
            temp := nested_var * 2;
        end Helper;
        
        -- Multiple levels of nesting for deep scope testing
        procedure DeepNest is
            deep_var1 : integer;
            
            procedure DeeperNest is
                deep_var2 : float;
            begin
                deep_var2 := 3.14;
                deep_var1 := 42;
            end DeeperNest;
            
        begin
            deep_var1 := 10;
            DeeperNest;
        end DeepNest;
        
    begin
        -- Procedure body with different statement types
        temp := a + 5;
        result := float(temp) * PI;
        b := result;
        
        -- Call nested procedures
        Helper;
        DeepNest;
        
        -- Conditional statements
        if temp > 10 then
            b := b + 1.0;
        elsif temp < 5 then
            b := b - 1.0;
        else
            b := b * 2.0;
        end if;
        
        -- Loop statements
        for i in 1..5 loop
            temp := temp + i;
        end loop;
        
        -- While loop
        while temp < 100 loop
            temp := temp * 2;
        end loop;
    end Calculate;
    
    -- SECTION A: Edge case - intentionally commented out to avoid compilation error
    -- Testing invalid constant (from test30.ada)
    -- invalid_string_const : constant := "abc";  -- Invalid string constant
    
    -- SECTION B: Edge case - intentionally commented out to avoid compilation error
    -- Testing duplicate declarations (from test14.ada)
    -- dup_var : integer;
    -- dup_var : float;  -- Duplicate declaration at the same depth
    
    -- SECTION 8: Another procedure to demonstrate scope
    procedure PrintValues(in value : integer) is
        local_value : integer;
    begin
        local_value := value;
        
        -- Demonstrate block statement with local declarations
        declare
            block_var : integer;
        begin
            block_var := local_value * 2;
        end;
    end PrintValues;
    
    -- SECTION 3.5: Tests for procedures with multiple parameters (test29.ada)
    procedure MultiParamProc1 (id, id2:integer) is
        id3:integer;
    begin
        id3 := id + id2;
    end MultiParamProc1;
    
    -- Test for procedure with no parameters (test24.ada, test27.ada)
    procedure SimpleProc is
    begin
        -- Empty body
    end SimpleProc;
    
    -- Test of procedure with out parameters (test22.ada)
    procedure Add(in A, B: integer; out C: integer) is
    begin
        C := A + B;
    end Add;
    
    -- Test with multiple parameters of different types (test21.ada)
    procedure Quadratic(in A, B, C: Float;
                        out Root_1, Root_2: Float; out OK: Integer) is
        D: Float;
    begin
        D := B * B - 4.0 * A * C;
        if D < 0.0 then
            OK := 0;
        else
            OK := 1;
            Root_1 := (-B + D) / (2.0 * A);
            Root_2 := (-B - D) / (2.0 * A);
        end if;
    end Quadratic;
    
    -- Test with procedure with comments in various positions (test23.ada)
    procedure CommentTest is -- comment at end of line
        count:CONSTANT:=5; -- another comment
    begin -- comment after begin
        null; -- empty statement with comment
    end CommentTest; -- final comment
    
    -- SECTION 4.5: Test for procedures with multiple levels of nesting (test28.ada)
    procedure MultiLevelExample is
        a, b, c, d: integer;
        
        procedure NestedFun(a: integer; out b: integer) is
            c: integer;
        begin
            c := a * 2;
            b := c;
        end NestedFun;
        
        procedure AnotherNested is
            local_var: integer;
            
            procedure DeepNested is
                deep_var: float;
            begin
                deep_var := 3.14;
            end DeepNested;
            
        begin
            local_var := 10;
            DeepNested;
        end AnotherNested;
        
    begin
        a := 5;
        b := 10;
        NestedFun(a, c);
        d := c;
        AnotherNested;
    end MultiLevelExample;
    
begin
    -- SECTION 9: Main procedure body with various statements
    
    -- Assignment statements
    count := 0;
    total := MAX_VALUE;
    average := 0.0;
    letter := 'A';
    
    -- Array assignments
    for i in 1..10 loop
        scores(i) := i * 10;
    end loop;
    
    for i in 1..7 loop
        temperatures(i) := float(i) * PI;
    end loop;
    
    -- Initialize matrix
    for i in 1..3 loop
        for j in 1..3 loop
            matrix(i, j) := i * j;
        end loop;
    end loop;
    
    -- Arithmetic operations
    sum := 0.0;
    for i in 1..10 loop
        sum := sum + float(scores(i));
    end loop;
    
    average := sum / 10.0;
    
    -- Procedure calls with different parameter patterns
    Calculate(total, average, letter);
    PrintValues(count);
    ParamTest1(MAX_VALUE, sum, symbol);
    ParamTest2(MIN_VALUE, rate);
    SameNameTest;
    
    -- Variable shadowing test
    declare
        count : float;  -- Shadows the outer 'count' variable
    begin
        count := 3.14;  -- This should reference the local count
    end;
    
    -- Conditional execution
    if average > 50.0 then
        count := count + 1;
    end if;
    
    -- Case statement
    case count is
        when 0 =>
            letter := 'Z';
        when 1 =>
            letter := 'Y';
        when 2 =>
            letter := 'X';
        when others =>
            letter := 'W';
    end case;
    
    -- Exit statement in loop
    for i in 1..100 loop
        if i > 50 then
            exit;
        end if;
        count := count + 1;
    end loop;
    
    -- Nested if statements
    if count > 0 then
        if total > 500 then
            letter := 'S';
        else
            letter := 'T';
        end if;
    end if;
    
    -- Expression with parentheses and multiple operators
    total := (count * 2) + (MAX_VALUE / 10) - 5;
    
    -- Boolean expressions
    if (count > 10) and (total < 1000) then
        letter := 'C';
    elsif (count <= 10) or (total >= 1000) then
        letter := 'D';
    end if;
    
    -- Test of various arithmetic expressions
    var1 := 5 + 10;
    var1 := var1 - 3;
    var1 := var1 * 2;
    var1 := var1 / 4;
    
    -- Test of nested expressions
    var2 := ((var1 + 5) * 2) - (8 / 2);
    
    -- Test of mixed type expressions
    average := float(var1) + 2.5;
    
    -- Test of relational operators
    if var1 = var2 then
        letter := 'E';
    elsif var1 /= var2 then
        letter := 'F';
    elsif var1 < var2 then
        letter := 'G';
    elsif var1 <= var2 then
        letter := 'H';
    elsif var1 > var2 then
        letter := 'I';
    elsif var1 >= var2 then
        letter := 'J';
    end if;
    
    -- Call the added procedures
    SimpleProc;
    Add(5, 10, total);
    MultiParamProc1(count, total);
    Quadratic(1.0, 2.0, 1.0, average, sum, count);
    CommentTest;
    MultiLevelExample;
    
    -- Additional procedural calls to cover more test cases
    declare
        temp_a, temp_b, temp_c: integer;
    begin
        temp_a := 10;
        temp_b := 20;
        Add(temp_a, temp_b, temp_c);
    end;
    
end SuperTest;

-- EXPECTED OUTPUT (symbol table information for key elements)
-- Lexeme: PI
  -- Type: CONST_FLOAT
 -- Value: 3.14159
 -- Depth: 1

-- Lexeme: MAX_VALUE
  -- Type: CONST_INT
 -- Value: 1000
 -- Depth: 1

-- Lexeme: count
  -- Type: INT
-- Offset: 0
  -- Size: 2
 -- Depth: 1

-- Lexeme: SuperTest
  -- Type: PROC
-- Locals: numerous
-- Parameters: (0)
 -- Depth: 0

-- Lexeme: Calculate
  -- Type: PROC
-- Locals: several
-- Parameters: (3) [in a:integer, out b:float, inout c:char]
 -- Depth: 1

-- Lexeme: ParamTest1
  -- Type: PROC
-- Locals: 1
-- Parameters: (3) [in param1:integer, out param2:float, inout param3:char]
 -- Depth: 1

-- Lexeme: ParamTest2
  -- Type: PROC
-- Locals: 2
-- Parameters: (2) [in x:integer, out y:float]
 -- Depth: 1

-- Lexeme: SameNameTest
  -- Type: PROC
-- Locals: 1
-- Parameters: (0)
 -- Depth: 1

-- Lexeme: var1 (in SameNameTest)
  -- Type: FLOAT
-- Offset: 0
  -- Size: 4
 -- Depth: 2

-- Lexeme: var1 (in SuperTest)
  -- Type: INT
-- Offset: appropriate_value
  -- Size: 2
 -- Depth: 1

-- Lexeme: Helper
  -- Type: PROC
-- Locals: 1
-- Parameters: (0)
 -- Depth: 2

-- Examples of other expected entries omitted for brevity