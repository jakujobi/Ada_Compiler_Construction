# rd_parser_mixins_expressions.py

# Imports (will likely need adjustment)
import sys
from typing import List, Optional, Any, Dict, Union, TYPE_CHECKING, Callable
from .RDParser import ParseTreeNode # Assuming RDParser has ParseTreeNode
from .Token import Token
# from .Definitions import Definitions # Definitions likely accessed via self.defs
from .Logger import Logger # Assuming logger is passed or inherited
from .SymTable import Symbol, EntryType, SymbolTable, SymbolNotFoundError, VarType, DuplicateSymbolError # Assuming access via self.symbol_table
# from .TACGenerator import TACGenerator # Assuming access via self.tac_gen

# Use TYPE_CHECKING to avoid circular imports at runtime if necessary
# if TYPE_CHECKING:
#     from .Definitions import Definitions
#     from .TACGenerator import TACGenerator

# Assuming these modules exist in the same directory
from .Definitions import Definitions 
from .TACGenerator import TACGenerator
from .TypeUtils import TypeUtils # Added TypeUtils

# Use TYPE_CHECKING to provide context for self attributes/methods
if TYPE_CHECKING:
    from .RDParser import RDParser
    # If methods unique to RDParserExtExt are called, import it too
    # from .RDParserExtExt import RDParserExtExt 

class ExpressionsMixin:
    """Mixin class containing expression parsing methods for RDParserExtExt."""

    # Need to declare types for attributes accessed from self
    # These might be inherited from RDParser or set in RDParserExtExt.__init__
    # Add type hints for attributes accessed via self used in these methods
    logger: Logger
    build_parse_tree: bool
    tac_gen: Optional[TACGenerator]
    current_token: Optional[Token]
    symbol_table: Optional[SymbolTable]
    defs: Definitions
    current_procedure_symbol: Optional[Symbol]
    current_procedure_depth: Optional[int]

    # Methods from base class assumed to exist:
    # advance: () -> None
    # match_leaf: (Any, Optional[ParseTreeNode]) -> Optional[ParseTreeNode]
    # report_error: (str) -> None
    # _add_child: (ParseTreeNode, Optional[ParseTreeNode]) -> None
    # report_semantic_error: (str, int, int) -> None # Added this

    # Explicitly declare expected methods from base/core class using Callable
    advance: Callable[[], None]
    match_leaf: Callable[[Any, Optional[ParseTreeNode]], Optional[ParseTreeNode]]
    report_error: Callable[[str], None]
    _add_child: Callable[[ParseTreeNode, Optional[ParseTreeNode]], None]
    report_semantic_error: Callable[[str, int, int], None]
    # These are defined within this mixin, hint for clarity
    # Removing Callable hints for recursive calls as they seem to confuse the linter
    # parseExpr: Callable[[], Union[ParseTreeNode, str, None]]
    # parseRelation: Callable[[], Union[ParseTreeNode, str, None]]
    # parseSimpleExpr: Callable[[], Union[ParseTreeNode, str, None]]
    # parseTerm: Callable[[], Union[ParseTreeNode, str, None]]
    # parseFactor: Callable[[], Union[ParseTreeNode, str, None]]

    def parseExpr(self) -> Union[ParseTreeNode, str, None]:
        """
        Expr -> Relation
        Enhanced to generate TAC and return the place where the result is stored.
        """
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Expr")
            self.logger.debug("Parsing Expr (tree)")
            child = self.parseRelation() # Should return ParseTreeNode
            # Ensure child is a ParseTreeNode before adding
            if isinstance(child, ParseTreeNode):
                self._add_child(node, child)
            else:
                 # Log if child is None or unexpected type
                 if child is None:
                     self.logger.warning("parseRelation returned None in tree mode, expected ParseTreeNode.")
                 else:
                     self.logger.error(f"Type mismatch: Expected ParseTreeNode from parseRelation in tree mode, got {type(child)}.")
            return node
            # --- End Tree Building ---
        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Expr (TAC)")
            # Delegate to parseRelation and return the place (string)
            place = self.parseRelation() # Should return str
            if not isinstance(place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseRelation in TAC mode, got {type(place)}")
                 return "ERROR_PLACE" # Return error placeholder
            return place
            # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Expr (non-tree)")
            self.parseRelation() # Just parse
            return None # Explicitly return None
            # --- End Non-Tree, Non-TAC ---
    
    def parseRelation(self) -> Union[ParseTreeNode, str, None]:
        """
        Relation -> SimpleExpr [ relop SimpleExpr ]
        Enhanced for TAC generation (currently only handles SimpleExpr).
        NOTE: Relational operators are not handled in the provided TAC snippets.
              This implementation only handles the SimpleExpr part.
        """
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Relation")
            self.logger.debug("Parsing Relation (tree)")
            child = self.parseSimpleExpr() # Returns ParseTreeNode
            if isinstance(child, ParseTreeNode):
                self._add_child(node, child)
            else: # Log if None or wrong type
                 if child is None:
                     self.logger.warning("parseSimpleExpr returned None in tree mode, expected ParseTreeNode.")
                 else:
                    self.logger.error(f"Type mismatch: Expected ParseTreeNode from parseSimpleExpr in tree mode, got {type(child)}.")
            # TODO: Add parsing for optional relop SimpleExpr part if needed
            return node
            # --- End Tree Building ---
        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Relation (TAC)")
            # Delegate to parseSimpleExpr and return the place
            place = self.parseSimpleExpr() # Returns str
            if not isinstance(place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseSimpleExpr in TAC mode, got {type(place)}")
                 return "ERROR_PLACE"
            # TODO: Add TAC generation for relational operators if needed
            # Example:
            # if self.current_token and self.current_token.token_type == self.defs.TokenType.RELOP:
            #     op_token = self.current_token
            #     self.advance()
            #     right_place = self.parseSimpleExpr()
            #     result_place = self.tac_gen.newTemp()
            #     # emit conditional jump or boolean result based on op_token.lexeme
            #     # e.g., self.tac_gen.emitIfFalseJump(place op right_place, label)
            #     # or self.tac_gen.emitBinaryOp(map_relop(op_token.lexeme), result_place, place, right_place)
            #     place = result_place # update place to the result of relation
            return place
            # --- End TAC Generation ---
        else:
             # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Relation (non-tree)")
            self.parseSimpleExpr()
            # TODO: Parse optional relop SimpleExpr part
            return None # Explicitly return None
             # --- End Non-Tree, Non-TAC ---
    

    def parseSimpleExpr(self) -> Union[ParseTreeNode, str, None]:
        """
        SimpleExpr -> Term { addopt Term }*
        Enhanced to generate TAC and return the place where the result is stored.
        """
        node = None # Initialize node
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("SimpleExpr")
            self.logger.debug("Parsing SimpleExpr (tree)")
            t = self.parseTerm() # Returns ParseTreeNode
            if isinstance(t, ParseTreeNode):
                 self._add_child(node, t) # Add first term
            else: # Log if None or wrong type
                if t is None:
                    self.logger.warning("parseTerm returned None in tree mode, expected ParseTreeNode for first term.")
                else:
                    self.logger.error(f"Type mismatch: Expected ParseTreeNode for first term in tree mode, got {type(t)}.")
            
            # Handling MoreTerm equivalent iteratively for tree
            while self.current_token and self.is_addopt(self.current_token.token_type):
                 op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                 self._add_child(node, op_node)
                 self.advance() # Consume operator
                 next_t = self.parseTerm() # Returns ParseTreeNode
                 if isinstance(next_t, ParseTreeNode):
                      self._add_child(node, next_t)
                 else:
                      self.logger.error("Expected ParseTreeNode for term after addopt.")
                      break 
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing SimpleExpr (TAC)")
            left_place = self.parseTerm() # Returns str
            if not isinstance(left_place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseTerm in TAC mode, got {type(left_place)}")
                 return "ERROR_PLACE_ADDOPT_TERM"

            # Parse additional terms if they exist
            while self.current_token and self.is_addopt(self.current_token.token_type):
                op_token = self.current_token
                op = op_token.lexeme # Use lexeme for TAC op if it matches (+, -)
                                     # Or map if different (e.g. 'OR' to 'or')
                self.advance()
                right_place = self.parseTerm() # Returns str
                if not isinstance(right_place, str):
                     self.logger.error(f"Type mismatch: Expected str place from parseTerm (right operand) in TAC mode, got {type(right_place)}")
                     # Potentially return an error marker or raise an exception
                     return "ERROR_PLACE_ADDOPT_TERM"
                
                if not self.tac_gen or not self.symbol_table or not hasattr(self, 'current_local_offset') or not hasattr(self, 'defs'):
                     self.logger.error("TAC/SymbolTable/current_local_offset/defs not available for SimpleExpr TAC emission.")
                     return "ERROR_CONTEXT_MISSING_ADDOPT"
                
                temp_name_str = self.tac_gen.newTempName()
                temp_var_type = VarType.INT # Assuming INT for results of +/- expressions
                temp_token_for_symbol = op_token 
                
                temp_depth = self.symbol_table.current_depth
                # temp_size = TypeUtils.get_type_size(temp_var_type, self.defs.TYPE_SIZE_MAP)
                temp_size = 2 # Direct assumption for INT size

                temp_offset = self.current_local_offset
                self.current_local_offset -= temp_size
                
                temp_sym = Symbol(temp_name_str, temp_token_for_symbol, EntryType.VARIABLE, temp_depth)
                temp_sym.set_variable_info(temp_var_type, temp_offset, temp_size)
                try:
                    self.symbol_table.insert(temp_sym)
                    self.logger.info(f"EXPR_MIXIN (SimpleExpr): Inserted temp symbol {temp_sym.name} (type: {temp_var_type.name}, offset: {temp_offset}, size: {temp_size}) at depth {temp_depth}")
                except DuplicateSymbolError as e:
                    self.logger.error(f"EXPR_MIXIN (SimpleExpr): Duplicate symbol error for temp {temp_name_str}: {e}")
                    # Potentially bubble this error up or handle more gracefully
                
                result_place_for_tac = temp_name_str 
                self.tac_gen.emitBinaryOp(op, result_place_for_tac, left_place, right_place)
                left_place = result_place_for_tac # Update left_place for the next iteration

            return left_place # Return the final place
            # --- End TAC Generation ---

        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing SimpleExpr (non-tree)")
            self.parseTerm() # Consume Term
            while self.current_token and self.is_addopt(self.current_token.token_type):
                 self.advance() # Consume operator
                 self.parseTerm() # Consume next Term
            return None # Explicitly return None
            # --- End Non-Tree, Non-TAC ---
    
    def parseTerm(self) -> Union[ParseTreeNode, str, None]:
        """
        Term -> Factor { mulopt Factor }*
        Enhanced to generate TAC and return the place where the result is stored.
        """
        node = None # Initialize node
        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Term")
            self.logger.debug("Parsing Term (tree)")
            f = self.parseFactor() # Returns ParseTreeNode
            if isinstance(f, ParseTreeNode):
                 self._add_child(node, f) # Add first factor
            else: # Log if None or wrong type
                if f is None:
                    self.logger.warning("parseFactor returned None in tree mode, expected ParseTreeNode for first factor.")
                else:
                    self.logger.error(f"Type mismatch: Expected ParseTreeNode for first factor in tree mode, got {type(f)}.")

            # Handling MoreFactor equivalent iteratively for tree
            while self.current_token and self.is_mulopt(self.current_token.token_type):
                 op_node = ParseTreeNode(self.current_token.lexeme, self.current_token)
                 self._add_child(node, op_node)
                 self.advance() # Consume operator
                 next_f = self.parseFactor() # Returns ParseTreeNode
                 if isinstance(next_f, ParseTreeNode):
                      self._add_child(node, next_f)
                 else:
                      self.logger.error("Expected ParseTreeNode for factor after mulopt.")
                      break 
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
             # --- TAC Generation ---
            self.logger.debug("Parsing Term (TAC)")
            left_place = self.parseFactor() # Returns str
            if not isinstance(left_place, str):
                 self.logger.error(f"Type mismatch: Expected str place from parseFactor in TAC mode, got {type(left_place)}")
                 return "ERROR_PLACE_MULOPT_FACTOR"

            # Parse additional factors if they exist
            while self.current_token and self.is_mulopt(self.current_token.token_type):
                op_token = self.current_token
                op = op_token.lexeme # Use lexeme for TAC op if it matches (*, /)
                                     # Or map if different (e.g. 'MOD' to 'mod')
                self.advance()
                right_place = self.parseFactor() # Returns str
                if not isinstance(right_place, str):
                    self.logger.error(f"Type mismatch: Expected str place from parseFactor (right operand) in TAC mode, got {type(right_place)}")
                    return "ERROR_PLACE_MULOPT_FACTOR"

                if not self.tac_gen or not self.symbol_table or not hasattr(self, 'current_local_offset') or not hasattr(self, 'defs'):
                    self.logger.error("TAC/SymbolTable/current_local_offset/defs not available for Term TAC emission.")
                    return "ERROR_CONTEXT_MISSING_MULOPT"

                temp_name_str = self.tac_gen.newTempName()
                temp_var_type = VarType.INT # Assuming INT for results of */ expressions
                temp_token_for_symbol = op_token

                temp_depth = self.symbol_table.current_depth
                # temp_size = TypeUtils.get_type_size(temp_var_type, self.defs.TYPE_SIZE_MAP)
                temp_size = 2 # Direct assumption for INT size
                
                temp_offset = self.current_local_offset
                self.current_local_offset -= temp_size

                temp_sym = Symbol(temp_name_str, temp_token_for_symbol, EntryType.VARIABLE, temp_depth)
                temp_sym.set_variable_info(temp_var_type, temp_offset, temp_size)
                try:
                    self.symbol_table.insert(temp_sym)
                    self.logger.info(f"EXPR_MIXIN (Term): Inserted temp symbol {temp_sym.name} (type: {temp_var_type.name}, offset: {temp_offset}, size: {temp_size}) at depth {temp_depth}")
                except DuplicateSymbolError as e:
                    self.logger.error(f"EXPR_MIXIN (Term): Duplicate symbol error for temp {temp_name_str}: {e}")

                result_place_for_tac = temp_name_str
                self.tac_gen.emitBinaryOp(op, result_place_for_tac, left_place, right_place)
                left_place = result_place_for_tac # Update for next iteration

            return left_place # Return the final place
             # --- End TAC Generation ---
        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Term (non-tree)")
            self.parseFactor() # Consume Factor
            while self.current_token and self.is_mulopt(self.current_token.token_type): # Consume MoreFactor equivalent
                 self.advance() # Consume operator
                 self.parseFactor() # Consume next Factor
            return None # Explicitly return None
            # --- End Non-Tree, Non-TAC ---
    
        
    def parseFactor(self) -> Union[ParseTreeNode, str, None]:
        """
        Factor -> idt | numt | ( Expr ) | not Factor | signopt Factor
        Enhanced to generate TAC and return the place where the result is stored.
        Also performs semantic checking for undeclared variables.
        """
        node = None # Initialize
        place = "ERROR_PLACE" # Default place for TAC

        if self.build_parse_tree:
            # --- Tree Building ---
            node = ParseTreeNode("Factor")
            self.logger.debug("Parsing Factor (tree)")
            
            if not self.current_token:
                self.report_error("Unexpected end of input in Factor")
                return node # Return empty Factor node
                
            token_type = self.current_token.token_type
            
            if token_type == self.defs.TokenType.ID:
                id_token = self.current_token
                self.match_leaf(self.defs.TokenType.ID, node)
                if self.symbol_table:
                    try: 
                        self.symbol_table.lookup(id_token.lexeme)
                    except SymbolNotFoundError:
                        # Ensure proper indentation for the except block content
                        msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                        self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))
            
            elif token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                self.match_leaf(token_type, node)
            
            elif token_type == self.defs.TokenType.LPAREN:
                self.match_leaf(self.defs.TokenType.LPAREN, node)
                child = self.parseExpr() 
                if isinstance(child, ParseTreeNode): self._add_child(node, child)
                self.match_leaf(self.defs.TokenType.RPAREN, node)
            
            elif token_type == self.defs.TokenType.NOT:
                self.match_leaf(self.defs.TokenType.NOT, node)
                child = self.parseFactor() 
                if isinstance(child, ParseTreeNode): self._add_child(node, child)
            
            elif self.is_signopt(token_type):
                self.match_leaf(token_type, node)
                child = self.parseFactor()
                if isinstance(child, ParseTreeNode): self._add_child(node, child)
            
            else:
                self.report_error(f"Expected an identifier, number, '(', 'not', or sign, found {self.current_token.lexeme if self.current_token else 'EOF'}")
            return node
            # --- End Tree Building ---

        elif self.tac_gen:
            # --- TAC Generation ---
            self.logger.debug("Parsing Factor (TAC)")
            if not self.current_token:
                 self.report_error("Unexpected end of input in Factor")
                 return "ERROR_PLACE"
                 
            token_type = self.current_token.token_type
            id_token = self.current_token # Store potential ID token for error reporting

            if token_type == self.defs.TokenType.ID:
                self.advance() # Consume identifier
                if self.symbol_table:
                    try:
                        symbol = self.symbol_table.lookup(id_token.lexeme)
                        # --- TAC Place Calculation --- 
                        if self.tac_gen:
                            # Pass the current procedure depth for context
                            place = self.tac_gen.getPlace(symbol, current_proc_depth=self.current_procedure_depth)
                        else:
                            place = id_token.lexeme # Fallback if no TAC generator
                    except SymbolNotFoundError:
                        msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                        self.report_semantic_error(msg, id_token.line_number, id_token.column_number)
                        place = id_token.lexeme # Use lexeme as placeholder place on error
                else:
                    # No symbol table, assume lexeme is the place (for basic testing)
                    place = id_token.lexeme
                # No return here, place is set

            elif token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                place = self.current_token.lexeme # Literals are their own place
                self.advance()

            elif token_type == self.defs.TokenType.LPAREN:
                self.advance() # Consume LPAREN
                place = self.parseExpr() # Returns str (place)
                if not self.current_token or self.current_token.token_type != self.defs.TokenType.RPAREN:
                     self.report_error("Expected ')'")
                else:
                     self.advance() # Consume RPAREN

            elif token_type == self.defs.TokenType.NOT:
                self.advance() # Consume NOT
                operand_place = self.parseFactor() # Returns str
                if isinstance(operand_place, str):
                     result_place = self.tac_gen.newTemp()
                     self.tac_gen.emitUnaryOp("not", result_place, operand_place)
                     place = result_place
                else:
                     place = "ERROR_PLACE" # Error in operand

            elif self.is_signopt(token_type):
                sign = self.current_token.lexeme
                self.advance() # Consume sign
                operand_place = self.parseFactor() # Returns str

                if isinstance(operand_place, str):
                     # Only generate unary op TAC if operand is not a simple literal
                     # (e.g., avoid _t1 = - 5, just use -5)
                     is_literal = False
                     try:
                          float(operand_place) # Check if it looks like a number
                          is_literal = True
                     except ValueError:
                          is_literal = False
                     
                     if is_literal:
                          place = sign + operand_place # Combine sign and literal
                     elif sign == '+':
                          # Unary plus on non-literal is identity for TAC place
                          place = operand_place
                     else: # Unary minus
                        result_place = self.tac_gen.newTemp()
                        self.tac_gen.emitUnaryOp("-", result_place, operand_place)
                        place = result_place
                else:
                     place = "ERROR_PLACE" # Error in operand

            else:
                self.report_error(f"Expected an identifier, number, '(', 'not', or sign, found {id_token.lexeme}")
                # place remains "ERROR_PLACE"

            return place # Return the place string
            # --- End TAC Generation ---

        else:
            # --- Non-Tree, Non-TAC ---
            self.logger.debug("Parsing Factor (non-tree)")
            if self.current_token and self.current_token.token_type == self.defs.TokenType.ID:
                 id_token = self.current_token # Save for semantic check
                 self.advance() # Use advance in non-tree mode
                 if self.symbol_table: # Optional semantic check
                     try: self.symbol_table.lookup(id_token.lexeme)
                     except SymbolNotFoundError:
                         msg = f"Undeclared variable '{id_token.lexeme}' used in expression"
                         self.report_semantic_error(msg, getattr(id_token,'line_number',-1), getattr(id_token,'column_number',-1))

            elif self.current_token and self.current_token.token_type in {self.defs.TokenType.NUM, self.defs.TokenType.REAL}:
                self.advance()
            
            elif self.current_token and self.current_token.token_type == self.defs.TokenType.LPAREN:
                self.advance()
                self.parseExpr() # Recursive call returns None here
                if self.current_token and self.current_token.token_type == self.defs.TokenType.RPAREN:
                     self.advance()
                else:
                     self.report_error("Expected ')'")
            
            elif self.current_token and self.current_token.token_type == self.defs.TokenType.NOT:
                self.advance()
                self.parseFactor() # Recursive call returns None
            
            elif self.current_token and self.is_signopt(self.current_token.token_type):
                self.advance()
                self.parseFactor() # Recursive call returns None
            
            else:
                 id_token = self.current_token # Get token for error message
                 err_lexeme = id_token.lexeme if id_token else 'EOF'
                 self.report_error(f"Expected an identifier, number, '(', 'not', or sign, found {err_lexeme}")
            
            return None # Return None for non-tree, non-TAC branch
            # --- End Non-Tree, Non-TAC ---
    
    def is_addopt(self, token_type):
        """
        Check if a token type is an addopt operator (+ | - | or)
        """
        # Lexical ADDOP covers + and -, reserved OR covers 'or'
        return token_type in {
            self.defs.TokenType.ADDOP,
            self.defs.TokenType.OR
        }
    
    def is_mulopt(self, token_type):
        """
        Check if a token type is a mulopt operator (* | / | mod | rem | and)
        """
        # Lexical MULOP covers *, /; specific types for mod, rem; reserved AND for 'and'
        return token_type in {
            self.defs.TokenType.MULOP,
            self.defs.TokenType.MOD,
            self.defs.TokenType.REM,
            self.defs.TokenType.AND
        }
    
    def is_signopt(self, token_type):
        """
        Check if a token type is a signopt operator (+ | -)
        """
        # Sign operators are lexed as ADDOP
        return token_type == self.defs.TokenType.ADDOP
    
# --- End of Expression Parsing Methods --- 