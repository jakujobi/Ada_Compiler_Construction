procedure MinimalTest4 is
    var1 : integer;

    procedure InnerProc is
        var1 : float;    -- Same name, different depth
    begin
        -- Empty body
    end InnerProc;

begin
    -- Empty body
end MinimalTest4;