#!/usr/bin/env python3
# asm_instruction_mapper.py
# Author: AI Assistant
# Date: 2024-05-08
# Version: 1.0
"""
ASM Instruction Mapper for ASM Generation.
Maps TAC instructions to 8086 assembly instructions.
"""

from typing import List, Optional, Dict
import logging
import re
# Import TACInstruction from the correct path
try:
    from .tac_instruction import TACInstruction  # Relative import in package
except ImportError:
    # Fallback if relative import fails
    from tac_instruction import TACInstruction  # Direct import

# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if run standalone or not configured elsewhere
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ASMInstructionMapper:
    """
    Maps TAC instructions to 8086 assembly instruction sequences.
    Handles operand formatting and dereferencing logic.
    """
    
    def __init__(self, formatter, symbol_table):
        """
        Initialize with an ASMOperandFormatter and SymbolTable instance.
        
        Args:
            formatter: ASMOperandFormatter instance for operand formatting
            symbol_table: SymbolTable instance for procedure info lookup
        """
        self.formatter = formatter
        self.symbol_table = symbol_table
        
    def translate(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a TAC instruction to ASM instruction sequence.
        
        Args:
            instr: TACInstruction to translate
            current_proc_symbol: Symbol for the current procedure or None
            
        Returns:
            List of ASM instruction strings
        """
        # Add a comment with the original TAC instruction for readability
        comment = f"; -- {instr.original_tuple} --"
        
        # Choose the appropriate translation method based on opcode
        method_name = f"_translate_{instr.opcode.lower()}"
        
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            result = method(instr, current_proc_symbol)
            if result:
                return [comment] + result
            return [comment]  # Empty result (e.g., for 'start_proc')
            
        # If no specific method, log a warning and return just the comment
        logger.warning(f"No translation method for opcode: {instr.opcode}")
        return [comment, f"; -- WARNING: No translation available for {instr.opcode} --"]
    
    def _translate_assign(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate an assignment instruction (='s op1 is the source, dest is the destination).
        
        Args:
            instr: Assignment instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        # Format operands
        dest_asm = self.formatter.format_operand(instr.dest)
        src_asm = self.formatter.format_operand(instr.op1)
        
        asm_lines = []
        
        # Handle dereferencing for parameters by reference
        if src_asm.startswith('[bp+'):
            # Source is a parameter by reference (address)
            asm_lines.append(f" mov bx, {src_asm}")
            asm_lines.append(f" mov ax, [bx]")
        else:
            # Source is a direct value or memory location
            asm_lines.append(f" mov ax, {src_asm}")
            
        # Handle destination dereferencing for parameters by reference
        if dest_asm.startswith('[bp+'):
            # Destination is a parameter by reference (address)
            asm_lines.append(f" mov bx, {dest_asm}")
            asm_lines.append(f" mov [bx], ax")
        else:
            # Destination is a direct memory location
            asm_lines.append(f" mov {dest_asm}, ax")
            
        return asm_lines
        
    def _translate_binary_op(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a binary operation instruction.
        
        Args:
            instr: Binary operation instruction (opcode in +, -, *, /, etc.)
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        dest_asm = self.formatter.format_operand(instr.dest)
        op1_asm = self.formatter.format_operand(instr.op1)
        op2_asm = self.formatter.format_operand(instr.op2)
        
        asm_lines = []
        
        # Load op1 into AX
        if op1_asm.startswith('[bp+'):
            # op1 is a parameter by reference (address)
            asm_lines.append(f" mov bx, {op1_asm}")
            asm_lines.append(f" mov ax, [bx]")
        else:
            # op1 is a direct value or memory location
            asm_lines.append(f" mov ax, {op1_asm}")
            
        # Special handling for different operations
        if instr.opcode == '*':
            # MUL requires special handling
            if op2_asm.startswith('[bp+'):
                # op2 is a parameter by reference (address)
                asm_lines.append(f" mov bx, {op2_asm}")
                asm_lines.append(f" mov bx, [bx]")
            else:
                # op2 is a direct value or memory location
                asm_lines.append(f" mov bx, {op2_asm}")
                
            # Multiply AX by BX, result in DX:AX (we'll just use AX)
            asm_lines.append(f" imul bx")
        elif instr.opcode == '/':
            # DIV requires special handling
            asm_lines.append(f" cwd")  # Sign-extend AX into DX:AX
            
            if op2_asm.startswith('[bp+'):
                # op2 is a parameter by reference (address)
                asm_lines.append(f" mov bx, {op2_asm}")
                asm_lines.append(f" mov bx, [bx]")
            else:
                # op2 is a direct value or memory location
                asm_lines.append(f" mov bx, {op2_asm}")
                
            # Divide DX:AX by BX, quotient in AX, remainder in DX
            asm_lines.append(f" idiv bx")
        else:
            # For ADD, SUB, operations
            # Handle op2 loading
            is_immediate = re.match(r'^-?\d+$', op2_asm)
            
            if op2_asm.startswith('[bp+'):
                # op2 is a parameter by reference (address)
                asm_lines.append(f" mov bx, {op2_asm}")
                asm_lines.append(f" mov bx, [bx]")
                # Perform operation with BX
                asm_lines.append(f" {self._get_asm_opcode(instr.opcode)} ax, bx")
            elif is_immediate:
                # op2 is an immediate value, can use directly with ADD/SUB
                asm_lines.append(f" {self._get_asm_opcode(instr.opcode)} ax, {op2_asm}")
            else:
                # op2 is a direct memory location
                asm_lines.append(f" mov bx, {op2_asm}")
                asm_lines.append(f" {self._get_asm_opcode(instr.opcode)} ax, bx")
        
        # Store result from AX to dest
        if dest_asm.startswith('[bp+'):
            # dest is a parameter by reference (address)
            asm_lines.append(f" mov bx, {dest_asm}")
            asm_lines.append(f" mov [bx], ax")
        else:
            # dest is a direct memory location
            asm_lines.append(f" mov {dest_asm}, ax")
            
        return asm_lines
    
    def _translate_proc(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a procedure declaration.
        
        Args:
            instr: Procedure declaration instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        proc_name = instr.op1
        
        try:
            # Lookup the procedure symbol for local size
            proc_symbol = self.symbol_table.lookup(proc_name)
            size_locals = proc_symbol.local_size  # Should include space for temps
            
            # Set the current procedure context for the formatter
            self.formatter.set_current_procedure(proc_name)
            
            return [
                f"{proc_name}:",
                f" push bp",
                f" mov bp, sp",
                f" sub sp, {size_locals}"
            ]
        except Exception as e:
            logger.error(f"Error translating procedure {proc_name}: {e}")
            # Return a basic procedure header without local allocation
            return [
                f"{proc_name}:",
                f" push bp",
                f" mov bp, sp",
                f"; ERROR: Could not determine local size"
            ]
    
    def _translate_endp(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a procedure end.
        
        Args:
            instr: Procedure end instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        proc_name = instr.op1
        
        try:
            # Lookup the procedure symbol for parameter size
            proc_symbol = self.symbol_table.lookup(proc_name)
            size_params = proc_symbol.param_size
            
            # Clear the current procedure context
            self.formatter.set_current_procedure(None)
            
            return [
                f" mov sp, bp",
                f" pop bp",
                f" ret {size_params}"
            ]
        except Exception as e:
            logger.error(f"Error translating procedure end {proc_name}: {e}")
            # Return a basic procedure end without parameter cleanup
            return [
                f" mov sp, bp",
                f" pop bp",
                f" ret"
            ]
    
    def _translate_call(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a procedure call.
        
        Args:
            instr: Procedure call instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        proc_name = instr.op1
        return [f" call {proc_name}"]
    
    def _translate_push(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a push instruction.
        
        Args:
            instr: Push instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        operand = instr.op1
        
        # Check if this is a pass-by-reference parameter (starts with @)
        if operand.startswith('@'):
            # Extract the base operand (remove the @)
            target = operand[1:]
            target_asm = self.formatter.format_operand(target)
            
            # Handle different cases based on the formatted operand
            if target_asm.startswith('[bp-'):
                # Local variable or temporary - push its address
                return [f" lea ax, {target_asm}", f" push ax"]
            elif target_asm.startswith('[bp+'):
                # Parameter by reference - already an address, just push it
                return [f" push word {target_asm}"]
            else:
                # Global variable - push its offset
                return [f" push offset {target_asm}"]
        else:
            # Pass by value - push the value itself
            val_asm = self.formatter.format_operand(operand)
            
            if val_asm.startswith('[bp+'):
                # Parameter by reference - dereference and push
                return [
                    f" mov bx, {val_asm}",
                    f" mov ax, [bx]",
                    f" push ax"
                ]
            elif re.match(r'^-?\d+$', val_asm):
                # Immediate value - push directly
                return [f" push {val_asm}"]
            else:
                # Variable or memory location - load to AX then push
                return [f" mov ax, {val_asm}", f" push ax"]
    
    def _translate_wrs(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a write string instruction.
        
        Args:
            instr: Write string instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        label = self.formatter.format_operand(instr.op1)
        return [
            f" mov dx, offset {label}",
            f" call writestr"
        ]
    
    def _translate_wri(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a write integer instruction.
        
        Args:
            instr: Write integer instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        src_asm = self.formatter.format_operand(instr.op1)
        
        if src_asm.startswith('[bp+'):
            # Source is a parameter by reference (address)
            return [
                f" mov bx, {src_asm}",
                f" mov ax, [bx]",
                f" call writeint"
            ]
        else:
            # Source is a direct value or memory location
            return [
                f" mov ax, {src_asm}",
                f" call writeint"
            ]
    
    def _translate_rdi(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a read integer instruction.
        
        Args:
            instr: Read integer instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        dest_asm = self.formatter.format_operand(instr.op1)
        
        if dest_asm.startswith('[bp+'):
            # Destination is a parameter by reference (address)
            return [
                f" call readint",
                f" mov ax, bx",  # Result in BX, move to AX as intermediate
                f" mov bx, {dest_asm}",
                f" mov [bx], ax"
            ]
        else:
            # Destination is a direct memory location
            return [
                f" call readint",
                f" mov {dest_asm}, bx"  # Result in BX
            ]
    
    def _translate_wrln(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a writeln instruction.
        
        Args:
            instr: Writeln instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            List of ASM instructions
        """
        return [f" call writeln"]
    
    def _translate_start_proc(self, instr: TACInstruction, current_proc_symbol) -> List[str]:
        """
        Translate a START PROC instruction (handled by main generator).
        
        Args:
            instr: START PROC instruction
            current_proc_symbol: Current procedure symbol or None
            
        Returns:
            Empty list (handled by main generator)
        """
        return []
    
    def _get_asm_opcode(self, tac_opcode: str) -> str:
        """
        Convert a TAC opcode to its ASM equivalent.
        
        Args:
            tac_opcode: TAC operation code
            
        Returns:
            Corresponding ASM opcode
        """
        opcode_map = {
            '+': 'add',
            '-': 'sub',
            '*': 'imul',  # Handled specially in translate_binary_op
            '/': 'idiv',  # Handled specially in translate_binary_op
            'mod': 'idiv',  # Handled specially in translate_binary_op
            'and': 'and',
            'or': 'or'
        }
        
        return opcode_map.get(tac_opcode, f"UNKNOWN_{tac_opcode}") 