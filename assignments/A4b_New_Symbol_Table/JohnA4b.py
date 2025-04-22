#!/usr/bin/env python3
# JohnA4b.py
# Author: AI Assistant
# Date: 2025-03-14
# Version: 1.0
"""
Unit test driver for Assignment A4: SymbolTable.
This script exercises SymbolTable functionality:
- Inserting variables, constants, procedures
- Checking duplicate declarations
- Lookup success/failure
- Scope management (enter/exit, shadowing)
- Final table dumps
"""
import os
import sys

try:
    from jakadac.modules.Logger import Logger  # type: ignore
    from jakadac.modules.Token import Token  # type: ignore
    from jakadac.modules.SymTable import SymbolTable, Symbol, EntryType, VarType, DuplicateSymbolError, SymbolNotFoundError  # type: ignore
except ImportError:
    # Add 'src' folder to path so 'jakadac' package is discoverable
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_root = os.path.join(repo_root, "src")
    sys.path.append(src_root)
    from jakadac.modules.Logger import Logger  # type: ignore
    from jakadac.modules.Token import Token  # type: ignore
    from jakadac.modules.SymTable import *  # type: ignore

def main():
    print("=== SymbolTable Unit Tests ===")
    symtab = SymbolTable()
    print("Initial (global) scope:")
    print(symtab)

    # Test insertion of variable
    print("\n-- Insert variable 'a' at depth 0 --")
    t_a = Token(token_type=None, lexeme='a', line_number=1, column_number=1)
    sym_a = Symbol('a', t_a, EntryType.VARIABLE, symtab.current_depth)
    sym_a.set_variable_info(VarType.INT, offset=0, size=2)
    symtab.insert(sym_a)
    print(symtab)

    # Test insertion of constant
    print("\n-- Insert constant 'pi' at depth 0 --")
    t_pi = Token(token_type=None, lexeme='pi', line_number=2, column_number=1)
    sym_pi = Symbol('pi', t_pi, EntryType.CONSTANT, symtab.current_depth)
    sym_pi.set_constant_info(VarType.FLOAT, value=3.14)
    symtab.insert(sym_pi)
    print(symtab)

    # Duplicate insertion should fail
    print("\n-- Attempt duplicate insert of 'a' --")
    try:
        symtab.insert(sym_a)
    except DuplicateSymbolError as e:
        print(f"Caught expected DuplicateSymbolError: {e}")

    # Lookup existing
    print("\n-- Lookup 'a' and 'pi' --")
    try:
        print("Lookup 'a':", symtab.lookup('a'))
        print("Lookup 'pi':", symtab.lookup('pi'))
    except Exception as e:
        print("Unexpected lookup error:", e)

    # Lookup non-existent
    print("\n-- Lookup non-existent 'x' --")
    try:
        symtab.lookup('x')
    except SymbolNotFoundError as e:
        print(f"Caught expected SymbolNotFoundError: {e}")

    # Enter new scope and shadow 'a'
    print("\n-- Enter new scope and shadow 'a' --")
    symtab.enter_scope()
    t_a2 = Token(token_type=None, lexeme='a', line_number=3, column_number=1)
    sym_a2 = Symbol('a', t_a2, EntryType.VARIABLE, symtab.current_depth)
    sym_a2.set_variable_info(VarType.CHAR, offset=4, size=1)
    symtab.insert(sym_a2)
    print(symtab)
    # Lookup 'a' should find the inner one
    print("Lookup 'a' in inner scope:", symtab.lookup('a'))

    # Exit scope, lookup 'a' should find outer
    print("\n-- Exit inner scope --")
    symtab.exit_scope()
    print(symtab)
    print("Lookup 'a' after exit:", symtab.lookup('a'))

    # Nested scopes test
    print("\n-- Nested scopes test --")
    symtab.enter_scope()
    symtab.insert(Symbol('b', Token(None,'b',4,1), EntryType.VARIABLE, symtab.current_depth))
    symtab.enter_scope()
    symtab.insert(Symbol('c', Token(None,'c',5,1), EntryType.VARIABLE, symtab.current_depth))
    print(symtab)
    symtab.exit_scope()
    print("After exiting one scope:")
    print(symtab)
    symtab.exit_scope()
    print("Back to global:")
    print(symtab)

    print("\nAll tests completed.")


if __name__ == '__main__':
    main()
