# src/jakadac/modules/asm_gen/instruction_translators/asm_im_control_flow_translators.py

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..asm_generator import ASMGenerator
    from ...Logger import Logger
    from ...SymTable import SymbolTable # Added for self.symbol_table hint

from ..tac_instruction import ParsedTACInstruction, TACOpcode

class ControlFlowTranslators:
    # self will be an instance of ASMInstructionMapper

    def _translate_label(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        target_label = tac_instruction.label 
        if target_label:
            self.logger.debug(f"LABEL {target_label} -> {target_label}:")
            return [f"{target_label}:"]
        else:
            self.logger.error(f"LABEL TAC at line {tac_instruction.line_number} with Opcode=LABEL but missing label string in .label field.")
            return [f"; ERROR: Malformed LABEL TAC at line {tac_instruction.line_number} - Missing label name in .label field."]

    def _translate_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        target_label_operand = tac_instruction.destination
        if not target_label_operand or target_label_operand.value is None:
            self.logger.error(f"GOTO TAC at line {tac_instruction.line_number} is missing target label value (dest operand).")
            return [f"; ERROR: Malformed GOTO TAC at line {tac_instruction.line_number}"]
        
        target_label = str(target_label_operand.value)
        self.logger.debug(f"GOTO {target_label} -> JMP {target_label}")
        return [f"JMP {target_label}"]

    def _translate_if_false_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        condition_operand = tac_instruction.operand1
        target_label_operand = tac_instruction.destination

        if not condition_operand or condition_operand.value is None or \
           not target_label_operand or target_label_operand.value is None:
            self.logger.error(f"IF_FALSE_GOTO TAC at line {tac_instruction.line_number} is missing condition or target value.")
            return [f"; ERROR: Malformed IF_FALSE_GOTO TAC at line {tac_instruction.line_number}"]

        cond_asm = self.asm_generator.get_operand_asm(str(condition_operand.value), tac_instruction.opcode)
        target_label = str(target_label_operand.value)
        
        asm_lines = []
        # Ensure cond_asm is not an immediate for CMP's first operand unless it's already in a register
        if self.asm_generator.is_immediate(cond_asm):
            asm_lines.append(f"MOV AX, {cond_asm}") # Move immediate to AX
            asm_lines.append(f"CMP AX, 0")
        elif cond_asm.startswith("["): 
            asm_lines.append(f"CMP WORD PTR {cond_asm}, 0")
        else: 
            asm_lines.append(f"CMP {cond_asm}, 0")
        
        asm_lines.append(f"JE {target_label}") 
        self.logger.debug(f"IF_FALSE_GOTO {cond_asm}, {target_label} -> CMP ..., 0; JE {target_label}")
        return asm_lines

    def _common_conditional_jump_translation(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction, jump_mnemonic: str) -> List[str]:
        op1 = tac_instruction.operand1
        op2 = tac_instruction.operand2
        target_label_op = tac_instruction.destination

        if not op1 or op1.value is None or \
           not op2 or op2.value is None or \
           not target_label_op or target_label_op.value is None:
            op_name = tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else str(tac_instruction.opcode)
            self.logger.error(f"{op_name} TAC at line {tac_instruction.line_number} is missing operand or target values.")
            return [f"; ERROR: Malformed {op_name} TAC at line {tac_instruction.line_number}"]

        op1_asm = self.asm_generator.get_operand_asm(str(op1.value), tac_instruction.opcode)
        op2_asm = self.asm_generator.get_operand_asm(str(op2.value), tac_instruction.opcode)
        target_label = str(target_label_op.value)
        asm_lines = []

        op1_is_mem = op1_asm.startswith("[")
        op2_is_mem = op2_asm.startswith("[")
        op1_is_imm = self.asm_generator.is_immediate(op1_asm)
        op2_is_imm = self.asm_generator.is_immediate(op2_asm)

        cmp_op1, cmp_op2 = op1_asm, op2_asm
        actual_jump_mnemonic = jump_mnemonic

        # Strategy:
        # 1. Avoid mem, mem: move one to AX.
        # 2. Prefer reg, imm or mem, imm.
        # 3. If imm, reg: swap to reg, imm and invert jump condition if necessary.

        if op1_is_mem and op2_is_mem:
            asm_lines.append(f"MOV AX, {op2_asm}") # Load op2 into AX
            cmp_op1, cmp_op2 = op1_asm, "AX"       # Compare op1 (mem) with AX
        elif op1_is_imm and op2_is_mem: # imm, mem -> prefer mem, imm
            cmp_op1, cmp_op2 = op2_asm, op1_asm
            # Invert jump condition (e.g. JE -> JE, JL -> JG)
            opposite_jump_map = { "JE": "JE", "JNE": "JNE", "JL": "JG", "JLE": "JGE", "JG": "JL", "JGE": "JLE" }
            actual_jump_mnemonic = opposite_jump_map.get(jump_mnemonic, jump_mnemonic)
        elif op1_is_imm and not op2_is_mem and not op2_is_imm: # imm, reg -> prefer reg, imm
            cmp_op1, cmp_op2 = op2_asm, op1_asm
            opposite_jump_map = { "JE": "JE", "JNE": "JNE", "JL": "JG", "JLE": "JGE", "JG": "JL", "JGE": "JLE" }
            actual_jump_mnemonic = opposite_jump_map.get(jump_mnemonic, jump_mnemonic)
        elif (op1_is_imm and op2_is_imm) or \
             (not op1_is_mem and not op1_is_imm and op2_is_mem and not self.asm_generator.is_register(op1_asm)): # reg, mem (where op1 is not a reg, implies error or complex op1)
            # Both immediate OR op1 is not suitable for direct CMP (e.g. complex offset that isn't reg)
            asm_lines.append(f"MOV AX, {op1_asm}")
            cmp_op1, cmp_op2 = "AX", op2_asm
        # else: op1 can be reg/mem, op2 can be reg/imm/mem (if op1 is reg) - handled by direct CMP

        asm_lines.append(f"CMP {cmp_op1}, {cmp_op2}")
        asm_lines.append(f"{actual_jump_mnemonic} {target_label}")
        
        op_name_log = tac_instruction.opcode.name if isinstance(tac_instruction.opcode, TACOpcode) else str(tac_instruction.opcode)
        self.logger.debug(f"{op_name_log} {op1_asm}, {op2_asm}, {target_label} -> {asm_lines}")
        return asm_lines

    def _translate_if_eq_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JE")

    def _translate_if_ne_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JNE")

    def _translate_if_lt_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JL") 

    def _translate_if_le_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JLE")

    def _translate_if_gt_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JG") 

    def _translate_if_ge_goto(self: 'ASMInstructionMapper', tac_instruction: ParsedTACInstruction) -> List[str]:
        return self._common_conditional_jump_translation(tac_instruction, "JGE")