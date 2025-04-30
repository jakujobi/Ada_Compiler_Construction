"""
Unit tests for the TACGenerator class.
"""
import pytest
from pathlib import Path
import sys
import os

# Adjust path to import modules from src
# Assuming tests are run from the project root (e.g., using 'pytest')
project_root = Path(__file__).parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Conditional import guard
try:
    from jakadac.modules.TACGenerator import TACGenerator
    from jakadac.modules.SymTable import Symbol, EntryType, ParameterMode, VarType
    # Dummy Token class for creating Symbols if Token module isn't needed directly
    class DummyToken:
        def __init__(self, lexeme="", line=0, col=0):
            self.lexeme = lexeme
            self.line_number = line
            self.column_number = col
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Ensure PYTHONPATH is set correctly or tests are run from the project root.")
    # Define dummy classes if import fails, so tests can be discovered/skipped
    class TACGenerator: pass
    class Symbol: pass
    class EntryType: pass
    class ParameterMode: pass
    class VarType: pass
    class DummyToken: pass


# --- Fixtures ---

@pytest.fixture
def tac_gen(tmp_path):
    """Provides a TACGenerator instance with a temporary output file path."""
    output_file = tmp_path / "test_output.tac"
    return TACGenerator(str(output_file))

@pytest.fixture
def dummy_token():
     """Provides a default DummyToken."""
     return DummyToken()

# Helper to create mock Symbols easily
def create_symbol(
    name="test_sym",
    token=None,
    entry_type=EntryType.VARIABLE,
    depth=1,
    var_type=VarType.INT, # Default type
    offset=None,
    const_value=None
):
    """Creates a Symbol object for testing getPlace."""
    token = token or DummyToken(lexeme=name)
    sym = Symbol(name=name, token=token, entry_type=entry_type, depth=depth)
    if entry_type == EntryType.CONSTANT:
        sym.set_constant_info(var_type, const_value)
    elif entry_type in (EntryType.VARIABLE, EntryType.PARAMETER):
        # set_variable_info requires size, calculate based on type or use default
        # This requires TypeUtils, which we might not want to import here.
        # For simplicity, let's assume a default size or handle it directly if needed.
        # Or, directly set offset/var_type if set_variable_info is too complex here.
        sym.var_type = var_type
        sym.offset = offset
        # sym.size = TypeUtils.get_type_size(var_type) # Requires TypeUtils
    # Handle other types if necessary
    return sym


# --- Test Class ---

class TestTACGenerator:

    def test_initialization(self, tac_gen, tmp_path):
        """Test the initial state of the TACGenerator."""
        assert tac_gen.output_filename == str(tmp_path / "test_output.tac")
        assert tac_gen.temp_counter == 0
        assert tac_gen.tac_lines == []
        assert tac_gen.start_proc_name is None
        assert tac_gen.logger is not None # Check logger exists

    def test_emit(self, tac_gen):
        """Test emitting single and multiple instructions."""
        instr1 = "_t1 = 5"
        instr2 = "_t2 = _t1 ADD 1"
        tac_gen.emit(instr1)
        assert tac_gen.tac_lines == [instr1]
        tac_gen.emit(instr2)
        assert tac_gen.tac_lines == [instr1, instr2]

    def test_newTemp(self, tac_gen):
        """Test the generation of sequential temporary names."""
        assert tac_gen.newTemp() == "_t1"
        assert tac_gen.temp_counter == 1
        assert tac_gen.newTemp() == "_t2"
        assert tac_gen.temp_counter == 2
        assert tac_gen.newTemp() == "_t3"
        assert tac_gen.temp_counter == 3

    # --- map_ada_op_to_tac Tests ---
    @pytest.mark.parametrize("ada_op, expected_tac_op", [
        ('+', 'ADD'), ('-', 'SUB'), ('*', 'MUL'), ('/', 'DIV'),
        ('div', 'IDIV'), ('mod', 'MOD'), ('rem', 'REM'),
        ('and', 'AND'), ('or', 'OR'), ('not', 'NOT'),
        ('=', 'EQ'), ('/=', 'NE'), ('<', 'LT'), ('>', 'GT'),
        ('<=', 'LE'), ('>=', 'GE'),
        # Case insensitivity for keywords
        ('MOD', 'MOD'), ('AnD', 'AND'),
        # Unknown operator fallback
        ('xor', 'xor'), ('**', '**')
    ])
    def test_map_ada_op_to_tac(self, tac_gen, ada_op, expected_tac_op):
        """Test mapping of various Ada operators to TAC operators."""
        assert tac_gen.map_ada_op_to_tac(ada_op) == expected_tac_op

    # --- getPlace Tests ---
    def test_getPlace_temporary(self, tac_gen):
        """Test getPlace with a temporary variable name."""
        assert tac_gen.getPlace("_t10") == "_t10"

    def test_getPlace_integer_literal(self, tac_gen):
        """Test getPlace with an integer literal."""
        assert tac_gen.getPlace(123) == "123"

    def test_getPlace_float_literal(self, tac_gen):
        """Test getPlace with a float literal."""
        assert tac_gen.getPlace(3.14) == "3.14"
        assert tac_gen.getPlace(-0.5) == "-0.5"

    def test_getPlace_constant_symbol(self, tac_gen):
        """Test getPlace with a constant symbol."""
        sym = create_symbol(entry_type=EntryType.CONSTANT, const_value=42)
        assert tac_gen.getPlace(sym) == "42"
        sym_float = create_symbol(entry_type=EntryType.CONSTANT, const_value=9.81)
        assert tac_gen.getPlace(sym_float) == "9.81"
        sym_none = create_symbol(entry_type=EntryType.CONSTANT, const_value=None) # Should this happen?
        # Behavior for constant None depends on implementation, assume name fallback
        assert tac_gen.getPlace(sym_none) == sym_none.name # Check fallback

    def test_getPlace_parameter_symbol(self, tac_gen):
        """Test getPlace with a parameter symbol (positive offset)."""
        sym = create_symbol(name="param1", entry_type=EntryType.PARAMETER, depth=1, offset=4)
        assert tac_gen.getPlace(sym) == "_BP+4"
        sym2 = create_symbol(name="param2", entry_type=EntryType.PARAMETER, depth=2, offset=12) # Depth shouldn't matter for offset calc itself
        assert tac_gen.getPlace(sym2) == "_BP+12"

    def test_getPlace_variable_symbol(self, tac_gen):
        """Test getPlace with a local variable symbol (negative offset)."""
        sym = create_symbol(name="local1", entry_type=EntryType.VARIABLE, depth=1, offset=-2)
        assert tac_gen.getPlace(sym) == "_BP-2"
        sym_zero = create_symbol(name="local0", entry_type=EntryType.VARIABLE, depth=1, offset=0) # Edge case
        assert tac_gen.getPlace(sym_zero) == "_BP-0"
        sym_large = create_symbol(name="local_large", entry_type=EntryType.VARIABLE, depth=3, offset=-100)
        assert tac_gen.getPlace(sym_large) == "_BP-100"

    def test_getPlace_symbol_no_offset(self, tac_gen, caplog):
        """Test getPlace when a symbol (Var/Param > depth 0) has no offset."""
        sym = create_symbol(name="local_no_off", entry_type=EntryType.VARIABLE, depth=1, offset=None)
        assert tac_gen.getPlace(sym) == "local_no_off" # Fallback to name
        assert "has no offset defined" in caplog.text # Check for error log

    def test_getPlace_symbol_unhandled_type_with_offset(self, tac_gen, caplog):
        """Test getPlace with a non-Var/Param symbol that has an offset."""
        # e.g., a TYPE symbol somehow got an offset
        sym = create_symbol(name="my_type", entry_type=EntryType.TYPE, depth=1, offset=-8)
        assert tac_gen.getPlace(sym) == "my_type" # Fallback to name
        assert "has offset but is not PARAMETER or VARIABLE" in caplog.text # Check for warning log

    def test_getPlace_symbol_global_depth(self, tac_gen):
        """Test getPlace for a symbol at depth 0 (assuming name is used)."""
        sym_var = create_symbol(name="g_var", entry_type=EntryType.VARIABLE, depth=0, offset=None) # Globals might not use BP offsets
        assert tac_gen.getPlace(sym_var) == "g_var"
        sym_proc = create_symbol(name="g_proc", entry_type=EntryType.PROCEDURE, depth=0, offset=None)
        assert tac_gen.getPlace(sym_proc) == "g_proc"

    def test_getPlace_unexpected_type(self, tac_gen, caplog):
        """Test getPlace with an unexpected input type."""
        unexpected = [1, 2, 3]
        assert tac_gen.getPlace(unexpected) == str(unexpected)
        assert "Unknown type encountered in getPlace" in caplog.text

    # --- emit* Method Tests ---
    def test_emitBinaryOp(self, tac_gen):
        tac_gen.emitBinaryOp("ADD", "_t1", "a", "b")
        assert tac_gen.tac_lines == ["_t1 = a ADD b"]

    def test_emitUnaryOp(self, tac_gen):
        tac_gen.emitUnaryOp("UMINUS", "_t2", "_t1")
        assert tac_gen.tac_lines == ["_t2 = UMINUS _t1"]
        tac_gen.emitUnaryOp("NOT", "_t3", "flag")
        assert tac_gen.tac_lines == ["_t2 = UMINUS _t1", "_t3 = NOT flag"]

    def test_emitAssignment(self, tac_gen):
        tac_gen.emitAssignment("x", "_t3")
        assert tac_gen.tac_lines == ["x = _t3"]
        tac_gen.emitAssignment("_BP-4", "5") # Assign literal to local
        assert tac_gen.tac_lines == ["x = _t3", "_BP-4 = 5"]

    def test_emitProcStart(self, tac_gen):
        tac_gen.newTemp() # _t1
        tac_gen.newTemp() # _t2
        assert tac_gen.temp_counter == 2
        tac_gen.emitProcStart("myProc")
        assert tac_gen.tac_lines == ["proc myProc"]
        assert tac_gen.temp_counter == 0 # Verify counter reset

    def test_emitProcEnd(self, tac_gen):
        tac_gen.emitProcEnd("myProc")
        assert tac_gen.tac_lines == ["endp myProc"]

    def test_emitPush(self, tac_gen):
        tac_gen.emitPush("arg1", ParameterMode.IN)
        assert tac_gen.tac_lines == ["push arg1"]
        tac_gen.emitPush("_t5", ParameterMode.OUT)
        assert tac_gen.tac_lines == ["push arg1", "push @_t5"]
        tac_gen.emitPush("_BP-8", ParameterMode.INOUT)
        assert tac_gen.tac_lines == ["push arg1", "push @_t5", "push @_BP-8"]

    def test_emitCall(self, tac_gen):
        tac_gen.emitCall("anotherProc")
        assert tac_gen.tac_lines == ["call anotherProc"]

    def test_emitProgramStart(self, tac_gen):
        assert tac_gen.start_proc_name is None
        tac_gen.emitProgramStart("main")
        assert tac_gen.start_proc_name == "main"

    # --- writeOutput Tests ---
    def test_writeOutput_basic(self, tac_gen, tmp_path):
        """Test writing basic TAC lines and start directive."""
        out_file = Path(tac_gen.output_filename)
        tac_gen.emit("_t1 = 5")
        tac_gen.emit("_t2 = _t1 ADD 1")
        tac_gen.emitProgramStart("main_proc")
        assert tac_gen.writeOutput() is True
        assert out_file.exists()
        content = out_file.read_text().strip().split('\n')
        assert content == [
            "_t1 = 5",
            "_t2 = _t1 ADD 1",
            "start main_proc"
        ]

    def test_writeOutput_no_start_proc(self, tac_gen, tmp_path, caplog):
        """Test writing when start procedure name wasn't set."""
        out_file = Path(tac_gen.output_filename)
        tac_gen.emit("x = y")
        # tac_gen.emitProgramStart("main_proc") # Intentionally omitted
        assert tac_gen.writeOutput() is True # Should still write file
        assert "No start procedure name was recorded" in caplog.text
        assert out_file.exists()
        content = out_file.read_text().strip().split('\n')
        assert content == ["x = y"] # No start directive

    def test_writeOutput_empty(self, tac_gen, tmp_path):
        """Test writing when no TAC lines were emitted."""
        out_file = Path(tac_gen.output_filename)
        tac_gen.emitProgramStart("empty_main")
        assert tac_gen.writeOutput() is True
        assert out_file.exists()
        content = out_file.read_text().strip().split('\n')
        # Should only contain the start directive
        assert content == ["start empty_main"]

    def test_writeOutput_creates_directory(self, tmp_path):
        """Test if writeOutput creates the parent directory if it doesn't exist."""
        output_dir = tmp_path / "sub" / "dir"
        output_file = output_dir / "output.tac"
        # Ensure directory does not exist initially
        assert not output_dir.exists()
        gen = TACGenerator(str(output_file))
        gen.emit("_t1 = 0")
        gen.emitProgramStart("proc_in_subdir")
        assert gen.writeOutput() is True
        assert output_file.exists()
        content = output_file.read_text().strip().split('\n')
        assert content == ["_t1 = 0", "start proc_in_subdir"]
        assert output_dir.is_dir() # Check directory was created 