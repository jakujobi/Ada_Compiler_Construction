procedure one () is
	id:integer;
	procedure two () is
	begin
	end two;
	procedure three(id:integer) is
		id2:integer;
	begin
	end three;
-- 	Expected OUTPUT:
--		Lexeme: id
--		  TYPE:	INT
--		Offset: 0
--		  Size: 2
--		 DEPTH: 2
--
--		Lexeme: id2
--		  TYPE:	INT
--		Offset: 0
--		  Size: 2
--		 DEPTH: 2
	procedure four (id, id2:integer) is
		id3:integer;
	begin
	end four;
-- 	Expected OUTPUT:
--		Lexeme: id
--		  TYPE:	INT
--		Offset: 2
--		  Size: 2
--		 DEPTH: 2
--
--		Lexeme: id2
--		  TYPE:	INT
--		Offset: 0
--		  Size: 2
--		 DEPTH: 2
--
--		Lexeme: id3
--		  TYPE:	INT
--		Offset: 0
--		  Size: 2
--		 DEPTH: 2
begin
end one;
-- 	Expected OUTPUT:
--			Lexeme: id
--			  TYPE:	INT
--			Offset: 0
--			  Size: 2
--			 DEPTH: 1
-- 	
--			LEXEME: two
--		 	  TYPE:	PROC
--		 	LOCALS: 0
--		PARAMETERS: (0)
--			 DEPTH: 1
--
--			LEXEME: three
--		 	  TYPE:	PROC
--		 	LOCALS: 1
--		PARAMETERS: IN INT, (1)
--			 DEPTH: 1
--
--			LEXEME: four
--		 	  TYPE:	PROC
--		 	LOCALS: 1
--		PARAMETERS: IN INT, IN INT, (2)
--			 DEPTH: 1
--
-- //	(OPT.)
--			LEXEME: one
--		 	  TYPE:	PROC
--		 	LOCALS: 4
--		PARAMETERS: (0)
--			 DEPTH: 0