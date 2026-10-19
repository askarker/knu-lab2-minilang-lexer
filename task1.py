# task1.py - задание 1: НКА Томпсона, ДКА подмножеств и минимизация для выражения варианта.
# Использует движок из lexgen.py и проверяет ручное решение на цепочках.
import sys
from lexgen import (regex_nfa, eps_closure, subset_construction, minimize, describe)

VARIANTS = {1: "(a|b)*bab", 2: "a(a|b)*b", 3: "(ab|b)*a", 4: "(a|ba)*bb", 5: "b(ab)*a?",
            6: "(a|b)*a(a|b)", 7: "(aa|b)*ab", 8: "a*b*a", 9: "(ab)*|(ba)*", 10: "(a|b)*bb(a|b)*"}
AB = [ord("a"), ord("b")]


def solve(regex):
    nfa, s, e = regex_nfa(regex)
    nfa.accept[e] = (0, "ACC")
    dfa = subset_construction(nfa, s, alphabet=AB)
    trace = []
    mini = minimize(dfa, trace)
    return nfa, s, e, dfa, mini, trace


def accepts(dfa, text):
    st = dfa.start
    for ch in text:
        st = dfa.step(st, ord(ch))
        if st is None:
            return False
    return dfa.accept[st] is not None


def letter(i):
    return chr(ord("A") + i)


def show(variant):
    regex = VARIANTS[variant]
    nfa, s, e, dfa, mini, trace = solve(regex)
    a_cls, b_cls = dfa.class_of[ord("a")], dfa.class_of[ord("b")]
    print(f"Вариант {variant}: {regex}")
    print(f"\nНКА Томпсона: {len(nfa.eps)} состояний (0..{len(nfa.eps)-1}), начальное {s}, допускающее {e}")
    for i in range(len(nfa.eps)):
        out = [f"ε→{t}" for t in nfa.eps[i]] + [f"{describe(cs)}→{t}" for cs, t in nfa.edges[i]]
        print(f"  {i}: " + (", ".join(out) if out else "-"))
    print(f"\nε-closure начального состояния: {sorted(eps_closure(nfa, [s]))}")
    print(f"\nДКА ({len(dfa)} состояний):")
    for i, sub in enumerate(dfa.subsets):
        ta = dfa.trans[i].get(a_cls); tb = dfa.trans[i].get(b_cls)
        f = lambda t: letter(t) if t is not None else "-"
        mark = ("→ " if i == dfa.start else "") + letter(i) + (" (допуск.)" if dfa.accept[i] else "")
        print(f"  {mark:<14} {sorted(sub)}  a→{f(ta)}  b→{f(tb)}")
    print("\nШаги минимизации (номера групп по состояниям A, B, ...):")
    for k, b in enumerate(trace):
        groups = {}
        for st, g in enumerate(b):
            groups.setdefault(g, []).append(letter(st))
        print(f"  шаг {k}: " + "  ".join("{" + ",".join(v) + "}" for v in groups.values()))
    print(f"\nМинимальный ДКА ({len(mini)} состояний):")
    for i in range(len(mini)):
        ta = mini.trans[i].get(a_cls); tb = mini.trans[i].get(b_cls)
        f = lambda t: str(t) if t is not None else "-"
        members = "".join(letter(x) for x in mini.subsets[i])
        mark = ("→ " if i == mini.start else "") + f"M{i}" + (" (допуск.)" if mini.accept[i] else "")
        print(f"  {mark:<14} = {{{members}}}  a→M{f(ta)}  b→M{f(tb)}")
    print("\nПроверка цепочек:")
    import itertools
    words = ["".join(w) for n in range(0, 7) for w in itertools.product("ab", repeat=n)]
    acc = [w for w in words if accepts(mini, w)]
    rej = [w for w in words if not accepts(mini, w)]
    print("  допускает:", ", ".join(w or "ε" for w in acc[:6]))
    print("  отвергает:", ", ".join(w or "ε" for w in rej[:6]))
    return nfa, s, e, dfa, mini


def verify():
    """Проверка движка: для всех вариантов сравниваем НКА->ДКА->мин. ДКА со стандартным re
    на всех цепочках над {a, b} длиной до 10 (модуль re используется только для проверки)."""
    import itertools
    import re
    for v, rx in VARIANTS.items():
        nfa, s, e, dfa, mini, _ = solve(rx)
        pat = re.compile(rx)
        bad = 0
        for n in range(0, 11):
            for w in itertools.product("ab", repeat=n):
                w = "".join(w)
                if not (accepts(mini, w) == accepts(dfa, w) == bool(pat.fullmatch(w))):
                    bad += 1
        print(f"вариант {v:>2}: {rx:<16} НКА {len(nfa.eps):>2}, ДКА {len(dfa)}, минимальный {len(mini)}, "
              f"расхождений с re на цепочках до длины 10: {bad}")


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify()
    else:
        show(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
