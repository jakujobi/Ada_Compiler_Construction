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
IOStat -> ε  
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


from Modules.RDParser import RDParser, ParseTreeNode
from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.Logger import Logger
from Modules.AdaSymbolTable import AdaSymbolTable


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
        self.symbol_table = symbol_table
        self.semantic_errors = []
        
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
        start_id_token = self.current_token
        procedure_name = start_id_token.lexeme if self.current_token else "unknown"
        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Parse the rest of the procedure declaration
        child = self.parseArgs()
        if child and self.build_parse_tree: 
            node.add_child(child)
        
        self.match_leaf(self.defs.TokenType.IS, node)
        
        child = self.parseDeclarativePart()
        if child and self.build_parse_tree: 
            node.add_child(child)
        
        child = self.parseProcedures()
        if child and self.build_parse_tree: 
            node.add_child(child)
        
        self.match_leaf(self.defs.TokenType.BEGIN, node)
        
        child = self.parseSeqOfStatements()
        if child and self.build_parse_tree: 
            node.add_child(child)
        
        self.match_leaf(self.defs.TokenType.END, node)
        
        # Save the procedure identifier (second occurrence)
        end_id_token = self.current_token
        
        # Match the identifier and continue parsing
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Check if the procedure identifiers match
        if end_id_token and start_id_token and end_id_token.lexeme != start_id_token.lexeme:
            error_msg = f"Procedure name mismatch: procedure '{start_id_token.lexeme}' ends with '{end_id_token.lexeme}'"
            self.report_error(error_msg)
            self.report_semantic_error(error_msg, end_id_token.line if hasattr(end_id_token, 'line') else 0, 
                                    end_id_token.column if hasattr(end_id_token, 'column') else 0)
        
        self.match_leaf(self.defs.TokenType.SEMICOLON, node)
        
        return node
    
    def parseSeqOfStatements(self):
        """
        SeqOfStatments -> Statement ; StatTail | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SeqOfStatements")
        else:
            node = None
        
        self.logger.debug("Parsing SeqOfStatements")
        
        # Check if we have at least one statement
        if self.current_token.token_type != self.defs.TokenType.END:
            # Parse the first statement
            child = self.parseStatement()
            if self.build_parse_tree and child:
                node.add_child(child)
            
            # Match semicolon
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            
            # Parse the rest of statements (StatTail)
            child = self.parseStatTail()
            if self.build_parse_tree and child:
                node.add_child(child)
        else:
            # Empty sequence of statements (ε)
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
        
        return node
    
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
        if self.current_token.token_type != self.defs.TokenType.END:
            # Parse the statement
            child = self.parseStatement()
            if self.build_parse_tree and child:
                node.add_child(child)
            
            # Match semicolon
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            
            # Parse the rest of statements (StatTail)
            child = self.parseStatTail()
            if self.build_parse_tree and child:
                node.add_child(child)
        else:
            # End of statements (ε)
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
        
        return node
    
    def parseStatement(self):
        """
        Statement -> AssignStat | IOStat
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Statement")
        else:
            node = None
        
        self.logger.debug("Parsing Statement")
        
        # For now, only assignment statements are implemented
        # Later, IO statements can be added
        if self.current_token.token_type == self.defs.TokenType.ID:
            child = self.parseAssignStat()
            if self.build_parse_tree and child:
                node.add_child(child)
        else:
            # Assume IOStat for now (which is just ε in the grammar)
            child = self.parseIOStat()
            if self.build_parse_tree and child:
                node.add_child(child)
        
        return node
    
    def parseAssignStat(self):
        """
        AssignStat -> idt := Expr
        
        Also performs semantic checking for undeclared variables.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("AssignStat")
        else:
            node = None
        
        self.logger.debug("Parsing AssignStat")
        
        # Save the ID token for semantic checking
        id_token = self.current_token
        
        # Match the identifier
        self.match_leaf(self.defs.TokenType.ID, node)
        
        # Check if the variable is declared (semantic check)
        if self.symbol_table and id_token.token_type == self.defs.TokenType.ID:
            entry = self.symbol_table.lookup(id_token.lexeme)
            if not entry:
                error_msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                self.report_semantic_error(error_msg, id_token.line if hasattr(id_token, 'line') else 0, 
                                          id_token.column if hasattr(id_token, 'column') else 0)
        
        # Match the assignment operator
        self.match_leaf(self.defs.TokenType.ASSIGN, node)
        
        # Parse the expression
        child = self.parseExpr()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        return node
    
    def parseIOStat(self):
        """
        IOStat -> ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("IOStat")
            node.add_child(ParseTreeNode("ε"))
            return node
        else:
            self.logger.debug("IOStat -> ε")
            return None
    
    def parseExpr(self):
        """
        Expr -> Relation
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Expr")
        else:
            node = None
        
        self.logger.debug("Parsing Expr")
        
        child = self.parseRelation()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        return node
    
    def parseRelation(self):
        """
        Relation -> SimpleExpr
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Relation")
        else:
            node = None
        
        self.logger.debug("Parsing Relation")
        
        child = self.parseSimpleExpr()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        return node
    
    def parseSimpleExpr(self):
        """
        SimpleExpr -> Term MoreTerm
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SimpleExpr")
        else:
            node = None
        
        self.logger.debug("Parsing SimpleExpr")
        
        child = self.parseTerm()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        child = self.parseMoreTerm()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        return node
    
    def parseMoreTerm(self):
        """
        MoreTerm -> addopt Term MoreTerm | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("MoreTerm")
        else:
            node = None
        
        self.logger.debug("Parsing MoreTerm")
        
        # Check if we have an addopt operator
        if self.is_addopt(self.current_token.token_type):
            # Match the operator
            self.match_leaf(self.current_token.token_type, node)
            
            # Parse the term
            child = self.parseTerm()
            if self.build_parse_tree and child:
                node.add_child(child)
            
            # Parse more terms
            child = self.parseMoreTerm()
            if self.build_parse_tree and child:
                node.add_child(child)
        else:
            # No more terms (ε)
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
        
        return node
    
    def parseTerm(self):
        """
        Term -> Factor MoreFactor
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Term")
        else:
            node = None
        
        self.logger.debug("Parsing Term")
        
        child = self.parseFactor()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        child = self.parseMoreFactor()
        if self.build_parse_tree and child:
            node.add_child(child)
        
        return node
    
    def parseMoreFactor(self):
        """
        MoreFactor -> mulopt Factor MoreFactor | ε
        """
        if self.build_parse_tree:
            node = ParseTreeNode("MoreFactor")
        else:
            node = None
        
        self.logger.debug("Parsing MoreFactor")
        
        # Check if we have a mulopt operator
        if self.is_mulopt(self.current_token.token_type):
            # Match the operator
            self.match_leaf(self.current_token.token_type, node)
            
            # Parse the factor
            child = self.parseFactor()
            if self.build_parse_tree and child:
                node.add_child(child)
            
            # Parse more factors
            child = self.parseMoreFactor()
            if self.build_parse_tree and child:
                node.add_child(child)
        else:
            # No more factors (ε)
            if self.build_parse_tree:
                node.add_child(ParseTreeNode("ε"))
        
        return node
    
    def parseFactor(self):
        """
        Factor -> idt | numt | ( Expr ) | nott Factor | signopt Factor
        
        Also performs semantic checking for undeclared variables.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("Factor")
        else:
            node = None
        
        self.logger.debug("Parsing Factor")
        
        if self.current_token.token_type == self.defs.TokenType.ID:
            # Save the ID token for semantic checking
            id_token = self.current_token
            
            # Match the identifier
            self.match_leaf(self.defs.TokenType.ID, node)
            
            # Check if the variable is declared (semantic check)
            if self.symbol_table and id_token.token_type == self.defs.TokenType.ID:
                entry = self.symbol_table.lookup(id_token.lexeme)
                if not entry:
                    error_msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                    self.report_semantic_error(error_msg, id_token.line if hasattr(id_token, 'line') else 0, 
                                              id_token.column if hasattr(id_token, 'column') else 0)
        
        elif self.current_token.token_type == self.defs.TokenType.NUM:
            # Match the number
            self.match_leaf(self.defs.TokenType.NUM, node)
        
        elif self.current_token.token_type == self.defs.TokenType.LPAREN:
            # Match the left parenthesis
            self.match_leaf(self.defs.TokenType.LPAREN, node)
            
            # Parse the expression
            child = self.parseExpr()
            if self.build_parse_tree and child:
                node.add_child(child)
            
            # Match the right parenthesis
            self.match_leaf(self.defs.TokenType.RPAREN, node)
        
        elif self.current_token.token_type == self.defs.TokenType.NOT:
            # Match the NOT operator
            self.match_leaf(self.defs.TokenType.NOT, node)
            
            # Parse the factor
            child = self.parseFactor()
            if self.build_parse_tree and child:
                node.add_child(child)
        
        elif self.is_signopt(self.current_token.token_type):
            # Match the sign operator
            self.match_leaf(self.current_token.token_type, node)
            
            # Parse the factor
            child = self.parseFactor()
            if self.build_parse_tree and child:
                node.add_child(child)
        
        else:
            self.report_error(f"Expected an identifier, number, parenthesized expression, NOT, or sign operator")
        
        return node
    
    def is_addopt(self, token_type):
        """
        Check if a token type is an addopt operator (+ | - | or)
        """
        return token_type in {
            self.defs.TokenType.PLUS,
            self.defs.TokenType.MINUS,
            self.defs.TokenType.OR
        }
    
    def is_mulopt(self, token_type):
        """
        Check if a token type is a mulopt operator (* | / | mod | rem | and)
        """
        return token_type in {
            self.defs.TokenType.MULT,
            self.defs.TokenType.DIV,
            self.defs.TokenType.MOD,
            self.defs.TokenType.REM,
            self.defs.TokenType.AND
        }
    
    def is_signopt(self, token_type):
        """
        Check if a token type is a signopt operator (+ | -)
        """
        return token_type in {
            self.defs.TokenType.PLUS,
            self.defs.TokenType.MINUS
        }
    
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
