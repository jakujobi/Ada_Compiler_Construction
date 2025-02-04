# Lexical Analyzer for Ada Subset

Welcome to the Lexical Analyzer project! This project is part of a compiler construction course and is designed to scan a subset of the Ada programming language, breaking the source code into meaningful tokens. The project uses several modules to keep the design modular, robust, and maintainable.

---
## Overview

The Lexical Analyzer reads an Ada source file and produces a stream of tokens. It handles:

- **Reserved Keywords:** e.g., `PROCEDURE`, `MODULE`, etc.
- **Identifiers:** Variable names and procedure names. (Identifiers longer than 17 characters are rejected.)
- **Numeric Literals:** Both integer and real number tokens.
- **String Literals:** Enclosed in double quotes with support for escaped quotes.
- **Character Literals:** Enclosed in single quotes with support for escaped single quotes.
- **Operators & Punctuation:** Assignment (`:=`), arithmetic operators, relational operators, and more.

Detailed debugging and logging are provided via a custom Logger, and file operations are handled by the FileHandler module.

---
## Project Structure
- **Definitions.py:**  
    Defines the token types (using an `Enum`), reserved words, and regular expression patterns for matching tokens.
    
    - **Regular Expressions:**
        - **LITERAL:** Matches string literals using the pattern  
            `r'"(?:[^"\n]|"")*(?:"|$)'`  
            which starts with a double quote, accepts any character that is not a double quote or a newline (or allows two consecutive double quotes as an escape), and then ends with a double quote (or end-of-input if unterminated).
        - **CHAR_LITERAL:** Matches character literals with the pattern  
            `r"'(?:[^'\n]|'')(?:"+"'|$)"`  
            that handles a single quoted character (or an escaped quote).
        - **ID:** Matches identifiers with the pattern  
            `r"[a-zA-Z][a-zA-Z0-9_]*"`  
            while additional logic ensures identifiers are no longer than 17 characters.
        - Other patterns exist for numbers, operators, and punctuation.
- **Token.py:**  
    Implements the `Token` class. Each token stores its type, lexeme, line number, column number, and any associated values (for numbers or literals). The class provides methods for debugging and user‑friendly output.
    
- **LexicalAnalyzer.py:**  
    Contains the `LexicalAnalyzer` class, which is responsible for:
    
    - Reading source code.
    - Skipping whitespace and comments.
    - Matching tokens using the regex patterns from Definitions.
    - Logging errors (e.g., identifiers longer than 17 characters are logged and skipped).
- **FileHandler.py:**  
    Provides file-related operations such as finding, reading, writing, and appending to files. It supports both command‑line arguments and interactive input (including a GUI file explorer via Tkinter if available).
    
- **Logger.py:**  
    Implements a singleton logger that supports colored output, caller filtering, and configuration options for both console and file logging. This is used throughout the project to provide consistent debug information.
    
- **JohnA1.py:**  
    Serves as the main driver. It uses FileHandler to read a source file, invokes the LexicalAnalyzer to tokenize the file, and then prints (and optionally writes) the token table.

---
## How to Run

### Prerequisites
- **Python 3.6+**
- Tkinter (optional): For the file explorer functionality. If not installed, the program will prompt you to enter file paths manually.

### Installation
1. **Clone the Repository:**
    ```bash
    git clone https://github.com/jakujobi/Ada_Compiler_Construction.git
    ```
2. Navigate to the Directory:**
    ```bash
    cd Ada_Compiler_Construction
    cd A1 - lexical Analyzer
    ```
3. **Set Up a Virtual Environment (Optional):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate
    ```

### Running the Analyzer
To run the lexical analyzer, use the following command:
```bash
python3 JohnA1.py <input_file.ada> [output_file.txt]
```

- **input_file.ada:**  
    The Ada source file to analyze.
- **output_file.txt (Optional):**  
    File where the token table will be saved.

### Example
If you have a file named `example.ada`, run:
```bash
python3 JohnA1.py example.ada tokens.txt
```

This will:
1. Read the source code from `example.ada`.
2. Tokenize the source code.
3. Print the source code and a formatted token table to the console.
4. Save the token table to `tokens.txt`.
---
## Design Decisions
- **Modular Design:**  
    The project is split into multiple modules (Definitions, Token, LexicalAnalyzer, FileHandler, Logger, JohnA1) to enhance code reuse and maintainability.
- **Regular Expressions:**  
    Each token type is matched using specific regex patterns. For instance:
    - **LITERAL:**  
        Matches string literals and supports escaped quotes.
    - **CHAR_LITERAL:**  
        Matches character literals and handles escape sequences.
    - **ID:**  
        Matches identifiers while enforcing a maximum length of 17 characters via additional logic.
- **Error Handling:**  
    The lexer logs errors (for example, when an identifier is too long) and skips such tokens to prevent further processing issues.
- **Logging:**  
    A custom Logger is used throughout the project to provide detailed debugging information. This helps in development and troubleshooting.
- **File Operations:**  
    The FileHandler module abstracts all file-related operations, making it easy to handle files across various parts of the project.
---
## Ethical Use of AI
### Ethical Considerations
This project is developed with ethical practices in mind, especially concerning the use of artificial intelligence. Here are the key points regarding ethical use:

- **Local, Self-Run AI LLM Models:**  
    Any AI or language model used in this project is run locally on your machine. This means no data is sent to external servers, preserving the privacy and security of your source code and personal information.
    
- **Transparency:**  
    The AI tools are used solely to provide assistance in code generation, debugging, and documentation. They help in suggesting improvements, generating documentation, and even offering coding examples. All AI-generated suggestions are reviewed by the developer before integration.
    
- **No Unethical Data Handling:**  
    Since the AI models are self-run and local, there is no risk of your data being misused or stored on remote servers.
    
- **User Control:**  
    You have full control over how the AI tools are used in the project. This project encourages you to understand and verify any AI-generated output, ensuring that you maintain ownership and responsibility for your code.
    
- **Purpose of AI Use:**  
    The AI assistance in this project is intended to:
    
    - Help with code documentation and commenting.
    - Provide suggestions on design and error handling.
    - Aid in the generation of additional documentation and support materials.
    
    The tools are not used to replace human judgment or to make decisions on behalf of the developer but to serve as a helpful aid in the software development process.
    

## Contributing

Contributions are welcome! If you have suggestions or improvements:

- Fork the repository.
- Make your changes.
- Submit a pull request.
- Ensure your changes are well-documented and tested.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Thanks to my professor and classmates for their feedback and support.
- Special thanks to the open-source community for the tools and libraries that made this project possible.
- Inspired by numerous compiler construction resources and AI ethics discussions.

---

This README should provide a comprehensive guide to your Lexical Analyzer project, including detailed information about its structure, functionality, usage, design choices, and ethical considerations.