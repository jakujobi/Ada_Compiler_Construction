**CSC 446**  
**HAMER**  
**Assign #6**  
**DUE April 4th, 2025**

Add the following grammar rules to your parser.
```
SeqOfStatments -> Statement ; StatTail | ε  
StatTail -> Statement ; StatTail | ε  
Statement -> AssignStat | IOStat  
AssignStat -> idt := Expr  
IOStat -> ε  
Expr -> Relation  
Relation -> SimpleExpr  
SimpleExpr -> Term MoreTerm  
MoreTerm -> addopt Term MoreTerm | ε  
Term -> Factor MoreFactor  
MoreFactor -> mulopt Factor MoreFactor | ε  
Factor -> idt | numt | ( Expr )| nott Factor| signopt Factor  
```

**addopt** are `+ | - | or`  
**mulopt** are `* | / | mod | rem | and`  
**signopt** is `+ | -` (you may use **addopt** here)

Add the appropriate actions to your parser to check for undeclared variables used in an assignment statement.