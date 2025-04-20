CSC 446

ASSIGN #5 

HAMER

DUE: 03-26-25

## Requirement Description
Add the appropriate semantic actions to your parser to insert all constants, variables and procedures into your symbol table.  For constants you will have to set either the value or valuer field as returned by your lexical analyzer.  Variables will require the type, size and current offset of the new variable.  The first variable at a given depth will be at offset 0.  Integers have size 2, characters have size 1 and float has size 4.  Update the offset field by the size of the new variable after inserting the variable.  Procedures will require that you keep track of the size of all local variables and the size of formal parameters, the number, type, and passing mode of all formal parameters.  In all three cases the field’s lexeme, token and depth are required.

When processing a procedure you must also insert all formal parameters into the symbol table at the appropriate depth along with their type.

Your parser must also reject multiple declarations of the same name at the same depth.
ex.  `num, num2, num:integer;`

The second occurrence of num would be a multiple declaration.

Add an action that will print out the contents of the symbol table to the monitor as you exit each procedure (depth).  Print out the lexeme and the class of the lexeme for each entry in the table at the depth you are exiting.  At the end of the program write out the same for all entries remaining at depth zero.