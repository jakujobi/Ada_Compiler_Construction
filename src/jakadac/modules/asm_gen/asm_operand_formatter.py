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
    def __init__(self, symbol_table: 'SymbolTable', asm_generator_instance: 'ASMGenerator', logger_instance: 'Logger'):
        self.symbol_table = symbol_table
        self.asm_generator = asm_generator_instance # Provides current_procedure_context
        self.logger = logger_instance
        self.logger.debug("ASMOperandFormatter initialized.")

    def format_operand(self, operand_name: str, context_opcode: Optional[TACOpcode] = None, active_procedure_symbol: Optional['Symbol'] = None) -> str:
        """
        Formats a TAC operand (string) into its assembly representation.
        Handles variables (global, local, param), temporaries, integer literals, and string labels.
        `active_procedure_symbol` is crucial for looking up locals/params in the correct scope.
        """
        self.logger.debug(f"ASMOperandFormatter: Formatting operand: '{operand_name}' (context: {context_opcode}, active_proc: {active_procedure_symbol.name if active_procedure_symbol else 'None'})")

        if operand_name is None:
            self.logger.error("format_operand called with None operand_name")
            return "<ERROR_NONE_OPERAND>"

        # Check if it's an integer literal
        try:
            val = int(operand_name)
            return str(val)  # Immediate value
        except ValueError:
            pass # Not an integer, proceed

        # Check if it's a known string literal label (e.g., _S0, _S1)
        if operand_name in self.asm_generator.string_literals_map.values():
            # For NASM, string labels are used directly with OFFSET if they are in .data
            # However, here we just return the label itself as the data segment manager handles OFFSET.
            # If it's a string literal from string_literals_map (which are labels like _S0)
            return f"OFFSET {operand_name}"

        # Check if it's a temporary variable (e.g., _t0, _t1)
        # These are expected to be found in the symbol table with offsets by TACGenerator
        if operand_name.startswith("_t"):
            search_depth = -1 # Default for logging if active_procedure_symbol is None
            try:
                # Temporaries are local to the procedure they were generated in.
                # Their depth in symbol table would match the procedure's body scope depth.
                if active_procedure_symbol:
                    search_depth = active_procedure_symbol.depth + 1
                else:
                    # Fallback, though active_procedure_symbol should ideally always be present for temps
                    search_depth = self.symbol_table.current_depth 
                
                self.logger.debug(f"ASMOperandFormatter: Temp '{operand_name}', active_proc '{active_procedure_symbol.name if active_procedure_symbol else 'None'}', calculated search_depth for temp: {search_depth}.")

                symbol_entry = self.symbol_table.lookup(operand_name, search_from_depth=search_depth)
                
                if symbol_entry.offset is not None:
                    # Correctly format as [BP - offset] or [BP + offset] based on convention
                    # Assuming standard local var (negative) / param (positive) offset from BP
                    if symbol_entry.offset < 0: # Local variable or temp on stack
                        return f"[BP{symbol_entry.offset:+#}]" # e.g., [BP-2], [BP-4]
                    else: # Parameter or other positive offset
                        return f"[BP+{symbol_entry.offset}]" # e.g. [BP+4], [BP+6]
                else: # symbol_entry.offset is None
                    self.logger.error(f"Temporary variable '{operand_name}' found but has no offset.")
                    return f"<ERROR_NO_OFFSET_{operand_name}>"
            except SymbolNotFoundError:
                self.logger.error(f"Temporary variable '{operand_name}' not found in symbol table at depth {search_depth}.")
                return f"<ERROR_TEMP_NOT_FOUND_{operand_name}>"
            except Exception as e:
                self.logger.error(f"Unexpected error formatting temporary '{operand_name}': {e}")
                return f"<ERROR_TEMP_UNEXPECTED_{operand_name}>"

        # 1. Try to find as a variable (local, param, or global)
        # Ensure it's not a special prefix, not a label, and not purely numeric (already handled)
        if not operand_name.startswith(("_", ".")) and not operand_name.isdigit():
            current_search_depth_for_logging = "global/current" 
            try:
                start_search_depth = None
                if active_procedure_symbol:
                    # The procedure's own variables are at its declaration depth + 1
                    # Parameters are at its declaration depth
                    start_search_depth = active_procedure_symbol.depth + 1 # Search locals first
                    current_search_depth_for_logging = f"proc '{active_procedure_symbol.name}' depth {start_search_depth}"
                    self.logger.debug(f"ASMOperandFormatter: Var '{operand_name}', active_proc '{active_procedure_symbol.name}' (depth {active_procedure_symbol.depth}), searching from depth {start_search_depth}.")
                else:
                    self.logger.debug(f"ASMOperandFormatter: Var '{operand_name}', no active_procedure_symbol, search_from_depth=None (use symtab current/global).")

                # Lookup logic revised
                symbol_entry = self.symbol_table.lookup(operand_name, search_from_depth=start_search_depth)
                current_search_depth_for_logging = f"depth {symbol_entry.depth}" # Update with actual found depth

                # For CALL, the operand_name is the procedure label, not a variable to be looked up for memory access.
                if context_opcode == TACOpcode.CALL and (symbol_entry.entry_type == EntryType.PROCEDURE or symbol_entry.entry_type == EntryType.FUNCTION):
                    return symbol_entry.name # Procedure/Function labels are used directly

                if symbol_entry.entry_type == EntryType.CONSTANT:
                    if symbol_entry.value is not None:
                        return str(symbol_entry.value) # Use the constant's value directly
                    else: # Constant with no value (should not happen for resolved constants)
                        self.logger.error(f"Constant symbol '{operand_name}' found but has no value.")
                        return f"<ERROR_CONST_NO_VALUE_{operand_name}>"

                # Handle variables (global, local, param)
                if symbol_entry.offset is not None:
                    # Global variables (depth 0 or 1, check specific project convention)
                    # Using a simplified check for globals: depth 1 or specific list
                    is_global_via_map = self.asm_generator.program_global_vars and operand_name in self.asm_generator.program_global_vars
                    if symbol_entry.depth <= 1 or is_global_via_map: # Adjust depth for globals if needed (0 for builtins, 1 for program globals)
                         # Check if it's a global var explicitly tracked in ASMGenerator
                        if is_global_via_map or (not active_procedure_symbol and symbol_entry.depth <=1 ): # Crude check, refine if SymbolTable has better global distinction
                            return f"{operand_name}" # Global variable, use its name as label
                    
                    # Locals and Parameters (relative to BP)
                    if symbol_entry.offset < 0: # Local variable
                        return f"[BP{symbol_entry.offset:+#}]"
                    else: # Parameter (positive offset)
                        return f"[BP+{symbol_entry.offset}]"
                else: # Has no offset (and not a handled constant/procedure)
                    self.logger.error(f"Symbol '{operand_name}' (type: {symbol_entry.entry_type}) found but has no offset and is not a global label or handled constant.")
                    return f"<ERROR_NO_ADDR_OR_VAL_{operand_name}>"

            except SymbolNotFoundError:
                self.logger.error(f"Symbol '{operand_name}' not found in symbol table (searched from {current_search_depth_for_logging}). Context: {context_opcode}")
                return f"<ERROR_SYMBOL_NOT_FOUND_{operand_name}>"
            except Exception as e:
                self.logger.error(f"Unexpected error formatting variable/symbol '{operand_name}': {e}")
                return f"<ERROR_UNEXPECTED_FORMAT_{operand_name}>"

        # 2. Handle integer literals
        # ... existing code ...

        # ... rest of the method ...