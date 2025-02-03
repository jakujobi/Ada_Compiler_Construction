# FileHandler.py
# Version: 2.0
# Author: John Akujobi
# Date: 2025-02-1
# Github: https://github.com/jakujobi

"""
/********************************************************************
***  FILE  : FileHandler.py                                       ***
*********************************************************************
***  DESCRIPTION :                                                 ***
***  This program defines a class `FileHandler` that handles      ***
***  various file operations, including finding, opening, and      ***
***  reading files line by line. The class also provides methods   ***
***  for prompting the user to input file paths or use the system  ***
***  file explorer to locate files. The program is designed to     ***
***  work with both command-line arguments and interactive user    ***
***  input.                                                        ***
***  The program then outputs the information as a list of lines   ***
***                                                                ***
***  The `FileHandler` class includes the following methods:      ***
***                                                                ***
***  - process_file(file_name):                                    ***
***      Processes the specified file by finding it, opening it,   ***
***      and reading it line by line. Returns a list of cleaned    ***
***      lines from the file or None if errors occur.              ***
***                                                                ***
***  - process_arg_file(file_name):                                ***
***      Processes the file provided as a command-line argument.   ***
***      Finds, opens, and reads the file.                         ***
***                                                                ***
***  - find_file(file_name):                                       ***
***      Checks if the specified file exists in the same directory ***
***      as the script. If not, prompts the user to input the file ***
***      path or use the system file explorer.                     ***
***                                                                ***
***  - prompt_for_file(file_name):                                 ***
***      Prompts the user to either type the file path or use the  ***
***      system file explorer. Validates the input and returns a   ***
***      valid file path.                                          ***
***                                                                ***
***  - handle_invalid_input(question, retry_limit):                ***
***      Handles invalid inputs with retry logic and displays a    ***
***      message if retries are exhausted.                         ***
***                                                                ***
***  - open_file(file_path):                                       ***
***      Opens the specified file and yields each line using a     ***
***      generator to avoid loading the entire file into memory.   ***
***                                                                ***
***  - read_file(file):                                            ***
***      Reads the file line by line, cleans each line, and        ***
***      returns a list of cleaned lines.                          ***
***                                                                ***
***  - use_system_explorer():                                      ***
***      Opens a system file explorer window using Tkinter for the ***
***      user to select a file. Returns the selected file path.    ***
***                                                                ***
***  - read_line_from_file(line):                                  ***
***      Cleans and processes a single line from the file. Removes ***
***      leading/trailing spaces and everything after '//' to skip ***
***      comments. Skips empty lines.                              ***
***                                                                ***
***  The program also includes error handling to manage common     ***
***  issues such as file not found, permission errors, and invalid ***
***  user inputs.                                                  ***
***                                                                ***
***  USAGE:                                                        ***
***  - To use this program, create an instance of the `FileHandler`***
***    class and call the `process_file` or `process_arg_file`     ***
***    method with the desired file name.                          ***
***                                                                ***
***  - Example:                                                    ***
***      explorer = FileHandler()                                 ***
***      lines = explorer.process_file("example.txt")              ***
***                                                                ***
********************************************************************/
"""

import sys
import os
import logging


try:
    repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(repo_home_path)
    from Modules.Logger import Logger
    logger = Logger()
except ImportError:
    # Revert the path changes if Logger module is not found
    sys.path.remove(repo_home_path)
    
    # Configure a specific logger for this module
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a console handler with a specific format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s"
    )
    console_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(console_handler)

    # Optionally, add a file handler if you want to log to a file as well
    file_handler = logging.FileHandler('filehandler.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# Try to import Tkinter for GUI file explorer. If not available, fallback to manual entry.
try:
    import tkinter as tk
    from tkinter import filedialog
    tkinter_available = True
except ImportError:
    tkinter_available = False


class FileHandler:
    """
    FileHandler class handles file operations such as finding, opening,
    reading, writing, and appending to files. It supports both command-line
    arguments and interactive user input.
    """
    
    def process_file(self, file_name):
        """
        Processes the file by finding it, opening it, and reading it line by line.
        Returns a list of cleaned lines or None if an error occurs.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                logger.error("Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None

            file_generator = self.open_file(file_path)
            if file_generator is None:
                logger.error("Could not open the file '%s'.", file_name)
                print(f"Error: Could not open the file '{file_name}'.")
                return None
            
            return self.read_file(file_generator)
        except FileNotFoundError:
            logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def process_arg_file(self, file_name):
        logger.info("Processing file: %s from argument", file_name)
        file_path = self.find_file(file_name)
        if file_path is None:
            logger.error("Could not find the file '%s'.", file_name)
            print(f"Error: Could not find the file '{file_name}'.")
            return None
        file_generator = self.open_file(file_path)
        # If needed, you could return self.read_file(file_generator)

    def find_file(self, file_name, create_if_missing=False):
        """
        Checks for the file in the main program directory. If not found,
        prompts the user for the file path (or uses the system file explorer).
        """
        main_program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        default_path = os.path.join(main_program_directory, file_name)
        logger.debug("Checking for file at: %s", default_path)
    
        if os.path.isfile(default_path):
            logger.info("Found %s in the main program directory (%s).", file_name, main_program_directory)
            use_found_file = input(f"Do you want to use this {file_name}? (y/n): ").strip().lower()
    
            if use_found_file in {"y", "", "yes"}:
                logger.info("Using %s from main program directory (%s).", file_name, main_program_directory)
                return default_path
            elif use_found_file in {"n", "no"}:
                logger.info("Alright, let's find it manually then.")
            else:
                # Invalid response handling; this remains interactive.
                self.handle_invalid_input("Do you want to use this file?", 5)
        elif create_if_missing:
            try:
                with open(default_path, "w") as file:
                    pass  # Create an empty file
                logger.info("Created a new file: %s", file_name)
                return default_path
            except Exception as e:
                logger.error("Error creating the file '%s': %s", file_name, e)
                print(f"Error creating the file '{file_name}': {e}")
                return None
    
        return self.prompt_for_file(file_name)

    def prompt_for_file(self, file_name):
        """
        Prompts the user to either type the file path or use the system file explorer.
        This method remains interactive.
        """
        retry_limit = 5
        retries = 0

        while True:
            if retries >= retry_limit:
                print(f"\nSeriously? After {retry_limit} attempts, you still can't choose between 1 or 2?")
                choice = input("Do you want to keep trying or end the program? (try/exit): ").strip().lower()

                if choice in ["exit", "e", "n", "no"]:
                    print("\nBruh!\nFine, exiting the program. Goodbye!")
                    sys.exit(1)  # Exit gracefully
                elif choice in ["try", "y", "yes", ""]:
                    print("Alright, let's give it another shot!")
                    retries = 0  # Reset retry count
                else:
                    print("Invalid input. I'll assume you want to keep trying.")
                    retries = 0  # Reset retry count

            # Interactive menu for file selection.
            print("\nFinding Menu:")
            print(f"1. Type the {file_name} file path manually.")
            if tkinter_available:
                print(f"2. Use your system file explorer to locate the {file_name} file.")
            
            choice = input("Choose an option (1 or 2): ").strip()

            if choice == "1":
                file_path = input(f"Enter the full path to {file_name}: ").strip()
                if os.path.isfile(file_path):
                    return file_path
                else:
                    print(f"Error: Invalid typed file path for {file_name}. Please try again.\n"
                          f"Example: c:/Users/username/path_to_project/{file_name}\n")
            elif choice == "2" and tkinter_available:
                try:
                    file_path = self.use_system_explorer()
                    if os.path.isfile(file_path):
                        return file_path
                    else:
                        print(f"Error: Invalid file path for {file_name} from system explorer. Please try again.")
                except Exception as e:
                    print(f"Unexpected Error: {e} occurred while trying to use the system file explorer.")
                    continue  # Try again
            else:
                print("Invalid choice. Please select 1 or 2.")
                retries += 1

    def handle_invalid_input(self, question: str, retry_limit: int = 5):
        """
        Handles invalid inputs with retry logic. This method remains interactive.
        """
        retries = 0
        while retries < retry_limit:
            response = input(f"{question} (y/n): ").strip().lower()
            if response in {"y", "yes", ""}:
                return True
            elif response in {"n", "no"}:
                return False
            else:
                print("Invalid input. Please type 'y' for yes or 'n' for no.")
                retries += 1

        print(f"\n*sigh* \nOkay, you had {retry_limit} chances. I'm moving on without your input.")
        return False

    def open_file(self, file_path):
        """
        Opens the file and yields each line using a generator.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    yield line
        except FileNotFoundError:
            logger.error("Error: %s not found. @ open_file", file_path)
            print(f"Error: {file_path} not found. @ open_file")
        except PermissionError:
            logger.error("Error: Permission denied for %s. @ open_file", file_path)
            print(f"Error: Permission denied for {file_path}. @ open_file")
        except Exception as e:
            logger.error("An unexpected error occurred while opening %s: %s @ open_file", file_path, e)
            print(f"An unexpected error occurred while opening {file_path}: {e} @ open_file")

    def create_new_file_in_main(self, file_name: str, extension: str) -> str:
        """
        Creates a new file in the main program directory.
        """
        main_program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        file_path = os.path.join(main_program_directory, f"{file_name}.{extension}")

        try:
            with open(file_path, "w") as file:
                pass  # Create an empty file
            logger.info("Successfully created the file: %s", file_path)
            return file_path
        except Exception as e:
            logger.error("An error occurred while creating the file '%s': %s", file_path, e)
            print(f"An error occurred while creating the file '{file_path}': {e}")
            return None

    def read_file(self, file):
        """
        Reads the file line by line, cleans each line, and returns a list of cleaned lines.
        """
        lines = []
        for line in file:
            cleaned_line = self.read_line_from_file(line)
            if cleaned_line:
                lines.append(cleaned_line)
        
        if not lines:
            logger.warning("No valid lines found in the file.")
        
        return lines

    def read_file_raw(self, file_name):
        """
        Reads the file without modifying its content.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                logger.error("Error: Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None

            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return lines
        except FileNotFoundError:
            logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def process_file_char_stream(self, file_name):
        """
        Reads the specified file and yields one character at a time.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                logger.error("Error: Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    char = f.read(1)
                    if not char:
                        break
                    yield char
        except FileNotFoundError:
            logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")

    def read_file_as_string(self, file_name):
        """
        Reads the file and returns its contents as a single string.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                logger.error("Error: Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None
            with open(file_path, 'r', encoding='utf-8') as file:
                file_contents = file.read()
            return file_contents
        except FileNotFoundError:
            logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def use_system_explorer(self):
        """
        Opens a system file explorer window using Tkinter for the user to select a file.
        """
        if not tkinter_available:
            return input("Enter the full path to the file: ").strip()

        root = tk.Tk()
        root.withdraw()
        root.update()
        
        file_path = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("All files", "*.*"), ("DAT files", "*.dat"), ("Text files", "*.txt")]
        )
        
        root.destroy()
        
        return file_path if file_path else None

    def read_line_from_file(self, line):
        """
        Cleans a line by removing leading/trailing spaces and everything after '//' (comments).
        """
        line = line.split("//", 1)[0].strip()
        if not line:
            return None
        return line

    def write_file(self, file_name, lines):
        """
        Writes a list of lines to the specified file (creates or overwrites).
        """
        file_path = self.find_file(file_name, create_if_missing=True)
        if not file_path:
            logger.error("Error: Could not create or find the file '%s'.", file_name)
            print(f"Error: Could not create or find the file '{file_name}'.")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                for line in lines:
                    file.write(line + "\n")
            logger.info("Successfully wrote to the file: %s", file_path)
            return True
        except Exception as e:
            logger.error("An error occurred while writing to the file: %s", e)
            print(f"An error occurred while writing to the file: {e}")
            return False

    def append_to_file(self, file_name, lines):
        """
        Appends a list of lines to the specified file (creates if it doesn't exist).
        """
        file_path = self.find_file(file_name, create_if_missing=True)
        if not file_path:
            logger.error("Error: Could not create or find the file '%s'.", file_name)
            print(f"Error: Could not create or find the file '{file_name}'.")
            return False

        try:
            with open(file_path, "a", encoding="utf-8") as file:
                for line in lines:
                    file.write(line + "\n")
            logger.info("Successfully appended to the file: %s", file_path)
            return True
        except Exception as e:
            logger.error("An error occurred while appending to the file: %s", e)
            print(f"An error occurred while appending to the file: {e}")
            return False

    def file_exists(self, file_name):
        """
        Checks if a file exists.
        """
        return os.path.exists(file_name)


# Test main program
if __name__ == "__main__":
    explorer = FileHandler()

    # Check for a command-line argument for the file name.
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "example.txt"  # Default file name

    lines = explorer.process_file(file_name)

    if lines:
        print("\nFile Contents:")
        for line in lines:
            print(line)
    else:
        print("No lines to display.")

    if lines:
        # Test writing to a file.
        output_file = "output_example.txt"
        explorer.write_file(output_file, lines)

        # Test appending to a file.
        append_lines = ["This is an appended line.", "Appending more lines."]
        explorer.append_to_file(output_file, append_lines)
