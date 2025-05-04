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
        self.tac_lines: List[Union[str, tuple]] = []    # List of TAC instructions (can be tuple or string)  
        self.start_proc_name = None  # Store the outermost procedure name  
        self.string_literals: Dict[str, str] = {} # For storing string labels -> values  
        self.string_label_counter = 0 # For generating unique string labels  
        
        # Track procedure declarations for reordering  
        self.proc_declarations = {}  
        self.current_proc = None  
        self.pending_main_proc = None  
        self.main_proc_instructions: List[Union[str, tuple]] = [] # Store tuples or strings  
        
        self.logger = logger  
        self.logger.info(f"TAC Generator initialized. Output Target: '{self.output_filename}'")  
      
    def _format_instruction(self, instruction: Union[str, tuple]) -> str:  
        """Formats a TAC instruction tuple into a string."""  
        if isinstance(instruction, str):  
            return instruction # Already formatted  
        elif isinstance(instruction, tuple):  
            op = instruction[0]  
            args = instruction[1:]  
            if op in ('rdi', 'wri', 'wrs', 'push', 'call', 'proc', 'endp', 'START PROC'): # Instructions with 1 arg  
                return f"{op} {args[0]}"  
            elif op in ('wrln',): # Instructions with 0 args  
                return op  
            elif op == '=': # Assignment  
                if len(args) == 2:  
                    return f"{args[0]} = {args[1]}"  
                elif len(args) == 3: # Unary op assignment  
                    return f"{args[0]} = {args[1]} {args[2]}"  
            elif op in ('+', '-', '*', '/', 'mod', 'rem', 'and', 'or'): # Binary op assignment  
                if len(args) == 3:  
                    return f"{args[0]} = {args[1]} {op} {args[2]}"  
            # Add other formatting rules as needed  
            self.logger.warning(f"Unrecognized TAC tuple format: {instruction}. Using default format.")  
            return " ".join(map(str, instruction))  
        else:  
            self.logger.error(f"Cannot format non-string/non-tuple instruction: {instruction}")  
            return "ERROR_FORMATTING"  
      
    def emit(self, instruction: Union[str, tuple]):  
        """  
        Emit a TAC instruction (tuple preferred).  
          
        Args:  
            instruction: The instruction tuple or string to emit  
        """  
        # Format the instruction for logging and potentially for immediate list storage  
        # instruction_str = self._format_instruction(instruction)  
      
        if self.pending_main_proc and self.current_proc == self.pending_main_proc:  
            self.main_proc_instructions.append(instruction) # Store tuple/string  
            self.logger.debug(f"Added to deferred main proc: {instruction}")  
        else:  
            self.tac_lines.append(instruction) # Store tuple/string  
            self.logger.debug(f"Emit TAC: {instruction}")  
      
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
                 # Check if it's a string literal constant (using label as name)
                 if isinstance(symbol.const_value, str) and symbol.name.startswith("_S"):
                     place_str = symbol.name # Use the label as the place
                     self.logger.debug(f"Place for STRING CONSTANT '{symbol.name}' is label: {place_str}")
                 else:
                    place_str = str(symbol.const_value)
                    self.logger.debug(f"Place for CONSTANT '{symbol.name}' is value: {place_str}")

            # Handle Variables/Parameters based on scope depth
            elif symbol.entry_type in (EntryType.VARIABLE, EntryType.PARAMETER) and symbol.offset is not None:
                if current_proc_depth is None: # Should not happen if parsing structured code
                    self.logger.error(f"getPlace called for {symbol.name} outside a procedure scope. Using name.")
                    place_str = symbol.name
                # Check if symbol belongs to the current procedure's scope (depth + 1)
                elif symbol.depth == (current_proc_depth + 1 if current_proc_depth is not None else 0):
                    # LOCAL to the current procedure: Use BP Offset
                    if symbol.entry_type == EntryType.PARAMETER:
                        # Positive offset for parameters relative to BP
                        place_str = f"_BP+{symbol.offset}"
                        self.logger.debug(f"Place for LOCAL PARAMETER '{symbol.name}' (Depth {symbol.depth}) is BP offset: {place_str}")
                    else: # VARIABLE
                        # Negative offset for local variables relative to BP
                        offset_val = symbol.offset # Assume offset is already negative or 0
                        if offset_val > 0: # Safety check if offset logic was positive for locals
                             self.logger.warning(f"Local variable '{symbol.name}' offset {symbol.offset} is positive, expected negative or zero. Using as is.")
                        # Use _BP-N for negative offsets, _BP for offset 0 (potentially first local)
                        place_str = f"_BP{offset_val}" if offset_val < 0 else f"_BP+{offset_val}" # Or just _BP if 0?
                        self.logger.debug(f"Place for LOCAL VARIABLE '{symbol.name}' (Depth {symbol.depth}) is BP offset: {place_str}")
                # Check if symbol belongs to an enclosing scope (including global 0)
                elif current_proc_depth is not None and symbol.depth <= current_proc_depth:
                    # From an ENCLOSING scope (including global depth 0): Use Name
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
             # Check if it looks like a BP offset
             if symbol_or_value.startswith("_BP"):
                 place_str = symbol_or_value
             # Assume it's a literal, temp, or global name otherwise
             else:
                 place_str = symbol_or_value

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
        instruction = (op, dest_place, left_place, right_place)  
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
        instruction = ('=', dest_place, op, operand_place)  
        self.logger.debug(f"Emitting Unary Op: {instruction}")  
        self.emit(instruction)  
      
    def emitAssignment(self, dest_place: str, source_place: str):  
        """  
        Emit an assignment instruction.  
          
        Args:  
            dest_place: The destination place  
            source_place: The source place  
        """  
        instruction = ('=', dest_place, source_place)  
        self.logger.debug(f"Emitting Assignment: {instruction}")  
        self.emit(instruction)  
      
    def emitProcStart(self, proc_name: str):  
        """  
        Emit a procedure start directive.  
          
        Args:  
            proc_name: The name of the procedure  
        """  
        instruction = ('proc', proc_name)  
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
        instruction = ('endp', proc_name)  
        self.logger.info(f"Emitting Procedure End: {instruction}")  
        
        # If ending the deferred main procedure, append endp and process  
        if self.pending_main_proc and self.current_proc == self.pending_main_proc:  
            self.main_proc_instructions.append(instruction)  
            # Reorder instructions: main procedure first, then others  
            self.tac_lines = self.main_proc_instructions + self.tac_lines  
            self.logger.debug(f"Deferred main procedure '{proc_name}' ended and instructions prepended.")  
            self.pending_main_proc = None # Reset pending flag  
            self.main_proc_instructions = []  
        else:  
            self.emit(instruction)  
            
        # Reset current_proc context if needed (optional, might be handled by caller)  
        # self.current_proc = None  
      
    def emitPush(self, place: str, mode: ParameterMode):  
        """  
        Emit a push instruction for a parameter.  
        Handles adding '@' for OUT/INOUT parameters.  
        Format: ('push', place_or_addr)  
        """  
        operand = place  
        if mode in (ParameterMode.OUT, ParameterMode.INOUT):  
            # Check if place is already an address (e.g., global variable name)  
            # This logic might be tricky. Assume getPlace provides the correct base name.  
            # Let ASM generator handle dereferencing globals vs. locals.  
            operand = f"@{place}"  
            self.logger.debug(f"Pushing address for OUT/INOUT param: {operand}")  
        else:  
            self.logger.debug(f"Pushing value for IN param: {operand}")  

        instruction = ('push', operand)  
        self.emit(instruction)  
      
    def emitCall(self, proc_name: str):  
        """  
        Emit a call instruction.  
          
        Args:  
            proc_name: The name of the procedure to call  
        """  
        instruction = ('call', proc_name)  
        self.logger.debug(f"Emitting Call: {instruction}")  
        self.emit(instruction)  
      
    # --- New I/O Methods ---  
    def emitRead(self, place: str):  
        """  
        Emit a read integer instruction.  
        Format: ('rdi', place)  
        """  
        instruction = ('rdi', place)  
        self.logger.info(f"Emitting Read Int: {instruction}")  
        self.emit(instruction)  
      
    def emitWrite(self, place: str):  
        """  
        Emit a write integer instruction.  
        Format: ('wri', place)  
        """  
        # Semantic check: Is place likely an integer? (Best effort)  
        # Could check symbol table type if place is a symbol name  
        instruction = ('wri', place)  
        self.logger.info(f"Emitting Write Int: {instruction}")  
        self.emit(instruction)  
      
    def emitWriteString(self, string_value: str):  
        """  
        Emit a write string instruction.  
        Generates a label, stores the string, and emits 'wrs'.  
        Format: ('wrs', label)  
        """  
        # Generate label  
        label = f"_S{self.string_label_counter}"  
        self.string_label_counter += 1  

        # Store processed string value with terminator  
        processed_value = string_value # Assuming parser already processed escapes  
        if not processed_value.endswith('$'):  
             processed_value += '$'  
        self.string_literals[label] = processed_value  
        self.logger.debug(f"Stored string literal: {label} -> \"{processed_value}\"")  

        # Emit instruction  
        instruction = ('wrs', label)  
        self.logger.info(f"Emitting Write String: {instruction}")  
        self.emit(instruction)  
      
    def emitNewLine(self):  
        """  
        Emit a write newline instruction.  
        Format: ('wrln',)  
        """  
        instruction = ('wrln',)  
        self.logger.info(f"Emitting Write Newline: {instruction}")  
        self.emit(instruction)  
    # --- End New I/O Methods ---  
      
    def emitProgramStart(self, main_proc_name: str):  
        """  
        Emit the START PROC directive after all code.  
        This now just records the main procedure name for reordering logic.  
        Format: ('START PROC', main_proc_name)  
        """  
        # Store the name of the procedure designated as the program entry point  
        self.start_proc_name = main_proc_name  
        self.logger.info(f"Program entry point set to: '{main_proc_name}'")  
        # The actual START PROC line is added during writeOutput  
      
    def get_string_literals(self) -> Dict[str, str]:  
        """Returns the dictionary of stored string literals (label -> value)."""  
        return self.string_literals.copy()  
      
    def writeOutput(self) -> bool:  
        """  
        Write the generated TAC instructions to the output file.  
        Handles reordering and adding START PROC.  
        Returns True on success, False on failure.  
        """  
        self.logger.info(f"Writing TAC output to: {self.output_filename}")  

        # Ensure main procedure (if deferred) is processed  
        if self.pending_main_proc:  
             self.logger.warning(f"Main procedure '{self.pending_main_proc}' was started but not ended. Appending instructions.")  
             # Append an endp if missing?  
             if not self.main_proc_instructions or self.main_proc_instructions[-1] != ('endp', self.pending_main_proc):  
                  self.main_proc_instructions.append(('endp', self.pending_main_proc))  
             self.tac_lines = self.main_proc_instructions + self.tac_lines  
             self.pending_main_proc = None  

        # Add START PROC directive at the end if a start procedure was identified  
        if self.start_proc_name:  
            start_instruction = ('START PROC', self.start_proc_name)  
            self.tac_lines.append(start_instruction)  
            self.logger.debug(f"Appended final instruction: {start_instruction}")  
        else:  
            self.logger.warning("No start procedure was designated (emitProgramStart never called).")  

        try:  
            # Ensure output directory exists  
            output_dir = Path(self.output_filename).parent  
            output_dir.mkdir(parents=True, exist_ok=True)  
  
            with open(self.output_filename, 'w') as f:  
                for instruction in self.tac_lines:  
                    formatted_line = self._format_instruction(instruction)  
                    f.write(formatted_line + '\n')  
            self.logger.info(f"Successfully wrote {len(self.tac_lines)} TAC lines.")  
            return True  
        except IOError as e:  
            self.logger.error(f"Failed to write TAC file '{self.output_filename}': {e}")  
            return False  
        except Exception as e:  
            self.logger.error(f"An unexpected error occurred during TAC writing: {e}")  
            return False