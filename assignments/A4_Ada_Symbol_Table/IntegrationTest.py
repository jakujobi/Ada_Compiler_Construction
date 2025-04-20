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

# Create an instance of Definitions to access token types
definitions = Definitions()

def test_integration_with_lexical_analyzer():
    """
    Test integration with the lexical analyzer by processing simulated tokens
    and inserting them into the symbol table.
    """
    print("\n=== Integration with Lexical Analyzer ===")
    
    # Sample Ada code (for reference only, not actually parsed)
    print("Simulating lexical analysis of Ada code:")
    print("""
    procedure Test is
        a, b : INTEGER;
        c : FLOAT;
        CONST_PI : constant := 3.14159;
    begin
        a := 5;
        b := 10;
        c := a * b * CONST_PI;
    end Test;
    """)
    
    # Create simulated tokens that would come from lexical analysis
    print("\nCreating simulated tokens...")
    tokens = [
        # procedure Test is
        Token(definitions.TokenType.PROCEDURE, "procedure", 1, 1),
        Token(definitions.TokenType.ID, "Test", 1, 11),
        Token(definitions.TokenType.IS, "is", 1, 16),
        
        # a, b : INTEGER;
        Token(definitions.TokenType.ID, "a", 2, 5),
        Token(definitions.TokenType.COMMA, ",", 2, 6),
        Token(definitions.TokenType.ID, "b", 2, 8),
        Token(definitions.TokenType.COLON, ":", 2, 10),
        Token(definitions.TokenType.INTEGER, "INTEGER", 2, 12),
        Token(definitions.TokenType.SEMICOLON, ";", 2, 19),
        
        # c : FLOAT;
        Token(definitions.TokenType.ID, "c", 3, 5),
        Token(definitions.TokenType.COLON, ":", 3, 7),
        Token(definitions.TokenType.FLOAT, "FLOAT", 3, 9),
        Token(definitions.TokenType.SEMICOLON, ";", 3, 14),
        
        # CONST_PI : constant := 3.14159;
        Token(definitions.TokenType.ID, "CONST_PI", 4, 5),
        Token(definitions.TokenType.COLON, ":", 4, 14),
        Token(definitions.TokenType.CONSTANT, "constant", 4, 16),
        Token(definitions.TokenType.ASSIGN, ":=", 4, 25),
        Token(definitions.TokenType.REAL, "3.14159", 4, 28),
        Token(definitions.TokenType.SEMICOLON, ";", 4, 35),
        
        # begin
        Token(definitions.TokenType.BEGIN, "begin", 5, 1),
        
        # a := 5;
        Token(definitions.TokenType.ID, "a", 6, 5),
        Token(definitions.TokenType.ASSIGN, ":=", 6, 7),
        Token(definitions.TokenType.NUM, "5", 6, 10),
        Token(definitions.TokenType.SEMICOLON, ";", 6, 11),
        
        # b := 10;
        Token(definitions.TokenType.ID, "b", 7, 5),
        Token(definitions.TokenType.ASSIGN, ":=", 7, 7),
        Token(definitions.TokenType.NUM, "10", 7, 10),
        Token(definitions.TokenType.SEMICOLON, ";", 7, 12),
        
        # c := a * b * CONST_PI;
        Token(definitions.TokenType.ID, "c", 8, 5),
        Token(definitions.TokenType.ASSIGN, ":=", 8, 7),
        Token(definitions.TokenType.ID, "a", 8, 10),
        Token(definitions.TokenType.MULOP, "*", 8, 12),
        Token(definitions.TokenType.ID, "b", 8, 14),
        Token(definitions.TokenType.MULOP, "*", 8, 16),
        Token(definitions.TokenType.ID, "CONST_PI", 8, 18),
        Token(definitions.TokenType.SEMICOLON, ";", 8, 26),
        
        # end Test;
        Token(definitions.TokenType.END, "end", 9, 1),
        Token(definitions.TokenType.ID, "Test", 9, 5),
        Token(definitions.TokenType.SEMICOLON, ";", 9, 9)
    ]
    
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
        if token.token_type == definitions.TokenType.PROCEDURE or token.token_type == definitions.TokenType.BEGIN:
            current_depth += 1
            print(f"Entering scope at depth {current_depth}")
            
        # Exit scope on 'end'
        elif token.token_type == definitions.TokenType.END:
            if current_depth <= 0:
                print("Warning: Attempting to exit scope when already at global scope!")
            else:
                print(f"Exiting scope at depth {current_depth}")
                symbol_table.deleteDepth(current_depth)
                current_depth -= 1
            
        # Process variable declarations
        elif token.token_type == definitions.TokenType.ID:
            # Check if we're in a declaration part (followed by ":" and a type)
            if i + 2 < len(tokens) and tokens[i+1].token_type == definitions.TokenType.COLON:
                var_name = token.lexeme
                variables.append(var_name)
                
                # Keep collecting variable names if there are commas
                j = i + 1
                while j < len(tokens) and tokens[j].token_type == definitions.TokenType.COMMA:
                    j += 1
                    if j < len(tokens) and tokens[j].token_type == definitions.TokenType.ID:
                        var_name = tokens[j].lexeme
                        variables.append(var_name)
                        j += 1
                
                # Now find the type after ':'
                while j < len(tokens) and tokens[j].token_type != definitions.TokenType.SEMICOLON:
                    if tokens[j].token_type == definitions.TokenType.INTEGER:
                        # Insert all collected variables with INTEGER type
                        for var in variables:
                            try:
                                entry = symbol_table.insert(var, tokens[j], current_depth)
                                entry.set_variable_info(VarType.INT, 0, 4)  # Simplified offset management
                                print(f"Added variable: {var} (INTEGER) at depth {current_depth}")
                            except ValueError as e:
                                print(f"Error adding variable {var}: {e}")
                    elif tokens[j].token_type == definitions.TokenType.FLOAT:
                        # Insert all collected variables with FLOAT type
                        for var in variables:
                            try:
                                entry = symbol_table.insert(var, tokens[j], current_depth)
                                entry.set_variable_info(VarType.FLOAT, 0, 8)  # Simplified offset management
                                print(f"Added variable: {var} (FLOAT) at depth {current_depth}")
                            except ValueError as e:
                                print(f"Error adding variable {var}: {e}")
                    j += 1
                
                # Reset variables list
                variables = []
                i = j
                continue
                
            # Process constant declarations
            elif i + 4 < len(tokens) and tokens[i+1].token_type == definitions.TokenType.COLON and tokens[i+2].token_type == definitions.TokenType.CONSTANT:
                const_name = token.lexeme
                # Find the value after ':='
                j = i + 3
                while j < len(tokens) and tokens[j].token_type != definitions.TokenType.ASSIGN:
                    j += 1
                
                if j + 1 < len(tokens) and tokens[j+1].token_type == definitions.TokenType.REAL:
                    value = float(tokens[j+1].lexeme)
                    try:
                        entry = symbol_table.insert(const_name, token, current_depth)
                        entry.set_constant_info(VarType.FLOAT, value)
                        print(f"Added constant: {const_name} = {value} at depth {current_depth}")
                    except ValueError as e:
                        print(f"Error adding constant {const_name}: {e}")
                elif j + 1 < len(tokens) and tokens[j+1].token_type == definitions.TokenType.NUM:
                    value = int(tokens[j+1].lexeme)
                    try:
                        entry = symbol_table.insert(const_name, token, current_depth)
                        entry.set_constant_info(VarType.INT, value)
                        print(f"Added constant: {const_name} = {value} at depth {current_depth}")
                    except ValueError as e:
                        print(f"Error adding constant {const_name}: {e}")
                
                # Find semicolon
                while j < len(tokens) and tokens[j].token_type != definitions.TokenType.SEMICOLON:
                    j += 1
                
                i = j
                continue
        
        i += 1
    
    # Display symbol table entries at each depth
    print("\nFinal Symbol Table Contents:")
    for depth in range(current_depth + 2):  # +2 to ensure we check one level beyond the current depth
        try:
            entries = symbol_table.writeTable(depth)
            if entries:
                print(f"\nEntries at depth {depth}:")
                for lexeme, entry in entries.items():
                    print(f"  {entry}")
        except ValueError as e:
            print(f"Error accessing depth {depth}: {e}")

def test_integration_with_semantic_analyzer():
    """
    Test integration with a semantic analyzer by checking type compatibility
    in Ada expressions using the symbol table.
    """
    print("\n=== Integration with Semantic Analyzer ===")
    
    # Create a symbol table with some entries
    symbol_table = AdaSymbolTable()
    
    # Add some entries at depth 1
    a = symbol_table.insert("a", Token(definitions.TokenType.ID, "a", 1, 1), 1)
    a.set_variable_info(VarType.INT, 0, 4)
    
    b = symbol_table.insert("b", Token(definitions.TokenType.ID, "b", 1, 5), 1)
    b.set_variable_info(VarType.FLOAT, 4, 8)
    
    # Simulate a semantic analyzer checking type compatibility
    print("Performing semantic analysis on expressions...")
    
    # Function to check if types are compatible for an operation
    def check_type_compatibility(type1, type2, operation):
        """Check if two types are compatible for a given operation."""
        if type1 == type2:
            return True, type1
        elif (type1 == VarType.INT and type2 == VarType.FLOAT) or \
             (type1 == VarType.FLOAT and type2 == VarType.INT):
            # Int and float can be mixed, result is float
            return True, VarType.FLOAT
        elif (type1 == VarType.CHAR and type2 == VarType.CHAR) and operation == '+':
            # Chars can only be concatenated
            return True, VarType.CHAR
        else:
            type1_name = type1.name if type1 else "UNKNOWN"
            type2_name = type2.name if type2 else "UNKNOWN"
            return False, f"Incompatible types: {type1_name} and {type2_name} for operation '{operation}'"
    
    # Check expression "a + 5"
    print("\nExpression: a + 5")
    a_entry = symbol_table.lookup("a")
    if a_entry and a_entry.entry_type == EntryType.VARIABLE:
        int_lit = Token(definitions.TokenType.NUM, "5", 1, 10)
        int_lit_type = VarType.INT  # Infer type from the token
        
        # Check if types are compatible for addition
        compatible, result_type = check_type_compatibility(a_entry.var_type, int_lit_type, '+')
        if compatible:
            print(f"  Type check OK: {a_entry.var_type.name} + {int_lit_type.name} is valid")
            print(f"  Expression type: {result_type.name}")
        else:
            print(f"  Type error: {result_type}")
    else:
        print("  Error: Symbol 'a' not found or not a variable")
    
    # Check expression "a + b"
    print("\nExpression: a + b")
    a_entry = symbol_table.lookup("a")
    b_entry = symbol_table.lookup("b")
    if a_entry and b_entry and a_entry.entry_type == EntryType.VARIABLE and b_entry.entry_type == EntryType.VARIABLE:
        # Check if types are compatible for addition
        compatible, result_type = check_type_compatibility(a_entry.var_type, b_entry.var_type, '+')
        if compatible:
            print(f"  Type check OK: {a_entry.var_type.name} + {b_entry.var_type.name} is valid")
            print(f"  Expression type: {result_type.name}")
        else:
            print(f"  Type error: {result_type}")
    else:
        print("  Error: Symbols not found or not variables")
        
    # Check incompatible expression for more detailed error message
    print("\nExpression: 'A' * 5 (incompatible types)")
    char_type = VarType.CHAR
    int_type = VarType.INT
    compatible, result_type = check_type_compatibility(char_type, int_type, '*')
    if compatible:
        print(f"  Type check OK: {char_type.name} * {int_type.name} is valid")
        print(f"  Expression type: {result_type.name}")
    else:
        print(f"  Type error: {result_type}")

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
    symbol_table.insert("a", Token(definitions.TokenType.ID, "a", 1, 1), 1).set_variable_info(VarType.INT, 0, 4)
    symbol_table.insert("b", Token(definitions.TokenType.ID, "b", 1, 5), 1).set_variable_info(VarType.INT, 4, 4)
    symbol_table.insert("c", Token(definitions.TokenType.ID, "c", 1, 10), 1).set_variable_info(VarType.FLOAT, 8, 8)
    
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
        if not a_entry:
            print("  Error: Symbol 'a' not found in symbol table")
        if not b_entry:
            print("  Error: Symbol 'b' not found in symbol table")
            
    # Generate code for a variable that doesn't exist
    print("\nGenerating code for: nonexistent := 10")
    nonexistent = symbol_table.lookup("nonexistent")
    if nonexistent:
        print("  ; Store 10 in nonexistent")
        print(f"  STORE [SP+{nonexistent.offset}], #10")
    else:
        print("  Error: Symbol 'nonexistent' not found in symbol table")
        print("  - Code generation cannot proceed for this assignment")
        print("  - This would typically trigger a compilation error")

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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
