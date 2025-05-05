#!/usr/bin/env python3
# procedure_registry.py
# Author: AI Assistant
# Date: 2024-05-09
# Version: 1.0
"""
Procedure Registry for ASM Generation.

Maintains a record of all procedures encountered during parsing,
including nested procedures that would be lost when exiting scopes.
"""

from typing import Dict, List, Optional, Any
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

class ProcedureRegistry:
    """
    Registry to track all procedures and their symbols regardless of scope.
    """
    
    def __init__(self):
        """
        Initialize the procedure registry.
        """
        self.procedures = {}  # name -> symbol
        logger.info("Procedure Registry initialized")
    
    def register_procedure(self, name: str, symbol: Any):
        """
        Register a procedure with its symbol.
        
        Args:
            name: The name of the procedure
            symbol: The Symbol object for the procedure
        """
        self.procedures[name] = symbol
        logger.info(f"Registered procedure '{name}' in registry")
    
    def get_procedure(self, name: str) -> Optional[Any]:
        """
        Get a procedure's symbol by name.
        
        Args:
            name: The name of the procedure
            
        Returns:
            The Symbol object if found, None otherwise
        """
        if name in self.procedures:
            logger.debug(f"Found procedure '{name}' in registry")
            return self.procedures[name]
        logger.debug(f"Procedure '{name}' not found in registry")
        return None
    
    def get_all_procedures(self) -> Dict[str, Any]:
        """
        Get all registered procedures.
        
        Returns:
            Dictionary mapping procedure names to their symbols
        """
        return self.procedures.copy()

# Singleton instance
registry = ProcedureRegistry() 