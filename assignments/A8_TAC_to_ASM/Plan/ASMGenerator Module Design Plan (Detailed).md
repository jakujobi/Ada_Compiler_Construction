# **ASMGenerator Module Design Plan (Detailed \- Assignment 8\)**

## **1\. Overview**

This document provides a detailed plan for the 8086 assembly code generation module (ASMGenerator) and its sub-components. It elaborates on the responsibilities, interactions, and implementation details for each part, building upon the initial design.

**Input:**

* A .tac file (output of A7 \+ A8 I/O extensions).
* A populated SymbolTable object instance (from previous phases).

**Output:**

* A .asm file (MASM/TASM compatible, runnable in DOSBox).

**Core Strategy:**

* **Two-pass approach** orchestrated by ASMGenerator.
* **Modular Design:** Split into TACInstruction, TACParser, DataSegmentManager, ASMOperandFormatter, ASMInstructionMapper, and ASMGenerator.

## **2\. Component Details (Expanded)**

### **2.1. TACInstruction (Data Class)**

* **File:** tac\_instruction.py
* **Purpose:** A structured container for a single parsed TAC instruction line.
* **Implementation:** Python @dataclass recommended for simplicity and type hinting.
* **Attributes:**
  * line\_number: int (For error reporting)
  * label: Optional\[str\] \= None (e.g., "L1")
  * opcode: Optional\[str\] \= None (e.g., "ASSIGN", "ADD", "WRS", "PROC")
  * op1: Optional\[str\] \= None (Source operand 1 / Address / Label)
  * op2: Optional\[str\] \= None (Source operand 2\)
  * dest: Optional\[str\] \= None (Destination operand / Procedure Name)
* **Methods:**
  * @staticmethod from\_tac\_line(line: str, line\_num: int) \-\> 'TACInstruction':
    * **Input:** Raw string line from .tac, line number.
    * **Action:**
      1. Strip leading/trailing whitespace. Ignore empty lines or comment lines (if any defined).
      2. Check for and extract a leading label (e.g., L1:). Store label without the colon.
      3. **(Crucial!)** Based on the **actual, observed format** of your A7 TAC output (delimiters, operand order), split the remaining string into components.
      4. Identify the opcode (usually the first component after the label, or the first component if no label).
      5. Map the remaining components to op1, op2, dest based on the *known format* of the specific opcode. Define expected patterns clearly (e.g., for `dest = op1 op op2`, order might be dest, op1, op2 after `=`; for `wrs Label`, just op1=Label; for `proc Name`, dest=Name).
      6. Handle instructions with varying numbers of operands gracefully (e.g., `wrln` has none, `push @Var` has one, `add` has three).
    * **Output:** Populated TACInstruction instance. Raise an error for unparseable lines.

### **2.2. TACParser Class**

* **File:** tac\_parser.py
* **Purpose:** Read the entire .tac file and produce a list of TACInstruction objects.
* **Attributes:**
  * tac\_filepath: str
* **Methods:**
  * \_\_init\_\_(self, tac\_filepath: str): Stores file path.
  * parse(self) \-\> List\[TACInstruction\]:
    * **Action:**
      1. Open tac\_filepath for reading. Handle FileNotFoundError.
      2. Initialize an empty list instructions.
      3. Read the file line by line, keeping track of line\_number.
      4. For each non-empty line, call TACInstruction.from\_tac\_line(line, line\_number).
      5. Append the resulting TACInstruction object to the instructions list.
      6. Handle potential parsing errors from from\_tac\_line.
      7. Close the file.
    * **Output:** The complete list of TACInstruction objects representing the program.

### **2.3. DataSegmentManager Class**

* **File:** data\_segment\_manager.py
* **Purpose:** Collect definitions for the .data segment (globals, strings) by analyzing the TAC and symbol table. Generate the final .data section assembly code.
* **Attributes:**
  * symbol\_table: SymbolTable
  * global\_vars: Set\[str\] (Stores unique lexemes of depth 1 variables)
  * string\_literals: Dict\[str, str\] (Maps label like \_S0 to string value like "Prompt$")
* **Methods:**
  * \_\_init\_\_(self, symbol\_table: SymbolTable): Stores symbol\_table, initializes empty global\_vars set and string\_literals dict.
  * collect\_definitions(self, instructions: List\[TACInstruction\]):
    * **Input:** List of all TACInstruction objects.
    * **Action:**
      1. Iterate through instructions.
      2. For each operand (op1, op2, dest) that is not None and looks like an identifier (not immediate, not \[bp...\], not \_S...):
         * entry \= self.symbol\_table.lookup(operand) (Need context if names can be reused across scopes, but globals should be unique).
         * If entry found and entry.depth \== 1 and it's a variable (not procedure name): Add entry.lexeme to self.global\_vars.
      3. If instr.opcode \== 'wrs' (or equivalent):
         * Assume instr.op1 is the string label (e.g., \_S0).
         * entry \= self.symbol\_table.lookup(instr.op1)
         * If entry found and represents a stored string literal:
           * Retrieve the actual string value (e.g., from entry.value).
           * Ensure the value includes the $ terminator (this should ideally be added when stored in SymTable during TAC generation).
           * Store self.string\_literals\[instr.op1\] \= entry.value.
         * Else: Raise an error (string label not found in symbol table).
  * get\_data\_section\_asm(self) \-\> List\[str\]:
    * **Action:**
      1. Initialize asm\_lines \= \[".data"\].
      2. For var\_name in sorted(list(self.global\_vars)): (Sorting provides consistent output order)
         * Handle potential c \-\> cc rename if needed based on the stored lexeme.
         * Append f" {renamed\_var\_name:\<8} DW ?".
      3. For label, value in sorted(self.string\_literals.items()):
         * Append f"{label:\<8} DB \\"{value}\\"".
    * **Output:** List of assembly lines for the .data section.

### **2.4. ASMOperandFormatter Class**

* **File:** asm\_operand\_formatter.py
* **Purpose:** The critical translator for converting a single TAC operand string into its final 8086 assembly representation.
* **Attributes:**
  * symbol\_table: SymbolTable
* **Methods:**
  * \_\_init\_\_(self, symbol\_table: SymbolTable): Stores symbol table reference.
  * format\_operand(self, tac\_operand: str, current\_proc\_name: Optional\[str\] \= None) \-\> str:
    * **Input:** TAC operand string, optional name of the procedure currently being processed (for scoped lookups).
    * **Action (Detailed Logic):**
      1. **Handle None/Empty:** If tac\_operand is None or empty, return empty string or raise error.
      2. **Immediate Check:** Use try-except or regex to check if tac\_operand is an integer literal. If yes, return it as a string.
      3. **BP-Relative Check:** Check if tac\_operand starts with "\[bp" (or \_bp if that's the TAC format). If yes:
         * *If TAC uses internal offsets (e.g., \_bp+0, \_bp+2):* Parse the offset value. Look up the operand name (if needed, might not be present in TAC) or use context to determine if it was a parameter. Calculate the final offset (e.g., local 0 \-\> \-2, param 2 \-\> \+6). Return formatted f"\[bp{sign}{offset}\]".
         * *If TAC already uses final offsets (e.g., \[bp-2\], \[bp+6\]):* Validate the format and return it directly.
         * **Decision:** Assume TAC uses an internal representation like \_bp+Offset or just the variable name, requiring lookup and translation here.
      4. **String Label Check:** If tac\_operand matches the string label pattern (e.g., \_S\<number\>): Return f"OFFSET {tac\_operand}".
      5. **Identifier/Temp Lookup:** If none of the above, assume it's a variable or temporary name.
         * entry \= self.symbol\_table.lookup(tac\_operand, context=current\_proc\_name) (Handle KeyError or equivalent if not found).
         * Apply c \-\> cc rename if entry.lexeme \== 'c'. Store the potentially renamed lexeme.
         * If entry.depth \== 1: Return the (potentially renamed) entry.lexeme.
         * If entry.depth \>= 2:
           * Retrieve offset \= entry.offset and is\_param \= entry.isParameter.
           * **Translate Internal Offset to 8086 Offset:**
             * **(Verify!)** Cross-reference your specific stack frame documentation (`Notes/Semantic Analysis.md`, `Notes/Symbol Tables.md`) for exact layout.
             * If is\_param: asm\_offset \= offset \+ 4 (Assuming internal param offsets start at 0, first param is at [bp+4] after RetAddr(+2) and OldBP(+0)). Example: offset 0 -> +4, offset 2 -> +6.
             * Else (local/temp): asm\_offset \= \-(offset \+ 2\) (Assuming internal local/temp offsets start at 0, first local is at [bp-2] after OldBP(+0)). Example: offset 0 -> -2, offset 2 -> -4.
           * Return formatted f"\[bp{'+' if asm\_offset \> 0 else ''}{asm\_offset}\]".
      6. **Error:** If lookup fails or type is unexpected, raise an informative error including the tac\_operand and line\_number (if available).
    * **Output:** The assembly operand string (e.g., "10", "\[bp-4\]", "\[bp+6\]", "myGlobal", "OFFSET \_S0", "cc").

### **2.5. ASMInstructionMapper Class**

* **File:** asm\_instruction\_mapper.py
* **Purpose:** Provides the specific 8086 assembly instruction sequences (templates) for each TAC opcode.
* **Attributes:**
  * symbol\_table: SymbolTable
* **Methods:**
  * \_\_init\_\_(self, symbol\_table: SymbolTable): Stores symbol table reference.
  * **translate\_\*(self, instr: TACInstruction, formatter: ASMOperandFormatter) \-\> List\[str\]:** (One per opcode)
    * **translate\_assign(self, instr, formatter):**
      * dest \= formatter.format\_operand(instr.dest, ...)
      * src \= formatter.format\_operand(instr.op1, ...)
      * Return \[f" mov ax, {src}", f" mov {dest}, ax"\] (Handle potential immediate source differently if needed: mov {dest}, {src}).
      * **Note on Dereferencing:** If `dest` corresponds to a reference parameter (e.g., looks like `[bp+N]` from formatter), the sequence should be: `mov bx, dest_address_from_[bp+N]; mov ax, src; mov [bx], ax`. Similarly, if `src` is a reference parameter: `mov bx, src_address_from_[bp+N]; mov ax, [bx]; mov dest, ax`.
    * **translate\_add(self, instr, formatter):**
      * dest \= formatter.format\_operand(instr.dest, ...)
      * op1 \= formatter.format\_operand(instr.op1, ...)
      * op2 \= formatter.format\_operand(instr.op2, ...)
      * Return \[f" mov ax, {op1}", f" add ax, {op2}", f" mov {dest}, ax"\]
      * **Note on Dereferencing:** Similar logic applies if operands or destination are reference parameters (load address to BX, use `[bx]` for operation, store result via `[bx]` if dest is reference).
    * **translate\_mul(self, instr, formatter):** (Similar to add, using mov bx, op2, imul bx, apply dereferencing logic)
    * **translate\_proc(self, instr, formatter):**
      * proc\_name \= instr.dest
      * proc\_info \= self.symbol\_table.lookup(proc\_name)
      * size\_locals \= proc\_info.size\_of\_locals
      * Return \[f"{proc\_name} PROC", f" push bp", f" mov bp, sp", f" sub sp, {size\_locals}"\]
    * **translate\_endp(self, instr, formatter):**
      * proc\_name \= instr.dest
      * proc\_info \= self.symbol\_table.lookup(proc\_name)
      * size\_locals \= proc\_info.size\_of\_locals
      * size\_params \= proc\_info.size\_of\_params
      * Return \[f" add sp, {size\_locals}", f" pop bp", f" ret {size\_params}", f"{proc\_name} ENDP"\]
    * **translate\_call(self, instr, formatter):**
      * proc\_name \= instr.dest (or op1 depending on TAC format)
      * Return \[f" call {proc\_name}"\]
    * **translate\_push(self, instr, formatter):** (Pass by Value)
      * value\_op \= formatter.format\_operand(instr.op1, ...)
      * Return \[f" mov ax, {value\_op}", f" push ax"\] (Handle immediate push directly: push {value\_op})
    * **translate\_push\_ref(self, instr, formatter):** (Pass by Reference)
      * var\_name \= instr.op1 \# Assumes op1 is the variable *name* before formatting
      * address\_op \= f"offset {var\_name}" \# Generate OFFSET format directly
      * Return \[f" mov ax, {address\_op}", f" push ax"\]
    * **translate\_wrs(self, instr, formatter):**
      * label\_op \= formatter.format\_operand(instr.op1, ...) \# Should return "OFFSET \_S0"
      * Return \[f" mov dx, {label\_op}", f" call writestr"\]
    * **translate\_wri(self, instr, formatter):**
      * address\_op \= formatter.format\_operand(instr.op1, ...) \# e.g., "\[bp-6\]"
      * register \= "dx" \# **Confirm this from io.asm\!** Assume DX for now.
      * Return \[f" mov {register}, {address\_op}", f" call writeint"\]
    * **translate\_rdi(self, instr, formatter):**
      * address\_op \= formatter.format\_operand(instr.dest, ...) \# e.g., "\[bp-2\]"
      * Return \[f" call readint", f" mov {address\_op}, bx"\] \# readint returns in BX
    * **translate\_wrln(self, instr, formatter):**
      * Return \[f" call writeln"\]
    * *(Add methods for other ops like SUB, potentially control flow if needed)*

### **2.6. ASMGenerator Class (Orchestrator)**

* **File:** asm\_generator.py
* **Purpose:** Coordinates the entire process, uses the other components.
* **Attributes:** As defined previously (paths, symbol table, instances of other components, start proc name).
* **Methods:**
  * \_\_init\_\_(...): Initializes attributes and instantiates components.
  * generate\_asm(self):
    * **Action:** Executes the two-pass strategy:
      1. Calls parser.parse() to get instructions.
      2. Calls data\_manager.collect\_definitions(instructions).
      3. Calls data\_manager.get\_data\_section\_asm() to get data\_lines.
      4. Initializes code\_lines \= \[\].
      5. Sets current\_proc\_context \= None.
      6. Iterates through instructions:
         * Handles labels (code\_lines.append(f"{instr.label}:")).
         * Handles start directive (stores instr.op1 in self.start\_proc\_name).
         * Handles proc (sets current\_proc\_context, calls mapper.translate\_proc).
         * Handles endp (calls mapper.translate\_endp, clears current\_proc\_context).
         * For all other opcodes, looks up the appropriate mapper.translate\_\* method (e.g., using getattr or a dispatch dictionary) and calls it, passing instr and self.formatter. Appends results to code\_lines.
      7. Calls self.\_generate\_main\_entry() to get main\_lines.
      8. Assembles the final list of strings: Boilerplate \+ data\_lines \+ .code \+ include io.asm \+ code\_lines \+ main\_lines \+ END main\_label.
      9. Writes the result to self.asm\_filepath.
  * \_generate\_main\_entry(self) \-\> List\[str\]:
    * **Action:** Returns the list of strings for the standard main PROC block, ensuring call {self.start\_proc\_name} uses the name collected during the loop. Includes error handling if start\_proc\_name is missing.

## **3\. Error Handling & Logging**

* Implement specific and informative error messages throughout all components (e.g., "Invalid TAC format on line {line_num}: {line}", "SymbolTable lookup failed for identifier '{operand}' in procedure '{proc_name}' during TAC line {line_num}", "Missing required procedure size information for '{proc_name}' in SymbolTable").
* Utilize the existing `Logger` for debug tracing and informational messages.
