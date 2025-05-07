# src/jakadac/modules/asm_gen/asm_operand_formatter.py

from ..SymTable import SymbolTable, EntryType
from ..Logger import logger

class ASMOperandFormatter:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table

    def format_operand(self, operand_value: str, context_opcode: str = None) -> str:
        """
        Formats a TAC operand value into its ASM representation.
        For Phase 2:
            - Handles immediate values (numeric literals).
            - Handles global variables (depth 1 from SymbolTable).
            - Handles string literal labels (e.g., _S0) by prefixing with OFFSET for relevant opcodes.
            - TODO: Implement name mangling for globals if needed (e.g., 'c' -> 'cc').
        """
        logger.debug(f"ASMOperandFormatter: Formatting operand: '{operand_value}' (context: {context_opcode})")

        # Try to interpret as an integer immediate
        try:
            int_val = int(operand_value)
            logger.debug(f"Formatted '{operand_value}' as immediate: {int_val}")
            return str(int_val)
        except ValueError:
            pass # Not an integer immediate

        # Check if it's a known symbol
        symbol_entry = self.symbol_table.lookup_any_depth(operand_value)

        if symbol_entry:
            if symbol_entry.depth == 1 and symbol_entry.entry_type == EntryType.VARIABLE:
                # TODO: Implement name mangling if needed (e.g., 'c' -> 'cc')
                asm_name = operand_value 
                logger.debug(f"Formatted '{operand_value}' as global variable: {asm_name}")
                return asm_name
            elif symbol_entry.entry_type == EntryType.CONSTANT and operand_value.startswith("_S"):
                # For string labels like _S0, _S1, etc.
                # If context requires an address (like WRS), use OFFSET
                # This check might be better placed in the instruction mapper based on opcode context
                if context_opcode and context_opcode.upper() in ["WRS"]:
                    logger.debug(f"Formatted string label '{operand_value}' as OFFSET {operand_value}")
                    return f"OFFSET {operand_value}"
                else:
                    # Other contexts might just use the label directly if ever needed, though unlikely
                    logger.debug(f"Formatted string label '{operand_value}' as {operand_value}")
                    return operand_value
            # Future: Handle parameters ([BP+offset]), locals ([BP-offset]), temps

        # If not an immediate or a known symbol, it might be a temporary variable or a label for jumps/calls.
        # For Phase 2, direct usage of such names is fine as placeholders.
        if operand_value.startswith("_t") or (symbol_entry is None and operand_value.isidentifier()):
            logger.debug(f"Operand '{operand_value}' treated as a non-immediate identifier (temp, local, label). Returning as is.")
            return operand_value

        logger.warning(f"Could not definitively format operand: '{operand_value}'. Returning as is. This may indicate an unhandled case or an error.")
        return operand_value # Fallback: treat as a direct string, could be a procedure name or label