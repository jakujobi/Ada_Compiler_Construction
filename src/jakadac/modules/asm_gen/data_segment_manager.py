# src/jakadac/modules/asm_gen/data_segment_manager.py

from ..SymTable import SymbolTable, EntryType
from ..Logger import logger

class DataSegmentManager:
    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.global_vars = {}  # Stores unique global variable names and their ASM type (e.g., "DW ?")
        self.string_literals = {}  # Stores string labels and their raw string values

    def collect_definitions(self):
        """
        Scans the symbol table for global variables (depth 1) and string literals.
        Populates self.global_vars and self.string_literals.
        Handles mangling for 'c' -> 'cc' if specified by conventions.
        """
        logger.debug("DataSegmentManager: Collecting definitions from symbol table.")
        for name, symbol_entry in self.symbol_table.table.items():
            if symbol_entry.depth == 1 and symbol_entry.entry_type == EntryType.VARIABLE:
                # TODO: Implement name mangling if needed (e.g. 'c' -> 'cc') based on project conventions
                # For now, using direct name usage for globals.
                mangled_name = name 
                self.global_vars[mangled_name] = "DW ?" # Default to Define Word, uninitialized
                logger.debug(f"Collected global variable: {mangled_name} {self.global_vars[mangled_name]}")
            elif symbol_entry.entry_type == EntryType.CONSTANT and isinstance(symbol_entry.const_value, str) and name.startswith("_S"):
                self.string_literals[name] = symbol_entry.const_value
                logger.debug(f"Collected string literal: {name} -> \"{symbol_entry.const_value}\"")

    def get_data_section_asm(self) -> str:
        """
        Generates the .DATA section assembly code as a single string.
        Sorts definitions for consistent output.
        String literals are terminated with '$' as per io.asm conventions.
        Example:
            .DATA
            VarName DW ?
            _SLabel DB "Value$",'$'
        """
        asm_lines = [".DATA"] # Start with the .DATA directive
        
        # Sort global vars for consistent output
        for var_name in sorted(self.global_vars.keys()):
            asm_lines.append(f"    {var_name} {self.global_vars[var_name]}")
            
        # Sort string literals for consistent output
        for str_label in sorted(self.string_literals.keys()):
            raw_string = self.string_literals[str_label]

            asm_lines.append(f"    {str_label} DB \"{raw_string}\", '$'")
            
        if not self.global_vars and not self.string_literals:
            asm_lines.append("    ; No global variables or string literals defined in the .DATA section.")
            
        return "\n".join(asm_lines)