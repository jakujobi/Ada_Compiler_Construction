#!/usr/bin/env python3
# NewSemanticAnalyzer.py
# Author: AI Assistant
# Version: 1.0
"""
Semantic Analyzer for Ada Compiler

This module visits a parse tree (built by RDParser) and performs semantic actions:
- Inserts constants, variables, and procedures into the symbol table
- Computes and tracks offsets for variables by scope depth
- Rejects duplicate declarations in the same scope
- Dumps the symbol table contents at each procedure exit and at program end
"""
from typing import Optional
from .SymTable import *
from .RDParser import ParseTreeNode
from .Logger import logger

class NewSemanticAnalyzer:
    def __init__(self, symtab: SymbolTable, root: ParseTreeNode, defs):
        """
        Initialize the semantic analyzer.

        Args:
            symtab: The shared symbol table instance
            root: The parse-tree root from RDParser.parse()
            defs: The Definitions object (token types, etc.)
        """
        self.symtab = symtab
        self.root = root
        self.defs = defs
        # Track current offset per depth for variable declarations
        self.offsets = {}
        # Collect semantic errors
        self.errors = []

    def analyze(self) -> bool:
        """
        Traverse the parse tree, perform semantic actions, and dump symbol tables.
        Returns True if no semantic errors were encountered.
        """
        # Begin at global scope (depth 0)
        self.symtab.enter_scope()
        self.offsets[self.symtab.current_depth] = 0

        # Process the program node
        self._visit_prog(self.root)

        # Dump remaining global symbols
        self._dump_scope(self.symtab.current_depth)
        self.symtab.exit_scope()

        return len(self.errors) == 0

    def _visit_prog(self, node: ParseTreeNode) -> None:
        """
        Visit a 'Prog' node: insert program procedure, then its body.
        """
        # The first ID child is the program/procedure name
        id_node = next((c for c in node.children if c.name == 'ID'), None)
        if id_node is None or id_node.token is None:
            self._error('Missing program name')
            return
        name = id_node.token.lexeme
        # Create and insert the procedure symbol
        proc_symbol = Symbol(name, id_node.token, EntryType.PROCEDURE, self.symtab.current_depth)
        try:
            self.symtab.insert(proc_symbol)
        except DuplicateSymbolError:
            self._error(f"Duplicate procedure declaration: {name}")
            return
        # Initialize procedure entry with empty local/param info for now
        proc_symbol.set_procedure_info([], {}, 0)

        # Handle declarations in this scope
        decl = node.find_child_by_name('DeclarativePart')
        if decl:
            self._visit_declarative_part(decl)

        # Handle nested procedures
        procs = node.find_child_by_name('Procedures')
        if procs:
            for child in procs.children:
                if child.name == 'Prog':
                    # Enter nested procedure (new scope)
                    self.symtab.enter_scope()
                    self.offsets[self.symtab.current_depth] = 0
                    self._visit_prog(child)

    def _visit_declarative_part(self, node: ParseTreeNode) -> None:
        """
        Visit 'DeclarativePart': one or more variable/constant declarations.
        """
        # Continue as long as ID appears
        current = node
        while current and current.name == 'DeclarativePart':
            # IdentifierList child
            id_list = next((c for c in current.children if c.name == 'IdentifierList'), None)
            # TypeMark child
            type_mark = next((c for c in current.children if c.name == 'TypeMark'), None)
            if id_list and type_mark:
                var_type = self._extract_type(type_mark)
                # For each ID in the list, insert variable or constant
                for id_leaf in [c for c in id_list.children if c.name == 'ID']:
                    lex = id_leaf.token.lexeme
                    token = id_leaf.token
                    var_symbol = Symbol(lex, token, EntryType.VARIABLE, self.symtab.current_depth)
                    try:
                        self.symtab.insert(var_symbol)
                    except DuplicateSymbolError:
                        self._error(f"Duplicate declaration '{lex}' at depth {self.symtab.current_depth}")
                        continue
                    # Compute size based on type
                    size = {VarType.INT:2, VarType.CHAR:1, VarType.FLOAT:4}.get(var_type, 0)
                    offset = self.offsets[self.symtab.current_depth]
                    var_symbol.set_variable_info(var_type, offset, size)
                    self.offsets[self.symtab.current_depth] += size
            # Move to the next DeclarativePart (recursive)
            next_decl = None
            for c in current.children:
                if c.name == 'DeclarativePart' and c is not node:
                    next_decl = c
                    break
            current = next_decl

    def _extract_type(self, node: ParseTreeNode) -> VarType:
        """
        Given a 'TypeMark' node, deduce the VarType.
        """
        child = node.children[0] if node.children else None
        if child and child.token:
            ttype = child.token.token_type
            if ttype == self.defs.TokenType.INTEGERT:
                return VarType.INT
            if ttype == self.defs.TokenType.CHART:
                return VarType.CHAR
            if ttype in (self.defs.TokenType.REALT, self.defs.TokenType.FLOAT):
                return VarType.FLOAT
        # default
        return VarType.INT

    def _dump_scope(self, depth: int) -> None:
        """
        Print all symbols at the given scope depth.
        """
        print(f"\nSymbol Table at depth {depth}:")
        for sym in self.symtab.get_current_scope_symbols().values():
            print(f"  {sym.name}: {sym.entry_type.name}")

    def _error(self, message: str) -> None:
        """
        Record a semantic error (will be reported by the driver).
        """
        logger.error(message)
        self.errors.append(message)
