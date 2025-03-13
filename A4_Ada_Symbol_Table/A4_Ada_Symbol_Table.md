# Project Requirements
# CSC 446  
### Assignment #4  
**HAMER**  
**DUE: 3-5-25**  

For this assignment you are to write a module that will maintain a symbol table for your compiler. Use the linked implementation of a hash table. The unit should provide the following operations (named as given in assignment):
1. **`insert (lex, token, depth)`** - insert the lexeme, token and depth into a record in the symbol table.
2. **`lookup (lex)`** - lookup uses the lexeme to find the entry and returns a pointer to that entry.
3. **`deleteDepth (depth)`** - delete is passed the depth and deletes all records that are in the table at that depth.
4. **`writeTable (depth)`** - include a procedure that will write out all variables (lexeme only) that are in the table at a specified depth.  
   *[this will be useful for debugging your compiler]*  
5. **`hash (lexeme)`** - *(private)* passed a lexeme and return the location for that lexeme. *(this should be an internal routine only, do not list in the interface section).*

The module should automatically initialize the table to empty and the table itself should be a variable declared in the module.
Store the following information for each record type in the symbol table:
1. **VARIABLE** type of variable (use an enumerated data type), offset (use an integer variable) and size (use an integer variable).
2. **CONSTANT** appropriate fields to store either a real or integer value.
3. **PROCEDURE** size of local variables *(this is the total required for all locals)*, number of parameters, type of each parameter, parameter passing mode of each parameter.

You must use a **union** in to store the information, for each item in the table the fields **token, lexeme, depth and next** will be needed.



---