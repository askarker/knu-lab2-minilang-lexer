# compare.py - сравнение потоков токенов: ручной лексер, ANTLR и лексер из мини-генератора lexgen.py
import re
import subprocess
import sys

# имена токенов-ошибок ANTLR соответствуют ошибкам ручного лексера (токен не выдаётся)
ERR = {"ERROR", "ERROR_CHAR", "BAD_NUMBER", "UNTERMINATED_STRING", "UNTERMINATED_COMMENT"}
LINE = re.compile(r"^(\d+):(\d+)\s+(\w+)\s")


def types(cmd, path):
    out = subprocess.run([sys.executable, "-X", "utf8", cmd, path],
                         capture_output=True, text=True).stdout
    return [LINE.match(l).group(3) for l in out.splitlines() if LINE.match(l)]


def main():
    ok = True
    for path in sys.argv[1:]:
        hand = types("lexer.py", path)
        antlr = [t for t in types("run_antlr.py", path) if t not in ERR]
        gen = [t for t in types("lexgen.py", path) if t not in ERR]
        same = hand == antlr == gen
        ok &= same
        print(f"{path}: ручной={len(hand)}, ANTLR={len(antlr)}, lexgen={len(gen)} токенов -> "
              f"{'ПОСЛЕДОВАТЕЛЬНОСТИ ТИПОВ СОВПАДАЮТ' if same else 'РАСХОЖДЕНИЕ'}")
        if not same:
            for name, other in (("ANTLR", antlr), ("lexgen", gen)):
                for i, (a, b) in enumerate(zip(hand, other)):
                    if a != b:
                        print(f"  {name}: первое расхождение, токен {i}: ручной {a}, {name} {b}")
                        break
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
