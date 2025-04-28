#!/usr/bin/env python3
# RDParserA7.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-27
# Version: 1.0
"""
Recursive Descent Parser for Assignment 7: Three Address Code Generation
"""

import os
import sys
from typing import List, Optional, Tuple, Union
import traceback


from .RDParser import RDParser, ParseTreeNode
from .Token import Token
from .Definitions import Definitions
from .Logger import Logger
from .SymTable import SymbolTable, Symbol, EntryType, DuplicateSymbolError, VarType, ParameterMode
from .TACGenerator import TACGenerator

# Define type sizes for memory allocation (in bytes)
TYPE_SIZES = {
    VarType.INT: 2,     # Integer is 2 bytes
    VarType.FLOAT: 4,   # Float is 4 bytes 
    VarType.REAL: 4,    # REAL is an alias for FLOAT
    VarType.BOOLEAN: 1, # Boolean is 1 byte
    VarType.CHAR: 1     # Char is 1 byte
}

class RDParserA7(RDParser):
    """
    Extended Recursive Descent Parser with grammar rules for statements and expressions
    """
    
    def __init__(self, tokens, defs, symbol_table=None, tac_generator=None, stop_on_error=False, panic_mode_recover=False, build_parse_tree=False):
        """
        Initialize the extended parser.
        
        Parameters:
            tokens (List[Token]): The list of tokens from the lexical analyzer.
            defs (Definitions): The definitions instance from the lexical analyzer.
            symbol_table (AdaSymbolTable): Symbol table for semantic checking.
            tac_generator (TACGenerator): The three-address code generator.
            stop_on_error (bool): Whether to stop on error.
            panic_mode_recover (bool): Whether to attempt recovery from errors.
            build_parse_tree (bool): Whether to build a parse tree.
        """
        super().__init__(tokens, defs, stop_on_error, panic_mode_recover, build_parse_tree)
        # Use provided symbol_table or default to a new one
        self.symbol_table: SymbolTable = symbol_table if symbol_table is not None else SymbolTable()
        self.semantic_errors = []
        
        # Store the TAC generator reference
        self.tac_generator = tac_generator
        
        # Variables for offset calculation
        self.current_local_offset = None  # Will be set to -2 for each procedure
        self.current_param_offset = None  # Will be set to +4 for each procedure
        
    def _add_child(self, parent, child):
        """
        Safely add a child to the parse tree when building it.
        """
        if self.build_parse_tree and parent is not None and child is not None:
            parent.add_child(child)
        
    def parseProg(self):
        """
        Prog -> procedure idt Args is DeclarativePart Procedures begin SeqOfStatements end idt;
        
        Enhanced to check that the procedure identifier at the end matches the one at the beginning.
        Also calculates and tracks memory offsets for parameters and local variables.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Prog")
        else:
            node = None
        
        self.logger.debug("Parsing Prog")
        
        # Match procedure keyword
        self.match_leaf(self.defs.TokenType.PROCEDURE, node)
        
        # Save the procedure identifier (first occurrence)
        if self.current_token is not None:
            start_id_token = self.current_token
            procedure_name = self.current_token.lexeme
        else:
            start_id_token = None
            procedure_name = "unknown"
        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Create procedure symbol for current depth to track sizes
        proc_symbol = None
        if start_id_token:
            try:
                proc_symbol = self.symbol_table.lookup(start_id_token.lexeme)
            except Exception:
                self.logger.debug(f"Could not find procedure symbol for {start_id_token.lexeme}")
        
        # Initialize offset tracking for parameters (starting at +4)
        self.current_param_offset = 4
        
        # Parse the rest of the procedure declaration
        child = self.parseArgs()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
        # Store total parameter size on procedure symbol
        if proc_symbol:
            param_size = self.current_param_offset - 4  # Calculate total bytes used
            proc_symbol.param_size = param_size
            self.logger.debug(f"Set procedure {procedure_name} param_size to {param_size}")
        
        self.match_leaf(self.defs.TokenType.IS, node)
        
        # Enter new scope for procedure body
        if self.symbol_table: self.symbol_table.enter_scope()
        
        # Initialize offset tracking for local variables (starting at -2)
        self.current_local_offset = -2
        
        child = self.parseDeclarativePart()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
        # Store total local variable size on procedure symbol
        if proc_symbol:
            local_size = abs(self.current_local_offset) - 2  # Calculate total bytes used by locals
            proc_symbol.local_size = local_size
            self.logger.debug(f"Set procedure {procedure_name} local_size to {local_size}")
        
        child = self.parseProcedures()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.BEGIN, node)
        
        child = self.parseSeqOfStatements()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.END, node)
        
        # Save the procedure identifier (second occurrence)
        end_id_token = self.current_token
        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Check if the procedure identifiers match
        if end_id_token and start_id_token and end_id_token.lexeme != start_id_token.lexeme:
            error_msg = (
                f"Procedure name mismatch: procedure '{start_id_token.lexeme}' ends with '{end_id_token.lexeme}'"
            )
            self.report_error(error_msg)
            line = getattr(end_id_token, 'line_number', -1)
            col  = getattr(end_id_token, 'column_number', -1)
            self.report_semantic_error(error_msg, line, col)
        
        self.match_leaf(self.defs.TokenType.SEMICOLON, node)
        
        # Exit procedure scope before returning
        if self.symbol_table: self.symbol_table.exit_scope()
        
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
    
    def parseAssignStat(self):
        """
        AssignStat -> idt := Expr
        
        Also performs semantic checking for undeclared variables.
        """
        # Two modes: tree-building vs non-tree parse
        if self.build_parse_tree:
            node = ParseTreeNode("AssignStat")
            self.logger.debug("Parsing AssignStat (tree)")
            id_token = self.current_token
            self.match_leaf(self.defs.TokenType.ID, node)
            # semantic check
            if self.symbol_table and id_token and id_token.token_type == self.defs.TokenType.ID:
                try:
                    self.symbol_table.lookup(id_token.lexeme)
                except Exception:
                    msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                    self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
            self.match_leaf(self.defs.TokenType.ASSIGN, node)
            child = self.parseExpr()
            self._add_child(node, child)
            return node
        # Non-tree branch
        self.logger.debug("Parsing AssignStat (non-tree)")
        id_token = self.current_token
        self.match(self.defs.TokenType.ID)
        if self.symbol_table and id_token and id_token.token_type == self.defs.TokenType.ID:
            try: self.symbol_table.lookup(id_token.lexeme)
            except Exception:
                msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
        self.match(self.defs.TokenType.ASSIGN)
        self.parseExpr()
        return None
    
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
    
    def parseExpr(self):
        """
        Expr -> Relation
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Expr")
            self.logger.debug("Parsing Expr (tree)")
            child = self.parseRelation()
            self._add_child(node, child)
            return node
        # Non-tree
        self.logger.debug("Parsing Expr (non-tree)")
        self.parseRelation()
        return None
    
    def parseRelation(self):
        """
        Relation -> SimpleExpr
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Relation")
            self.logger.debug("Parsing Relation (tree)")
            child = self.parseSimpleExpr()
            self._add_child(node, child)
            return node
        # Non-tree
        self.logger.debug("Parsing Relation (non-tree)")
        self.parseSimpleExpr()
        return None
    
    def parseSimpleExpr(self):
        """
        SimpleExpr -> Term MoreTerm
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SimpleExpr")
            self.logger.debug("Parsing SimpleExpr (tree)")
            t = self.parseTerm()
            self._add_child(node, t)
            mt = self.parseMoreTerm()
            self._add_child(node, mt)
            return node
        # Non-tree
        self.logger.debug("Parsing SimpleExpr (non-tree)")
        self.parseTerm()
        self.parseMoreTerm()
        return None
    
    def parseMoreTerm(self):
        """
        MoreTerm -> addopt Term MoreTerm | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("MoreTerm")
            self.logger.debug("Parsing MoreTerm (tree)")
            if self.current_token and self.is_addopt(self.current_token.token_type):
                # Create leaf for the specific addopt token and add it
                op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                self._add_child(node, op_node)
                # Advance past the operator token
                self.advance()
                # Parse the following Term
                t = self.parseTerm()
                self._add_child(node, t)
                # Parse the rest (MoreTerm)
                mt = self.parseMoreTerm()
                self._add_child(node, mt)
            else:
                # Epsilon
                self._add_child(node, ParseTreeNode("ε"))
            return node
        # Non-tree
        self.logger.debug("Parsing MoreTerm (non-tree)")
        if self.current_token and self.is_addopt(self.current_token.token_type):
            # Advance past the operator
            self.advance()
            self.parseTerm()
            self.parseMoreTerm()
        return None
    
    def parseTerm(self):
        """
        Term -> Factor MoreFactor
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Term")
            self.logger.debug("Parsing Term (tree)")
            f = self.parseFactor()
            self._add_child(node, f)
            mf = self.parseMoreFactor()
            self._add_child(node, mf)
            return node
        # Non-tree
        self.logger.debug("Parsing Term (non-tree)")
        self.parseFactor()
        self.parseMoreFactor()
        return None
    
    def parseMoreFactor(self):
        """
        MoreFactor -> mulopt Factor MoreFactor | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("MoreFactor")
            self.logger.debug("Parsing MoreFactor (tree)")
            if self.current_token and self.is_mulopt(self.current_token.token_type):
                # Create leaf for the specific mulopt token and add it
                op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                self._add_child(node, op_node)
                # Advance past the operator token
                self.advance()
                # Parse the following Factor
                f = self.parseFactor()
                self._add_child(node, f)
                # Parse the rest (MoreFactor)
                mf = self.parseMoreFactor()
                self._add_child(node, mf)
            else:
                # Epsilon
                self._add_child(node, ParseTreeNode("ε"))
            return node
        # Non-tree
        self.logger.debug("Parsing MoreFactor (non-tree)")
        if self.current_token and self.is_mulopt(self.current_token.token_type):
            # Advance past the operator
            self.advance()
            self.parseFactor()
            self.parseMoreFactor()
        return None
    
    def parseFactor(self):
        """
        Factor -> idt | numt | ( Expr ) | nott Factor | signopt Factor
        
        Also performs semantic checking for undeclared variables.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Factor")
            self.logger.debug("Parsing Factor (tree)")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                # Save the ID token for semantic checking
                id_token = self.current_token
                
                # Match the identifier
                self.match_leaf(self.defs.TokenType.ID, node)
                
                # Check if the variable is declared (semantic check)
                if self.symbol_table:
                    try:
                        self.symbol_table.lookup(id_token.lexeme)
                    except Exception:
                        error_msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                        line = getattr(id_token, 'line_number', -1)
                        col  = getattr(id_token, 'column_number', -1)
                        self.report_semantic_error(error_msg, line, col)
            
            elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                # Match the numeric literal (integer or real)
                self.match_leaf(self.current_token.token_type, node)
            
            elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                # Match the left parenthesis
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                
                # Parse the expression
                child = self.parseExpr()
                self._add_child(node, child)
                
                # Match the right parenthesis
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            
            elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
                # Match the NOT operator
                self.match_leaf(self.defs.TokenType.NOT, node)
                
                # Parse the factor
                child = self.parseFactor()
                self._add_child(node, child)
            
            elif self.current_token and self.is_signopt(self.current_token.token_type):
                # Match the sign operator
                self.match_leaf(self.current_token.token_type, node)
                
                # Parse the factor
                child = self.parseFactor()
                self._add_child(node, child)
            
            else:
                self.report_error(f"Expected an identifier, number, parenthesized expression, NOT, or sign operator")
            
            return node
        # Non-tree
        self.logger.debug("Parsing Factor (non-tree)")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            # Save the ID token for semantic checking
            id_token = self.current_token
            # Match the identifier (no node needed for non-tree branch)
            self.match(self.defs.TokenType.ID)
            # Check if the variable is declared (semantic check)
            if self.symbol_table:
                try:
                    self.symbol_table.lookup(id_token.lexeme)
                except Exception:
                    error_msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                    line = getattr(id_token, 'line_number', -1)
                    col  = getattr(id_token, 'column_number', -1)
                    self.report_semantic_error(error_msg, line, col)
        
        elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
            # Match the numeric literal (integer or real)
            self.match(self.current_token.token_type)
        
        elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
            # Match the left parenthesis
            self.match(self.defs.TokenType.LPAREN)
            # Parse the expression
            self.parseExpr()
            # Match the right parenthesis
            self.match(self.defs.TokenType.RPAREN)
        
        elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
            # Match the NOT operator
            self.match(self.defs.TokenType.NOT)
            # Parse the factor
            self.parseFactor()
        
        elif self.current_token and self.is_signopt(self.current_token.token_type):
            # Match the sign operator
            self.match(self.current_token.token_type)
            # Parse the factor
            self.parseFactor()
        
        else:
            self.report_error(f"Expected an identifier, number, parenthesized expression, NOT, or sign operator")
        
        return None # Return None for non-tree branch
    
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
        
    def parseTypeMark(self):
        """
        Override TypeMark to return the actual VarType enum value rather than a node.
        TypeMark -> integert | realt | chart | float | const/constant assignop Value 
        """
        self.logger.debug("Parsing TypeMark with type conversion")
        token_type = None
        if self.current_token:
            token_type = self.current_token.token_type
        
        # Map token types to VarType enums
        if token_type == self.defs.TokenType.INTEGERT:
            return VarType.INT
        elif token_type == self.defs.TokenType.REALT:
            return VarType.REAL
        elif token_type == self.defs.TokenType.CHART:
            return VarType.CHAR
        elif token_type == self.defs.TokenType.FLOAT:
            return VarType.FLOAT  # Using FLOAT for both FLOAT and REAL tokens
        elif token_type == self.defs.TokenType.CONSTANT:
            # For constants, we'd need to determine the type from the value
            # For now, default to INT for all constants
            return VarType.INT
        else:
            self.logger.error(f"Unknown type token: {token_type}")
            return VarType.INT  # Default to INT on error
    
    def parseArgs(self):
        """
        Override Args production to add offset calculation for parameters.
        Args -> ( ArgList ) | ε
        
        Parses function/procedure parameters and calculates memory offsets.
        Parameters start at +4 (right after the BP), and grow upward.
        Parameters are processed in reverse order for offset assignment.
        """
        self.logger.debug("Parsing Args with offset calculation")
        
        # Storage for collected parameter info to be processed in reverse later
        collected_params = []
        
        if self.build_parse_tree:
            node = ParseTreeNode("Args")
            # Check for parameters
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                # Parse the parameter list - collect parameters
                params_info = self.parseArgList(collected_params)
                if params_info:
                    node.add_child(params_info)
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            else:
                # Add an ε leaf for empty parameter list
                node.add_child(ParseTreeNode("ε"))
                
            # Now process collected parameters in REVERSE order to assign offsets
            self.processParameterOffsets(collected_params)
                
            return node
        else:
            # Non-tree building version
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match(self.defs.TokenType.LPAREN)
                # Parse the parameter list - collect parameters
                self.parseArgList(collected_params)
                self.match(self.defs.TokenType.RPAREN)
            
            # Now process collected parameters in REVERSE order to assign offsets
            self.processParameterOffsets(collected_params)
            
            return None
            
    def parseArgList(self, collected_params=None):
        """
        Override ArgList production to collect parameter information.
        ArgList -> Mode IdentifierList : TypeMark MoreArgs
        
        Collects parameter information during parsing.
        """
        if collected_params is None:
            collected_params = []
            
        self.logger.debug("Parsing ArgList with parameter collection")
        
        if self.build_parse_tree:
            node = ParseTreeNode("ArgList")
            
            # Parse mode
            mode_node = self.parseMode()
            if mode_node:
                node.add_child(mode_node)
                # Determine parameter mode - default to IN if not specified
                param_mode = ParameterMode.IN
                if mode_node.name == "Mode" and mode_node.children:
                    mode_child = mode_node.children[0]
                    if mode_child.name == "OUT":
                        param_mode = ParameterMode.OUT
                    elif mode_child.name == "INOUT":
                        param_mode = ParameterMode.INOUT
            else:
                param_mode = ParameterMode.IN
            
            # Parse identifiers
            id_list_node = self.parseIdentifierList()
            node.add_child(id_list_node)
            
            # Insert parameter symbols and collect tokens for later offset calculation
            for id_leaf in id_list_node.find_children_by_name("ID"):
                if id_leaf.token:
                    # Create and insert parameter symbol
                    sym = Symbol(
                        id_leaf.token.lexeme,
                        id_leaf.token,
                        EntryType.PARAMETER,
                        self.symbol_table.current_depth
                    )
                    try:
                        self.symbol_table.insert(sym)
                        # Collect for offset calculation (token, mode)
                        collected_params.append((id_leaf.token, param_mode))
                    except DuplicateSymbolError as e:
                        self.report_semantic_error(
                            f"Duplicate parameter declaration: '{e.name}' at depth {e.depth}",
                            getattr(id_leaf.token, 'line_number', -1),
                            getattr(id_leaf.token, 'column_number', -1)
                        )
            
            # Parse type mark
            self.match_leaf(self.defs.TokenType.COLON, node)
            var_type = self.parseTypeMark()
            type_mark_node = super().parseTypeMark()  # Get the parse tree node using parent method
            node.add_child(type_mark_node)  # Add the type mark node without extra parameters       
            # Update the collected parameter information with the type
            for i in range(len(collected_params)):
                if i >= len(collected_params) - len(id_list_node.find_children_by_name("ID")):
                    collected_params[i] = (collected_params[i][0], collected_params[i][1], var_type)
            
            # Parse more arguments
            more_args = self.parseMoreArgs(collected_params)
            if more_args:
                node.add_child(more_args)
                
            return node
        else:
            # Non-tree building version
            # Parse mode
            mode_node = self.parseMode()
            param_mode = ParameterMode.IN  # Default
            if mode_node and mode_node.name == "Mode" and mode_node.children:
                mode_child = mode_node.children[0]
                if mode_child.name == "OUT":
                    param_mode = ParameterMode.OUT
                elif mode_child.name == "INOUT":
                    param_mode = ParameterMode.INOUT
            
            # Parse identifiers
            id_list_node = self.parseIdentifierList()
            
            # Insert parameter symbols and collect tokens for later offset calculation
            for id_leaf in id_list_node.find_children_by_name("ID"):
                if id_leaf.token:
                    # Create and insert parameter symbol
                    sym = Symbol(
                        id_leaf.token.lexeme,
                        id_leaf.token,
                        EntryType.PARAMETER,
                        self.symbol_table.current_depth
                    )
                    try:
                        self.symbol_table.insert(sym)
                        # Collect for offset calculation (token, mode)
                        collected_params.append((id_leaf.token, param_mode))
                    except DuplicateSymbolError as e:
                        self.report_semantic_error(
                            f"Duplicate parameter declaration: '{e.name}' at depth {e.depth}",
                            getattr(id_leaf.token, 'line_number', -1),
                            getattr(id_leaf.token, 'column_number', -1)
                        )
            
            # Parse type mark
            self.match(self.defs.TokenType.COLON)
            var_type = self.parseTypeMark()  # Get the variable type
            super().parseTypeMark()  # Call parent method to consume tokens
            
            # Update the collected parameter information with the type
            for i in range(len(collected_params)):
                if i >= len(collected_params) - len(id_list_node.find_children_by_name("ID")):
                    collected_params[i] = (collected_params[i][0], collected_params[i][1], var_type)
            
            # Parse more arguments
            self.parseMoreArgs(collected_params)
            
            return None
            
    def parseMoreArgs(self, collected_params=None):
        """
        Override MoreArgs production to continue collecting parameter information.
        MoreArgs -> ; ArgList | ε
        """
        if collected_params is None:
            collected_params = []
            
        self.logger.debug("Parsing MoreArgs with parameter collection")
        
        if self.build_parse_tree:
            node = ParseTreeNode("MoreArgs")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)
                arg_list = self.parseArgList(collected_params)
                if arg_list:
                    node.add_child(arg_list)
                return node
            else:
                node.add_child(ParseTreeNode("ε"))
                return node
        else:
            if self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
                self.match(self.defs.TokenType.SEMICOLON)
                self.parseArgList(collected_params)
            return None
            
    def processParameterOffsets(self, collected_params):
        """
        Process the collected parameters in reverse order to assign memory offsets.
        
        Args:
            collected_params: List of (token, mode, var_type) tuples
        """
        # Process in reverse order since parameters are pushed onto stack right to left
        for token, mode, var_type in reversed(collected_params):
            try:
                # Look up the symbol
                symbol = self.symbol_table.lookup(token.lexeme, lookup_current_scope_only=True)
                
                # Set the parameter mode
                symbol.param_mode = mode
                
                # Set the variable type
                symbol.var_type = var_type
                
                # Get the size for this type
                if var_type not in TYPE_SIZES:
                    self.report_semantic_error(
                        f"Unknown parameter type: {var_type}",
                        getattr(token, 'line_number', -1),
                        getattr(token, 'column_number', -1)
                    )
                    size = 1  # Default to 1 byte on error
                else:
                    size = TYPE_SIZES[var_type]
                
                # Set size and offset
                symbol.size = size
                symbol.offset = self.current_param_offset
                self.logger.debug(f"Assigned parameter {symbol.name}: mode={mode}, type={var_type}, size={size}, offset={self.current_param_offset}")
                
                # Increment the parameter offset for the next parameter
                self.current_param_offset += size
                
            except Exception as e:
                self.logger.error(f"Error setting parameter attributes: {e}")

    def parseDeclarativePart(self):
        """
        DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε
        Also insert each declared identifier into the symbol table and calculate memory offsets.
        """
        self.logger.debug("Parsing DeclarativePart (Extended)")
        # Build tree branch
        if self.build_parse_tree:
            node = ParseTreeNode("DeclarativePart")
            # If there's a declaration
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                # Identifiers
                id_list_node = self.parseIdentifierList()
                assert id_list_node is not None
                # Insert declarations
                for id_leaf in id_list_node.find_children_by_name("ID"):
                    if id_leaf.token:
                        sym = Symbol(
                            id_leaf.token.lexeme,
                            id_leaf.token,
                            EntryType.VARIABLE,
                            self.symbol_table.current_depth
                        )
                        try:
                            self.symbol_table.insert(sym)
                        except DuplicateSymbolError as e:
                            # report duplicate declaration but continue parsing
                            self.report_semantic_error(
                                f"Duplicate symbol declaration: '{e.name}' at depth {e.depth}",
                                getattr(id_leaf.token, 'line_number', -1),
                                getattr(id_leaf.token, 'column_number', -1)
                            )
                # Type and semicolon
                self.match_leaf(self.defs.TokenType.COLON, node)
                var_type = self.parseTypeMark()
                assert var_type is not None
                type_mark_node = super().parseTypeMark()  # Get the parse tree node using parent method
                node.add_child(type_mark_node)  # Add the type mark node without extra parameters
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)
                
                # After parsing the TypeMark, look up each variable again to set type, size, and offset
                for id_leaf in id_list_node.find_children_by_name("ID"):
                    if id_leaf.token:
                        try:
                            # Look up the symbol that was already inserted
                            symbol = self.symbol_table.lookup(id_leaf.token.lexeme, lookup_current_scope_only=True)
                            # Determine type and size
                            symbol.var_type = var_type  # Use the var_type returned by parseTypeMark
                            
                            # Get the size for this type
                            if var_type not in TYPE_SIZES:
                                self.report_semantic_error(
                                    f"Unknown variable type: {var_type}",
                                    getattr(id_leaf.token, 'line_number', -1),
                                    getattr(id_leaf.token, 'column_number', -1)
                                )
                                size = 1  # Default to 1 byte on error
                            else:
                                size = TYPE_SIZES[var_type]
                            
                            # Set size and offset
                            symbol.size = size
                            symbol.offset = self.current_local_offset
                            self.logger.debug(f"Assigned local var {symbol.name}: type={var_type}, size={size}, offset={self.current_local_offset}")
                            
                            # Decrement the local offset for the next variable
                            self.current_local_offset -= size
                            
                        except Exception as e:
                            self.logger.error(f"Error setting variable attributes: {e}")
                
                # Recursively parse further declarations
                next_node = self.parseDeclarativePart()
                # Attach children
                node.add_child(id_list_node)
                if next_node:
                    node.add_child(next_node)
            else:
                # Epsilon
                node.add_child(ParseTreeNode("ε"))
            return node
        # Non-tree branch: just parse and insert
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            id_list_node = self.parseIdentifierList()
            assert id_list_node is not None
            # Insert declarations
            id_tokens = []  # Keep track of inserted identifiers
            for id_leaf in id_list_node.find_children_by_name("ID"):
                if id_leaf.token:
                    sym = Symbol(
                        id_leaf.token.lexeme,
                        id_leaf.token,
                        EntryType.VARIABLE,
                        self.symbol_table.current_depth
                    )
                    try:
                        self.symbol_table.insert(sym)
                        id_tokens.append(id_leaf.token)  # Track successfully inserted IDs
                    except DuplicateSymbolError as e:
                        # report duplicate declaration but continue parsing
                        self.report_semantic_error(
                            f"Duplicate symbol declaration: '{e.name}' at depth {e.depth}",
                            getattr(id_leaf.token, 'line_number', -1),
                            getattr(id_leaf.token, 'column_number', -1)
                        )
            
            self.match(self.defs.TokenType.COLON)
            var_type = self.parseTypeMark()  # Get the variable type
            super().parseTypeMark()  # Call parent method to consume tokens
            self.match(self.defs.TokenType.SEMICOLON)
            
            # After parsing the TypeMark, look up each variable again to set type, size, and offset
            for token in id_tokens:
                try:
                    # Look up the symbol that was already inserted
                    symbol = self.symbol_table.lookup(token.lexeme, lookup_current_scope_only=True)
                    # Determine type and size
                    symbol.var_type = var_type  # Use the var_type returned by parseTypeMark
                    
                    # Get the size for this type
                    if var_type not in TYPE_SIZES:
                        self.report_semantic_error(
                            f"Unknown variable type: {var_type}",
                            getattr(token, 'line_number', -1),
                            getattr(token, 'column_number', -1)
                        )
                        size = 1  # Default to 1 byte on error
                    else:
                        size = TYPE_SIZES[var_type]
                    
                    # Set size and offset
                    symbol.size = size
                    symbol.offset = self.current_local_offset
                    self.logger.debug(f"Assigned local var {symbol.name}: type={var_type}, size={size}, offset={self.current_local_offset}")
                    
                    # Decrement the local offset for the next variable
                    self.current_local_offset -= size
                    
                except Exception as e:
                    self.logger.error(f"Error setting variable attributes: {e}")
            
            # Further declarations
            self.parseDeclarativePart()
        return None