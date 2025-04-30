#!/usr/bin/env python3  
# TACGenerator.py  
# Author: John Akujobi  
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction  
# Date: 2025-04-18  
# Version: 1.0  
"""  
Three Address Code Generator for Ada Compiler  
  
This module generates Three Address Code (TAC) from the parsed AST for Assignment 7.  
It handles:  
- Temporary variable generation  
- Procedure/function boundaries  
- Expression evaluation  
- Assignment statements  
- Procedure calls with parameter passing  
"""  
  
import os  
from pathlib import Path  
from typing import List, Dict, Optional, Any, TextIO, Union  
from enum import Enum, auto  
  
from .Logger import logger  
from .SymTable import Symbol, EntryType, ParameterMode  
from .TypeUtils import TypeUtils  
  
class TACGenerator:  
    """  
    Generates Three Address Code for an Ada program.  
      
    This class handles the generation of TAC instructions and manages  
    temporaries, procedure boundaries, and basic operations.  
    """  
      
    def __init__(self, output_filename: str):  
        """  
        Initialize the TAC Generator.  
          
        Args:  
            output_filename: The path to the output TAC file  
        """  
        self.output_filename = output_filename  
        self.temp_counter = 0  # For generating temporary variables  
        self.tac_lines = []    # List of TAC instructions  
        self.start_proc_name = None  # Store the outermost procedure name  
        logger.info(f"TAC Generator initialized with output file: {output_filename}")  
      
    def emit(self, instruction_str: str):  
        """  
        Emit a TAC instruction.  
          
        Args:  
            instruction_str: The instruction string to emit  
        """  
        self.tac_lines.append(instruction_str)  
        logger.debug(f"Emitted TAC: {instruction_str}")  
      
    def _newTempName(self) -> str:  
        """  
        Generate a new temporary variable name.  
          
        Returns:  
            A unique temporary variable name (_t1, _t2, etc.)  
        """  
        self.temp_counter += 1  
        return f"_t{self.temp_counter}"  
      
    def newTemp(self) -> str:  
        """  
        Get a new temporary variable.  
          
        Returns:  
            The name of the new temporary variable  
        """  
        return self._newTempName()  
      
    def getPlace(self, symbol_or_value) -> str:  
        """  
        Get the place string for a symbol or value.  
          
        Args:  
            symbol_or_value: Symbol object, literal value, or temporary  
              
        Returns:  
            String representation for TAC operand/result  
        """  
        # Handle literals (strings or numbers)  
        if isinstance(symbol_or_value, (int, float, str)):  
            if isinstance(symbol_or_value, str) and symbol_or_value.startswith("_t"):  
                # It's a temporary variable, return as is  
                return symbol_or_value  
            # It's a literal value, return as string  
            return str(symbol_or_value)  
          
        # Handle symbols from symbol table  
        if isinstance(symbol_or_value, Symbol):  
            symbol = symbol_or_value  
              
            # Handle constants - use their value directly  
            if symbol.entry_type == EntryType.CONSTANT and symbol.const_value is not None:  
                return str(symbol.const_value)  
              
            # Depth 1 variables use their actual names  
            if symbol.depth == 1:  
                return symbol.name  
              
            # Depth > 1 variables and parameters use BP-relative addressing  
            if symbol.offset is not None:  
                # Parameters have positive offsets  
                if symbol.entry_type == EntryType.PARAMETER:  
                    return f"_BP+{symbol.offset}"  
                # Local variables have negative offsets  
                return f"_BP-{abs(symbol.offset)}"  
              
            # Shouldn't get here if symbol table is properly populated  
            logger.error(f"Symbol {symbol.name} has no offset defined")  
            return f"ERROR_{symbol.name}"  
          
        # Default case for unknown types  
        logger.warning(f"Unknown place type: {type(symbol_or_value)}")  
        return str(symbol_or_value)  
      
    def emitBinaryOp(self, op: str, dest_place: str, left_place: str, right_place: str):  
        """  
        Emit a binary operation instruction.  
          
        Args:  
            op: The operation (ADD, SUB, MUL, etc.)  
            dest_place: The destination place  
            left_place: The left operand place  
            right_place: The right operand place  
        """  
        self.emit(f"{dest_place} = {left_place} {op} {right_place}")  
      
    def emitUnaryOp(self, op: str, dest_place: str, operand_place: str):  
        """  
        Emit a unary operation instruction.  
          
        Args:  
            op: The operation (UMINUS, NOT)  
            dest_place: The destination place  
            operand_place: The operand place  
        """  
        self.emit(f"{dest_place} = {op} {operand_place}")  
      
    def emitAssignment(self, dest_place: str, source_place: str):  
        """  
        Emit an assignment instruction.  
          
        Args:  
            dest_place: The destination place  
            source_place: The source place  
        """  
        self.emit(f"{dest_place} = {source_place}")  
      
    def emitProcStart(self, proc_name: str):  
        """  
        Emit a procedure start directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        self.emit(f"proc {proc_name}")  
        # Reset temporary counter for this procedure  
        self.temp_counter = 0  
      
    def emitProcEnd(self, proc_name: str):  
        """  
        Emit a procedure end directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        self.emit(f"endp {proc_name}")  
      
    def emitPush(self, place: str, mode: ParameterMode):  
        """  
        Emit a push instruction for procedure calls.  
          
        Args:  
            place: The place to push  
            mode: The parameter mode (IN, OUT, INOUT)  
        """  
        # For OUT or INOUT parameters, push the address (pass by reference)  
        if mode in (ParameterMode.OUT, ParameterMode.INOUT):  
            self.emit(f"push @{place}")  
        else:  
            # For IN parameters, push the value (pass by value)  
            self.emit(f"push {place}")  
      
    def emitCall(self, proc_name: str):  
        """  
        Emit a procedure call instruction.  
          
        Args:  
            proc_name: The name of the procedure to call  
        """  
        self.emit(f"call {proc_name}")  
      
    def emitProgramStart(self, main_proc_name: str):  
        """  
        Store the outermost procedure name for the start directive.  
          
        Args:  
            main_proc_name: The name of the main procedure  
        """  
        self.start_proc_name = main_proc_name  
      
    def writeOutput(self) -> bool:  
        """  
        Write the TAC instructions to the output file.  
          
        Returns:  
            True if successful, False otherwise  
        """  
        try:  
            with open(self.output_filename, 'w') as f:  
                # Write all TAC instructions  
                for line in self.tac_lines:  
                    f.write(f"{line}\n")  
                  
                # Write START directive as the last line  
                if self.start_proc_name:  
                    f.write(f"start {self.start_proc_name}\n")  
                else:  
                    logger.error("No start procedure name set")  
              
            logger.info(f"TAC output written to {self.output_filename}")  
            return True  
        except Exception as e:  
            logger.error(f"Error writing TAC output: {e}")  
            return False  
      
    def map_ada_op_to_tac(self, ada_op: str) -> str:  
        """  
        Map Ada operators to TAC operators.  
          
        Args:  
            ada_op: The Ada operator  
              
        Returns:  
            The corresponding TAC operator  
        """  
        mapping = {  
            '+': 'ADD',  
            '-': 'SUB',  
            '*': 'MUL',  
            '/': 'DIV',  
            'div': 'DIV',  
            'mod': 'MOD',  
            'rem': 'REM',  
            'and': 'AND',  
            'or': 'OR',  
            'not': 'NOT'  
        }  
        return mapping.get(ada_op.lower(), ada_op)