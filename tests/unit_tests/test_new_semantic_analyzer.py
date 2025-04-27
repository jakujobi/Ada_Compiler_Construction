import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Optional, List

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Modules to test/mock
from jakadac.modules.NewSemanticAnalyzer import NewSemanticAnalyzer
from jakadac.modules.SymTable import (
    SymbolTable, Symbol, EntryType, VarType, ParameterMode,
    SymbolNotFoundError, DuplicateSymbolError
)
from jakadac.modules.Token import Token
# Need ParseTreeNode, which might be in RDParser or RDParserExtended
# Assuming RDParser for the base class
from jakadac.modules.RDParser import ParseTreeNode
from jakadac.modules.Definitions import Definitions
from jakadac.modules.Logger import Logger

# Create a dummy logger for tests
dummy_logger = Logger(log_level_console=None, log_level_file=None)

# Helper to create dummy tokens
def create_dummy_token(lexeme: str, token_type: str = "ID", line: int = 1, col: int = 1) -> Token:
    return Token(token_type=token_type, lexeme=lexeme, line_number=line, column_number=col)

# Helper to build simple mock parse trees
def build_mock_prog_node(proc_name: str, decls: Optional[List] = None, stmts: Optional[List] = None) -> ParseTreeNode:
    """Builds a mock ParseTreeNode for a simple procedure."""
    # Initialize to empty lists if None is passed
    if decls is None:
        decls = []
    if stmts is None:
        stmts = []
        
    prog_node = ParseTreeNode("Prog")
    # --- Procedure Header --- 
    # Simplified: just add the ID node directly
    proc_id_token = create_dummy_token(proc_name)
    proc_id_node = ParseTreeNode("ID", token=proc_id_token)
    # In reality, Prog has children like PROCEDURE, ID, Args, IS, etc.
    # For analyzer, we mainly need the ID and the structure containing decls/stmts.
    prog_node.add_child(proc_id_node) # Add ID node to find proc name

    # --- Declarative Part --- 
    decl_part_node = ParseTreeNode("DeclarativePart")
    if decls: # Now checks the initialized list
        for decl in decls:
            # decl should be a tuple: (name_list_node, type_mark_node)
            decl_wrapper_node = ParseTreeNode("Declaration") # Wrapper if needed
            decl_wrapper_node.add_child(decl[0]) # IdentifierList
            decl_wrapper_node.add_child(decl[1]) # TypeMark
            decl_part_node.add_child(decl_wrapper_node)
    else:
        # Add epsilon if no declarations, though analyzer might just skip if empty children
        decl_part_node.add_child(ParseTreeNode("ε"))
    prog_node.add_child(decl_part_node)

    # --- Procedures Part (simplified: assuming none for basic tests) ---
    procs_node = ParseTreeNode("Procedures")
    procs_node.add_child(ParseTreeNode("ε"))
    prog_node.add_child(procs_node)

    # --- Sequence of Statements --- 
    stmts_part_node = ParseTreeNode("SeqOfStatements")
    if stmts: # Now checks the initialized list
        for stmt_node in stmts:
            stmts_part_node.add_child(stmt_node)
    else:
        stmts_part_node.add_child(ParseTreeNode("ε")) # Or just empty
    prog_node.add_child(stmts_part_node)

    return prog_node

def build_identifier_list(names: list) -> ParseTreeNode:
    id_list_node = ParseTreeNode("IdentifierList")
    for name in names:
        token = create_dummy_token(name)
        id_node = ParseTreeNode("ID", token=token)
        id_list_node.add_child(id_node)
    return id_list_node

def build_type_mark(type_token_type: str, type_lexeme: str, is_const: bool = False, const_val_token: Token = None) -> ParseTreeNode:
    type_mark_node = ParseTreeNode("TypeMark")
    if is_const:
        const_kw_token = create_dummy_token("constant", "CONSTANT")
        const_kw_node = ParseTreeNode("CONSTANT", token=const_kw_token)
        type_mark_node.add_child(const_kw_node)
        # Add ASSIGN node? Analyzer structure might expect it.
        assign_token = create_dummy_token(":=", "ASSIGN")
        assign_node = ParseTreeNode("ASSIGN", token=assign_token)
        type_mark_node.add_child(assign_node)
        # Value node
        value_node = ParseTreeNode("Value")
        if const_val_token:
             # The child of Value is the actual literal node (NUM, REAL, etc.)
             literal_node = ParseTreeNode(const_val_token.token_type, token=const_val_token)
             value_node.add_child(literal_node)
        type_mark_node.add_child(value_node)
    else:
        type_token = create_dummy_token(type_lexeme, type_token_type)
        type_node = ParseTreeNode(type_token_type, token=type_token)
        type_mark_node.add_child(type_node)
    return type_mark_node

def build_assign_stat(var_name: str, expr_node: ParseTreeNode = None) -> ParseTreeNode:
    assign_node = ParseTreeNode("AssignStat")
    var_token = create_dummy_token(var_name)
    var_id_node = ParseTreeNode("ID", token=var_token)
    assign_op_node = ParseTreeNode("ASSIGN", token=create_dummy_token(":=", "ASSIGN"))

    assign_node.add_child(var_id_node)
    assign_node.add_child(assign_op_node)
    # Add a dummy expression node if none provided, otherwise analyzer might fail
    if expr_node is None:
        expr_node = ParseTreeNode("Expr") # Simplified expression
        num_token = create_dummy_token("0", "NUM")
        num_node = ParseTreeNode("NUM", token=num_token)
        factor = ParseTreeNode("Factor")
        factor.add_child(num_node)
        term = ParseTreeNode("Term")
        term.add_child(factor)
        simple_expr = ParseTreeNode("SimpleExpr")
        simple_expr.add_child(term)
        relation = ParseTreeNode("Relation")
        relation.add_child(simple_expr)
        expr_node.add_child(relation)

    assign_node.add_child(expr_node)
    return assign_node

class TestNewSemanticAnalyzer(unittest.TestCase):

    def setUp(self):
        self.defs = Definitions()
        self.symtab = SymbolTable()
        # Assign dummy logger to SymTable too, if it uses it directly
        self.symtab.logger = dummy_logger

    def test_analyze_simple_proc(self):
        """Test analysis inserts the procedure symbol correctly."""
        proc_name = "test_proc"
        root_node = build_mock_prog_node(proc_name)
        analyzer = NewSemanticAnalyzer(self.symtab, root_node, self.defs)
        analyzer.logger = dummy_logger # Suppress analyzer logs

        # Patch _dump_scope to avoid printing during tests
        with patch.object(analyzer, '_dump_scope') as mock_dump:
            sem_ok = analyzer.analyze()

        self.assertTrue(sem_ok)
        self.assertEqual(len(analyzer.errors), 0)
        # Check if procedure symbol was inserted at depth 0
        try:
            proc_symbol = self.symtab.lookup(proc_name, lookup_current_scope_only=True)
            self.assertEqual(proc_symbol.name, proc_name)
            self.assertEqual(proc_symbol.entry_type, EntryType.PROCEDURE)
            self.assertEqual(proc_symbol.depth, 0)
            # Check if dump was called (once for global scope at the end)
            self.assertEqual(mock_dump.call_count, 1)
            # Check if scope was exited correctly (back to -1 theoretically, but 0 after re-enter)
            # Note: Analyzer exits the proc scope, then BaseDriver exits global?
            # Let's check internal state if possible, or rely on side effects.
            self.assertEqual(self.symtab.current_depth, 0) # Should be back to global after analyze

        except SymbolNotFoundError:
            self.fail(f"Procedure symbol '{proc_name}' not found in global scope after analysis.")

    def test_analyze_variable_decl(self):
        """Test analysis inserts variable symbols with correct info."""
        proc_name = "var_decl_proc"
        var_names = ["count", "total"]
        id_list = build_identifier_list(var_names)
        type_mark = build_type_mark("INTEGERT", "integer")
        decls = [(id_list, type_mark)]
        root_node = build_mock_prog_node(proc_name, decls=decls)

        analyzer = NewSemanticAnalyzer(self.symtab, root_node, self.defs)
        analyzer.logger = dummy_logger
        with patch.object(analyzer, '_dump_scope') as mock_dump:
            sem_ok = analyzer.analyze()

        self.assertTrue(sem_ok)
        self.assertEqual(len(analyzer.errors), 0)

        # Check symbols INSIDE the procedure scope (analyzer enters scope)
        # We need to look up symbols assuming the analyzer handles scope correctly
        # Since analyze returns, we are back in global scope (depth 0).
        # We can't directly look up the locals unless we mock/modify lookup
        # OR we check the final symbol table dump contents if we captured it.
        # Alternative: Check the offsets were updated correctly within the analyzer
        # Let's assume the analyzer logs info we could capture or check internal state.

        # Check the *procedure's* symbol info (updated at the end of _visit_program)
        proc_symbol = self.symtab.lookup(proc_name)
        # Var size: INT = 2
        expected_local_size = len(var_names) * 2
        self.assertEqual(proc_symbol.local_size, expected_local_size)

        # Check dump scope calls (once for proc scope, once for global)
        # self.assertEqual(mock_dump.call_count, 2) # Depends on implementation details

    def test_analyze_constant_decl(self):
        """Test analysis inserts constant symbols."""
        proc_name = "const_decl_proc"
        const_name = ["LIMIT"]
        id_list = build_identifier_list(const_name)
        val_token = create_dummy_token("100", "NUM")
        val_token.value = 100 # Set the value lexer would find
        type_mark = build_type_mark("", "", is_const=True, const_val_token=val_token)
        decls = [(id_list, type_mark)]
        root_node = build_mock_prog_node(proc_name, decls=decls)

        analyzer = NewSemanticAnalyzer(self.symtab, root_node, self.defs)
        analyzer.logger = dummy_logger
        with patch.object(analyzer, '_dump_scope') as mock_dump:
            sem_ok = analyzer.analyze()

        self.assertTrue(sem_ok)
        self.assertEqual(len(analyzer.errors), 0)
        # We'd need to enter the scope manually or capture dump to check the const symbol

    def test_analyze_duplicate_decl(self):
        """Test analysis detects duplicate declarations in the same scope."""
        proc_name = "dup_decl_proc"
        var_names = ["val", "val"] # Duplicate name
        id_list = build_identifier_list(var_names)
        type_mark = build_type_mark("INTEGERT", "integer")
        decls = [(id_list, type_mark)]
        root_node = build_mock_prog_node(proc_name, decls=decls)

        analyzer = NewSemanticAnalyzer(self.symtab, root_node, self.defs)
        analyzer.logger = dummy_logger
        with patch.object(analyzer, '_dump_scope'):
             sem_ok = analyzer.analyze()

        self.assertFalse(sem_ok)
        self.assertEqual(len(analyzer.errors), 1)
        self.assertIn("Duplicate constant 'val'", analyzer.errors[0]) # Adjust msg based on exact error
        # Or Duplicate variable

    def test_analyze_undeclared_assign(self):
        """Test analysis detects undeclared identifier in assignment."""
        proc_name = "undecl_assign_proc"
        # Assign to 'x' which is not declared
        assign_stmt = build_assign_stat("x")
        stmts = [assign_stmt]
        root_node = build_mock_prog_node(proc_name, stmts=stmts)

        analyzer = NewSemanticAnalyzer(self.symtab, root_node, self.defs)
        analyzer.logger = dummy_logger
        with patch.object(analyzer, '_dump_scope'):
            sem_ok = analyzer.analyze()

        self.assertFalse(sem_ok)
        self.assertEqual(len(analyzer.errors), 1)
        self.assertIn("Undeclared identifier 'x' used in assignment", analyzer.errors[0])

    # Add tests for undeclared in expression factors
    # Add tests for nested procedures and scope resolution
    # Add tests for parameter handling

if __name__ == '__main__':
    unittest.main() 