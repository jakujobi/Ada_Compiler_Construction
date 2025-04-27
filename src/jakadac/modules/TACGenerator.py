#!/usr/bin/env python3
# TACGenerator.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-27
# Version: 1.0
"""
Three Address Code (TAC) Generator for the Ada Compiler.

This module provides functionality to generate Three Address Code during the parsing process.
It supports:
- Variable place representations: global names or stack-relative references (_BP+/-offset)
- Binary and unary operations
- Assignment statements
- Procedure call handling with parameter passing
- Temporary variable management
"""

import os
from typing import Dict, Optional, Union

from .SymTable import Symbol, EntryType, ParameterMode

class TACGenerator:
    """
    Generates Three Address Code (TAC) instructions.
    """
    
    def __init__(self, output_filename: str):
        """
        Initialize the TAC generator with an output file.
        
        Args:
            output_filename: Path to the output .tac file
        """
        self._output_file = open(output_filename, 'w')
        self._temp_counter = 0  # Counter for temporary variables
        self._current_proc = None  # Track the current procedure being processed
    
    def emit(self, instruction: str):
        """
        Write an instruction to the output file, followed by a newline.
        
        Args:
            instruction: The TAC instruction to write
        """
        self._output_file.write(instruction + '\n')
    
    def _newTempName(self) -> str:
        """
        Generate a new temporary variable name (_t1, _t2, etc.)
        
        Returns:
            The new temporary variable name
        """
        self._temp_counter += 1
        return f"_t{self._temp_counter}"
    
    def getPlace(self, symbol_or_value: Union[Symbol, str, int, float]) -> str:
        """
        Get the TAC representation for a symbol or constant value.
        
        Args:
            symbol_or_value: A Symbol object, or a constant value (string/number)
            
        Returns:
            The TAC representation ("A" for globals, "_BP+4" for params, "_BP-2" for locals, or literal constants)
        """
        if isinstance(symbol_or_value, Symbol):
            symbol = symbol_or_value
            # Global variable (depth 1) - use name directly
            if symbol.depth == 0:
                return symbol.name
            # Local variable or parameter (depth > 1) - use _BP+/-offset
            elif symbol.offset is not None:
                # For parameters, offset is positive
                if symbol.entry_type == EntryType.PARAMETER:
                    return f"_BP+{symbol.offset}"
                # For locals, offset is negative
                else:
                    return f"_BP{symbol.offset}"  # Negative offset already includes the minus sign
            else:
                # Should not happen if offsets are calculated correctly
                return f"<ERROR: No offset for {symbol.name}>"
        elif isinstance(symbol_or_value, (int, float)):
            # Numeric constant - use the value directly
            return str(symbol_or_value)
        else:
            # String or other type - just convert to string
            return str(symbol_or_value)
    
    def newTemp(self) -> str:
        """
        Generate a new temporary variable name.
        
        Returns:
            The name of the new temporary variable (_tN)
        """
        return self._newTempName()
    
    def emitBinaryOp(self, op: str, dest_place: str, left_place: str, right_place: str):
        """
        Emit a binary operation instruction.
        
        Args:
            op: The operator symbol (+, -, *, /, etc.)
            dest_place: The destination place
            left_place: The left operand place
            right_place: The right operand place
        """
        self.emit(f"{dest_place} = {left_place} {op} {right_place}")
    
    def emitUnaryOp(self, op: str, dest_place: str, operand_place: str):
        """
        Emit a unary operation instruction.
        
        Args:
            op: The operator symbol (-, not, etc.)
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
        Emit the beginning of a procedure.
        
        Args:
            proc_name: The name of the procedure
        """
        self._current_proc = proc_name
        self._temp_counter = 0  # Reset temp counter for the new procedure
        self.emit(f"proc {proc_name}")
    
    def emitProcEnd(self, proc_name: str):
        """
        Emit the end of a procedure.
        
        Args:
            proc_name: The name of the procedure
        """
        self.emit(f"endp {proc_name}")
        self._current_proc = None
    
    def emitPush(self, place: str, mode: ParameterMode = None):
        """
        Emit a push instruction for parameter passing.
        
        Args:
            place: The place to push (variable, constant, etc.)
            mode: The parameter mode (IN, OUT, INOUT)
        """
        # If OUT or INOUT parameter, pass by reference
        if mode in (ParameterMode.OUT, ParameterMode.INOUT):
            self.emit(f"push @{place}")
        # Otherwise (IN or None), pass by value
        else:
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
        Emit the program start directive.
        
        Args:
            main_proc_name: The name of the main/outermost procedure
        """
        self.emit(f"start {main_proc_name}")
    
    def close(self):
        """
        Close the output file.
        """
        if self._output_file:
            self._output_file.close()
            self._output_file = None