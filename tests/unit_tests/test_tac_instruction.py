import unittest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Optional, List

# --- Adjust path to import modules from src ---
repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

# Modules to test/mock
from jakadac.modules.asm_gen.tac_instruction import TACOpcode, TACOperand, ParsedTACInstruction

class TestTACOpcode(unittest.TestCase):
    def test_from_string_valid(self):
        self.assertEqual(TACOpcode.from_string('='), TACOpcode.ASSIGN)
        self.assertEqual(TACOpcode.from_string('+'), TACOpcode.ADD)
        self.assertEqual(TACOpcode.from_string('goto'), TACOpcode.GOTO)
        self.assertEqual(TACOpcode.from_string('GOTO'), TACOpcode.GOTO)
        self.assertEqual(TACOpcode.from_string('proc'), TACOpcode.PROC_BEGIN)
        self.assertEqual(TACOpcode.from_string('rdi'), TACOpcode.READ_INT)
        self.assertEqual(TACOpcode.from_string(':ASCIZ'), TACOpcode.STRING_DEF)

    def test_from_string_direct_mappings(self):
        """Tests direct opcode string values (typically symbols or specific keywords)."""
        self.assertEqual(TACOpcode.from_string('-'), TACOpcode.SUB)
        self.assertEqual(TACOpcode.from_string('*'), TACOpcode.MUL)
        self.assertEqual(TACOpcode.from_string('/'), TACOpcode.DIV)
        self.assertEqual(TACOpcode.from_string('mod'), TACOpcode.MOD)
        self.assertEqual(TACOpcode.from_string('rem'), TACOpcode.REM)
        self.assertEqual(TACOpcode.from_string('uminus'), TACOpcode.UMINUS)
        self.assertEqual(TACOpcode.from_string('if_eq'), TACOpcode.IF_EQ) 
        # Add more direct mappings that represent actual values in TAC files.

    def test_from_string_invalid(self):
        self.assertEqual(TACOpcode.from_string('invalid_op'), TACOpcode.UNKNOWN)
        self.assertEqual(TACOpcode.from_string(''), TACOpcode.UNKNOWN)

class TestTACOperand(unittest.TestCase):
    def test_str_representation(self):
        self.assertEqual(str(TACOperand("varX")), "varX")
        self.assertEqual(str(TACOperand(123)), "123")
        self.assertEqual(str(TACOperand(45.67)), "45.67")
        self.assertEqual(str(TACOperand("varY", is_address_of=True)), "@varY")
        self.assertEqual(str(TACOperand(100, is_address_of=True)), "@100")

class TestParsedTACInstruction(unittest.TestCase):
    def test_str_representation_full(self):
        op_dest = TACOperand("_t0")
        op_1 = TACOperand("A")
        op_2 = TACOperand(5)
        instr = ParsedTACInstruction(
            line_number=10,
            raw_line="L1: _t0 = A + 5\n",
            label="L1",
            opcode=TACOpcode.ADD,
            destination=op_dest,
            operand1=op_1,
            operand2=op_2
        )
        expected_str = "TACLine(10: L1: _t0 = A + 5 | Parsed: L1: ADD _t0 A 5)"
        self.assertEqual(str(instr), expected_str)

    def test_str_representation_no_label_one_operand(self):
        op_1 = TACOperand("myVar")
        instr = ParsedTACInstruction(
            line_number=5,
            raw_line="push myVar\n",
            opcode=TACOpcode.PUSH,
            operand1=op_1
        )
        expected_str = "TACLine(5: push myVar | Parsed: PUSH myVar)"
        self.assertEqual(str(instr), expected_str)

    def test_str_representation_no_operands(self):
        instr = ParsedTACInstruction(
            line_number=20,
            raw_line="wrln\n",
            opcode=TACOpcode.WRITE_NEWLINE
        )
        expected_str = "TACLine(20: wrln | Parsed: WRITE_NEWLINE)"
        self.assertEqual(str(instr), expected_str)

    def test_str_representation_only_label(self):
        instr = ParsedTACInstruction(
            line_number=15,
            raw_line="LOOP_START:\n",
            label="LOOP_START",
            opcode=TACOpcode.LABEL # Assuming LABEL is an opcode for lines with only labels
        )
        expected_str = "TACLine(15: LOOP_START: | Parsed: LOOP_START: LABEL)"
        self.assertEqual(str(instr), expected_str)

if __name__ == '__main__':
    unittest.main()
