# fuzz_compare.py - дифференциальное тестирование: случайные входы подаются на три лексера
# (ручной, ANTLR, лексер из lexgen.py); потоки типов токенов должны совпасть.
import random
import sys

from antlr4 import InputStream, Token

from MiniLangLexer import MiniLangLexer
from lexer import Lexer
from lexgen import ERROR_TOKENS, minilang

ANTLR_ERRORS = {"ERROR_CHAR", "BAD_NUMBER", "UNTERMINATED_STRING", "UNTERMINATED_COMMENT"}
# без кавычек и обратной косой черты: сообщения о строках у лексеров различаются по замыслу
ALPHABET = list("0123456789.eExXaAfFgz_+-*/%<>=!&|(){};, \n") + ["//", "/*", "*/", "let", "if", "0x", "1.5e", "é"]


def antlr_types(src):
    lx = MiniLangLexer(InputStream(src))
    out = []
    while True:
        t = lx.nextToken()
        if t.type == Token.EOF:
            return out + ["EOF"]
        name = lx.symbolicNames[t.type]
        if name not in ANTLR_ERRORS:
            out.append(name)


def main(n=20000, seed=7):
    random.seed(seed)
    gen = minilang()
    bad = 0
    for _ in range(n):
        src = "".join(random.choice(ALPHABET) for _ in range(random.randint(1, 14)))
        hand = [t.type.name for t in Lexer(src).tokens()]
        a = antlr_types(src)
        g = [name for name, *_ in gen.tokens(src) if name not in ERROR_TOKENS]
        if not (hand == a == g):
            bad += 1
            if bad <= 5:
                print("расхождение:", repr(src), hand, a, g)
    print(f"случайных входов: {n}, расхождений: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
