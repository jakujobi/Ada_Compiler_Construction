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
  
from .Logger import Logger, logger  
from .SymTable import Symbol, EntryType, ParameterMode  
from .TypeUtils import TypeUtils  

# This one passed all the tests of test_tac_generator.py
  
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
        self.logger = logger  
        self.logger.info(f"TAC Generator initialized. Output Target: '{self.output_filename}'")  
      
    def emit(self, instruction_str: str):  
        """  
        Emit a TAC instruction.  
          
        Args:  
            instruction_str: The instruction string to emit  
        """  
        self.tac_lines.append(instruction_str)  
        self.logger.debug(f"Emit TAC: {instruction_str}")  
      
    def _newTempName(self) -> str:  
        """  
        Generate a new temporary variable name.  
          
        Returns:  
            A unique temporary variable name (_t1, _t2, etc.)  
        """  
        self.temp_counter += 1  
        temp_name = f"_t{self.temp_counter}"  
        self.logger.debug(f"Generated new temporary: {temp_name}")  
        return temp_name  
      
    def newTemp(self) -> str:  
        """  
        Get a new temporary variable.  
          
        Returns:  
            The name of the new temporary variable  
        """  
        return self._newTempName()  
      
    def getPlace(self, symbol_or_value) -> str:  
        """  
        Get the place string for a symbol or value for use in TAC.  
          
        Args:  
            symbol_or_value: Symbol object, literal value, or temporary name (str)  
              
        Returns:  
            String representation for TAC operand/result (e.g., 'x', '5', '_t1', '_BP+4').  
        """  
        self.logger.debug(f"Getting place for: {symbol_or_value} (Type: {type(symbol_or_value)})")  
  
        place_str = "ERROR_UNKNOWN_PLACE"  # Default error value  
  
        # Handle temporary variables (already strings like '_t1')  
        if isinstance(symbol_or_value, str) and symbol_or_value.startswith("_t"):  
            place_str = symbol_or_value  
  
        # Handle literals (numbers, potentially strings if supported later)  
        elif isinstance(symbol_or_value, (int, float)):  
            place_str = str(symbol_or_value)  
  
        # Handle Symbols from symbol table  
        elif isinstance(symbol_or_value, Symbol):  
            symbol = symbol_or_value  
  
            # Handle constants - use their value directly  
            if symbol.entry_type == EntryType.CONSTANT and symbol.const_value is not None:  
                place_str = str(symbol.const_value)  
                self.logger.debug(f"Place for CONSTANT '{symbol.name}' is value: {place_str}")  
  
            # Depth 0 (Global) variables/procedures might use their actual names (implementation dependent)  
            # Assuming globals are not directly handled by BP offsets here. Adjust if needed.  
            # For A7, focus might be on locals/params with offsets.  
            # If depth 0 is global, it might need a different addressing scheme (e.g., labels)  
  
            # Use Base Pointer (BP) relative addressing for parameters and locals (Depth > 0)  
            elif symbol.depth > 0 and symbol.offset is not None:  
                # Parameters typically have positive offsets from BP  
                if symbol.entry_type == EntryType.PARAMETER:  
                    place_str = f"_BP+{symbol.offset}"  
                # Local variables typically have negative offsets from BP  
                elif symbol.entry_type == EntryType.VARIABLE:  
                    # Ensure offset is negative for locals, take absolute for clarity in TAC  
                    place_str = f"_BP-{abs(symbol.offset)}"  
                else:  
                    # Other symbol types might not have standard BP offsets (e.g., TYPE)  
                    self.logger.warning(f"Symbol '{symbol.name}' (Type: {symbol.entry_type}) has offset but is not PARAMETER or VARIABLE. Using name as place.")  
                    place_str = symbol.name  # Fallback to name  
  
                self.logger.debug(f"Place for Symbol '{symbol.name}' (Depth {symbol.depth}, Type {symbol.entry_type}) is offset: {place_str}")  
  
            # Fallback for symbols without offsets or unhandled cases  
            else:  
                if symbol.offset is None:  
                    self.logger.error(f"Symbol '{symbol.name}' (Depth {symbol.depth}, Type {symbol.entry_type}) has no offset defined. Using name as place.")  
                else:  
                    self.logger.warning(f"Unhandled case for Symbol '{symbol.name}' (Depth {symbol.depth}, Type {symbol.entry_type}). Using name as place.")  
                place_str = symbol.name  # Fallback to the symbol's name  
  
        # Handle other unexpected types  
        else:  
            self.logger.warning(f"Unknown type encountered in getPlace: {type(symbol_or_value)}. Converting to string: '{str(symbol_or_value)}'")  
            place_str = str(symbol_or_value)  # Fallback: string representation  
  
        self.logger.debug(f"Calculated place: '{place_str}'")  
        return place_str  
      
    def emitBinaryOp(self, op: str, dest_place: str, left_place: str, right_place: str):  
        """  
        Emit a binary operation instruction.  
          
        Args:  
            op: The operation (ADD, SUB, MUL, etc.)  
            dest_place: The destination place  
            left_place: The left operand place  
            right_place: The right operand place  
        """  
        instruction = f"{dest_place} = {left_place} {op} {right_place}"  
        self.logger.debug(f"Emitting Binary Op: {instruction}")  
        self.emit(instruction)  
      
    def emitUnaryOp(self, op: str, dest_place: str, operand_place: str):  
        """  
        Emit a unary operation instruction.  
          
        Args:  
            op: The operation (UMINUS, NOT)  
            dest_place: The destination place  
            operand_place: The operand place  
        """  
        instruction = f"{dest_place} = {op} {operand_place}"  
        self.logger.debug(f"Emitting Unary Op: {instruction}")  
        self.emit(instruction)  
      
    def emitAssignment(self, dest_place: str, source_place: str):  
        """  
        Emit an assignment instruction.  
          
        Args:  
            dest_place: The destination place  
            source_place: The source place  
        """  
        instruction = f"{dest_place} = {source_place}"  
        self.logger.debug(f"Emitting Assignment: {instruction}")  
        self.emit(instruction)  
      
    def emitProcStart(self, proc_name: str):  
        """  
        Emit a procedure start directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        instruction = f"proc {proc_name}"  
        self.logger.info(f"Emitting Procedure Start: {instruction}")  
        self.emit(instruction)  
        # Reset temporary counter for this procedure's scope  
        self.temp_counter = 0  
        self.logger.debug(f"Temporary counter reset for procedure '{proc_name}'")  
      
    def emitProcEnd(self, proc_name: str):  
        """  
        Emit a procedure end directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        instruction = f"endp {proc_name}"  
        self.logger.info(f"Emitting Procedure End: {instruction}")  
        self.emit(instruction)  
      
    def emitPush(self, place: str, mode: ParameterMode):  
        """  
        Emit a push instruction for procedure calls.  
          
        Args:  
            place: The place to push (value or address source)  
            mode: The parameter mode (IN, OUT, INOUT)  
        """  
        # For OUT or INOUT parameters, push the address (pass by reference)  
        if mode in (ParameterMode.OUT, ParameterMode.INOUT):  
            instruction = f"push @{place}"  # Indicate address push  
            self.logger.debug(f"Emitting Push Address ({mode.name}): {instruction}")  
        else:  
            # For IN parameters, push the value (pass by value)  
            instruction = f"push {place}"  
            self.logger.debug(f"Emitting Push Value ({mode.name}): {instruction}")  
        self.emit(instruction)  
      
    def emitCall(self, proc_name: str):  
        """  
        Emit a procedure call instruction.  
          
        Args:  
            proc_name: The name of the procedure to call  
        """  
        instruction = f"call {proc_name}"  
        self.logger.debug(f"Emitting Call: {instruction}")  
        self.emit(instruction)  
      
    def emitRead(self, place: str):
        """
        Emit a read instruction (for GET).
        
        Args:
            place: The destination place for the input
        """
        instruction = f"read {place}"
        self.logger.debug(f"Emitting Read: {instruction}")
        self.emit(instruction)
        
    def emitWrite(self, place: str):
        """
        Emit a write instruction (for PUT).
        
        Args:
            place: The source place to output
        """
        instruction = f"write {place}"
        self.logger.debug(f"Emitting Write: {instruction}")
        self.emit(instruction)
      
    def emitProgramStart(self, main_proc_name: str):  
        """  
        Record the outermost procedure name for the final 'start' directive.  
          
        Args:  
            main_proc_name: The name of the main procedure  
        """  
        self.logger.info(f"Recording program start procedure: '{main_proc_name}'")  
        self.start_proc_name = main_proc_name  
      
    def writeOutput(self) -> bool:  
        """  
        Write the TAC instructions to the output file.  
          
        Returns:  
            True if successful, False otherwise  
        """  
        self.logger.info(f"Attempting to write {len(self.tac_lines)} TAC instructions to '{self.output_filename}'...")  
        try:  
            # Ensure the output directory exists  
            output_path = Path(self.output_filename)  
            output_path.parent.mkdir(parents=True, exist_ok=True)  
  
            with open(output_path, 'w', encoding='utf-8') as f:  
                # Write all collected TAC instructions  
                for line in self.tac_lines:  
                    f.write(f"{line}\n")  
  
                # Write START directive as the last line, if recorded  
                if self.start_proc_name:  
                    start_instruction = f"start {self.start_proc_name}"  
                    f.write(f"{start_instruction}\n")  
                    self.logger.debug(f"Wrote Start Directive: {start_instruction}")  
                else:  
                    # This should ideally be caught earlier by the driver or parser logic  
                    self.logger.error("No start procedure name was recorded. TAC output may be incomplete.")  
                    # Optionally raise an error or return False here? For now, just log error.  
  
            self.logger.info(f"TAC output successfully written to '{self.output_filename}'")  
            return True  
        except IOError as e:  # Catch specific IO errors  
            self.logger.error(f"IOError writing TAC output to '{self.output_filename}': {e}")  
            return False  
        except Exception as e:  # Catch any other unexpected errors  
            self.logger.error(f"Unexpected error writing TAC output to '{self.output_filename}': {e}")  
            # Optionally log traceback for unexpected errors  
            # import traceback  
            # self.logger.error(traceback.format_exc())  
            return False  
      
    def map_ada_op_to_tac(self, ada_op: str) -> str:  
        """  
        Map Ada operators (lexemes) to TAC operator strings.  
          
        Args:  
            ada_op: The Ada operator lexeme (e.g., '+', 'mod', 'and')  
              
        Returns:  
            The corresponding TAC operator string (e.g., 'ADD', 'MOD', 'AND').  
            Returns the original operator if no mapping is found.  
        """  
        ada_op_lower = ada_op.lower()  # Ensure case-insensitivity for keywords  
        mapping = {  
            '+': 'ADD',  
            '-': 'SUB',  
            '*': 'MUL',  
            '/': 'DIV',    # Floating point or integer division? Assumed context-dependent for now.  
            'div': 'IDIV', # Explicit integer division if lexer distinguishes  
            'mod': 'MOD',  
            'rem': 'REM',  
            'and': 'AND',  
            'or': 'OR',  
            'not': 'NOT',  
            # Relational operators might map differently (e.g., to conditional jumps)  
            # For direct boolean result TAC:  
            '=': 'EQ',  
            '/=': 'NE',  
            '<': 'LT',  
            '<=': 'LE',  
            '>': 'GT',  
            '>=': 'GE'  
        }  
        tac_op = mapping.get(ada_op_lower, ada_op)  # Default to original if no map  
        self.logger.debug(f"Mapped Ada op '{ada_op}' to TAC op '{tac_op}'")  
        return tac_op