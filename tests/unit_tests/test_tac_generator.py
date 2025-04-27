# Ada_Compiler_Construction/tests/unit_tests/test_tac_generator.py

import pytest
import os
import tempfile

# Assuming the structure allows this import
# Adjust if tests are run differently (e.g., using package install)
try:
    from src.jakadac.modules.TACGenerator import TACGenerator
    from src.jakadac.modules.SymTable import Symbol, EntryType, VarType, ParameterMode
    from src.jakadac.modules.Token import Token
except ImportError:
    # Fallback if running from a different structure or package not installed
    # This might require adjusting PYTHONPATH or how tests are invoked
    pytest.skip("Skipping TACGenerator tests, modules not found.", allow_module_level=True)

# --- Fixtures ---

@pytest.fixture
def dummy_token():
    """Provides a dummy token for creating Symbol objects."""
    return Token(token_type='DUMMY', lexeme='dummy', line_number=1, column_number=1)

@pytest.fixture
def tac_generator(tmp_path):
    """Provides a TACGenerator instance writing to a temporary file."""
    # Use pytest's tmp_path fixture for a unique temporary directory per test function
    temp_tac_file = tmp_path / "test_output.tac"
    return TACGenerator(str(temp_tac_file))

# --- Test Cases ---

def test_tac_generator_init(tac_generator, tmp_path):
    """Test basic initialization of TACGenerator."""
    assert tac_generator.output_filename == str(tmp_path / "test_output.tac")
    assert tac_generator.tac_lines == []
    assert tac_generator.temp_counter == 0
    assert tac_generator.start_proc_name is None

def test_emit(tac_generator):
    """Test the emit method adds lines correctly."""
    tac_generator.emit("line 1")
    tac_generator.emit("line 2")
    assert tac_generator.tac_lines == ["line 1", "line 2"]

def test_newTemp(tac_generator):
    """Test temporary variable generation."""
    assert tac_generator.newTemp() == "_t1"
    assert tac_generator.temp_counter == 1
    assert tac_generator.newTemp() == "_t2"
    assert tac_generator.temp_counter == 2

def test_emitProcStart_resets_temp(tac_generator):
    """Test that emitProcStart resets the temporary counter."""
    tac_generator.newTemp() # _t1
    tac_generator.newTemp() # _t2
    assert tac_generator.temp_counter == 2
    tac_generator.emitProcStart("MyProc")
    assert tac_generator.temp_counter == 0
    assert tac_generator.newTemp() == "_t1" # Should restart from _t1
    assert tac_generator.tac_lines == ["proc MyProc"] # Check emitProcStart output

def test_emitProcEnd(tac_generator):
    """Test emitProcEnd output."""
    tac_generator.emitProcEnd("MyProc")
    assert tac_generator.tac_lines == ["endp MyProc"]

def test_getPlace_literals(tac_generator):
    """Test getPlace for literal values."""
    assert tac_generator.getPlace(123) == "123"
    assert tac_generator.getPlace(45.6) == "45.6"
    # Add tests for other literals like strings or booleans if supported/needed

def test_getPlace_symbols(tac_generator, dummy_token):
    """Test getPlace for various Symbol objects based on plan."""
    # Global Variable (Depth 1)
    global_var = Symbol(name="GVAR", token=dummy_token, entry_type=EntryType.VARIABLE, depth=1)
    assert tac_generator.getPlace(global_var) == "GVAR"

    # Global Constant (Depth 1)
    global_const = Symbol(name="MAX", token=dummy_token, entry_type=EntryType.CONSTANT, depth=1)
    global_const.set_constant_info(VarType.INT, 99)
    assert tac_generator.getPlace(global_const) == "99"

    # Local Variable (Depth 2, Offset -4)
    local_var = Symbol(name="LVAR", token=dummy_token, entry_type=EntryType.VARIABLE, depth=2)
    local_var.set_variable_info(VarType.INT, offset=-4, size=2)
    assert tac_generator.getPlace(local_var) == "_BP-4"

    # Parameter (Depth 2, Offset +6)
    param_var = Symbol(name="PVAR", token=dummy_token, entry_type=EntryType.PARAMETER, depth=2)
    # Parameters often use set_variable_info for offset/size in this structure
    param_var.set_variable_info(VarType.INT, offset=6, size=2)
    assert tac_generator.getPlace(param_var) == "_BP+6"

    # Parameter (Depth 3, Offset +0 - less common, but possible)
    param_zero = Symbol(name="PZERO", token=dummy_token, entry_type=EntryType.PARAMETER, depth=3)
    param_zero.set_variable_info(VarType.INT, offset=0, size=2)
    assert tac_generator.getPlace(param_zero) == "_BP+0"

def test_getPlace_string_inputs(tac_generator):
    """Test getPlace for string inputs (temps, BP formats, potential globals)."""
    assert tac_generator.getPlace("_t5") == "_t5"
    assert tac_generator.getPlace("_BP-10") == "_BP-10"
    assert tac_generator.getPlace("_BP+4") == "_BP+4"
    # Assumes strings not matching patterns are treated as potential globals
    assert tac_generator.getPlace("SomeGlobalOrTypo") == "SomeGlobalOrTypo"

def test_getPlace_error_cases(tac_generator, dummy_token):
    """Test getPlace error handling for symbols."""
    # Local/Param without offset
    bad_local = Symbol(name="NoOffset", token=dummy_token, entry_type=EntryType.VARIABLE, depth=2)
    # bad_local.offset = None # Default is None
    assert "ERROR_NO_OFFSET" in tac_generator.getPlace(bad_local)

    # Symbol with unexpected depth 0
    bad_depth = Symbol(name="BadDepth", token=dummy_token, entry_type=EntryType.VARIABLE, depth=0)
    assert "ERROR_BAD_SYMBOL_DEPTH" in tac_generator.getPlace(bad_depth)

    # Constant symbol without a value set
    bad_const = Symbol(name="NoValueConst", token=dummy_token, entry_type=EntryType.CONSTANT, depth=1)
    with pytest.raises(ValueError, match="has no value"):
        tac_generator.getPlace(bad_const)

    # Passing something completely unexpected
    assert "ERROR_UNKNOWN_PLACE_TYPE" in tac_generator.getPlace(object()) # Pass a generic object

def test_emitProgramStart(tac_generator):
    """Test storing the start procedure name."""
    assert tac_generator.start_proc_name is None
    tac_generator.emitProgramStart("MainProc")
    assert tac_generator.start_proc_name == "MainProc"

def test_writeOutput_success(tac_generator, tmp_path):
    """Test writing the TAC file successfully."""
    output_file = tmp_path / "test_output.tac"
    tac_generator.emitProgramStart("MainProc")
    tac_generator.emitProcStart("MainProc")
    tac_generator.emit("instr 1")
    tac_generator.emit("instr 2")
    tac_generator.emitProcEnd("MainProc")
    tac_generator.writeOutput()

    assert output_file.exists()
    with open(output_file, 'r') as f:
        content = f.readlines()

    expected_content = [
        "start MainProc\n",
        "proc MainProc\n",
        "instr 1\n",
        "instr 2\n",
        "endp MainProc\n"
    ]
    assert content == expected_content

def test_writeOutput_no_start_proc(tac_generator):
    """Test that writeOutput fails if start procedure name is not set."""
    tac_generator.emit("some instruction")
    with pytest.raises(RuntimeError, match="Start procedure name was not set"):
        tac_generator.writeOutput()

# --- Placeholder Tests for Operations (to be expanded later) ---

def test_emitBinaryOp_placeholder(tac_generator):
    """Basic test for emitBinaryOp placeholder."""
    tac_generator.emitBinaryOp("ADD", "_t1", "A", "_BP-2")
    assert tac_generator.tac_lines == ["_t1 = A ADD _BP-2"]

def test_emitUnaryOp_placeholder(tac_generator):
    """Basic test for emitUnaryOp placeholder."""
    tac_generator.emitUnaryOp("UMINUS", "_t2", "_BP+4")
    assert tac_generator.tac_lines == ["_t2 = UMINUS _BP+4"]

def test_emitAssignment_placeholder(tac_generator):
    """Basic test for emitAssignment placeholder."""
    tac_generator.emitAssignment("_BP-6", "5")
    assert tac_generator.tac_lines == ["_BP-6 = 5"]

def test_emitPush_placeholder(tac_generator):
    """Basic test for emitPush placeholder (assumes default 'push')."""
    # Need ParameterMode.IN for proper test later
    tac_generator.emitPush("A", None) # Pass None for mode for now
    assert tac_generator.tac_lines == ["push A"]

def test_emitCall_placeholder(tac_generator):
    """Basic test for emitCall placeholder."""
    tac_generator.emitCall("MySub")
    assert tac_generator.tac_lines == ["call MySub"] 