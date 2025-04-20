import os
import glob
import subprocess

# Path to JohnA5.py relative to this file.
# Assumes the repository structure is maintained.
johnA5_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'Ada_Compiler_Construction', 'A5_Semantic_Analyzer', 'JohnA5.py')

if not os.path.exists(johnA5_path):
    print(f"JohnA5.py not found at {johnA5_path}")
    exit(1)

# Directory containing the current test files (.ada)
test_dir = os.path.abspath(os.path.dirname(__file__))
# Find all test files ending with .ada in the test directory
test_files = glob.glob(os.path.join(test_dir, '*.ada'))

if not test_files:
    print("No test files found in", test_dir)
    exit(1)

print(f"Found {len(test_files)} test file(s).")
# Run JohnA5.py on each test file
for test_file in test_files:
    print(f"\nRunning test: {os.path.basename(test_file)}")
    result = subprocess.run(['python', johnA5_path, test_file],
                            capture_output=True, text=True)
    print("----- STDOUT -----")
    print(result.stdout)
    print("----- STDERR -----")
    print(result.stderr)
    if result.returncode != 0:
        print(f"Test {os.path.basename(test_file)} failed with return code {result.returncode}")
    else:
        print(f"Test {os.path.basename(test_file)} passed.")
