# Лабораторная работа № 2. Лексический анализ MiniLang

Студент: Керимкулов А.С., группа ИИ(М)-1-25. Вариант N = 1 (регулярное выражение `(a|b)*bab`).

## Установка

    pip install pytest antlr4-tools==0.2.1 antlr4-python3-runtime==4.13.2

Нужны Python 3.10+ и Java 11+ (jar ANTLR 4.13.2 скачивается при первом запуске `antlr4`).

## Запуск

    python lexer.py test.ml                  # рукописный лексер (в Windows: python -X utf8 lexer.py test.ml)
    python lexer.py bad.ml                   # лексические ошибки: строка:столбец
    python lexer.py literals.ml              # hex, экспонента (задание 2)
    python lexer.py bad_numbers.ml           # 0x, 1.5e, 123abc, 12.x

    antlr4 -v 4.13.2 -Dlanguage=Python3 MiniLangLexer.g4    # генерация лексера ANTLR (задание 3)
    python run_antlr.py test.ml > antlr.txt
    python lexer.py test.ml > hand.txt
    diff antlr.txt hand.txt                  # различаются только значения чисел (= 3.14)
    python compare.py test.ml literals.ml bad.ml bad_numbers.ml   # сравнение типов токенов трёх лексеров

    python -m pytest -v                      # задание 4 (test_lexer.py)
    python task1.py 1                        # задание 1: НКА, ДКА, минимизация для (a|b)*bab
    python task1.py --verify                 # проверка движка по всем 10 вариантам (сравнение с re)
    python lexgen.py test.ml                 # задание А: лексер, построенный мини-генератором
    python fuzz_compare.py                   # случайное сравнение трёх лексеров
    python draw_automata.py ../рисунки       # рисунки автоматов для отчёта

## Файлы

| Файл | Назначение |
|---|---|
| `lexer.py` | рукописный лексер, расширенный (hex, экспонента, ошибка `123abc`) |
| `MiniLangLexer.g4`, `run_antlr.py` | тот же лексер на ANTLR4 и драйвер печати токенов |
| `test_lexer.py` | 33 теста pytest |
| `task1.py` | задание 1: автоматы по регулярному выражению варианта |
| `lexgen.py` | задание А: мини-генератор лексеров (regexp → НКА → ДКА → минимальный ДКА → лексер) |
| `compare.py`, `fuzz_compare.py` | сравнение ручного лексера, ANTLR и генератора |
| `test.ml`, `bad.ml`, `literals.ml`, `bad_numbers.ml` | входные файлы |

Сгенерированные ANTLR файлы (`MiniLangLexer.py`, `*.interp`, `*.tokens`) в репозиторий не кладутся (см. `.gitignore`).
