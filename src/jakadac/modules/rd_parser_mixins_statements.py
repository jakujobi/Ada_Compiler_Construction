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

class StatementsMixin: 
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
    # ADDED type hint for current_procedure_depth from base
    current_procedure_depth: Optional[int]

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
            stmt_node = self.parseStatement() # type: ignore[misc]
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
            child = self.parseStatement() # type: ignore[misc]
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
                child_node = self.parseAssignStat() # type: ignore[misc]
            elif token_type in {self.defs.TokenType.GET, self.defs.TokenType.PUT, self.defs.TokenType.PUTLN}:
                # IOStat
                self.logger.debug(f" Statement starts with '{self.current_token.lexeme}', parsing as IOStat")
                child_node = self.parseIOStat() # type: ignore[misc]
            elif token_type == self.defs.TokenType.NULL:
                # Explicit NULL statement
                self.logger.debug(" Statement is NULL")
                # Need a parseNullStatement or handle here
                if self.build_parse_tree and node:
                     child_node = self.match_leaf(self.defs.TokenType.NULL, node) # Create leaf node
                else:
                     self.match(self.defs.TokenType.NULL) # Just consume
            else:
                self.report_error(f"Expected statement (Identifier, GET, PUT, PUTLN, NULL), found {self.current_token.lexeme}")
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
        Distinguishes assignment from procedure call by looking ahead for '(', ';', or ':='.
        Returns a ParseTreeNode ('AssignStat' or 'ProcCall') if building tree, else None.
        """
        self.logger.debug("Entering parseAssignStat")
        node: Optional[ParseTreeNode] = None
        result_node: Optional[ParseTreeNode] = None # What the function finally returns

        if not self.current_token or self.current_token.token_type != self.defs.TokenType.ID:
            self.report_error(f"Expected identifier at start of assignment/procedure call, found {self.current_token}")
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            return None

        id_token = self.current_token
        
        # Peek ahead to decide the path without consuming ID yet
        next_token_index = self.current_index + 1
        token_after_id = self.tokens[next_token_index] if next_token_index < len(self.tokens) else None

        is_assignment = False
        is_proc_call = False

        if token_after_id:
            if token_after_id.token_type == self.defs.TokenType.ASSIGN:
                 is_assignment = True
                 self.logger.debug(f" Lookahead indicates assignment for '{id_token.lexeme}' (found ':=')")
            elif token_after_id.token_type == self.defs.TokenType.LPAREN or token_after_id.token_type == self.defs.TokenType.SEMICOLON:
                 is_proc_call = True
                 self.logger.debug(f" Lookahead indicates procedure call for '{id_token.lexeme}' (found '{token_after_id.lexeme}')")
            # Else: Could be an error (e.g., ID followed by END), handled below
        else:
            # If ID is the last token, it's likely an error, but treat as non-assignment/non-call for now
            self.logger.warning(f" Identifier '{id_token.lexeme}' is last token, cannot be assignment or standard call.")

        # --- Dispatch based on lookahead --- 
        if is_assignment:
            # --- Handle Assignment --- 
            self.logger.info(f" Parsing as Assignment to: {id_token.lexeme}")
            self.advance() # Consume ID
            # Semantic check (can we assign to this?) - Check before consuming ':=
            target_symbol: Optional[Symbol] = None
            if self.symbol_table:
                try:
                    target_symbol = self.symbol_table.lookup(id_token.lexeme)
                    if target_symbol.entry_type == EntryType.CONSTANT:
                         msg = f"Cannot assign to constant '{id_token.lexeme}'"
                         self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                         target_symbol = None # Prevent TAC emission
                    elif target_symbol.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                         msg = f"Cannot assign to procedure/function '{id_token.lexeme}'"
                         self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                         target_symbol = None # Prevent TAC emission
                except SymbolNotFoundError:
                    msg = f"Undeclared variable '{id_token.lexeme}' used in assignment"
                    self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
                    target_symbol = None # Prevent TAC emission
            
            # Match ':=
            self.match(self.defs.TokenType.ASSIGN) # Use match/match_leaf based on mode? Assume match.
            
            # Parse Expression (returns Node or Place)
            expr_result = self.parseExpr() # type: ignore[misc]
            
            # Build Tree or Emit TAC
            if self.build_parse_tree:
                node = ParseTreeNode("AssignStat")
                self._add_child(node, ParseTreeNode(f"ID: {id_token.lexeme}", token=id_token))
                self._add_child(node, ParseTreeNode(":="))
                if isinstance(expr_result, ParseTreeNode):
                     self._add_child(node, expr_result)
                result_node = node
            elif self.tac_gen and target_symbol and isinstance(expr_result, str):
                 # Use self.current_procedure_depth for context
                 dest_place = self.tac_gen.getPlace(target_symbol, current_proc_depth=self.current_procedure_depth)
                 source_place = expr_result
                 # Handle literal assignment via temporary (Simpler: let TAC gen handle)
                 # is_literal = source_place.isdigit() or (source_place.startswith('-') and source_place[1:].isdigit())
                 # if is_literal:
                 #     temp_place = self.tac_gen.newTemp()
                 #     self.logger.debug(f" Emitting TAC: {temp_place} = {source_place}")
                 #     self.tac_gen.emitAssignment(temp_place, source_place)
                 #     self.logger.debug(f" Emitting TAC: {dest_place} = {temp_place}")
                 #     self.tac_gen.emitAssignment(dest_place, temp_place)
                 # else:
                 self.logger.debug(f" Emitting TAC: {dest_place} = {source_place}")
                 self.tac_gen.emitAssignment(dest_place, source_place)
                 result_node = None # No node in TAC mode
            else:
                 # Log warning if TAC couldn't be generated
                 if self.tac_gen:
                      self.logger.warning(f" Could not emit assignment TAC for '{id_token.lexeme}' (target_symbol={target_symbol}, expr_result type={type(expr_result)}). ")
                 result_node = None
            # --- End Handle Assignment --- 
        
        elif is_proc_call:
            # --- Handle Procedure Call --- 
            self.logger.info(f" Parsing as Procedure Call: {id_token.lexeme}")
            # DO NOT consume ID here, let parseProcCall do it.
            result_node = self.parseProcCall() # type: ignore[misc]
            # --- End Handle Procedure Call ---
        
        else:
            # --- Handle Error --- 
            # Expected :=, (, or ; after ID but found something else or EOF
            expected = "':=', '(', or ';'" 
            found = f"'{token_after_id.lexeme}'" if token_after_id else "end of input"
            self.report_error(f"Expected {expected} after identifier '{id_token.lexeme}', found {found}")
            # Consume the ID and attempt recovery
            self.advance()
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            result_node = None
            # --- End Handle Error ---

        self.logger.debug("Exiting parseAssignStat")
        return result_node

    def parseIOStat(self) -> Optional[ParseTreeNode]:
        """
        IOStat -> GetStat | PutStat | PutLnStat
        GetStat -> GET ( idt )
        PutStat -> PUT ( WriteArg )
        PutLnStat -> PUTLN ( WriteArg )
        WriteArg -> Expr | LITERAL (String literal)
        """
        node: Optional[ParseTreeNode] = None
        if self.build_parse_tree: node = ParseTreeNode("IOStat")
        
        self.logger.debug("Entering parseIOStat")
        if not self.current_token:
             self.report_error("Unexpected end of input in IOStat")
             return node # Or None

        token_type = self.current_token.token_type

        if token_type == self.defs.TokenType.GET:
            self.logger.info("Parsing GET statement")
            # --- Parse GET ---
            get_node: Optional[ParseTreeNode] = None
            if self.build_parse_tree: get_node = ParseTreeNode("GetStat")

            self.match_leaf(self.defs.TokenType.GET, get_node)
            self.match_leaf(self.defs.TokenType.LPAREN, get_node)

            idt_token: Optional[Token] = None
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                idt_token = self.current_token
            self.match_leaf(self.defs.TokenType.ID, get_node) # Handles error reporting

            # --- TAC Generation for GET ---
            if self.tac_gen and idt_token and self.symbol_table:
                 try:
                     target_sym = self.symbol_table.lookup(idt_token.lexeme)
                     # Semantic check: Can we assign to this?
                     if target_sym.entry_type == EntryType.CONSTANT:
                          msg = f"Cannot GET into constant '{idt_token.lexeme}'"
                          self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                     elif target_sym.entry_type in (EntryType.PROCEDURE, EntryType.FUNCTION):
                          msg = f"Cannot GET into procedure/function '{idt_token.lexeme}'"
                          self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                     else:
                          # Use self.current_procedure_depth for context
                          target_place = self.tac_gen.getPlace(target_sym, current_proc_depth=self.current_procedure_depth)
                          self.logger.debug(f" Emitting TAC: read {target_place}")
                          self.tac_gen.emitRead(target_place) # Assume emitRead exists
                 except SymbolNotFoundError:
                     msg = f"Undeclared variable '{idt_token.lexeme}' used in GET statement"
                     self.report_semantic_error(msg, getattr(idt_token,'line_number',-1), getattr(idt_token,'column_number',-1))
                 except AttributeError as e:
                      self.logger.error(f"Attribute error during GET TAC generation: {e}")
            # --- End TAC ---

            self.match_leaf(self.defs.TokenType.RPAREN, get_node)
            if self.build_parse_tree and node and get_node: self._add_child(node, get_node)
            # --- End Parse GET ---

        elif token_type == self.defs.TokenType.PUT:
            self.logger.info("Parsing PUT statement")
            put_node: Optional[ParseTreeNode] = None
            if self.build_parse_tree: put_node = ParseTreeNode("PutStat")

            self.match_leaf(self.defs.TokenType.PUT, put_node)
            self.match_leaf(self.defs.TokenType.LPAREN, put_node)

            # --- Parse WriteArg (Literal or Expression) for PUT ---
            expr_node_put: Optional[ParseTreeNode] = None # Renamed to avoid clash if factored
            expr_place_put: Optional[str] = None
            literal_token_put: Optional[Token] = None

            current_put_token = self.current_token
            if current_put_token and current_put_token.token_type == self.defs.TokenType.LITERAL:
                self.logger.debug("Parsing PUT with string literal")
                literal_token_put = current_put_token
                self.match_leaf(self.defs.TokenType.LITERAL, put_node)
                if self.tac_gen and self.symbol_table and literal_token_put:
                    raw_string = literal_token_put.lexeme
                    if len(raw_string) >= 2 and raw_string.startswith('"') and raw_string.endswith('"'):
                        processed_string = raw_string[1:-1].replace('""', '"')
                        # New string handling logic for PUT
                        label = self.symbol_table.add_string_literal(processed_string)
                        self.tac_gen.add_string_definition(label, processed_string)
                        self.logger.debug(f" Emitting TAC: wrs {label} (string: \"{processed_string}\") for PUT")
                        self.tac_gen.emit_write_string_by_label(label) # Use new method
                    else:
                        self.logger.error(f"Invalid string literal format: {raw_string}")
                        self.report_error(f"Invalid string literal format: {raw_string}")
            else:
                self.logger.debug("Parsing PUT with expression")
                expr_result_put = self.parseExpr()
                if self.build_parse_tree and put_node and isinstance(expr_result_put, ParseTreeNode):
                    expr_node_put = expr_result_put
                    self._add_child(put_node, expr_node_put)
                elif self.tac_gen and isinstance(expr_result_put, str):
                    expr_place_put = expr_result_put
                    self.logger.debug(f" Emitting TAC: write {expr_place_put} for PUT")
                    try:
                        self.tac_gen.emitWrite(expr_place_put)
                    except AttributeError as e:
                        self.logger.error(f"Attribute error during PUT TAC generation: {e}")
                elif self.tac_gen:
                    self.logger.error(f"Could not get TAC place for PUT expression (got type {type(expr_result_put)}).")
                    self.report_error(f"Invalid expression in PUT statement.")
            # --- End Parse WriteArg for PUT ---

            self.match_leaf(self.defs.TokenType.RPAREN, put_node)
            if self.build_parse_tree and node and put_node: self._add_child(node, put_node)

        elif token_type == self.defs.TokenType.PUTLN:
            self.logger.info("Parsing PUTLN statement")
            putln_node: Optional[ParseTreeNode] = None
            if self.build_parse_tree: putln_node = ParseTreeNode("PutLnStat")

            self.match_leaf(self.defs.TokenType.PUTLN, putln_node)

            # Check for parameterless PUTLN; vs PUTLN ( WriteArg )
            if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                # This is PUTLN ( WriteArg )
                self.match_leaf(self.defs.TokenType.LPAREN, putln_node)
                
                # --- Parse WriteArg (Literal or Expression) for PUTLN ---
                expr_node_putln: Optional[ParseTreeNode] = None # Renamed
                expr_place_putln: Optional[str] = None
                literal_token_putln: Optional[Token] = None

                current_putln_token = self.current_token
                if current_putln_token and current_putln_token.token_type == self.defs.TokenType.LITERAL:
                    self.logger.debug("Parsing PUTLN with string literal")
                    literal_token_putln = current_putln_token
                    self.match_leaf(self.defs.TokenType.LITERAL, putln_node)
                    if self.tac_gen and self.symbol_table and literal_token_putln:
                        raw_string = literal_token_putln.lexeme
                        if len(raw_string) >= 2 and raw_string.startswith('"') and raw_string.endswith('"'):
                            processed_string = raw_string[1:-1].replace('""', '"')
                            # New string handling logic for PUTLN
                            label = self.symbol_table.add_string_literal(processed_string)
                            self.tac_gen.add_string_definition(label, processed_string)
                            self.logger.debug(f" Emitting TAC: wrs {label} (string: \"{processed_string}\") for PUTLN")
                            self.tac_gen.emit_write_string_by_label(label) # Use new method
                        else:
                            self.logger.error(f"Invalid string literal format: {raw_string}")
                            self.report_error(f"Invalid string literal format: {raw_string}")
                else:
                    self.logger.debug("Parsing PUTLN with expression")
                    expr_result_putln = self.parseExpr()
                    if self.build_parse_tree and putln_node and isinstance(expr_result_putln, ParseTreeNode):
                        expr_node_putln = expr_result_putln
                        self._add_child(putln_node, expr_node_putln)
                    elif self.tac_gen and isinstance(expr_result_putln, str):
                        expr_place_putln = expr_result_putln
                        self.logger.debug(f" Emitting TAC: write {expr_place_putln} for PUTLN")
                        try:
                            self.tac_gen.emitWrite(expr_place_putln)
                        except AttributeError as e:
                            self.logger.error(f"Attribute error during PUTLN expression TAC generation: {e}")
                    elif self.tac_gen:
                        self.logger.error(f"Could not get TAC place for PUTLN expression (got type {type(expr_result_putln)}).")
                        self.report_error(f"Invalid expression in PUTLN statement.")
                # --- End Parse WriteArg for PUTLN ---
                
                self.match_leaf(self.defs.TokenType.RPAREN, putln_node)

                # After argument, emit newline for PUTLN(arg)
                if self.tac_gen:
                    self.logger.debug(" Emitting TAC: wrln after PUTLN(arg)")
                    try:
                        self.tac_gen.emitNewLine()
                    except AttributeError as e:
                        self.logger.error(f"Attribute error during PUTLN(arg) newline TAC generation: {e}")
            else:
                # This is parameterless PUTLN; (semicolon handled by caller of parseStatement)
                self.logger.debug("Parsing parameterless PUTLN;")
                if self.build_parse_tree and putln_node:
                    # Optionally add a node to indicate it's parameterless
                    # For example: self._add_child(putln_node, ParseTreeNode("Parameterless")) 
                    pass 
                if self.tac_gen:
                    self.logger.debug(" Emitting TAC: wrln for PUTLN;")
                    try:
                        self.tac_gen.emitNewLine()
                    except AttributeError as e:
                        self.logger.error(f"Attribute error during PUTLN; newline TAC generation: {e}")
        
            if self.build_parse_tree and node and putln_node: self._add_child(node, putln_node)
    
        else: # This 'else' corresponds to the main if/elif for GET/PUT/PUTLN
            # Handle potential empty IOStat or error if grammar requires GET/PUT/PUTLN
            self.report_error(f"Expected GET, PUT, or PUTLN, found {self.current_token.lexeme if self.current_token else 'EOF'}")
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            # pass # 'pass' is not needed here as report_error and panic_recovery are called
        self.logger.debug("Exiting parseIOStat")
        return node # Return IOStat node if building tree, else None


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
        ProcCall -> idt [ ( Params ) ]
        Handles procedure calls, including zero-argument calls (e.g., `proc;`)
        and calls with parameters (e.g., `proc(a, b);`).
        Handles tree building or TAC generation.
        """
        self.logger.debug("Entering parseProcCall")
        result_node: Optional[ParseTreeNode] = None # Final node returned
        node: Optional[ParseTreeNode] = None # Node for tree building
        proc_name_token: Optional[Token] = None # Store matched ID token
        proc_name = "<unknown>"

        # 1. Match the Procedure Identifier
        if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
             proc_name_token = self.current_token
             proc_name = proc_name_token.lexeme
             self.logger.debug(f" Procedure call target: {proc_name}")
             # Match ID - Use match_leaf for tree mode, advance otherwise
             if self.build_parse_tree:
                 node = ParseTreeNode("ProcCall") # Create node for tree mode
                 self.match_leaf(self.defs.TokenType.ID, node)
             else:
                 self.advance() # Just consume in non-tree modes
        else:
            self.report_error(f"Expected procedure identifier, found {self.current_token}")
            self.panic_recovery({self.defs.TokenType.SEMICOLON, self.defs.TokenType.END})
            return None # Cannot proceed without identifier
            
        # --- Semantic Check: Lookup Procedure --- 
        proc_sym: Optional[Symbol] = None
        try:
            if not self.symbol_table:
                 raise SymbolNotFoundError("Symbol table not available.")
            proc_sym = self.symbol_table.lookup(proc_name)
            if proc_sym.entry_type != EntryType.PROCEDURE:
                raise SymbolNotFoundError(f"'{proc_name}' is not a procedure.")
            self.logger.debug(f" Found procedure symbol: {proc_sym}")
        except SymbolNotFoundError as e:
            self.logger.error(f"Procedure call error: {e}")
            if proc_name_token: # Report error context if token available
                 self.report_semantic_error(str(e), proc_name_token.line_number, proc_name_token.column_number)
            # Even if proc not found, try to parse potential params to maintain syntax
            proc_sym = None 
        # --- End Semantic Check ---
            
        # 2. Handle Optional Parentheses and Parameters
        has_parentheses = False
        parsed_params: Union[List[str], ParseTreeNode, List] = [] # Type depends on mode
        
        if self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
            has_parentheses = True
            self.logger.debug(" Found '(', parsing parameters.")
            # Match LPAREN
            self.match_leaf(self.defs.TokenType.LPAREN, node) # match_leaf safe if node=None
            
            # Parse Parameters
            parsed_params = self.parseParams() # type: ignore[misc]
                
            # Match RPAREN
            self.match_leaf(self.defs.TokenType.RPAREN, node)
            
            # Add Params node to tree if building
            if self.build_parse_tree and node and isinstance(parsed_params, ParseTreeNode):
                 self._add_child(node, parsed_params)

        else:
            # No parentheses found - implies zero-argument call (like `one;`)
            self.logger.debug(" No '(' found, assuming zero-argument call.")
            # parsed_params remains empty list

        # --- Semantic Check: Parameter Count/Types --- 
        formal_param_list = []
        formal_param_modes = {}
        if proc_sym: # Only check if procedure was found
             formal_param_list = proc_sym.param_list if proc_sym.param_list else []
             formal_param_modes = proc_sym.param_modes if proc_sym.param_modes else {}
        
        expected_params = len(formal_param_list)
        actual_params_count = 0
        actual_param_places: List[str] = [] # Specifically for TAC

        if self.tac_gen and isinstance(parsed_params, list):
            actual_param_places = parsed_params # List[str] from parseParams (TAC mode)
            actual_params_count = len(actual_param_places)
        elif self.build_parse_tree and isinstance(parsed_params, ParseTreeNode):
            # Estimate count for tree mode if needed (less critical)
            actual_params_count = len(parsed_params.children) # Approximation
        # Else: Non-tree/non-TAC or error in parseParams, count remains 0
        
        self.logger.debug(f" Parameter count check: Expected={expected_params}, Actual={actual_params_count}")
        if proc_sym and expected_params != actual_params_count:
             mismatch_msg = f"Parameter count mismatch for procedure '{proc_name}'. Expected {expected_params}, got {actual_params_count}."
             self.logger.error(mismatch_msg)
             if proc_name_token: # Check token exists for context
                  self.report_semantic_error(mismatch_msg, proc_name_token.line_number, proc_name_token.column_number)
        # TODO: Add type checking logic here if required, comparing actual_param_places/nodes with formal_param_list types.

        # --- TAC Generation --- 
        if self.tac_gen and proc_sym: # Only emit if procedure known
             try:
                 # Push parameters (if any)
                 if actual_params_count > 0 and len(actual_param_places) == len(formal_param_list): # Ensure lists align
                      self.logger.info(f" Emitting Param Pushes for {proc_sym.name}")
                      # Iterate in reverse for standard stack push order (last param first)
                      for i in range(actual_params_count - 1, -1, -1):
                          actual_place = actual_param_places[i]
                          formal_param_symbol = formal_param_list[i] # Safe index
                          # Default to IN mode if not found (shouldn't happen with proper setup)
                          param_mode = formal_param_modes.get(formal_param_symbol.name, ParameterMode.IN)

                          push_operand = actual_place # Default
                          # --- Determine if push operand needs adjustment (e.g., for globals) ---
                          # Note: Previous code attempted lookup, but push should generally use the
                          # computed place (could be var name, temp, or offset like _BP-X)
                          # Let TACGenerator handle how places are used.
                          # if self.symbol_table and isinstance(actual_place, str):
                          #      try:
                          #          source_symbol = self.symbol_table.lookup(actual_place)
                          #          # Check if symbol is global/outermost? This check might be fragile.
                          #          # if source_symbol.depth == 1: # If param is global/outermost
                          #          #      push_operand = source_symbol.name
                          #          #      self.logger.debug(f" Push operand potentially adjusted to: {push_operand}")
                          #      except SymbolNotFoundError:
                          #          pass # Literal or temporary, use actual_place
                          # --- End adjustment check ---

                          self.logger.info(f"  Pushing Param {i+1}/{actual_params_count}: {push_operand} (Mode: {param_mode.name})")
                          # Pass the mode to emitPush
                          self.tac_gen.emitPush(push_operand, param_mode)

                 elif actual_params_count > 0: # Mismatch case, log warning
                      self.logger.warning("Skipping param pushes due to count mismatch.")

                 # Emit call instruction
                 self.logger.info(f" Emitting Call: {proc_name}")
                 self.tac_gen.emitCall(proc_name)

                 # --- Handle return value for FUNCTION calls (if implemented) ---
                 # if proc_sym.entry_type == EntryType.FUNCTION:
                 #     return_place = self.tac_gen.newTemp()
                 #     self.logger.info(f" Emitting POP for function return value into {return_place}")
                 #     self.tac_gen.emitPop(return_place) # Assuming emitPop exists
                 #     # The function result is now in return_place
                 #     # This would likely be handled in parseFactor for function calls

             except AttributeError as ae:
                  self.logger.error(f"Attribute error during TAC generation for proc call: {ae}")
        # --- End TAC Generation ---

        self.logger.debug("Exiting parseProcCall")
        # Return node if tree building, otherwise None
        return node if self.build_parse_tree else None 