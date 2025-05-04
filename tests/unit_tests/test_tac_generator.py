"""
Unit tests for the TACGenerator class.
"""
import pytest
from pathlib import Path
import sys
import os
import logging # Import logging for caplog checks
from enum import Enum # Import Enum
from typing import Optional

# Adjust path to import modules from the project root
# Go up three levels from test file (tests/unit_tests/ -> tests/ -> Ada_Compiler_Construction/)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
     sys.path.insert(0, str(project_root))
# Remove the old src_path addition if it exists (optional, but cleaner)
try:
    src_path_str = str(project_root / 'src')
    if src_path_str in sys.path:
        sys.path.remove(src_path_str)
except ValueError:
    pass # Not in list

# Direct Imports (assuming path adjustment works)
from src.jakadac.modules.TACGenerator import TACGenerator
from src.jakadac.modules.SymTable import Symbol, EntryType, ParameterMode, VarType
from src.jakadac.modules.Token import Token
from src.jakadac.modules.Definitions import Definitions # Import Definitions class

# Instantiate Definitions to access TokenType
defs = Definitions()
TokenType = defs.TokenType # Assign to variable for convenience if preferred, or use defs.TokenType directly

# --- Fixtures ---

@pytest.fixture
def tac_gen(tmp_path):
    """Provides a TACGenerator instance with a temporary output file path."""
    output_file = tmp_path / "test_output.tac"
    # Pass ParameterMode enum to the generator if needed, otherwise remove
    return TACGenerator(str(output_file))

@pytest.fixture
def dummy_token_instance():
     """Provides a default Token instance."""
     return Token(lexeme="dummy", token_type=TokenType.ID, line_number=1, column_number=1)

# Helper to create mock Symbols easily
def create_symbol(
    name="test_sym",
    token=None,
    entry_type=EntryType.VARIABLE,
    depth=1,
    var_type: Optional[VarType] = VarType.INT, # ALLOW Optional VarType, default still INT
    offset=None,
    const_value=None,
):
    """Creates a Symbol object for testing getPlace."""
    token = token or Token(lexeme=name, token_type=TokenType.ID, line_number=0, column_number=0)
    sym = Symbol(name=name, token=token, entry_type=entry_type, depth=depth)

    try:
        if entry_type == EntryType.CONSTANT:
             # Check if var_type is provided before calling set_constant_info
             # String constants might not have a VarType explicitly set
             if var_type is not None:
                 sym.set_constant_info(const_type=var_type, value=const_value)
             else: # Handle case like string literals where var_type might be None
                 sym.const_value = const_value
        elif entry_type in (EntryType.VARIABLE, EntryType.PARAMETER):
             # Ensure var_type is not None before proceeding
             if var_type is None:
                 # Default to INT if somehow None is passed for Var/Param
                 print(f"\nWarning: var_type is None for Var/Param symbol '{name}'. Defaulting to INT.", file=sys.stderr)
                 var_type = VarType.INT

             size = {VarType.INT: 2, VarType.FLOAT: 4, VarType.CHAR: 1, VarType.BOOLEAN: 1}.get(var_type, 2)
             current_offset = offset if offset is not None else 0
             sym.set_variable_info(var_type=var_type, offset=current_offset, size=size)
    except AttributeError as e:
         print(f"\nWarning: AttributeError calling set_info for symbol ({name}): {e}. Using direct assignment fallback.", file=sys.stderr)
         sym.var_type = var_type
         sym.offset = offset
         sym.const_value = const_value
    except TypeError as e:
        print(f"\nWarning: TypeError calling set_info for symbol ({name}): {e}. Using direct assignment fallback.", file=sys.stderr)
        sym.var_type = var_type
        sym.offset = offset
        sym.const_value = const_value

    return sym


# --- Test Class ---
class TestTACGenerator:

    def test_initialization(self, tac_gen, tmp_path):
        """Test the initial state of the TACGenerator."""
        assert tac_gen.output_filename == str(tmp_path / "test_output.tac")
        assert tac_gen.temp_counter == 0
        assert tac_gen.tac_lines == []
        assert tac_gen.start_proc_name is None
        assert hasattr(tac_gen, 'logger') and tac_gen.logger is not None
        assert hasattr(tac_gen, 'string_literals') and tac_gen.string_literals == {}
        assert hasattr(tac_gen, 'string_label_counter') and tac_gen.string_label_counter == 0

    def test_emit(self, tac_gen):
        """Test emitting single and multiple instruction tuples."""
        instr1 = ('=', '_t1', '5')
        instr2 = ('+', '_t2', '_t1', '1')
        instr_str = "comment should be stored as string"
        tac_gen.emit(instr1)
        assert tac_gen.tac_lines == [instr1]
        tac_gen.emit(instr2)
        assert tac_gen.tac_lines == [instr1, instr2]
        tac_gen.emit(instr_str)
        assert tac_gen.tac_lines == [instr1, instr2, instr_str]

    def test_newTemp(self, tac_gen):
        """Test the generation of sequential temporary names."""
        assert tac_gen.newTemp() == "_t1"
        assert tac_gen.temp_counter == 1
        assert tac_gen.newTemp() == "_t2"
        assert tac_gen.temp_counter == 2
        assert tac_gen.newTemp() == "_t3"
        assert tac_gen.temp_counter == 3

    # --- getPlace Tests (Keep existing ones, ensure they pass with new getPlace logic) ---
    def test_getPlace_temporary(self, tac_gen):
        """Test getPlace with a temporary variable name."""
        assert tac_gen.getPlace("_t10", 1) == "_t10" # Pass dummy depth

    def test_getPlace_integer_literal(self, tac_gen):
        """Test getPlace with an integer literal."""
        assert tac_gen.getPlace(123, 1) == "123"

    def test_getPlace_float_literal(self, tac_gen):
        """Test getPlace with a float literal."""
        assert tac_gen.getPlace(3.14, 1) == "3.14"
        assert tac_gen.getPlace(-0.5, 1) == "-0.5"

    def test_getPlace_constant_symbol_numeric(self, tac_gen):
        """Test getPlace with a numeric constant symbol."""
        sym = create_symbol(entry_type=EntryType.CONSTANT, const_value=42, var_type=VarType.INT)
        assert tac_gen.getPlace(sym, 1) == "42"
        sym_float = create_symbol(entry_type=EntryType.CONSTANT, const_value=9.81, var_type=VarType.FLOAT)
        assert tac_gen.getPlace(sym_float, 1) == "9.81"
        sym_none = create_symbol(entry_type=EntryType.CONSTANT, const_value=None, var_type=VarType.INT)
        assert tac_gen.getPlace(sym_none, 1) == sym.name # Fallback

    def test_getPlace_constant_symbol_string(self, tac_gen):
        """Test getPlace with a string literal constant symbol (uses label)."""
        sym = create_symbol(name="_S5", entry_type=EntryType.CONSTANT, const_value="hello$", var_type=None, depth=0)
        assert tac_gen.getPlace(sym, 1) == "_S5" # Expect label

    def test_getPlace_parameter_symbol_local(self, tac_gen):
        """Test getPlace with a parameter symbol local to current scope."""
        # Parameter declared at depth 1, current parse depth is 0 (proc head)
        # getPlace is called when parsing body (current depth 1)
        sym = create_symbol(name="param1", entry_type=EntryType.PARAMETER, depth=1, offset=4)
        assert tac_gen.getPlace(sym, current_proc_depth=0) == "_BP+4"

    def test_getPlace_variable_symbol_local(self, tac_gen):
        """Test getPlace with a local variable symbol."""
        # Variable declared at depth 1, current parse depth is 1
        sym = create_symbol(name="local1", entry_type=EntryType.VARIABLE, depth=1, offset=-2)
        assert tac_gen.getPlace(sym, current_proc_depth=0) == "_BP-2"
        sym_zero = create_symbol(name="local0", entry_type=EntryType.VARIABLE, depth=1, offset=0)
        assert tac_gen.getPlace(sym_zero, current_proc_depth=0) == "_BP+0" # Assuming _BP+0 format

    def test_getPlace_variable_symbol_enclosing(self, tac_gen):
        """Test getPlace with a variable from an enclosing scope."""
        # Variable declared at depth 0, current parse depth is 1
        sym = create_symbol(name="g_var", entry_type=EntryType.VARIABLE, depth=0, offset=None)
        assert tac_gen.getPlace(sym, current_proc_depth=1) == "g_var"
        # Variable declared at depth 1, current parse depth is 2
        sym2 = create_symbol(name="outer_local", entry_type=EntryType.VARIABLE, depth=1, offset=-4)
        assert tac_gen.getPlace(sym2, current_proc_depth=2) == "outer_local"

    def test_getPlace_symbol_no_offset_error(self, tac_gen, caplog):
        """Test getPlace fallback for Var/Param missing offset."""
        caplog.set_level(logging.ERROR)
        sym = Symbol("bad_var", dummy_token_instance(), EntryType.VARIABLE, 1) # No offset set
        assert tac_gen.getPlace(sym, current_proc_depth=0) == "bad_var"
        assert "Symbol 'bad_var' (Depth 1, Type EntryType.VARIABLE) has no offset defined" in caplog.text

    def test_getPlace_procedure_symbol(self, tac_gen):
        """Test getPlace with procedure/function symbols."""
        sym_proc = create_symbol(name="myProc", entry_type=EntryType.PROCEDURE, depth=0)
        assert tac_gen.getPlace(sym_proc, current_proc_depth=1) == "myProc"
        sym_func = create_symbol(name="myFunc", entry_type=EntryType.FUNCTION, depth=1)
        assert tac_gen.getPlace(sym_func, current_proc_depth=2) == "myFunc"

    def test_getPlace_bp_offset_string(self, tac_gen):
        """Test getPlace when input is already a BP offset string."""
        assert tac_gen.getPlace("_BP-8", current_proc_depth=1) == "_BP-8"
        assert tac_gen.getPlace("_BP+12", current_proc_depth=2) == "_BP+12"

    # --- emit* Method Tests (Updated for Tuple Format) ---
    def test_emitBinaryOp(self, tac_gen):
        tac_gen.emitBinaryOp("+", "_t1", "a", "b")
        assert tac_gen.tac_lines == [('+', '_t1', 'a', 'b')]
        tac_gen.emitBinaryOp("/", "_t2", "_t1", "2")
        assert tac_gen.tac_lines == [('+', '_t1', 'a', 'b'), ('/', '_t2', '_t1', '2')]

    def test_emitUnaryOp(self, tac_gen):
        tac_gen.emitUnaryOp("-", "_t2", "_t1") # Op is passed as second element for unary
        assert tac_gen.tac_lines == [('=', '_t2', '-', '_t1')]
        tac_gen.emitUnaryOp("not", "_t3", "flag")
        assert tac_gen.tac_lines == [('=', '_t2', '-', '_t1'), ('=', '_t3', 'not', 'flag')]

    def test_emitAssignment(self, tac_gen):
        tac_gen.emitAssignment("x", "_t3")
        assert tac_gen.tac_lines == [('=', 'x', '_t3')]
        tac_gen.emitAssignment("_BP-4", "5")
        assert tac_gen.tac_lines == [('=', 'x', '_t3'), ('=', '_BP-4', '5')]

    def test_emitProcStart(self, tac_gen):
        tac_gen.newTemp() # _t1
        tac_gen.newTemp() # _t2
        assert tac_gen.temp_counter == 2
        tac_gen.emitProcStart("myProc")
        assert tac_gen.tac_lines == [('proc', 'myProc')]
        assert tac_gen.temp_counter == 0 # Verify counter reset

    def test_emitProcEnd(self, tac_gen):
        tac_gen.emitProcEnd("myProc")
        assert tac_gen.tac_lines == [('endp', 'myProc')]

    def test_emitPush(self, tac_gen):
        """Test emitPush with different parameter modes."""
        # IN mode
        tac_gen.emitPush("var1", ParameterMode.IN)
        assert tac_gen.tac_lines == [('push', 'var1')]
        tac_gen.emitPush("_t5", ParameterMode.IN)
        assert tac_gen.tac_lines == [('push', 'var1'), ('push', '_t5')]
        # OUT mode
        tac_gen.emitPush("var2", ParameterMode.OUT)
        assert tac_gen.tac_lines == [('push', 'var1'), ('push', '_t5'), ('push', '@var2')]
        # INOUT mode
        tac_gen.emitPush("_BP-4", ParameterMode.INOUT)
        assert tac_gen.tac_lines == [('push', 'var1'), ('push', '_t5'), ('push', '@var2'), ('push', '@_BP-4')]

    def test_emitCall(self, tac_gen):
        tac_gen.emitCall("otherProc")
        assert tac_gen.tac_lines == [('call', 'otherProc')]

    # --- New I/O Test Methods ---
    def test_emitRead(self, tac_gen):
        tac_gen.emitRead("input_var")
        assert tac_gen.tac_lines == [('rdi', 'input_var')]
        tac_gen.emitRead("_BP-6")
        assert tac_gen.tac_lines == [('rdi', 'input_var'), ('rdi', '_BP-6')]

    def test_emitWrite(self, tac_gen):
        tac_gen.emitWrite("output_var")
        assert tac_gen.tac_lines == [('wri', 'output_var')]
        tac_gen.emitWrite("_t3")
        assert tac_gen.tac_lines == [('wri', 'output_var'), ('wri', '_t3')]
        tac_gen.emitWrite("42")
        assert tac_gen.tac_lines == [('wri', 'output_var'), ('wri', '_t3'), ('wri', '42')]

    def test_emitWriteString(self, tac_gen):
        tac_gen.emitWriteString("Hello World")
        assert tac_gen.tac_lines == [('wrs', '_S0')]
        assert tac_gen.string_literals == {"_S0": "Hello World$"}
        assert tac_gen.string_label_counter == 1

        tac_gen.emitWriteString("Another \"quoted\" string$") # Already has terminator
        assert tac_gen.tac_lines == [('wrs', '_S0'), ('wrs', '_S1')]
        assert tac_gen.string_literals == {"_S0": "Hello World$", "_S1": "Another \"quoted\" string$"}
        assert tac_gen.string_label_counter == 2

        tac_gen.emitWriteString("") # Empty string
        assert tac_gen.tac_lines == [('wrs', '_S0'), ('wrs', '_S1'), ('wrs', '_S2')]
        assert tac_gen.string_literals == {"_S0": "Hello World$", "_S1": "Another \"quoted\" string$", "_S2": "$"}
        assert tac_gen.string_label_counter == 3

    def test_emitNewLine(self, tac_gen):
        tac_gen.emitNewLine()
        assert tac_gen.tac_lines == [('wrln',)]
        tac_gen.emitNewLine()
        assert tac_gen.tac_lines == [('wrln',), ('wrln',)]

    def test_get_string_literals(self, tac_gen):
        assert tac_gen.get_string_literals() == {}
        tac_gen.emitWriteString("First")
        tac_gen.emitWriteString("Second")
        expected = {"_S0": "First$", "_S1": "Second$"}
        assert tac_gen.get_string_literals() == expected
        # Check that it returns a copy
        lit_map = tac_gen.get_string_literals()
        lit_map["_S0"] = "Changed"
        assert tac_gen.string_literals["_S0"] == "First$"
    # --- End New I/O Test Methods ---

    def test_emitProgramStart(self, tac_gen):
        """Test that emitProgramStart just records the name."""
        assert tac_gen.start_proc_name is None
        tac_gen.emitProgramStart("mainProc")
        assert tac_gen.start_proc_name == "mainProc"
        assert tac_gen.tac_lines == [] # Should not emit immediately

    # --- writeOutput Tests (Updated for Tuple Formatting) ---
    def test_writeOutput_basic(self, tac_gen, tmp_path):
        """Test writing basic TAC instructions, including START PROC."""
        tac_gen.emitProgramStart("proc1")
        tac_gen.emitProcStart("proc1")
        tac_gen.emitAssignment("a", "5")
        tac_gen.emitProcEnd("proc1")

        output_file = Path(tac_gen.output_filename)
        assert tac_gen.writeOutput() is True
        assert output_file.exists()
        content = output_file.read_text().strip().split('\n')
        assert content == [
            "proc proc1",
            "a = 5",
            "endp proc1",
            "START PROC proc1"
        ]

    def test_writeOutput_reordering(self, tac_gen, tmp_path):
        """Test that the main procedure instructions are placed first."""
        tac_gen.emitProgramStart("main") # Designate main

        # Inner proc first
        tac_gen.emitProcStart("inner")
        tac_gen.emitAssignment("i", "1")
        tac_gen.emitProcEnd("inner")

        # Main proc second (deferred)
        tac_gen.emitProcStart("main")
        tac_gen.emitAssignment("m", "0")
        tac_gen.emitCall("inner")
        tac_gen.emitProcEnd("main")

        output_file = Path(tac_gen.output_filename)
        assert tac_gen.writeOutput() is True
        content = output_file.read_text().strip().split('\n')
        # Expected: main instructions, then inner instructions, then START
        assert content == [
            "proc main",
            "m = 0",
            "call inner",
            "endp main",
            "proc inner",
            "i = 1",
            "endp inner",
            "START PROC main"
        ]

    def test_writeOutput_no_start_proc(self, tac_gen, tmp_path, caplog):
        """Test writing when no start procedure was designated."""
        caplog.set_level(logging.WARNING)
        tac_gen.emitProcStart("someProc")
        tac_gen.emitAssignment("x", "1")
        tac_gen.emitProcEnd("someProc")

        output_file = Path(tac_gen.output_filename)
        assert tac_gen.writeOutput() is True
        assert "No start procedure was designated" in caplog.text
        content = output_file.read_text().strip().split('\n')
        assert content == [
            "proc someProc",
            "x = 1",
            "endp someProc"
            # No START PROC line
        ]

    def test_writeOutput_empty(self, tac_gen, tmp_path):
        """Test writing when no instructions were generated."""
        output_file = Path(tac_gen.output_filename)
        assert tac_gen.writeOutput() is True
        assert output_file.exists()
        content = output_file.read_text().strip()
        assert content == "" # No START PROC if no main designated

    def test_writeOutput_creates_directory(self, tmp_path):
        """Test that writeOutput creates the directory if it doesn't exist."""
        deep_dir = tmp_path / "deep" / "nested"
        output_file = deep_dir / "output.tac"
        assert not deep_dir.exists()
        tac_gen = TACGenerator(str(output_file))
        tac_gen.emitProcStart("test")
        tac_gen.emitProcEnd("test")
        assert tac_gen.writeOutput() is True
        assert deep_dir.exists()
        assert output_file.exists()
        content = output_file.read_text().strip().split('\n')
        assert content == ["proc test", "endp test"]

# You might want to add tests for the _format_instruction helper directly
# or implicitly trust it via the writeOutput tests. 