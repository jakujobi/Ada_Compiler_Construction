import logging
import os
import sys
import inspect
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------
# Colored Formatter for Console Logging
# --------------------------------------------------------------------
class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter that adds colors to log level names.
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
        super().__init__(fmt, datefmt)
        self.use_color = use_color

    def format(self, record):
        if self.use_color and record.levelname in self.COLOR_CODES:
            record.levelname = f"{self.COLOR_CODES[record.levelname]}{record.levelname}{self.RESET_CODE}"
        return super().format(record)

# --------------------------------------------------------------------
# Logger Singleton Class
# --------------------------------------------------------------------
class Logger:
    """
    Logger is a singleton class that wraps Python's logging module.
    It provides a single point of configuration and sharing of the logger
    instance across the entire application.
    
    Default Configuration:
      - Console log level: DEBUG (messages at DEBUG and above will show)
      - File log level: DEBUG (all messages are captured in the file)
      - Log directory: "logs" (created in the directory of the main script)
      - Log file name: <caller_name>_<timestamp>.log (caller_name is detected automatically)
      - Log format: "%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s"
      - Date format: "%Y-%m-%d %H:%M:%S"
      - Colored output: Enabled
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton: return the existing instance if available.
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
        # Avoid reinitialization if already configured.
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Determine the source name if not provided.
        if source_name is None:
            source_name = self._get_caller_name()
        self.source_name = source_name

        # Create log directory relative to the main script's directory.
        main_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.log_directory = os.path.join(main_dir, log_directory)
        Path(self.log_directory).mkdir(exist_ok=True)

        # Create a log filename: <source_name>_<timestamp>.log
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_filename = os.path.join(self.log_directory, f"{self.source_name}_{timestamp}.log")

        # Create the logger instance.
        self._logger = logging.getLogger("AppLogger")
        self._logger.setLevel(logging.DEBUG)  # Capture all messages; filtering is done by handlers.

        # Clear any existing handlers.
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        # Set default format if not provided.
        if fmt is None:
            fmt = "%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        # Create formatter for console output (colored).
        console_formatter = ColoredFormatter(fmt=fmt, datefmt=datefmt, use_color=use_color)
        # Formatter for file output (no colors).
        file_formatter = logging.Formatter(fmt, datefmt)

        # File handler: logs everything at or above log_level_file.
        file_handler = logging.FileHandler(self.log_filename, encoding="utf-8")
        file_handler.setLevel(log_level_file)
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

        # Console handler: displays messages at or above log_level_console.
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level_console)
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        self._initialized = True
        self._logger.debug(f"Logger initialized. Log file: {self.log_filename}")

    def _get_caller_name(self):
        """
        Inspects the call stack to determine the name of the class (or module)
        that first called the logger.
        """
        import inspect
        stack = inspect.stack()
        # stack[0] is _get_caller_name, [1] is __init__, [2] is the caller.
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
    # Logging method wrappers.
    # ----------------------------------------------------------------
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)

    # ----------------------------------------------------------------
    # Additional Configuration Methods.
    # ----------------------------------------------------------------
    def set_level(self, level, handler_type="both"):
        """
        Change the logging level for console and/or file handlers.
        
        Parameters:
          - level: The log level (e.g., logging.INFO, logging.DEBUG).
          - handler_type: 'console', 'file', or 'both'.
        """
        for handler in self._logger.handlers:
            if handler_type == "both":
                handler.setLevel(level)
            elif handler_type == "console" and isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)
            elif handler_type == "file" and isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
        self._logger.debug(f"Logger level changed to {logging.getLevelName(level)} for {handler_type} handler(s).")

    def help(self):
        """
        Prints help information for the Logger configuration.
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
         Default: "%(asctime)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d - %(funcName)s"
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
