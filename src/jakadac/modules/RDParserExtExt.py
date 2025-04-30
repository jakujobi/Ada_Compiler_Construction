#!/usr/bin/env python3
# RDParserExtended.py
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


class RDParserExtended(RDParser):
    """
    Extended Recursive Descent Parser with grammar rules for statements and expressions,
    and integrated TAC generation.
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
        super().__init__(tokens, defs, stop_on_error, panic_mode_recover, build_parse_tree)
        # Use provided symbol_table or default to a new one
        self.symbol_table: SymbolTable = symbol_table if symbol_table is not None else SymbolTable()
        self.semantic_errors = []
        # Store TAC generator
        self.tac_gen = tac_generator
        self.current_procedure_name: Optional[str] = None
        # Track offsets within the current procedure scope for TAC generation
        self.current_local_offset: int = 0 # Initialized when entering proc scope
        self.current_param_offset: int = 0 # Initialized when entering proc scope
        
    def _add_child(self, parent, child):
        """
        Safely add a child to the parse tree when building it.
        """
        if self.build_parse_tree and parent is not None and child is not None:
            parent.add_child(child)
        
    def parseProg(self):
        """
        Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;
        
        Enhanced to check that the procedure identifier at the end matches the one at the beginning,
        and to emit TAC for procedure boundaries.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Prog")
        else:
            node = None # Initialize node to None for non-tree branch

        self.logger.debug("Parsing Prog")

        # Match procedure keyword
        self.match_leaf(self.defs.TokenType.PROCEDURE, node)

        # Save the procedure identifier (first occurrence)
        procedure_name = "unknown" # Default
        start_id_token = self.current_token # Potentially None if at end of stream

        if start_id_token and start_id_token.token_type == self.defs.TokenType.ID:
            procedure_name = start_id_token.lexeme

            # --- TAC Generation Start ---
            if self.tac_gen:
                # Store current procedure name for use in other methods
                self.current_procedure_name = procedure_name
                self.tac_gen.emitProcStart(procedure_name)
                # Initialize offsets for this procedure's scope
                self.current_local_offset = -2 # Locals start at BP-2
                self.current_param_offset = 4  # Params start at BP+4

                # Insert preliminary procedure symbol if needed
                if self.symbol_table and self.symbol_table.current_depth == 0:
                    try:
                        # Check if already declared in the target scope (scope 1)
                        # Need to temporarily enter scope to check/insert
                        self.symbol_table.enter_scope()
                        try:
                             self.symbol_table.lookup(procedure_name, lookup_current_scope_only=True)
                             # Already exists, potentially from forward declaration
                        except SymbolNotFoundError:
                             # Does not exist, create and insert
                            proc_sym = Symbol(
                                procedure_name,
                                start_id_token, # Known to be non-None here
                                EntryType.PROCEDURE,
                                self.symbol_table.current_depth # Now in scope 1
                            )
                            proc_sym.param_list = []
                            proc_sym.param_modes = {}
                            try:
                                self.symbol_table.insert(proc_sym)
                            except DuplicateSymbolError:
                                # Should not happen due to lookup check, but handle defensively
                                pass
                        finally:
                             # Ensure we exit the temporary scope entry
                            self.symbol_table.exit_scope()
                    except Exception as e:
                        # Catch potential errors during symbol table operations
                        self.logger.error(f"Error during preliminary procedure symbol insertion: {e}")
                        # Ensure scope consistency if an error occurred during enter/exit
                        if self.symbol_table.current_depth != 0:
                             self.logger.warning("Correcting symbol table depth after error.")
                             while self.symbol_table.current_depth > 0:
                                 self.symbol_table.exit_scope()


            # --- TAC Generation End ---

        elif start_id_token: # Token exists but is not an ID
            # Report error but keep a placeholder token
            start_id_token = Token(self.defs.TokenType.ID, "unknown",
                                   start_id_token.line_number,
                                   start_id_token.column_number)
            self.report_error("Expected procedure identifier")
        else: # No token left
             start_id_token = Token(self.defs.TokenType.ID, "unknown", -1, -1) # Dummy token
             self.report_error("Expected procedure identifier, found end of input")


        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)

        # Enter new scope for procedure body *before* parsing Args and Declarations
        if self.symbol_table: self.symbol_table.enter_scope()

        # Parse the rest of the procedure declaration
        child = self.parseArgs()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)

        self.match_leaf(self.defs.TokenType.IS, node)

        child = self.parseDeclarativePart()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)

        # child = self.parseProcedures() # Optional nested procedures
        # if self.build_parse_tree and node is not None and child:
        #     self._add_child(node, child)

        self.match_leaf(self.defs.TokenType.BEGIN, node)

        child = self.parseSeqOfStatements()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)

        self.match_leaf(self.defs.TokenType.END, node)

        # Save the procedure identifier (second occurrence)
        end_id_token = self.current_token # Potentially None

        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)

        # Check if the procedure identifiers match
        # Ensure both tokens exist before comparing lexemes
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
             outermost = (self.symbol_table and self.symbol_table.current_depth == 1)

             self.tac_gen.emitProcEnd(self.current_procedure_name)

             if outermost:
                 self.tac_gen.emitProgramStart(self.current_procedure_name)

        # --- TAC Generation End ---

        # Exit procedure scope before returning
        if self.symbol_table: self.symbol_table.exit_scope()

        # Reset procedure name context after exiting scope
        self.current_procedure_name = None

        return node
    
    def parseSeqOfStatements(self):
        """
        SeqOfStatements -> { Statement ; }*
        Iteratively parse zero or more statements terminated by semicolons until END.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SeqOfStatements")
        else:
            node = None

        self.logger.debug("Parsing SeqOfStatements (iterative)")
        # Parse statements until END is encountered; break on missing semicolon to avoid infinite loop
        while self.current_token and self.current_token.token_type != self.defs.TokenType.END:
            # Parse a single statement (should advance tokens)
            stmt_node = self.parseStatement()
            if self.build_parse_tree and node is not None and stmt_node:
                self._add_child(node, stmt_node)
            # Consume trailing semicolon if present, else break to avoid hang
            if self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            else:
                break
        return node if self.build_parse_tree else None
    
    def parseStatTail(self):
        """
        StatTail -> Statement ; StatTail | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("StatTail")
        else:
            node = None
        
        self.logger.debug("Parsing StatTail")
        
        # Check if we have another statement
        if self.current_token and self.current_token.token_type != self.defs.TokenType.END:
            # Parse the statement
            child = self.parseStatement()
            if self.build_parse_tree and child:
                self._add_child(node, child)
            
            # Match semicolon
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            
            # Parse the rest of statements (StatTail)
            child = self.parseStatTail()
            if self.build_parse_tree and child:
                self._add_child(node, child)
        else:
            # End of statements (ε)
            if self.build_parse_tree and node is not None:
                self._add_child(node, ParseTreeNode("ε"))
        
        return node
    
    def parseStatement(self):
        """
        Statement -> AssignStat | IOStat
        """
        # Two modes: tree-building vs non-tree parse
        if self.build_parse_tree:
            node = ParseTreeNode("Statement")
            self.logger.debug("Parsing Statement (tree)")
            # Assignment or IO
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                child = self.parseAssignStat()
                self._add_child(node, child)
            else:
                child = self.parseIOStat()
                self._add_child(node, child)
            return node
        # Non-tree branch: just consume and semantic-check
        self.logger.debug("Parsing Statement (non-tree)")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            self.parseAssignStat()
        else:
            self.parseIOStat()
        return None
    
    def parseAssignStat(self) -> Union[ParseTreeNode, None]:
        """
        AssignStat -> idt := Expr | ProcCall
        Enhanced to handle procedure calls and generate TAC for assignments.
        Distinguishes assignment from procedure call by looking ahead for '('.
        """
        node = None # Initialize
        if self.build_parse_tree:
            # --- Tree Building ---
            # Requires lookahead to decide which node type to create (AssignStat or ProcCall)
            # Simplified: Assume base grammar handles assignment, ProcCall needs extension
            node = ParseTreeNode("AssignStat") # Default to AssignStat
            self.logger.debug("Parsing AssignStat/ProcCall (tree)")
            # We might need more sophisticated lookahead or backtracking for clean tree building
            # based on whether '(' follows the ID. Let's assume current structure focuses on assignment.
            id_token = self.current_token
            self.match_leaf(self.defs.TokenType.ID, node)
            # Semantic check (original logic)
            if self.symbol_table and id_token and id_token.token_type == self.defs.TokenType.ID:
                try: self.symbol_table.lookup(id_token.lexeme)
                except SymbolNotFoundError:
                     msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                     self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))

            # If it was a procedure call, the tree might be incorrect here.
            # Proper handling would involve checking for '(' after ID and calling parseProcCall for tree building too.

            self.match_leaf(self.defs.TokenType.ASSIGN, node)
            child = self.parseExpr() # Returns ParseTreeNode
            if isinstance(child, ParseTreeNode):
                 self._add_child(node, child)
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing AssignStat/ProcCall (TAC)")

            # Save the current position for lookahead
            saved_token = self.current_token
            saved_index = self.current_index

            # Expect an identifier
            if not self.current_token or self.current_token.token_type != self.defs.TokenType.ID:
                self.report_error("Expected identifier or procedure name at start of statement")
                return None # Cannot proceed

            id_token = self.current_token
            self.advance() # Tentatively consume ID

            # Lookahead to determine if this is an assignment or procedure call
            is_proc_call = self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN

            # Reset position to before the ID
            self.current_index = saved_index
            self.current_token = saved_token

            if is_proc_call:
                # Parse the procedure call
                self.parseProcCall()
            else:
                # This is an assignment
                # Re-consume the ID (already checked it exists)
                id_token = self.current_token
                self.advance()

                dest_place = "ERROR_PLACE" # Default
                # Check if the variable is declared
                if self.symbol_table and id_token:
                    try:
                        symbol = self.symbol_table.lookup(id_token.lexeme)

                        # Check if it's a constant (error)
                        if symbol.entry_type == EntryType.CONSTANT:
                            msg = f"Cannot assign to constant '{id_token.lexeme}'"
                            self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                            # Continue parsing, but dest_place remains error

                        # Check if it's a procedure/function name (error)
                        elif symbol.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                             msg = f"Cannot assign to procedure/function '{id_token.lexeme}'"
                             self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))

                        else:
                             # Get the place for the left-hand side (variable/parameter)
                            dest_place = self.tac_gen.getPlace(symbol)

                    except SymbolNotFoundError:
                        msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                        self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                        dest_place = id_token.lexeme # Use lexeme as fallback place

                else:
                    # Fallback if no symbol table
                    dest_place = id_token.lexeme if id_token else "UNKNOWN_LHS"

                # Match the assignment operator
                if self.current_token and self.current_token.token_type == self.defs.TokenType.ASSIGN:
                     self.advance() # Consume ASSIGN
                else:
                     self.report_error("Expected ':=' for assignment statement")
                     # Attempt to continue by parsing expression

                # Parse the expression and get its place
                source_place = self.parseExpr() # Returns str
                if isinstance(source_place, str) and dest_place != "ERROR_PLACE":
                    # Emit the assignment instruction only if places are valid
                    self.tac_gen.emitAssignment(dest_place, source_place)
                else:
                     self.logger.error("Skipping TAC for assignment due to errors in LHS or RHS.")

            return None # No node returned in TAC mode
            # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing AssignStat (non-tree)")
            # Original non-tree logic (assuming assignment only for simplicity here)
            id_token = self.current_token
            self.match(self.defs.TokenType.ID)
            if self.symbol_table and id_token and id_token.token_type == self.defs.TokenType.ID:
                try: self.symbol_table.lookup(id_token.lexeme)
                except SymbolNotFoundError:
                    msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                    self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
            self.match(self.defs.TokenType.ASSIGN)
            self.parseExpr() # Consumes expression tokens
            return None
            # --- End Non-Tree, Non-TAC ---


    def parseIOStat(self):
        """
        IOStat -> NULL | ε
        """
        # Tree-building branch
        if self.build_parse_tree:
            node = ParseTreeNode("IOStat")
            self.logger.debug("Parsing IOStat (tree)")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.NULL:
                self.match_leaf(self.defs.TokenType.NULL, node)
            else:
                self._add_child(node, ParseTreeNode("ε"))
            return node
        # Non-tree branch
        self.logger.debug("Parsing IOStat (non-tree)")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.NULL:
            self.match(self.defs.TokenType.NULL)
        return None
    
    def parseExpr(self) -> Union[ParseTreeNode, str, None]:
        """
        Expr -> Relation
        Enhanced to generate TAC and return the place where the result is stored.
        """
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Expr")
            self.logger.debug("Parsing Expr (tree)")
            child = self.parseRelation() # Should return ParseTreeNode
            # Ensure child is a ParseTreeNode before adding
            if isinstance(child, ParseTreeNode):
                 self._add_child(node, child)
            else:
                 # This case should ideally not happen if logic is correct
                 self.logger.error("Type mismatch: Expected ParseTreeNode from parseRelation in tree mode.")
            return node
            # --- End Tree Building ---
        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Expr (TAC)")
            # Delegate to parseRelation and return the place (string)
            place = self.parseRelation() # Should return str
            if not isinstance(place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseRelation in TAC mode, got {type(place)}")
                 return "ERROR_PLACE" # Return error placeholder
            return place
            # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Expr (non-tree)")
            self.parseRelation() # Just parse
            return None
            # --- End Non-Tree, Non-TAC ---

    def parseRelation(self) -> Union[ParseTreeNode, str, None]:
        """
        Relation -> SimpleExpr [ relop SimpleExpr ]
        Enhanced for TAC generation (currently only handles SimpleExpr).
        NOTE: Relational operators are not handled in the provided TAC snippets.
              This implementation only handles the SimpleExpr part.
        """
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Relation")
            self.logger.debug("Parsing Relation (tree)")
            child = self.parseSimpleExpr() # Returns ParseTreeNode
            if isinstance(child, ParseTreeNode):
                self._add_child(node, child)
            # TODO: Add parsing for optional relop SimpleExpr part if needed
            return node
            # --- End Tree Building ---
        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Relation (TAC)")
            # Delegate to parseSimpleExpr and return the place
            place = self.parseSimpleExpr() # Returns str
            if not isinstance(place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseSimpleExpr in TAC mode, got {type(place)}")
                 return "ERROR_PLACE"
            # TODO: Add TAC generation for relational operators if needed
            # Example:
            # if self.current_token and self.current_token.token_type == self.defs.TokenType.RELOP:
            #     op_token = self.current_token
            #     self.advance()
            #     right_place = self.parseSimpleExpr()
            #     result_place = self.tac_gen.newTemp()
            #     # emit conditional jump or boolean result based on op_token.lexeme
            #     # e.g., self.tac_gen.emitIfFalseJump(place op right_place, label)
            #     # or self.tac_gen.emitBinaryOp(map_relop(op_token.lexeme), result_place, place, right_place)
            #     place = result_place # update place to the result of relation
            return place
            # --- End TAC Generation ---
        else:
             # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Relation (non-tree)")
            self.parseSimpleExpr()
            # TODO: Parse optional relop SimpleExpr part
            return None
             # --- End Non-Tree, Non-TAC ---


    def parseSimpleExpr(self) -> Union[ParseTreeNode, str, None]:
        """
        SimpleExpr -> Term { addopt Term }*
        Enhanced to generate TAC and return the place where the result is stored.
        """
        node = None # Initialize node
        if self.build_parse_tree:
            # --- Tree Building ---
            # Initialize node here for tree building mode
            node = ParseTreeNode("SimpleExpr")
            self.logger.debug("Parsing SimpleExpr (tree)")
            t = self.parseTerm() # Returns ParseTreeNode
            # Handling MoreTerm equivalent iteratively for tree
            while self.current_token and self.is_addopt(self.current_token.token_type):
                 # Create node for operator, add it, then parse Term
                 # Ensure node exists before adding children
                 if node:
                     op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                     self._add_child(node, op_node)
                 self.advance() # Consume operator
                 next_t = self.parseTerm() # Returns ParseTreeNode
                 # Ensure node exists before adding children
                 if node and isinstance(next_t, ParseTreeNode):
                      self._add_child(node, next_t)
                 else:
                      # If next_t is not a node or node is None, something is wrong, stop iteration
                      break # Stop if parsing fails or node is unexpectedly None
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing SimpleExpr (TAC)")
            left_place = self.parseTerm() # Returns str
            if not isinstance(left_place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseTerm in TAC mode, got {type(left_place)}")
                 return "ERROR_PLACE"

            # Parse additional terms if they exist
            while self.current_token and self.is_addopt(self.current_token.token_type):
                # Save the operator
                op_token = self.current_token
                op = op_token.lexeme
                self.advance()

                # Parse the right term
                right_place = self.parseTerm() # Returns str
                if not isinstance(right_place, str):
                     self.logger.error(f"Type mismatch: Expected str place from parseTerm (right operand) in TAC mode, got {type(right_place)}")
                     return "ERROR_PLACE"


                # Generate a temporary for the result
                result_place = self.tac_gen.newTemp()

                # Map Ada operator to TAC operator
                tac_op = self.tac_gen.map_ada_op_to_tac(op)

                # Emit the binary operation
                self.tac_gen.emitBinaryOp(tac_op, result_place, left_place, right_place)

                # Update left_place for next iteration
                left_place = result_place

            return left_place # Return the final place
            # --- End TAC Generation ---

        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing SimpleExpr (non-tree)")
            self.parseTerm() # Consume Term
            while self.current_token and self.is_addopt(self.current_token.token_type):
                 self.advance() # Consume operator
                 self.parseTerm() # Consume next Term
            return None
            # --- End Non-Tree, Non-TAC ---

    def parseTerm(self) -> Union[ParseTreeNode, str, None]:
        """
        Term -> Factor { mulopt Factor }*
        Enhanced to generate TAC and return the place where the result is stored.
        """
        node = None # Initialize node
        if self.build_parse_tree:
            # --- Tree Building ---
            # Initialize node here for tree building mode
            node = ParseTreeNode("Term")
            self.logger.debug("Parsing Term (tree)")
            f = self.parseFactor() # Returns ParseTreeNode
             # Handling MoreFactor equivalent iteratively for tree
            while self.current_token and self.is_mulopt(self.current_token.token_type):
                 # Ensure node exists before adding children
                 if node:
                      op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                      self._add_child(node, op_node)
                 self.advance() # Consume operator
                 next_f = self.parseFactor() # Returns ParseTreeNode
                 # Ensure node exists before adding children
                 if node and isinstance(next_f, ParseTreeNode):
                      self._add_child(node, next_f)
                 else:
                      # If next_f is not a node or node is None, something is wrong, stop iteration
                      break # Stop if parsing fails or node is unexpectedly None
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
             # --- TAC Generation ---
            self.logger.debug("Parsing Term (TAC)")
            left_place = self.parseFactor() # Returns str
            if not isinstance(left_place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseFactor in TAC mode, got {type(left_place)}")
                 return "ERROR_PLACE"

            # Parse additional factors if they exist
            while self.current_token and self.is_mulopt(self.current_token.token_type):
                # Save the operator
                op_token = self.current_token
                op = op_token.lexeme
                self.advance()
                # Parse the right factor
                right_place = self.parseFactor() # Returns str
                if not isinstance(right_place, str):
                     self.logger.error(f"Type mismatch: Expected str place from parseFactor (right operand) in TAC mode, got {type(right_place)}")
                     return "ERROR_PLACE"

                # Generate a temporary for the result
                result_place = self.tac_gen.newTemp()
                # Map Ada operator to TAC operator
                tac_op = self.tac_gen.map_ada_op_to_tac(op)
                # Emit the binary operation
                self.tac_gen.emitBinaryOp(tac_op, result_place, left_place, right_place)
                # Update left_place for next iteration
                left_place = result_place

            return left_place # Return the final place
             # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Term (non-tree)")
            self.parseFactor() # Consume Factor
            while self.current_token and self.is_mulopt(self.current_token.token_type): # Consume MoreFactor equivalent
                 self.advance() # Consume operator
                 self.parseFactor() # Consume next Factor
            return None
            # --- End Non-Tree, Non-TAC ---


    def parseFactor(self) -> Union[ParseTreeNode, str, None]:
        """
        Factor -> idt | numt | ( Expr ) | not Factor | signopt Factor
        Enhanced to generate TAC and return the place where the result is stored.
        Also performs semantic checking for undeclared variables.
        """
        node = None # Initialize
        place = "ERROR_PLACE" # Default place for TAC

        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Factor")
            self.logger.debug("Parsing Factor (tree)")
            # Keep original tree building logic, ensure recursive calls return ParseTreeNode
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                id_token = self.current_token # Save for semantic check if needed later
                self.match_leaf(self.defs.TokenType.ID, node)
                # Perform semantic check here if desired for tree mode too
                if self.symbol_table:
                    try: self.symbol_table.lookup(id_token.lexeme)
                    except SymbolNotFoundError: # Be specific
                        msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                        self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))

            elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                self.match_leaf(self.current_token.token_type, node)

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                child = self.parseExpr() # Returns ParseTreeNode
                if isinstance(child, ParseTreeNode): self._add_child(node, child)
                self.match_leaf(self.defs.TokenType.RPAREN, node)

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
                self.match_leaf(self.defs.TokenType.NOT, node)
                child = self.parseFactor() # Returns ParseTreeNode
                if isinstance(child, ParseTreeNode): self._add_child(node, child)

            elif self.current_token and self.is_signopt(self.current_token.token_type):
                self.match_leaf(self.current_token.token_type, node)
                child = self.parseFactor() # Returns ParseTreeNode
                if isinstance(child, ParseTreeNode): self._add_child(node, child)

            else:
                self.report_error(f"Expected an identifier, number, '(', 'not', or sign")
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Factor (TAC)")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                id_token = self.current_token
                self.advance() # Use advance for non-leaf

                if self.symbol_table:
                    try:
                        symbol = self.symbol_table.lookup(id_token.lexeme)
                        place = self.tac_gen.getPlace(symbol) # Get TAC place
                    except SymbolNotFoundError:
                        error_msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                        self.report_semantic_error(error_msg, getattr(id_token, 'line_number', -1), getattr(id_token, 'column_number', -1))
                        place = id_token.lexeme # Use lexeme as placeholder place
                else:
                     place = id_token.lexeme # Fallback if no symbol table

            elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                place = self.current_token.lexeme # Literals are their own place
                self.advance()

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.advance() # Consume LPAREN
                place = self.parseExpr() # Returns str (place)
                if not self.current_token or self.current_token.token_type != self.defs.TokenType.RPAREN:
                     self.report_error("Expected ')'")
                else:
                     self.advance() # Consume RPAREN

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
                self.advance() # Consume NOT
                operand_place = self.parseFactor() # Returns str
                if isinstance(operand_place, str):
                     result_place = self.tac_gen.newTemp()
                     self.tac_gen.emitUnaryOp("NOT", result_place, operand_place)
                     place = result_place
                else:
                     place = "ERROR_PLACE" # Error in operand

            elif self.current_token and self.is_signopt(self.current_token.token_type):
                sign = self.current_token.lexeme
                self.advance() # Consume sign
                operand_place = self.parseFactor() # Returns str

                if isinstance(operand_place, str):
                     if sign == '+':
                        place = operand_place # Unary plus is identity
                     else: # Unary minus
                        result_place = self.tac_gen.newTemp()
                        self.tac_gen.emitUnaryOp("UMINUS", result_place, operand_place)
                        place = result_place
                else:
                     place = "ERROR_PLACE" # Error in operand

            else:
                self.report_error(f"Expected an identifier, number, '(', 'not', or sign")
                # place remains "ERROR_PLACE"

            return place # Return the place string
            # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Factor (non-tree)")
            # Keep original non-tree logic (just consume tokens)
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                 id_token = self.current_token # Save for semantic check
                 self.match(self.defs.TokenType.ID)
                 if self.symbol_table: # Optional semantic check
                     try: self.symbol_table.lookup(id_token.lexeme)
                     except SymbolNotFoundError:
                         msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                         self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))

            elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                self.match(self.current_token.token_type)

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match(self.defs.TokenType.LPAREN)
                self.parseExpr() # Recursive call returns None here
                self.match(self.defs.TokenType.RPAREN)

            elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
                self.match(self.defs.TokenType.NOT)
                self.parseFactor() # Recursive call returns None

            elif self.current_token and self.is_signopt(self.current_token.token_type):
                self.match(self.current_token.token_type)
                self.parseFactor() # Recursive call returns None

            else:
                 self.report_error(f"Expected an identifier, number, '(', 'not', or sign")

            return None # Return None for non-tree, non-TAC branch
            # --- End Non-Tree, Non-TAC ---

    def is_addopt(self, token_type):
        """
        Check if a token type is an addopt operator (+ | - | or)
        """
        # Lexical ADDOP covers + and -, reserved OR covers 'or'
        return token_type in {
            self.defs.TokenType.ADDOP,
            self.defs.TokenType.OR
        }
    
    def is_mulopt(self, token_type):
        """
        Check if a token type is a mulopt operator (* | / | mod | rem | and)
        """
        # Lexical MULOP covers *, /; specific types for mod, rem; reserved AND for 'and'
        return token_type in {
            self.defs.TokenType.MULOP,
            self.defs.TokenType.MOD,
            self.defs.TokenType.REM,
            self.defs.TokenType.AND
        }
    
    def is_signopt(self, token_type):
        """
        Check if a token type is a signopt operator (+ | -)
        """
        # Sign operators are lexed as ADDOP
        return token_type == self.defs.TokenType.ADDOP
    
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
        self.logger.error(f"Semantic error at line {line}, column {column}: {message}")
    
    def parse(self) -> bool:
        """
        Override parse to allow multiple top-level procedures.
        """
        if self.build_parse_tree:
            root = ParseTreeNode("ProgramList")
        else:
            root = None # Initialize root to None for non-tree branch
        self.logger.debug("Starting extended parse for multiple procedures.")
        # Parse all top-level procedures
        while self.current_token and self.current_token.token_type == self.defs.TokenType.PROCEDURE:
            child = self.parseProg()
            # Only add child if root exists (i.e., building parse tree)
            if root is not None and child:
                root.add_child(child)
        # After procedures, expect EOF
        if self.current_token and self.current_token.token_type != self.defs.TokenType.EOF:
            self.report_error("Extra tokens found after program end.")
        if self.build_parse_tree:
            self.parse_tree_root = root
        return len(self.errors) == 0

    def parseDeclarativePart(self):
        """
        DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε
        Also insert each declared identifier into the symbol table with offset calculation for TAC.
        """
        node = None # Initialize node
        if self.build_parse_tree:
            node = ParseTreeNode("DeclarativePart")

        # Check if there's a declaration (starts with ID)
        is_declaration = self.current_token and self.current_token.token_type == self.defs.TokenType.ID

        if is_declaration:
            self.logger.debug("Parsing DeclarativePart (Declaration)")

            if self.build_parse_tree and node:
                 # Tree building mode
                id_list_node = self.parseIdentifierList()
                assert id_list_node is not None
                node.add_child(id_list_node)

                self.match_leaf(self.defs.TokenType.COLON, node)
                type_mark_node = self.parseTypeMark()
                assert type_mark_node is not None
                node.add_child(type_mark_node)
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)

                # Semantic Action
                if self.symbol_table:
                     # Simplified: Infer type from the first child of TypeMark if it's a type keyword token
                     var_type: Optional[VarType] = None
                     const_value: Optional[Any] = None
                     type_token_node = None
                     if type_mark_node.children:
                        type_token_node = type_mark_node.children[0] # Assuming structure like TypeMark -> INTEGERT

                     if type_token_node and type_token_node.token:
                         type_lexeme = type_token_node.token.lexeme.upper()
                         if type_lexeme == 'INTEGER': var_type = VarType.INT
                         elif type_lexeme in ['REAL', 'FLOAT']: var_type = VarType.FLOAT
                         elif type_lexeme == 'CHAR': var_type = VarType.CHAR
                         # Add constant handling if parseTypeMark structure allows easy detection
                         # ...

                     entry_kind = EntryType.VARIABLE # Assume variable unless constant detected


                     for id_leaf in id_list_node.find_children_by_name("ID"):
                         if id_leaf.token:
                            sym = Symbol(
                                id_leaf.token.lexeme,
                                id_leaf.token,
                                entry_kind, # Update if constant detected
                                self.symbol_table.current_depth
                            )
                            if self.tac_gen and entry_kind == EntryType.VARIABLE:
                                # Ensure var_type is not None before using it
                                if var_type is not None:
                                     var_size = TypeUtils.get_type_size(var_type)
                                     sym.set_variable_info(var_type, self.current_local_offset, var_size)
                                     self.current_local_offset -= var_size
                                else:
                                     # Handle case where type is unknown - use default? report error?
                                     self.logger.warning(f"Unknown variable type for {id_leaf.token.lexeme}, using default size/offset.")
                                     var_size = 2 # Default size
                                     # Cannot call set_variable_info without a valid VarType
                                     # Maybe store raw offset/size or skip TAC info?
                                     # sym.offset = self.current_local_offset # Example direct storage
                                     # sym.size = var_size
                                     # self.current_local_offset -= var_size
                                     pass # Skip TAC info if type unknown for now
                            # Add constant info setting here if applicable
                            # elif self.tac_gen and entry_kind == EntryType.CONSTANT:
                            #    if var_type is not None:
                            #        sym.set_constant_info(var_type, const_value)

                            try:
                                self.symbol_table.insert(sym)
                            except DuplicateSymbolError as e:
                                self.report_semantic_error(
                                    f"Duplicate symbol declaration: '{e.name}' at depth {e.depth}",
                                    getattr(id_leaf.token, 'line_number', -1),
                                    getattr(id_leaf.token, 'column_number', -1)
                                )

                 # Recursively parse further declarations
                next_node = self.parseDeclarativePart()
                if next_node and node:
                    if not (len(next_node.children) == 1 and next_node.children[0].name == "ε"):
                         node.add_child(next_node)

            elif self.tac_gen:
                 # TAC generation mode (not building tree)
                 id_tokens = self._parseIdentifierListTokens()
                 self.match(self.defs.TokenType.COLON)
                 var_type, const_value = self._parseTypeMarkInfo() # Get type info
                 self.match(self.defs.TokenType.SEMICOLON)

                 if self.symbol_table:
                    entry_kind = EntryType.CONSTANT if const_value is not None else EntryType.VARIABLE

                    for id_token in id_tokens:
                         sym = Symbol(
                            id_token.lexeme,
                            id_token,
                            entry_kind,
                            self.symbol_table.current_depth
                         )
                         if entry_kind == EntryType.VARIABLE:
                            # Ensure var_type is valid before calling set_variable_info
                            if var_type is not None:
                                var_size = TypeUtils.get_type_size(var_type)
                                sym.set_variable_info(var_type, self.current_local_offset, var_size)
                                self.current_local_offset -= var_size
                            else:
                                # Handle unknown type case for TAC gen
                                self.logger.warning(f"Unknown variable type for {id_token.lexeme} in TAC gen mode.")
                                pass # Skip setting offset/size info for TAC

                         elif entry_kind == EntryType.CONSTANT:
                            # Ensure const_type (var_type) is valid before calling set_constant_info
                            if var_type is not None:
                                sym.set_constant_info(var_type, const_value)
                            else:
                                # Handle unknown type case for constant
                                self.logger.warning(f"Unknown constant type for {id_token.lexeme} in TAC gen mode.")
                                pass # Skip setting const info? or use raw value?

                         try:
                            self.symbol_table.insert(sym)
                         except DuplicateSymbolError as e:
                            self.report_semantic_error(
                                f"Duplicate symbol declaration: '{e.name}' at depth {e.depth}",
                                getattr(id_token, 'line_number', -1),
                                getattr(id_token, 'column_number', -1)
                            )
                 # Recursively parse
                 self.parseDeclarativePart()

            else:
                 # Non-tree, non-TAC mode: Just parse without actions
                 self._parseIdentifierListTokens()
                 self.match(self.defs.TokenType.COLON)
                 self._parseTypeMarkInfo()
                 self.match(self.defs.TokenType.SEMICOLON)
                 self.parseDeclarativePart()

        else:
            # Epsilon case
            self.logger.debug("Parsing DeclarativePart (ε)")
            if self.build_parse_tree and node:
                node.add_child(ParseTreeNode("ε"))

        return node if self.build_parse_tree else None

    # Helper to parse IdentifierList returning tokens
    def _parseIdentifierListTokens(self) -> List[Token]:
        tokens = []
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            tokens.append(self.current_token)
            self.advance() # Use advance as we are not building tree here
            while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
                self.advance() # Skip comma
                if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                    tokens.append(self.current_token)
                    self.advance()
                else:
                    self.report_error("Expected identifier after comma in list")
                    break # Avoid infinite loop on error
        else:
             self.report_error("Expected identifier at start of list")
        return tokens

    # Helper to parse TypeMark returning type info (VarType or None for constant)
    # Returns tuple: (Optional[VarType], Optional[Any])
    def _parseTypeMarkInfo(self) -> tuple[Optional[VarType], Optional[Any]]:
         var_type: Optional[VarType] = None # Explicitly type hint
         const_value: Optional[Any] = None
         if self.current_token and self.current_token.token_type in {
             self.defs.TokenType.INTEGERT,
             self.defs.TokenType.REALT,
             self.defs.TokenType.CHART,
             self.defs.TokenType.FLOAT # Assuming FLOAT maps to VarType.FLOAT/REAL
         }:
             # Map token type to VarType
             type_lexeme = self.current_token.lexeme.upper()
             if type_lexeme == 'INTEGER': var_type = VarType.INT
             elif type_lexeme in ['REAL', 'FLOAT']: var_type = VarType.FLOAT # or REAL
             elif type_lexeme == 'CHAR': var_type = VarType.CHAR
             # Add mappings for BOOLEAN etc. if needed
             self.advance()
         elif self.current_token and self.current_token.token_type == self.defs.TokenType.CONSTANT:
             self.advance() # Consume CONSTANT
             if self.current_token and self.current_token.token_type == self.defs.TokenType.ASSIGN:
                 self.advance() # Consume :=
                 # Parse value - assuming simple NUM/REAL for now
                 if self.current_token and self.current_token.token_type == self.defs.TokenType.NUM:
                     const_value = int(self.current_token.lexeme)
                     var_type = VarType.INT # Infer type from value
                     self.advance()
                 elif self.current_token and self.current_token.token_type == self.defs.TokenType.REAL:
                     const_value = float(self.current_token.lexeme)
                     var_type = VarType.FLOAT # Infer type from value
                     self.advance()
                 else:
                      self.report_error("Expected numerical literal after ':=' for constant")
             else:
                  self.report_error("Expected ':=' after CONSTANT")
         else:
             self.report_error("Expected a type (INTEGER, REAL, CHAR, FLOAT) or CONSTANT declaration.")
         return var_type, const_value

    def parseArgs(self):
        """
        Args -> ( ArgList ) | ε
        Enhanced to calculate and store offsets for parameters during TAC generation.
        """
        node = None
        if self.build_parse_tree:
            node = ParseTreeNode("Args")
            # --- Tree Building Logic ---
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                child = self.parseArgList() # Original ArgList parser
                if child and node:
                    node.add_child(child)
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            else:
                # Epsilon case for tree
                if node:
                    node.add_child(ParseTreeNode("ε"))
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation Logic ---
            self.logger.debug("Parsing Args (TAC)")
            param_info_list = [] # To store [(name, token, type, mode), ...]
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.advance() # Consume LPAREN
                # Parse using the helper that returns info
                param_info_list = self._parseArgListInfo()
                if not self.current_token or self.current_token.token_type != self.defs.TokenType.RPAREN:
                    self.report_error("Expected ')' after parameter list")
                else:
                    self.advance() # Consume RPAREN

                # --- Semantic Action: Insert Parameter Symbols with Offsets ---
                if self.symbol_table and self.current_procedure_name:
                    try:
                         # Retrieve the procedure symbol (should exist from parseProg)
                         # It's in the outer scope (depth - 1), but args/locals go in current scope
                         # We need to update the symbol in the outer scope? No, parameters belong to inner scope.
                         # Let's lookup in the current scope (procedure's scope)
                         # If preliminary symbol was added, it needs updating?
                         # Let's assume we insert params into the current scope (proc scope)
                         # And we update the proc symbol's param_list/modes later if needed

                         # Use the param offset tracker initialized in parseProg
                         current_param_offset = self.current_param_offset

                         # Process parameters (consider stack push order - often right-to-left)
                         # Let's calculate offsets left-to-right based on declaration order first.
                         # The CALLER (parseProcCall) will handle push order.
                         proc_symbol_params = []
                         proc_symbol_modes = {}

                         for param_name, param_token, param_type, param_mode in param_info_list:
                             if param_type is None:
                                 # Skip symbol creation if type unknown? Or create with placeholder?
                                 self.logger.error(f"Skipping parameter '{param_name}' due to unknown type.")
                                 continue

                             param_size = TypeUtils.get_type_size(param_type)

                             param_symbol = Symbol(
                                 param_name,
                                 param_token,
                                 EntryType.PARAMETER,
                                 self.symbol_table.current_depth # Params are in the proc's scope
                             )

                             # Assign offset and update next offset
                             param_symbol.set_variable_info(param_type, current_param_offset, param_size)
                             current_param_offset += param_size

                             # Add to lists for potentially updating the main proc symbol later
                             proc_symbol_params.append(param_symbol)
                             proc_symbol_modes[param_name] = param_mode

                             # Insert into symbol table (current scope)
                             try:
                                 self.symbol_table.insert(param_symbol)
                             except DuplicateSymbolError as e:
                                 self.report_semantic_error(
                                     f"Duplicate parameter name: '{e.name}'",
                                     getattr(param_token, 'line_number', -1),
                                     getattr(param_token, 'column_number', -1)
                                 )

                         # Update the main procedure symbol (if needed and exists) with param info
                         # This might be complex if proc symbol is in outer scope.
                         # Alternative: Store param info separately associated with proc name.
                         # For now, let's assume Symbol Table handles relationships or
                         # we update the proc symbol later if necessary.

                         # Update the parser's offset tracker state
                         self.current_param_offset = current_param_offset

                    except SymbolNotFoundError:
                         self.logger.error(f"Procedure symbol '{self.current_procedure_name}' not found for parameter processing.")
                    except Exception as e:
                         self.logger.error(f"Error processing parameters for TAC: {e}")
                # --- End Semantic Action ---
            else:
                # Epsilon case for TAC gen (no parentheses)
                self.logger.debug("Parsing Args (ε TAC)")
            # --- End TAC Generation ---

        else:
            # --- Non-Tree, Non-TAC Parsing ---
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match(self.defs.TokenType.LPAREN)
                self.parseArgList() # Original parser consumes tokens
                self.match(self.defs.TokenType.RPAREN)
            # Epsilon case requires no action
            # --- End Non-Tree, Non-TAC ---


        return node # Return node only if building tree

    # Helper to parse Mode returning ParameterMode enum
    def _parseModeInfo(self) -> ParameterMode:
        mode = ParameterMode.IN # Default mode is IN
        if self.current_token:
            if self.current_token.token_type == self.defs.TokenType.IN:
                mode = ParameterMode.IN
                self.advance()
            elif self.current_token.token_type == self.defs.TokenType.OUT:
                mode = ParameterMode.OUT
                self.advance()
            elif self.current_token.token_type == self.defs.TokenType.INOUT:
                mode = ParameterMode.INOUT
                self.advance()
            # Else: Epsilon case, mode remains IN
        return mode

    # Helper to parse one argument spec: Mode IdentifierList : TypeMark
    # Returns: List of tuples: [(name: str, token: Token, type: VarType, mode: ParameterMode)]
    def _parseOneArgSpecInfo(self) -> List[tuple[str, Token, Optional[VarType], ParameterMode]]:
        arg_info_list = []
        mode = self._parseModeInfo()
        id_tokens = self._parseIdentifierListTokens()
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.COLON:
            self.report_error("Expected ':' after identifier list in parameter specification")
            return arg_info_list # Return empty on error
        self.advance() # Consume COLON

        var_type, const_value = self._parseTypeMarkInfo() # TypeMark determines type
        if const_value is not None:
            self.report_error("Constant declaration not allowed in parameter specification")
            # Continue processing with the inferred type if available

        for id_token in id_tokens:
             if var_type is None:
                 # Report error if type couldn't be determined
                 self.report_error(f"Could not determine type for parameter '{id_token.lexeme}'")
             # Add tuple even if type is None, handle downstream
             arg_info_list.append((id_token.lexeme, id_token, var_type, mode))

        return arg_info_list

    # Helper to parse ArgList returning combined info
    def _parseArgListInfo(self) -> List[tuple[str, Token, Optional[VarType], ParameterMode]]:
        all_args_info = []
        # Parse first spec
        all_args_info.extend(self._parseOneArgSpecInfo())
        # Parse MoreArgs ( ; ArgList )
        while self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
            self.advance() # Consume SEMICOLON
            # Check if another spec follows or if it's just a trailing semicolon before RPAREN
            if self.current_token and self.current_token.token_type != self.defs.TokenType.RPAREN:
                 all_args_info.extend(self._parseOneArgSpecInfo())
            else:
                 # Trailing semicolon is technically allowed by some interpretations,
                 # but often considered an error or indicates an empty spec.
                 # Ada grammar usually expects a spec after ';'. Let's report potential issue.
                 if self.current_token and self.current_token.token_type != self.defs.TokenType.RPAREN:
                      self.report_error("Expected parameter specification after ';'")
                 break # Exit loop if no more specs expected
        return all_args_info

    # --- New Methods for Procedure Calls (TAC Generation) ---

    def parseParams(self) -> List[str]:
        """
        Params -> Expr { , Expr }* | ε
        Parse actual parameters in a procedure call for TAC generation.
        Returns a list of places (str) where each parameter's value resides.
        """
        self.logger.debug("Parsing Params (TAC)")
        param_places = []

        # Check for empty parameter list (next token is RPAREN)
        if self.current_token and self.current_token.token_type == self.defs.TokenType.RPAREN:
            return param_places

        # Parse the first parameter expression
        place = self.parseExpr() # Should return str
        if isinstance(place, str):
             param_places.append(place)
        else:
             self.report_error("Expected expression for parameter")
             param_places.append("ERROR_PARAM_PLACE") # Add placeholder on error

        # Parse subsequent parameters separated by commas
        while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
            self.advance() # Consume comma
            place = self.parseExpr() # Parse next expression
            if isinstance(place, str):
                 param_places.append(place)
            else:
                 self.report_error("Expected expression after comma for parameter")
                 param_places.append("ERROR_PARAM_PLACE") # Add placeholder

        return param_places


    def parseProcCall(self) -> None:
        """
        ProcCall -> idt ( Params )
        Implementation of procedure call parsing with TAC generation.
        Assumes called only when tac_gen is True.
        """
        self.logger.debug("Parsing ProcCall (TAC)")
        if not self.tac_gen: # Should not happen based on call site, but check
             self.logger.warning("parseProcCall invoked without active TAC generator")
             # Consume tokens without generating TAC? Or raise error?
             # Let's just consume for now to avoid infinite loops
             self.match(self.defs.TokenType.ID)
             self.match(self.defs.TokenType.LPAREN)
             # Skip parsing params if not generating TAC
             while self.current_token and self.current_token.token_type != self.defs.TokenType.RPAREN and self.current_token.token_type != self.defs.TokenType.EOF:
                  self.advance()
             self.match(self.defs.TokenType.RPAREN)
             return

        # Get the procedure name
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.ID:
            self.report_error("Expected procedure identifier for call")
            return

        proc_name = self.current_token.lexeme
        proc_token = self.current_token
        self.advance() # Consume ID

        # Look up the procedure in the symbol table
        proc_symbol: Optional[Symbol] = None
        formal_params: List[Symbol] = []
        param_modes: Dict[str, ParameterMode] = {}
        if self.symbol_table:
            try:
                proc_symbol = self.symbol_table.lookup(proc_name)
                if proc_symbol.entry_type not in (EntryType.PROCEDURE, EntryType.FUNCTION):
                     msg = f"Identifier '{proc_name}' is not a procedure or function"
                     self.report_semantic_error(msg, getattr(proc_token,'line_number',-1), getattr(proc_token,'column_number',-1))
                     proc_symbol = None # Treat as undeclared if wrong type
                else:
                     # Get formal parameter info if available
                     formal_params = proc_symbol.param_list or []
                     param_modes = proc_symbol.param_modes or {}
            except SymbolNotFoundError:
                msg = f"Undeclared procedure/function '{proc_name}'"
                self.report_semantic_error(msg, getattr(proc_token,'line_number',-1), getattr(proc_token,'column_number',-1))
                proc_symbol = None # Mark as not found

        # Match the opening parenthesis
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.LPAREN:
             self.report_error("Expected '(' after procedure name for call")
             # Attempt to recover by skipping until possible ')' or ';' ? Difficult. Stop processing call.
             return
        self.advance() # Consume LPAREN

        # Parse the actual parameters -> List[str] (places)
        actual_param_places = self.parseParams()

        # Match the closing parenthesis
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.RPAREN:
             self.report_error("Expected ')' after parameters in procedure call")
             # Attempt to recover? Stop processing call.
             return
        self.advance() # Consume RPAREN

        # --- Emit TAC for Parameter Pushing ---
        num_actual = len(actual_param_places)
        num_formal = len(formal_params)

        if num_actual != num_formal:
            self.report_semantic_error(
                f"Procedure '{proc_name}' call parameter count mismatch: Expected {num_formal}, got {num_actual}",
                getattr(proc_token, 'line_number', -1),
                getattr(proc_token, 'column_number', -1)
            )
            # Don't emit push/call if parameter count mismatch
        else:
            # Push parameters (consider order - typically right-to-left for stack)
            # Iterate through actual places and formal param info together
            push_order = list(zip(formal_params, actual_param_places))
            for formal_param_symbol, actual_param_place in reversed(push_order):
                # Get the mode for this formal parameter
                mode = param_modes.get(formal_param_symbol.name, ParameterMode.IN) # Default IN

                # Perform type checking between actual_param_place and formal_param_symbol.var_type? (Requires type info on places)
                # TODO: Add type checking if types are tracked for temporaries/expressions

                # Emit the push instruction based on mode
                self.tac_gen.emitPush(actual_param_place, mode)

            # Emit the call instruction
            self.tac_gen.emitCall(proc_name)

        # --- End TAC Emission ---
