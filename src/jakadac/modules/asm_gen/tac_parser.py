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
        self.logger = logger

    def _parse_operand(self, operand_str: Optional[str]) -> Optional[TACOperand]:
        """
        Parses a string representation of an operand into a TACOperand object.
        Handles '@' prefix for addresses and tries to identify literals.
        """
        if operand_str is None:
            self.logger.warning("TACParser._parse_operand: operand_str is None")
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
            self.logger.info(f"TACParser._parse_operand: parsed integer {numeric_val}")
            return TACOperand(value=numeric_val, is_address_of=is_address)
        except ValueError:
            try:
                # Check if it's a float
                numeric_val = float(val)
                self.logger.info(f"TACParser._parse_operand: parsed float {numeric_val}")
                return TACOperand(value=numeric_val, is_address_of=is_address)
            except ValueError:
                # Otherwise, it's a string (variable, temp, label)
                self.logger.info(f"TACParser._parse_operand: parsed string {val}")
                return TACOperand(value=val, is_address_of=is_address)

    def _parse_line(self, line_number: int, raw_line: str) -> Optional[ParsedTACInstruction]:
        """
        Parses a single line from the .tac file.
        """
        stripped_line = raw_line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            self.logger.info(f"L{line_number}: Skipping comment or empty line: '{raw_line.strip()}'")
            return None

        # --- Helper to clean comments from a string ---
        def clean_comment(s: Optional[str]) -> Optional[str]:
            if s is None: return None
            return s.split('#')[0].strip()
        # ---

        label: Optional[str] = None
        instruction_part = stripped_line # Full line initially
        
        # 1. Check for label
        label_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)', stripped_line)
        if label_match:
            label = label_match.group(1)
            instruction_part = label_match.group(2).strip() # Instruction part is what's AFTER the label
            self.logger.info(f"L{line_number}: Found label '{label}', pre-comment instruction_part: '{instruction_part}'")
            if not instruction_part or instruction_part.startswith('#'): # Line only contains a label (or label + comment)
                self.logger.info(f"L{line_number}: Line is label-only or label+comment.")
                return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.LABEL)
        
        # Clean comment from the determined instruction_part
        instruction_part = clean_comment(instruction_part)
        if not instruction_part: # If instruction part became empty after comment removal (e.g. "L1: #comment" or just " #comment")
             if label: # If there was a label, it's a label-only line
                 return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.LABEL)
             else: # Only a comment line, should have been caught by the initial check
                 return None


        self.logger.info(f"L{line_number}: Effective instruction part (label and comments stripped): '{instruction_part}'")

        # 2. Handle string definitions (e.g., _S0: .ASCIZ "Hello")
        # This check must happen BEFORE assignment checks, as "_S0:" could look like a variable.
        
        # Scenario A: Label was parsed, and it's a string label like _S0, and instruction is .ASCIZ
        if label and label.startswith("_S") and instruction_part.upper().startswith(".ASCIZ"):
            match_asciz = re.match(r'\.(ASCIZ)\s*(".*?"|\'.*?\')', instruction_part, re.IGNORECASE)
            if match_asciz:
                str_value_with_quotes = clean_comment(match_asciz.group(2))
                self.logger.info(f"L{line_number}: String def (Scenario A): Label '{label}', Value '{str_value_with_quotes}'")
                return ParsedTACInstruction(
                    line_number=line_number, raw_line=raw_line, label=label,
                    opcode=TACOpcode.STRING_DEF,
                    operand1=self._parse_operand(str_value_with_quotes)
                )

        # Scenario B: No label parsed separately, or label isn't _S*, check if full instruction_part is `_S<num>: .ASCIZ "..."`
        # This regex now applies to `instruction_part` which has had an *optional* outer label already stripped.
        # So if outer label was `L1:`, `instruction_part` is `_S0: .ASCIZ "..."`.
        # If no outer label, `instruction_part` is `_S0: .ASCIZ "..."`.
        string_def_match_full = re.match(r'^([_a-zA-Z][a-zA-Z0-9_]*):\s*\.(ASCIZ)\s*(".*?"|\'.*?\')', instruction_part, re.IGNORECASE)
        if string_def_match_full:
            str_def_label = string_def_match_full.group(1) # This is the _S0 part
            str_value_with_quotes = clean_comment(string_def_match_full.group(3))
            # Use outer label if present and this is a valid string def, otherwise use the string's own label.
            final_label_for_string_def = label if label else str_def_label
            # Ensure that if an outer label (e.g. L1) exists, the str_def_label is indeed the _S type.
            if str_def_label.startswith("_S"):
                 self.logger.info(f"L{line_number}: String def (Scenario B): Effective Label '{final_label_for_string_def}', String Label '{str_def_label}', Value '{str_value_with_quotes}'")
                 return ParsedTACInstruction(
                    line_number=line_number, raw_line=raw_line, label=final_label_for_string_def,
                    opcode=TACOpcode.STRING_DEF,
                    operand1=self._parse_operand(str_value_with_quotes)
                )

        # 3. Try to parse assignment-like structures first (dest = ... forms)
        #    dest = op1 BIN_OP op2 (e.g., t1 = a + b)
        bin_assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_@\.\-]*)\s*=\s*(\d+(?:\.\d+)?|[a-zA-Z_][a-zA-Z0-9_@\.\-]*)\s*([+\-*/]|mod|rem)\s*(\d+(?:\.\d+)?|[a-zA-Z_][a-zA-Z0-9_@\.\-]*)', instruction_part, re.IGNORECASE)
        if bin_assign_match:
            dest_str, op1_str, op_str, op2_str = map(clean_comment, bin_assign_match.groups())
            opcode = TACOpcode.from_string(op_str)
            self.logger.info(f"L{line_number}: Parsed binary assignment: D='{dest_str}', O1='{op1_str}', OP='{op_str}', O2='{op2_str}' -> {opcode}")
            return ParsedTACInstruction(line_number, raw_line, label, opcode,
                                        self._parse_operand(dest_str),
                                        self._parse_operand(op1_str),
                                        self._parse_operand(op2_str))

        #    dest = UN_OP op1 (e.g., t1 = uminus a)
        unary_assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_@\.+-]*)\s*=\s*(uminus|not)\s+([a-zA-Z_][a-zA-Z0-9_@\.+-]*)', instruction_part, re.IGNORECASE)
        if unary_assign_match:
            dest_str, op_str, op1_str = map(clean_comment, unary_assign_match.groups())
            opcode = TACOpcode.from_string(op_str)
            self.logger.info(f"L{line_number}: Parsed unary assignment: D='{dest_str}', OP='{op_str}', O1='{op1_str}' -> {opcode}")
            return ParsedTACInstruction(line_number, raw_line, label, opcode,
                                        self._parse_operand(dest_str),
                                        self._parse_operand(op1_str))
        
        #    dest = op1 (simple assignment, e.g., t1 = a  OR _t4 = retrieve)
        #    Regex for op1 should not be too greedy for keywords like 'retrieve' if they are meant to be opcodes.
        #    However, 'retrieve' is unique as it's an op that *returns a value into* a destination.
        # simple_assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_@\.\+\-]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_@\.\+\-\"\']*)', instruction_part)
        simple_assign_match = re.match(r'([a-zA-Z_][a-zA-Z0-9_@\.\-]*)\s*=\s*(\d+(?:\.\d+)?|[a-zA-Z_][a-zA-Z0-9_@\.\-]*|\"[^\"]*\"|\'[^\']*\')', instruction_part)
        if simple_assign_match:
            dest_str, op1_str_candidate = map(clean_comment, simple_assign_match.groups())
            
            if op1_str_candidate and op1_str_candidate.lower() == TACOpcode.RETRIEVE.value:
                opcode = TACOpcode.RETRIEVE
                op1_parsed = None # RETRIEVE has no source operand in "dest = retrieve" form
                self.logger.info(f"L{line_number}: Parsed RETRIEVE (from simple assign form): D='{dest_str}' -> {opcode}")
            else:
                opcode = TACOpcode.ASSIGN
                op1_parsed = self._parse_operand(op1_str_candidate)
                self.logger.info(f"L{line_number}: Parsed simple assignment: D='{dest_str}', O1='{op1_str_candidate}' -> {opcode}")

            return ParsedTACInstruction(line_number, raw_line, label, opcode,
                                        self._parse_operand(dest_str),
                                        op1_parsed) # op2 is None

        # 4. If not an assignment-like structure, parse as Opcode-first structure
        parts = instruction_part.split(None, 1) 
        op_str = clean_comment(parts[0]) if parts else ""
        args_str = clean_comment(parts[1]) if len(parts) > 1 else ""
        
        if not op_str: # instruction_part was empty or only whitespace after comment stripping
            self.logger.warning(f"L{line_number}: op_str became empty for instruction_part '{instruction_part}'. Original raw: '{raw_line.strip()}'")
            # This might occur if the line was just a comment or label + comment, should have been caught.
            # If a label exists, it's a label-only instruction.
            if label:
                return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.LABEL)
            return ParsedTACInstruction(line_number=line_number, raw_line=raw_line, label=label, opcode=TACOpcode.UNKNOWN, comment="Empty/Comment instruction part")


        # Special handling for "START PROC"
        if op_str.upper() == "START" and args_str and args_str.upper().startswith("PROC"):
            op_str_for_enum = "START PROC" # Canonical form
            self.logger.info(f"L{line_number}: Detected 'START PROC', op_str_for_enum='{op_str_for_enum}'")
            proc_parts = args_str.split(None, 1) # PROC might be followed by program name
            args_str = clean_comment(proc_parts[1]) if len(proc_parts) > 1 else ""
        else:
            op_str_for_enum = op_str

        opcode = TACOpcode.from_string(op_str_for_enum)
        self.logger.info(f"L{line_number}: Opcode-first: op_str='{op_str_for_enum}' -> {opcode}, args_str='{args_str}'")
        
        dest, op1, op2 = None, None, None
        
        arg_parts_raw = [clean_comment(p) for p in args_str.split(',') if clean_comment(p)] if args_str else []
        if not arg_parts_raw and args_str: # If no commas, try splitting by space, clean each part
            arg_parts_raw = [clean_comment(p) for p in args_str.split(None) if clean_comment(p)]
        
        # Filter out None/empty strings that might result from multiple clean_comment calls
        arg_parts = [ap for ap in arg_parts_raw if ap]

        self.logger.info(f"L{line_number}: Opcode-first: Parsed arg_parts: {arg_parts}")


        if opcode in [TACOpcode.PROC_BEGIN, TACOpcode.PROC_END, TACOpcode.PROGRAM_START]:
            if arg_parts: op1 = self._parse_operand(arg_parts[0])
        elif opcode == TACOpcode.CALL: 
            if len(arg_parts) >= 1: op1 = self._parse_operand(arg_parts[0]) 
            if len(arg_parts) >= 2: op2 = self._parse_operand(arg_parts[1]) 
        elif opcode in [TACOpcode.PUSH, TACOpcode.GOTO, TACOpcode.WRITE_INT, TACOpcode.WRITE_STR]:
            if arg_parts: op1 = self._parse_operand(arg_parts[0])
        elif opcode == TACOpcode.RETURN:
            if arg_parts: op1 = self._parse_operand(arg_parts[0]) # Will be None if args_str was empty/comment
        elif opcode == TACOpcode.READ_INT:
            if arg_parts: dest = self._parse_operand(arg_parts[0])
        elif opcode == TACOpcode.RETRIEVE: # Form: retrieve dest_var
            # Note: "dest = retrieve" is handled by simple_assign_match section
            if arg_parts: dest = self._parse_operand(arg_parts[0])
        elif opcode in [TACOpcode.IF_EQ_GOTO, TACOpcode.IF_NE_GOTO, TACOpcode.IF_LT_GOTO, TACOpcode.IF_LE_GOTO, TACOpcode.IF_GT_GOTO, TACOpcode.IF_GE_GOTO]:
            if len(arg_parts) >= 3: # if_op op1, op2, label_target
                op1 = self._parse_operand(arg_parts[0])
                op2 = self._parse_operand(arg_parts[1])
                dest = self._parse_operand(arg_parts[2]) # Using dest for the target label
            elif len(arg_parts) == 2: # if_op val, label
                op1 = self._parse_operand(arg_parts[0])
                dest = self._parse_operand(arg_parts[1]) # Target label in dest
        elif opcode == TACOpcode.ASSIGN: # Explicit "ASSIGN dest, src"
            if len(arg_parts) >= 2:
                dest = self._parse_operand(arg_parts[0])
                op1 = self._parse_operand(arg_parts[1])
        elif opcode in [TACOpcode.ADD, TACOpcode.SUB, TACOpcode.MUL, TACOpcode.DIV, TACOpcode.MOD, TACOpcode.REM]:
            if len(arg_parts) >= 3: # "OP dest, src1, src2"
                dest = self._parse_operand(arg_parts[0])
                op1 = self._parse_operand(arg_parts[1])
                op2 = self._parse_operand(arg_parts[2])
        elif opcode == TACOpcode.UMINUS or opcode == TACOpcode.NOT_OP: # Explicit "OP dest, src"
             if len(arg_parts) >= 2:
                dest = self._parse_operand(arg_parts[0])
                op1 = self._parse_operand(arg_parts[1])
        # TACOpcode.LABEL, TACOpcode.WRITE_NEWLINE, TACOpcode.UNKNOWN handled.
        
        self.logger.info(f"L{line_number}: Final Parsed Instruction: Label='{label}', Opcode='{opcode}', Dest='{dest}', Op1='{op1}', Op2='{op2}'")
        return ParsedTACInstruction(line_number, raw_line, label, opcode, dest, op1, op2)

    def parse_tac_file(self) -> List[ParsedTACInstruction]:
        """
        Reads the .tac file and parses all lines.
        Returns:
            A list of ParsedTACInstruction objects.
        """
        instructions: List[ParsedTACInstruction] = []
        try:
            self.logger.info(f"TACParser.parse_tac_file: parsing file '{self.tac_filepath}'")
            with open(self.tac_filepath, 'r', encoding='utf-8') as f:
                for i, line_content in enumerate(f):
                    parsed_instruction = self._parse_line(i + 1, line_content)
                    if parsed_instruction:
                        instructions.append(parsed_instruction)
                        self.logger.info(f"TACParser.parse_tac_file: parsed instruction {i + 1}: {parsed_instruction}")
            self.logger.debug(f"Successfully parsed {len(instructions)} TAC instructions from '{self.tac_filepath}'.")
        except FileNotFoundError:
            self.logger.error(f"TAC file not found: '{self.tac_filepath}'")
            print(f"Error: TAC file not found: '{self.tac_filepath}'") # Basic error
            raise FileNotFoundError(f"TAC file not found: '{self.tac_filepath}'")
        except Exception as e:
            self.logger.error(f"Error parsing TAC file '{self.tac_filepath}': {e}")
            print(f"Error: Could not parse TAC file '{self.tac_filepath}': {e}") # Basic error
            raise e
        self.logger.debug(f"TACParser.parse_tac_file: parsed {len(instructions)} instructions from '{self.tac_filepath}'")
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