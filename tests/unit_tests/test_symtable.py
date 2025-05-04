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
        symbol.set_procedure_info(param_list=[], param_modes={}, size_of_locals=10, size_of_params=0)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("do_something")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.entry_type, EntryType.PROCEDURE)
        self.assertEqual(found_symbol.param_list, [])
        self.assertEqual(found_symbol.size_of_locals, 10)
        self.assertEqual(found_symbol.size_of_params, 0)

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

    # --- A8 Specific Tests --- 

    def test_insert_parameter(self):
        """Test inserting a parameter symbol with the is_parameter flag."""
        token = create_dummy_token("param1")
        # Create as PARAMETER type
        symbol = Symbol("param1", token, EntryType.PARAMETER, depth=1)
        # Set variable info, explicitly marking as parameter
        symbol.set_variable_info(VarType.INT, offset=4, size=2, is_parameter=True)

        self.symtab.enter_scope() # Enter scope 1 for the parameter
        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("param1")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.entry_type, EntryType.PARAMETER)
        self.assertTrue(found_symbol.is_parameter)
        self.assertEqual(found_symbol.var_type, VarType.INT)
        self.assertEqual(found_symbol.offset, 4)
        self.assertEqual(found_symbol.size, 2)

    def test_insert_local_variable_not_parameter(self):
        """Test inserting a local variable symbol, ensuring is_parameter is False."""
        token = create_dummy_token("local_x")
        symbol = Symbol("local_x", token, EntryType.VARIABLE, depth=1)
        # is_parameter defaults to False or can be set explicitly
        symbol.set_variable_info(VarType.FLOAT, offset=-2, size=4, is_parameter=False)

        self.symtab.enter_scope() # Enter scope 1
        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("local_x")
        self.assertEqual(found_symbol, symbol)
        self.assertEqual(found_symbol.entry_type, EntryType.VARIABLE)
        self.assertFalse(found_symbol.is_parameter)
        self.assertEqual(found_symbol.var_type, VarType.FLOAT)
        self.assertEqual(found_symbol.offset, -2)

    def test_procedure_sizes(self):
        """Test storing and retrieving size_of_locals and size_of_params for procedures."""
        token = create_dummy_token("proc_with_sizes")
        symbol = Symbol("proc_with_sizes", token, EntryType.PROCEDURE, depth=0)
        # Simulate 4 bytes for params, 8 bytes for locals+temps
        symbol.set_procedure_info(param_list=[], param_modes={}, size_of_locals=8, size_of_params=4)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("proc_with_sizes")
        self.assertEqual(found_symbol.entry_type, EntryType.PROCEDURE)
        self.assertEqual(found_symbol.size_of_locals, 8)
        self.assertEqual(found_symbol.size_of_params, 4)

    def test_function_sizes(self):
        """Test storing and retrieving size_of_locals and size_of_params for functions."""
        token = create_dummy_token("func_with_sizes")
        symbol = Symbol("func_with_sizes", token, EntryType.FUNCTION, depth=0)
        # Simulate 2 bytes for params, 6 bytes for locals+temps
        symbol.set_function_info(return_type=VarType.INT, param_list=[], param_modes={}, size_of_locals=6, size_of_params=2)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("func_with_sizes")
        self.assertEqual(found_symbol.entry_type, EntryType.FUNCTION)
        self.assertEqual(found_symbol.return_type, VarType.INT)
        self.assertEqual(found_symbol.size_of_locals, 6)
        self.assertEqual(found_symbol.size_of_params, 2)

    def test_string_literal_storage(self):
        """Test inserting and retrieving a string literal symbol."""
        label_token = create_dummy_token("_S0") # Label used as name
        string_value = "Hello World!"
        symbol = Symbol("_S0", label_token, EntryType.STRING_LITERAL, depth=0) # Use specific type
        symbol.set_string_literal_info(string_value)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("_S0")
        self.assertEqual(found_symbol.entry_type, EntryType.STRING_LITERAL)
        self.assertEqual(found_symbol.var_type, VarType.STRING)
        self.assertEqual(found_symbol.const_value, "Hello World!$", "Should append $ terminator")
        self.assertIsNone(found_symbol.offset)
        self.assertIsNone(found_symbol.size)

    def test_string_literal_already_terminated(self):
        """Test inserting a string literal that already has the terminator."""
        label_token = create_dummy_token("_S1")
        string_value = "Another one$"
        symbol = Symbol("_S1", label_token, EntryType.STRING_LITERAL, depth=0)
        symbol.set_string_literal_info(string_value)

        self.symtab.insert(symbol)
        found_symbol = self.symtab.lookup("_S1")
        self.assertEqual(found_symbol.const_value, "Another one$", "Should not double append $")


if __name__ == '__main__':
    unittest.main() 