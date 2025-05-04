#!/usr/bin/env python3
# NewSemanticAnalyzer.py
# type: ignore
# Author: AI Assistant
# Version: 1.0
"""
Semantic Analyzer for Ada Compiler

This module traverses the parse tree to:
  - Insert constants, variables, parameters, and procedures into the symbol table
  - Compute and track offsets by scope depth
  - Reject duplicate declarations at the same depth
  - Dump the symbol table at each scope exit and at program end
"""
from typing import List, Dict, Optional
from .SymTable import (
    SymbolTable,
    Symbol,
    EntryType,
    DuplicateSymbolError,
    VarType,
    ParameterMode,
    SymbolNotFoundError,
)
from .Logger import logger
from .RDParser import ParseTreeNode
from .Token import Token

class NewSemanticAnalyzer:
    def __init__(
        self,
        symtab: SymbolTable,
        root: ParseTreeNode,
        defs,
    ):
        """
        Initialize semantic analyzer.

        Args:
            symtab: Shared symbol table instance
            root:   Parse tree root from RDParser
            defs:   Definitions object (for token enums)
        """
        self.symtab = symtab
        self.root = root
        self.defs = defs
        self.errors: List[str] = []
        # next free offset for locals by depth
        self.offsets: Dict[int, int] = {}
        # next free positive offset for parameters
        self.param_offsets: Dict[int, int] = {}
        self.string_label_counter: int = 0 # Added for unique string labels

    def analyze(self) -> bool:
        """
        Perform semantic analysis: insert symbols and dump tables.
        Returns True if no semantic errors.
        """
        # Initialize offsets at global scope (depth0)
        depth0 = self.symtab.current_depth
        self.offsets[depth0] = 0
        self.param_offsets[depth0] = 0

        # Process program(s): handle single Prog node or a ProgramList
        if hasattr(self.root, 'name') and self.root.name == 'ProgramList':  # multiple procs
            for prog_node in self.root.children or []:
                self._visit_program(prog_node)
        else:
            # Single program/procedure node
            self._visit_program(self.root)

        # Dump remaining global symbols at depth0
        self._dump_scope(self.symtab.current_depth)
        return len(self.errors) == 0

    def _find_first_id(self, node: ParseTreeNode) -> Optional[ParseTreeNode]:
        """Recursively find the first ID node in the parse subtree."""
        # Direct ID leaf
        if node.name == "ID" and node.token:
            return node
        # Recurse into children
        for child in getattr(node, 'children', []):
            found = self._find_first_id(child)
            if found:
                return found
        return None

    def _visit_program(self, node: ParseTreeNode) -> None:
        """
        Visit a 'Prog' node to insert procedure, process params, declarations, nested procs.
        """
        depth = self.symtab.current_depth
        # Get program/procedure name from first ID leaf in subtree
        id_node = self._find_first_id(node)
        if id_node is None or id_node.token is None:
            self._error("Missing program/procedure name")
            return
        name = id_node.token.lexeme
        proc_symbol = Symbol(name, id_node.token, EntryType.PROCEDURE, depth)  # type: ignore[arg-type]
        # Insert procedure symbol
        try:
            self.symtab.insert(proc_symbol)
        except DuplicateSymbolError as e:
            self._error(f"Duplicate procedure '{e.name}' at depth {e.depth}")
            return
        # Enter new scope for procedure body
        self.symtab.enter_scope()
        current_scope_depth = self.symtab.current_depth
        # Initialize offsets at new depth for locals and parameters
        self.offsets[current_scope_depth] = 0
        self.param_offsets[current_scope_depth] = 0 # This might not be used if offsets calculated in _visit_formals
        
        # Handle formal parameters (inserted at this new scope depth)
        param_list, param_modes = self._visit_formals(node)
        # Calculate total parameter size
        total_param_size = sum(p.size for p in param_list if p.size is not None)

        # Declarations (constants & variables)
        decls_node = node.find_child_by_name("DeclarativePart")
        self._visit_declarative_part(decls_node)
        # Get size of declared locals from offset counter
        declared_local_size = self.offsets[current_scope_depth]

        # Nested procedures
        procs_node = node.find_child_by_name("Procedures")
        if procs_node:
            for child in procs_node.children:
                if child.name == "Prog":
                    self._visit_program(child)

        # Check statements for undeclared identifier uses and handle string literals
        stmts_node = node.find_child_by_name("SeqOfStatements")
        if stmts_node:
            self._visit_statements(stmts_node) # Pass symtab to allow global string insertion

        # Record sizes and update procedure info
        # Note: local_size here only includes declared locals, not temps.
        # Temps size needs to be handled later (e.g., by ASMGenerator based on TAC).
        if proc_symbol:
             if proc_symbol.entry_type == EntryType.PROCEDURE:
                 proc_symbol.set_procedure_info(param_list, param_modes, declared_local_size, total_param_size)
                 logger.info(f"Updated procedure '{proc_symbol.name}': local_size={declared_local_size}, param_size={total_param_size}")
             elif proc_symbol.entry_type == EntryType.FUNCTION: # Assuming FUNCTION processing is similar
                 # Ensure return_type is set appropriately elsewhere if needed
                 proc_symbol.set_function_info(proc_symbol.return_type, param_list, param_modes, declared_local_size, total_param_size)
                 logger.info(f"Updated function '{proc_symbol.name}': local_size={declared_local_size}, param_size={total_param_size}")

        # Dump and exit this scope
        self._dump_scope(self.symtab.current_depth)
        self.symtab.exit_scope()

    def _visit_formals(self, node: ParseTreeNode) -> tuple[List[Symbol], Dict[str, ParameterMode]]:
        """
        Traverse 'Args' subtree to insert parameters with offsets and modes.
        """
        depth = self.symtab.current_depth
        param_list: List[Symbol] = []
        param_modes: Dict[str, ParameterMode] = {}
        args_node = node.find_child_by_name("Args")
        if args_node is None:
            return param_list, param_modes
        # Gather all parameter entries (lexeme, token, var_type, size, mode)
        entries = []
        for arg_list in args_node.find_children_by_name("ArgList") or []:
            current = arg_list
            while current:
                # Determine mode
                mode = ParameterMode.IN
                mode_node = current.find_child_by_name("Mode")
                if mode_node and mode_node.children and mode_node.children[0].token:
                    ttype = mode_node.children[0].token.token_type
                    if ttype == self.defs.TokenType.OUT:
                        mode = ParameterMode.OUT
                    elif ttype == self.defs.TokenType.INOUT:
                        mode = ParameterMode.INOUT
                # TypeMark and IdentifierList
                id_list = current.find_child_by_name("IdentifierList")
                type_mark = current.find_child_by_name("TypeMark")
                if not id_list or not type_mark:
                    break
                var_type = self._map_typemark_to_vartype(type_mark)
                size = {VarType.INT:2, VarType.CHAR:1, VarType.FLOAT:4}.get(var_type, 0)
                for id_leaf in id_list.find_children_by_name("ID") or []:
                    if not id_leaf.token:
                        continue
                    lex = id_leaf.token.lexeme
                    tok = id_leaf.token
                    entries.append((lex, tok, var_type, size, mode))
                # Move to next MoreArgs
                more = current.find_child_by_name("MoreArgs")
                current = more.find_child_by_name("ArgList") if more else None
        # Compute offsets in reverse order (first param highest offset)
        if entries:
            base = 2
            sizes = [e[3] for e in entries]
            for i, (lex, tok, var_type, size, mode) in enumerate(entries):
                offset = base + sum(sizes[i:])
                psym = Symbol(lex, tok, EntryType.PARAMETER, self.symtab.current_depth)  # type: ignore[arg-type]
                psym.set_variable_info(var_type, offset, size)
                try:
                    self.symtab.insert(psym)
                except DuplicateSymbolError as e:
                    self._error(f"Duplicate parameter '{e.name}' at depth {e.depth}")
                    continue
                param_list.append(psym)
                param_modes[lex] = mode
        return param_list, param_modes

    def _visit_declarative_part(self, node: Optional[ParseTreeNode]) -> None:
        """
        Traverse subtree to find all DeclarativePart nodes and process their declarations.
        """
        if node is None:
            return
        # Debug: show immediate children of the DeclarativePart subtree
        logger.info(f"DeclarativePart subtree children: {[c.name for c in node.children]}")
        # DFS find all DeclarativePart nodes
        dp_nodes = []
        def dfs(n: ParseTreeNode):
            if n.name == "DeclarativePart":
                dp_nodes.append(n)
            for c in n.children:
                dfs(c)
        dfs(node)
        # Process each declarative-part occurrence
        for dp in dp_nodes:
            # Debug: show details of this DeclarativePart node
            logger.info(f"Found DeclarativePart node with {len(dp.children)} children; first child: {dp.children[0].name if dp.children else 'None'}")
            # Skip epsilon
            if dp.children and dp.children[0].name == "ε":
                continue
            id_list = dp.find_child_by_name("IdentifierList")
            type_mark = dp.find_child_by_name("TypeMark")
            if not id_list or not type_mark:
                continue
            # Constant or variable
            first = type_mark.children[0] if type_mark.children else None
            if first and first.token and first.token.token_type == self.defs.TokenType.CONSTANT:
                self._insert_constants(id_list, type_mark)
            else:
                self._insert_variables(id_list, type_mark)

    def _insert_constants(self, id_list: ParseTreeNode, type_mark: ParseTreeNode) -> None:
        """
        Insert constant declarations into symbol table with their literal values.
        """
        depth = self.symtab.current_depth
        val_node = type_mark.find_child_by_name("Value")
        if val_node and val_node.children and val_node.children[0].token:
            lit_token = val_node.children[0].token
            ttype = lit_token.token_type
            # Determine constant's var type and correct value field
            if ttype == self.defs.TokenType.NUM:
                var_type = VarType.INT
                value = lit_token.value
            elif ttype == self.defs.TokenType.REAL:
                var_type = VarType.FLOAT
                value = getattr(lit_token, 'real_value', lit_token.value)
            else:
                var_type = VarType.INT
                value = getattr(lit_token, 'literal_value', lit_token.value)
            for id_leaf in id_list.find_children_by_name("ID") or []:
                if not id_leaf.token:
                    continue
                name = id_leaf.token.lexeme
                csym = Symbol(name, id_leaf.token, EntryType.CONSTANT, depth)  # type: ignore[arg-type]
                csym.set_constant_info(var_type, value)
                try:
                    self.symtab.insert(csym)
                except DuplicateSymbolError as e:
                    self._error(f"Duplicate constant '{e.name}' at depth {e.depth}")

    def _insert_variables(self, id_list: ParseTreeNode, type_mark: ParseTreeNode) -> None:
        """
        Insert variable declarations into symbol table with offsets and sizes.
        """
        depth = self.symtab.current_depth
        var_type = self._map_typemark_to_vartype(type_mark)
        size = {VarType.INT:2, VarType.CHAR:1, VarType.FLOAT:4}.get(var_type, 0)
        ids = [leaf.token.lexeme for leaf in id_list.find_children_by_name("ID") or [] if leaf.token]
        logger.debug(f"Inserting variables {ids} at depth {self.symtab.current_depth}")
        for id_leaf in id_list.find_children_by_name("ID") or []:
            if id_leaf.token is None:
                continue
            name = id_leaf.token.lexeme
            offset = self.offsets[depth]
            logger.info(f"Inserting variable: {name}, type={var_type.name}, offset={offset}, size={size}")
            # token type mismatch; suppress
            vsym = Symbol(name, id_leaf.token, EntryType.VARIABLE, depth)  # type: ignore[arg-type]
            vsym.set_variable_info(var_type, offset, size)
            self.offsets[depth] += size
            try:
                self.symtab.insert(vsym)
            except DuplicateSymbolError as e:
                self._error(f"Duplicate variable '{e.name}' at depth {e.depth}")

    def _map_typemark_to_vartype(self, type_mark: Optional[ParseTreeNode]) -> VarType:
        """
        Map a 'TypeMark' node's first child to a VarType enum.
        """
        if not type_mark or not type_mark.children:
            return VarType.INT
        child = type_mark.children[0]
        if not child.token:
            return VarType.INT
        ttype = child.token.token_type
        if ttype == self.defs.TokenType.INTEGERT:
            return VarType.INT
        if ttype == self.defs.TokenType.CHART:
            return VarType.CHAR
        if ttype in (self.defs.TokenType.REALT, self.defs.TokenType.FLOAT):
            return VarType.FLOAT
        return VarType.INT

    def _dump_scope(self, depth: int) -> None:
        """
        Dump all symbols at the given scope depth.
        """
        symbols = list(self.symtab.get_current_scope_symbols().values())
        # If empty, show empty scope message
        if not symbols:
            print(f"\n=== Symbol Table at depth {depth} (empty) ===")
            return
        # Column headers
        headers = ["Lexeme", "Class", "Type", "Offset", "Size", "Value", "Params", "LocalSize"]
        rows = []
        for sym in symbols:
            lex = sym.name
            cls = sym.entry_type.name
            typ = ""
            offset = ""
            size = ""
            value = ""
            params = ""
            localsz = ""
            if sym.entry_type in (EntryType.VARIABLE, EntryType.PARAMETER):
                typ = sym.var_type.name
                offset = str(sym.offset)
                size = str(sym.size)
            elif sym.entry_type == EntryType.CONSTANT:
                typ = sym.var_type.name
                value = str(sym.const_value)
            elif sym.entry_type == EntryType.PROCEDURE:
                params = str(len(sym.param_list) if sym.param_list else 0)
                localsz = str(sym.local_size if sym.local_size is not None else 0)
            rows.append([lex, cls, typ, offset, size, value, params, localsz])
        # Compute column widths
        col_widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
        # Print header
        print(f"\n=== Symbol Table at depth {depth} ===")
        header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
        separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
        print(header_line)
        print(separator)
        # Print rows
        for row in rows:
            print(" | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers))))

    def _error(self, message: str) -> None:
        """
        Record and log a semantic error.
        """
        logger.error(message)
        self.errors.append(message)

    def _visit_statements(self, node: ParseTreeNode) -> None:
        """
        Traverse SeqOfStatements nodes, checking for undeclared IDs
        and handling string literals within I/O calls.
        """
        # Example: This needs to be adapted based on *your specific parse tree structure* for I/O statements.
        # Assume a structure like: Statement -> IOStat -> PutStat -> WriteList -> WriteToken -> LITERAL
        def dfs(n: ParseTreeNode):
            if n.name == "PutStat": # Or whatever your node name for put/putln is
                # Find string literals within the arguments/write list
                write_list = n.find_child_by_name("WriteList") # Example name
                if write_list:
                     for write_token in write_list.find_children_by_name("WriteToken"): # Example name
                          literal_node = write_token.find_child_by_name("LITERAL") # Find the literal leaf
                          if literal_node:
                              self._handle_string_literal(literal_node)
                               # The label returned isn't directly used here, but insertion is done.
                               # The *Parser* action associated with this node would need the label.
            elif n.name == "AssignStat": # Example: Check assignment statement LHS
                 self._visit_assign_stat(n)
            
            # Recurse
            for child in getattr(n, 'children', []):
                dfs(child)

        if node:
           dfs(node)

    def _visit_assign_stat(self, node: ParseTreeNode) -> None:
        """Check that the variable on the left side of an assignment is declared."""
        # The first ID child in an AssignStat node is the LHS
        id_node = node.find_child_by_name("ID")
        if id_node and id_node.token:
            lex = id_node.token.lexeme
            try:
                self.symtab.lookup(lex)
            except SymbolNotFoundError:
                line = getattr(id_node.token, 'line_number', -1)
                self._error(f"Undeclared identifier '{lex}' used in assignment at line {line}")

    def _handle_string_literal(self, string_node: ParseTreeNode) -> Optional[str]:
        """
        Generates a unique label for a string literal, adds it to the global
        symbol table scope (depth 0) as a constant, and returns the label.
        Ensures the string value has a '$' terminator.
        """
        if not (string_node.token and string_node.token.token_type == self.defs.TokenType.LITERAL):
            logger.error("Node passed to _handle_string_literal is not a string literal.")
            return None

        # Get value, remove quotes, ensure $ terminator
        # Assuming literal_value holds the content without outer quotes
        original_value = getattr(string_node.token, 'literal_value', string_node.token.lexeme)
        # Strip outer quotes if lexeme was used
        if original_value.startswith('"') and original_value.endswith('"'):
             string_value = original_value[1:-1]
        else:
             string_value = original_value
        # Replace Ada doubled quotes "" with single quote " for ASM
        string_value = string_value.replace("""", '"')
             
        if not string_value.endswith('$'):
            string_value += '$'

        # Generate unique label
        label = f"_S{self.string_label_counter}"
        self.string_label_counter += 1

        # Create symbol (use string_node's token for location info)
        # Store at depth 0 (global scope)
        str_sym = Symbol(label, string_node.token, EntryType.CONSTANT, 0) 
        str_sym.const_value = string_value
        str_sym.var_type = None # Or potentially a new VarType.STRING_LITERAL?
        
        # Insert into GLOBAL scope (depth 0)
        try:
             global_scope = self.symtab._scope_stack[0]
             if label in global_scope:
                  logger.warning(f"String label '{label}' somehow already exists. Reusing.")
                  return label # Avoid inserting duplicate label
             global_scope[label] = str_sym # Insert directly into depth 0
             logger.info(f"Inserted string literal symbol: {str_sym} into global scope.")
        except IndexError:
             logger.error("Cannot access global scope (depth 0) to insert string literal.")
             self._error(f"Internal error: Could not access global scope for string '{label}'.")
             return None
        except Exception as e:
             logger.error(f"Unexpected error inserting string literal '{label}': {e}")
             self._error(f"Failed to insert string literal '{label}' due to {e}")
             return None
             
        return label
