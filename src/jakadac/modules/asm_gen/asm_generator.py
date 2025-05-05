#!/usr/bin/env python3
# asm_generator.py
# Author: AI Assistant
# Date: 2024-05-08
# Version: 1.0
"""
ASM Generator for Ada Compiler.
Orchestrates the assembly code generation process.
"""

from typing import List, Dict, Tuple, Optional, Set, Any
import os
import re
import logging

# Import local modules
try:
    from .tac_instruction import TACInstruction
    from .data_segment_manager import DataSegmentManager
    from .asm_operand_formatter import ASMOperandFormatter
    from .asm_instruction_mapper import ASMInstructionMapper
except ImportError:
    # Fallback for direct imports if relative imports fail
    from tac_instruction import TACInstruction
    from data_segment_manager import DataSegmentManager
    from asm_operand_formatter import ASMOperandFormatter
    from asm_instruction_mapper import ASMInstructionMapper

# Configure logger for this module
logger = logging.getLogger(__name__)
# Basic configuration if run standalone or not configured elsewhere
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ASMGenerator:
    """
    Main ASM generator class that coordinates the assembly generation process.
    Takes TAC instructions, string literals, and symbol table as input.
    Produces ASM output file.
    """
    
    def __init__(self, tac_instructions: List[Any], string_literals: Dict[str, str], 
                 symbol_table, asm_filepath: str):
        """
        Initialize the ASM generator.
        
        Args:
            tac_instructions: List of TAC instruction tuples from TACGenerator
            string_literals: Dictionary mapping string labels to values
            symbol_table: SymbolTable instance with all symbols
            asm_filepath: Path to output the ASM file
        """
        self.tac_instructions = tac_instructions
        self.string_literals = string_literals
        self.symbol_table = symbol_table
        self.asm_filepath = asm_filepath
        
        # Components to be initialized during generation
        self.data_manager = None
        self.formatter = None
        self.mapper = None
        
        # Variables to track during generation
        self.start_proc_name = None
        self.temp_allocations = {}  # proc_name -> {temp_name -> offset}
        
        # Error tracking
        self.error_count = 0
        self.has_critical_errors = False
        
        logger.info(f"ASM Generator initialized with {len(tac_instructions)} TAC instructions")
        logger.info(f"ASM output will be written to: {asm_filepath}")
    
    def _allocate_temporaries(self):
        """
        Analyze TAC to identify all temporary variables used in each procedure.
        Allocate stack space for them and update local_size in symbol table.
        """
        current_proc = None
        proc_temps = {}  # proc_name -> set of temp vars
        
        logger.info("Analyzing TAC for temporary variable allocation")
        
        # Pass 1: Identify all temps used in each procedure
        for tac_tuple in self.tac_instructions:
            instr = TACInstruction.from_tuple(tac_tuple)
            
            # Track current procedure
            if instr.opcode.lower() == 'proc':
                current_proc = instr.op1
                proc_temps[current_proc] = set()
                logger.debug(f"Scanning procedure: {current_proc}")
            elif instr.opcode.lower() == 'endp':
                current_proc = None
                
            # Skip if not in a procedure
            if not current_proc:
                continue
                
            # Check for temporary variables in all operands
            for operand in (instr.dest, instr.op1, instr.op2):
                if operand and isinstance(operand, str) and operand.startswith('_t'):
                    proc_temps[current_proc].add(operand)
                    logger.debug(f"Found temp {operand} in {current_proc}")
        
        # Log all procedure names for which we need to allocate temporaries
        logger.debug(f"Procedures needing temp allocation: {list(proc_temps.keys())}")
        
        # Pass 2: Allocate offsets for temps and update symbol table
        for proc_name, temps in proc_temps.items():
            try:
                # Get procedure symbol
                logger.debug(f"Attempting to look up symbol for procedure '{proc_name}' for temp allocation.")
                
                # Log current scope depths in symbol table
                logger.debug(f"Current symbol table depth: {self.symbol_table.current_depth}")
                
                # Try to find the procedure in any accessible scope
                proc_symbol = self.symbol_table.lookup(proc_name)
                
                # Calculate additional space needed for temps (2 bytes per temp for Integer)
                temp_space = len(temps) * 2
                
                # Update local_size to include space for temps
                current_local_size = proc_symbol.local_size
                proc_symbol.local_size = current_local_size + temp_space
                
                logger.info(f"Procedure {proc_name}: {len(temps)} temps, added {temp_space} bytes, "
                           f"total locals now {proc_symbol.local_size}")
                
                # Allocate specific offsets for each temp
                # Start after declared locals
                base_offset = -(current_local_size + 2)  # Start at first temp position
                
                # Create dict for this procedure's temps
                self.temp_allocations[proc_name] = {}
                
                # Assign offsets to each temp
                for i, temp in enumerate(sorted(temps)):  # Sort for consistent allocation
                    offset = base_offset - (i * 2)  # Each temp is 2 bytes
                    self.temp_allocations[proc_name][temp] = offset
                    logger.debug(f"Allocated {temp} at [bp{offset}] in {proc_name}")
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error allocating temps for {proc_name}: {e}")
                # Set critical error flag if this is a procedure symbol not found error
                if "Symbol '" in str(e) and "not found" in str(e):
                    self.has_critical_errors = True
                # Continue with other procedures rather than aborting entirely
    
    def generate_asm(self):
        """
        Generate the complete ASM file.
        Performs multi-pass processing:
        1. Allocate temporaries
        2. Generate data segment
        3. Generate code segment
        4. Write final file
        
        Returns:
            bool: True if ASM generation was successful, False if critical errors were encountered
        """
        try:
            # Pass 1: Allocate temporaries
            self._allocate_temporaries()
            
            # Exit early if critical errors detected in temporary allocation
            if self.has_critical_errors:
                logger.error("Critical errors encountered during temporary allocation. ASM generation may be incomplete.")
                return False
            
            # Initialize components
            self.data_manager = DataSegmentManager(self.symbol_table)
            try:
                self.data_manager.collect_definitions()
            except Exception as e:
                self.error_count += 1
                logger.error(f"Error in data segment collection: {e}")
                self.has_critical_errors = True
                return False
            
            self.formatter = ASMOperandFormatter(self.temp_allocations)
            self.mapper = ASMInstructionMapper(self.formatter, self.symbol_table)
            
            # Pass 2: Generate data segment
            data_lines = self.data_manager.get_data_section_asm(self.string_literals)
            
            # Pass 3: Generate code segment
            code_lines = []
            current_proc_symbol = None
            
            # Process each TAC instruction
            for tac_tuple in self.tac_instructions:
                instr = TACInstruction.from_tuple(tac_tuple)
                
                # Track current procedure
                if instr.opcode.lower() == 'proc':
                    try:
                        current_proc_symbol = self.symbol_table.lookup(instr.op1)
                        self.formatter.set_current_procedure(instr.op1)
                    except Exception as e:
                        self.error_count += 1
                        logger.error(f"Error retrieving symbol for procedure {instr.op1}: {e}")
                        # This is a critical error - can't proceed correctly without procedure symbol
                        if "not found" in str(e):
                            self.has_critical_errors = True
                        
                elif instr.opcode.lower() == 'endp':
                    current_proc_symbol = None
                    self.formatter.set_current_procedure(None)
                    
                elif instr.opcode.lower() == 'start_proc':
                    self.start_proc_name = instr.op1
                    logger.info(f"Main entry procedure: {self.start_proc_name}")
                    continue  # Skip translation for START PROC
                
                # Translate the instruction to ASM
                try:
                    asm_snippet = self.mapper.translate(instr, current_proc_symbol)
                    code_lines.extend(asm_snippet)
                except Exception as e:
                    self.error_count += 1
                    error_comment = f"; -- ERROR translating {instr.original_tuple}: {e} --"
                    logger.error(f"Error translating instruction {instr.original_tuple}: {e}")
                    code_lines.append(error_comment)
            
            # Generate main entry point
            main_lines = self._generate_main_entry()
            
            # Assemble final ASM file
            asm_lines = [
                "; Generated by JakAdaC 8086 Compiler",
                "; Assignment 8 - TAC to ASM Code Generator",
                "",
                "%include \"io.asm\"",
                "",
                "section .text",
                "global _start",
                ""
            ]
            
            # Add data segment
            asm_lines.extend(data_lines)
            asm_lines.append("")
            
            # Add code segment
            asm_lines.extend(code_lines)
            asm_lines.append("")
            
            # Add main entry
            asm_lines.extend(main_lines)
            
            # Write to file
            with open(self.asm_filepath, 'w') as f:
                for line in asm_lines:
                    f.write(line + '\n')
                    
            logger.info(f"ASM generation complete. Written to {self.asm_filepath}")
            logger.info(f"ASM file contains {len(asm_lines)} lines")
            
            # Return success only if no critical errors were encountered
            return not self.has_critical_errors
            
        except Exception as e:
            self.error_count += 1
            self.has_critical_errors = True
            logger.error(f"Error during ASM generation: {e}")
            raise
    
    def _generate_main_entry(self) -> List[str]:
        """
        Generate the main entry point code.
        
        Returns:
            List of ASM lines for the main entry
        """
        if not self.start_proc_name:
            logger.warning("No start procedure found, using 'main' as default")
            self.start_proc_name = "main"
            
        return [
            "_start:",
            f" call {self.start_proc_name}",
            " mov eax, 1    ; Exit syscall number",
            " xor ebx, ebx  ; Exit code 0",
            " int 0x80      ; Call kernel"
        ] 