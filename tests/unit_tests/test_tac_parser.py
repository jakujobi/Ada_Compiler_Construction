# tests/unit_tests/test_tac_parser.py
import unittest
import os
from jakadac.modules.asm_gen.tac_parser import TACParser
from jakadac.modules.asm_gen.tac_instruction import TACOpcode, TACOperand, ParsedTACInstruction

class TestTACParser(unittest.TestCase):
    def setUp(self):
        """Create a temporary TAC file for testing."""
        self.temp_tac_file = "temp_test_file.tac"
        tac_content = (
            "# This is a comment\n"
            "\n"
            "_S0: .ASCIZ \"Hello, World!\"\n"
            "_S1: .ASCIZ 'Another string'\n"
            "START_PROC: \n"
            "    proc MAIN_PROC\n"
            "    _t0 = 5                   # Assign literal\n"
            "    _t1 = A                   # Assign variable\n"
            "    _t2 = _t0 + _t1           # Binary operation\n"
            "    _t3 = _t0 + 10            # Binary op with literal\n"
            "    RESULT = _t2 * B\n"
            "    X = uminus Y              # Unary operation\n"
            "    rdi INPUT_VAR             # Read integer\n"
            "    wri OUTPUT_VAR            # Write integer\n"
            "    wrs _S0                   # Write string label\n"
            "    push @SOME_VAR            # Push address\n"
            "    push 123                  # Push literal\n"
            "    push TEMP_VAL             # Push variable\n"
            "    call MY_FUNC, 2           # Call procedure with param count\n"
            "    call ANOTHER_FUNC         # Call procedure without param count (assuming parser handles)\n"
            "    GOTO END_LABEL            # Unconditional jump\n"
            "    IF_EQ _t1, 0, ELSE_LABEL  # Conditional jump (simulated structure)\n"
            "    _t4 = retrieve            # Retrieve function result\n"
            "    return                    # Return without value\n"
            "    return _t4                # Return with value\n"
            "ELSE_LABEL:                 # A label\n"
            "    wrln                      # Write newline\n"
            "END_LABEL:                  # Another label\n"
            "    endp MAIN_PROC\n"
            "START PROC MAIN_PROC        # Main program start indicator\n"
        )
        with open(self.temp_tac_file, "w") as f:
            f.write(tac_content)
        self.parser = TACParser(self.temp_tac_file)

    def tearDown(self):
        """Remove the temporary TAC file."""
        if os.path.exists(self.temp_tac_file):
            os.remove(self.temp_tac_file)

    def test_parse_tac_file(self):
        instructions = self.parser.parse_tac_file()
        self.assertIsNotNone(instructions)
        # Expected number of instructions (excluding comments and blank lines)
        # Count them from the setUp content carefully.
        # _S0, _S1, START_PROC (label only), proc, _t0=, _t1=, _t2=, _t3=, RESULT=, X=, rdi, wri, wrs, push @, push 123, push TEMP_VAL, call MY_FUNC, call ANOTHER_FUNC, GOTO, IF_EQ, _t4=retrieve, return, return _t4, ELSE_LABEL (label only), wrln, END_LABEL (label only), endp, START PROC
        self.assertEqual(len(instructions), 28) 

    def test_string_definition(self):
        instructions = self.parser.parse_tac_file()
        instr = instructions[0] # _S0: .ASCIZ "Hello, World!"
        self.assertEqual(instr.line_number, 3)
        self.assertEqual(instr.label, "_S0")
        self.assertEqual(instr.opcode, TACOpcode.STRING_DEF)
        self.assertIsNotNone(instr.operand1)
        self.assertEqual(instr.operand1.value, '"Hello, World!"')
        self.assertFalse(instr.operand1.is_address_of)

        instr_s1 = instructions[1] # _S1: .ASCIZ 'Another string'
        self.assertEqual(instr_s1.line_number, 4)
        self.assertEqual(instr_s1.label, "_S1")
        self.assertEqual(instr_s1.opcode, TACOpcode.STRING_DEF)
        self.assertIsNotNone(instr_s1.operand1)
        self.assertEqual(instr_s1.operand1.value, "'Another string'")

    def test_label_only_line(self):
        instructions = self.parser.parse_tac_file()
        # START_PROC: (line 5)
        instr = next(i for i in instructions if i.raw_line.strip() == "START_PROC:")
        self.assertEqual(instr.label, "START_PROC")
        self.assertEqual(instr.opcode, TACOpcode.LABEL)
        self.assertIsNone(instr.destination)
        self.assertIsNone(instr.operand1)
        self.assertIsNone(instr.operand2)

    def test_proc_begin_end(self):
        instructions = self.parser.parse_tac_file()
        proc_instr = instructions[3] # proc MAIN_PROC
        self.assertEqual(proc_instr.opcode, TACOpcode.PROC_BEGIN)
        self.assertIsNotNone(proc_instr.operand1)
        self.assertEqual(proc_instr.operand1.value, "MAIN_PROC")

        endp_instr = next(i for i in instructions if i.opcode == TACOpcode.PROC_END)
        self.assertEqual(endp_instr.opcode, TACOpcode.PROC_END)
        self.assertIsNotNone(endp_instr.operand1)
        self.assertEqual(endp_instr.operand1.value, "MAIN_PROC")

    def test_assignment_literal(self):
        instructions = self.parser.parse_tac_file()
        instr = instructions[4] # _t0 = 5
        self.assertEqual(instr.opcode, TACOpcode.ASSIGN)
        self.assertEqual(instr.destination.value, "_t0")
        self.assertEqual(instr.operand1.value, 5) # Parser should convert to int
        self.assertIsNone(instr.operand2)

    def test_assignment_variable(self):
        instructions = self.parser.parse_tac_file()
        instr = instructions[5] # _t1 = A
        self.assertEqual(instr.opcode, TACOpcode.ASSIGN)
        self.assertEqual(instr.destination.value, "_t1")
        self.assertEqual(instr.operand1.value, "A")

    def test_binary_operation(self):
        instructions = self.parser.parse_tac_file()
        instr = instructions[6] # _t2 = _t0 + _t1
        self.assertEqual(instr.opcode, TACOpcode.ADD)
        self.assertEqual(instr.destination.value, "_t2")
        self.assertEqual(instr.operand1.value, "_t0")
        self.assertEqual(instr.operand2.value, "_t1")
        
        instr_lit = instructions[7] # _t3 = _t0 + 10
        self.assertEqual(instr_lit.opcode, TACOpcode.ADD)
        self.assertEqual(instr_lit.destination.value, "_t3")
        self.assertEqual(instr_lit.operand1.value, "_t0")
        self.assertEqual(instr_lit.operand2.value, 10)

    def test_unary_operation(self):
        instructions = self.parser.parse_tac_file()
        instr = instructions[9] # X = uminus Y
        self.assertEqual(instr.opcode, TACOpcode.UMINUS)
        self.assertEqual(instr.destination.value, "X")
        self.assertEqual(instr.operand1.value, "Y")

    def test_io_operations(self):
        instructions = self.parser.parse_tac_file()
        rdi_instr = instructions[10] # rdi INPUT_VAR
        self.assertEqual(rdi_instr.opcode, TACOpcode.READ_INT)
        self.assertEqual(rdi_instr.destination.value, "INPUT_VAR") # rdi uses destination field for the variable

        wri_instr = instructions[11] # wri OUTPUT_VAR
        self.assertEqual(wri_instr.opcode, TACOpcode.WRITE_INT)
        self.assertEqual(wri_instr.operand1.value, "OUTPUT_VAR")

        wrs_instr = instructions[12] # wrs _S0
        self.assertEqual(wrs_instr.opcode, TACOpcode.WRITE_STR)
        self.assertEqual(wrs_instr.operand1.value, "_S0")
        
        wrln_instr = next(i for i in instructions if i.opcode == TACOpcode.WRITE_NEWLINE)
        self.assertEqual(wrln_instr.opcode, TACOpcode.WRITE_NEWLINE)
        self.assertIsNone(wrln_instr.operand1)

    def test_push_operation(self):
        instructions = self.parser.parse_tac_file()
        push_addr_instr = instructions[13] # push @SOME_VAR
        self.assertEqual(push_addr_instr.opcode, TACOpcode.PUSH)
        self.assertEqual(push_addr_instr.operand1.value, "SOME_VAR")
        self.assertTrue(push_addr_instr.operand1.is_address_of)

        push_lit_instr = instructions[14] # push 123
        self.assertEqual(push_lit_instr.opcode, TACOpcode.PUSH)
        self.assertEqual(push_lit_instr.operand1.value, 123)
        self.assertFalse(push_lit_instr.operand1.is_address_of)

    def test_call_operation(self):
        instructions = self.parser.parse_tac_file()
        call_instr = instructions[16] # call MY_FUNC, 2
        self.assertEqual(call_instr.opcode, TACOpcode.CALL)
        self.assertEqual(call_instr.operand1.value, "MY_FUNC")
        self.assertEqual(call_instr.operand2.value, 2) # Num params
        
        call_instr_no_params = instructions[17] # call ANOTHER_FUNC
        self.assertEqual(call_instr_no_params.opcode, TACOpcode.CALL)
        self.assertEqual(call_instr_no_params.operand1.value, "ANOTHER_FUNC")
        self.assertIsNone(call_instr_no_params.operand2) # No num_params specified

    def test_goto_operation(self):
        instructions = self.parser.parse_tac_file()
        goto_instr = instructions[18] # GOTO END_LABEL
        self.assertEqual(goto_instr.opcode, TACOpcode.GOTO)
        self.assertEqual(goto_instr.operand1.value, "END_LABEL") # GOTO uses operand1 for target label

    def test_conditional_goto_operation(self):
        instructions = self.parser.parse_tac_file()
        if_eq_instr = instructions[19] # IF_EQ _t1, 0, ELSE_LABEL
        self.assertEqual(if_eq_instr.opcode, TACOpcode.IF_EQ)
        self.assertEqual(if_eq_instr.operand1.value, "_t1")
        self.assertEqual(if_eq_instr.operand2.value, 0)
        self.assertEqual(if_eq_instr.destination.value, "ELSE_LABEL") # Conditional jumps use destination for target label

    def test_retrieve_operation(self):
        instructions = self.parser.parse_tac_file()
        retrieve_instr = instructions[20] # _t4 = retrieve
        self.assertEqual(retrieve_instr.opcode, TACOpcode.RETRIEVE)
        self.assertEqual(retrieve_instr.destination.value, "_t4")

    def test_return_operation(self):
        instructions = self.parser.parse_tac_file()
        return_no_val_instr = instructions[21] # return
        self.assertEqual(return_no_val_instr.opcode, TACOpcode.RETURN)
        self.assertIsNone(return_no_val_instr.operand1)

        return_val_instr = instructions[22] # return _t4
        self.assertEqual(return_val_instr.opcode, TACOpcode.RETURN)
        self.assertEqual(return_val_instr.operand1.value, "_t4")

    def test_program_start_operation(self):
        instructions = self.parser.parse_tac_file()
        start_proc_instr = next(i for i in instructions if i.opcode == TACOpcode.PROGRAM_START)
        self.assertEqual(start_proc_instr.opcode, TACOpcode.PROGRAM_START)
        self.assertEqual(start_proc_instr.operand1.value, "MAIN_PROC")


if __name__ == '__main__':
    unittest.main()
