# ErrorHandler Module

import logging
import re



class ErrorHandler:
    def __init__(self):
        self.errors = []
        
        self.warnings = []

    def add_error(self, error_message: str, line_number: int, column_number: int):
        self.errors.append((error_message, line_number, column_number))
        
    def add_warning(self, warning_message: str, line_number: int, column_number: int):
        self.warnings.append((warning_message, line_number, column_number))
        
    def print_errors(self):
        for error in self.errors:
            print(f"Error: {error[0]} at line {error[1]}, column {error[2]}")

    def print_warnings(self):
        for warning in self.warnings:
            print(f"Warning: {warning[0]} at line {warning[1]}, column {warning[2]}")

    def is_string_empty(self, text: str) -> bool:
        """
        Checks if the provided string is empty.
        """
        if len(text) == 0:
            logging.warning("The string is empty.")
            return True
        return False

    def is_end_of_file(self, current_position: int, file_length: int) -> bool:
        """
        Checks if the current position is at or beyond the end of the file.
        """
        if current_position >= file_length:
            logging.warning("Reached the end of the file.")
            return True

    def is_string_only_whitespace(self, text: str) -> bool:
        """
        Checks if the provided string contains only whitespace.
        log if the string contains only whitespace.
        """
        if text.isspace():
            logging.warning("The string contains only whitespace.")
            return True
        return False