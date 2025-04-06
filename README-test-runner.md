# Test Runner for Ada Compiler Construction

This tool allows you to easily run any of your driver files (JohnA1, JohnA3, etc.) on any test file in the test_files directory or its subdirectories.

## Features

- Automatically finds all driver files (JohnA*.py) in the project
- Lists all test files in the test_files directory and its subdirectories
- Provides an interactive menu to select a driver and a test file
- Runs the selected driver on the selected test file
- Displays the output of the test run
- Allows running multiple tests in succession
- Configurable through a JSON configuration file
- Robust error handling and timeout management
- Output truncation for large test outputs

## Usage

1. Navigate to the Ada_Compiler_Construction directory
2. Run the test runner:

```bash
# Basic usage
python test_runner.py

# With a custom configuration file
python test_runner.py --config test_runner_config.json
```

3. Follow the prompts to select a driver and a test file
4. View the output of the test run
5. Choose to run another test or exit

## Configuration

The test runner can be configured using a JSON configuration file. The following options are available:

| Option | Description | Default |
|--------|-------------|---------|
| `log_level` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | INFO |
| `driver_pattern` | Glob pattern to find driver files | JohnA*.py |
| `test_file_extensions` | List of file extensions to consider as test files | [".ada"] |
| `test_directory` | Directory containing test files | test_files |
| `output_format` | Format for output display | text |
| `timeout` | Maximum time in seconds to wait for a test to complete | 30 |
| `max_output_lines` | Maximum number of lines to display from test output | 1000 |

Example configuration file:

```json
{
    "log_level": "DEBUG",
    "driver_pattern": "JohnA*.py",
    "test_file_extensions": [".ada", ".txt"],
    "test_directory": "test_files",
    "output_format": "text",
    "timeout": 60,
    "max_output_lines": 500
}
```

## How It Works

The test runner:

1. Scans the project for all driver files (JohnA*.py)
2. Scans the test_files directory for all .ada files
3. Presents a menu of available drivers
4. Presents a menu of available test files
5. Runs the selected driver on the selected test file
6. Displays the output of the test run

## Benefits

- No need to copy test files to different directories
- Quickly test any driver on any test file
- Maintains the ability to run files from their respective directories if needed
- Provides a consistent interface for testing
- Configurable to adapt to different testing needs
- Robust error handling to prevent crashes

## Example

```
Ada Compiler Construction Test Runner
=====================================

Driver Files:
------------
1. JohnA1
2. JohnA3
3. JohnA4
4. JohnA5
0. Cancel

Enter your choice (0-4): 1

Test Files:
----------
1. A5/test1.ada
2. A5/test2.ada
3. Errors/error1.ada
4. procedures/proc1.ada
5. Simple_procedures/simple1.ada
6. tf_add.ada
7. tf_const_and_order.ada
8. tf_inner_proc_local_vars.ada
9. tf_proc_params_vs_locals.ada
10. test19.ada
11. test20.ada
12. test21.ada
13. test22.ada
14. test23.ada
15. test24.ada
16. test25.ada
17. test26.ada
18. test27.ada
19. test28.ada
20. test29.ada
21. test30.ada
22. t51.ada
23. t52.ada
24. t53.ada
25. t54.ada
26. t55.ada
27. valid_03.ada
0. Cancel

Enter your choice (0-27): 6

Running JohnA1 on tf_add.ada

Output:
--------------------------------------------------
Source Code:
procedure add(a, b: integert) is
begin
    c := a + b;
end add;

Tokens:
Token Type      | Lexeme                    | Value
--------------------------------------------------
PROCEDURE       | procedure                 | None
ID              | add                       | None
LPAREN          | (                         | None
ID              | a                         | None
COMMA           | ,                         | None
ID              | b                         | None
COLON           | :                         | None
INTEGERT        | integert                  | None
RPAREN          | )                         | None
IS              | is                        | None
BEGIN           | begin                     | None
ID              | c                         | None
ASSIGN          | :=                        | None
ID              | a                         | None
PLUS            | +                         | None
ID              | b                         | None
SEMICOLON       | ;                         | None
END             | end                       | None
ID              | add                       | None
SEMICOLON       | ;                         | None

Compilation Summary
==================
Lexical Errors: 0
Syntax Errors: 0
Semantic Errors: 0
Total Errors: 0

Compilation completed successfully!

Run another test? (y/n): n
```

## Notes

- The test runner assumes that your driver files accept a test file path as a command-line argument
- If a driver file requires additional arguments, you may need to modify the test runner
- The test runner only looks for .ada files in the test_files directory by default, but this can be configured
- The test runner has a timeout of 30 seconds by default, but this can be configured
- Large test outputs are truncated to prevent overwhelming the console 