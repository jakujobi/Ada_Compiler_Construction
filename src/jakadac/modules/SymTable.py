#!/usr/bin/env python3
# SymTable.py
# Author: John Akujobi (Refactored by AI Assistant)
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-03-14 (Refactored Date)
# Version: 2.0
"""
Improved Symbol Table Implementation for the Ada Compiler.

This module provides a robust symbol table implementation utilizing a stack of
scopes (dictionaries) to manage symbols according to lexical scoping rules.

Key Features:
- Scope Management: Uses a stack to handle nested scopes (`enter_scope`, `exit_scope`).
- Efficient Lookups: Leverages Python dictionaries for efficient access within scopes.
- Clear Symbol Representation: Uses a dedicated `Symbol` class.
- Integration: Designed to work with `Token` and `logger` modules.
- Error Handling: Uses custom exceptions for specific error conditions.

Classes:
- VarType: Enumeration for variable/constant/parameter types.
- EntryType: Enumeration for symbol types (VARIABLE, CONSTANT, PROCEDURE).
- ParameterMode: Enumeration for procedure parameter modes.
- Symbol: Represents an entry in the symbol table.
- SymbolNotFoundError: Exception for failed lookups.
- DuplicateSymbolError: Exception for attempting to redeclare a symbol in the same scope.
- SymbolTable: The main class managing scopes and symbols.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

# Always import the shared logger instance
from .Logger import logger

# Always import the shared Token class
from .Token import Token

# Remove the fallback definition of Token class
# try:
#     # Import Token (shared); ignore type mismatches
#     from .Token import Token  # type: ignore
# except ImportError:
#     # Define a dummy Token for standalone testing if needed
#     class Token:
#         def __init__(self, token_type, lexeme, line_number, column_number,
#                     value=None, real_value=None, literal_value=None):
#             """
#             Initialize a Token instance.
#
#             Parameters:
#                 token_type: The type of the token (usually from the TokenType enumeration).
#                 lexeme (str): The actual text matched from the source code.
#                 line_number (int): The line number in the source code where this token appears.
#                 column_number (int): The column number in the source code where this token starts.
#                 value: (Optional) The numeric value if this is an integer token.
#                 real_value: (Optional) The floating-point value if this is a real number token.
#                 literal_value: (Optional) The inner text for string or character literals.
#             """
#             self.token_type = token_type
#             self.lexeme = lexeme
#             self.line_number = line_number
#             self.column_number = column_number
#             self.value = value
#             self.real_value = real_value
#             self.literal_value = literal_value
#
#         def __repr__(self):
#             """
#             Return an official string representation of the Token.
#
#             This is useful for debugging. It shows the token type, lexeme, value,
#             and the location (line and column) where it was found.
#             """
#             try:
#                 return (f"Token(type={self.token_type}, lexeme='{self.lexeme}', "
#                         f"value={self.value}, line={self.line_number}, "
#                         f"column={self.column_number})")
#             except Exception:
#                 # If an error occurs during representation, log it and re-raise.
#                 logger.error('Error in Token __repr__: %s', self.__dict__)
#                 raise
#
#         def __str__(self):
#             """
#             Return a user-friendly string representation of the Token.
#
#             For example: <ID, 'myVariable'>
#             """
#             # Note: There's a small typo in the attribute name ("self. Lexeme" with a space).
#             # It should be "self.lexeme".
#             return f"<{self.token_type}, {self.lexeme}>"

# --- Enumerations ---
class VarType(Enum):
    """Enumeration for variable, constant, and parameter data types."""
    CHAR = auto()
    INT = auto()
    FLOAT = auto()
    REAL = auto() # Alias for FLOAT
    BOOLEAN = auto() # Added Boolean type
    # Add other Ada types as needed (e.g., STRING, ARRAY, RECORD)

class EntryType(Enum):
    """Enumeration for the kind of symbol being stored."""
    VARIABLE = auto()
    CONSTANT = auto()
    PROCEDURE = auto()
    FUNCTION = auto() # Distinguish procedures from functions
    TYPE = auto() # For user-defined types
    PARAMETER = auto() # Explicitly mark parameters

class ParameterMode(Enum):
    """Enumeration for parameter passing modes."""
    IN = auto()
    OUT = auto()
    INOUT = auto()

# --- Symbol Definition ---
class Symbol:
    """Represents a single entry (symbol) in the symbol table."""
    def __init__(self, name: str, token: Token, entry_type: EntryType, depth: int):
        """
        Initialize a new Symbol.

        Args:
            name: The identifier (lexeme) of the symbol.
            token: The token associated with the symbol's declaration.
            entry_type: The kind of symbol (VARIABLE, PROCEDURE, etc.).
            depth: The lexical scope depth where this symbol is declared.
        """
        self.name: str = name
        self.token: Token = token # Store the original token for error reporting
        self.entry_type: EntryType = entry_type
        self.depth: int = depth

        # Attributes specific to the entry type (initialize to None)
        self.var_type: Optional[VarType] = None # Data type for VAR, CONST, PARAM, FUNCTION return
        self.offset: Optional[int] = None # Memory offset for VAR, PARAM
        self.size: Optional[int] = None # Memory size for VAR, PARAM
        self.const_value: Any = None # Value for CONST
        self.param_list: Optional[List['Symbol']] = None # Parameters for PROCEDURE/FUNCTION
        self.param_modes: Optional[Dict[str, ParameterMode]] = None # Modes for parameters
        self.return_type: Optional[VarType] = None # Return type for FUNCTION
        self.local_size: Optional[int] = None # Size of locals for PROCEDURE/FUNCTION
        self.param_size: Optional[int] = None # Added: Use for SizeOfParams (total bytes)
        # Add fields for TYPE definitions if needed (e.g., base type, fields)

    def set_variable_info(self, var_type: VarType, offset: int, size: int):
        """Sets attributes specific to VARIABLE or PARAMETER symbols."""
        if self.entry_type not in (EntryType.VARIABLE, EntryType.PARAMETER):
            logger.warning(f"Attempting to set variable info on non-variable/parameter symbol '{self.name}'")
        self.var_type = var_type
        self.offset = offset
        self.size = size

    def set_constant_info(self, const_type: VarType, value: Any):
        """Sets attributes specific to CONSTANT symbols."""
        if self.entry_type != EntryType.CONSTANT:
            logger.warning(f"Attempting to set constant info on non-constant symbol '{self.name}'")
        self.var_type = const_type
        self.const_value = value

    def set_procedure_info(self, param_list: List['Symbol'], param_modes: Dict[str, ParameterMode], local_size: int, param_size: int):
        """Sets attributes specific to PROCEDURE symbols."""
        if self.entry_type != EntryType.PROCEDURE:
            logger.warning(f"Attempting to set procedure info on non-procedure symbol '{self.name}'")
        self.param_list = param_list or []
        self.param_modes = param_modes or {}
        self.local_size = local_size
        self.param_size = param_size # Store total parameter size

    def set_function_info(self, return_type: VarType, param_list: List['Symbol'], param_modes: Dict[str, ParameterMode], local_size: int, param_size: int):
        """Sets attributes specific to FUNCTION symbols."""
        if self.entry_type != EntryType.FUNCTION:
            logger.warning(f"Attempting to set function info on non-function symbol '{self.name}'")
        self.return_type = return_type
        self.param_list = param_list or []
        self.param_modes = param_modes or {}
        self.local_size = local_size
        self.param_size = param_size # Store total parameter size

    def __str__(self) -> str:
        """Provides a concise string representation of the symbol."""
        details = f"name='{self.name}', type={self.entry_type.name}, depth={self.depth}"
        if self.var_type: details += f", var_type={self.var_type.name}"
        if self.offset is not None: details += f", offset={self.offset}"
        if self.size is not None: details += f", size={self.size}"
        if self.const_value is not None: details += f", value={self.const_value!r}"
        if self.return_type: details += f", return={self.return_type.name}"
        # Display calculated sizes if available
        if self.local_size is not None: details += f", local_size={self.local_size}"
        if self.param_size is not None: details += f", param_size={self.param_size}"
        elif self.param_list is not None: details += f", params={len(self.param_list)}" # Fallback if size not set
        return f"Symbol({details})"

    def __repr__(self) -> str:
        return self.__str__()


# --- Custom Exceptions ---
class SymbolTableError(Exception):
    """Base class for symbol table specific errors."""
    pass

class SymbolNotFoundError(SymbolTableError):
    """Raised when a symbol lookup fails."""
    def __init__(self, name: str):
        super().__init__(f"Symbol '{name}' not found.")
        self.name = name

class DuplicateSymbolError(SymbolTableError):
    """Raised when attempting to insert a duplicate symbol in the same scope."""
    def __init__(self, name: str, depth: int):
        super().__init__(f"Symbol '{name}' already declared at depth {depth}.")
        self.name = name
        self.depth = depth


# --- Symbol Table Implementation ---
class SymbolTable:
    """
    Manages symbols using a stack of scopes for lexical scoping.
    """
    def __init__(self):
        """Initializes the symbol table with a single global scope (depth 0)."""
        self._scope_stack: List[Dict[str, Symbol]] = []
        self._current_depth: int = -1 # Will become 0 when first scope is entered
        self.enter_scope() # Initialize the global scope
        logger.info("Symbol Table initialized.")

    @property
    def current_depth(self) -> int:
        """Returns the current lexical scope depth."""
        return self._current_depth

    def enter_scope(self):
        """Enters a new lexical scope."""
        self._current_depth += 1
        self._scope_stack.append({})
        logger.info(f"Entered scope depth {self._current_depth}")

    def exit_scope(self):
        """Exits the current lexical scope."""
        if self._current_depth < 0:
            logger.error("Attempted to exit scope below global scope.")
            # Optionally raise an internal error
            return
        exiting_scope = self._scope_stack.pop()
        logger.info(f"Exiting scope depth {self._current_depth}. Removing {len(exiting_scope)} symbols.")
        self._current_depth -= 1
        if self._current_depth < -1: # Should not happen if logic is correct
             logger.critical("Symbol table depth inconsistency detected!")
             self._current_depth = -1 # Reset for safety


    def insert(self, symbol: Symbol):
        """
        Inserts a symbol into the current scope.

        Args:
            symbol: The Symbol object to insert.

        Raises:
            DuplicateSymbolError: If a symbol with the same name already exists
                                  in the current scope.
        """
        if not self._scope_stack:
             logger.error("Cannot insert symbol: No active scope.")
             # Optionally raise an internal error
             return

        current_scope = self._scope_stack[-1]
        name = symbol.name
        depth = self.current_depth # Symbol should belong to the current scope

        # Ensure symbol's depth matches current scope depth
        if symbol.depth != depth:
            # logger.warning(f"Inserting symbol '{name}' with depth {symbol.depth} into scope {depth}. Adjusting symbol depth.")
            # symbol.depth = depth # Remove adjustment - enforce correct depth from caller
            logger.error(f"Symbol '{name}' has depth {symbol.depth}, but current scope depth is {depth}.")
            raise ValueError(f"Attempting to insert symbol '{name}' with incorrect depth ({symbol.depth}) into scope {depth}.")

        if name in current_scope:
            logger.error(f"Duplicate symbol declaration: '{name}' at depth {depth}")
            raise DuplicateSymbolError(name, depth)

        current_scope[name] = symbol
        logger.info(f"Inserted symbol: {symbol}")

    def lookup(self, name: str, lookup_current_scope_only: bool = False) -> Symbol:
        """
        Looks up a symbol by name, searching from the current scope outwards.

        Args:
            name: The name (identifier) of the symbol to find.
            lookup_current_scope_only: If True, only search the current scope.

        Returns:
            The found Symbol object.

        Raises:
            SymbolNotFoundError: If the symbol is not found in any accessible scope.
        """
        logger.debug(f"Looking up symbol '{name}' (current scope only: {lookup_current_scope_only})")

        if lookup_current_scope_only:
            if self._scope_stack:
                current_scope = self._scope_stack[-1]
                if name in current_scope:
                    found_symbol = current_scope[name]
                    logger.debug(f"Found '{name}' in current scope (depth {self.current_depth})")
                    return found_symbol
            logger.debug(f"'{name}' not found in current scope (depth {self.current_depth})")
            raise SymbolNotFoundError(name)
        else:
            # Search from current scope down to global scope
            for depth in range(self.current_depth, -1, -1):
                if depth < len(self._scope_stack): # Ensure index is valid
                    scope = self._scope_stack[depth]
                    if name in scope:
                        found_symbol = scope[name]
                        logger.debug(f"Found '{name}' at depth {depth}")
                        return found_symbol
                else:
                     logger.warning(f"Scope inconsistency: looking for depth {depth}, but stack size is {len(self._scope_stack)}")

            logger.debug(f"'{name}' not found in any accessible scope.")
            raise SymbolNotFoundError(name)

    def get_current_scope_symbols(self) -> Dict[str, Symbol]:
        """Returns a dictionary of symbols in the current scope."""
        if not self._scope_stack:
            return {}
        return self._scope_stack[-1].copy() # Return a copy

    def __str__(self) -> str:
        """
        Return a formatted string representation of the current scope's symbol table.
        """
        symbols = self.get_current_scope_symbols()
        depth = self.current_depth
        lines = []
        lines.append(f"=== Symbol Table at depth {depth} ===")
        if not symbols:
            lines.append("<empty>")
            return "\n".join(lines)
        # Define columns
        headers = ["Lexeme", "Class", "Type", "Offset", "Size", "Value", "Params", "LocalSize"]
        rows = []
        for sym in symbols.values():
            lex = sym.name
            cls = sym.entry_type.name
            typ = ""
            offset = ""
            size = ""
            value = ""
            params = ""
            localsz = ""
            if sym.entry_type in (EntryType.VARIABLE, EntryType.PARAMETER):
                typ = sym.var_type.name if sym.var_type else ""
                offset = str(sym.offset) if sym.offset is not None else ""
                size = str(sym.size) if sym.size is not None else ""
            elif sym.entry_type == EntryType.CONSTANT:
                typ = sym.var_type.name if sym.var_type else ""
                value = str(sym.const_value)
            elif sym.entry_type == EntryType.PROCEDURE:
                params = str(len(sym.param_list) if sym.param_list else 0)
                localsz = str(sym.local_size if sym.local_size is not None else 0)
            rows.append([lex, cls, typ, offset, size, value, params, localsz])
        # Compute column widths
        col_widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
        # Build table
        header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
        separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
        lines.append(header_line)
        lines.append(separator)
        for row in rows:
            lines.append(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers))))
        return "\n".join(lines)

# --- Example Usage ---
if __name__ == "__main__":
    logger.info("--- Symbol Table Example ---")
    symtab = SymbolTable()

    # Global scope (depth 0)
    try:
        # Provide dummy line/column numbers for example Tokens
        global_var_token = Token("IDENTIFIER", "g_count", line_number=0, column_number=0)
        global_var = Symbol("g_count", global_var_token, EntryType.VARIABLE, symtab.current_depth)
        global_var.set_variable_info(VarType.INT, 0, 4)
        symtab.insert(global_var)

        proc_token = Token("IDENTIFIER", "my_proc", line_number=0, column_number=0)
        my_proc = Symbol("my_proc", proc_token, EntryType.PROCEDURE, symtab.current_depth)
        my_proc.set_procedure_info([], {}, 0, 0) # No params, 0 local size, 0 param size for example
        symtab.insert(my_proc)

    except DuplicateSymbolError as e:
        logger.error(e)

    # Lookups in global scope
    try:
        print(f"Lookup 'g_count': {symtab.lookup('g_count')}")
        print(f"Lookup 'my_proc': {symtab.lookup('my_proc')}")
    except SymbolNotFoundError as e:
        logger.error(e)

    # Enter scope 1
    symtab.enter_scope()
    try:
        local_var_token = Token("IDENTIFIER", "l_val", line_number=0, column_number=0)
        local_var = Symbol("l_val", local_var_token, EntryType.VARIABLE, symtab.current_depth)
        local_var.set_variable_info(VarType.FLOAT, 4, 8) # Example offset/size
        symtab.insert(local_var)

        # Try to redeclare global var (should fail)
        # g_count_token_dup = Token("IDENTIFIER", "g_count", line_number=0, column_number=0)
        # g_count_dup = Symbol("g_count", g_count_token_dup, EntryType.CONSTANT, symtab.current_depth)
        # symtab.insert(g_count_dup) # This would raise DuplicateSymbolError if uncommented

        # Shadow global var (allowed)
        shadow_proc_token = Token("IDENTIFIER", "my_proc", line_number=0, column_number=0)
        shadow_proc = Symbol("my_proc", shadow_proc_token, EntryType.VARIABLE, symtab.current_depth)
        shadow_proc.set_variable_info(VarType.BOOLEAN, 12, 1)
        symtab.insert(shadow_proc)

    except DuplicateSymbolError as e:
        logger.error(e)


    # Lookups in scope 1
    try:
        print(f"Lookup 'l_val' (scope 1): {symtab.lookup('l_val')}")
        print(f"Lookup 'g_count' (scope 1): {symtab.lookup('g_count')}") # Should find global
        print(f"Lookup 'my_proc' (scope 1): {symtab.lookup('my_proc')}") # Should find local shadow
        print(f"Lookup 'my_proc' (scope 1, current only): {symtab.lookup('my_proc', lookup_current_scope_only=True)}")
        # print(f"Lookup 'g_count' (scope 1, current only): {symtab.lookup('g_count', lookup_current_scope_only=True)}") # Raises SymbolNotFoundError
    except SymbolNotFoundError as e:
        logger.error(e)

    # Exit scope 1
    symtab.exit_scope()

    # Lookups after exiting scope 1
    try:
        print(f"Lookup 'g_count' (back in global): {symtab.lookup('g_count')}")
        print(f"Lookup 'my_proc' (back in global): {symtab.lookup('my_proc')}") # Should find global proc again
        # print(f"Lookup 'l_val' (back in global): {symtab.lookup('l_val')}") # Raises SymbolNotFoundError
    except SymbolNotFoundError as e:
        logger.error(e)

    print("--- Example End ---")
