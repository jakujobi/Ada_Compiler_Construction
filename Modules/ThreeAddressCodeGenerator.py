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


class ThreeAddressCodeGenerator:
    """
    Generates Three Address Code from a parsed and semantically analyzed Ada program.
    
    This class traverses the parse tree and generates TAC instructions for each node,
    keeping track of variable references, procedure calls, and expressions.
    """
    
    def __init__(self, parse_tree: ParseTreeNode, symbol_table: AdaSymbolTable, 
                 logger: Optional[Logger] = None):
        """
        Initialize the TAC generator.
        
        Args:
            parse_tree: The root of the parse tree
            symbol_table: The symbol table
            logger: Optional logger for logging messages
        """
        self.parse_tree = parse_tree
        self.symbol_table = symbol_table
        self.logger = logger if logger else Logger()
        
        self.current_depth = 0
        self.current_procedure = None
        self.tac_program = None
        
        # Variable size mapping
        self.type_sizes = {
            VarType.INT: 2,    # Integers have size 2
            VarType.CHAR: 1,   # Characters have size 1
            VarType.FLOAT: 4,  # Floats have size 4
            VarType.REAL: 4    # Alias for FLOAT
        }
        
        self.logger.info("Three Address Code Generator initialized")
    
    def generate(self) -> TACProgram:
        """
        Generate TAC for the entire program.
        
        Returns:
            The generated TAC program
        """
        self.logger.info("Starting TAC generation")
        
        # Determine the program name from the parse tree
        program_name = self._determine_program_name()
        self.tac_program = TACProgram(program_name)
        
        # Process the root node of the parse tree
        if self.parse_tree.name == "ProgramList":
            # Handle multiple top-level procedures
            for child in self.parse_tree.children:
                self._process_node(child)
        else:
            # Handle a single procedure
            self._process_node(self.parse_tree)
        
        # Add the START instruction at the end
        self.tac_program.add_start_instruction()
        
        self.logger.info("TAC generation completed")
        return self.tac_program
    
    def _determine_program_name(self) -> str:
        """
        Determine the name of the program from the parse tree.
        
        Returns:
            The name of the outermost procedure
        """
        if self.parse_tree.name == "ProgramList" and self.parse_tree.children:
            # Get the first procedure in the list
            prog_node = self.parse_tree.children[0]
            if prog_node.name == "Prog" and len(prog_node.children) > 1:
                # The second child of Prog is the identifier
                id_node = prog_node.children[1]
                if id_node.token:
                    return id_node.token.lexeme
        
        # Default name if we couldn't determine it
        return "Program"
    
    def _process_node(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process a node in the parse tree and generate TAC instructions.
        
        Args:
            node: The node to process
            
        Returns:
            List of generated TAC instructions
        """
        self.logger.debug(f"Processing node: {node.name}")
        
        instructions = []
        
        if node.name == "Prog":
            # Process a procedure definition
            instructions.extend(self._process_procedure(node))
        elif node.name == "SeqOfStatements":
            # Process a sequence of statements
            instructions.extend(self._process_seq_of_statements(node))
        elif node.name == "Statement":
            # Process a statement
            instructions.extend(self._process_statement(node))
        elif node.name == "AssignStat":
            # Process an assignment statement
            instructions.extend(self._process_assign_stat(node))
        elif node.name == "ProcCall":
            # Process a procedure call
            instructions.extend(self._process_proc_call(node))
        elif node.name == "Expr":
            # Process an expression
            instructions.extend(self._process_expression(node))
        # Add more node types as needed
        
        return instructions
    
    def _process_procedure(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process a procedure definition and generate TAC instructions.
        
        Args:
            node: The procedure node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Extract the procedure name
        if len(node.children) < 2 or node.children[1].name != "ID":
            self.logger.error("Invalid procedure node: missing identifier")
            return instructions
        
        proc_name = node.children[1].token.lexeme
        self.current_procedure = proc_name
        
        # Add a label for the procedure
        self.tac_program.add_instruction("LABEL", proc_name)
        
        # Find the body of the procedure (sequence of statements)
        for i, child in enumerate(node.children):
            if child.name == "BEGIN":
                # The next child after BEGIN should be SeqOfStatements
                if i + 1 < len(node.children) and node.children[i + 1].name == "SeqOfStatements":
                    # Process the statements
                    instructions.extend(self._process_seq_of_statements(node.children[i + 1]))
                break
        
        # Add a return instruction at the end of the procedure
        self.tac_program.add_instruction("RETURN")
        
        return instructions
    
    def _process_seq_of_statements(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process a sequence of statements and generate TAC instructions.
        
        Args:
            node: The sequence of statements node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Find all Statement nodes and process them
        for child in node.children:
            if child.name == "Statement":
                instructions.extend(self._process_statement(child))
            elif child.name == "SeqOfStatements":
                # Recursive case for nested statement sequences
                instructions.extend(self._process_seq_of_statements(child))
        
        return instructions
    
    def _process_statement(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process a statement and generate TAC instructions.
        
        Args:
            node: The statement node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Find the type of statement
        for child in node.children:
            if child.name == "AssignStat":
                instructions.extend(self._process_assign_stat(child))
            elif child.name == "ProcCall":
                instructions.extend(self._process_proc_call(child))
            # Add more statement types as needed
        
        return instructions
    
    def _process_assign_stat(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process an assignment statement and generate TAC instructions.
        
        Args:
            node: The assignment statement node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Get the identifier and expression
        id_node = None
        expr_node = None
        
        for i, child in enumerate(node.children):
            if child.name == "ID":
                id_node = child
            elif child.name == "Expr":
                expr_node = child
        
        if id_node and expr_node:
            # Resolve the variable reference
            var_ref = self._resolve_variable(id_node.token.lexeme)
            
            # Process the expression
            expr_instructions, expr_result = self._process_expression_with_result(expr_node)
            instructions.extend(expr_instructions)
            
            # Add the assignment instruction
            self.tac_program.add_instruction("=", expr_result, None, var_ref)
        
        return instructions
    
    def _process_proc_call(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process a procedure call and generate TAC instructions.
        
        Args:
            node: The procedure call node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Get the procedure name and parameters
        proc_name = None
        params_node = None
        
        for i, child in enumerate(node.children):
            if child.name == "ID":
                proc_name = child.token.lexeme
            elif child.name == "Params":
                params_node = child
        
        if proc_name:
            # Process parameters if they exist
            if params_node:
                param_instructions = self._process_params(params_node)
                instructions.extend(param_instructions)
            
            # Add the call instruction
            self.tac_program.add_instruction("CALL", proc_name)
        
        return instructions
    
    def _process_params(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process procedure parameters and generate TAC instructions.
        
        Args:
            node: The parameters node
            
        Returns:
            List of generated TAC instructions
        """
        instructions = []
        
        # Get all ID and NUM nodes in the parameter list
        param_nodes = []
        self._collect_param_nodes(node, param_nodes)
        
        # Process each parameter
        for param_node in param_nodes:
            if param_node.name == "ID":
                # Check if this is a pass-by-reference parameter
                entry = self.symbol_table.lookup(param_node.token.lexeme)
                if entry and hasattr(entry, 'param_mode') and entry.param_mode in [ParameterMode.INOUT, ParameterMode.OUT]:
                    # Push the address
                    self.tac_program.add_instruction("PUSHA", self._resolve_variable(param_node.token.lexeme))
                else:
                    # Push the value
                    self.tac_program.add_instruction("PUSH", self._resolve_variable(param_node.token.lexeme))
            elif param_node.name == "NUM":
                # Constants are pushed directly
                self.tac_program.add_instruction("PUSH", param_node.token.lexeme)
        
        return instructions
    
    def _collect_param_nodes(self, node: ParseTreeNode, result: List[ParseTreeNode]) -> None:
        """
        Collect all parameter nodes from a Params or ParamsTail node.
        
        Args:
            node: The params or params tail node
            result: List to store parameter nodes
        """
        if not node or not node.children:
            return
        
        for child in node.children:
            if child.name in ["ID", "NUM"]:
                result.append(child)
            elif child.name in ["Params", "ParamsTail"]:
                self._collect_param_nodes(child, result)
    
    def _process_expression(self, node: ParseTreeNode) -> List[TACInstruction]:
        """
        Process an expression and generate TAC instructions.
        
        Args:
            node: The expression node
            
        Returns:
            List of generated TAC instructions
        """
        instructions, _ = self._process_expression_with_result(node)
        return instructions
    
    def _process_expression_with_result(self, node: ParseTreeNode) -> Tuple[List[TACInstruction], str]:
        """
        Process an expression and generate TAC instructions with a result variable.
        
        Args:
            node: The expression node
            
        Returns:
            Tuple of (list of generated TAC instructions, result variable)
        """
        instructions = []
        
        # Process based on the expression type
        if node.name == "Expr":
            # Find the relation node
            relation_node = self._find_child_by_name(node, "Relation")
            if relation_node:
                return self._process_expression_with_result(relation_node)
        elif node.name == "Relation":
            # Find the simple expression node
            simple_expr_node = self._find_child_by_name(node, "SimpleExpr")
            if simple_expr_node:
                return self._process_expression_with_result(simple_expr_node)
        elif node.name == "SimpleExpr":
            # Process term and more terms
            term_node = self._find_child_by_name(node, "Term")
            more_term_node = self._find_child_by_name(node, "MoreTerm")
            
            if term_node:
                term_instructions, term_result = self._process_expression_with_result(term_node)
                instructions.extend(term_instructions)
                
                if more_term_node and more_term_node.children and more_term_node.children[0].name != "ε":
                    # Process more terms with the term result
                    more_instructions, final_result = self._process_more_term(more_term_node, term_result)
                    instructions.extend(more_instructions)
                    return instructions, final_result
                
                return instructions, term_result
        elif node.name == "Term":
            # Process factor and more factors
            factor_node = self._find_child_by_name(node, "Factor")
            more_factor_node = self._find_child_by_name(node, "MoreFactor")
            
            if factor_node:
                factor_instructions, factor_result = self._process_expression_with_result(factor_node)
                instructions.extend(factor_instructions)
                
                if more_factor_node and more_factor_node.children and more_factor_node.children[0].name != "ε":
                    # Process more factors with the factor result
                    more_instructions, final_result = self._process_more_factor(more_factor_node, factor_result)
                    instructions.extend(more_instructions)
                    return instructions, final_result
                
                return instructions, factor_result
        elif node.name == "Factor":
            # Process based on the factor type
            if node.children:
                child = node.children[0]
                
                if child.name == "ID":
                    # Variable reference
                    var_ref = self._resolve_variable(child.token.lexeme)
                    return instructions, var_ref
                elif child.name == "NUM":
                    # Numeric constant
                    return instructions, child.token.lexeme
                elif child.token and child.token.token_type.name == "LPAREN":
                    # Parenthesized expression
                    for i, c in enumerate(node.children):
                        if c.name == "Expr":
                            expr_instructions, expr_result = self._process_expression_with_result(c)
                            instructions.extend(expr_instructions)
                            return instructions, expr_result
                elif child.token and child.token.token_type.name in ["PLUS", "MINUS"]:
                    # Unary operation
                    if len(node.children) > 1:
                        factor_instructions, factor_result = self._process_expression_with_result(node.children[1])
                        instructions.extend(factor_instructions)
                        
                        # Create a new temporary for the unary operation
                        temp = self.tac_program.generate_temp()
                        op = "+" if child.token.token_type.name == "PLUS" else "-"
                        
                        # Special case for unary minus
                        if op == "-":
                            self.tac_program.add_instruction(op, "0", factor_result, temp)
                        else:
                            # Unary plus is a no-op, just assign
                            self.tac_program.add_instruction("=", factor_result, None, temp)
                        
                        return instructions, temp
        
        # Default case: create a temporary variable
        temp = self.tac_program.generate_temp()
        self.tac_program.add_instruction("=", "0", None, temp)  # Default to 0
        return instructions, temp
    
    def _process_more_term(self, node: ParseTreeNode, left_operand: str) -> Tuple[List[TACInstruction], str]:
        """
        Process a MoreTerm node and generate TAC instructions.
        
        Args:
            node: The MoreTerm node
            left_operand: The left operand from the previous term
            
        Returns:
            Tuple of (list of generated TAC instructions, result variable)
        """
        instructions = []
        
        # Check if this is an empty MoreTerm (ε)
        if not node.children or node.children[0].name == "ε":
            return instructions, left_operand
        
        # Get the operator
        op_node = node.children[0]
        op = op_node.token.token_type.name
        if op == "PLUS":
            op = "+"
        elif op == "MINUS":
            op = "-"
        # Add more operators as needed
        
        # Get the right operand (Term)
        term_node = self._find_child_by_name(node, "Term")
        if term_node:
            term_instructions, term_result = self._process_expression_with_result(term_node)
            instructions.extend(term_instructions)
            
            # Create a temporary for the result
            temp = self.tac_program.generate_temp()
            self.tac_program.add_instruction(op, left_operand, term_result, temp)
            
            # Process the rest of the MoreTerm
            more_term_node = self._find_child_by_name(node, "MoreTerm")
            if more_term_node and more_term_node.children and more_term_node.children[0].name != "ε":
                more_instructions, final_result = self._process_more_term(more_term_node, temp)
                instructions.extend(more_instructions)
                return instructions, final_result
            
            return instructions, temp
        
        return instructions, left_operand
    
    def _process_more_factor(self, node: ParseTreeNode, left_operand: str) -> Tuple[List[TACInstruction], str]:
        """
        Process a MoreFactor node and generate TAC instructions.
        
        Args:
            node: The MoreFactor node
            left_operand: The left operand from the previous factor
            
        Returns:
            Tuple of (list of generated TAC instructions, result variable)
        """
        instructions = []
        
        # Check if this is an empty MoreFactor (ε)
        if not node.children or node.children[0].name == "ε":
            return instructions, left_operand
        
        # Get the operator
        op_node = node.children[0]
        op = op_node.token.token_type.name
        if op == "MULT":
            op = "*"
        elif op == "DIV":
            op = "/"
        # Add more operators as needed
        
        # Get the right operand (Factor)
        factor_node = self._find_child_by_name(node, "Factor")
        if factor_node:
            factor_instructions, factor_result = self._process_expression_with_result(factor_node)
            instructions.extend(factor_instructions)
            
            # Create a temporary for the result
            temp = self.tac_program.generate_temp()
            self.tac_program.add_instruction(op, left_operand, factor_result, temp)
            
            # Process the rest of the MoreFactor
            more_factor_node = self._find_child_by_name(node, "MoreFactor")
            if more_factor_node and more_factor_node.children and more_factor_node.children[0].name != "ε":
                more_instructions, final_result = self._process_more_factor(more_factor_node, temp)
                instructions.extend(more_instructions)
                return instructions, final_result
            
            return instructions, temp
        
        return instructions, left_operand
    
    def _resolve_variable(self, variable_name: str, current_depth: int = None) -> str:
        """
        Resolve a variable reference based on its declaration depth.
        
        Args:
            variable_name: The name of the variable
            current_depth: The current lexical depth (or None for the current depth)
            
        Returns:
            The resolved variable reference
        """
        if current_depth is None:
            current_depth = self.current_depth
        
        # Look up the variable in the symbol table
        entry = self.symbol_table.lookup(variable_name)
        if not entry:
            self.logger.error(f"Undeclared variable: {variable_name}")
            return variable_name  # Default to the name itself
        
        # Check if this is a constant
        if entry.entry_type == EntryType.CONSTANT:
            # Return the constant value directly
            return str(entry.const_value)
        
        # Variables at depth 1 use their actual name
        if entry.depth == 1:
            return variable_name
        
        # Parameters use positive offsets
        if entry.entry_type == EntryType.VARIABLE and hasattr(entry, 'param_mode'):
            # Calculate parameter offset
            offset = self._calculate_parameter_offset(entry)
            return f"_BP+{offset}"
        
        # Local variables use negative offsets
        offset = self._calculate_local_offset(entry)
        return f"_BP-{offset}"
    
    def _calculate_local_offset(self, entry: TableEntry) -> int:
        """
        Calculate the offset for a local variable.
        
        Args:
            entry: The symbol table entry
            
        Returns:
            The calculated offset
        """
        if hasattr(entry, 'offset') and entry.offset is not None:
            return entry.offset
        
        # Default to 0 if offset is not available
        return 0
    
    def _calculate_parameter_offset(self, entry: TableEntry) -> int:
        """
        Calculate the offset for a parameter.
        
        Args:
            entry: The symbol table entry
            
        Returns:
            The calculated offset
        """
        if hasattr(entry, 'offset') and entry.offset is not None:
            # Parameters are pushed from left to right (Pascal style)
            # so their offsets are positive and start from higher values
            return entry.offset
        
        # Default to 4 if offset is not available
        return 4
    
    def _find_child_by_name(self, node: ParseTreeNode, name: str) -> Optional[ParseTreeNode]:
        """
        Find a child node by name.
        
        Args:
            node: The parent node
            name: The name of the child to find
            
        Returns:
            The child node if found, None otherwise
        """
        if not node or not node.children:
            return None
        
        for child in node.children:
            if child.name == name:
                return child
        
        return None


# Test code for the module
if __name__ == "__main__":
    print("ThreeAddressCodeGenerator module - Use with JohnA7.py driver program")