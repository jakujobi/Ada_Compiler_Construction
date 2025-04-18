#!/usr/bin/env python3
# ThreeAddressCodeGenerator.py
# Author: John Akujobi (implemented with help)
# GitHub: [https://github.com/jakujobi/Ada_Compiler_Construction](https://github.com/jakujobi/Ada_Compiler_Construction)
# Date: 2025-04-18
# Version: 1.0
"""
Three Address Code Generator for the Ada Compiler Construction Project

This module is responsible for generating Three Address Code (TAC) from a
parsed and semantically analyzed Ada program. It handles variable references,
arithmetic expressions, and procedure calls according to the specifications.

Key features:
- Variables at depth 1 referenced by name
- Variables at depth > 1 referenced by offset (_BP-offset)
- Parameters referenced with positive offsets (_BP+offset)
- Constants substituted directly
- Pascal-style procedure calls (parameters pushed left to right)
"""

import os
import sys
from typing import List, Dict, Optional, Any, Tuple, Union, Set
from pathlib import Path

# Add the parent directory to the path so we can import modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.RDParser import ParseTreeNode
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter, TableEntry
from Modules.Logger import Logger


class TACInstruction:
    """
    Represents a single Three Address Code instruction.
    
    A TAC instruction has an operation and up to three operands:
    - op: The operation (e.g., =, +, -, *, /, LABEL, GOTO, IF, etc.)
    - arg1: The first operand
    - arg2: The second operand (optional)
    - result: The result operand (optional)
    """
    
    def __init__(self, op: str, arg1: Optional[str] = None, 
                 arg2: Optional[str] = None, result: Optional[str] = None):
        """
        Initialize a TAC instruction.
        
        Args:
            op: The operation code
            arg1: The first operand (optional)
            arg2: The second operand (optional)
            result: The result operand (optional)
        """
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
    
    def to_string(self) -> str:
        """
        Convert the instruction to a string representation.
        
        Returns:
            String representation of the instruction
        """
        if self.op == "LABEL":
            return f"LABEL {self.arg1}"
        elif self.op == "GOTO":
            return f"goto {self.arg1}"
        elif self.op == "IF":
            return f"if {self.arg1} goto {self.result}"
        elif self.op == "RETURN":
            return "return"
        elif self.op == "PUSH":
            return f"push {self.arg1}"
        elif self.op == "PUSHA":  # Push address (for reference parameters)
            return f"push @{self.arg1}"
        elif self.op == "CALL":
            return f"call {self.arg1}"
        elif self.op == "START":
            return f"START {self.arg1}"
        elif self.op == "=":
            return f"{self.result} := {self.arg1}"
        elif self.op in ["+", "-", "*", "/", "AND", "OR", "MOD", "REM"]:
            return f"{self.result} := {self.arg1} {self.op} {self.arg2}"
        else:
            # Generic format for other operations
            parts = [self.op]
            if self.arg1 is not None:
                parts.append(str(self.arg1))
            if self.arg2 is not None:
                parts.append(str(self.arg2))
            if self.result is not None:
                parts.append(str(self.result))
            return ", ".join(parts)
    
    def __str__(self) -> str:
        """
        String representation of the instruction.
        
        Returns:
            String representation of the instruction
        """
        return self.to_string()
    
    def is_jump(self) -> bool:
        """
        Check if this instruction is a jump instruction.
        
        Returns:
            True if the instruction is a jump, False otherwise
        """
        return self.op in ["GOTO", "IF"]
    
    def is_label(self) -> bool:
        """
        Check if this instruction is a label.
        
        Returns:
            True if the instruction is a label, False otherwise
        """
        return self.op == "LABEL"


class TACProgram:
    """
    Represents a Three Address Code program.
    
    A TAC program is a collection of TAC instructions with methods for
    adding instructions, generating temporary variables, and writing the
    program to a file.
    """
    
    def __init__(self, program_name: str):
        """
        Initialize a TAC program.
        
        Args:
            program_name: The name of the program
        """
        self.program_name = program_name
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
    
    def add_instruction(self, op: str, arg1: Optional[str] = None, 
                        arg2: Optional[str] = None, result: Optional[str] = None) -> TACInstruction:
        """
        Add an instruction to the program.
        
        Args:
            op: The operation code
            arg1: The first operand (optional)
            arg2: The second operand (optional)
            result: The result operand (optional)
            
        Returns:
            The added instruction
        """
        instruction = TACInstruction(op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction
    
    def add_raw_instruction(self, instruction: TACInstruction) -> None:
        """
        Add a pre-created instruction to the program.
        
        Args:
            instruction: The instruction to add
        """
        self.instructions.append(instruction)
    
    def generate_temp(self) -> str:
        """
        Generate a temporary variable name.
        
        Returns:
            A unique temporary variable name
        """
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def generate_label(self) -> str:
        """
        Generate a unique label.
        
        Returns:
            A unique label name
        """
        label_name = f"L{self.label_counter}"
        self.label_counter += 1
        return label_name
    
    def get_instructions(self) -> List[TACInstruction]:
        """
        Get all instructions in the program.
        
        Returns:
            List of instructions
        """
        return self.instructions
    
    def add_start_instruction(self) -> None:
        """
        Add the START instruction to the end of the program.
        """
        self.add_instruction("START", self.program_name)
    
    def write_to_file(self, output_file: str) -> bool:
        """
        Write the TAC program to a file.
        
        Args:
            output_file: The path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_file, "w") as f:
                for instruction in self.instructions:
                    f.write(f"{instruction}\n")
            return True
        except Exception as e:
            print(f"Error writing TAC program to file: {e}")
            return False

