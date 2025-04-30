# rd_parser_mixins_statements.py

# Imports (will likely need adjustment)
import sys
from typing import List, Optional, Any, Dict, Union, TYPE_CHECKING, Callable

# Assuming these modules exist in the same directory
from .RDParser import ParseTreeNode # Assuming RDParser has ParseTreeNode
from .Token import Token
from .Logger import Logger # Assuming logger is passed or inherited
from .SymTable import Symbol, EntryType, SymbolTable, SymbolNotFoundError, ParameterMode, VarType # Added ParameterMode, VarType
# Import needed classes directly
from .Definitions import Definitions 
from .TACGenerator import TACGenerator


# Use TYPE_CHECKING to provide context for self attributes/methods
if TYPE_CHECKING:
    from .RDParser import RDParser
    # If methods unique to RDParserExtExt are called, import it too
    from .RDParserExtExt import RDParserExtExt 
    # Import Expression methods if called directly (e.g., parseExpr)
    from .rd_parser_mixins_expressions import ExpressionsMixin 
    # Hint the type of self for mixins
    SelfType = RDParserExtExt
else:
    # At runtime, SelfType can be generic object if RDParserExtExt is not fully defined yet
    # This helps avoid runtime circular dependency errors while aiding static analysis.
    SelfType = object

class StatementsMixin(SelfType): # Hint self type for linter
    """Mixin class containing statement parsing methods for RDParserExtExt."""

    # --- Type hints for attributes/methods accessed from self --- 
    logger: Logger
    build_parse_tree: bool
    tac_gen: Optional[TACGenerator]
    current_token: Optional[Token]
    symbol_table: Optional[SymbolTable]
    defs: Definitions
    current_index: int # Used for lookahead save/restore
    tokens: List[Token] # ADDED: Explicitly declare tokens attribute for linter
    
    # Base/Core methods expected on self (signatures inferred via TYPE_CHECKING)
    advance: Callable[[], None]
    match_leaf: Callable[[Any, Optional[ParseTreeNode]], Optional[ParseTreeNode]]
    match: Callable[[Any], None] # Used in non-tree mode
    report_error: Callable[[str], None]
    panic_recovery: Callable[[set], None] # CORRECTED: Use panic_recovery, not panic_mode_recover
    _add_child: Callable[[ParseTreeNode, Optional[ParseTreeNode]], None]
    _peek: Callable[[int], Optional[Token]] # Used for lookahead
    report_semantic_error: Callable[[str, int, int], None]
    # Methods from other mixins
    parseExpr: Callable[[], Union[ParseTreeNode, str, None]] # From ExpressionsMixin
    # Methods defined in this mixin
    parseStatement: Callable[[], Optional[ParseTreeNode]]
    parseAssignStat: Callable[[], Optional[ParseTreeNode]]
    parseProcCall: Callable[[], Optional[ParseTreeNode]]
    parseParams: Callable[[], Union[ParseTreeNode, List[str]]]
    parseIOStat: Callable[[], Optional[ParseTreeNode]]

    # --- Statement Parsing Methods --- 

    def parseSeqOfStatements(self):
        """
        SeqOfStatements -> { Statement ; }*
        Iteratively parse zero or more statements terminated by semicolons until END.
        """
        if self.build_parse_tree:
            node = ParseTreeNode("SeqOfStatements")
        else:
            node = None

        self.logger.debug("Entering SeqOfStatements")
        count = 0
        while self.current_token and self.current_token.token_type != self.defs.TokenType.END:
            count += 1
            self.logger.debug(f" Parsing statement #{count}")
            stmt_node = self.parseStatement()
            if self.build_parse_tree and node is not None:
                 # Ensure stmt_node is a ParseTreeNode before adding
                 if isinstance(stmt_node, ParseTreeNode):
                     self._add_child(node, stmt_node)
                 else:
                     # Log error if statement parsing didn't return a node in tree mode
                     self.logger.error(f"parseStatement did not return a ParseTreeNode in tree mode (got {type(stmt_node)}).")
            
            # Consume trailing semicolon if present, else break to avoid hang
            if self.current_token and self.current_token.token_type == self.defs.TokenType.SEMICOLON:
                self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            else:
                # If END is next, it's okay. Otherwise, it's a missing semicolon.
                if self.current_token and self.current_token.token_type != self.defs.TokenType.END:
                     self.report_error(f"Expected ';' after statement, found {self.current_token.lexeme if self.current_token else 'EOF'}")
                break # Stop processing sequence if semicolon missing or END reached
        self.logger.debug(f"Exiting SeqOfStatements after {count} statements")
        return node if self.build_parse_tree else None
    
    def parseStatTail(self):
        """
        StatTail -> Statement ; StatTail | ε
        (Note: This recursive structure might be less efficient than the iterative parseSeqOfStatements)
        """
        node = None
        if self.build_parse_tree:
            node = ParseTreeNode("StatTail")
        
        self.logger.debug("Parsing StatTail")
        
        # Check if we have another statement (lookahead needed to distinguish from epsilon)
        # Simple check: if not END or EOF, assume a statement follows
        if self.current_token and self.current_token.token_type not in {self.defs.TokenType.END, self.defs.TokenType.EOF}:
            # Parse the statement
            child = self.parseStatement()
            if self.build_parse_tree and node and isinstance(child, ParseTreeNode):
                self._add_child(node, child)
            
            # Match semicolon
            self.match_leaf(self.defs.TokenType.SEMICOLON, node)
            
            # Parse the rest of statements (StatTail)
            tail_child = self.parseStatTail()
            if self.build_parse_tree and node and isinstance(tail_child, ParseTreeNode):
                 # Avoid adding empty epsilon tails if possible for cleaner trees
                 if not (len(tail_child.children) == 1 and tail_child.children[0].name == "ε"): 
                     self._add_child(node, tail_child)
        else:
            # End of statements (ε)
            if self.build_parse_tree and node is not None:
                self._add_child(node, ParseTreeNode("ε"))
        
        return node
    
    def parseStatement(self):
        """
        Statement -> AssignStat | IOStat | NULL
        Updated to handle NULL statement.
        """
        node: Optional[ParseTreeNode] = None # Initialize node for return type consistency
        child_node: Optional[ParseTreeNode] = None
        
        self.logger.debug("Entering parseStatement")
        if self.build_parse_tree:
            node = ParseTreeNode("Statement")

        if self.current_token:
            token_type = self.current_token.token_type
            # Lookahead for assignment or IO statement or NULL
            if token_type == self.defs.TokenType.ID:
                # Could be AssignStat (assignment or procedure call)
                self.logger.debug(f" Statement starts with ID ('{self.current_token.lexeme}'), parsing as AssignStat/ProcCall")
                child_node = self.parseAssignStat()
            elif token_type == self.defs.TokenType.GET or token_type == self.defs.TokenType.PUT:
                # IOStat
                self.logger.debug(f" Statement starts with '{self.current_token.lexeme}', parsing as IOStat")
                child_node = self.parseIOStat()
            elif token_type == self.defs.TokenType.NULL:
                # Explicit NULL statement
                self.logger.debug(" Statement is NULL")
                # Need a parseNullStatement or handle here
                if self.build_parse_tree and node:
                     child_node = self.match_leaf(self.defs.TokenType.NULL, node) # Create leaf node
                else:
                     self.match(self.defs.TokenType.NULL) # Just consume
            else:
                self.report_error(f"Expected statement (Identifier, GET, PUT, NULL), found {self.current_token.lexeme}")
                self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
                child_node = None
            
            # Add child only if tree building is active and child exists
            if self.build_parse_tree and node and isinstance(child_node, ParseTreeNode):
                self._add_child(node, child_node)
        else:
            self.report_error("Expected statement, found end of input")
            child_node = None

        self.logger.debug("Exiting parseStatement")
        return node # Return top-level Statement node if tree building, else None
    
    def parseAssignStat(self) -> Optional[ParseTreeNode]:
        """
        AssignStat -> idt := Expr | ProcCall
        Handles tree building (simplified) or TAC generation.
        Distinguishes assignment from procedure call by looking ahead for '('.
        Returns a ParseTreeNode ('AssignStat' or 'ProcCall') if building tree, else None.
        """
        self.logger.debug("Entering parseAssignStat")
        node: Optional[ParseTreeNode] = None
        result_node: Optional[ParseTreeNode] = None # What the function finally returns

        # Peek ahead to decide the path without consuming ID yet
        if not self.current_token or self.current_token.token_type != self.defs.TokenType.ID:
            self.report_error(f"Expected identifier at start of assignment/procedure call, found {self.current_token}")
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            return None

        id_token = self.current_token
        # Check if there's a next token and if it's LPAREN
        next_token_index = self.current_index + 1
        next_token = self.tokens[next_token_index] if next_token_index < len(self.tokens) else None
        is_proc_call = next_token and next_token.token_type == self.defs.TokenType.LPAREN

        if self.build_parse_tree:
            # --- Tree Building --- 
            if is_proc_call:
                self.logger.info(f" Building parse tree for Procedure Call: {id_token.lexeme}")
                result_node = self.parseProcCall() # parseProcCall should handle tree building
            else:
                self.logger.info(f" Building parse tree for Assignment: {id_token.lexeme}")
                node = ParseTreeNode("AssignStat")
                self.match_leaf(self.defs.TokenType.ID, node) # Consumes ID
                # Optional Semantic check for tree mode
                if self.symbol_table:
                    try: 
                         # Make sure symbol_table is not None before lookup
                         if self.symbol_table:
                              self.symbol_table.lookup(id_token.lexeme)
                    except SymbolNotFoundError:
                        msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                        self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                
                self.match_leaf(self.defs.TokenType.ASSIGN, node) # Consumes :=
                expr_node = self.parseExpr() # Returns ParseTreeNode
                if isinstance(expr_node, ParseTreeNode):
                     self._add_child(node, expr_node)
                result_node = node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation --- 
            if is_proc_call:
                self.logger.info(f" Parsing as Procedure Call (TAC): {id_token.lexeme}")
                _ = self.parseProcCall() # Returns None in TAC mode
            else:
                self.logger.info(f" Parsing as Assignment (TAC) to: {id_token.lexeme}")
                self.advance() # Consume ID (we know it's an ID)
                dest_place = "ERROR_PLACE"
                if self.symbol_table:
                    try:
                        symbol = self.symbol_table.lookup(id_token.lexeme)
                        if symbol.entry_type == EntryType.CONSTANT:
                            msg = f"Cannot assign to constant '{id_token.lexeme}'"
                            self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                        elif symbol.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                             msg = f"Cannot assign to procedure/function '{id_token.lexeme}'"
                             self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                        else:
                             if self.tac_gen: # Check tac_gen exists
                                 dest_place = self.tac_gen.getPlace(symbol)
                    except SymbolNotFoundError:
                        msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                        self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                        dest_place = id_token.lexeme
                else:
                    dest_place = id_token.lexeme

                # Match := 
                if self.current_token and self.current_token.token_type == self.defs.TokenType.ASSIGN:
                     self.advance()
                else:
                     self.report_error("Expected ':=' for assignment statement")

                # Parse Expression
                source_place = self.parseExpr() # Returns str
                if isinstance(source_place, str) and dest_place != "ERROR_PLACE" and self.tac_gen:
                    # Check if source_place is a literal (basic check, might need refinement for floats/etc.)
                    is_literal = source_place.isdigit() or (source_place.startswith('-') and source_place[1:].isdigit())
                    if is_literal:
                        # Assign literal to temporary first
                        temp_place = self.tac_gen.newTemp()
                        self.logger.debug(f" Emitting TAC: {temp_place} = {source_place}")
                        self.tac_gen.emitAssignment(temp_place, source_place)
                        # Assign temporary to destination
                        self.logger.debug(f" Emitting TAC: {dest_place} = {temp_place}")
                        self.tac_gen.emitAssignment(dest_place, temp_place)
                    else:
                        # Assign non-literal (variable or temp) directly
                        self.logger.debug(f" Emitting TAC: {dest_place} = {source_place}")
                        self.tac_gen.emitAssignment(dest_place, source_place)
                else:
                     self.logger.warning(f" Could not emit assignment TAC for '{id_token.lexeme}' due to missing place(s) or generator.")
                result_node = None # No node returned in TAC mode
            # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC --- 
            # Consume based on lookahead
            if is_proc_call:
                 self.logger.debug(f"Parsing ProcCall (non-tree): {id_token.lexeme}")
                 _ = self.parseProcCall() # Consumes tokens
            else:
                 self.logger.debug(f"Parsing AssignStat (non-tree): {id_token.lexeme}")
                 self.match(self.defs.TokenType.ID)
                 if self.symbol_table: # Optional semantic check
                     try: 
                          # Make sure symbol_table is not None
                          if self.symbol_table:
                               self.symbol_table.lookup(id_token.lexeme)
                     except SymbolNotFoundError:
                         msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                         self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                 self.match(self.defs.TokenType.ASSIGN)
                 _ = self.parseExpr() # Consumes expression tokens
            result_node = None
            # --- End Non-Tree, Non-TAC ---
        
        self.logger.debug("Exiting parseAssignStat")
        return result_node

    def parseIOStat(self) -> Optional[ParseTreeNode]:
        """
        IOStat -> GET ( idt ) | PUT ( Expr )
        (Assuming modified grammar based on logging added earlier)
        """
        node: Optional[ParseTreeNode] = None
        if self.build_parse_tree:
            node = ParseTreeNode("IOStat")
        
        self.logger.debug("Entering parseIOStat")
        if self.current_token and self.current_token.token_type == self.defs.TokenType.GET:
            self.logger.info("Parsing GET statement")
            self.match_leaf(self.defs.TokenType.GET, node)
            self.match_leaf(self.defs.TokenType.LPAREN, node)
            
            idt_token: Optional[Token] = None
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                idt_token = self.current_token
            # Call match_leaf even if token is None or wrong type, it will handle error reporting
            self.match_leaf(self.defs.TokenType.ID, node) 
            
            # --- TAC Generation for GET ---
            if self.tac_gen and idt_token and self.symbol_table:
                 try:
                     target_sym = self.symbol_table.lookup(idt_token.lexeme)
                     # TODO: Check if assignable (not constant/procedure)
                     if target_sym.entry_type == EntryType.CONSTANT:
                          msg = f"Cannot GET into constant '{idt_token.lexeme}'"
                          self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                     elif target_sym.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                          msg = f"Cannot GET into procedure/function '{idt_token.lexeme}'"
                          self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                     else:
                          target_place = self.tac_gen.getPlace(target_sym)
                          self.logger.debug(f" Emitting TAC: read {target_place}")
                          # Check if emitRead method exists before calling
                          if hasattr(self.tac_gen, 'emitRead'):
                              self.tac_gen.emitRead(target_place)
                          else:
                              self.logger.error("TAC Generator does not have emitRead method.")
                 except SymbolNotFoundError:
                     msg = f"Undeclared variable '{idt_token.lexeme}' used in GET statement"
                     self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                 except AttributeError as e:
                      self.logger.error(f"Attribute error during GET TAC generation: {e}") # Catch potential None errors
            # --- End TAC --- 
            
            self.match_leaf(self.defs.TokenType.RPAREN, node)
            
        elif self.current_token and self.current_token.token_type == self.defs.TokenType.PUT:
            self.logger.info("Parsing PUT statement")
            self.match_leaf(self.defs.TokenType.PUT, node)
            self.match_leaf(self.defs.TokenType.LPAREN, node)
            
            # Parse expression (returns Node or str)
            expr_result = self.parseExpr()
            if self.build_parse_tree and node and isinstance(expr_result, ParseTreeNode):
                self._add_child(node, expr_result)
                
            # --- TAC Generation for PUT --- 
            if self.tac_gen and isinstance(expr_result, str):
                 source_place = expr_result
                 self.logger.debug(f" Emitting TAC: write {source_place}")
                 try:
                      # Check if emitWrite method exists
                      if hasattr(self.tac_gen, 'emitWrite'):
                           self.tac_gen.emitWrite(source_place)
                      else:
                           self.logger.error("TAC Generator does not have emitWrite method.")
                 except AttributeError as e:
                      self.logger.error(f"Attribute error during PUT TAC generation: {e}") # Catch None errors
            elif self.tac_gen and not isinstance(expr_result, str):
                 self.logger.error(f"Could not get TAC place for PUT expression (got type {type(expr_result)}).")
            # --- End TAC --- 
                 
            self.match_leaf(self.defs.TokenType.RPAREN, node)
        else:
            # Handle potential empty IOStat or error if grammar requires GET/PUT
            self.report_error(f"Expected GET or PUT, found {self.current_token.lexeme if self.current_token else 'EOF'}")
            # self.panic_mode_recover({...}) # Optional recovery
            pass 
        self.logger.debug("Exiting parseIOStat")
        return node # Return node if building tree, else None (implicitly)


    def parseParams(self) -> Union[ParseTreeNode, List[str]]:
        """
        Params -> Expr { , Expr }* | ε
        Parse actual parameters in a procedure call.
        Returns a list of places (str) if tac_gen is True,
        or a ParseTreeNode if build_parse_tree is True.
        """
        self.logger.debug("Entering parseParams")
        
        if self.build_parse_tree:
            # --- Parse Tree Mode ---
            node = ParseTreeNode("Params")
            # Check for empty parameter list (next token is RPAREN)
            if self.current_token and self.current_token.token_type == self.defs.TokenType.RPAREN:
                self.logger.debug("Exiting parseParams (empty list, tree mode)")
                # Add epsilon for clarity?
                # self._add_child(node, ParseTreeNode("ε")) 
                return node

            # Parse the first parameter expression
            expr_node = self.parseExpr()
            if isinstance(expr_node, ParseTreeNode): # Check type
                 self._add_child(node, expr_node)
            else:
                 self.report_error("Expected expression for parameter")
                 # Add error node?
                 # self._add_child(node, ParseTreeNode("ERROR_PARAM"))

            # Parse subsequent parameters separated by commas
            while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
                self.advance() # Consume comma
                expr_node = self.parseExpr()
                if isinstance(expr_node, ParseTreeNode):
                     self._add_child(node, expr_node)
                else:
                     self.report_error("Expected expression after comma for parameter")
                     # self._add_child(node, ParseTreeNode("ERROR_PARAM"))
                     break 

            self.logger.debug(f"Exiting parseParams (tree mode)")
            return node
            # --- End Parse Tree Mode ---
        
        elif self.tac_gen:
            # --- TAC Mode ---
            param_places = []
            # Check for empty parameter list (next token is RPAREN)
            if self.current_token and self.current_token.token_type == self.defs.TokenType.RPAREN:
                self.logger.debug("Exiting parseParams (empty list, TAC mode)")
                return param_places

            # Parse the first parameter expression
            place = self.parseExpr() # Should return str
            if isinstance(place, str):
                 param_places.append(place)
            else:
                 self.report_error("Expected expression for parameter")
                 param_places.append("ERROR_PARAM_PLACE") # Add placeholder on error

            # Parse subsequent parameters separated by commas
            while self.current_token and self.current_token.token_type == self.defs.TokenType.COMMA:
                self.advance() # Consume comma
                place = self.parseExpr()
                if isinstance(place, str):
                     param_places.append(place)
                else:
                     self.report_error("Expected expression after comma for parameter")
                     param_places.append("ERROR_PARAM_PLACE") # Add placeholder
                     break # Avoid potential infinite loop

            self.logger.debug(f"Exiting parseParams, places: {param_places} (TAC mode)")
            return param_places
            # --- End TAC Mode ---
        else:
            # Fallback/Error case: Not building tree or generating TAC?
            self.logger.warning("parseParams called without build_parse_tree or tac_gen enabled. Consuming tokens.")
            while self.current_token and self.current_token.token_type not in {self.defs.TokenType.RPAREN, self.defs.TokenType.SEMICOLON, self.defs.TokenType.END, self.defs.TokenType.EOF}:
                 self.advance()
            return [] # Return empty list


    def parseProcCall(self) -> Optional[ParseTreeNode]:
        """
        ProcCall -> idt ( Params )
        Implementation of procedure call parsing with TAC generation or Parse Tree building.
        """
        self.logger.debug("Entering parseProcCall")
        proc_name = "<unknown>"
        result_node: Optional[ParseTreeNode] = None # Initialize result_node
        node: Optional[ParseTreeNode] = None # Node for tree building
        proc_name_token: Optional[Token] = None # Store matched ID token

        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
             proc_name_token = self.current_token # Store the token
             proc_name = proc_name_token.lexeme
             self.logger.debug(f" Procedure call target: {proc_name}")

             # --- Branch based on mode (Tree or TAC or Other) ---
             if self.build_parse_tree:
                  # --- Parse Tree Mode --- 
                 node = ParseTreeNode("ProcCall")
                 # Match ID and add leaf to this node
                 self.match_leaf(self.defs.TokenType.ID, node)
                 
                 # Match LPAREN
                 self.match_leaf(self.defs.TokenType.LPAREN, node)
                 
                 # Parse Params (should return ParseTreeNode)
                 params_node = self.parseParams()
                 if isinstance(params_node, ParseTreeNode):
                      self._add_child(node, params_node)
                 else: # Handle error or unexpected return from parseParams
                      self.logger.warning("parseParams did not return a ParseTreeNode in tree mode.")
                      self._add_child(node, ParseTreeNode("Params_Error"))
                 
                 # Match RPAREN
                 self.match_leaf(self.defs.TokenType.RPAREN, node)
                 result_node = node # Set result_node to the built tree
                 # --- End Parse Tree Mode ---

             elif self.tac_gen:
                 # --- TAC Generation --- 
                 self.advance() # Consume ID (already captured in proc_name_token)
                 
                 # Check and Consume LPAREN
                 if not self.current_token or self.current_token.token_type != self.defs.TokenType.LPAREN:
                      self.report_error(f"Expected '(' after procedure name '{proc_name}'")
                      # Attempt recovery? For now, assume error stops TAC gen for this call.
                      # We might need to consume until RPAREN or SEMICOLON here
                      self.panic_recovery({self.defs.TokenType.RPAREN, self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
                      return None # Return None as call is invalid
                 self.advance() # Consume LPAREN
                 
                 # Look up procedure symbol
                 proc_sym: Optional[Symbol] = None
                 try:
                     if not self.symbol_table:
                          raise SymbolNotFoundError("Symbol table not available.")
                     proc_sym = self.symbol_table.lookup(proc_name)
                     if proc_sym.entry_type != EntryType.PROCEDURE:
                         raise SymbolNotFoundError(f"'{proc_name}' is not a procedure.")
                     
                     self.logger.debug(f" Found procedure symbol: {proc_sym}")
                     
                     # Parse actual parameters and get their places
                     parsed_params = self.parseParams() # Returns List[str] in TAC mode
                     # Type check result rigorously
                     if not isinstance(parsed_params, list):
                          self.logger.error("parseParams did not return List[str] in TAC mode!")
                          actual_param_places = [] # Use empty list on error
                     else:
                          actual_param_places: List[str] = parsed_params
                     self.logger.debug(f" Actual parameter places: {actual_param_places}")
                     
                     # Check parameter count
                     formal_param_list = proc_sym.param_list if proc_sym.param_list else []
                     formal_param_modes = proc_sym.param_modes if proc_sym.param_modes else {}
                     expected_params = len(formal_param_list)
                     actual_params = len(actual_param_places)
                     
                     self.logger.debug(f" Parameter count check: Expected={expected_params}, Actual={actual_params}")
                     if expected_params != actual_params:
                         mismatch_msg = f"Parameter count mismatch for procedure '{proc_name}'. Expected {expected_params}, got {actual_params}."
                         self.logger.error(mismatch_msg)
                         if proc_name_token: # Check token exists
                              self.report_semantic_error(mismatch_msg, proc_name_token.line_number, proc_name_token.column_number)
                     # Removed the 'else:' here - push/call should happen even if count mismatches, 
                     # allowing semantic error to be reported but attempting TAC generation.
                     # This matches behavior for undeclared variables etc.
                     
                     # Prepare for TAC emission: Push parameters
                     if self.tac_gen and proc_sym and actual_param_places:
                         self.logger.info(f" Emitting TAC for procedure call: {proc_sym.name}")
                         # Iterate through ACTUAL parameters parsed (actual_param_places) 
                         # and corresponding FORMAL parameter symbols (formal_param_list - already checked for None)
                         if len(actual_param_places) == len(formal_param_list): # Check against known-good list
                             for i, actual_place in enumerate(actual_param_places):
                                 formal_param_symbol = formal_param_list[i] # Safe to index
                                 # Use formal_param_modes (known-good dict) and corrected default
                                 param_mode = formal_param_modes.get(formal_param_symbol.name, ParameterMode.IN) 
                                 
                                 # --- MODIFIED PUSH LOGIC --- 
                                 push_operand = actual_place # Default
                                 if self.symbol_table and isinstance(actual_place, str): # Check if actual_place is a string first
                                      try:
                                           source_symbol = self.symbol_table.lookup(actual_place)
                                           if source_symbol.depth == 1: 
                                                push_operand = source_symbol.name
                                                self.logger.debug(f" Push operand is outermost variable: {push_operand}")
                                      except SymbolNotFoundError:
                                           pass # It's a literal or temporary
                                      # Removed AttributeError handler as we checked isinstance(actual_place, str)
                                          
                                 # Emit push/param instruction
                                 self.logger.info(f" Emitting Param Push: {push_operand} (mode: {param_mode})")
                                 # Use 'push' instead of 'param' based on exp_test75.tac
                                 self.tac_gen.emitPush(push_operand, param_mode) 
                                 # --- END MODIFIED PUSH LOGIC ---
                         else:
                             # Log internal error if lengths still mismatch despite earlier check (shouldn't happen)
                             self.logger.error("Internal error: Mismatch between actual and formal param count during TAC push.")

                         # Emit call instruction - Corrected signature
                         self.tac_gen.emitCall(proc_sym.name)
                         # --- End TAC Generation ---
                         
                 except SymbolNotFoundError as e:
                     self.logger.error(f"Procedure call error: {e}")
                     if proc_name_token: # Check token exists for error reporting context
                          self.report_semantic_error(str(e), proc_name_token.line_number, proc_name_token.column_number)
                     # Consume remaining params even if proc not found
                     _ = self.parseParams()
                 except AttributeError as ae:
                      # Catch errors accessing tac_gen or symbol_table if None
                      self.logger.error(f"Attribute error during TAC generation for proc call: {ae}")
                      _ = self.parseParams() # Consume params

                 # Consume RPAREN
                 if self.current_token and self.current_token.token_type == self.defs.TokenType.RPAREN:
                      self.advance()
                 else:
                      self.report_error(f"Expected ')' after parameters for procedure call '{proc_name}'")
                 result_node = None # No node in TAC mode
                 # --- End TAC Generation ---

             else:
                 # --- Non-Tree, Non-TAC Mode --- 
                 self.logger.warning("parseProcCall invoked without TAC or Tree mode. Consuming tokens.")
                 self.advance() # Consume ID
                 self.match(self.defs.TokenType.LPAREN)
                 # Consume tokens until RPAREN
                 while self.current_token and self.current_token.token_type not in {self.defs.TokenType.RPAREN, self.defs.TokenType.EOF, self.defs.TokenType.SEMICOLON}:
                      self.logger.debug(f" Consuming token inside (): {self.current_token.lexeme}")
                      self.advance()
                 self.match(self.defs.TokenType.RPAREN)
                 result_node = None
                 # --- End Non-Tree, Non-TAC Mode ---
        else:
            # This case should be caught by parseStatement or parseAssignStat before calling parseProcCall
            # If called directly, handle error.
            self.report_error(f"Expected procedure identifier, found {self.current_token}")
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            result_node = None
            
        self.logger.debug("Exiting parseProcCall")
        return result_node 