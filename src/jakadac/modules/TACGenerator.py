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
        
        # Track procedure declarations for reordering
        self.proc_declarations = {}
        self.current_proc = None
        self.pending_main_proc = None
        self.main_proc_instructions = []
        
        self.logger = logger  
        self.logger.info(f"TAC Generator initialized. Output Target: '{self.output_filename}'")  
      
    def emit(self, instruction_str: str):  
        """  
        Emit a TAC instruction.  
          
        Args:  
            instruction_str: The instruction string to emit  
        """  
        # If we're in the main procedure, add to deferred list
        if self.pending_main_proc and self.current_proc == self.pending_main_proc:
            self.main_proc_instructions.append(instruction_str)
            self.logger.debug(f"Added to deferred main proc: {instruction_str}")
        else:
            # Regular emit - add to tac_lines directly
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
      
    def getPlace(self, symbol_or_value, current_proc_depth: Optional[int] = None) -> str:  
        """  
        Get the place string for a symbol or value for use in TAC.
        Uses current_proc_depth to differentiate between local and outer-scope variables.
        
        Args:
            symbol_or_value: Symbol object, literal value, or temporary name (str)
            current_proc_depth: The depth of the procedure currently being parsed.
                              None if not currently inside a procedure scope.
                              Depth 0 represents the global/outermost procedure scope.
          
        Returns:
            String representation for TAC operand/result (e.g., 'x', '5', '_t1', '_BP+4').
        """
        self.logger.debug(f"Getting place for: {symbol_or_value} (Type: {type(symbol_or_value)}), Current Proc Depth: {current_proc_depth}")

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

            # Handle Variables/Parameters based on scope depth
            elif symbol.entry_type in (EntryType.VARIABLE, EntryType.PARAMETER) and symbol.offset is not None:
                if current_proc_depth is None: # Should not happen if parsing structured code
                    self.logger.error(f"getPlace called for {symbol.name} outside a procedure scope. Using name.")
                    place_str = symbol.name
                elif symbol.depth == current_proc_depth + 1:
                    # LOCAL to the current procedure: Use BP Offset
                    if symbol.entry_type == EntryType.PARAMETER:
                        # Positive offset for parameters relative to BP
                        place_str = f"_BP+{symbol.offset}"
                        self.logger.debug(f"Place for LOCAL PARAMETER '{symbol.name}' (Depth {symbol.depth}) is BP offset: {place_str}")
                    else: # VARIABLE
                        # Negative offset for local variables relative to BP
                        offset_val = symbol.offset # Assume offset is already negative
                        if offset_val > 0: # Safety check if offset logic was positive
                             self.logger.warning(f"Local variable '{symbol.name}' offset {symbol.offset} is positive, expected negative. Using as is.")
                        place_str = f"_BP{offset_val}" 
                        self.logger.debug(f"Place for LOCAL VARIABLE '{symbol.name}' (Depth {symbol.depth}) is BP offset: {place_str}")
                elif symbol.depth <= current_proc_depth:
                    # From an ENCLOSING scope (including global depth 0): Use Name
                    # Note: Depth 0 variables are handled implicitly here if current_proc_depth >= 0
                    place_str = symbol.name
                    self.logger.debug(f"Place for ENCLOSING SCOPE Symbol '{symbol.name}' (Declared Depth {symbol.depth}, Current Depth {current_proc_depth}) is name: {place_str}")
                else:
                    # Should not happen with correct parsing/symbol table depth tracking
                    self.logger.error(f"Unexpected depth scenario for Symbol '{symbol.name}' (Declared Depth {symbol.depth}, Current Depth {current_proc_depth}). Using name.")
                    place_str = symbol.name
        
            # Handle Procedure/Function names (typically just use the name)
            elif symbol.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                 place_str = symbol.name 
                 self.logger.debug(f"Place for PROCEDURE/FUNCTION Symbol '{symbol.name}' is name: {place_str}")

            # Handle other unexpected symbol types or symbols without offsets
            else:
                if symbol.offset is None and symbol.entry_type not in (EntryType.CONSTANT, EntryType.PROCEDURE, EntryType.FUNCTION):
                    self.logger.error(f"Symbol '{symbol.name}' (Depth {symbol.depth}, Type {symbol.entry_type}) has no offset defined. Using name as place.")
                else:
                    self.logger.warning(f"Unhandled case for Symbol '{symbol.name}' (Depth {symbol.depth}, Type {symbol.entry_type}). Using name as place.")
                place_str = symbol.name

        # Handle direct strings (e.g., from expression parsing results that aren't temps or symbols)
        elif isinstance(symbol_or_value, str):
             self.logger.debug(f"Getting place for a raw string value: '{symbol_or_value}'")
             place_str = symbol_or_value # Assume it's a literal or already processed place

        # Log the final place decision
        self.logger.debug(f"==> Final Place determined: {place_str}")
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
        
        # Track the current procedure for instruction sorting
        self.current_proc = proc_name
        
        # Check if this is the main procedure (outermost)
        if self.start_proc_name == proc_name:
            self.pending_main_proc = proc_name
            self.main_proc_instructions = []  # Clear any old instructions
            self.logger.debug(f"Main procedure '{proc_name}' declarations will be deferred")
            self.main_proc_instructions.append(instruction)  # Add to main proc instructions
        else:
            # This is an inner procedure - emit directly
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
        
        # If this is the end of the main procedure, store it but don't emit yet
        if self.pending_main_proc == proc_name:
            self.main_proc_instructions.append(instruction)
            self.logger.debug(f"Added end directive for main procedure '{proc_name}' to deferred list")
        else:
            # Inner procedure - emit directly
            self.emit(instruction)
            
        # Reset current procedure tracking
        self.current_proc = None
      
    def emitPush(self, place: str, mode: ParameterMode):  
        """  
        Emit a push instruction for procedure calls.  
        NOTE: Simplified to always emit 'push' based on exp_test75.tac format.
        The 'mode' argument is kept for potential future use or debugging.
        
        Args:  
            place: The place to push (value, address source, or name)  
            mode: The parameter mode (currently ignored for instruction generation)
        """  
        # Always emit 'push' instruction, using the provided place directly
        instruction = f"push {place}"
        self.logger.debug(f"Emitting Push (Mode: {mode.name}): {instruction}")  
        self.emit(instruction)
        
        # --- Original logic (commented out) ---
        # # For OUT or INOUT parameters, push the address (pass by reference)  
        # if mode in (ParameterMode.OUT, ParameterMode.INOUT):  
        #     instruction = f"push @{place}"  # Indicate address push  
        #     self.logger.debug(f"Emitting Push Address ({mode.name}): {instruction}")  
        # else:  
        #     # For IN parameters, push the value (pass by value)  
        #     instruction = f"push {place}"  
        #     self.logger.debug(f"Emitting Push Value ({mode.name}): {instruction}")  
        # self.emit(instruction)  
      
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
        Record the outermost procedure name for the final 'start' directive. # REVERTED
          
        Args:  
            main_proc_name: The name of the main procedure  
        """  
        self.logger.info(f"Recording program start procedure: '{main_proc_name}'")  
        self.start_proc_name = main_proc_name # REVERTED 
        # --- REMOVED: Emit start instruction directly --- 
        # start_instruction = f"start proc {main_proc_name}"
        # self.logger.debug(f"Emit TAC: {start_instruction}")
        # self.emit(start_instruction) 
      
    def writeOutput(self) -> bool:  
        """  
        Write the TAC instructions to the output file.  
          
        Returns:  
            True if successful, False otherwise  
        """  
        # Add any deferred main procedure instructions AFTER all other procedure declarations
        if self.main_proc_instructions:
            self.logger.info(f"Appending {len(self.main_proc_instructions)} deferred instructions for main procedure '{self.pending_main_proc}'")
            self.tac_lines.extend(self.main_proc_instructions)
            
        self.logger.info(f"Attempting to write {len(self.tac_lines)} TAC instructions to '{self.output_filename}'...")

        # Append the final START PROC instruction if a start procedure was identified
        if self.start_proc_name:
            start_instruction = f"START\tPROC\t{self.start_proc_name}"
            self.tac_lines.append(start_instruction)
            self.logger.debug(f"Appended final START instruction: {start_instruction}")
        else:
            self.logger.warning("No start procedure name was recorded; cannot emit START PROC directive.")

        try:  
            # Ensure the output directory exists  
            output_path = Path(self.output_filename)  
            output_path.parent.mkdir(parents=True, exist_ok=True)  
  
            with open(output_path, 'w', encoding='utf-8') as f:  
                # Write all collected TAC instructions  
                for line in self.tac_lines:  
                    f.write(f"{line}\n")  
  
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