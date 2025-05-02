# rd_parser_mixins_declarations.py

# Imports (will likely need adjustment)
import sys
from typing import List, Optional, Any, Dict, Union, TYPE_CHECKING, Callable

# Assuming these modules exist in the same directory
from .RDParser import ParseTreeNode # Assuming RDParser has ParseTreeNode
from .Token import Token
from .Logger import Logger # Assuming logger is passed or inherited
from .SymTable import Symbol, EntryType, SymbolTable, SymbolNotFoundError, ParameterMode, VarType, DuplicateSymbolError # Added imports
from .Definitions import Definitions 
from .TypeUtils import TypeUtils
# from .TACGenerator import TACGenerator # TACGenerator not directly used here


# Use TYPE_CHECKING to provide context for self attributes/methods
if TYPE_CHECKING:
    from .RDParser import RDParser
    # If methods unique to RDParserExtExt are called, import it too
    # from .RDParserExtExt import RDParserExtExt 

class DeclarationsMixin:
    """Mixin class containing declaration and argument parsing methods for RDParserExtExt."""

    # --- Type hints for attributes/methods accessed from self --- 
    logger: Logger
    build_parse_tree: bool
    tac_gen: Optional[Any] # Use Any for TACGenerator if not imported directly
    current_token: Optional[Token]
    symbol_table: Optional[SymbolTable]
    defs: Definitions
    current_local_offset: int
    current_param_offset: int
    current_procedure_name: Optional[str]
    
    # Base/Core methods expected on self
    advance: Callable[[], None]
    match_leaf: Callable[[Any, Optional[ParseTreeNode]], Optional[ParseTreeNode]]
    match: Callable[[Any], None] 
    report_error: Callable[[str], None]
    _add_child: Callable[[ParseTreeNode, Optional[ParseTreeNode]], None]
    report_semantic_error: Callable[[str, int, int], None]
    # Methods from other mixins (potentially ExpressionsMixin for constant init)
    parseExpr: Callable[[], Union[ParseTreeNode, str, None]]
    # Methods from this mixin
    parseIdentifierList: Callable[[], Optional[ParseTreeNode]] # Assuming this exists in base/core for tree mode
    parseTypeMark: Callable[[], Optional[ParseTreeNode]] # Assuming this exists in base/core for tree mode
    parseArgList: Callable[[], Optional[ParseTreeNode]] # Assuming this exists in base/core for tree mode

    # --- Declaration Parsing Methods --- 

    def parseDeclarativePart(self):
        """
        DeclarativePart -> ObjectDeclaration | ProcedureDeclaration | ε
        (Handles object decls and nested procedures iteratively)
        """
        node = None 
        if self.build_parse_tree:
            node = ParseTreeNode("DeclarativePart")

        self.logger.debug("Entering parseDeclarativePart")
        declarations_found = False
        # Loop while we see an ID (for object decl) or PROCEDURE keyword
        while self.current_token and self.current_token.token_type in {self.defs.TokenType.ID, self.defs.TokenType.PROCEDURE}:
            declarations_found = True
            child_node: Optional[ParseTreeNode] = None # Node for the parsed item
            
            if self.current_token.token_type == self.defs.TokenType.ID:
                self.logger.debug("Parsing Object Declaration")
                # Call parseObjectDeclaration which handles modes internally
                child_node = self.parseObjectDeclaration() # type: ignore[misc]
            elif self.current_token.token_type == self.defs.TokenType.PROCEDURE:
                 self.logger.debug("Parsing Nested Procedure Declaration")
                 # Call parseProg recursively to handle the nested procedure
                 child_node = self.parseProg() # type: ignore[misc]
            
            # Add the parsed node (object decl or prog) to the tree if building
            if self.build_parse_tree and node and isinstance(child_node, ParseTreeNode):
                 self._add_child(node, child_node)
        
        # Handle epsilon case for tree building
        if not declarations_found and self.build_parse_tree and node:
            self.logger.debug("Parsing DeclarativePart (ε)")
            self._add_child(node, ParseTreeNode("ε"))

        self.logger.debug("Exiting parseDeclarativePart")
        return node

    def parseObjectDeclaration(self):
        """
        ObjectDeclaration -> IdentifierList : [ CONSTANT ] TypeMark [ := Expr ] ;
        Handles tree building, TAC generation, or non-tree parsing.
        Returns ParseTreeNode if building tree, else None.
        """
        node: Optional[ParseTreeNode] = None
        self.logger.debug("Entering parseObjectDeclaration")

        # --- Common Parsing Steps --- 
        id_tokens = self._parseIdentifierListTokens()
        id_names = [t.lexeme for t in id_tokens]
        self.logger.debug(f" Identifiers: {id_names}")
        
        # Use match/match_leaf based on mode inside helpers or here?
        # Let's assume match consumes token correctly regardless of mode if node=None
        self.match(self.defs.TokenType.COLON)

        is_constant = False
        if self.current_token and self.current_token.token_type == self.defs.TokenType.CONSTANT:
            is_constant = True
            self.logger.debug(" Found CONSTANT keyword")
            self.match(self.defs.TokenType.CONSTANT)

        var_type, const_value_from_type = self._parseTypeMarkInfo()
        self.logger.debug(f" Parsed type: {var_type}, Const value from TypeMark: {const_value_from_type}")
        # If const was declared via TypeMark (e.g., CONSTANT := literal), const_value_from_type will be set.
        # This might override later := Expr initialisation for constants.

        initial_value_expr_place: Optional[str] = None
        initial_value_expr_node: Optional[ParseTreeNode] = None
        initial_value_for_symbol: Any = const_value_from_type # Prioritize value from CONSTANT := <val>

        if self.current_token and self.current_token.token_type == self.defs.TokenType.ASSIGN:
            self.logger.debug(" Found initialization assignment (:=)")
            self.match(self.defs.TokenType.ASSIGN)
            
            expr_result = self.parseExpr() # Returns Node or Str or None
            
            if self.tac_gen and isinstance(expr_result, str):
                initial_value_expr_place = expr_result
                self.logger.debug(f" Initializer expression place: {initial_value_expr_place}")
                # Try to get a literal value for symbol table if possible (only for constants)
                if is_constant and initial_value_for_symbol is None:
                     try: initial_value_for_symbol = int(initial_value_expr_place)
                     except (ValueError, TypeError): 
                          try: initial_value_for_symbol = float(initial_value_expr_place)
                          except (ValueError, TypeError): 
                              # If it's not a direct literal, we can't store const value now
                              self.logger.warning(f"Cannot determine compile-time constant value from expression place '{initial_value_expr_place}'")
                              initial_value_for_symbol = None 
            elif self.build_parse_tree and isinstance(expr_result, ParseTreeNode):
                 initial_value_expr_node = expr_result
                 # Value for constant in tree mode might need later analysis
            elif expr_result is not None: # Handle case where parseExpr returns unexpected type
                 self.logger.error(f"parseExpr returned unexpected type {type(expr_result)} in parseObjectDeclaration")

        self.match(self.defs.TokenType.SEMICOLON)

        # --- Mode-Specific Actions (Symbol Insertion / Tree Building) --- 
        if self.build_parse_tree:
             # Construct the node after parsing all parts
             node = ParseTreeNode("ObjectDeclaration")
             # Add children: ID list (need function?), CONSTANT keyword?, TypeMark node?, Init Expr?
             # This part needs rethinking if we use helpers that don't build trees.
             # Option 1: Re-parse slightly for tree (less efficient)
             # Option 2: Helpers return info AND build tree nodes (complex)
             # Option 3: Build node here from collected info (tokens, type, init_node)
             # Let's try Option 3 (Simplified): 
             # Add ID tokens as leaves
             for tk in id_tokens:
                  self._add_child(node, ParseTreeNode(f"ID: {tk.lexeme}", token=tk))
             if is_constant:
                  self._add_child(node, ParseTreeNode("CONSTANT"))
             # Add Type Info (assuming _parseTypeMarkInfo doesn't build tree yet)
             # Need a parseTypeMark() that returns Node
             type_mark_node = ParseTreeNode(f"TypeMark: {var_type.name if var_type else 'Unknown'}")
             self._add_child(node, type_mark_node)
             if initial_value_expr_node:
                  assign_node = ParseTreeNode(":=")
                  self._add_child(assign_node, initial_value_expr_node)
                  self._add_child(node, assign_node)
             # Fallback if tree building is difficult with current helpers
             self.logger.warning("Tree building for ObjectDeclaration is simplified/incomplete.")
             
        if self.symbol_table: # Insert symbols regardless of mode (needed for TAC)
            if var_type is None and not is_constant: # Constants might infer type from value
                self.logger.error(f"Could not determine type for variable identifiers: {id_names}")
                for id_token in id_tokens:
                    self.report_semantic_error(f"Could not determine type for '{id_token.lexeme}'", id_token.line_number, id_token.column_number)
            else:
                size = TypeUtils.get_type_size(var_type) if var_type else 0 # Default size 0 if unknown
                self.logger.debug(f" Size for type {var_type}: {size}")
                
                for id_token in id_tokens:
                    idt_name = id_token.lexeme
                    entry_kind = EntryType.CONSTANT if is_constant else EntryType.VARIABLE
                    
                    sym = Symbol(idt_name, id_token, entry_kind, self.symbol_table.current_depth)
                    
                    success = False
                    if is_constant:
                        # Add specific check for None type before setting constant info
                        if var_type is None:
                             self.logger.error(f"Cannot declare constant '{idt_name}' without a determinable type.")
                             self.report_semantic_error(f"Could not determine type for constant '{idt_name}'", id_token.line_number, id_token.column_number)
                             # success remains False, skip insertion
                        else:
                             self.logger.info(f" Declaring CONSTANT: {idt_name} : {var_type} = {initial_value_for_symbol}")
                             sym.set_constant_info(const_type=var_type, value=initial_value_for_symbol)
                             success = True
                    else: # Variable
                         if var_type is not None:
                            self.logger.info(f" Declaring VARIABLE: {idt_name} : {var_type}")
                            offset = self.current_local_offset
                            sym.set_variable_info(var_type=var_type, offset=offset, size=size)
                            success = True
                            # Update offset only if symbol insertion is likely to succeed (type known)
                            self.current_local_offset -= size 
                            self.logger.debug(f" Updated current_local_offset = {self.current_local_offset}")
                         # Error reported above if var_type is None

                    # Insert into symbol table if info was set successfully
                    if success:
                         try:
                            self.symbol_table.insert(sym)
                            self.logger.debug(f" Inserted symbol: {sym}")
                            # Emit TAC for variable initialization if present (Constants use getPlace)
                            if not is_constant and self.tac_gen and initial_value_expr_place:
                                 target_place = self.tac_gen.getPlace(sym)
                                 self.logger.debug(f" Emitting VARIABLE init TAC: {target_place} = {initial_value_expr_place}")
                                 self.tac_gen.emitAssignment(target_place, initial_value_expr_place)
                         except DuplicateSymbolError as e:
                             self.logger.error(f"Duplicate symbol error: {e}")
                             self.report_semantic_error(str(e), id_token.line_number, id_token.column_number)
                             # If variable failed insert, revert offset change?
                             if not is_constant and var_type is not None:
                                  self.current_local_offset += size # Revert offset subtraction
                                  self.logger.debug(f" Reverted current_local_offset = {self.current_local_offset} due to insert error.")
                         except AttributeError as e:
                              self.logger.error(f"Attribute error during symbol insertion or TAC gen: {e}")

        self.logger.debug("Exiting parseObjectDeclaration")
        return node # Return node only if building tree

    # Helper to parse IdentifierList returning tokens
    def _parseIdentifierListTokens(self) -> List[Token]:
        tokens = []
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
            tokens.append(self.current_token)
            self.advance() # Use advance as we are not building tree here
            while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
                self.advance() # Skip comma
                if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                    tokens.append(self.current_token)
                    self.advance()
                else:
                    self.report_error("Expected identifier after comma in list")
                    break # Avoid infinite loop on error
        else:
             self.report_error("Expected identifier at start of list")
        return tokens

    # Helper to parse TypeMark returning type info (VarType or None for constant)
    # Returns tuple: (Optional[VarType], Optional[Any]) -> (Type, ConstantValue)
    def _parseTypeMarkInfo(self) -> tuple[Optional[VarType], Optional[Any]]:
         var_type: Optional[VarType] = None # Explicitly type hint
         const_value: Optional[Any] = None
         if self.current_token and self.current_token.token_type in {
             self.defs.TokenType.INTEGERT,
             self.defs.TokenType.REALT,
             self.defs.TokenType.CHART,
             self.defs.TokenType.FLOAT # Assuming FLOAT maps to VarType.FLOAT/REAL
         }:
             # Map token type to VarType
             type_lexeme = self.current_token.lexeme.upper()
             # Use direct mapping from Definitions if available, otherwise manual
             if type_lexeme == 'INTEGER': var_type = VarType.INT
             elif type_lexeme in ['REAL', 'FLOAT']: var_type = VarType.FLOAT
             elif type_lexeme == 'CHAR': var_type = VarType.CHAR
             # TODO: Add BOOLEAN etc. if token exists
             self.advance()
         # This helper previously handled CONSTANT := <val>, but that's now parsed
         # in parseObjectDeclaration. This helper just identifies basic types.
         # If no basic type found, report error unless grammar allows other TypeMarks (e.g., subtype idt).
         elif self.current_token and self.current_token.token_type != self.defs.TokenType.ASSIGN and self.current_token.token_type != self.defs.TokenType.SEMICOLON:
              # Allow for other type marks? Subtypes? Access types? For now, assume basic types or error.
              self.report_error(f"Expected a basic type (INTEGER, REAL, CHAR, FLOAT), found '{self.current_token.lexeme}'")
         
         # Return only the type found, constant value is handled by caller
         return var_type, None 

    def parseArgs(self):
        """
        Args -> ( ArgList ) | ε
        Enhanced to calculate and store offsets for parameters during TAC generation.
        """
        node = None
        if self.build_parse_tree:
            node = ParseTreeNode("Args")
            # --- Tree Building Logic --- 
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                # parseArgList needs to build a tree here
                child = self.parseArgList() # Assumes this returns ParseTreeNode
                if isinstance(child, ParseTreeNode): # Check return type
                    self._add_child(node, child)
                else:
                     self.logger.warning("parseArgList did not return ParseTreeNode in tree mode.")
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            else:
                # Epsilon case for tree
                self._add_child(node, ParseTreeNode("ε"))
            # --- End Tree Building ---
            return node # Return node in tree mode

        elif self.tac_gen:
            # --- TAC Generation Logic --- 
            self.logger.debug("Parsing Args (TAC)")
            param_info_list = [] # To store [(name, token, type, mode), ...]
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.advance() # Consume LPAREN
                # Parse using the helper that returns info
                param_info_list = self._parseArgListInfo()
                if not self.current_token or self.current_token.token_type != self.defs.TokenType.RPAREN:
                    self.report_error("Expected ')' after parameter list")
                else:
                    self.advance() # Consume RPAREN

                # --- Semantic Action: Insert Parameter Symbols with Offsets --- 
                if self.symbol_table and self.current_procedure_name:
                    # Use the param offset tracker initialized in parseProg
                    current_param_offset = self.current_param_offset 
                    self.logger.debug(f"Processing {len(param_info_list)} parameters, starting offset: {current_param_offset}")
                    proc_symbol_params = [] # For updating proc symbol later if needed
                    proc_symbol_modes = {}
                    
                    for param_name, param_token, param_type, param_mode in param_info_list:
                        if param_type is None:
                            self.logger.error(f"Skipping parameter '{param_name}' due to unknown type.")
                            self.report_semantic_error(f"Could not determine type for parameter '{param_name}'", param_token.line_number, param_token.column_number)
                            continue

                        param_size = TypeUtils.get_type_size(param_type)
                        param_symbol = Symbol(
                            param_name,
                            param_token,
                            EntryType.PARAMETER,
                            self.symbol_table.current_depth
                        )
                        # Assign offset and update next offset
                        param_symbol.set_variable_info(param_type, current_param_offset, param_size)
                        self.logger.debug(f" Assigning offset {current_param_offset} to param '{param_name}'")
                        # FIXED: Decrement parameter offset instead of incrementing
                        # Parameters should be assigned decreasing offsets (4, 2) rather than (4, 6)
                        current_param_offset -= param_size
                        
                        proc_symbol_params.append(param_symbol) # Store symbol for later?
                        proc_symbol_modes[param_name] = param_mode
                        
                        try:
                            self.symbol_table.insert(param_symbol)
                            self.logger.debug(f" Inserted PARAMETER symbol: {param_symbol}")
                        except DuplicateSymbolError as e:
                            self.report_semantic_error(f"Duplicate parameter name: '{e.name}'", getattr(param_token, 'line_number', -1), getattr(param_token, 'column_number', -1))
                        except Exception as e:
                             self.logger.error(f"Unexpected error inserting parameter symbol {param_name}: {e}")
                             
                    # Update the parser's offset tracker state
                    self.current_param_offset = current_param_offset
                    self.logger.debug(f"Finished processing parameters, next param offset: {self.current_param_offset}")
                    # TODO: Update the main procedure symbol's param_list/modes if necessary?
                # --- End Semantic Action ---
            else:
                # Epsilon case for TAC gen (no parentheses)
                self.logger.debug("Parsing Args (ε TAC)")
            # --- End TAC Generation ---
            return None # No node in TAC mode

        else:
            # --- Non-Tree, Non-TAC Parsing --- 
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.match(self.defs.TokenType.LPAREN)
                self.parseArgList() # Original parser consumes tokens
                self.match(self.defs.TokenType.RPAREN)
            # Epsilon case requires no action
            # --- End Non-Tree, Non-TAC ---
            return None

    # Helper to parse Mode returning ParameterMode enum
    def _parseModeInfo(self) -> ParameterMode:
        mode = ParameterMode.IN # Default mode is IN
        if self.current_token:
            if self.current_token.token_type == self.defs.TokenType.IN:
                mode = ParameterMode.IN
                self.advance()
            elif self.current_token.token_type == self.defs.TokenType.OUT:
                mode = ParameterMode.OUT
                self.advance()
            elif self.current_token.token_type == self.defs.TokenType.INOUT:
                mode = ParameterMode.INOUT
                self.advance()
            # Else: Epsilon case, mode remains IN
        return mode

    # Helper to parse one argument spec: Mode IdentifierList : TypeMark
    # Returns: List of tuples: [(name: str, token: Token, type: VarType, mode: ParameterMode)]
    def _parseOneArgSpecInfo(self) -> List[tuple[str, Token, Optional[VarType], ParameterMode]]:
        arg_info_list = []
        mode = self._parseModeInfo()
        id_tokens = self._parseIdentifierListTokens()
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.COLON:
            self.report_error("Expected ':' after identifier list in parameter specification")
            return arg_info_list # Return empty on error
        self.advance() # Consume COLON

        var_type, const_value = self._parseTypeMarkInfo() # TypeMark determines type
        if const_value is not None:
            # This shouldn't happen if _parseTypeMarkInfo is updated
            self.report_error("Constant value assignment not allowed in parameter specification type mark")

        for id_token in id_tokens:
             # Add tuple (type might be None if _parseTypeMarkInfo failed)
             arg_info_list.append((id_token.lexeme, id_token, var_type, mode))

        return arg_info_list

    # Helper to parse ArgList returning combined info
    def _parseArgListInfo(self) -> List[tuple[str, Token, Optional[VarType], ParameterMode]]:
        all_args_info = []
        if not self.current_token or self.current_token.token_type == self.defs.TokenType.RPAREN:
             # Handle empty ArgList immediately
             return all_args_info
             
        # Parse first spec
        all_args_info.extend(self._parseOneArgSpecInfo())
        # Parse MoreArgs ( ; ArgList )
        while self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
            self.advance() # Consume SEMICOLON
            # Check if another spec follows or if it's just a trailing semicolon before RPAREN
            if self.current_token and self.current_token.token_type != self.defs.TokenType.RPAREN:
                 all_args_info.extend(self._parseOneArgSpecInfo())
            else:
                 # Trailing semicolon might be error depending on strictness
                 if self.current_token and self.current_token.token_type != self.defs.TokenType.RPAREN:
                      self.report_error("Expected parameter specification after ';'")
                 break 
        return all_args_info

    # --- End of Declarations/Args Parsing Methods ---