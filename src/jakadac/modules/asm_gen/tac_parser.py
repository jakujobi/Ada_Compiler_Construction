#!/usr/bin/env python3
# src/jakadac/modules/asm_gen/tac_parser.py
# tac_parser.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2025-05-4
# Version: 1.0
"""
Parses a .tac file into a list of ParsedTACInstruction objects.
"""
import re
from typing import List, Optional, Tuple

from .tac_instruction import ParsedTACInstruction, TACOpcode, TACOperand
from ..Logger import logger

class TACParser:
    """
    Parses a Three-Address Code (.tac) file.
    """

    def __init__(self, tac_filepath: str):
        """
        Initializes the TACParser.

        Args:
            tac_filepath: The path to the .tac file.
        """
        self.tac_filepath = tac_filepath
        # self.logger = logger # Uncomment for logging

    def _parse_operand(self, operand_str: Optional[str]) -> Optional[TACOperand]:
        """
        Parses a string representation of an operand into a TACOperand object.
        Handles '@' prefix for addresses and tries to identify literals.
        """
        if operand_str is None:
            return None

        val = operand_str
        is_address = False
        if operand_str.startswith('@'):
            is_address = True
            val = operand_str[1:]

        # Attempt to convert to numeric literal if possible
        try:
            # Check if it's an integer
            numeric_val = int(val)
            return TACOperand(value=numeric_val, is_address_of=is_address)
        except ValueError:
            try:
                # Check if it's a float
                numeric_val = float(val)
                return TACOperand(value=numeric_val, is_address_of=is_address)
            except ValueError:
                # Otherwise, it's a string (variable, temp, label)
                return TACOperand(value=val, is_address_of=is_address)

    def _parse_line(self, line_number: int, raw_line: str) -> Optional[ParsedTACInstruction]:
        """
        Parses a single line from the .tac file.
        """
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith('#'): # Skip empty lines or full-line comments
            return None # Or a specific instruction type for comments if needed

        label: Optional[str] = None
        instruction_part = stripped_line

        # Check for label
        label_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', stripped_line)
        if label_match:
            label = label_match.group(1)
            instruction_part = label_match.group(2).strip()
            if not instruction_part: # Line only contains a label
                return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.LABEL)
        
        # Handle string definitions like _S0: .ASCIZ "Hello"
        string_def_match = re.match(r'^(_S\d+):\s*\.ASCIZ\s*(".*?"|\'.*?\')', stripped_line, re.IGNORECASE)
        if string_def_match:
            str_label = string_def_match.group(1)
            str_value = string_def_match.group(2)
            return ParsedTACInstruction(
                line_number=line_number,
                raw_line=raw_line,
                label=str_label, # The string label itself
                opcode=TACOpcode.STRING_DEF,
                operand1=self._parse_operand(str_value) # Store the string value
            )

        parts = instruction_part.split(None, 1) # Split opcode from the rest
        if not parts: # Should not happen if instruction_part was non-empty
            return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.UNKNOWN)

        op_str = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""
        
        opcode = TACOpcode.from_string(op_str)
        dest, op1, op2 = None, None, None

        # Simple pattern matching based on common TAC structures.
        # This can be made more robust with regex for each opcode type.
        
        # Structure: result = op1 op op2 (e.g. x = y + z)
        # Need to handle op1 being a unary op for x = -y
        # Structure: result = op1 (e.g. x = y, x = 5)
        assign_match = re.match(r'^(.[^=\s]*)\s*=\s*(.[^+\-*/\s]*)\s*([+\-*/])\s*(.*)', args_str) # x = y + z
        assign_unary_match = re.match(r'^(.[^=\s]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_@\.\+\-]*)\s+([a-zA-Z_][a-zA-Z0-9_@\.\+\-]*)', args_str) # x = uminus y
        assign_simple_match = re.match(r'^(.[^=\s]*)\s*=\s*(.*)', args_str) # x = y

        if opcode == TACOpcode.ASSIGN: # '=' was the op_str
            if assign_match: # x = y + z (parsed as op1=y, operator=+, op2=z, dest=x)
                # This is a bit tricky, the TACGenerator produces "dest = op1 op op2"
                # but the parser might see "=" as the primary opcode.
                # Let's assume TAC is "dest = src" or "dest = src1 op src2"
                # If "op_str" is one of "+","-","*", etc. it's a binary op directly
                # This indicates the .tac file might be like: "x = y" or "_t1 = _t2 + _t3" where "=" is part of the line.
                # For "op_str" actually being "=", it's an assignment.
                # We assume the TAC input separates the assignment part
                # e.g. TAC line: `_t0 = A` -> op_str `_t0`, args_str `= A` (this is how TACGenerator.format might do it)
                # OR TAC line: `ASSIGN _t0 A`
                # Given `op_str` is from `parts[0]`, we need to adjust if `=` is not the opcode itself.

                # Hmm, i need to re-evaluate based on common .tac file structures:
                # 1. Label: Op Dest, Arg1, Arg2  (e.g. L1: ADD t1, a, b)
                # 2. Label: Op Dest, Arg1      (e.g. L1: ASSIGN t1, a  OR rdi t1)
                # 3. Label: Op Arg1            (e.g. L1: PUSH a OR GOTO L2)
                # 4. Label: Op                 (e.g. L1: WRLN)
                # 5. Label:                    (e.g. L1:)
                # 6.       Dest = Arg1 Op Arg2 (e.g. t1 = a + b) -> Op is +, Dest is t1, Arg1 is a, Arg2 is b
                # 7.       Dest = Op Arg1      (e.g. t1 = uminus a) -> Op is uminus, Dest is t1, Arg1 is a
                # 8.       Dest = Arg1         (e.g. t1 = a) -> Op is ASSIGN, Dest is t1, Arg1 is a
                
                # Case 6: t1 = a + b
                m = re.match(r'(.+?)\s*=\s*(.+?)\s*([+\-*/]|mod|rem|and|or)\s*(.+)', instruction_part)
                if m:
                    dest_str, op1_str, op_symbol_str, op2_str = m.groups()
                    opcode = TACOpcode.from_string(op_symbol_str) # Actual operator
                    dest = self._parse_operand(dest_str.strip())
                    op1 = self._parse_operand(op1_str.strip())
                    op2 = self._parse_operand(op2_str.strip())
                    return ParsedTACInstruction(line_number, raw_line, label, opcode, dest, op1, op2)

                # Case 7: t1 = uminus a
                m = re.match(r'(.+?)\s*=\s*(uminus|not)\s+(.+)', instruction_part, re.IGNORECASE) # Assuming uminus/not are keywords
                if m:
                    dest_str, op_keyword_str, op1_str = m.groups()
                    opcode = TACOpcode.from_string(op_keyword_str)
                    dest = self._parse_operand(dest_str.strip())
                    op1 = self._parse_operand(op1_str.strip())
                    return ParsedTACInstruction(line_number, raw_line, label, opcode, dest, op1)
                
                # Case 8: t1 = a
                m = re.match(r'(.+?)\s*=\s*(.+)', instruction_part)
                if m:
                    dest_str, op1_str = m.groups()
                    opcode = TACOpcode.ASSIGN # Explicitly assignment
                    dest = self._parse_operand(dest_str.strip())
                    op1 = self._parse_operand(op1_str.strip())
                    return ParsedTACInstruction(line_number, raw_line, label, opcode, dest, op1)

            # Fall through for other opcodes based on op_str (e.g. PUSH, CALL, RDI)
            # These generally follow "OPCODE arg1, arg2, arg3" structure
            # where args_str contains "arg1, arg2, arg3"
            
            arg_parts = [a.strip() for a in args_str.split(',') if a.strip()] if args_str else []

            if opcode in [TACOpcode.ADD, TACOpcode.SUB, TACOpcode.MUL, TACOpcode.DIV, TACOpcode.MOD, TACOpcode.REM,
                        TACOpcode.IF_EQ, TACOpcode.IF_NE, TACOpcode.IF_LT, TACOpcode.IF_LE, TACOpcode.IF_GT, TACOpcode.IF_GE]:
                # Expects: Op Dest, Op1, Op2 (for arithmetic) or Op Op1, Op2, Label (for conditional jumps)
                if opcode.name.startswith("IF_"): # if op1 rel_op op2 goto label_dest
                    if len(arg_parts) == 3:
                        op1 = self._parse_operand(arg_parts[0])
                        op2 = self._parse_operand(arg_parts[1])
                        dest = self._parse_operand(arg_parts[2]) # Jump label
                elif len(arg_parts) == 3: # Arithmetic
                    dest = self._parse_operand(arg_parts[0])
                    op1 = self._parse_operand(arg_parts[1])
                    op2 = self._parse_operand(arg_parts[2])

            elif opcode in [TACOpcode.ASSIGN, TACOpcode.UMINUS, TACOpcode.RETRIEVE, TACOpcode.READ_INT]:
                # Expects: Op Dest, Op1 (ASSIGN, UMINUS) or Op Dest (RETRIEVE, READ_INT)
                if len(arg_parts) == 2: # ASSIGN, UMINUS
                    dest = self._parse_operand(arg_parts[0])
                    op1 = self._parse_operand(arg_parts[1])
                elif len(arg_parts) == 1: # RETRIEVE, READ_INT
                    dest = self._parse_operand(arg_parts[0])
            
            elif opcode in [TACOpcode.PUSH, TACOpcode.CALL, TACOpcode.GOTO, TACOpcode.WRITE_INT, TACOpcode.WRITE_STR, TACOpcode.PROC_BEGIN, TACOpcode.PROC_END, TACOpcode.RETURN, TACOpcode.PROGRAM_START]:
                # Expects: Op Arg1 (or Op Arg1, Arg2 for CALL/PROC_BEGIN if they include counts)
                if len(arg_parts) >= 1:
                    op1 = self._parse_operand(arg_parts[0]) # ProcName, Label, VarToPush/Write
                if opcode == TACOpcode.CALL and len(arg_parts) > 1: # Optional: num_params for call
                    op2 = self._parse_operand(arg_parts[1]) # Num params
                elif opcode == TACOpcode.PROC_BEGIN and len(arg_parts) > 1: # Optional: size_locals, size_params
                    op2 = self._parse_operand(arg_parts[1]) # Could bundle sizes or have more operands
                # if RETURN has a value: Op Arg1
                
            elif opcode == TACOpcode.WRITE_NEWLINE: # No args
                pass
            
            else: # Default for unknown or simple opcodes if args exist
                if len(arg_parts) >= 1: op1 = self._parse_operand(arg_parts[0])
                if len(arg_parts) >= 2: op2 = self._parse_operand(arg_parts[1])
                if len(arg_parts) >= 3: dest = self._parse_operand(arg_parts[2]) # Or some other convention


        return ParsedTACInstruction(
            line_number=line_number,
            raw_line=raw_line,
            label=label,
            opcode=opcode,
            destination=dest,
            operand1=op1,
            operand2=op2
        )

    def parse_tac_file(self) -> List[ParsedTACInstruction]:
        """
        Reads the .tac file and parses all lines.
        Returns:
            A list of ParsedTACInstruction objects.
        """
        instructions: List[ParsedTACInstruction] = []
        try:
            with open(self.tac_filepath, 'r', encoding='utf-8') as f:
                for i, line_content in enumerate(f):
                    parsed_instruction = self._parse_line(i + 1, line_content)
                    if parsed_instruction:
                        instructions.append(parsed_instruction)
            # self.logger.info(f"Successfully parsed {len(instructions)} TAC instructions from '{self.tac_filepath}'.")
        except FileNotFoundError:
            # self.logger.error(f"TAC file not found: '{self.tac_filepath}'")
            print(f"Error: TAC file not found: '{self.tac_filepath}'") # Basic error
            # Consider raising an exception or returning empty list
        except Exception as e:
            # self.logger.error(f"Error parsing TAC file '{self.tac_filepath}': {e}")
            print(f"Error: Could not parse TAC file '{self.tac_filepath}': {e}") # Basic error
            # Consider raising an exception

        return instructions

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    # Create a dummy .tac file
    dummy_tac_content = """


# This is a comment
_S0: .ASCIZ "Hello World"
_S1: .ASCIZ "Input an integer: "

MAIN_PROC:
    proc MAIN_PROC
    _t0 = 5
    _t1 = _t0 + 3
    A = _t1
    wrs _S1
    rdi B
    push @A  # Pass address of A
    push B   # Pass value of B
    call MY_SUB, 2
    wri A
    wrln
    endp MAIN_PROC

MY_SUB:
    proc MY_SUB
    # Params: pA (ref), pB (val)
    # _BP+6 is pA (address)
    # _BP+4 is pB (value)
    _t2 = _BP+4   # Load value of pB
    # To use pA, you'd typically load its address into a reg, then dereference
    # e.g., load_addr_reg _BP+6 -> bx
    #        load_indirect _t3, bx  (dereference)
    # For simplicity, assume ASM generator handles this.
    # Here, we might see TAC like:
    # DEREF _temp_addr_holder, _BP+6  (hypothetical)
    # STORE_INDIRECT _temp_addr_holder, _t2 (hypothetical: *pA = _t2)
    # For now, let's assume the ASM layer handles dereferencing based on '@' or type info.
    # This parser is more about the raw TAC structure.
    C = _t2 * 2
    _temp_for_param_A_val = 100 # Pretend calculation for the parameter passed by reference
    # Store back into A (via its address passed as pA) would be complex in pure TAC like this
    # Typically: param_addr = _BP+6 ; *param_addr = _temp_for_param_A_val
    # Or, if simplified: _BP+6 = _temp_for_param_A_val (meaning store into address at _BP+6)
    # Let's assume for parsing, it might look like:
    # ASSIGN_INDIRECT _BP+6, _temp_for_param_A_val  (if a special opcode)
    # Or the simpler form as generated by current TACGen:
    _BP+6 = _temp_for_param_A_val # This means the *variable* at BP+6 (param A) is assigned
                                 # This needs careful handling in ASM gen if BP+6 holds an address
    endp MY_SUB

    START PROC MAIN_PROC
"""
    dummy_tac_path = "dummy_test.tac"
    with open(dummy_tac_path, "w", encoding="utf-8") as f:
        f.write(dummy_tac_content)

    print(f"Created dummy TAC file: {dummy_tac_path}")
    parser = TACParser(dummy_tac_path)
    parsed_instructions = parser.parse_tac_file()

    if parsed_instructions:
        print(f"\n--- Parsed {len(parsed_instructions)} TAC Instructions ---")
        for instr in parsed_instructions:
            print(instr)
    else:
        print("No instructions parsed or error occurred.")

    # Example of how to access components:
    # if parsed_instructions:
    #     first_instr = parsed_instructions[0]
    #     print(f"\nFirst instruction opcode: {first_instr.opcode}")
    #     if first_instr.destination:
    #         print(f"Destination: {first_instr.destination.value}, is_addr: {first_instr.destination.is_address_of}")