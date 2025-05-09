# src/jakadac/modules/asm_gen/asm_operand_formatter.py

from typing import Optional, TYPE_CHECKING

# Assuming these modules exist in the same directory
from jakadac.modules.SymTable import SymbolTable, Symbol, EntryType, SymbolNotFoundError
from jakadac.modules.Logger import Logger  # Import the Logger class
from jakadac.modules.asm_gen.tac_instruction import TACOpcode # Import needed at runtime

# Get the shared logger instance
logger = Logger()

# Use TYPE_CHECKING for imports needed only for type hints
if TYPE_CHECKING:
    # from jakadac.modules.asm_gen.tac_instruction import TACOpcode # Keep for hinting if desired, but direct import handles runtime
    pass


class ASMOperandFormatter:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        logger.debug("ASMOperandFormatter initialized.")

    def format_operand(self, tac_operand: Optional[str], context_opcode: Optional['TACOpcode'] = None) -> str:
        """
        Translates a TAC operand string into its 8086 assembly representation.
        Handles immediates, global variables, local variables/params ([bp+/-offset]),
        string labels (OFFSET _S...), and temporary variable names (_t...).

        Args:
            tac_operand: The operand string from TAC (e.g., variable name, literal, _S0, _t1, [bp...]).
            context_opcode: The TACOpcode of the instruction this operand belongs to (optional, for context like WRS).

        Returns:
            The assembly representation of the operand.
        """
        if tac_operand is None:
            logger.error("format_operand called with None operand.")
            return "<ERROR_NONE_OPERAND>"

        operand_str = str(tac_operand).strip()
        logger.debug(f"ASMOperandFormatter: Formatting operand: '{operand_str}' (context: {context_opcode})", stacklevel=2)

        # 1. Check if it's already formatted as [bp+/-offset] (should not happen ideally if TAC is clean)
        if operand_str.startswith(('[bp+', '[bp-')) and operand_str.endswith(']'):
            logger.debug(f"Operand '{operand_str}' is already in [bp+/-offset] format. Returning as is.")
            return operand_str

        # 2. Immediate Check (Integer/Float)
        try:
            # Attempt to convert to float first to handle decimals
            val = float(operand_str)
            # If it converts back to int without loss, treat as int for simplicity in ASM
            if val == int(val):
                int_val = int(val)
                logger.debug(f"Formatted '{operand_str}' as immediate integer: {int_val}")
                return str(int_val)
            else:
                # Handle float representation if needed (e.g., for FPU instructions)
                # For basic 8086, floating point requires dedicated handling or libraries.
                # Defaulting to string representation, may need refinement based on target ASM features.
                logger.warning(f"Operand '{operand_str}' is a non-integer number. Representing as string. Floating point ops require special handling.")
                return operand_str
        except ValueError:
            pass  # Not a number

        # 3. String Label Check (e.g., _S0)
        if operand_str.startswith("_S") and operand_str[2:].isdigit():
            # Context matters: WRS needs OFFSET, assignment might need the label name
            if context_opcode == TACOpcode.WRITE_STR:
                 formatted = f"OFFSET {operand_str}"
                 logger.debug(f"Formatted string label '{operand_str}' as {formatted} for WRS context.")
                 return formatted
            else:
                 logger.debug(f"Formatted string label '{operand_str}' as itself (non-WRS context). Potential address needed.")
                 return operand_str # Return label name; might need OFFSET later depending on usage

        # 4. Temporary Variable Check (e.g., _t1)
        if operand_str.startswith("_t") and operand_str[2:].isdigit():
             logger.debug(f"Operand '{operand_str}' recognized as temporary variable. Assuming it maps to [BP-offset].")
             # **CRITICAL**: Temps NEED lookup to get their BP offset assigned during TAC generation/SymTab phase!
             # Fallback for now: Treat like other identifiers needing lookup.
             pass # Continue to identifier lookup

        # 5. Identifier Lookup (Variable, Parameter, Procedure, Constant)
        try:
            entry = self.symbol_table.lookup(operand_str) # Use simple lookup for now
            logger.debug(f" Found symbol entry for '{operand_str}': {entry}")

            # Handle potential 'c' -> 'cc' MASM keyword conflict
            asm_name = "cc" if entry.name.lower() == "c" else entry.name

            # Global Variable (Depth 0 or 1 in some contexts)
            if entry.depth <= 1 and entry.entry_type in (EntryType.VARIABLE, EntryType.CONSTANT):
                logger.debug(f"Formatted '{operand_str}' as global variable/constant: {asm_name}")
                return asm_name

            # Local Variable or Parameter (Depth > 1)
            elif entry.depth >= 2 and entry.entry_type in (EntryType.VARIABLE, EntryType.PARAMETER):
                if entry.offset is None:
                     logger.error(f"Local/Param operand '{asm_name}' (Depth {entry.depth}) in scope '{entry.scope}' has no offset.")
                     return f"<ERROR_NO_OFFSET_{asm_name}>"

                # **Translate Internal Offset to 8086 Offset**
                internal_offset = entry.offset
                asm_offset_str = "<ERROR_OFFSET_CALC>"

                if entry.entry_type == EntryType.PARAMETER:
                    # Parameters: Positive offset from BP. First param [BP+4].
                    # Assumes internal offset 0 = first param, 2 = second (for WORDs), etc.
                    final_asm_offset = internal_offset + 4 # BP+0=OldBP, BP+2=RetAddr
                    asm_offset_str = f"[bp+{final_asm_offset}]"
                    logger.debug(f"Calculated PARAMETER offset for '{asm_name}' (internal: {internal_offset}) -> {asm_offset_str}")
                else: # VARIABLE (or Temporary treated as variable)
                    # Locals/Temps: Negative offset from BP. First local [BP-2].
                    # Assumes internal offset 0 = first local, 2 = second, etc.
                    final_asm_offset = -(internal_offset + 2)
                    asm_offset_str = f"[bp{final_asm_offset}]"
                    logger.debug(f"Calculated LOCAL/TEMP variable offset for '{asm_name}' (internal: {internal_offset}) -> {asm_offset_str}")

                return asm_offset_str

            # Procedure/Function Name (or other types like TYPE)
            elif entry.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION, EntryType.TYPE):
                logger.debug(f"Formatted '{operand_str}' as procedure/function/type name: {asm_name}")
                return asm_name
            else:
                 logger.warning(f"Symbol '{operand_str}' found but has unexpected type/depth combination: Type={entry.entry_type}, Depth={entry.depth}. Returning name '{asm_name}'.")
                 return asm_name

        except SymbolNotFoundError:
            # 6. Fallback: If not found in symbol table, not immediate, not string label, not temp pattern
            # Treat as potential label, temp, or error.
            logger.debug(f"Operand '{operand_str}' not found in symbol table or matched other patterns. Returning as potential label/temp name.")
            return operand_str
        except Exception as e:
            logger.error(f"Unexpected error formatting operand '{operand_str}': {e}")
            return f"<ERROR_FORMATTING_{operand_str}>"