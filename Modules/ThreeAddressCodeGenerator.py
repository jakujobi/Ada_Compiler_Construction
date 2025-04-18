#!/usr/bin/env python3
# ThreeAddressCodeGenerator.py
# Author: John Akujobi
# GitHub: [https://github.com/jakujobi/Ada_Compiler_Construction](https://github.com/jakujobi/Ada_Compiler_Construction)
# Date: 2025-04-18
# Version: 1.0
"""
Three Address Code Generator for Ada Compiler

This module generates Three Address Code (TAC) instructions from
the parsed and semantically analyzed Abstract Syntax Tree (AST).

It handles:
- Variable depth resolution (variables at depth 1 use names, >1 use offsets)
- Constant propagation
- Procedure calls with parameter pushing
- Expression decomposition

The output is TAC code that follows the assignment specifications.
"""

import os
import sys
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple, Set
from pathlib import Path

# Add the parent directory to the path so we can import modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Token import Token
from Modules.RDParser import ParseTreeNode
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter, TableEntry
from Modules.Logger import Logger


class TACInstruction:
    """
    Represents a Three Address Code instruction.
    """
    
    def __init__(self, operation: str, arg1: str = None, arg2: str = None, result: str = None):
        """
        Initialize a TAC instruction.
        
        Args:
            operation: The operation (e.g., +, -, *, /, :=, push, call, etc.)
            arg1: First argument
            arg2: Second argument
            result: Result operand
        """
        self.operation = operation
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
    
    def is_label(self) -> bool:
        """
        Check if this instruction is a label.
        
        Returns:
            True if it's a label (operation is "LABEL"), False otherwise
        """
        return self.operation == "LABEL"
    
    def is_jump(self) -> bool:
        """
        Check if this instruction is a jump.
        
        Returns:
            True if it's a jump/branch (operation starts with "j" or is "goto"), False otherwise
        """
        return self.operation.startswith("j") or self.operation == "goto"
    
    def __str__(self) -> str:
        """
        Convert the instruction to its string representation.
        
        Returns:
            String representation of the TAC instruction
        """
        if self.is_label():
            return f"LABEL {self.arg1}"
        elif self.operation == "push":
            return f"push {self.arg1}"
        elif self.operation == "call":
            return f"call {self.arg1}"
        elif self.operation == "return":
            return "return"
        elif self.operation == ":=":
            return f"{self.result} := {self.arg1}"
        elif self.operation in ["+", "-", "*", "/", "and", "or", "mod", "rem"]:
            return f"{self.result} := {self.arg1} {self.operation} {self.arg2}"
        elif self.operation == "START":
            return f"START {self.arg1}"
        elif self.operation == "param":
            return f"param {self.arg1}"
        else:
            # Generic format for other operations
            parts = [self.operation]
            if self.arg1 is not None:
                parts.append(str(self.arg1))
            if self.arg2 is not None:
                parts.append(str(self.arg2))
            if self.result is not None:
                parts.append(str(self.result))
            return " ".join(parts)


class TACProgram:
    """
    Represents a complete TAC program, consisting of multiple TAC instructions.
    """
    
    def __init__(self, program_name: str):
        """
        Initialize a TAC program.
        
        Args:
            program_name: The name of the program (main procedure)
        """
        self.program_name = program_name
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
    
    def add_instruction(self, operation: str, arg1: str = None, arg2: str = None, result: str = None) -> TACInstruction:
        """
        Add a new TAC instruction to the program.
        
        Args:
            operation: The operation
            arg1: First argument
            arg2: Second argument
            result: Result operand
            
        Returns:
            The created TACInstruction object
        """
        instruction = TACInstruction(operation, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction
    
    def add_raw_instruction(self, instruction: TACInstruction) -> None:
        """
        Add an existing TACInstruction to the program.
        
        Args:
            instruction: The TACInstruction to add
        """
        self.instructions.append(instruction)
    
    def generate_temp(self) -> str:
        """
        Generate a new temporary variable name.
        
        Returns:
            A unique temporary variable name
        """
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def write_to_file(self, filename: str) -> bool:
        """
        Write the TAC program to a file.
        
        Args:
            filename: The path of the file to write to
            
        Returns:
            True if the file was written successfully, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                for instruction in self.instructions:
                    f.write(str(instruction) + '\n')
                
                # Add the START instruction if it's not already there
                if not any(instr.operation == "START" for instr in self.instructions):
                    f.write(f"START {self.program_name}\n")
            return True
        except Exception as e:
            print(f"Error writing TAC to file: {e}")
            return False
    
    def get_instructions(self) -> List[TACInstruction]:
        """
        Get all instructions in the program.
        
        Returns:
            List of all TAC instructions
        """
        return self.instructions
    
    def __str__(self) -> str:
        """
        Convert the program to its string representation.
        
        Returns:
            String representation of the entire TAC program
        """
        return "\n".join(str(instruction) for instruction in self.instructions)


class ThreeAddressCodeGenerator:
    """
    Generates Three Address Code (TAC) from a parse tree and symbol table.
    """
    
    def __init__(self, parse_tree: ParseTreeNode, symbol_table: AdaSymbolTable, logger: Logger = None):
        """
        Initialize the TAC generator.
        
        Args:
            parse_tree: The root of the parse tree from the parser
            symbol_table: The symbol table from semantic analysis
            logger: Optional logger for logging
        """
        self.parse_tree = parse_tree
        self.symbol_table = symbol_table
        self.logger = logger if logger else Logger()
        
        # Initialize type sizes (same as in semantic analyzer)
        self.type_sizes = {
            VarType.INT: 2,      # Integers have size 2
            VarType.CHAR: 1,     # Characters have size 1
            VarType.FLOAT: 4,    # Floats have size 4
            VarType.REAL: 4      # Alias for FLOAT
        }
        
        # Program state
        self.current_depth = 0
        self.proc_name = None
        self.tac_program = None
    
    def generate(self) -> TACProgram:
        """
        Generate TAC from the parse tree and symbol table.
        
        Returns:
            A TACProgram containing all the generated instructions
        """
        self.logger.info("Starting Three Address Code generation")
        
        # Determine the main procedure name (from the top-level procedure)
        if self.parse_tree.name == "ProgramList" and self.parse_tree.children:
            # Find first procedure in the program list
            prog_node = self.parse_tree.children[0]
            if prog_node.name == "Prog" and len(prog_node.children) > 1:
                id_node = prog_node.children[1]  # Second child should be ID
                if id_node.name == "ID" and id_node.token:
                    self.proc_name = id_node.token.lexeme
        elif self.parse_tree.name == "Prog" and len(self.parse_tree.children) > 1:
            id_node = self.parse_tree.children[1]  # Second child should be ID
            if id_node.name == "ID" and id_node.token:
                self.proc_name = id_node.token.lexeme
        
        if not self.proc_name:
            self.logger.error("Could not determine main procedure name")
            self.proc_name = "Main"  # Default name
        
        self.logger.info(f"Main procedure name identified: {self.proc_name}")
        
        # Create the TAC program
        self.tac_program = TACProgram(self.proc_name)
        
        # Generate TAC for the entire program
        if self.parse_tree.name == "ProgramList":
            for prog_node in self.parse_tree.children:
                if prog_node.name == "Prog":
                    self.process_procedure(prog_node)
        else:
            # Single procedure
            self.process_procedure(self.parse_tree)
        
        self.logger.info("Three Address Code generation completed")
        return self.tac_program
    
    def process_procedure(self, node: ParseTreeNode) -> None:
        """
        Process a procedure node and generate its TAC.
        
        Args:
            node: The procedure node to process
        """
        if node.name != "Prog" or len(node.children) < 2:
            self.logger.error(f"Invalid procedure node: {node.name}")
            return
        
        # Get procedure name
        id_node = node.children[1]
        if id_node.name != "ID" or not id_node.token:
            self.logger.error("Missing procedure identifier")
            return
        
        proc_name = id_node.token.lexeme
        self.logger.info(f"Processing procedure: {proc_name}")
        
        # Add procedure label
        self.tac_program.add_instruction("LABEL", proc_name)
        
        # Save the current depth and increment for entering procedure
        saved_depth = self.current_depth
        self.current_depth += 1  # Parameters
        
        # Process Args (parameters)
        args_node = self.find_child_by_name(node, "Args")
        
        # Process procedure body
        self.current_depth += 1  # Local variables
        
        # Process declarative part
        decl_part_node = self.find_child_by_name(node, "DeclarativePart")
        if decl_part_node:
            self.process_declarative_part(decl_part_node)
        
        # Process nested procedures
        procedures_node = self.find_child_by_name(node, "Procedures")
        if procedures_node:
            self.process_procedures(procedures_node)
        
        # Process statements
        seq_of_statements_node = self.find_child_by_name(node, "SeqOfStatements")
        if seq_of_statements_node:
            self.process_seq_of_statements(seq_of_statements_node)
        
        # Add return instruction at the end
        if proc_name != self.proc_name:  # Not the main procedure
            self.tac_program.add_instruction("return")
        
        # Restore depth
        self.current_depth = saved_depth
    
    def process_declarative_part(self, node: ParseTreeNode) -> None:
        """
        Process a declarative part node.
        
        Args:
            node: The DeclarativePart node to process
        """
        # No direct TAC generation needed for declarations, 
        # as variables are accessed when used in statements
        # This method exists for possible future extension
        pass
    
    def process_procedures(self, node: ParseTreeNode) -> None:
        """
        Process nested procedures.
        
        Args:
            node: The Procedures node to process
        """
        if not node or not node.children:
            return
        
        # Process the first Prog node (nested procedure)
        prog_node = self.find_child_by_name(node, "Prog")
        if prog_node:
            self.process_procedure(prog_node)
        
        # Process the rest of the procedures (if any)
        next_procedures = self.find_child_by_name(node, "Procedures")
        if next_procedures and next_procedures.children:
            self.process_procedures(next_procedures)
    
    def process_seq_of_statements(self, node: ParseTreeNode) -> None:
        """
        Process a sequence of statements.
        
        Args:
            node: The SeqOfStatements node to process
        """
        if not node or not node.children:
            return
        
        # Process the first statement
        statement_node = self.find_child_by_name(node, "Statement")
        if statement_node:
            self.process_statement(statement_node)
        
        # Process the rest of the statements (if any)
        semicolon_index = self.find_child_index_by_token_type(node, "SEMICOLON")
        if semicolon_index != -1 and semicolon_index < len(node.children) - 1:
            next_seq_of_statements = node.children[semicolon_index + 1]
            if next_seq_of_statements.name == "SeqOfStatements":
                self.process_seq_of_statements(next_seq_of_statements)
    
    def process_statement(self, node: ParseTreeNode) -> None:
        """
        Process a statement node.
        
        Args:
            node: The Statement node to process
        """
        # Find what type of statement it is
        if not node or not node.children:
            return
        
        # Check first child to determine statement type
        for child in node.children:
            if child.name == "AssignStat":
                self.process_assign_stat(child)
                return
            elif child.name == "ProcCall":
                self.process_proc_call(child)
                return
        
        self.logger.warning(f"Unknown statement type: {node.name}")
    
    def process_assign_stat(self, node: ParseTreeNode) -> None:
        """
        Process an assignment statement.
        
        Args:
            node: The AssignStat node to process
        """
        # Format: idt := Expr
        if not node or len(node.children) < 3:
            self.logger.error("Invalid assignment statement")
            return
        
        # Get target variable
        id_node = node.children[0]
        if id_node.name != "ID" or not id_node.token:
            self.logger.error("Invalid identifier in assignment")
            return
        
        var_name = id_node.token.lexeme
        target = self.resolve_variable(var_name)
        
        # Process the expression
        expr_node = self.find_child_by_name(node, "Expr")
        if not expr_node:
            self.logger.error("Missing expression in assignment")
            return
        
        expr_result = self.process_expr(expr_node)
        
        # Generate the assignment instruction
        self.tac_program.add_instruction(":=", expr_result, None, target)
    
    def process_proc_call(self, node: ParseTreeNode) -> None:
        """
        Process a procedure call.
        
        Args:
            node: The ProcCall node to process
        """
        # Format: idt ( Params )
        if not node or len(node.children) < 1:
            self.logger.error("Invalid procedure call")
            return
        
        # Get procedure name
        id_node = node.children[0]
        if id_node.name != "ID" or not id_node.token:
            self.logger.error("Invalid procedure identifier in call")
            return
        
        proc_name = id_node.token.lexeme
        
        # Process parameters
        params_node = self.find_child_by_name(node, "Params")
        if params_node:
            self.process_params(params_node, proc_name)
        
        # Generate call instruction
        self.tac_program.add_instruction("call", proc_name)
    
    def process_params(self, node: ParseTreeNode, proc_name: str) -> None:
        """
        Process procedure call parameters.
        
        Args:
            node: The Params node to process
            proc_name: The name of the procedure being called
        """
        # Get procedure entry to check parameter modes
        proc_entry = self.symbol_table.lookup(proc_name)
        if not proc_entry or proc_entry.entry_type != EntryType.PROCEDURE:
            self.logger.warning(f"Unknown procedure or not a procedure: {proc_name}")
            return
        
        # Collect parameters
        params = []
        self.collect_params(node, params)
        
        # Generate push instructions for each parameter
        for i, param in enumerate(params):
            # Determine if this is a pass-by-reference parameter
            is_ref = False
            if proc_entry.param_list and i < len(proc_entry.param_list):
                param_info = proc_entry.param_list[i]
                is_ref = param_info.mode in [ParameterMode.OUT, ParameterMode.INOUT]
            
            # Generate push instruction
            if is_ref:
                # Pass by reference (pushing address)
                self.tac_program.add_instruction("push", f"@{param}")
            else:
                # Pass by value
                self.tac_program.add_instruction("push", param)
    
    def collect_params(self, node: ParseTreeNode, params: List[str]) -> None:
        """
        Collect parameters from a Params node recursively.
        
        Args:
            node: The Params or ParamsTail node to process
            params: List to store collected parameters
        """
        if not node or not node.children:
            return
        
        # Check first child to determine parameter type
        for child in node.children:
            if child.name == "ID" and child.token:
                params.append(self.resolve_variable(child.token.lexeme))
            elif child.name == "NUM" and child.token:
                params.append(child.token.lexeme)
            elif child.name == "ParamsTail":
                self.collect_params(child, params)
    
    def process_expr(self, node: ParseTreeNode) -> str:
        """
        Process an expression and generate TAC for it.
        
        Args:
            node: The Expr node to process
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: Expr -> Relation
        if not node or not node.children:
            self.logger.error("Invalid expression")
            return "error"
        
        # Process the relation
        relation_node = self.find_child_by_name(node, "Relation")
        if relation_node:
            return self.process_relation(relation_node)
        
        return "error"
    
    def process_relation(self, node: ParseTreeNode) -> str:
        """
        Process a relation and generate TAC for it.
        
        Args:
            node: The Relation node to process
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: Relation -> SimpleExpr
        if not node or not node.children:
            self.logger.error("Invalid relation")
            return "error"
        
        # Process the simple expression
        simple_expr_node = self.find_child_by_name(node, "SimpleExpr")
        if simple_expr_node:
            return self.process_simple_expr(simple_expr_node)
        
        return "error"
    
    def process_simple_expr(self, node: ParseTreeNode) -> str:
        """
        Process a simple expression and generate TAC for it.
        
        Args:
            node: The SimpleExpr node to process
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: SimpleExpr -> Term MoreTerm
        if not node or len(node.children) < 1:
            self.logger.error("Invalid simple expression")
            return "error"
        
        # Process the first term
        term_node = self.find_child_by_name(node, "Term")
        if not term_node:
            self.logger.error("Missing term in simple expression")
            return "error"
        
        result = self.process_term(term_node)
        
        # Process more terms (if any)
        more_term_node = self.find_child_by_name(node, "MoreTerm")
        if more_term_node and more_term_node.children and more_term_node.children[0].name != "ε":
            result = self.process_more_term(more_term_node, result)
        
        return result
    
    def process_term(self, node: ParseTreeNode) -> str:
        """
        Process a term and generate TAC for it.
        
        Args:
            node: The Term node to process
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: Term -> Factor MoreFactor
        if not node or len(node.children) < 1:
            self.logger.error("Invalid term")
            return "error"
        
        # Process the factor
        factor_node = self.find_child_by_name(node, "Factor")
        if not factor_node:
            self.logger.error("Missing factor in term")
            return "error"
        
        result = self.process_factor(factor_node)
        
        # Process more factors (if any)
        more_factor_node = self.find_child_by_name(node, "MoreFactor")
        if more_factor_node and more_factor_node.children and more_factor_node.children[0].name != "ε":
            result = self.process_more_factor(more_factor_node, result)
        
        return result
    
    def process_more_term(self, node: ParseTreeNode, left_operand: str) -> str:
        """
        Process a MoreTerm node and generate TAC for it.
        
        Args:
            node: The MoreTerm node to process
            left_operand: The result of the left operand (previous term)
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: MoreTerm -> addopt Term MoreTerm | ε
        if not node or not node.children or node.children[0].name == "ε":
            return left_operand
        
        # Get the operator
        op_node = node.children[0]
        if not op_node or not op_node.token:
            self.logger.error("Missing operator in MoreTerm")
            return left_operand
        
        operator = op_node.token.lexeme
        
        # Get the right operand (Term)
        term_node = self.find_child_by_name(node, "Term")
        if not term_node:
            self.logger.error("Missing term in MoreTerm")
            return left_operand
        
        right_operand = self.process_term(term_node)
        
        # Generate the operation
        result = self.tac_program.generate_temp()
        self.tac_program.add_instruction(operator, left_operand, right_operand, result)
        
        # Process more terms (if any)
        more_term_node = self.find_child_by_name(node, "MoreTerm")
        if more_term_node and more_term_node.children and more_term_node.children[0].name != "ε":
            result = self.process_more_term(more_term_node, result)
        
        return result
    
    def process_more_factor(self, node: ParseTreeNode, left_operand: str) -> str:
        """
        Process a MoreFactor node and generate TAC for it.
        
        Args:
            node: The MoreFactor node to process
            left_operand: The result of the left operand (previous factor)
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: MoreFactor -> mulopt Factor MoreFactor | ε
        if not node or not node.children or node.children[0].name == "ε":
            return left_operand
        
        # Get the operator
        op_node = node.children[0]
        if not op_node or not op_node.token:
            self.logger.error("Missing operator in MoreFactor")
            return left_operand
        
        operator = op_node.token.lexeme
        
        # Get the right operand (Factor)
        factor_node = self.find_child_by_name(node, "Factor")
        if not factor_node:
            self.logger.error("Missing factor in MoreFactor")
            return left_operand
        
        right_operand = self.process_factor(factor_node)
        
        # Generate the operation
        result = self.tac_program.generate_temp()
        self.tac_program.add_instruction(operator, left_operand, right_operand, result)
        
        # Process more factors (if any)
        more_factor_node = self.find_child_by_name(node, "MoreFactor")
        if more_factor_node and more_factor_node.children and more_factor_node.children[0].name != "ε":
            result = self.process_more_factor(more_factor_node, result)
        
        return result
    
    def process_factor(self, node: ParseTreeNode) -> str:
        """
        Process a factor and generate TAC for it.
        
        Args:
            node: The Factor node to process
            
        Returns:
            The name of the variable or temporary containing the result
        """
        # Format: Factor -> idt | numt | ( Expr ) | not Factor | signopt Factor
        if not node or not node.children:
            self.logger.error("Invalid factor")
            return "error"
        
        first_child = node.children[0]
        
        if first_child.name == "ID" and first_child.token:
            # Variable
            return self.resolve_variable(first_child.token.lexeme)
        elif first_child.name == "NUM" and first_child.token:
            # Literal number
            return first_child.token.lexeme
        elif first_child.token and first_child.token.token_type.name == "LPAREN":
            # Parenthesized expression
            expr_node = self.find_child_by_name(node, "Expr")
            if expr_node:
                return self.process_expr(expr_node)
        elif first_child.token and first_child.token.token_type.name == "NOT":
            # Negation
            factor_node = self.find_child_by_name(node, "Factor")
            if factor_node:
                operand = self.process_factor(factor_node)
                result = self.tac_program.generate_temp()
                self.tac_program.add_instruction("not", operand, None, result)
                return result
        elif first_child.token and first_child.token.token_type.name in ["PLUS", "MINUS"]:
            # Signed factor
            sign = first_child.token.lexeme
            factor_node = self.find_child_by_name(node, "Factor")
            if factor_node:
                operand = self.process_factor(factor_node)
                if sign == "-":
                    result = self.tac_program.generate_temp()
                    self.tac_program.add_instruction("-", "0", operand, result)
                    return result
                else:
                    # Positive sign doesn't change value
                    return operand
        
        self.logger.error(f"Unhandled factor type: {first_child.name}")
        return "error"
    
    def resolve_variable(self, var_name: str) -> str:
        """
        Resolve a variable name to its TAC representation based on depth.
        
        Args:
            var_name: The variable name to resolve
            
        Returns:
            The TAC representation of the variable
        """
        entry = self.symbol_table.lookup(var_name)
        if not entry:
            self.logger.warning(f"Unknown variable: {var_name}")
            return var_name  # Use the name directly if not found
        
        # Constants are replaced by their literal values
        if entry.entry_type == EntryType.CONSTANT:
            return str(entry.const_value)
        
        # Variables at depth 1 use their actual names
        if entry.depth == 1:
            return var_name
        
        # Variables at depth > 1 use offset notation
        offset = self.calculate_offset(entry)
        if entry.depth > 0:
            # Local variable - negative offset
            return f"_BP-{offset}"
        else:
            # Parameter - positive offset
            return f"_BP+{offset}"
    
    def calculate_offset(self, entry) -> int:
        """
        Calculate the memory offset for a variable.
        
        Args:
            entry: The symbol table entry
            
        Returns:
            The offset value
        """
        if not entry or entry.offset is None:
            return 0
        
        # Just return the offset calculated by the semantic analyzer
        return entry.offset
    
    def find_child_by_name(self, node: ParseTreeNode, name: str) -> Optional[ParseTreeNode]:
        """
        Helper method to find a child node by name.
        
        Args:
            node: The parent node
            name: The name of the child node to find
            
        Returns:
            The child node if found, None otherwise
        """
        if not node or not node.children:
            return None
            
        for child in node.children:
            if child.name == name:
                return child
                
        return None
    
    def find_child_index_by_token_type(self, node: ParseTreeNode, token_type: str) -> int:
        """
        Helper method to find the index of a child node by token type.
        
        Args:
            node: The parent node
            token_type: The token type to search for
            
        Returns:
            The index of the child if found, -1 otherwise
        """
        if not node or not node.children:
            return -1
            
        for i, child in enumerate(node.children):
            if child.token and child.token.token_type.name == token_type:
                return i
                
        return -1


# For testing
if __name__ == "__main__":
    print("ThreeAddressCodeGenerator module - integrate with JohnA7.py driver program")