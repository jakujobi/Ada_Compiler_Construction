#!/usr/bin/env python3
# ThreeAddressCodeGenerator.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-04-18
# Version: 1.0
"""
Three Address Code Generator for Ada Compiler

This module translates the parsed and semantically analyzed Ada source code into
Three Address Code (TAC) instructions. It handles variable references based on declaration
depth, manages procedure calls with parameter passing, and generates properly formatted
TAC output files.

The generator follows these rules:
- Variables at depth 1: use actual names
- Variables at depth > 1: use offset notation (_BP-offset)
- Parameters: use positive offsets (_BP+offset)
- Constants: substitute literal values directly

Key components:
- TACInstruction: Represents a TAC instruction
- TACProgram: Stores TAC instructions and manages code generation
- ThreeAddressCodeGenerator: Main generator that walks the parse tree and produces code
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
import os
from pathlib import Path

from .AdaSymbolTable import AdaSymbolTable, TableEntry, VarType, EntryType, ParameterMode
from .Logger import Logger


class TACInstruction:
    """
    Represents a Three Address Code instruction.
    
    Each instruction has an operation and up to three operands.
    Special instructions like labels and jumps are also supported.
    
    Attributes:
        op (str): The operation code
        arg1 (Optional[str]): First operand
        arg2 (Optional[str]): Second operand
        result (Optional[str]): Destination operand
    """
    def __init__(self, op: str, arg1: Optional[str] = None, arg2: Optional[str] = None, result: Optional[str] = None):
        """
        Initialize a TAC instruction.
        
        Args:
            op: The operation code
            arg1: First operand (optional)
            arg2: Second operand (optional)
            result: Destination operand (optional)
        """
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
    
    def to_string(self) -> str:
        """
        Convert the instruction to a string representation.
        
        Returns:
            String representation of the TAC instruction
        """
        if self.is_label():
            return f"LABEL {self.op.replace('LABEL ', '')}"
        
        if self.op == "START":
            return f"START {self.arg1}"
        
        if self.op == "push":
            return f"push {self.arg1}"
        
        if self.op == "call":
            return f"call {self.arg1}"
            
        if self.op == "return":
            return "return"
            
        if self.op == ":=" and self.arg2 is None:
            # Simple assignment
            return f"{self.result} := {self.arg1}"
        
        # Regular operation
        if self.result is not None and self.arg1 is not None:
            if self.arg2 is not None:
                # Binary operation
                return f"{self.result} := {self.arg1} {self.op} {self.arg2}"
            else:
                # Unary operation
                return f"{self.result} := {self.op} {self.arg1}"
        
        return f"{self.op} {self.arg1 or ''} {self.arg2 or ''} {self.result or ''}".strip()
    
    def is_jump(self) -> bool:
        """
        Check if this instruction is a jump.
        
        Returns:
            True if this is a jump instruction, False otherwise
        """
        return self.op in ["goto", "iffalse", "iftrue"]
    
    def is_label(self) -> bool:
        """
        Check if this instruction is a label.
        
        Returns:
            True if this is a label instruction, False otherwise
        """
        return self.op.startswith("LABEL")


class TACProgram:
    """
    Represents a complete Three Address Code program.
    
    Manages a list of TACInstructions and provides methods to add
    instructions and generate temporary variable names.
    
    Attributes:
        program_name (str): The name of the program
        instructions (List[TACInstruction]): The list of TAC instructions
        temp_counter (int): Counter for generating temporary variables
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
    
    def add_instruction(self, op: str, arg1: Optional[str] = None, 
                       arg2: Optional[str] = None, result: Optional[str] = None) -> TACInstruction:
        """
        Add a new instruction to the program.
        
        Args:
            op: The operation code
            arg1: First operand (optional)
            arg2: Second operand (optional)
            result: Destination operand (optional)
            
        Returns:
            The created TACInstruction
        """
        instruction = TACInstruction(op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction
    
    def add_raw_instruction(self, instruction: TACInstruction) -> None:
        """
        Add an existing instruction to the program.
        
        Args:
            instruction: The TACInstruction to add
        """
        self.instructions.append(instruction)
    
    def generate_temp(self) -> str:
        """
        Generate a unique temporary variable name.
        
        Returns:
            A new temporary variable name (t1, t2, etc.)
        """
        self.temp_counter += 1
        return f"t{self.temp_counter}"
    
    def add_start_instruction(self) -> None:
        """
        Add the START instruction to the end of the program.
        """
        self.add_instruction("START", self.program_name)
    
    def write_to_file(self, filename: str) -> bool:
        """
        Write the TAC program to a file.
        
        Args:
            filename: The name of the file to write to
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            with open(filename, 'w') as file:
                for instruction in self.instructions:
                    file.write(instruction.to_string() + '\n')
            return True
        except Exception as e:
            print(f"Error writing TAC to file: {e}")
            return False
    
    def get_instructions(self) -> List[TACInstruction]:
        """
        Get the list of instructions.
        
        Returns:
            The list of TACInstructions
        """
        return self.instructions


class ThreeAddressCodeGenerator:
    """
    Generates Three Address Code from a parse tree and symbol table.
    
    This is the main class that traverses the parse tree and generates
    TAC instructions according to the specified rules.
    
    Attributes:
        parse_tree: The parse tree
        symbol_table (AdaSymbolTable): The symbol table
        logger (Logger): The logger
        tac_program (TACProgram): The generated TAC program
        current_depth (int): The current depth in the parse tree
    """
    def __init__(self, parse_tree: Any, symbol_table: AdaSymbolTable, logger: Logger):
        """
        Initialize the generator.
        
        Args:
            parse_tree: The parse tree
            symbol_table: The symbol table
            logger: The logger
        """
        self.parse_tree = parse_tree
        self.symbol_table = symbol_table
        self.logger = logger
        self.current_depth = 0
        
        # Extract the program name from the parse tree
        if hasattr(parse_tree, 'name') and parse_tree.name:
            self.program_name = parse_tree.name
        else:
            self.program_name = "Program"
        
        self.tac_program = TACProgram(self.program_name)
        
    def generate(self) -> TACProgram:
        """
        Generate TAC for the entire program.
        
        Returns:
            The generated TACProgram
        """
        try:
            # Process the root node to start the traversal
            self.process_node(self.parse_tree)
            
            # Add the START instruction at the end
            self.tac_program.add_start_instruction()
            
            return self.tac_program
        except Exception as e:
            self.logger.error(f"Error generating TAC: {e}")
            # Return empty program on error
            return TACProgram(self.program_name)
    
    def process_node(self, node: Any) -> None:
        """
        Process a node in the parse tree and generate TAC instructions.
        
        This method dispatches to more specific methods based on the node type.
        
        Args:
            node: The node to process
        """
        if node is None:
            return
        
        # Handle different types of nodes based on node type or class name
        node_type = node.__class__.__name__ if hasattr(node, '__class__') else type(node).__name__
        
        # Check for specific node types and dispatch accordingly
        if node_type == 'Program':
            self._process_program(node)
        elif node_type == 'Procedure':
            self._process_procedure(node)
        elif node_type == 'Block':
            self._process_block(node)
        elif node_type == 'AssignmentStatement':
            self._process_assignment(node)
        elif node_type == 'IfStatement':
            self._process_if_statement(node)
        elif node_type == 'WhileStatement':
            self._process_while_statement(node)
        elif node_type == 'ProcedureCall':
            self._process_procedure_call(node)
        elif node_type == 'BinaryExpression':
            return self._process_binary_expression(node)
        elif node_type == 'UnaryExpression':
            return self._process_unary_expression(node)
        elif node_type == 'VariableReference':
            return self._resolve_variable(node.name)
        elif node_type == 'NumericLiteral':
            return str(node.value)
        # Add more node types as needed
        
        # If there's a list of statements or other child nodes, process them
        if hasattr(node, 'statements') and node.statements:
            for statement in node.statements:
                self.process_node(statement)
        
        # Process child nodes (will need to be adapted based on actual AST structure)
        if hasattr(node, 'children'):
            for child in node.children:
                self.process_node(child)
    
    def _process_program(self, node: Any) -> None:
        """
        Process a program node.
        
        Args:
            node: The program node
        """
        self.logger.info(f"Processing program: {node.name}")
        
        # Add procedure label
        self.tac_program.add_instruction(f"LABEL {node.name}")
        
        # Process the body of the program
        if hasattr(node, 'body'):
            self.process_node(node.body)
    
    def _process_procedure(self, node: Any) -> None:
        """
        Process a procedure node.
        
        Args:
            node: The procedure node
        """
        self.logger.info(f"Processing procedure: {node.name}")
        
        # Increase depth when entering a procedure
        self.current_depth += 1
        
        # Add procedure label
        self.tac_program.add_instruction(f"LABEL {node.name}")
        
        # Process the body of the procedure
        if hasattr(node, 'body'):
            self.process_node(node.body)
        
        # Add return instruction at the end
        self.tac_program.add_instruction("return")
        
        # Decrease depth when exiting the procedure
        self.current_depth -= 1
    
    def _process_block(self, node: Any) -> None:
        """
        Process a block node.
        
        Args:
            node: The block node
        """
        # Process each statement in the block
        if hasattr(node, 'statements'):
            for statement in node.statements:
                self.process_node(statement)
    
    def _process_assignment(self, node: Any) -> None:
        """
        Process an assignment statement.
        
        Args:
            node: The assignment statement node
        """
        # Evaluate the right-hand side expression
        expr_result = self.process_node(node.expression)
        
        # Resolve the left-hand side variable
        target = self._resolve_variable(node.target.name)
        
        # Add assignment instruction
        self.tac_program.add_instruction(":=", expr_result, None, target)
    
    def _process_binary_expression(self, node: Any) -> str:
        """
        Process a binary expression and return the result variable.
        
        Args:
            node: The binary expression node
            
        Returns:
            The variable containing the result of the expression
        """
        # Get left and right operands
        left_operand = self.process_node(node.left)
        right_operand = self.process_node(node.right)
        
        # Create a temporary variable for the result
        result = self.tac_program.generate_temp()
        
        # Add the instruction
        self.tac_program.add_instruction(node.operator, left_operand, right_operand, result)
        
        return result
    
    def _process_unary_expression(self, node: Any) -> str:
        """
        Process a unary expression and return the result variable.
        
        Args:
            node: The unary expression node
            
        Returns:
            The variable containing the result of the expression
        """
        # Get the operand
        operand = self.process_node(node.operand)
        
        # Create a temporary variable for the result
        result = self.tac_program.generate_temp()
        
        # Add the instruction
        self.tac_program.add_instruction(node.operator, operand, None, result)
        
        return result
    
    def _process_if_statement(self, node: Any) -> None:
        """
        Process an if statement.
        
        Args:
            node: The if statement node
        """
        # Evaluate the condition
        condition_result = self.process_node(node.condition)
        
        # Generate labels
        else_label = f"L{self.tac_program.temp_counter + 1}"
        end_label = f"L{self.tac_program.temp_counter + 2}"
        
        # Jump to else part if condition is false
        self.tac_program.add_instruction("iffalse", condition_result, else_label)
        
        # Process the then part
        self.process_node(node.then_part)
        
        # Jump to end of if statement
        self.tac_program.add_instruction("goto", end_label)
        
        # Add the else label
        self.tac_program.add_instruction(f"LABEL {else_label}")
        
        # Process the else part if it exists
        if hasattr(node, 'else_part') and node.else_part:
            self.process_node(node.else_part)
        
        # Add the end label
        self.tac_program.add_instruction(f"LABEL {end_label}")
    
    def _process_while_statement(self, node: Any) -> None:
        """
        Process a while statement.
        
        Args:
            node: The while statement node
        """
        # Generate labels
        start_label = f"L{self.tac_program.temp_counter + 1}"
        end_label = f"L{self.tac_program.temp_counter + 2}"
        
        # Add the start label
        self.tac_program.add_instruction(f"LABEL {start_label}")
        
        # Evaluate the condition
        condition_result = self.process_node(node.condition)
        
        # Jump to end if condition is false
        self.tac_program.add_instruction("iffalse", condition_result, end_label)
        
        # Process the body
        self.process_node(node.body)
        
        # Jump back to the start
        self.tac_program.add_instruction("goto", start_label)
        
        # Add the end label
        self.tac_program.add_instruction(f"LABEL {end_label}")
    
    def _process_procedure_call(self, node: Any) -> None:
        """
        Process a procedure call.
        
        Args:
            node: The procedure call node
        """
        # Push parameters in the correct order (left to right for Pascal-style)
        if hasattr(node, 'arguments') and node.arguments:
            for arg in node.arguments:
                # Check if this is a pass-by-reference parameter
                is_reference = self._is_reference_parameter(node.procedure_name, arg.name)
                
                # Resolve the argument
                arg_value = self._resolve_variable(arg.name)
                
                # Add the push instruction with @ prefix for reference parameters
                if is_reference:
                    self.tac_program.add_instruction("push", f"@{arg_value}")
                else:
                    self.tac_program.add_instruction("push", arg_value)
        
        # Add the call instruction
        self.tac_program.add_instruction("call", node.procedure_name)
    
    def _is_reference_parameter(self, proc_name: str, arg_name: str) -> bool:
        """
        Check if a parameter is passed by reference.
        
        Args:
            proc_name: The name of the procedure
            arg_name: The name of the argument
            
        Returns:
            True if the parameter is passed by reference, False otherwise
        """
        # Look up the procedure in the symbol table
        proc_entry = self.symbol_table.lookup(proc_name)
        if not proc_entry or proc_entry.entry_type != EntryType.PROCEDURE:
            return False
        
        # Find the parameter in the parameter list
        if not proc_entry.param_list:
            return False
        
        # This is a simplification; in a real implementation, you would need to match
        # the argument position with the parameter position
        for param in proc_entry.param_list:
            if param.param_mode in [ParameterMode.INOUT, ParameterMode.OUT]:
                return True
        
        return False
    
    def _resolve_variable(self, variable_name: str) -> str:
        """
        Resolve a variable reference based on its depth.
        
        Args:
            variable_name: The name of the variable
            
        Returns:
            The resolved variable reference
        """
        # Look up the variable in the symbol table
        entry = self.symbol_table.lookup(variable_name)
        
        if not entry:
            # If not found, just use the name as is (might be a literal or external reference)
            return variable_name
        
        # Handle constants - substitute the literal value
        if entry.entry_type == EntryType.CONSTANT and entry.const_value is not None:
            return str(entry.const_value)
        
        # Handle variables based on depth
        if entry.depth == 1:
            # Use the actual name for variables at depth 1
            return variable_name
        else:
            # Calculate offset for variables at depths > 1
            offset = self._calculate_offset(entry)
            
            # Positive offset for parameters, negative for local variables
            if self._is_parameter(entry):
                return f"_BP+{offset}"
            else:
                return f"_BP-{offset}"
    
    def _calculate_offset(self, entry: TableEntry) -> int:
        """
        Calculate the memory offset for a variable.
        
        Args:
            entry: The symbol table entry
            
        Returns:
            The calculated offset
        """
        # Use the offset directly if it's already set in the symbol table
        if entry.offset is not None:
            return entry.offset
        
        # Otherwise, calculate it based on variable type
        if entry.var_type == VarType.INT:
            return 2  # Integers are 2 bytes
        elif entry.var_type == VarType.FLOAT or entry.var_type == VarType.REAL:
            return 4  # Floats are 4 bytes
        elif entry.var_type == VarType.CHAR:
            return 1  # Characters are 1 byte
        
        # Default size
        return 2
    
    def _is_parameter(self, entry: TableEntry) -> bool:
        """
        Check if an entry is a parameter.
        
        This is a simplification; in a real implementation, you would have more
        specific information in the symbol table about whether an entry is a parameter.
        
        Args:
            entry: The symbol table entry
            
        Returns:
            True if the entry is a parameter, False otherwise
        """
        # This is a simplified check; in reality, you would have more specific information
        # about whether an entry is a parameter in the symbol table
        return False  # Replace with actual logic