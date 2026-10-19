# run_antlr.py - печать токенов, полученных лексером ANTLR
import sys
from antlr4 import FileStream, Token
from MiniLangLexer import MiniLangLexer

# токены-ошибки грамматики
ERRORS = {"ERROR_CHAR", "BAD_NUMBER", "UNTERMINATED_STRING", "UNTERMINATED_COMMENT"}


def main():
    lexer = MiniLangLexer(FileStream(sys.argv[1], encoding="utf-8"))
    errors = 0
    while True:
        tok = lexer.nextToken()
        eof = tok.type == Token.EOF
        name = "EOF" if eof else lexer.symbolicNames[tok.type]
        text = "" if eof else tok.text
        print(f"{tok.line}:{tok.column + 1:<4} {name:<8} {text!r}")
        if name in ERRORS:
            errors += 1
        if eof:
            break
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
