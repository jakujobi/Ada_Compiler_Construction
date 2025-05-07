"""
Defines the structure for representing a parsed Three-Address Code (TAC) instruction,
including an enumeration for TAC opcodes.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Union

# (Potentially) from ..Logger import logger # If logging is needed here

class TACOpcode(Enum):
    # Data Movement / Assignment
    ASSIGN = "="          # result = arg1 (e.g., x = y, x = 5)
    # Binary Arithmetic Operations
    ADD = "+"           # result = arg1 + arg2
    SUB = "-"           # result = arg1 - arg2
    MUL = "*"           # result = arg1 * arg2
    DIV = "/"           # result = arg1 / arg2
    MOD = "mod"         # result = arg1 mod arg2
    REM = "rem"         # result = arg1 rem arg2 (if different from mod)

    # Unary Operations
    UMINUS = "uminus"   # result = -arg1 (e.g., x = -y)
    NOT_OP = "not"      # result = not arg1 (logical not)
    # (Add other unary ops like NOT if needed)

    # Array Operations
    ARRAY_ASSIGN_FROM = "array_assign_from" # e.g. x = a[i]
    ARRAY_ASSIGN_TO = "array_assign_to"     # e.g. a[i] = x

    # Control Flow - Unconditional
    GOTO = "goto"       # goto label
    LABEL = "label"     # L1: (represented by defining a label)

    # Control Flow - Conditional Jumps (evaluate condition then jump)
    # These usually take the form: if arg1 op arg2 goto label
    # For simplicity, we can have specific opcodes or a generic 'IF_GOTO'
    # For example:
    IF_FALSE_GOTO = "if_false_goto" # if_false_goto label, condition_var
    IF_EQ_GOTO = "if_eq_goto"     # if arg1 == arg2 goto label
    IF_NE_GOTO = "if_ne_goto"     # if arg1 != arg2 goto label
    IF_LT_GOTO = "if_lt_goto"     # if arg1 <  arg2 goto label
    IF_LE_GOTO = "if_le_goto"     # if arg1 <= arg2 goto label
    IF_GT_GOTO = "if_gt_goto"     # if arg1 >  arg2 goto label
    IF_GE_GOTO = "if_ge_goto"     # if arg1 >= arg2 goto label
    # A more generic form could be:
    # IF_COND_GOTO = "if_cond_goto" # result (label), arg1, arg2, condition_op

    # Procedure Call Mechanism
    PUSH = "push"       # push param_value_or_addr
    PARAM = "param"     # define a parameter (distinct from push for call arguments)
    CALL = "call"       # call proc_name, num_params (optional: num_params for stack cleanup)
    RETURN = "return"   # return [value]
    RETRIEVE = "retrieve" # result = retrieve (for function return values)

    # Procedure Definition
    PROC_BEGIN = "proc"   # proc proc_name [size_locals] [size_params]
    PROC_END = "endp"     # endp proc_name

    # Input/Output (from A8 requirements)
    READ_INT = "rdi"      # rdi dest_var
    WRITE_INT = "wri"     # wri source_var_or_literal
    WRITE_STR = "wrs"     # wrs string_label
    WRITE_NEWLINE = "wrln"# wrln

    # Special / Meta Instructions
    PROGRAM_START = "START PROC" # Indicates the main entry point
    STRING_DEF = ":ASCIZ" # For lines like _S0: .ASCIZ "Hello"
    # Other meta-instructions as needed, e.g., for comments, data declarations.
    COMMENT = "#" # If comments are preserved as TAC instructions

    # Catch-all for unrecognized or unhandled TAC lines
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, s: str) -> 'TACOpcode':
        """Converts a string operation to a TACOpcode enum member."""
        # First, try a direct case-sensitive match.
        # This is important for symbols like '=', '+', and specific values like "START PROC", ":ASCIZ".
        for member in cls:
            if member.value == s:
                return member

        # If no direct match, try a case-insensitive match for potentially word-based opcodes.
        # This allows flexibility if the TAC file uses, e.g., "PROC" instead of "proc".
        # We assume that enum values for such opcodes are stored in lowercase.
        s_lower = s.lower()
        for member in cls:
            # Apply lowercasing comparison primarily to enum members whose values are already all lowercase.
            # This avoids issues if an enum value itself is meant to be mixed-case and not matched insensitively.
            if member.value.islower() and member.value == s_lower:
                return member

        # logger.warning(f"Unknown TAC opcode string: '{s}'. Mapping to UNKNOWN.")
        return cls.UNKNOWN

@dataclass
class TACOperand:
    """Represents an operand in a TAC instruction."""
    value: Union[str, int, float]  # Can be a variable name, temp name, literal, label
    is_address_of: bool = False    # True if this operand represents an address (e.g. @var for push)
    # Optional: Add type information if known/needed during ASM generation
    # var_type: Optional[Any] = None # E.g. 'integer', 'float', 'address'

    def __str__(self):
        prefix = "@" if self.is_address_of else ""
        return f"{prefix}{self.value}"

@dataclass
class ParsedTACInstruction:
    """
    Represents a single parsed TAC instruction with its components.
    The 'line_number' is the original line number from the .tac file for reference/debugging.
    The 'raw_line' is the original string from the .tac file.
    'label' is any label defined on this line (e.g., L1: ...).
    'opcode' is the operation (e.g., ADD, ASSIGN, GOTO).
    'destination', 'operand1', 'operand2' are the arguments for the opcode.
    Their meaning depends on the opcode.
    """
    line_number: int
    raw_line: str
    label: Optional[str] = None
    opcode: Union[TACOpcode, str] = TACOpcode.UNKNOWN
    destination: Optional[TACOperand] = None  # Also used for jump targets in IF_GOTO
    operand1: Optional[TACOperand] = None
    operand2: Optional[TACOperand] = None
    # For CALL, could store num_params if available
    # For PROC_BEGIN, could store size_locals, size_params

    def __str__(self) -> str:
        """Returns a string representation of the TAC instruction."""
        parts = []
        if self.label:
            parts.append(f"{self.label}:")

        # Handle opcode representation carefully
        opcode_str = ""
        if isinstance(self.opcode, TACOpcode):
            opcode_str = self.opcode.name # Or self.opcode.value if preferred for output
        elif isinstance(self.opcode, str):
            opcode_str = self.opcode # Use the string directly if it's not an enum
        else:
            opcode_str = "[unknown_opcode_type]"
        parts.append(opcode_str)

        # Append operands if they exist
        if self.destination:
            parts.append(str(self.destination))
        if self.operand1:
            parts.append(str(self.operand1))
        if self.operand2:
            parts.append(str(self.operand2))
            
        return f"TACLine({self.line_number}: {self.raw_line.strip()} | Parsed: {' '.join(parts)})"