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
AssignStat -> idt := Expr  
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
from typing import List, Optional
import traceback


from .RDParser import RDParser, ParseTreeNode
from .Token import Token
from .Definitions import Definitions
from .Logger import Logger
from .SymTable import SymbolTable, Symbol, EntryType, DuplicateSymbolError


class RDParserExtended(RDParser):
    """
    Extended Recursive Descent Parser with grammar rules for statements and expressions
    """
    
    def __init__(self, tokens, defs, symbol_table=None, stop_on_error=False, panic_mode_recover=False, build_parse_tree=False):
        """
        Initialize the extended parser.
        
        Parameters:
            tokens (List[Token]): The list of tokens from the lexical analyzer.
            defs (Definitions): The definitions instance from the lexical analyzer.
            symbol_table (AdaSymbolTable): Symbol table for semantic checking.
            stop_on_error (bool): Whether to stop on error.
            panic_mode_recover (bool): Whether to attempt recovery from errors.
            build_parse_tree (bool): Whether to build a parse tree.
        """
        super().__init__(tokens, defs, stop_on_error, panic_mode_recover, build_parse_tree)
        # Use provided symbol_table or default to a new one
        self.symbol_table: SymbolTable = symbol_table if symbol_table is not None else SymbolTable()
        self.semantic_errors = []
        
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
        
        # Parse the rest of the procedure declaration
        child = self.parseArgs()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
        self.match_leaf(self.defs.TokenType.IS, node)
        
        child = self.parseDeclarativePart()
        if self.build_parse_tree and node is not None and child:
            self._add_child(node, child)
        
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

    def parseDeclarativePart(self):
        """
        DeclarativePart -> IdentifierList : TypeMark ; DeclarativePart | ε
        Also insert each declared identifier into the symbol table.
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
                type_mark_node = self.parseTypeMark()
                assert type_mark_node is not None
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)
                # Recursively parse further declarations
                next_node = self.parseDeclarativePart()
                # Attach children
                node.add_child(id_list_node)
                node.add_child(type_mark_node)
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
            self.match(self.defs.TokenType.COLON)
            self.parseTypeMark()
            self.match(self.defs.TokenType.SEMICOLON)
            # Further declarations
            self.parseDeclarativePart()
        return None
