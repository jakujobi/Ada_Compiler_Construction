# Ada_Compiler_Construction/tests/unit_tests/test_rdparser_a7.py

import pytest
import unittest
import sys
from pathlib import Path
import logging # Need logging module for levels

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Modules to test/mock
try:
    from jakadac.modules.LexicalAnalyzer import LexicalAnalyzer  # type: ignore
    from jakadac.modules.Definitions import Definitions  # type: ignore
    from jakadac.modules.SymTable import SymbolTable, Symbol, EntryType, VarType, ParameterMode  # type: ignore
    from jakadac.modules.TACGenerator import TACGenerator  # type: ignore
    from jakadac.modules.RDParserA7 import RDParserA7  # type: ignore
    from jakadac.modules.Logger import Logger  # type: ignore
except ImportError as e:
    # Skip entire module if essential imports are missing
    raise unittest.SkipTest(f"Skipping RDParserA7 tests due to import error: {e}")

# --- Fixtures ---

@pytest.fixture(scope="module")
def defs():
    """Provides a Definitions instance."""
    # LexicalAnalyzer likely creates its own Definitions
    lex = LexicalAnalyzer()
    return lex.defs

@pytest.fixture
def dummy_logger():
     # Configure logger not to output during tests unless debugging tests themselves
     # Use a valid logging level like CRITICAL to minimize output
     return Logger(log_level_console=logging.CRITICAL)

@pytest.fixture
def tac_generator(tmp_path, dummy_logger):
    """Provides a TACGenerator instance writing to a temporary file."""
    # Give TACGenerator the dummy logger too
    # TACGenerator itself doesn't impact offset calculation, but RDParserA7 requires it
    temp_tac_file = tmp_path / "test_a7_output.tac"
    gen = TACGenerator(str(temp_tac_file))
    # Inject logger if TACGenerator uses it (assuming it might)
    # gen.logger = dummy_logger # If TACGenerator has a logger attribute
    return gen

# Helper function to parse a snippet and return parser/symtab
def parse_snippet(ada_code: str, defs, tac_generator, dummy_logger):
    # Instantiate the lexical analyzer with provided definitions and inject dummy logger
    lex = LexicalAnalyzer(stop_on_error=False, defs=defs)
    lex.logger = dummy_logger
    tokens = lex.analyze(ada_code)
    symtab = SymbolTable()
    # Inject logger into SymTable if it uses the shared one directly
    # symtab.logger = dummy_logger
    parser = RDParserA7(
        tokens=tokens,
        defs=defs,
        symbol_table=symtab,
        tac_generator=tac_generator,
        stop_on_error=True, # Fail fast for syntax errors
        panic_mode_recover=False,
        build_parse_tree=False # Not needed for offset testing
    )
    # Inject logger into parser
    parser.logger = dummy_logger
    success = parser.parse()
    return parser, symtab, success

# --- Offset Test Cases ---

def test_local_offset_no_locals(defs, tac_generator, dummy_logger):
    """Test procedure with no local variables."""
    ada_code = """
    procedure NoLocals is
    begin
        null;
    end NoLocals;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors
    proc_symbol = symtab.lookup("NoLocals", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.local_size == 0

def test_local_offset_single_int(defs, tac_generator, dummy_logger):
    """Test procedure with a single integer local."""
    ada_code = """
    procedure SingleInt is
        X : INTEGER;
    begin
        null;
    end SingleInt;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors
    proc_symbol = symtab.lookup("SingleInt", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.local_size == 2 # INTEGER size = 2
    # Lookup local var (need to know the scope it's in - depth 1 relative to global)
    # symtab.enter_scope() # Simulate parser entering scope? No, lookup should handle depth.
    local_x = symtab.lookup("X")
    assert local_x is not None
    assert local_x.offset == -2
    assert local_x.size == 2
    assert local_x.depth == 1 # Declared inside the procedure scope

def test_local_offset_multiple_mixed(defs, tac_generator, dummy_logger):
    """Test procedure with multiple locals of different types."""
    ada_code = """
    procedure MultiMixed is
        Count : INTEGER;
        Value : FLOAT;
        Flag  : BOOLEAN;
        Ch    : CHARACTER;
    begin
        null;
    end MultiMixed;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

    proc_symbol = symtab.lookup("MultiMixed", lookup_current_scope_only=True)
    assert proc_symbol is not None
    expected_total_size = 2 + 4 + 1 + 1 # INT + FLOAT + BOOL + CHAR
    assert proc_symbol.local_size == expected_total_size

    sym_count = symtab.lookup("Count")
    sym_value = symtab.lookup("Value")
    sym_flag = symtab.lookup("Flag")
    sym_ch = symtab.lookup("Ch")

    assert sym_count.offset == -2
    assert sym_count.size == 2
    assert sym_value.offset == -6 # -2 - 4
    assert sym_value.size == 4
    assert sym_flag.offset == -7 # -6 - 1
    assert sym_flag.size == 1
    assert sym_ch.offset == -8 # -7 - 1
    assert sym_ch.size == 1

def test_param_offset_no_params(defs, tac_generator, dummy_logger):
    """Test procedure with no parameters."""
    ada_code = """
    procedure NoParams () is
    begin
        null;
    end NoParams;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors
    proc_symbol = symtab.lookup("NoParams", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.param_size == 0
    assert proc_symbol.param_list == []
    assert proc_symbol.param_modes == {}

def test_param_offset_single_int_in(defs, tac_generator, dummy_logger):
    """Test procedure with a single IN INTEGER parameter."""
    ada_code = """
    procedure SingleParam ( A : in INTEGER ) is
    begin
        null;
    end SingleParam;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

    proc_symbol = symtab.lookup("SingleParam", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.param_size == 2 # INTEGER size
    assert proc_symbol.param_list is not None
    assert len(proc_symbol.param_list) == 1
    assert proc_symbol.param_modes == {"A": ParameterMode.IN}

    param_a = proc_symbol.param_list[0] # Stored in declaration order
    assert param_a.name == "A"
    assert param_a.offset == 4 # First (and only) param is at BP+4
    assert param_a.size == 2
    assert param_a.entry_type == EntryType.PARAMETER
    assert param_a.depth == 1 # Inside procedure scope

def test_param_offset_multiple_mixed_modes(defs, tac_generator, dummy_logger):
    """Test procedure with multiple parameters of different types and modes."""
    # Params: (Count : INTEGER; Value : out FLOAT; Flag : in out BOOLEAN)
    # Reverse order for offset: Flag (BP+4, sz 1), Value (BP+5, sz 4), Count (BP+9, sz 2)
    # Total Size = 1 + 4 + 2 = 7
    ada_code = """
    procedure MultiParam (
        Count : INTEGER;
        Value : out FLOAT;
        Flag  : in out BOOLEAN
    ) is
    begin
        null;
    end MultiParam;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

    proc_symbol = symtab.lookup("MultiParam", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.param_size == 7
    assert proc_symbol.param_list is not None
    assert len(proc_symbol.param_list) == 3
    assert proc_symbol.param_modes == {
        "Count": ParameterMode.IN, # Default is IN
        "Value": ParameterMode.OUT,
        "Flag": ParameterMode.INOUT
    }

    # Check symbols from param_list (declaration order)
    param_count = proc_symbol.param_list[0]
    param_value = proc_symbol.param_list[1]
    param_flag = proc_symbol.param_list[2]

    assert param_count.name == "Count"
    assert param_count.offset == 9
    assert param_count.size == 2

    assert param_value.name == "Value"
    assert param_value.offset == 5
    assert param_value.size == 4

    assert param_flag.name == "Flag"
    assert param_flag.offset == 4
    assert param_flag.size == 1

def test_combined_offsets(defs, tac_generator, dummy_logger):
    """Test procedure with both parameters and local variables."""
    # Params: (P1: INT at BP+6(sz=2), P2: BOOL at BP+4(sz=1)) -> ParamSize=3
    # Locals: (L1: FLT at BP-2(sz=4), L2: CHR at BP-6(sz=1)) -> LocalSize=5
    ada_code = """
    procedure Combined (
        P1 : INTEGER;
        P2 : in BOOLEAN -- Explicit IN mode
    ) is
        L1 : FLOAT;
        L2 : CHARACTER;
    begin
        null;
    end Combined;
    """
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

    proc_symbol = symtab.lookup("Combined", lookup_current_scope_only=True)
    assert proc_symbol is not None
    assert proc_symbol.param_size == 3 # 2 (P1) + 1 (P2)
    assert proc_symbol.local_size == 5 # 4 (L1) + 1 (L2)
    assert proc_symbol.param_list is not None
    assert len(proc_symbol.param_list) == 2
    assert proc_symbol.param_modes == {"P1": ParameterMode.IN, "P2": ParameterMode.IN}

    # Check params
    param_p1 = proc_symbol.param_list[0]
    param_p2 = proc_symbol.param_list[1]
    assert param_p1.name == "P1"
    assert param_p1.offset == 6 # P2(sz 1)@+4, P1(sz 2)@+5 -> ERROR, should be P2@+4, P1@+5
    # Corrected: P2(sz 1) starts at +4. Next offset is +4+1 = +5. P1(sz 2) starts at +5. param_size = 1+2=3
    # Let's retrace: Param list [P1, P2]. Reversed: [P2, P1].
    # P2: offset=4, size=1. next_offset=4+1=5.
    # P1: offset=5, size=2. next_offset=5+2=7.
    # Total size = 1+2 = 3. Looks correct.
    assert param_p1.offset == 5
    assert param_p1.size == 2
    assert param_p2.name == "P2"
    assert param_p2.offset == 4
    assert param_p2.size == 1

    # Check locals (need to lookup in symtab)
    local_l1 = symtab.lookup("L1")
    local_l2 = symtab.lookup("L2")
    assert local_l1.name == "L1"
    assert local_l1.offset == -2
    assert local_l1.size == 4
    assert local_l2.name == "L2"
    assert local_l2.offset == -3 # L1(sz 4)@-2. Next offset = -2-4 = -6.
    # Corrected: L1(sz 4)@ -2. next = -2-4 = -6. L2(sz 1)@ -6. local_size = 4+1 = 5.
    assert local_l2.offset == -6
    assert local_l2.size == 1

# --- Expanded Syntax & Semantic Tests from RDParserExtended ---

def test_empty_program(defs, tac_generator, dummy_logger):
    """Test minimal valid program structure."""
    ada_code = "procedure empty is begin null; end empty;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

def test_simple_assignment(defs, tac_generator, dummy_logger):
    """Test parsing a single assignment statement."""
    ada_code = "procedure assign_test is x : integer; begin x := 5; end assign_test;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors

def test_undeclared_variable_assignment(defs, tac_generator, dummy_logger):
    """Test semantic error for assignment to undeclared variable."""
    ada_code = "procedure undeclared is begin y := 10; end undeclared;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert len(parser.semantic_errors) == 1
    assert "Undeclared variable 'y'" in parser.semantic_errors[0]['message']

def test_undeclared_variable_factor(defs, tac_generator, dummy_logger):
    """Test semantic error for undeclared variable in expression factor."""
    ada_code = "procedure undeclared_expr is x : integer; begin x := z + 5; end undeclared_expr;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert len(parser.semantic_errors) == 1
    assert "Undeclared variable 'z'" in parser.semantic_errors[0]['message']

def test_procedure_name_mismatch(defs, tac_generator, dummy_logger):
    """Test error reporting for mismatched procedure end name."""
    ada_code = "procedure name_test is begin null; end different_name;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert not success
    assert len(parser.errors) == 1
    assert "Procedure name mismatch" in parser.errors[0]
    assert len(parser.semantic_errors) == 1
    assert "Procedure name mismatch" in parser.semantic_errors[0]['message']

def test_sequence_of_statements(defs, tac_generator, dummy_logger):
    """Test parsing multiple statements."""
    ada_code = "procedure multi is a, b, c : integer; begin a := 1; b := a + 2; c := a * b; end multi;"
    parser, symtab, success = parse_snippet(ada_code, defs, tac_generator, dummy_logger)
    assert success, f"Parsing failed. Errors: {parser.errors}, Sem Errors: {parser.semantic_errors}"
    assert not parser.errors
    assert not parser.semantic_errors 