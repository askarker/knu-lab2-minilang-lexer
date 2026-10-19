# lexer.py - рукописный лексический анализатор MiniLang
import sys
from dataclasses import dataclass
from enum import Enum, auto


class T(Enum):
    # ключевые слова
    LET = auto(); IF = auto(); ELSE = auto(); WHILE = auto(); PRINT = auto()
    FN = auto(); RETURN = auto(); TRUE = auto(); FALSE = auto()
    # имена и литералы
    ID = auto(); INT = auto(); FLOAT = auto(); STRING = auto()
    # операторы
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); PERCENT = auto()
    ASSIGN = auto(); EQ = auto(); NE = auto(); LT = auto(); LE = auto()
    GT = auto(); GE = auto(); AND = auto(); OR = auto(); NOT = auto()
    # разделители
    LPAREN = auto(); RPAREN = auto(); LBRACE = auto(); RBRACE = auto()
    COMMA = auto(); SEMI = auto()
    EOF = auto()


KEYWORDS = {
    "let": T.LET, "if": T.IF, "else": T.ELSE, "while": T.WHILE,
    "print": T.PRINT, "fn": T.FN, "return": T.RETURN,
    "true": T.TRUE, "false": T.FALSE,
}

SINGLE = {
    "+": T.PLUS, "-": T.MINUS, "*": T.STAR, "%": T.PERCENT,
    "(": T.LPAREN, ")": T.RPAREN, "{": T.LBRACE, "}": T.RBRACE,
    ",": T.COMMA, ";": T.SEMI,
}

# первый символ -> (второй символ, токен из двух символов, токен из одного или None)
DOUBLE = {
    "=": ("=", T.EQ, T.ASSIGN), "!": ("=", T.NE, T.NOT),
    "<": ("=", T.LE, T.LT),     ">": ("=", T.GE, T.GT),
    "&": ("&", T.AND, None),    "|": ("|", T.OR, None),
}

ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}

END = "\0"  # символ-сторож «конец входа»


def is_letter(c):
    return c == "_" or "a" <= c <= "z" or "A" <= c <= "Z"


def is_digit(c):
    return "0" <= c <= "9"


def is_hex_digit(c):
    return is_digit(c) or "a" <= c <= "f" or "A" <= c <= "F"


@dataclass
class Token:
    type: T
    lexeme: str
    value: object
    line: int
    col: int

    def __str__(self):
        s = f"{self.line}:{self.col:<4} {self.type.name:<8} {self.lexeme!r}"
        return s if self.value is None else f"{s} = {self.value!r}"


class Lexer:
    def __init__(self, src):
        self.src = src
        self.pos = 0
        self.line = 1
        self.col = 1
        self.errors = []

    # --- работа с входным потоком ---
    def peek(self, k=0):
        i = self.pos + k
        return self.src[i] if i < len(self.src) else END

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def error(self, msg, line, col):
        self.errors.append(f"{line}:{col}: лексическая ошибка: {msg}")

    # --- публичный интерфейс ---
    def tokens(self):
        while True:
            tok = self.next_token()
            if tok is None:          # ошибка уже записана, продолжаем
                continue
            yield tok
            if tok.type is T.EOF:
                return

    # --- пропуск пробелов и комментариев ---
    def skip_ws_and_comments(self):
        while True:
            ch = self.peek()
            if ch in " \t\r\n":
                self.advance()
            elif ch == "/" and self.peek(1) == "/":
                while self.peek() not in ("\n", END):
                    self.advance()
            elif ch == "/" and self.peek(1) == "*":
                line, col = self.line, self.col
                self.advance(); self.advance()
                while not (self.peek() == "*" and self.peek(1) == "/"):
                    if self.pos >= len(self.src):
                        self.error("незакрытый комментарий", line, col)
                        return
                    self.advance()
                self.advance(); self.advance()
            else:
                return

    # --- один токен ---
    def next_token(self):
        self.skip_ws_and_comments()
        line, col = self.line, self.col
        if self.pos >= len(self.src):
            return Token(T.EOF, "", None, line, col)

        start = self.pos
        ch = self.peek()

        if is_letter(ch):                                  # ID или ключевое слово
            while is_letter(self.peek()) or is_digit(self.peek()):
                self.advance()
            text = self.src[start:self.pos]
            return Token(KEYWORDS.get(text, T.ID), text, None, line, col)

        if is_digit(ch):                                   # INT или FLOAT
            return self.number(start, line, col)

        if ch == '"':                                      # STRING
            return self.string(start, line, col)

        if ch in DOUBLE:                                   # maximal munch: '<=' длиннее '<'
            second, two, one = DOUBLE[ch]
            self.advance()
            if self.peek() == second:
                self.advance()
                return Token(two, ch + second, None, line, col)
            if one is None:
                self.error(f"ожидалось '{ch}{second}'", line, col)
                return None
            return Token(one, ch, None, line, col)

        if ch == "/":                                      # комментарии уже пропущены
            self.advance()
            return Token(T.SLASH, "/", None, line, col)

        if ch in SINGLE:
            self.advance()
            return Token(SINGLE[ch], ch, None, line, col)

        self.advance()                                      # панический режим: пропускаем символ
        self.error(f"недопустимый символ {ch!r}", line, col)
        return None

    # --- ДКА для чисел (рисунок «ДКА для чисел» в отчёте, состояния Q0..Q10) ---
    #   Q0 --0--> Q1 --x/X--> Q5 --hex--> Q7 (INT, 0x..)          шестнадцатеричные
    #   Q0 --1-9--> Q2 (INT) --.--> Q3 --цифра--> Q6 (FLOAT)      десятичные
    #   Q6 --e/E--> Q8 --+/-?--> Q9 --цифра--> Q10 (FLOAT)        экспонента
    #   из допускающих состояний буква или _ дальше -> Q4 (ошибка «некорректный числовой литерал»)
    def number(self, start, line, col):
        if self.peek() == "0" and self.peek(1) in ("x", "X"):
            self.advance(); self.advance()                 # Q1 -> Q5
            digits = 0
            while is_hex_digit(self.peek()):               # Q7
                self.advance()
                digits += 1
            if digits == 0:
                return self.bad_number(start, line, col, "шестнадцатеричный литерал без цифр")
            if is_letter(self.peek()):
                return self.bad_number(start, line, col)
            text = self.src[start:self.pos]
            return Token(T.INT, text, int(text, 16), line, col)

        while is_digit(self.peek()):                       # Q2
            self.advance()
        is_float = False
        if self.peek() == "." and is_digit(self.peek(1)):  # Q2 -> Q3 -> Q6
            is_float = True
            self.advance()
            while is_digit(self.peek()):
                self.advance()
            if self.peek() in ("e", "E"):                  # Q6 -> Q8 -> Q9 -> Q10
                k = 2 if self.peek(1) in ("+", "-") else 1
                if is_digit(self.peek(k)):
                    for _ in range(k):
                        self.advance()
                    while is_digit(self.peek()):
                        self.advance()
        if is_letter(self.peek()):                         # 123abc, 1.5e, 1e5
            return self.bad_number(start, line, col)
        text = self.src[start:self.pos]
        if is_float:
            return Token(T.FLOAT, text, float(text), line, col)
        return Token(T.INT, text, int(text), line, col)

    def bad_number(self, start, line, col, msg=None):
        """Некорректный числовой литерал: съедаем весь «хвост» из букв и цифр."""
        while is_letter(self.peek()) or is_digit(self.peek()):
            self.advance()
        text = self.src[start:self.pos]
        self.error(f"{msg}: {text!r}" if msg else f"некорректный числовой литерал {text!r}",
                   line, col)
        return None

    # --- строковый литерал ---
    def string(self, start, line, col):
        self.advance()                                     # открывающая кавычка
        chars = []
        while True:
            ch = self.peek()
            if ch == "\n" or self.pos >= len(self.src):
                self.error("незакрытая строка", line, col)
                return None
            self.advance()
            if ch == '"':
                break
            if ch == "\\":
                esc = self.peek()
                if esc in ESCAPES:
                    self.advance()
                    chars.append(ESCAPES[esc])
                else:
                    self.error(f"неизвестная escape-последовательность \\{esc}",
                               self.line, self.col - 1)
            else:
                chars.append(ch)
        return Token(T.STRING, self.src[start:self.pos], "".join(chars), line, col)


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        lexer = Lexer(f.read())
    for tok in lexer.tokens():
        print(tok)
    for err in lexer.errors:
        print(err, file=sys.stderr)
    sys.exit(1 if lexer.errors else 0)


if __name__ == "__main__":
    main()
