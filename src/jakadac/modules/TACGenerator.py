# Ada_Compiler_Construction/src/jakadac/modules/TACGenerator.py

import logging
from .SymTable import Symbol, EntryType, VarType # Assuming necessary imports
from .Token import Token # Needed for type hints if used, or Symbol creation checks

logger = logging.getLogger(__name__)

class TACGenerator:
    """
    Generates Three-Address Code (TAC) instructions based on semantic actions
    driven by the parser. It manages temporary variables, formats instructions,
    and writes the final TAC file.
    """
    def __init__(self, output_filename: str):
        """
        Initializes the TACGenerator.

        Args:
            output_filename (str): The path to the file where TAC will be written.
        """
        self.output_filename = output_filename
        self.tac_lines = []  # Stores generated TAC instructions as strings
        self.temp_counter = 0 # Counter for generating unique temporary variable names (_t1, _t2, ...)
        self.start_proc_name = None # Name of the main procedure for the 'start' directive
        logger.info(f"TACGenerator initialized for output: {self.output_filename}")

    def emit(self, instruction_str: str):
        """
        Appends a single, formatted TAC instruction string to the internal list.

        Args:
            instruction_str (str): The complete TAC instruction line.
        """
        self.tac_lines.append(instruction_str)
        # logger.debug(f"Emitted: {instruction_str}") # Optional: Log every emitted line

    def _newTempName(self) -> str:
        """Internal method to generate the next temporary variable name."""
        self.temp_counter += 1
        return f"_t{self.temp_counter}"

    def newTemp(self) -> str:
        """
        Generates and returns a new unique temporary variable name (e.g., "_t1").

        Returns:
            str: The new temporary variable name.
        """
        temp_name = self._newTempName()
        logger.debug(f"Generated new temporary: {temp_name}")
        return temp_name

    def getPlace(self, symbol_or_value) -> str:
        """
        Determines the 'place' string representation for a symbol or literal value
        in TAC instructions.

        Args:
            symbol_or_value: A Symbol object, a literal value (int, float, str),
                             or potentially a temporary name string.

        Returns:
            str: The TAC representation (e.g., "MyGlobal", "_BP-4", "_t1", "5").

        Raises:
            ValueError: If the input type is unrecognized or invalid for TAC.
            AttributeError: If a required attribute (like offset) is missing from a Symbol.
        """
        if isinstance(symbol_or_value, Symbol):
            symbol = symbol_or_value
            logger.debug(f"Getting place for Symbol: {symbol.name}, Depth: {symbol.depth}, Type: {symbol.entry_type}")

            if symbol.entry_type == EntryType.CONSTANT:
                # For constants, use their literal value
                if symbol.const_value is None:
                     raise ValueError(f"Constant symbol '{symbol.name}' has no value.")
                return str(symbol.const_value) # Use the stored constant value directly

            elif symbol.depth == 1:
                # Globals (Depth 1) use their name
                return symbol.name

            elif symbol.depth > 1:
                # Locals/Params (Depth > 1) use BP offset
                if symbol.offset is None:
                    # This indicates an error in offset calculation upstream (Parser/SymTable)
                    logger.error(f"Symbol '{symbol.name}' (Depth {symbol.depth}) has no offset assigned.")
                    # Option 1: Raise error
                    # raise AttributeError(f"Symbol '{symbol.name}' requires an offset for TAC generation.")
                    # Option 2: Return an error placeholder (as per plan example)
                    return f"ERROR_NO_OFFSET_FOR_{symbol.name}" # Or a generic error string
                elif symbol.offset >= 0: # Parameters have positive or zero offsets (BP+offset)
                     return f"_BP+{symbol.offset}"
                else: # Locals have negative offsets (BP-offset)
                     # Ensure the format is _BP-N, not _BP+-N
                     return f"_BP{symbol.offset}" # Offset is already negative
            else:
                # Should not happen for variables/params based on current understanding
                logger.error(f"Symbol '{symbol.name}' has unexpected depth {symbol.depth} for place generation.")
                return f"ERROR_BAD_SYMBOL_DEPTH_{symbol.name}"

        elif isinstance(symbol_or_value, (int, float)):
            # Literal numbers are used directly
            logger.debug(f"Getting place for literal number: {symbol_or_value}")
            return str(symbol_or_value)

        elif isinstance(symbol_or_value, str):
             # Could be a temporary name already generated (like "_t1")
             # Basic check: does it look like a temp or a known BP format?
             if symbol_or_value.startswith("_t") or symbol_or_value.startswith("_BP"):
                 logger.debug(f"Getting place for string (likely temp/place): {symbol_or_value}")
                 return symbol_or_value
             else:
                 # Or could it be a global name passed as string? Less ideal.
                 # Assume if it's a string and not a temp/BP, it might be a global.
                 # Requires SymTable lookup for validation if stricter checks are needed.
                 logger.warning(f"Treating string '{symbol_or_value}' as a potential global variable name.")
                 return symbol_or_value

        # Add handling for other literal types (bool, char) if needed

        else:
            logger.error(f"Cannot determine place for unexpected type: {type(symbol_or_value)}, value: {symbol_or_value}")
            # Option 1: Raise error
            # raise ValueError(f"Unsupported type for getPlace: {type(symbol_or_value)}")
            # Option 2: Return error placeholder
            return f"ERROR_UNKNOWN_PLACE_TYPE_{type(symbol_or_value).__name__}"


    def emitProcStart(self, proc_name: str):
        """Emits the 'proc <name>' directive and resets the temporary counter."""
        self.emit(f"proc {proc_name}")
        self.temp_counter = 0 # Reset temps for the new procedure scope
        logger.info(f"Emitted proc start for: {proc_name}, temp counter reset.")

    def emitProcEnd(self, proc_name: str):
        """Emits the 'endp <name>' directive."""
        self.emit(f"endp {proc_name}")
        logger.info(f"Emitted proc end for: {proc_name}")

    def emitProgramStart(self, main_proc_name: str):
        """Stores the name of the main procedure for the final 'start' directive."""
        self.start_proc_name = main_proc_name
        logger.info(f"Registered start procedure: {main_proc_name}")

    def writeOutput(self):
        """Writes all accumulated TAC lines, prefixed by the 'start' directive, to the output file."""
        if not self.start_proc_name:
            logger.error("Cannot write TAC output: Start procedure name not set.")
            raise RuntimeError("Start procedure name was not set before calling writeOutput.")

        try:
            with open(self.output_filename, 'w') as f:
                # Write the 'start' directive first, as required
                f.write(f"start {self.start_proc_name}\n")
                # Write all the accumulated instruction lines
                for line in self.tac_lines:
                    f.write(f"{line}\n")
            logger.info(f"Successfully wrote {len(self.tac_lines) + 1} lines to {self.output_filename}")
        except IOError as e:
            logger.error(f"Failed to write TAC output to {self.output_filename}: {e}")
            raise # Re-raise the exception after logging

    # --- Placeholder methods for operations (to be implemented based on plan) ---

    def emitBinaryOp(self, op: str, dest_place: str, left_place: str, right_place: str):
        """(Placeholder) Emits a binary operation instruction: dest = left op right."""
        # TODO: Map Ada ops (+, -, *, /, rem, mod, and, or) to TAC opcodes if necessary
        # TODO: Handle type checking/coercion if applicable at TAC level?
        tac_op = op # Placeholder - map if needed
        self.emit(f"{dest_place} = {left_place} {tac_op} {right_place}")
        logger.debug(f"Emitted Binary Op: {dest_place} = {left_place} {tac_op} {right_place}")

    def emitUnaryOp(self, op: str, dest_place: str, operand_place: str):
        """(Placeholder) Emits a unary operation instruction: dest = op operand."""
        # TODO: Map Ada ops (unary +, unary -, not) to TAC opcodes (e.g., UMINUS)
        tac_op = op # Placeholder - map if needed (e.g., '-' -> 'UMINUS')
        self.emit(f"{dest_place} = {tac_op} {operand_place}")
        logger.debug(f"Emitted Unary Op: {dest_place} = {tac_op} {operand_place}")

    def emitAssignment(self, dest_place: str, source_place: str):
        """Emits an assignment instruction: dest = source."""
        # TODO: Add checks? (e.g., LHS cannot be a literal)
        self.emit(f"{dest_place} = {source_place}")
        logger.debug(f"Emitted Assignment: {dest_place} = {source_place}")

    def emitPush(self, place: str, mode): # mode likely ParameterMode enum
        """(Placeholder) Emits a push instruction (value or address based on mode)."""
        # TODO: Import ParameterMode
        # TODO: Implement logic: if mode is IN -> push, else -> push @
        push_op = "push" # Placeholder
        # if mode != ParameterMode.IN:
        #    push_op = "push @"
        self.emit(f"{push_op} {place}")
        logger.debug(f"Emitted Push: {push_op} {place}") # Add mode info

    def emitCall(self, proc_name: str):
        """Emits a call instruction."""
        self.emit(f"call {proc_name}")
        logger.debug(f"Emitted Call: {proc_name}")


