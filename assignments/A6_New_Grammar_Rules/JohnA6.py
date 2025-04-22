#!/usr/bin/env python3
# pyright: reportMissingImports=false
# JohnA6.py
# Author: John Akujobi
# Date: 2025-04-02
# Version: 1.0
"""
Driver program for Assignment A6: New Grammar Rules

This driver runs:
  1. Lexical Analysis
  2. Syntax Analysis using the Extended RDParser

Usage:
    python JohnA6.py <input_file> [output_file]
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Try normal imports, then fallback to source directory
try:
    from jakadac.modules.Driver import BaseDriver  # type: ignore[import]
    from jakadac.modules.Logger import Logger      # type: ignore[import]
except ImportError:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    src_root = os.path.join(repo_root, "src")
    sys.path.append(src_root)
    from jakadac.modules.Driver import BaseDriver 
    from jakadac.modules.Logger import Logger     

class JohnA6(BaseDriver):
    """
    Driver for Assignment A6: New Grammar Rules.
    """
    def __init__(
        self,
        input_file_name: str,
        output_file_name: Optional[str] = None,
        debug: bool = False,
        logger: Optional[Logger] = None
    ):
        # Enable extended parser for grammar rules
        super().__init__(input_file_name, output_file_name, debug, logger=logger, use_extended_parser=True)
        self.run()

    def run(self) -> None:
        """
        Orchestrate lexical and extended syntax analysis.
        """
        self.logger.info("Starting Assignment A6 driver.")
        try:
            # Phase 0: Read input
            self.get_source_code_from_file()
            self.print_source_code()

            if not self.source_code:
                self.logger.error("No source code to process.")
                sys.exit(1)

            # Phase 1: Lexical Analysis
            print("\nPhase 1: Lexical Analysis")
            print("-" * 60)
            self.run_lexical()

            # Phase 2: Syntax Analysis (Extended)
            print("\nPhase 2: Syntax Analysis (Extended)")
            print("-" * 60)
            success = self.run_syntax(
                stop_on_error=False,
                panic_mode_recover=False,
                build_parse_tree=True
            )
            if success:
                print("Syntax analysis completed successfully")
                self.logger.info("Extended syntax analysis succeeded.")
            else:
                print(f"Syntax analysis failed with {len(self.syntax_errors)} errors")

            # Final summary
            self.print_compilation_summary()

        except Exception as e:
            self.logger.critical(f"Unhandled error in driver: {e}")
            if self.debug:
                import traceback; traceback.print_exc()
            sys.exit(1)


def main() -> None:
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Launching JohnA6 driver.")

    args = sys.argv[1:]
    if len(args) == 2:
        input_file, output_file = args
        JohnA6(input_file, output_file, logger=logger)
    elif len(args) == 1:
        input_file = args[0]
        JohnA6(input_file, logger=logger)
    else:
        print("Usage: python JohnA6.py <input_file> [output_file]")
        sys.exit(1)

if __name__ == '__main__':
    main()
