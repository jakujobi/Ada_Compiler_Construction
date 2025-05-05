#!/usr/bin/env python3
# data_segment_manager.py
# Author: AI Assistant
# Date: 2024-05-08
# Version: 1.0
"""
Data Segment Manager for ASM Generation.
Handles identification of global variables and string literals for the .data section.
"""

from typing import Dict, List, Set
import logging

# Import EntryType directly from SymTable
from ..SymTable import EntryType

# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if run standalone or not configured elsewhere
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataSegmentManager:
    """
    Manages the .data section of the generated ASM file.
    Identifies global variables from SymbolTable and formats string literals.
    """
    
    def __init__(self, symbol_table):
        """
        Initialize with a SymbolTable instance.
        
        Args:
            symbol_table: The populated SymbolTable containing symbol information
        """
        self.symbol_table = symbol_table
        self.global_vars = set()  # Will store unique lexemes of depth 0 variables
        
    def collect_definitions(self):
        """
        Iterate through the global scope (depth 0) of the symbol table.
        Identify variables to include in the .data section.
        """
        try:
            logger.info("Starting collection of global definitions for .data section")
            # Attempt to get the global scope (depth 0)
            try:
                global_scope = self.symbol_table.get_symbols_at_depth(0)
            except IndexError as e:
                logger.error(f"Error collecting global definitions: {e}")
                global_scope = {} # Fallback to empty scope
            except AttributeError as e:
                logger.error(f"Error collecting global definitions: {e}")
                global_scope = {} # Fallback to empty scope

            # Iterate through symbols in the retrieved global scope
            for symbol_name, symbol in global_scope.items():
                # Check if the symbol is a VARIABLE
                if symbol.entry_type == EntryType.VARIABLE:
                    # Add the variable name to our set (handles potential C -> CC rename)
                    self.global_vars.add(symbol.name)
                    logger.debug(f"Added global variable: {symbol.name}")
                    
            logger.info(f"Collected {len(self.global_vars)} global variables")
            
        except Exception as e:
            logger.error(f"Error collecting global definitions: {e}")
            raise
    
    def get_data_section_asm(self, string_literals: Dict[str, str]) -> List[str]:
        """
        Generate the .data section assembly code.
        
        Args:
            string_literals: Dictionary mapping string labels to their values
                             (from TACGenerator.get_string_literals())
        
        Returns:
            List of assembly lines for the .data section
        """
        asm_lines = ["section .data"]
        
        # Add string literals
        if string_literals:
            asm_lines.append("; --- String Literals ---")
            for label, value in sorted(string_literals.items()):
                # Format: _S0      db      "Hello$"
                # Note: value should already include the terminating $ from TACGenerator
                asm_lines.append(f"{label:<8} db      \"{value}\"")
        
        # Add global variables
        if self.global_vars:
            asm_lines.append("; --- Global Variables ---")
            for var_name in sorted(list(self.global_vars)):
                # For now, assume all variables are integers (dw)
                asm_lines.append(f"{var_name:<8} dw      ?")
        
        # If no strings or globals, ensure section directive still exists
        if len(asm_lines) == 1:
            asm_lines.append("; No global variables or string literals")
            
        return asm_lines 