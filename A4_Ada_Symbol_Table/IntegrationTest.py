#!/usr/bin/env python3
# IntegrationTest.py
# Author: John Akujobi
# Date: 2025-03-13
# Description: Test file demonstrating integration between the symbol table and other compiler components

import os
import sys
from typing import List

# Add the parent directory to the path so we can import the modules
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

# Import the necessary modules
from Modules.AdaSymbolTable import AdaSymbolTable, VarType, EntryType, ParameterMode, Parameter
from Modules.Token import Token
from Modules.Definitions import Definitions
from Modules.LexicalAnalyzer import LexicalAnalyzer

def test_integration_with_lexical_analyzer():
    """
    Test integration with the lexical analyzer by processing Ada code
    directly and inserting the resulting tokens into the symbol table.
    """
    print("\n=== Integration with Lexical Analyzer ===")
    
    # Sample Ada code with declarations
    ada_code = """
    procedure Test is
        a, b : INTEGER;
        c : FLOAT;
        CONST_PI : constant := 3.14159;
    begin
        a := 5;
        b := 10;
        c := a * b * CONST_PI;
    end Test;
    """
    
    # Create a lexical analyzer and analyze the code
    print("Analyzing Ada code...")
    lexer = LexicalAnalyzer()
    tokens = lexer.analyze_string(ada_code)
    
    # Create a symbol table
    symbol_table = AdaSymbolTable()
    
    # Process tokens and build symbol table
    # This is a simplified version of what the parser would do
    print("\nBuilding symbol table from tokens...")
    
    # Track current depth (scope)
    current_depth = 0
    variables = []
    
    # Process tokens to identify declarations (simplified parser simulation)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # Enter new scope on 'procedure' or 'begin'
        if token.token_type == Definitions.TokenType.PROCEDURE or token.token_type == Definitions.TokenType.BEGIN:
            current_depth += 1
            print(f"Entering scope at depth {current_depth}")
            
        # Exit scope on 'end'
        elif token.token_type == Definitions.TokenType.END:
            print(f"Exiting scope at depth {current_depth}")
            symbol_table.deleteDepth(current_depth)
            current_depth -= 1
            
        # Process variable declarations
        elif token.token_type == Definitions.TokenType.ID:
            # Check if we're in a declaration part (followed by ":" and a type)
            if i + 2 < len(tokens) and tokens[i+1].token_type == Definitions.TokenType.COLON:
                var_name = token.lexeme
                variables.append(var_name)
                
                # Keep collecting variable names if there are commas
                j = i + 1
                while j < len(tokens) and tokens[j].token_type == Definitions.TokenType.COMMA:
                    j += 1
                    if j < len(tokens) and tokens[j].token_type == Definitions.TokenType.ID:
                        var_name = tokens[j].lexeme
                        variables.append(var_name)
                        j += 1
                
                # Now find the type after ':'
                while j < len(tokens) and tokens[j].token_type != Definitions.TokenType.SEMI:
                    if tokens[j].token_type == Definitions.TokenType.INTEGERT:
                        # Insert all collected variables with INTEGER type
                        for var in variables:
                            entry = symbol_table.insert(var, tokens[j], current_depth)
                            entry.set_variable_info(VarType.INT, 0, 4)  # Simplified offset management
                            print(f"Added variable: {var} (INTEGER) at depth {current_depth}")
                    elif tokens[j].token_type == Definitions.TokenType.REALT:
                        # Insert all collected variables with FLOAT type
                        for var in variables:
                            entry = symbol_table.insert(var, tokens[j], current_depth)
                            entry.set_variable_info(VarType.FLOAT, 0, 8)  # Simplified offset management
                            print(f"Added variable: {var} (FLOAT) at depth {current_depth}")
                    j += 1
                
                # Reset variables list
                variables = []
                i = j
                continue
                
            # Process constant declarations
            elif i + 4 < len(tokens) and tokens[i+1].token_type == Definitions.TokenType.COLON and tokens[i+2].token_type == Definitions.TokenType.CONSTANT:
                const_name = token.lexeme
                # Find the value after ':='
                j = i + 3
                while j < len(tokens) and tokens[j].token_type != Definitions.TokenType.ASSIGNOP:
                    j += 1
                
                if j + 1 < len(tokens) and tokens[j+1].token_type == Definitions.TokenType.FLOATLIT:
                    value = float(tokens[j+1].lexeme)
                    entry = symbol_table.insert(const_name, token, current_depth)
                    entry.set_constant_info(VarType.FLOAT, value)
                    print(f"Added constant: {const_name} = {value} at depth {current_depth}")
                elif j + 1 < len(tokens) and tokens[j+1].token_type == Definitions.TokenType.INTLIT:
                    value = int(tokens[j+1].lexeme)
                    entry = symbol_table.insert(const_name, token, current_depth)
                    entry.set_constant_info(VarType.INT, value)
                    print(f"Added constant: {const_name} = {value} at depth {current_depth}")
                
                # Find semicolon
                while j < len(tokens) and tokens[j].token_type != Definitions.TokenType.SEMI:
                    j += 1
                
                i = j
                continue
        
        i += 1
    
    # Display symbol table entries at each depth
    print("\nFinal Symbol Table Contents:")
    for depth in range(current_depth + 2):  # +2 to ensure we check one level beyond the current depth
        entries = symbol_table.writeTable(depth)
        if entries:
            print(f"\nEntries at depth {depth}:")
            for lexeme, entry in entries.items():
                print(f"  {entry}")

def test_integration_with_semantic_analyzer():
    """
    Test integration with a semantic analyzer by checking type compatibility
    in Ada expressions using the symbol table.
    """
    print("\n=== Integration with Semantic Analyzer ===")
    
    # Create a symbol table with some entries
    symbol_table = AdaSymbolTable()
    
    # Add some entries at depth 1
    a = symbol_table.insert("a", Token(Definitions.TokenType.ID, "a", 1, 1), 1)
    a.set_variable_info(VarType.INT, 0, 4)
    
    b = symbol_table.insert("b", Token(Definitions.TokenType.ID, "b", 1, 5), 1)
    b.set_variable_info(VarType.FLOAT, 4, 8)
    
    # Simulate a semantic analyzer checking type compatibility
    print("Performing semantic analysis on expressions...")
    
    # Check expression "a + 5"
    print("\nExpression: a + 5")
    a_entry = symbol_table.lookup("a")
    if a_entry and a_entry.entry_type == EntryType.VARIABLE:
        int_lit = Token(Definitions.TokenType.INTLIT, "5", 1, 10)
        int_lit_type = VarType.INT  # Infer type from the token
        
        # Check if types are compatible for addition
        if a_entry.var_type == int_lit_type:
            print("  Type check OK: Both operands are integers")
            print("  Expression type: INTEGER")
        else:
            print("  Type mismatch: Cannot add INT and FLOAT")
    else:
        print("  Error: Symbol 'a' not found or not a variable")
    
    # Check expression "a + b"
    print("\nExpression: a + b")
    a_entry = symbol_table.lookup("a")
    b_entry = symbol_table.lookup("b")
    if a_entry and b_entry and a_entry.entry_type == EntryType.VARIABLE and b_entry.entry_type == EntryType.VARIABLE:
        # Check if types are compatible for addition
        if a_entry.var_type == b_entry.var_type:
            print("  Type check OK: Both operands have same type")
        else:
            print("  Type warning: Mixing INT and FLOAT in addition")
            print("  Expression type: FLOAT (wider type)")
    else:
        print("  Error: Symbols not found or not variables")

def test_integration_with_code_generator():
    """
    Test integration with a code generator by using offsets and sizes from
    the symbol table to generate memory addressing code.
    """
    print("\n=== Integration with Code Generator ===")
    
    # Create a symbol table with some entries
    symbol_table = AdaSymbolTable()
    
    # Add variables with proper offsets
    # In a real compiler, the offsets would be calculated based on the memory layout
    symbol_table.insert("a", Token(Definitions.TokenType.ID, "a", 1, 1), 1).set_variable_info(VarType.INT, 0, 4)
    symbol_table.insert("b", Token(Definitions.TokenType.ID, "b", 1, 5), 1).set_variable_info(VarType.INT, 4, 4)
    symbol_table.insert("c", Token(Definitions.TokenType.ID, "c", 1, 10), 1).set_variable_info(VarType.FLOAT, 8, 8)
    
    # Simulate code generator for the assignment "a := b + 5"
    print("\nGenerating code for: a := b + 5")
    
    # Look up variables
    a_entry = symbol_table.lookup("a")
    b_entry = symbol_table.lookup("b")
    
    if a_entry and b_entry:
        print("  ; Load the value of b into register R1")
        print(f"  LOAD R1, [SP+{b_entry.offset}]  ; Offset from symbol table: {b_entry.offset}")
        
        print("  ; Add constant 5 to register R1")
        print("  ADD R1, R1, #5")
        
        print("  ; Store result in variable a")
        print(f"  STORE [SP+{a_entry.offset}], R1  ; Offset from symbol table: {a_entry.offset}")
    else:
        print("  Error: Required symbols not found")

def main():
    """Main function to run all integration tests."""
    print("Symbol Table Integration Tests")
    print("=" * 50)
    
    try:
        test_integration_with_lexical_analyzer()
        test_integration_with_semantic_analyzer()
        test_integration_with_code_generator()
        
        print("\nAll integration tests completed successfully!")
    except Exception as e:
        print(f"Error during integration tests: {e}")

if __name__ == "__main__":
    main()
