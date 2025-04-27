import unittest
import os
import sys
from pathlib import Path

# --- Adjust path to import modules from src ---
# Assuming the script is run from the root of the Ada_Compiler_Construction directory
# or that the src directory is in the Python path.
try:
    from jakadac.modules.SymTable import (
        SymbolTable, Symbol, EntryType, VarType, ParameterMode,
        SymbolNotFoundError, DuplicateSymbolError
    )
    # Use the actual Token class for creating test tokens
    from jakadac.modules.Token import Token
except ImportError:
    # Fallback for running directly from tests/unit_tests or if src isn't setup correctly
    repo_root = Path(__file__).resolve().parent.parent.parent # Go up 3 levels (unit_tests -> tests -> root)
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    from jakadac.modules.SymTable import (
        SymbolTable, Symbol, EntryType, VarType, ParameterMode,
        SymbolNotFoundError, DuplicateSymbolError
    )
    from jakadac.modules.Token import Token


# Helper to create dummy tokens for tests
def create_dummy_token(lexeme: str) -> Token:
    # Using jakadac.modules.Token constructor which needs type, lexeme, line, column
    # We can use dummy values for type, line, column as they aren't critical for SymTable logic
    return Token(token_type="DUMMY", lexeme=lexeme, line_number=1, column_number=1)

class TestSymbolTable(unittest.TestCase):

    def setUp(self):
        """Set up a new symbol table for each test."""
        self.symtab = SymbolTable()

    def test_initialization(self):
        """Test initial state of the symbol table."""
        self.assertEqual(self.symtab.current_depth, 0, "Initial depth should be 0")
        self.assertEqual(len(self.symtab._scope_stack), 1, "Should have one scope (global) on init")
        self.assertEqual(self.symtab.get_current_scope_symbols(), {}, "Global scope should be empty initially")

    def test_scope_management(self):
        """Test entering and exiting scopes."""
        self.assertEqual(self.symtab.current_depth, 0)
        self.symtab.enter_scope()
        self.assertEqual(self.symtab.current_depth, 1)
        self.assertEqual(len(self.symtab._scope_stack), 2)
        self.symtab.enter_scope()
        self.assertEqual(self.symtab.current_depth, 2)
        self.assertEqual(len(self.symtab._scope_stack), 3)
        self.symtab.exit_scope()
        self.assertEqual(self.symtab.current_depth, 1)
        self.assertEqual(len(self.symtab._scope_stack), 2)
        self.symtab.exit_scope()
        self.assertEqual(self.symtab.current_depth, 0)
        self.assertEqual(len(self.symtab._scope_stack), 1)
        # Test exiting below global scope (should log error, not crash)
        self.symtab.exit_scope()
        self.assertEqual(self.symtab.current_depth, -1) # Check internal state after safe exit
        # Re-enter to restore state for potential further tests if needed
        self.symtab.enter_scope()
        self.assertEqual(self.symtab.current_depth, 0)


    def test_insert_variable(self):
        """Test inserting a variable symbol."""
        token = create_dummy_token("my_var")
        symbol = Symbol("my_var", token, EntryType.VARIABLE, depth=0)
        symbol.set_variable_info(VarType.INT, offset=0, size=2)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("my_var")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.var_type, VarType.INT)
        self.assertEqual(found_symbol.offset, 0)
        self.assertEqual(found_symbol.size, 2)

    def test_insert_constant(self):
        """Test inserting a constant symbol."""
        token = create_dummy_token("MAX_VALUE")
        symbol = Symbol("MAX_VALUE", token, EntryType.CONSTANT, depth=0)
        symbol.set_constant_info(VarType.INT, value=100)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("MAX_VALUE")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.var_type, VarType.INT)
        self.assertEqual(found_symbol.const_value, 100)

    def test_insert_procedure(self):
        """Test inserting a procedure symbol."""
        token = create_dummy_token("do_something")
        symbol = Symbol("do_something", token, EntryType.PROCEDURE, depth=0)
        symbol.set_procedure_info(param_list=[], param_modes={}, local_size=10)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("do_something")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.entry_type, EntryType.PROCEDURE)
        self.assertEqual(found_symbol.param_list, [])
        self.assertEqual(found_symbol.local_size, 10)

    def test_lookup_not_found(self):
        """Test lookup for a symbol that doesn't exist."""
        with self.assertRaises(SymbolNotFoundError):
            self.symtab.lookup("non_existent_symbol")

    def test_lookup_in_outer_scope(self):
        """Test finding a symbol declared in an outer scope."""
        global_token = create_dummy_token("global_val")
        global_symbol = Symbol("global_val", global_token, EntryType.VARIABLE, depth=0)
        self.symtab.insert(global_symbol)

        self.symtab.enter_scope() # Enter depth 1
        found_symbol = self.symtab.lookup("global_val")
        self.assertEqual(found_symbol, global_symbol)
        self.assertEqual(found_symbol.depth, 0)

    def test_lookup_shadowing(self):
        """Test that lookup finds the innermost symbol (shadowing)."""
        token0 = create_dummy_token("x")
        symbol0 = Symbol("x", token0, EntryType.VARIABLE, depth=0)
        symbol0.set_variable_info(VarType.INT, 0, 2)
        self.symtab.insert(symbol0)

        self.symtab.enter_scope() # Enter depth 1
        token1 = create_dummy_token("x")
        symbol1 = Symbol("x", token1, EntryType.VARIABLE, depth=1)
        symbol1.set_variable_info(VarType.FLOAT, 4, 4) # Different type/offset
        self.symtab.insert(symbol1)

        found_symbol = self.symtab.lookup("x")
        self.assertEqual(found_symbol, symbol1, "Should find symbol from depth 1")
        self.assertEqual(found_symbol.depth, 1)
        self.assertEqual(found_symbol.var_type, VarType.FLOAT)

        # Test lookup restricted to current scope
        found_current = self.symtab.lookup("x", lookup_current_scope_only=True)
        self.assertEqual(found_current, symbol1)

        # Test restricted lookup in outer scope after exiting inner
        self.symtab.exit_scope() # Back to depth 0
        found_global_again = self.symtab.lookup("x")
        self.assertEqual(found_global_again, symbol0)
        found_current_global = self.symtab.lookup("x", lookup_current_scope_only=True)
        self.assertEqual(found_current_global, symbol0, "Lookup restricted to current scope (0) should find global symbol")

    def test_duplicate_symbol_in_same_scope(self):
        """Test inserting a duplicate symbol in the same scope raises error."""
        token1 = create_dummy_token("duplicate")
        symbol1 = Symbol("duplicate", token1, EntryType.VARIABLE, depth=0)
        self.symtab.insert(symbol1)

        token2 = create_dummy_token("duplicate")
        symbol2 = Symbol("duplicate", token2, EntryType.CONSTANT, depth=0) # Same name, same depth
        with self.assertRaises(DuplicateSymbolError) as cm:
            self.symtab.insert(symbol2)
        self.assertEqual(cm.exception.name, "duplicate")
        self.assertEqual(cm.exception.depth, 0)

    def test_duplicate_symbol_in_different_scopes(self):
        """Test inserting symbols with the same name in different scopes (shadowing is allowed)."""
        token1 = create_dummy_token("shadow")
        symbol1 = Symbol("shadow", token1, EntryType.VARIABLE, depth=0)
        self.symtab.insert(symbol1)

        self.symtab.enter_scope() # Enter depth 1
        token2 = create_dummy_token("shadow")
        symbol2 = Symbol("shadow", token2, EntryType.CONSTANT, depth=1) # Same name, different depth
        try:
            self.symtab.insert(symbol2) # This should succeed
        except DuplicateSymbolError:
            self.fail("DuplicateSymbolError raised unexpectedly for shadowing")

        found_inner = self.symtab.lookup("shadow")
        self.assertEqual(found_inner, symbol2)

    def test_get_current_scope_symbols(self):
        """Test retrieving symbols only from the current scope."""
        token_g = create_dummy_token("global_var")
        symbol_g = Symbol("global_var", token_g, EntryType.VARIABLE, depth=0)
        self.symtab.insert(symbol_g)

        self.symtab.enter_scope() # Depth 1
        token_l = create_dummy_token("local_var")
        symbol_l = Symbol("local_var", token_l, EntryType.VARIABLE, depth=1)
        self.symtab.insert(symbol_l)

        current_symbols = self.symtab.get_current_scope_symbols()
        self.assertEqual(len(current_symbols), 1)
        self.assertIn("local_var", current_symbols)
        self.assertNotIn("global_var", current_symbols)
        self.assertEqual(current_symbols["local_var"], symbol_l)

        self.symtab.exit_scope() # Back to depth 0
        current_symbols = self.symtab.get_current_scope_symbols()
        self.assertEqual(len(current_symbols), 1)
        self.assertIn("global_var", current_symbols)
        self.assertNotIn("local_var", current_symbols)


if __name__ == '__main__':
    unittest.main() 