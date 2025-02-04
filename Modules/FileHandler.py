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
***  This module defines a FileHandler class that manages various   ***
***  file operations. It is used by multiple programs to handle     ***
***  tasks such as finding, opening, reading, writing, and appending  ***
***  to files. It supports both command-line file names and interactive***
***  input, including using a GUI file explorer (if Tkinter is available). ***
***                                                                  ***
***  The FileHandler class includes the following methods:         ***
***                                                                  ***
***  - process_file(file_name):                                    ***
***      Finds the file, opens it, reads it line by line, and returns ***
***      a list of cleaned lines. If an error occurs, returns None.  ***
***                                                                  ***
***  - process_arg_file(file_name):                                ***
***      Processes a file provided as a command-line argument.      ***
***                                                                  ***
***  - find_file(file_name, create_if_missing=False):              ***
***      Checks if the file exists in the main program directory.  ***
***      If not found, prompts the user for the file path or lets the ***
***      user use the system file explorer to locate it.            ***
***                                                                  ***
***  - prompt_for_file(file_name):                                 ***
***      Interactively prompts the user to type in a file path or     ***
***      select one via the system file explorer (if available).      ***
***                                                                  ***
***  - handle_invalid_input(question, retry_limit):                ***
***      Handles invalid responses during interactive input with a   ***
***      retry mechanism.                                            ***
***                                                                  ***
***  - open_file(file_path):                                       ***
***      Opens the file in read mode and yields each line one at a   ***
***      time using a generator (so large files aren’t fully loaded).***
***                                                                  ***
***  - read_file(file):                                            ***
***      Reads from a file generator line by line, cleans each line,  ***
***      and returns a list of non-empty, cleaned lines.             ***
***                                                                  ***
***  - read_file_raw(file_name):                                   ***
***      Reads the entire file into a list of raw lines without       ***
***      additional processing.                                      ***
***                                                                  ***
***  - process_file_char_stream(file_name):                        ***
***      Reads the file character by character using a generator.    ***
***                                                                  ***
***  - read_file_as_string(file_name):                             ***
***      Reads the entire file and returns its contents as a single   ***
***      string.                                                     ***
***                                                                  ***
***  - use_system_explorer():                                      ***
***      Opens a system file explorer window using Tkinter (if        ***
***      available) so the user can select a file interactively.       ***
***                                                                  ***
***  - read_line_from_file(line):                                  ***
***      Cleans an individual line by removing extra spaces and any  ***
***      inline comments (everything after '//'). Skips empty lines.   ***
***                                                                  ***
***  - write_file(file_name, lines):                               ***
***      Writes a list of lines to a file (overwriting if it exists).  ***
***                                                                  ***
***  - write_string_to_file(file_name, content):                   ***
***      Writes a single string to a file (overwriting if it exists).  ***
***                                                                  ***
***  - append_to_file(file_name, lines):                           ***
***      Appends a list of lines to a file (creates the file if missing). ***
***                                                                  ***
***  - file_exists(file_name):                                     ***
***      Checks if a file exists at the given path.                  ***
***                                                                  ***
***  USAGE:                                                         ***
***  - Create an instance of FileHandler and call its methods to read, ***
***    write, or process files. For example:                         ***
***                                                                  ***
***      explorer = FileHandler()                                   ***
***      lines = explorer.process_file("example.txt")               ***
***                                                                  ***
********************************************************************/
"""

import sys
import os
import logging

# Set the repository home path for module imports.
repo_home_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_home_path)

from Modules.Logger import Logger

# Try to import Tkinter for GUI file explorer; if not available, fall back to manual input.
try:
    import tkinter as tk
    from tkinter import filedialog
    tkinter_available = True
except ImportError:
    tkinter_available = False


class FileHandler:
    """
    FileHandler is a utility class to handle common file operations.
    
    This class supports:
      - Finding files (by checking the main directory and prompting the user).
      - Reading files line by line or as a whole.
      - Opening files safely using generators to manage memory usage.
      - Writing and appending to files.
      - Using a system file explorer (if Tkinter is available) for file selection.
      
    This class is used by multiple programs, so each method is thoroughly documented.
    """

    def __init__(self):
        """
        Initialize a FileHandler instance.
        
        It sets up a logger for this module so that all operations can be traced.
        """
        self.logger = Logger()
        self.logger.debug("Initializing FileHandler.")

    def process_file(self, file_name):
        """
        Process a file by finding, opening, and reading it line by line.
        
        This method:
          1. Attempts to locate the file using find_file().
          2. Opens the file using open_file() to create a generator.
          3. Reads and cleans each line using read_file().
          
        Parameters:
          file_name (str): The name or path of the file to process.
          
        Returns:
          list[str] or None: A list of cleaned lines from the file, or None if an error occurs.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                self.logger.error("Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None

            file_generator = self.open_file(file_path)
            if file_generator is None:
                self.logger.error("Could not open the file '%s'.", file_name)
                print(f"Error: Could not open the file '{file_name}'.")
                return None
            
            return self.read_file(file_generator)
        except FileNotFoundError:
            self.logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            self.logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def process_arg_file(self, file_name):
        """
        Process a file provided as a command-line argument.
        
        Parameters:
          file_name (str): The name of the file provided in the command line.
          
        Returns:
          None: This function processes the file for side effects (e.g., reading), but does not return the content.
        """
        self.logger.info("Processing file: %s from argument", file_name)
        file_path = self.find_file(file_name)
        if file_path is None:
            self.logger.error("Could not find the file '%s'.", file_name)
            print(f"Error: Could not find the file '{file_name}'.")
            return None
        file_generator = self.open_file(file_path)
        # If needed, you could return self.read_file(file_generator)

    def find_file(self, file_name, create_if_missing=False):
        """
        Checks if the file exists in the main program directory. If not, prompts the user for a path
        or to use the system file explorer.
        
        Parameters:
          file_name (str): The name of the file to locate.
          create_if_missing (bool): If True, attempts to create the file if it does not exist.
          
        Returns:
          str or None: The file path if found or created, otherwise None.
        """
        main_program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        default_path = os.path.join(main_program_directory, file_name)
        self.logger.debug("Checking for file at: %s", default_path)
    
        if os.path.isfile(default_path):
            self.logger.info("Found %s in the main program directory (%s).", file_name, main_program_directory)
            use_found_file = input(f"Do you want to use this {file_name}? (y/n): ").strip().lower()
    
            if use_found_file in {"y", "", "yes"}:
                self.logger.info("Using %s from main program directory (%s).", file_name, main_program_directory)
                return default_path
            elif use_found_file in {"n", "no"}:
                self.logger.info("Alright, let's find it manually then.")
            else:
                self.handle_invalid_input("Do you want to use this file?", 5)
        elif create_if_missing:
            try:
                with open(default_path, "w") as file:
                    pass  # Create an empty file
                self.logger.info("Created a new file: %s", file_name)
                return default_path
            except Exception as e:
                self.logger.error("Error creating the file '%s': %s", file_name, e)
                print(f"Error creating the file '{file_name}': {e}")
                return None
    
        return self.prompt_for_file(file_name)

    def prompt_for_file(self, file_name):
        """
        Prompts the user to type the file path or use the system file explorer to select a file.
        
        Parameters:
          file_name (str): The expected name of the file.
          
        Returns:
          str: A valid file path provided by the user.
        """
        retry_limit = 5
        retries = 0

        while True:
            if retries >= retry_limit:
                print(f"\nSeriously? After {retry_limit} attempts, you still can't choose?")
                choice = input("Do you want to keep trying or exit? (try/exit): ").strip().lower()

                if choice in ["exit", "e", "n", "no"]:
                    print("\nExiting the program. Goodbye!")
                    sys.exit(1)
                elif choice in ["try", "y", "yes", ""]:
                    print("Alright, let's give it another shot!")
                    retries = 0  # Reset retry count
                else:
                    print("Invalid input. I'll assume you want to keep trying.")
                    retries = 0

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
                    print(f"Error: Invalid file path for {file_name}. Please try again.\n")
            elif choice == "2" and tkinter_available:
                try:
                    file_path = self.use_system_explorer()
                    if os.path.isfile(file_path):
                        return file_path
                    else:
                        print(f"Error: Invalid file path from system explorer for {file_name}. Please try again.")
                except Exception as e:
                    print(f"Unexpected Error: {e} occurred while using the system file explorer.")
                    continue
            else:
                print("Invalid choice. Please select 1 or 2.")
                retries += 1

    def handle_invalid_input(self, question: str, retry_limit: int = 5):
        """
        Handles invalid interactive input with a retry mechanism.
        
        Parameters:
          question (str): The question to prompt the user.
          retry_limit (int): The maximum number of retry attempts.
          
        Returns:
          bool: True if the user eventually answers yes, False otherwise.
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

        print(f"\nYou had {retry_limit} chances. Moving on without input.")
        return False

    def open_file(self, file_path):
        """
        Opens the specified file and yields each line one at a time using a generator.
        
        Parameters:
          file_path (str): The path to the file to open.
          
        Yields:
          str: Each line of the file.
          
        This method uses a generator to avoid loading the entire file into memory.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    yield line
        except FileNotFoundError:
            self.logger.error("Error: %s not found. @ open_file", file_path)
            print(f"Error: {file_path} not found. @ open_file")
        except PermissionError:
            self.logger.error("Error: Permission denied for %s. @ open_file", file_path)
            print(f"Error: Permission denied for {file_path}. @ open_file")
        except Exception as e:
            self.logger.error("Unexpected error while opening %s: %s @ open_file", file_path, e)
            print(f"Unexpected error while opening {file_path}: {e} @ open_file")

    def create_new_file_in_main(self, file_name: str, extension: str) -> str:
        """
        Creates a new file in the main program directory.
        
        Parameters:
          file_name (str): The base name for the new file.
          extension (str): The file extension (without the dot).
          
        Returns:
          str: The full path of the newly created file.
        """
        main_program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        file_path = os.path.join(main_program_directory, f"{file_name}.{extension}")

        try:
            with open(file_path, "w") as file:
                pass  # Create an empty file.
            self.logger.info("Successfully created the file: %s", file_path)
            return file_path
        except Exception as e:
            self.logger.error("Error creating file '%s': %s", file_path, e)
            print(f"Error creating file '{file_path}': {e}")
            return None

    def read_file(self, file):
        """
        Reads from a file generator line by line, cleans each line,
        and returns a list of non-empty, cleaned lines.
        
        Parameters:
          file: A generator that yields lines from a file.
          
        Returns:
          list[str]: A list of cleaned lines.
        """
        lines = []
        for line in file:
            cleaned_line = self.read_line_from_file(line)
            if cleaned_line:
                lines.append(cleaned_line)
        
        if not lines:
            self.logger.warning("No valid lines found in the file.")
        
        return lines

    def read_file_raw(self, file_name):
        """
        Reads the entire file into a list of raw lines without any processing.
        
        Parameters:
          file_name (str): The name/path of the file to read.
          
        Returns:
          list[str] or None: A list of raw lines from the file, or None if an error occurs.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                self.logger.error("Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None

            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            return lines
        except FileNotFoundError:
            self.logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            self.logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def process_file_char_stream(self, file_name):
        """
        Reads the specified file and yields one character at a time.
        
        Parameters:
          file_name (str): The file to read.
          
        Yields:
          str: Each character in the file.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                self.logger.error("Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    char = f.read(1)
                    if not char:
                        break
                    yield char
        except FileNotFoundError:
            self.logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            self.logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")

    def read_file_as_string(self, file_name):
        """
        Reads the entire file and returns its content as a single string.
        
        Parameters:
          file_name (str): The file to read.
          
        Returns:
          str or None: The file content as a string, or None if an error occurs.
        """
        try:
            file_path = self.find_file(file_name)
            if file_path is None:
                self.logger.error("Could not find the file '%s'.", file_name)
                print(f"Error: Could not find the file '{file_name}'.")
                return None
            with open(file_path, 'r', encoding='utf-8') as file:
                file_contents = file.read()
            return file_contents
        except FileNotFoundError:
            self.logger.exception("File not found: %s.", file_name)
            print(f"File not found: {file_name}.")
        except Exception as e:
            self.logger.exception("An error occurred: %s", e)
            print(f"An error occurred: {e}")
            return None

    def use_system_explorer(self):
        """
        Opens a system file explorer window using Tkinter so the user can select a file.
        
        Returns:
          str: The selected file path, or prompts for input if Tkinter is unavailable.
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
        Cleans a single line from the file.
        
        It removes leading/trailing whitespace and removes any portion of the line
        that follows a '//' (used here to indicate inline comments). If the resulting
        line is empty, it returns None.
        
        Parameters:
          line (str): The line read from the file.
          
        Returns:
          str or None: The cleaned line, or None if the line is empty.
        """
        # Split the line at '//' and take the part before it, then strip spaces.
        line = line.split("//", 1)[0].strip()
        if not line:
            return None
        return line

    def write_file(self, file_name, lines):
        """
        Writes a list of lines to the specified file, creating or overwriting it.
        
        Parameters:
          file_name (str): The name/path of the file to write to.
          lines (list[str]): A list of lines to write to the file.
          
        Returns:
          bool: True if the operation was successful, False otherwise.
        """
        file_path = self.find_file(file_name, create_if_missing=True)
        if not file_path:
            self.logger.error("Could not create or find the file '%s'.", file_name)
            print(f"Error: Could not create or find the file '{file_name}'.")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                for line in lines:
                    file.write(line + "\n")
            self.logger.info("Successfully wrote to the file: %s", file_path)
            return True
        except Exception as e:
            self.logger.error("An error occurred while writing to the file: %s", e)
            print(f"An error occurred while writing to the file: {e}")
            return False

    def write_string_to_file(self, file_name, content):
        """
        Writes the given string content to the specified file, creating or overwriting it.
        
        Parameters:
          file_name (str): The file name/path to write to.
          content (str): The content to write.
          
        Returns:
          bool: True if writing was successful, False otherwise.
        """
        file_path = self.find_file(file_name, create_if_missing=True)
        if not file_path:
            self.logger.error("Could not create or find the file '%s'.", file_name)
            print(f"Error: Could not create or find the file '{file_name}'.")
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(content)
            self.logger.info("Successfully wrote to the file: %s", file_path)
            return True
        except Exception as e:
            self.logger.error("An error occurred while writing to the file: %s", e)
            print(f"An error occurred while writing to the file: {e}")
            return False

    def append_to_file(self, file_name, lines):
        """
        Appends a list of lines to the specified file, creating the file if it doesn't exist.
        
        Parameters:
          file_name (str): The file to which lines will be appended.
          lines (list[str]): The lines to append.
          
        Returns:
          bool: True if appending was successful, False otherwise.
        """
        file_path = self.find_file(file_name, create_if_missing=True)
        if not file_path:
            self.logger.error("Could not create or find the file '%s'.", file_name)
            print(f"Error: Could not create or find the file '{file_name}'.")
            return False

        try:
            with open(file_path, "a", encoding="utf-8") as file:
                for line in lines:
                    file.write(line + "\n")
            self.logger.info("Successfully appended to the file: %s", file_path)
            return True
        except Exception as e:
            self.logger.error("An error occurred while appending to the file: %s", e)
            print(f"An error occurred while appending to the file: {e}")
            return False

    def file_exists(self, file_name):
        """
        Checks if a file exists at the given file name/path.
        
        Parameters:
          file_name (str): The file name/path to check.
          
        Returns:
          bool: True if the file exists, False otherwise.
        """
        return os.path.exists(file_name)


###############################################################################
# Full Documentation for FileHandler Class
###############################################################################
"""
Class: FileHandler
------------------
The FileHandler class is a comprehensive utility for handling file operations within
the compiler project. It is used by various programs to perform tasks such as:

  - **Finding Files:** It checks the main program directory for a given file. If the file is not found,
    it can prompt the user to manually enter a file path or use a system file explorer.
  
  - **Reading Files:** The class provides methods to:
       * Read the file line by line using generators (e.g., open_file()) to conserve memory.
       * Read the file fully into a string (read_file_as_string()).
       * Read the file into a list of raw or processed lines (read_file() and read_file_raw()).
       * Process a file as a character stream (process_file_char_stream()).
  
  - **Writing and Appending Files:** Methods like write_file(), write_string_to_file(), and append_to_file()
    enable writing or appending data to files, creating the file if necessary.
  
  - **User Interaction:** For cases where the file isn't found automatically, prompt_for_file() and
    handle_invalid_input() provide an interactive mechanism to obtain a valid file path from the user.
  
  - **System File Explorer Integration:** If Tkinter is available, use_system_explorer() allows the user
    to visually select a file.
  
  - **Line Processing:** read_line_from_file() cleans individual lines by removing extra whitespace
    and inline comments.

This class is thoroughly documented so that any programmer, even a beginner, can understand how to
use its methods in various parts of the application.
"""

# End of FileHandler.py
