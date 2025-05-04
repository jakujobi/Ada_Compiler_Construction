#!/usr/bin/env python3
# asm_operand_formatter.py
# Author: AI Assistant
# Date: 2024-05-08
# Version: 1.0
"""
ASM Operand Formatter for ASM Generation.
Converts TAC operands into their 8086 assembly representation.
"""

from typing import Dict, Optional
import re
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if run standalone or not configured elsewhere
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ASMOperandFormatter:
    """
    Formats TAC operands for ASM generation.
    Converts operands like '_BP-2', '_t1', '_S0', etc. to their ASM representation.
    """
    
    def __init__(self, temp_offsets: Dict[str, Dict[str, int]]):
        """
        Initialize with a mapping of temporary variable offsets.
        
        Args:
            temp_offsets: Dictionary mapping procedure names to dictionaries 
                          that map temp names to BP-relative offsets
        """
        self.temp_offsets = temp_offsets
        self.current_proc = None  # Current procedure context
        
    def set_current_procedure(self, proc_name: Optional[str]):
        """
        Set the current procedure context for temporary variable resolution.
        
        Args:
            proc_name: Name of the current procedure or None to clear
        """
        self.current_proc = proc_name
        
    def format_operand(self, tac_operand: Optional[str]) -> str:
        """
        Convert a TAC operand to its ASM representation.
        
        Args:
            tac_operand: TAC operand string from getPlace or a literal
            
        Returns:
            The formatted ASM operand string
            
        Raises:
            ValueError: If the operand cannot be formatted or temp not found
        """
        if tac_operand is None or tac_operand == "":
            return ""
            
        # Convert to string to handle numeric types
        tac_operand = str(tac_operand)
        
        # Try to parse as an integer (immediate value)
        if re.match(r'^-?\d+$', tac_operand):
            return tac_operand
            
        # Handle BP-relative addresses (_BP+N or _BP-N)
        bp_plus_match = re.match(r'^_BP\+(\d+)$', tac_operand)
        bp_minus_match = re.match(r'^_BP-(\d+)$', tac_operand)
        
        if bp_plus_match:
            offset = bp_plus_match.group(1)
            return f"[bp+{offset}]"
            
        if bp_minus_match:
            offset = bp_minus_match.group(1)
            return f"[bp-{offset}]"
            
        # Handle string labels (_S0, _S1, etc.)
        if tac_operand.startswith('_S'):
            return tac_operand
            
        # Handle temporary variables (_t1, _t2, etc.)
        if tac_operand.startswith('_t'):
            if not self.current_proc:
                raise ValueError(f"No current procedure context for temp variable {tac_operand}")
                
            if self.current_proc not in self.temp_offsets:
                raise ValueError(f"No temp offset map for procedure {self.current_proc}")
                
            if tac_operand not in self.temp_offsets[self.current_proc]:
                raise ValueError(f"Temp variable '{tac_operand}' not found in allocation map for procedure '{self.current_proc}'")
                
            offset = self.temp_offsets[self.current_proc][tac_operand]
            return f"[bp{offset}]"  # offset should already include the sign
            
        # If none of the above, assume it's a global variable or identifier
        # Return as is (any C->CC renaming should have been done when generating TAC)
        return tac_operand 