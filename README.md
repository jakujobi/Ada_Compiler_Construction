# Ada Compiler Construction

This repository contains the code and assignments for CSC 446 Compiler Construction at SDSU.

## Project Structure

├─ assignments/           # Individual assignment folders
│  ├─ A1 - Lexical Analyzer
│  ├─ A2 - Parser
│  ├─ A3_Recursive_Parser
│  ├─ A4_New_Symbol_Table
│  ├─ A5_Semantic_Analyzer
│  ├─ A5b_New_Semantic_Analyzer
│  ├─ A6_New_Grammar_Rules
│  └─ A7_3_Address_Code

├─ src/jakadac/modules/   # Compiler modules
│  ├─ Token.py
│  ├─ Definitions.py
│  ├─ Logger.py
│  ├─ FileHandler.py
│  ├─ LexicalAnalyzer.py
│  ├─ RDParser.py
│  ├─ SymTable.py
│  ├─ NewSemanticAnalyzer.py
│  └─ Driver.py

└─ README.md              # This file

## Getting Started

1. Clone the repository:
   ```sh
   git clone https://github.com/jakujobi/Ada_Compiler_Construction.git
   cd Ada_Compiler_Construction
   ```

2. Install dependencies (if any):
   ```sh
   # For now only Python 3 is required
   ```

3. Run an assignment driver. For example, to test the symbol table (A4):
   ```sh
   cd assignments/A4_New_Symbol_Table
   python JohnA4b.py
   ```

4. For semantic analyzer (A5b):
   ```sh
   cd assignments/A5b_New_Semantic_Analyzer
   python JohnA5b.py path/to/source.ada
   ```

5. Use the BaseDriver pipeline in `src/jakadac/modules/Driver.py` for custom tests.

## Module Documentation
See `src/jakadac/modules/README.md` for details on each compiler component.

---

© 2025 John Akujobi / AI Assistant
