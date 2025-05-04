#!/usr/bin/env python3
# __init__.py for asm_gen package
"""
Assembly Generator package for the Ada Compiler.
Contains modules for TAC to ASM conversion.
"""

# Import and expose main classes for easier import by users of this package
from .tac_instruction import TACInstruction
from .data_segment_manager import DataSegmentManager
from .asm_operand_formatter import ASMOperandFormatter
from .asm_instruction_mapper import ASMInstructionMapper
from .asm_generator import ASMGenerator

__all__ = [
    'TACInstruction',
    'DataSegmentManager',
    'ASMOperandFormatter',
    'ASMInstructionMapper',
    'ASMGenerator'
] 