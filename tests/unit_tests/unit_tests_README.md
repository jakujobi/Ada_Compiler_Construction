# Ada Compiler Construction - Unit Tests

This directory contains unit tests for the various modules of the Ada Compiler Construction project (`jakadac`). These tests aim to verify the correctness and robustness of individual components in isolation.

## Purpose

Unit tests are crucial for:

*   **Verification:** Ensuring that each module (Lexer, Parser, Symbol Table, etc.) behaves as expected according to its specifications.
*   **Regression Prevention:** Detecting unintended side effects or breakages introduced by new code changes or refactoring.
*   **Design Improvement:** Writing tests often encourages better module design, promoting modularity and testability.
*   **Documentation:** Tests serve as executable documentation, demonstrating how modules are intended to be used.

## Running the Tests

Tests are implemented using Python's built-in `unittest` framework.

**Prerequisites:**

*   Python 3.x installed.
*   Necessary dependencies (if any, though the core modules seem self-contained) installed.

**Execution:**

1.  **Navigate to the Project Root:** Open your terminal or command prompt and change the directory to the root of the `Ada_Compiler_Construction` project (the directory containing the `src` and `tests` folders).

    ```bash
    cd /path/to/Ada_Compiler_Construction
    ```

2.  **Run `unittest` Discovery:** Use the following command to automatically discover and run all tests within the `tests/unit_tests` directory:

    ```bash
    # Standard execution
    python -m unittest discover tests/unit_tests

    # Verbose execution (shows status for each test)
    python -m unittest discover -v tests/unit_tests
    ```

    Alternatively, you can often use shorter versions if your primary test directory is `tests` or if tests are discoverable from the root:

    ```bash
    python -m unittest discover -v tests
    # or
    python -m unittest discover -v
    ```

3.  **Run Specific Test Files:** To run tests from only a specific file, you can target it directly:

    ```bash
    python -m unittest tests.unit_tests.test_symtable # Note the dot notation
    # or sometimes the file path works depending on the environment:
    python -m unittest tests/unit_tests/test_symtable.py
    ```

**Expected Output:**

The standard output will show the number of tests run, followed by either `OK` if all tests pass, or details about any `FAILURES` or `ERRORS` encountered. Using the `-v` flag provides a detailed status for each individual test run.

## Test Structure

Each `test_*.py` file corresponds to a specific module in the `src/jakadac/modules/` directory. (Currently 70 tests passing across all files).

*   **`test_definitions.py`**: Tests the `Definitions` class, verifying `TokenType` enum members, reserved word mappings, and operator mappings.
*   **`test_driver.py`**: Tests the `BaseDriver` class, focusing on its initialization logic and handling of arguments like input/output files, debug flags, and parser selection.
*   **`test_file_handler.py`**: Tests the `FileHandler` class, verifying methods for reading, writing, appending, finding files, and processing lines.
*   **`test_john_a1.py`**: (Purpose unclear from name - likely related to a specific assignment's driver or functionality).
*   **`test_lexical_analyzer.py`**: Tests the `LexicalAnalyzer`, ensuring it correctly tokenizes various Ada source code constructs (identifiers, numbers, reals, operators, comments, reserved words, EOF) and handles errors like long identifiers or unterminated strings.
*   **`test_logger.py`**: Tests the `Logger` setup, ensuring it initializes correctly as a singleton, handles different log levels, manages log files in temporary directories, and cleans up resources properly.
*   **`test_new_semantic_analyzer.py`**: Tests the `NewSemanticAnalyzer`, verifying its ability to traverse mock parse trees, manage scopes, insert symbols (procedures, variables, constants), calculate offsets (implicitly via local size), and detect errors like duplicate declarations and undeclared identifiers.
*   **`test_rdparser_extended.py`**: Tests the `RDParserExtended`, focusing on parsing specific grammar rules (declarations, assignments, expressions involving various operators), handling sequences of statements, managing scopes, and checking for semantic errors it can detect directly (like undeclared variables, procedure name mismatches).
*   **`test_symtable.py`**: Tests the `SymbolTable` class, covering scope management (enter/exit), symbol insertion (variables, constants, procedures), lookups (including shadowing and not-found errors), and duplicate symbol error handling.
*   **`test_token.py`**: Tests the `Token` class, ensuring correct initialization with different attributes (lexeme, type, line/col numbers, optional values) and verifying its `__str__` and `__repr__` methods.

## Important Notes

*   **Path Adjustments:** Test files include logic at the beginning to dynamically add the `src` directory to the Python path (`sys.path`). This allows tests in `tests/unit_tests` to import modules from `src/jakadac/modules`.
*   **Linter Import Errors:** Due to the dynamic path adjustments, static analysis tools or linters (like Pylance in VS Code) running directly on the test files might report "Import could not be resolved" errors. These errors usually **do not** prevent the tests from running correctly when executed using `python -m unittest discover` from the project root directory, as the path is correctly adjusted at runtime. However, be aware that dynamic path changes can occasionally lead to subtle issues (e.g., comparing class instances loaded differently) if not managed carefully in test setups.
*   **Logging:** Most test files attempt to suppress or disable logging during test execution to keep the output clean. Check the `setUp` method or specific tests if you need to re-enable logging for debugging.
*   **Mocking:** Tests for components that interact with the file system (`BaseDriver`, `Logger`) or other complex classes (`NewSemanticAnalyzer`, `RDParserExtended`) often use the `unittest.mock` library (`patch`, `MagicMock`) to isolate the component under test.
*   **Recent Fixes:** Several issues related to logger file handling (PermissionError, FileNotFoundError), singleton management across tests, token string representation, enum comparisons, parser scope management, and IdentifierList node generation were recently addressed, resulting in all tests passing.

## Future Improvements

*   **Increased Coverage:** Add more specific test cases within each file to cover edge cases, different combinations of inputs, and more complex grammatical structures (e.g., nested procedures, parameter modes, full expression variations).
*   **Integration Tests:** Add integration tests (perhaps in a separate `tests/integration_tests` directory) that test the interaction between multiple components (e.g., Lexer -> Parser -> Analyzer).
*   **Test Runner Configuration:** Consider adding a configuration file (like `pyproject.toml` for `pytest` or specific `unittest` configurations) to manage test discovery and execution, potentially resolving linter path issues.
*   **CI Integration:** Integrate test execution into a Continuous Integration (CI) pipeline to automatically run tests on code changes. 