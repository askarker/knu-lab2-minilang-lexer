lexer grammar MiniLangLexer;

// Ключевые слова - ДО правила ID: при равной длине побеждает правило выше
LET    : 'let' ;
IF     : 'if' ;
ELSE   : 'else' ;
WHILE  : 'while' ;
PRINT  : 'print' ;
FN     : 'fn' ;
RETURN : 'return' ;
TRUE   : 'true' ;
FALSE  : 'false' ;

ID     : [a-zA-Z_] [a-zA-Z0-9_]* ;

// Числа (задание 2/3): шестнадцатеричные и экспонента
// FLOAT и INT стоят ДО BAD_NUMBER: при равной длине побеждает правило выше
FLOAT  : DIGIT+ '.' DIGIT+ ( [eE] [+-]? DIGIT+ )? ;
INT    : DIGIT+ | '0' [xX] HEXDIGIT+ ;      // десятичное или шестнадцатеричное
// Число, сразу за которым идут буквы: 123abc, 1.5e, 0x, 0x1G, 1.5e+3x
BAD_NUMBER : DIGIT+ ( '.' DIGIT+ ( [eE] [+-] DIGIT+ )? )? [a-zA-Z_] [a-zA-Z0-9_]* ;

STRING : '"' ( ESC | ~["\\\r\n] )* '"' ;
// Незакрытая строка: до конца строки, без закрывающей кавычки
UNTERMINATED_STRING : '"' ( ESC | ~["\\\r\n] )* ;

// Двухсимвольные операторы: порядок не важен, работает maximal munch
EQ  : '==' ;  NE : '!=' ;  LE : '<=' ;  GE : '>=' ;
AND : '&&' ;  OR : '||' ;
ASSIGN : '=' ;  LT : '<' ;  GT : '>' ;  NOT : '!' ;
PLUS : '+' ;  MINUS : '-' ;  STAR : '*' ;  SLASH : '/' ;  PERCENT : '%' ;
LPAREN : '(' ;  RPAREN : ')' ;  LBRACE : '{' ;  RBRACE : '}' ;
COMMA : ',' ;  SEMI : ';' ;

// Пропускаемые лексемы
LINE_COMMENT  : '//' ~[\r\n]*  -> skip ;
BLOCK_COMMENT : '/*' .*? '*/'  -> skip ;
WS            : [ \t\r\n]+     -> skip ;

// Незакрытый комментарий. Вариант '/*' .*? EOF из задания здесь не годится:
// он тоже распознаёт всё до конца файла и по maximal munch ПЕРЕБИВАЕТ BLOCK_COMMENT.
// Поэтому тело описано так, чтобы в нём не могло встретиться '*/'.
UNTERMINATED_COMMENT : '/*' ( ~'*' | '*'+ ~[*/] )* '*'* EOF ;

// Последнее правило: любой другой символ - токен-ошибка
ERROR_CHAR : . ;

fragment DIGIT    : [0-9] ;
fragment HEXDIGIT : [0-9a-fA-F] ;
fragment ESC      : '\\' [nt"\\] ;
