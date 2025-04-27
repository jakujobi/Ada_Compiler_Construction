#!/usr/bin/env python3
# JohnA5b.py
# Author: John Akujobi
# Date: 2025-03-14
# Version: 1.0
"""
Driver program for Assignment 5b: Semantic Analysis Phase

This driver runs:
  1. Lexical Analysis
  2. Syntax Analysis (RDParser)
  3. Semantic Analysis (NewSemanticAnalyzer)
  4. Compilation Summary

Usage:
    python JohnA5b.py <input_file> [output_file]
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Try normal imports, then fallback to source directory for modules
try:
    from jakadac.modules.Driver import BaseDriver  # type: ignore
    from jakadac.modules.Logger import Logger  # type: ignore
    from jakadac.modules.RDParser import RDParser  # type: ignore
    from jakadac.modules.SymTable import SymbolTable  # type: ignore
    from jakadac.modules.NewSemanticAnalyzer import NewSemanticAnalyzer  # type: ignore
except ImportError:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(repo_root)
    from src.jakadac.modules.Driver import BaseDriver
    from src.jakadac.modules.Logger import Logger
    from src.jakadac.modules.RDParser import RDParser
    from src.jakadac.modules.SymTable import SymbolTable
    from src.jakadac.modules.NewSemanticAnalyzer import NewSemanticAnalyzer

class JohnA5b(BaseDriver):
    """
    Driver for semantic analysis (Assignment 5b).
    """
    def __init__(
        self,
        input_file_name: str,
        output_file_name: Optional[str] = None,
        debug: bool = False,
        logger: Optional[Logger] = None
    ):
        super().__init__(input_file_name, output_file_name, debug, logger)
        self.parser: Optional[RDParser] = None
        self.run()

    def run(self) -> None:
        """
        Orchestrate the 3 phases plus summary.
        """
        self.logger.info("Starting Assignment 5b driver.")
        try:
            # Phase 0: Read file
            self.get_source_code_from_file()
            self.print_source_code()

            if not self.source_code:
                self.logger.error("No source code to process.")
                sys.exit(1)

            # Phase 1: Lexical Analysis
            print("\nPhase 1: Lexical Analysis")
            print("-" * 60)
            self.run_lexical()

            # Phase 2: Syntax Analysis
            print("\nPhase 2: Syntax Analysis")
            print("-" * 60)
            success = self.run_syntax(
                stop_on_error=False,
                panic_mode_recover=False,
                build_parse_tree=True
            )
            assert self.parser is not None
            self.syntax_errors = self.parser.errors  # type: ignore
            if success:
                print("Syntax analysis completed successfully")
                self.logger.info("Syntax analysis succeeded.")
            else:
                print(f"Syntax analysis failed with {len(self.syntax_errors)} errors")

            # Phase 3: Semantic Analysis
            print("\nPhase 3: Semantic Analysis")
            print("-" * 60)
            symtab = SymbolTable()
            # Ensure parse tree root is available
            assert hasattr(self.parser, 'parse_tree_root') and self.parser.parse_tree_root is not None, "Parse tree not built"  # type: ignore
            analyzer = NewSemanticAnalyzer(
                symtab,
                self.parser.parse_tree_root,  # type: ignore[arg-type]
                self.lexical_analyzer.defs
            )
            sem_ok = analyzer.analyze()
            self.semantic_errors = analyzer.errors
            if sem_ok:
                print("Semantic analysis completed successfully")
                self.logger.info("Semantic analysis succeeded.")
            else:
                print(f"Semantic analysis failed with {len(self.semantic_errors)} errors")
                if self.debug:
                    for err in self.semantic_errors:
                        print(err)
            # Mark that semantic phase was run
            self.ran_semantic = True

            # Final summary
            self.print_compilation_summary()

        except Exception as e:
            self.logger.critical(f"Unhandled error in driver: {e}")
            if self.debug:
                import traceback; traceback.print_exc()
            sys.exit(1)


def main() -> None:
    """
    Entry point for JohnA5b driver.
    """
    logger = Logger(log_level_console=logging.INFO)
    logger.info("Launching JohnA5b driver.")

    args = sys.argv[1:]
    if len(args) == 2:
        input_file, output_file = args
        JohnA5b(input_file, output_file, logger=logger)
    elif len(args) == 1:
        input_file = args[0]
        JohnA5b(input_file, logger=logger)
    else:
        print("Usage: python JohnA5b.py <input_file> [output_file]")
        sys.exit(1)


if __name__ == "__main__":
    main()
