# Logger.py
# Author: John Akujobi
# GitHub: https://github.com/jakujobi/Ada_Compiler_Construction
# Date: 2024-02-01
# Version: 1.0

import logging
import os
import sys
import inspect
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------
# Custom Filter to add caller class information.
# --------------------------------------------------------------------
class CallerFilter(logging.Filter):
    """
    CallerFilter is a custom logging filter that tries to find and attach
    the caller's class name to each log record. It scans the call stack and 
    assigns the first class name it encounters that is not 'Logger'.

    This helps us know which part of our application generated a particular
    log message.
    """
    def filter(self, record):
        try:
            # Iterate through the call stack starting from a higher frame.
            # We skip the first few frames (like the ones inside the logger itself).
            for frame_info in inspect.stack()[8:]:
                # If 'self' exists in the frame's locals, it means we are inside a class method.
                if "self" in frame_info.frame.f_locals:
                    cls = frame_info.frame.f_locals["self"].__class__.__name__
                    # We do not want our Logger class itself to show as the caller.
                    if cls != "Logger":
                        record.caller_class = cls
                        return True
            # If no caller class was found, set it to "None".
            record.caller_class = "None"
        except Exception:
            # In case of any errors, just set the caller class to "None".
            record.caller_class = "None"
        return True

# --------------------------------------------------------------------
# Colored Formatter for Console Logging
# --------------------------------------------------------------------
class ColoredFormatter(logging.Formatter):
    """
    ColoredFormatter is a custom formatter that adds colors to the log level names.
    It helps make the console output more visually distinct so you can quickly spot
    warnings, errors, etc.

    The colors are defined in the COLOR_CODES dictionary.
    """
    COLOR_CODES = {
        'DEBUG': "\033[37m",     # White
        'INFO': "\033[36m",      # Cyan
        'WARNING': "\033[33m",   # Yellow
        'ERROR': "\033[31m",     # Red
        'CRITICAL': "\033[41m"   # Red background
    }
    RESET_CODE = "\033[0m"

    def __init__(self, fmt, datefmt=None, use_color=True):
        """
        Initialize the ColoredFormatter.
        
        Parameters:
          fmt (str): The format string for log messages.
          datefmt (str): The date format string.
          use_color (bool): Whether to add color codes to the level names.
        """
        super().__init__(fmt, datefmt)
        self.use_color = use_color

    def format(self, record):
        """
        Format the log record. If use_color is enabled, wrap the log level name
        in the corresponding ANSI color codes.
        
        Parameters:
          record (LogRecord): The log record to be formatted.
          
        Returns:
          str: The formatted log message.
        """
        if self.use_color and record.levelname in self.COLOR_CODES:
            record.levelname = f"{self.COLOR_CODES[record.levelname]}{record.levelname}{self.RESET_CODE}"
        return super().format(record)

# --------------------------------------------------------------------
# Logger Singleton Class
# --------------------------------------------------------------------
class Logger:
    """
    Logger is a singleton class that wraps Python's built-in logging module.
    It centralizes the configuration and provides a single point for logging 
    throughout the entire application.

    Default Configuration:
      - Console log level: DEBUG (messages at DEBUG level and above will show).
      - File log level: DEBUG (all messages are captured in the log file).
      - Log directory: "logs" (created in the same directory as the main script).
      - Log file name: <caller_name>_<timestamp>.log (caller_name is auto-detected).
      - Log format: 
            "%(asctime)s - %(levelname)s - %(message)s - %(caller_class)s - %(filename)s:%(lineno)d - %(funcName)s"
      - Date format: "%Y-%m-%d %H:%M:%S"
      - Colored output: Enabled for console messages.

    This class is designed so that every part of your application uses the same logger.
    You can adjust the configuration by passing parameters to the Logger constructor.
    """

    _instance = None  # Used to store the single instance of Logger

    def __new__(cls, *args, **kwargs):
        """
        Override __new__ to implement the singleton pattern.
        This ensures that only one instance of Logger exists across the application.
        """
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self,
                 log_level_console=logging.DEBUG,
                 log_level_file=logging.DEBUG,
                 log_directory="logs",
                 source_name=None,
                 fmt=None,
                 datefmt=None,
                 use_color=True):
        """
        Initialize the Logger. This sets up the file and console handlers, the log format,
        and any custom filters (like CallerFilter).

        Parameters:
          log_level_console (int): Log level for console output.
          log_level_file (int): Log level for file output.
          log_directory (str): Directory where log files will be stored.
          source_name (str): A name to use for the log file; if not provided, auto-detected.
          fmt (str): Format string for log messages.
          datefmt (str): Format string for dates.
          use_color (bool): Whether to use colored output for the console.
        """
        # If already initialized, skip reinitialization.
        if hasattr(self, "_initialized") and self._initialized:
            return

        # If no source name is provided, try to detect it automatically.
        if source_name is None:
            source_name = self._get_caller_name()
        self.source_name = source_name

        # Determine the main directory (where the main script is located)
        main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        # Create the log directory if it doesn't exist.
        self.log_directory = os.path.join(main_dir, log_directory)
        Path(self.log_directory).mkdir(exist_ok=True)

        # Create a log filename using the source name and current timestamp.
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_filename = os.path.join(self.log_directory, f"{self.source_name}_{timestamp}.log")

        # Create the underlying logger instance.
        self._logger = logging.getLogger("AppLogger")
        self._logger.setLevel(logging.DEBUG)  # Capture all messages; filtering is handled by handlers.

        # Clear any previously set handlers.
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        # Set default log message format if not provided.
        if fmt is None:
            fmt = "%(asctime)s - %(levelname)s - %(message)s - %(caller_class)s - %(filename)s:%(lineno)d - %(funcName)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        # Create a formatter for the console with color.
        console_formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt, use_color=use_color)
        # Create a formatter for the file (without colors).
        file_formatter = logging.Formatter(fmt, datefmt)

        # File handler: logs all messages to the file.
        file_handler = logging.FileHandler(self.log_filename, encoding="utf-8")
        file_handler.setLevel(log_level_file)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(CallerFilter())
        self._logger.addHandler(file_handler)

        # Console handler: logs messages to the console.
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_console)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(CallerFilter())
        self._logger.addHandler(console_handler)

        self._initialized = True

        # Log that the logger has been initialized.
        self._logger.debug(f"Logger initialized. Log file: {self.log_filename}", stacklevel=3)

    def _get_caller_name(self):
        """
        Inspect the call stack to determine the name of the caller (class or module).
        This is used to generate a log file name.
        
        Returns:
          str: The caller's class name or module name.
        """
        import inspect
        stack = inspect.stack()
        if len(stack) >= 3:
            frame = stack[2]
            if 'self' in frame.frame.f_locals:
                return frame.frame.f_locals["self"].__class__.__name__
            else:
                module = inspect.getmodule(frame.frame)
                if module and hasattr(module, "__name__"):
                    return module.__name__
        return "DefaultLogger"

    # ----------------------------------------------------------------
    # Logging Method Wrappers (with stacklevel adjustment)
    # These methods simply wrap the underlying logger's methods,
    # ensuring that the reported caller info skips our Logger wrapper.
    # ----------------------------------------------------------------
    def debug(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        kwargs.setdefault("stacklevel", 3)
        self._logger.critical(msg, *args, **kwargs)

    def set_level(self, level, handler_type="both"):
        """
        Change the logging level for the console and/or file handlers.

        Parameters:
          level (int): The new log level (e.g., logging.INFO, logging.DEBUG).
          handler_type (str): Which handler(s) to update. Options are 'console', 'file', or 'both'.
        """
        for handler in self._logger.handlers:
            if handler_type == "both":
                handler.setLevel(level)
            elif handler_type == "console" and isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)
            elif handler_type == "file" and isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
        self._logger.debug(f"Logger level changed to {logging.getLevelName(level)} for {handler_type} handler(s).", stacklevel=3)

    def help(self):
        """
        Print help information for configuring the Logger.

        This function prints out a detailed explanation of the Logger configuration
        options and usage examples.
        """
        help_text = """
Logger Configuration Help:
--------------------------
Parameters:
  - log_level_console: Log level for console output (e.g., logging.INFO, logging.DEBUG).
  - log_level_file: Log level for file output.
  - log_directory: Directory to store log files. Default is "logs" (created in the main script's directory).
  - source_name: Name used in the log filename. If not provided, it is auto-detected from the caller.
  - fmt: Format string for log messages.
         Default: "%(asctime)s - %(levelname)s - %(message)s - %(caller_class)s - %(filename)s:%(lineno)d - %(funcName)s"
  - datefmt: Date format string for timestamps.
         Default: "%Y-%m-%d %H:%M:%S"
  - use_color: Enable colored log messages in console output (True/False).

Usage Example:
--------------
    from Logger import Logger
    import logging

    # Create a logger instance (singleton)
    log = Logger(log_level_console=logging.INFO)

    # Log messages:
    log.debug("This is a debug message.")
    log.info("This is an info message.")
    log.warning("This is a warning message.")
    log.error("This is an error message.")
    log.critical("This is a critical message.")

    # Change log level for console output:
    log.set_level(logging.WARNING, handler_type="console")

    # Display help:
    log.help()

Log File Naming:
----------------
  The log file is named as:
      <source_name>_<timestamp>.log
  where <source_name> is auto-detected (or provided) and <timestamp> is the current date/time.
"""
        print(help_text)

###############################################################################
# Full Documentation for the Logger Class
###############################################################################
"""
Class: Logger
-------------
The Logger class is a singleton wrapper around Python’s built-in logging module.
It centralizes logging for your application and allows you to control the log 
output (both on the console and in a file) from a single place.

Key Features:
  - **Singleton Pattern:** Only one Logger instance is created and shared 
    across the entire application.
  - **Custom Formatting:** Supports a custom log format that includes the 
    timestamp, log level, message, the calling class name (using CallerFilter), 
    filename, line number, and function name.
  - **Colored Output:** Uses ColoredFormatter to add colors to console output,
    making it easier to distinguish between log levels.
  - **Flexible Configuration:** You can configure log levels for the console and 
    file, specify a custom log directory, format, date format, and whether to use colors.
  - **Automatic Caller Info:** Uses a CallerFilter to inspect the call stack 
    and attach the caller’s class name to each log record.
  - **Usage Simplicity:** The Logger class is designed to be easy to use. Simply 
    import Logger and call its methods (debug, info, warning, error, critical) to log messages.

Usage:
  1. Import and create a logger instance:
         from Logger import Logger
         logger = Logger(log_level_console=logging.INFO)
  2. Use the logger methods in your code:
         logger.debug("This is a debug message.")
         logger.info("This is an info message.")
  3. Adjust configuration using set_level() or view help() for more info.

This implementation is geared toward making logging robust yet simple to configure,
with detailed information to help you debug and trace through your application.
"""

# End of Logger module
