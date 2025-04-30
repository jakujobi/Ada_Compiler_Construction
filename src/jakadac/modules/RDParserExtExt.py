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

# CORRECTED Inheritance Order: Mixins first, then base class RDParser
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
        
        # Match procedure keyword
        self.match_leaf(self.defs.TokenType.PROCEDURE, node)
        
        # Save the procedure identifier (first occurrence)
        procedure_name = "unknown"
        start_id_token = self.current_token

        if start_id_token and start_id_token.token_type == self.defs.TokenType.ID:
            procedure_name = start_id_token.lexeme
            self.logger.info(f"Parsing procedure: {procedure_name}")

            # --- TAC Generation Start --- 
            if self.tac_gen:
                self.logger.debug(f" Setting current_procedure_name = '{procedure_name}'")
                self.current_procedure_name = procedure_name
                self.logger.debug(f" Emitting TAC: proc {procedure_name}")
                self.tac_gen.emitProcStart(procedure_name)
                # Initialize offsets for this procedure's scope
                # Common convention: Params positive offset, Locals negative
                self.current_local_offset = -2 # Start below FP, Return Addr
                self.current_param_offset = 4  # Start above FP, RA, Dynamic Link
                self.logger.debug(f" Initializing offsets: local={self.current_local_offset}, param={self.current_param_offset}")
                # Insert preliminary procedure symbol if needed for recursion/forward calls
                if self.symbol_table and self.symbol_table.current_depth == 0:
                    try:
                        # Enter scope 1 temporarily to check/insert
                        self.symbol_table.enter_scope()
                        try:
                             self.symbol_table.lookup(procedure_name, lookup_current_scope_only=True)
                        except SymbolNotFoundError:
                            proc_sym = Symbol(
                                procedure_name,
                                start_id_token, 
                                EntryType.PROCEDURE,
                                self.symbol_table.current_depth # Now in scope 1
                            )
                            # Initialize empty lists/dicts for params if needed
                            proc_sym.param_list = [] 
                            proc_sym.param_modes = {}
                            try:
                                self.symbol_table.insert(proc_sym)
                                self.current_procedure_symbol = proc_sym
                            except DuplicateSymbolError as dse:
                                self.report_semantic_error(str(dse), start_id_token.line_number, start_id_token.column_number)
                        finally:
                            self.symbol_table.exit_scope() # Exit temporary scope 1
                    except DuplicateSymbolError as dse:
                         self.logger.error(f"Critical Error during preliminary procedure symbol insertion: {dse}")
                         # Clean up scope if needed
                         if self.symbol_table and self.symbol_table.current_depth != 0:
                             self.logger.warning("Correcting symbol table depth after critical error.")
                             while self.symbol_table.current_depth > 0:
                                 self.symbol_table.exit_scope()
                         raise dse # Re-raise critical error to potentially halt compilation
                    except Exception as e:
                        self.logger.error(f"Non-critical error during preliminary procedure symbol insertion: {e}")
                        # Clean up scope but don't re-raise other exceptions
                        if self.symbol_table and self.symbol_table.current_depth != 0:
                             self.logger.warning("Correcting symbol table depth after error.")
                             while self.symbol_table.current_depth > 0:
                                 self.symbol_table.exit_scope()
            # --- TAC Generation End ---

        elif start_id_token: # Token exists but is not an ID
            start_id_token = Token(lexeme="unknown", 
                                   token_type=self.defs.TokenType.ID, 
                                   line_number=start_id_token.line_number, 
                                   column_number=start_id_token.column_number)
            self.report_error("Expected procedure identifier")
        else: # No token left
             start_id_token = Token(lexeme="unknown", token_type=self.defs.TokenType.ID, line_number=-1, column_number=-1)
             self.report_error("Expected procedure identifier, found end of input")

        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Enter new scope for procedure body *before* parsing Args and Declarations
        if self.symbol_table:
            self.logger.debug("Entering procedure scope.")
            self.symbol_table.enter_scope()

        # Parse the rest of the procedure declaration using Mixin methods
        # --- Call DeclarationsMixin method --- 
        child = self.parseArgs() 
        self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.IS, node)
        
        # --- Call DeclarationsMixin method --- 
        child = self.parseDeclarativePart()
        self._add_child(node, child)
        
        # child = self.parseProcedures() # Assuming this remains or is moved
        # self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.BEGIN, node)
        
        self.logger.debug("Parsing sequence of statements...")
        # --- Call StatementsMixin method --- 
        child = self.parseSeqOfStatements()
        self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.END, node)
        
        # Save the procedure identifier (second occurrence)
        end_id_token = self.current_token # Potentially None
        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Check if the procedure identifiers match
        if end_id_token and start_id_token and start_id_token.lexeme != "unknown" and end_id_token.lexeme != start_id_token.lexeme:
            error_msg = (
                f"Procedure name mismatch: procedure '{start_id_token.lexeme}' ends with '{end_id_token.lexeme}'"
            )
            self.report_error(error_msg)
            line = getattr(end_id_token, 'line_number', -1)
            col  = getattr(end_id_token, 'column_number', -1)
            self.report_semantic_error(error_msg, line, col)
        
        self.match_leaf(self.defs.TokenType.SEMICOLON, node)

        # --- TAC Generation Start --- 
        if self.tac_gen and self.current_procedure_name:
             outermost = (self.symbol_table and self.symbol_table.current_depth == 1) # Depth 1 after exit scope
             self.logger.debug(f" Emitting TAC: endp {self.current_procedure_name}")
             self.tac_gen.emitProcEnd(self.current_procedure_name)

             if outermost:
                 self.logger.info(f" Outermost procedure. Emitting TAC: start {self.current_procedure_name}")
                 self.tac_gen.emitProgramStart(self.current_procedure_name)
             else:
                 self.logger.debug(" Not outermost procedure, skipping 'start' directive.")
        # --- TAC Generation End --- 
        
        # Exit scope and reset procedure context *after* matching the final semicolon
        if self.symbol_table:
             self.logger.debug("Exiting procedure scope.")
             self.symbol_table.exit_scope()
             
        # Reset parser state for the next potential procedure (if any)
        self.current_procedure_name = None
        self.current_procedure_symbol = None
        self.current_local_offset = 0
        self.current_param_offset = 0
        self.logger.debug("Resetting current_procedure_name.")
        self.logger.info(f"Finished parsing procedure: {procedure_name}")
        return node
    
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
