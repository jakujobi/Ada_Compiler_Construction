#!/usr/bin/env python3
# SymTable.py
# Author: John Akujobi and improved with locally run Qwen
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
        self.procedure_definitions: Dict[str, Symbol] = {} # ADDED: For persistent procedure symbols
        self.enter_scope() # Initialize the global scope
        logger.info("Symbol Table initialized.")

        # For string literal management
        self.string_literals_map: Dict[str, str] = {} # Maps string value to unique label
        self.next_string_label_id: int = 0

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
        """Exits the current lexical scope. Scope dictionary is retained in _scope_stack for potential historical lookups."""
        if self._current_depth < 0:
            logger.error("Attempted to exit scope below global scope.")
            return
        
        # Scope is not popped from _scope_stack to allow historical lookup by depth.
        # exiting_scope = self._scope_stack.pop() 
        exiting_scope_dict = {}
        if self._current_depth < len(self._scope_stack):
            exiting_scope_dict = self._scope_stack[self._current_depth]
        
        logger.info(f"Exiting scope depth {self._current_depth}. Scope contained {len(exiting_scope_dict)} symbols. (Scope dictionary retained in stack)")
        self._current_depth -= 1
        if self._current_depth < -1: 
             logger.critical("Symbol table depth inconsistency detected post exit_scope!")
             self._current_depth = -1

    def insert(self, symbol: Symbol):
        """
        Inserts a symbol into the scope indicated by self._current_depth.
        Ensures _scope_stack is grown if current_depth is beyond its current len - 1.
        """
        name = symbol.name
        depth = self.current_depth

        if symbol.depth != depth:
            logger.error(f"Symbol '{name}' has depth {symbol.depth}, but current scope depth for insertion is {depth}.")
            raise ValueError(f"Attempting to insert symbol '{name}' with incorrect depth ({symbol.depth}) into scope {depth}.")

        # Ensure _scope_stack has a dictionary for the current depth
        while depth >= len(self._scope_stack):
            self._scope_stack.append({})
            logger.debug(f"Extended _scope_stack to accommodate depth {len(self._scope_stack)-1}")

        current_scope_dict = self._scope_stack[depth]

        if name in current_scope_dict:
            logger.error(f"Duplicate symbol declaration: '{name}' at depth {depth}")
            raise DuplicateSymbolError(name, depth)

        current_scope_dict[name] = symbol
        logger.info(f"Inserted symbol: {symbol} into scope {depth}")

        if symbol.entry_type in [EntryType.PROCEDURE, EntryType.FUNCTION]:
            if name in self.procedure_definitions:
                logger.warning(f"Procedure/Function '{name}' redefined. Overwriting in persistent store.")
            self.procedure_definitions[name] = symbol
            logger.info(f"Stored persistent definition for {symbol.entry_type.name}: {name}")

    def lookup(self, name: str, lookup_current_scope_only: bool = False, search_from_depth: Optional[int] = None) -> Symbol:
        """
        Looks up a symbol by name, searching from a specified depth or current_depth outwards.
        Assumes _scope_stack contains all historical scopes, indexed by their depth.
        """
        effective_start_depth = search_from_depth if search_from_depth is not None else self._current_depth

        if lookup_current_scope_only:
            if 0 <= effective_start_depth < len(self._scope_stack):
                scope_to_search = self._scope_stack[effective_start_depth]
                if name in scope_to_search:
                    logger.debug(f"Found '{name}' at depth {effective_start_depth} (current/specified scope only).")
                    return scope_to_search[name]
            logger.debug(f"'{name}' not found in scope {effective_start_depth} (current/specified scope only).")
            raise SymbolNotFoundError(name)

        # Search from effective_start_depth down to global scope (depth 0)
        # Ensure effective_start_depth is a valid index for _scope_stack
        if not (0 <= effective_start_depth < len(self._scope_stack)):
            logger.debug(f"'{name}' not found: initial search depth {effective_start_depth} is out of bounds for preserved scope stack (len {len(self._scope_stack)}).")
            raise SymbolNotFoundError(name)

        for i in range(effective_start_depth, -1, -1):
            # Ensure scope index i is valid for _scope_stack (it should be if effective_start_depth was valid)
            if i < len(self._scope_stack):
                scope = self._scope_stack[i]
                if name in scope:
                    logger.debug(f"Found '{name}' at depth {i} (searched from effective_depth {effective_start_depth}).")
                    return scope[name]
            else:
                # This case should ideally not be reached if effective_start_depth is validated.
                logger.error(f"SymbolTable.lookup internal error: index {i} out of bounds during loop for _scope_stack (len {len(self._scope_stack)})")
        
        logger.debug(f"'{name}' not found in any accessible scope (searched from effective_depth {effective_start_depth} down to 0).")
        raise SymbolNotFoundError(name)

    def get_procedure_definition(self, name: str) -> Optional[Symbol]:
        """Retrieves a procedure or function symbol from the persistent store."""
        found_symbol = self.procedure_definitions.get(name)
        if found_symbol:
            logger.debug(f"Retrieved persistent definition for '{name}': {found_symbol}")
        else:
            logger.warning(f"Persistent definition for procedure/function '{name}' not found.")
        return found_symbol

    def get_current_scope_symbols(self) -> Dict[str, Symbol]:
        """Returns a dictionary of symbols in the current scope."""
        if not self._scope_stack:
            return {}
        return self._scope_stack[-1].copy() # Return a copy

    def add_string_literal(self, string_value: str) -> str:
        """
        Adds a string literal to a global store and returns a unique label for it.
        If the string already exists, returns its existing label.

        Args:
            string_value: The processed string value (e.g., "Hello World").

        Returns:
            A unique label for the string (e.g., "_S0", "_S1").
        """
        if string_value in self.string_literals_map:
            logger.debug(f"String literal '{string_value}' already exists, reusing label '{self.string_literals_map[string_value]}'")
            return self.string_literals_map[string_value]
        else:
            label = f"_S{self.next_string_label_id}"
            self.string_literals_map[string_value] = label
            self.next_string_label_id += 1
            logger.debug(f"Added new string literal '{string_value}' with label '{label}'")
            return label

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
