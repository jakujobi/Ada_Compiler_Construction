#!/usr/bin/env python3
# RDParserExtExt.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-02
# Version: 2.0
"""
Extended Recursive Descent Parser for Assignment 6

This module extends the RDParser with additional grammar rules for statement parsing.
It implements the following grammar rules:

SeqOfStatments -> Statement ; StatTail | ε  
StatTail -> Statement ; StatTail | ε  
Statement -> AssignStat | IOStat  
AssignStat -> idt := Expr | ProcCall  
IOStat -> NULL | ε  
Expr -> Relation  
Relation -> SimpleExpr  
SimpleExpr -> Term MoreTerm  
MoreTerm -> addopt Term MoreTerm | ε  
Term -> Factor MoreFactor  
MoreFactor -> mulopt Factor MoreFactor | ε  
Factor -> idt | numt | ( Expr )| nott Factor| signopt Factor  

Where:
- addopt are + | - | or
- mulopt are * | / | mod | rem | and
- signopt is + | - (may use addopt here)
"""

import os
import sys
from typing import List, Optional, Any, Dict, Union
import traceback


from .RDParser import RDParser, ParseTreeNode
from .Token import Token
from .Definitions import Definitions
from .Logger import Logger
from .SymTable import SymbolTable, Symbol, EntryType, DuplicateSymbolError, SymbolNotFoundError, ParameterMode, VarType
from .TACGenerator import TACGenerator
from .TypeUtils import TypeUtils

# --- Import Mixins ---
from .rd_parser_mixins_declarations import DeclarationsMixin
from .rd_parser_mixins_statements import StatementsMixin
from .rd_parser_mixins_expressions import ExpressionsMixin
# --- End Import Mixins ---
class RDParserExtExt(DeclarationsMixin, StatementsMixin, ExpressionsMixin, RDParser):
    """
    Extended Recursive Descent Parser with grammar rules for statements and expressions,
    and integrated TAC generation.
    Inherits parsing logic from Mixin classes.
    """
    
    def __init__(self, tokens, defs, symbol_table: Optional[SymbolTable] = None, tac_generator: Optional[TACGenerator] = None, stop_on_error=False, panic_mode_recover=False, build_parse_tree=False):
        """
        Initialize the extended parser with TAC generation capabilities.
        
        Parameters:
            tokens (List[Token]): The list of tokens from the lexical analyzer.
            defs (Definitions): The definitions instance from the lexical analyzer.
            symbol_table (SymbolTable): Symbol table for semantic checking. Defaults to a new one if None.
            tac_generator (TACGenerator): TAC generator for code generation. Defaults to None.
            stop_on_error (bool): Whether to stop on error.
            panic_mode_recover (bool): Whether to attempt recovery from errors.
            build_parse_tree (bool): Whether to build a parse tree.
        """
        # Initialize base RDParser first
        super().__init__(tokens, defs, stop_on_error, panic_mode_recover, build_parse_tree)
        
        # Initialize RDParserExtExt specific attributes
        self.symbol_table: SymbolTable = symbol_table if symbol_table is not None else SymbolTable()
        self.semantic_errors = []
        self.tac_gen = tac_generator
        self.current_procedure_name: Optional[str] = None
        self.current_procedure_symbol: Optional[Symbol] = None
        self.current_procedure_depth: Optional[int] = None # ADDED: Track depth of proc being parsed
        self.current_local_offset: int = 0 # Typically starts negative for locals below BP
        self.current_param_offset: int = 0 # Typically starts positive for params above BP

        # --- Logging Start ---
        self.logger.info(f"RDParserExtExt Initialized. Mode: build_parse_tree={self.build_parse_tree}, tac_gen={bool(self.tac_gen)}")
        self.logger.debug(f" Symbol Table received: {bool(symbol_table)}")
        self.logger.debug(f" TAC Generator received: {bool(tac_generator)}")
        # --- Logging End ---
        
    def _add_child(self, parent, child):
        """
        Safely add a child to the parse tree when building it.
        Ensures parent and child are valid ParseTreeNodes.
        """
        if self.build_parse_tree and isinstance(parent, ParseTreeNode) and isinstance(child, ParseTreeNode):
            parent.add_child(child)
        # Optionally log if trying to add invalid child/parent?
        # elif self.build_parse_tree:
        #     self.logger.warning(f"Attempted to add invalid child ({type(child)}) to parent ({type(parent)})")
        
    def parseProg(self):
        """
        Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;
        
        Enhanced to check that the procedure identifier at the end matches the one at the beginning,
        and to emit TAC for procedure boundaries.
        Orchestrates calls to mixin methods for Args, DeclarativePart, SeqOfStatements.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Prog")
        else:
            node = None
        
        self.logger.info("Starting parsing: Prog")
        
        # Store the depth *before* this procedure is declared/entered
        # For the outermost procedure, this will be -1 (before global scope 0 is active)
        # For nested procedure P inside Q, this will be the depth of Q.
        # We add 1 to get the depth *where* the procedure symbol itself lives.
        procedure_declaration_depth = self.symbol_table.current_depth
        # Store the depth *of* this procedure's scope (which will be entered soon)
        procedure_scope_depth = procedure_declaration_depth + 1

        # Match procedure keyword
        self.match_leaf(self.defs.TokenType.PROCEDURE, node)
        
        # --- Get Procedure Name & Token --- 
        procedure_name = "<unknown>"
        start_id_token = self.current_token
        if start_id_token and start_id_token.token_type == self.defs.TokenType.ID:
            procedure_name = start_id_token.lexeme
            self.logger.info(f"Parsing procedure: {procedure_name} (Declared at depth {procedure_declaration_depth}, Scope will be {procedure_scope_depth})")
        else:
            # Handle error if ID is missing
            self.report_error("Expected procedure identifier")
            # Create a dummy token for potential later use, though unlikely useful
            start_id_token = Token(lexeme="<error>", token_type=self.defs.TokenType.ID, line_number=-1, column_number=-1)
        
        # Match the identifier token (even if it wasn't an ID, match advances past it)
        self.match_leaf(self.defs.TokenType.ID, node)

        # --- Insert Procedure Symbol into CURRENT scope --- 
        proc_sym: Optional[Symbol] = None
        is_outermost_procedure = self.symbol_table.current_depth == 0 # Check depth BEFORE inserting/entering scope
        if self.symbol_table and procedure_name != "<unknown>":
             try:
                 # Create symbol at the current depth (where it's declared)
                 proc_sym = Symbol(
                     procedure_name, 
                     start_id_token, 
                     EntryType.PROCEDURE, 
                     procedure_declaration_depth # Belongs to the scope where it's declared
                 )
                 # Initialize dummy param info; will be updated after parsing Args
                 proc_sym.param_list = [] 
                 proc_sym.param_modes = {} 
                 self.symbol_table.insert(proc_sym)
                 self.logger.debug(f" Inserted procedure symbol '{proc_sym.name}' at depth {proc_sym.depth}.")
             except DuplicateSymbolError as dse:
                 self.report_semantic_error(str(dse), start_id_token.line_number, start_id_token.column_number)
                 proc_sym = None # Failed insertion
             except Exception as e:
                 self.logger.error(f"Unexpected error inserting procedure symbol {procedure_name}: {e}")
                 proc_sym = None # Failed insertion

        # --- Emit TAC Proc Start (If generating TAC) --- 
        if self.tac_gen:
            self.logger.debug(f" Setting current_procedure context: name='{procedure_name}', depth={procedure_scope_depth}")
            # Store the current procedure context (name, symbol, AND DEPTH)
            self.current_procedure_name = procedure_name
            self.current_procedure_symbol = proc_sym
            self.current_procedure_depth = procedure_scope_depth # STORE DEPTH

            self.logger.debug(f" Emitting TAC: proc {procedure_name}")
            self.tac_gen.emitProcStart(procedure_name)
            
            # *** FIX 1: Only call emitProgramStart for the outermost procedure ***
            if is_outermost_procedure:
                 self.logger.info(f" Procedure '{procedure_name}' identified as outermost (depth 0). Recording for START PROC.")
                 self.tac_gen.emitProgramStart(procedure_name)
            else:
                 self.logger.debug(f" Procedure '{procedure_name}' is nested (depth {procedure_declaration_depth}). Not setting as program start.")

            # Initialize offsets for THIS procedure's scope
            self.current_local_offset = -2 
            self.current_param_offset = 4  
            self.logger.debug(f" Initializing offsets for '{procedure_name}': local={self.current_local_offset}, param={self.current_param_offset}")
            
        # --- Enter NEW Scope for procedure body --- 
        if self.symbol_table:
            self.logger.debug(f"Entering scope for procedure '{procedure_name}' body. New depth: {procedure_scope_depth}")
            self.symbol_table.enter_scope()
            # Verify depth after entering
            if self.symbol_table.current_depth != procedure_scope_depth:
                 self.logger.error(f"Scope depth mismatch after entering! Expected {procedure_scope_depth}, got {self.symbol_table.current_depth}")

        # --- Parse Args, IS, Declarations, BEGIN, Body, END --- 
        child = self.parseArgs() 
        self._add_child(node, child)
        # Update proc_sym.param_list/modes based on result of parseArgs
        if self.symbol_table and proc_sym:
            # This logic needs refinement. Parameters are inserted within parseArgs/
            # _parseArgListInfo into the *newly entered* scope (procedure_scope_depth).
            # We need to retrieve them from that scope and attach them to the proc_sym
            # which exists in the *outer* scope (procedure_declaration_depth).
            param_symbols_in_body_scope = []
            param_modes_in_body_scope = {}
            # Get symbols from the current scope (which is the procedure's body scope)
            current_scope_symbols = self.symbol_table.get_current_scope_symbols()
            for sym_name, sym in current_scope_symbols.items():
                 if sym.entry_type == EntryType.PARAMETER:
                     param_symbols_in_body_scope.append(sym)
                     # Assume mode was stored correctly during parseArgs
                     # If mode isn't on the symbol, this needs adjustment in parseArgs
                     param_modes_in_body_scope[sym_name] = getattr(sym, 'mode', ParameterMode.IN)

            # Update the procedure symbol (which lives in the outer scope)
            if param_symbols_in_body_scope:
                proc_sym.param_list = param_symbols_in_body_scope
                proc_sym.param_modes = param_modes_in_body_scope
                self.logger.debug(f" Updated procedure symbol '{proc_sym.name}' (at depth {proc_sym.depth}) with {len(param_symbols_in_body_scope)} parameters found in scope {self.symbol_table.current_depth}.")
            else:
                self.logger.debug(f"No parameter symbols found in scope {self.symbol_table.current_depth} to update procedure symbol '{proc_sym.name}'.")
        
        self.match_leaf(self.defs.TokenType.IS, node)
        
        child = self.parseDeclarativePart() # This will call parseProg recursively for nested procs
        self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.BEGIN, node)
        
        self.logger.debug("Parsing sequence of statements...")
        child = self.parseSeqOfStatements()
        self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.END, node)
        
        # --- Match End ID & Check Name --- 
        end_id_token = self.current_token
        self.match_leaf(self.defs.TokenType.ID, node)
        if end_id_token and start_id_token and start_id_token.lexeme != "<unknown>" and end_id_token.lexeme != start_id_token.lexeme:
            # ... (error reporting for mismatch) ...
            self.report_semantic_error(f"Procedure name mismatch: procedure '{start_id_token.lexeme}' ends with '{end_id_token.lexeme}'", getattr(end_id_token, 'line_number', -1), getattr(end_id_token, 'column_number', -1))
            
        self.match_leaf(self.defs.TokenType.SEMICOLON, node)

        # --- Emit TAC Proc End --- 
        if self.tac_gen and procedure_name != "<unknown>":
             self.logger.info(f" Emitting TAC: endp {procedure_name}")
             self.tac_gen.emitProcEnd(procedure_name)

        # --- Exit Scope --- 
        if self.symbol_table:
            self.logger.debug(f"Exiting scope {self.symbol_table.current_depth} for procedure '{procedure_name}'.")
            self.symbol_table.exit_scope()

        # Restore outer procedure context if this was nested
        # This requires maintaining a stack of procedure contexts
        # Simple approach for now: Reset depth if not nested (could be improved)
        if is_outermost_procedure:
             self.current_procedure_depth = None
             self.current_procedure_name = None
             self.current_procedure_symbol = None
             self.logger.debug("Reset procedure context after outermost procedure.")
        # Else: If nested, the caller's context should be restored implicitly by call stack
        # Needs verification if nesting > 1 level works correctly.

        self.logger.info(f"Finished parsing procedure: {procedure_name}")

        if self.build_parse_tree:
            return node
        else:
            return None # Or some indicator of success/failure
    
    def report_semantic_error(self, message, line=0, column=0):
        """
        Report a semantic error.
        
        Args:
            message: The error message
            line: The line number
            column: The column number
        """
        error = {
            'message': message,
            'line': line,
            'column': column
        }
        self.semantic_errors.append(error)
        self.logger.error(f"Semantic Error: {message} [Line: {line}, Col: {column}]")
    
    def parse(self) -> bool:
        """
        Override parse to allow multiple top-level procedures.
        """
        root: Optional[ParseTreeNode] = None
        if self.build_parse_tree:
            root = ParseTreeNode("ProgramList")
            
        self.logger.debug("Starting extended parse for multiple procedures.")
        # Parse all top-level procedures
        while self.current_token and self.current_token.token_type == self.defs.TokenType.PROCEDURE:
            child = self.parseProg()
            self._add_child(root, child) # _add_child handles None root/child gracefully

        # After procedures, expect EOF
        if self.current_token and self.current_token.token_type != self.defs.TokenType.EOF:
            self.report_error(f"Extra tokens found after program end: {self.current_token.lexeme}")
            # Consume extra tokens?
            while self.current_token and self.current_token.token_type != self.defs.TokenType.EOF:
                 self.advance()

        if self.build_parse_tree:
            self.parse_tree_root = root # Store the final tree root
            
        # Check for semantic errors accumulated
        if self.semantic_errors:
             self.logger.error("Semantic errors found during parsing.")
             # Optionally print them here or rely on driver
             for err in self.semantic_errors:
                  print(f"Semantic Error: {err['message']} [Line: {err['line']}, Col: {err['column']}]", file=sys.stderr)
        
        # Overall success depends on both syntax and semantic errors
        return len(self.errors) == 0 and len(self.semantic_errors) == 0
