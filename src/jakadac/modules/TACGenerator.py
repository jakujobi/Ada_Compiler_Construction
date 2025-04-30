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
        self.logger = logger  
        self.logger.info(f"TAC Generator initialized. Output file: '{output_filename}'")  
      
    def emit(self, instruction_str: str):  
        """  
        Emit a TAC instruction.  
          
        Args:  
            instruction_str: The instruction string to emit  
        """  
        self.tac_lines.append(instruction_str)  
        self.logger.debug(f"Emitted TAC: {instruction_str}")  
      
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
        Get the place string for a symbol or value.  
          
        Args:  
            symbol_or_value: Symbol object, literal value, or temporary  
              
        Returns:  
            String representation for TAC operand/result  
        """  
        place_str = "ERROR_UNKNOWN_PLACE"  # Default  
        self.logger.debug(f"Getting place for: {symbol_or_value} (type: {type(symbol_or_value)})")  
  
        # Handle literals (strings or numbers)  
        if isinstance(symbol_or_value, (int, float)):  
            place_str = str(symbol_or_value)  
            self.logger.debug(f" -> Literal Number Place: {place_str}")  
        elif isinstance(symbol_or_value, str):  
            if symbol_or_value.startswith("_t"):  
                # It's a temporary variable, return as is  
                place_str = symbol_or_value  
                self.logger.debug(f" -> Temporary Place: {place_str}")  
            else:  
                # It's likely a string literal or potentially an error/lexeme  
                # Assuming string literals aren't directly handled yet, treat as identifier/error?  
                # For now, let's assume it could be an undeclared identifier's lexeme  
                place_str = symbol_or_value  # Keep original string if not temp  
                self.logger.debug(f" -> String/Lexeme Place: {place_str}")  
  
        # Handle symbols from symbol table  
        elif isinstance(symbol_or_value, Symbol):  
            symbol = symbol_or_value  
            self.logger.debug(f" -> Symbol Place for '{symbol.name}' (Type: {symbol.entry_type.name}, Depth: {symbol.depth}, Offset: {symbol.offset})")  
  
            # Handle constants - use their value directly  
            if symbol.entry_type == EntryType.CONSTANT and symbol.const_value is not None:  
                place_str = str(symbol.const_value)  
                self.logger.debug(f"  -> Constant Value Place: {place_str}")  
            # Global variables (assuming depth 0 or 1 based on your convention) use names  
            # Adjust depth check based on your specific convention (0 or 1 for globals)  
            elif symbol.depth <= 1:  # Assuming depth 0/1 are global/outermost procedure vars  
                place_str = symbol.name  
                self.logger.debug(f"  -> Global/Outer Variable Place: {place_str}")  
            # Depth > 1 variables and parameters use BP-relative addressing  
            elif symbol.offset is not None:  
                if symbol.entry_type == EntryType.PARAMETER:  
                    place_str = f"_BP+{symbol.offset}"  
                    self.logger.debug(f"  -> Parameter Place (BP Relative): {place_str}")  
                else:  # Local variable  
                    place_str = f"_BP-{abs(symbol.offset)}"  
                    self.logger.debug(f"  -> Local Variable Place (BP Relative): {place_str}")  
            else:  
                # Shouldn't get here if symbol table is properly populated  
                self.logger.error(f"Symbol '{symbol.name}' has no offset defined, cannot determine place.")  
                place_str = f"ERROR_NO_OFFSET_{symbol.name}"  
  
        # Default case for unknown types  
        else:  
            self.logger.warning(f"Unknown type encountered in getPlace: {type(symbol_or_value)}. Using string representation.")  
            place_str = str(symbol_or_value)  
  
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
        self.logger.info(f"Emitting Procedure Start: {instruction}")  # Info level for procedure boundaries  
        self.emit(instruction)  
        # Reset temporary counter for this procedure  
        self.temp_counter = 0  
        self.logger.debug("Reset temporary counter for new procedure.")  
      
    def emitProcEnd(self, proc_name: str):  
        """  
        Emit a procedure end directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        instruction = f"endp {proc_name}"  
        self.logger.info(f"Emitting Procedure End: {instruction}")  # Info level  
        self.emit(instruction)  
      
    def emitPush(self, place: str, mode: ParameterMode):  
        """  
        Emit a push instruction for procedure calls.  
          
        Args:  
            place: The place to push  
            mode: The parameter mode (IN, OUT, INOUT)  
        """  
        push_operand = ""  
        log_detail = ""  
        # For OUT or INOUT parameters, push the address (pass by reference)  
        if mode in (ParameterMode.OUT, ParameterMode.INOUT):  
            push_operand = f"@{place}"  # Assuming '@' denotes address-of  
            log_detail = f"(Pass by Reference for {mode.name})"  
        else:  # IN parameters  
            push_operand = place  
            log_detail = f"(Pass by Value for {mode.name})"  
  
        instruction = f"push {push_operand}"  
        self.logger.debug(f"Emitting Push: {instruction} {log_detail}")  
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
      
    def emitProgramStart(self, main_proc_name: str):  
        """  
        Store the outermost procedure name for the start directive.  
          
        Args:  
            main_proc_name: The name of the main procedure  
        """  
        self.logger.info(f"Setting program start procedure: {main_proc_name}")  
        self.start_proc_name = main_proc_name  
      
    def writeOutput(self) -> bool:  
        """  
        Write the TAC instructions to the output file.  
          
        Returns:  
            True if successful, False otherwise  
        """  
        self.logger.info(f"Attempting to write {len(self.tac_lines)} TAC lines to {self.output_filename}")  
        # Check if start procedure was set before writing  
        if self.start_proc_name is None:  
            self.logger.error("Cannot write TAC output: Start procedure name was never set.")  
            # Optionally raise an error to signal failure more strongly  
            raise RuntimeError("Start procedure name not set before writing TAC output.")  
            # return False # Or just return false if raising is too harsh  
  
        try:  
            output_path = Path(self.output_filename)  
            # Ensure the directory exists  
            output_path.parent.mkdir(parents=True, exist_ok=True)  
            self.logger.debug(f"Writing TAC to: {output_path.resolve()}")  
  
            with open(output_path, 'w') as f:  
                self.logger.debug("Writing main TAC instructions...")  
                for i, line in enumerate(self.tac_lines):  
                    f.write(f"{line}\n")  
                    self.logger.debug(f" -> Wrote line {i+1}: {line}")  
  
                # Write START directive as the last line  
                start_instruction = f"start {self.start_proc_name}"  
                self.logger.debug(f"Writing start directive: {start_instruction}")  
                f.write(f"{start_instruction}\n")  
  
            self.logger.info(f"TAC output successfully written to {self.output_filename}")  
            return True  
        except IOError as e:  # Catch specific file errors  
            self.logger.error(f"Error writing TAC output file '{self.output_filename}': {e}")  
            return False  
        except Exception as e:  # Catch any other unexpected errors  
            self.logger.error(f"An unexpected error occurred during TAC writing: {e}")  
            import traceback  
            self.logger.debug(f"Traceback:\n{traceback.format_exc()}")  # Add traceback on debug  
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
            '/': 'DIV',  # Use DIV for float division? Or separate IDIV? Assuming general DIV for now.  
            # 'div': 'IDIV', # Integer division if needed  
            'mod': 'MOD',  
            'rem': 'REM',  
            'and': 'AND',  
            'or': 'OR',  
            'not': 'NOT',  
            # Add relational ops if needed by parser later  
            # '=': 'EQ', '/=': 'NE', '<': 'LT', '<=': 'LE', '>': 'GT', '>=': 'GE'  
        }  
        original_op = ada_op  # Keep original for logging  
        tac_op = mapping.get(original_op.lower(), original_op)  # Map lowercase, default to original if no map  
        self.logger.debug(f"Mapped Ada operator '{original_op}' to TAC operator '{tac_op}'")  
        return tac_op