"""
Adapter that makes the new SymTable.SymbolTable look like the old
AdaSymbolTable interface expected by SemanticAnalyzer.
Drop it in the same package and import instead of AdaSymbolTable.
"""

from collections import defaultdict
from typing import Dict, Optional

from .SymTable import (
    SymbolTable, Symbol, VarType, EntryType, ParameterMode
)

class AdaSymbolTableAdapter:
    """
    Wraps the modern stack‑based SymbolTable with the handful of
    methods/attrs SemanticAnalyzer uses: insert, lookup, deleteDepth,
    writeTable, table_size.
    """
    def __init__(self):
        self._core = SymbolTable()

    # ---------- helpers ----------
    @property
    def table_size(self) -> int:
        "Needed only for a debug print."
        total = 0
        for scope in self._core._scope_stack:          # pylint: disable=protected-access
            total += len(scope)
        return total

    # ---------- original API ----------
    def lookup(self, lexeme: str, depth: int) -> Optional[Symbol]:
        """
        Old code passes an *absolute depth*.  We obey it by scanning
        that scope only; otherwise fall back to regular lookup.
        """
        if 0 <= depth <= self._core.current_depth:
            return self._core._scope_stack[depth].get(lexeme)    # pylint: disable=protected-access
        return self._core.lookup(lexeme)

    def insert(self, lexeme, token_type, depth):
        """
        Create a Symbol and hand it to the core table.  The depth
        parameter from the old design must match the *current* scope,
        so we assert for safety.
        """
        if depth != self._core.current_depth:
            raise ValueError(
                f"Adapter out‑of‑sync: got depth {depth}, "
                f"but current scope is {self._core.current_depth}"
            )
        sym = Symbol(lexeme, token_type, EntryType.VARIABLE, depth)
        self._core.insert(sym)
        return sym            # returned so caller can fill in details

    def deleteDepth(self, depth: int):
        """
        Drop an entire scope (used when exiting a procedure body).
        """
        while self._core.current_depth >= depth:
            self._core.exit_scope()

    def writeTable(self, depth: int) -> Dict[str, Symbol]:
        """
        Return a *copy* of the requested scope for pretty printing.
        """
        if 0 <= depth <= self._core.current_depth:
            return dict(self._core._scope_stack[depth])          # pylint: disable=protected-access
        return {}

    # ---------- handy pass‑throughs ----------
    def enter_scope(self):
        self._core.enter_scope()

    def exit_scope(self):
        self._core.exit_scope()
