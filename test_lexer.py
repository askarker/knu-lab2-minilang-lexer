# test_lexer.py - тесты рукописного лексера MiniLang (pytest)
import pytest

from lexer import Lexer, T


def types(src):
    return [t.type for t in Lexer(src).tokens()]


def tokens(src):
    return list(Lexer(src).tokens())


def errors(src):
    lx = Lexer(src)
    list(lx.tokens())
    return lx.errors


# ---------- группы токенов из таблицы 3.1 ----------

def test_keywords():
    src = "let if else while print fn return true false"
    assert types(src) == [T.LET, T.IF, T.ELSE, T.WHILE, T.PRINT, T.FN,
                          T.RETURN, T.TRUE, T.FALSE, T.EOF]


def test_identifiers():
    toks = tokens("x _tmp sum2 Abc_9")
    assert [t.type for t in toks[:-1]] == [T.ID] * 4
    assert [t.lexeme for t in toks[:-1]] == ["x", "_tmp", "sum2", "Abc_9"]


def test_int_and_float_values():
    toks = tokens("0 42 3.14")
    assert [(t.type, t.value) for t in toks[:-1]] == [
        (T.INT, 0), (T.INT, 42), (T.FLOAT, 3.14)]


def test_string_with_escapes():
    tok = tokens(r'"a\tb\n\"q\" \\"')[0]
    assert tok.type is T.STRING
    assert tok.value == 'a\tb\n"q" \\'


def test_arithmetic_operators():
    assert types("+ - * / %") == [T.PLUS, T.MINUS, T.STAR, T.SLASH, T.PERCENT, T.EOF]


def test_comparison_operators():
    assert types("== != < <= > >=") == [T.EQ, T.NE, T.LT, T.LE, T.GT, T.GE, T.EOF]


def test_logic_and_assign():
    assert types("&& || ! =") == [T.AND, T.OR, T.NOT, T.ASSIGN, T.EOF]


def test_delimiters():
    assert types("( ) { } , ;") == [T.LPAREN, T.RPAREN, T.LBRACE, T.RBRACE,
                                    T.COMMA, T.SEMI, T.EOF]


def test_comments_and_whitespace_are_skipped():
    src = "a // строка\n/* блок\n   на две строки */ b"
    assert types(src) == [T.ID, T.ID, T.EOF]


# ---------- maximal munch и приоритет ----------

def test_maximal_munch():
    assert types("a<=b iffy") == [T.ID, T.LE, T.ID, T.ID, T.EOF]


def test_keyword_priority_over_identifier():
    assert types("while whilex") == [T.WHILE, T.ID, T.EOF]


def test_not_equal_vs_not():
    assert types("!a != b") == [T.NOT, T.ID, T.NE, T.ID, T.EOF]


# ---------- позиции ----------

def test_positions_line_and_column():
    toks = tokens("let x = 5;\n  print(x);")
    pos = [(t.type, t.line, t.col) for t in toks]
    assert pos[0] == (T.LET, 1, 1)
    assert pos[1] == (T.ID, 1, 5)
    assert pos[3] == (T.INT, 1, 9)
    assert pos[5] == (T.PRINT, 2, 3)      # после перевода строки и двух пробелов


def test_position_after_block_comment():
    toks = tokens("/* a\nb */ x")
    assert (toks[0].line, toks[0].col) == (2, 6)


# ---------- задание 2: новые числовые литералы ----------

@pytest.mark.parametrize("text,value", [("0x1F", 31), ("0XFF", 255), ("0x0", 0),
                                        ("0xdeadBEEF", 0xDEADBEEF)])
def test_hex_literals(text, value):
    tok = tokens(text)[0]
    assert (tok.type, tok.value) == (T.INT, value)


@pytest.mark.parametrize("text,value", [("1.5e3", 1500.0), ("2.0E-4", 0.0002),
                                        ("1.5e+2", 150.0)])
def test_float_exponent(text, value):
    tok = tokens(text)[0]
    assert (tok.type, tok.value) == (T.FLOAT, value)


# ---------- ошибки ----------

def test_unterminated_string():
    assert errors('"abc') == ["1:1: лексическая ошибка: незакрытая строка"]


def test_unterminated_string_stops_at_newline():
    lx = Lexer('"abc\nlet')
    got = [t.type for t in lx.tokens()]
    assert got == [T.LET, T.EOF]                       # сканирование продолжилось
    assert lx.errors == ["1:1: лексическая ошибка: незакрытая строка"]


def test_unterminated_comment():
    assert errors("a /* нет конца") == ["1:3: лексическая ошибка: незакрытый комментарий"]


def test_invalid_character():
    assert errors("let y = 3 @ 4;") == ["1:11: лексическая ошибка: недопустимый символ '@'"]


def test_single_ampersand():
    assert errors("a & b") == ["1:3: лексическая ошибка: ожидалось '&&'"]


def test_all_errors_found_in_one_pass():
    assert len(errors('"abc;\nlet y = 3 @ 4;\nlet z = a & b;\n')) == 3


def test_hex_without_digits():
    assert errors("0x") == ["1:1: лексическая ошибка: "
                             "шестнадцатеричный литерал без цифр: '0x'"]


def test_exponent_without_digits():
    assert errors("1.5e") == ["1:1: лексическая ошибка: некорректный числовой литерал '1.5e'"]


def test_number_followed_by_letters():
    lx = Lexer("123abc")
    assert [t.type for t in lx.tokens()] == [T.EOF]    # ни INT, ни ID не выдаются
    assert lx.errors == ["1:1: лексическая ошибка: некорректный числовой литерал '123abc'"]


def test_letters_after_signed_exponent():
    lx = Lexer("1.5e+3x")
    assert [t.type for t in lx.tokens()] == [T.EOF]
    assert lx.errors == ["1:1: лексическая ошибка: некорректный числовой литерал '1.5e+3x'"]


def test_dot_after_integer_is_not_float():
    lx = Lexer("12.x")
    assert [t.type for t in lx.tokens()] == [T.INT, T.ID, T.EOF]
    assert lx.errors == ["1:3: лексическая ошибка: недопустимый символ '.'"]


def test_unknown_escape_sequence():
    assert errors(r'"a\qb"') == [r"1:3: лексическая ошибка: неизвестная escape-последовательность \q"]
