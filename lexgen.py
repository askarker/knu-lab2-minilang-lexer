# lexgen.py - мини-генератор лексеров (задание повышенной сложности А), без модуля re.
#   регулярное выражение -> дерево -> НКА Томпсона -> ДКА (метод подмножеств)
#   -> минимальный ДКА -> лексер с maximal munch и приоритетом правил.
# Алфавит: коды 0..127 (ASCII) и один общий символ OTHER = 128 для всех остальных.
import sys

OTHER = 128
UNIVERSE = frozenset(range(129))


# ------------------------------------------------------------------ 1. парсер
class Parser:
    """alt := cat ('|' cat)* ; cat := rep* ; rep := atom ('*'|'+'|'?')* ;
    atom := '(' alt ')' | '[' класс ']' | '.' | '\\' символ | символ"""
    ESC = {"n": "\n", "t": "\t", "r": "\r"}

    def __init__(self, text):
        self.s, self.i = text, 0

    def parse(self):
        node = self.alt()
        if self.i != len(self.s):
            raise ValueError(f"лишний символ {self.s[self.i]!r} в {self.s!r}")
        return node

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def alt(self):
        parts = [self.cat()]
        while self.peek() == "|":
            self.i += 1
            parts.append(self.cat())
        return parts[0] if len(parts) == 1 else ("alt", parts)

    def cat(self):
        parts = []
        while self.peek() not in (None, "|", ")"):
            parts.append(self.rep())
        if not parts:
            return ("eps",)
        return parts[0] if len(parts) == 1 else ("cat", parts)

    def rep(self):
        node = self.atom()
        while self.peek() in ("*", "+", "?"):
            node = ({"*": "star", "+": "plus", "?": "opt"}[self.peek()], node)
            self.i += 1
        return node

    def atom(self):
        c = self.peek()
        self.i += 1
        if c == "(":
            node = self.alt()
            if self.peek() != ")":
                raise ValueError("нет закрывающей скобки")
            self.i += 1
            return node
        if c == "[":
            return ("set", self.char_class())
        if c == ".":
            return ("set", UNIVERSE)
        if c == "\\":
            return ("set", frozenset([self.escaped()]))
        return ("set", frozenset([self.code(c)]))

    @staticmethod
    def code(c):
        return ord(c) if ord(c) < 128 else OTHER

    def escaped(self):
        c = self.peek()
        self.i += 1
        return self.code(self.ESC.get(c, c))

    def char_class(self):
        negate = self.peek() == "^"
        if negate:
            self.i += 1
        chars = set()
        while self.peek() != "]":
            lo = self.escaped() if self.peek() == "\\" and self.advance() else self.code(self.advance())
            if self.peek() == "-" and self.s[self.i + 1] != "]":
                self.i += 1
                hi = self.escaped() if self.peek() == "\\" and self.advance() else self.code(self.advance())
                chars.update(range(lo, hi + 1))
            else:
                chars.add(lo)
        self.i += 1
        return frozenset(UNIVERSE - chars) if negate else frozenset(chars)

    def advance(self):
        c = self.s[self.i]
        self.i += 1
        return c


# ------------------------------------------------------------------ 2. НКА Томпсона
class NFA:
    def __init__(self):
        self.eps = []        # eps[i]  - список состояний, достижимых по ε
        self.edges = []      # edges[i] - список (множество символов, цель)
        self.accept = {}     # состояние -> (приоритет, имя токена)

    def new(self):
        self.eps.append([])
        self.edges.append([])
        return len(self.eps) - 1

    def build(self, node, start=None):
        """Строит фрагмент Томпсона, возвращает состояние-конец.
        start - уже существующее состояние (конкатенация отождествляет конец N(r) с началом N(s)).
        Номера выдаются в порядке построения: начало нового фрагмента - до его частей."""
        kind = node[0]
        if kind == "eps":
            s = self.new() if start is None else start
            e = self.new()
            self.eps[s].append(e)
            return e
        if kind == "set":
            s = self.new() if start is None else start
            e = self.new()
            self.edges[s].append((node[1], e))
            return e
        if kind == "cat":
            cur = start
            for part in node[1]:
                cur = self.build(part, cur)
            return cur
        if kind == "alt":
            s = self.new() if start is None else start
            ends = []
            for part in node[1]:
                ps = self.new()
                self.eps[s].append(ps)
                ends.append(self.build(part, ps))
            e = self.new()
            for x in ends:
                self.eps[x].append(e)
            return e
        if kind == "star":
            s = self.new() if start is None else start
            ps = self.new()
            self.eps[s].append(ps)
            pe = self.build(node[1], ps)
            e = self.new()
            self.eps[s].append(e)
            self.eps[pe].append(ps)
            self.eps[pe].append(e)
            return e
        if kind == "plus":                    # r+ = r r*
            return self.build(("cat", [node[1], ("star", node[1])]), start)
        if kind == "opt":                     # r? = r | ε
            return self.build(("alt", [node[1], ("eps",)]), start)
        raise ValueError(kind)


def regex_nfa(regex):
    """НКА для одного выражения: возвращает (nfa, начало, конец)."""
    nfa = NFA()
    node = Parser(regex).parse()
    start = nfa.new()
    end = nfa.build(node, start)
    return nfa, start, end


def rules_nfa(rules):
    """Объединённый НКА: новое начальное состояние с ε-дугами в начала всех правил.
    rules - список (имя, выражение); чем раньше правило, тем выше приоритет."""
    nfa = NFA()
    start = nfa.new()
    for prio, (name, regex) in enumerate(rules):
        s = nfa.new()
        nfa.eps[start].append(s)
        e = nfa.build(Parser(regex).parse(), s)
        nfa.accept[e] = (prio, name)
    return nfa, start


# ------------------------------------------------------------------ 3. ДКА
def eps_closure(nfa, states):
    stack, seen = list(states), set(states)
    while stack:
        q = stack.pop()
        for r in nfa.eps[q]:
            if r not in seen:
                seen.add(r)
                stack.append(r)
    return frozenset(seen)


def symbol_classes(nfa, alphabet=None):
    """Разбивает символы на классы эквивалентности (одинаковое поведение во всех дугах НКА)."""
    sets = [cs for e in nfa.edges for cs, _ in e]
    symbols = sorted(alphabet) if alphabet is not None else range(129)
    groups = {}
    for c in symbols:
        sig = tuple(i for i, cs in enumerate(sets) if c in cs)
        groups.setdefault(sig, []).append(c)
    return list(groups.values())


class DFA:
    def __init__(self):
        self.start = 0
        self.trans = []      # trans[state] = {индекс класса: состояние}
        self.accept = []     # accept[state] = (приоритет, имя) или None
        self.subsets = []    # для отладки: множество состояний НКА
        self.classes = []    # классы символов
        self.class_of = {}   # код символа -> индекс класса

    def __len__(self):
        return len(self.trans)

    def step(self, state, code):
        ci = self.class_of.get(code)
        return None if ci is None else self.trans[state].get(ci)


def subset_construction(nfa, start, alphabet=None):
    """Метод подмножеств. Допускающее состояние ДКА получает правило с лучшим приоритетом."""
    dfa = DFA()
    dfa.classes = symbol_classes(nfa, alphabet)
    dfa.class_of = {c: i for i, cl in enumerate(dfa.classes) for c in cl}
    d0 = eps_closure(nfa, [start])
    index = {d0: 0}
    queue = [d0]
    dfa.subsets, dfa.trans, dfa.accept = [d0], [{}], [None]
    qi = 0
    while qi < len(queue):
        T = queue[qi]
        di = index[T]
        acc = [nfa.accept[q] for q in T if q in nfa.accept]
        dfa.accept[di] = min(acc) if acc else None
        for ci, cl in enumerate(dfa.classes):
            sample = cl[0]
            moved = {t for q in T for cs, t in nfa.edges[q] if sample in cs}
            if not moved:
                continue
            U = eps_closure(nfa, moved)
            if U not in index:
                index[U] = len(queue)
                queue.append(U)
                dfa.subsets.append(U)
                dfa.trans.append({})
                dfa.accept.append(None)
            dfa.trans[di][ci] = index[U]
        qi += 1
    return dfa


def minimize(dfa, trace=None):
    """Разбиение Мура. Допускающие состояния разных токенов сразу в разных группах.
    trace - список, в который дописываются шаги разбиения (для отчёта)."""
    n = len(dfa)
    block = [(-1 if a is None else a[0]) for a in dfa.accept]
    ids = {}
    block = [ids.setdefault(b, len(ids)) for b in block]
    if trace is not None:
        trace.append(list(block))
    while True:
        sig = [(block[s],) + tuple(block[dfa.trans[s][c]] if c in dfa.trans[s] else -1
                                   for c in range(len(dfa.classes))) for s in range(n)]
        ids = {}
        new = [ids.setdefault(x, len(ids)) for x in sig]
        if len(ids) == len(set(block)):
            break
        block = new
        if trace is not None:
            trace.append(list(block))
    m = DFA()
    m.classes, m.class_of = dfa.classes, dfa.class_of
    k = len(set(block))
    m.trans, m.accept, m.subsets = [{} for _ in range(k)], [None] * k, [None] * k
    order = {}
    for s in range(n):                      # нумерация групп в порядке первого состояния
        order.setdefault(block[s], len(order))
    for s in range(n):
        b = order[block[s]]
        m.accept[b] = dfa.accept[s]
        m.subsets[b] = [x for x in range(n) if order[block[x]] == b]
        for c, t in dfa.trans[s].items():
            m.trans[b][c] = order[block[t]]
    m.start = order[block[dfa.start]]
    return m


# ------------------------------------------------------------------ 4. лексер
class Generated:
    """Лексер по таблице ДКА: maximal munch + приоритет правил + откат."""

    def __init__(self, rules, skip=(), error_name="ERROR"):
        nfa, start = rules_nfa(rules)
        self.nfa_states = len(nfa.eps)
        self.dfa = subset_construction(nfa, start)
        self.min = minimize(self.dfa)
        self.skip = set(skip)
        self.error_name = error_name

    @staticmethod
    def code(c):
        return ord(c) if ord(c) < 128 else OTHER

    def tokens(self, src):
        """Выдаёт (имя токена, лексема, строка, столбец). Непонятный символ - токен ERROR."""
        pos, line, col = 0, 1, 1
        dfa = self.min
        while pos < len(src):
            state, i, last = dfa.start, pos, None
            while i < len(src):
                nxt = dfa.step(state, self.code(src[i]))
                if nxt is None:
                    break
                state, i = nxt, i + 1
                if dfa.accept[state] is not None:
                    last = (i, dfa.accept[state][1])    # запоминаем последнее допускающее
            if last is None:
                end, name = pos + 1, self.error_name
            else:
                end, name = last
            lexeme = src[pos:end]
            if name not in self.skip:
                yield name, lexeme, line, col
            for ch in lexeme:
                if ch == "\n":
                    line, col = line + 1, 1
                else:
                    col += 1
            pos = end
        yield "EOF", "", line, col


# ------------------------------------------------------------------ 5. MiniLang
KEYWORDS = ["let", "if", "else", "while", "print", "fn", "return", "true", "false"]
MINILANG = (
    [(k.upper(), k) for k in KEYWORDS] + [
        ("ID", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("FLOAT", r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?"),
        ("INT", r"[0-9]+|0[xX][0-9a-fA-F]+"),
        ("BAD_NUMBER", r"[0-9]+(\.[0-9]+([eE][+-][0-9]+)?)?[a-zA-Z_][a-zA-Z0-9_]*"),
        ("STRING", r'"([^"\\\n]|\\[nt"\\])*"'),
        ("UNTERMINATED_STRING", r'"([^"\\\n]|\\[nt"\\])*'),
        ("EQ", "=="), ("NE", "!="), ("LE", "<="), ("GE", ">="),
        ("AND", "&&"), ("OR", r"\|\|"),
        ("ASSIGN", "="), ("LT", "<"), ("GT", ">"), ("NOT", "!"),
        ("PLUS", r"\+"), ("MINUS", "-"), ("STAR", r"\*"), ("SLASH", "/"), ("PERCENT", "%"),
        ("LPAREN", r"\("), ("RPAREN", r"\)"), ("LBRACE", "{"), ("RBRACE", "}"),
        ("COMMA", ","), ("SEMI", ";"),
        ("LINE_COMMENT", r"//[^\n]*"),
        ("BLOCK_COMMENT", r"/\*([^*]|\*+[^*/])*\*+/"),
        ("UNTERMINATED_COMMENT", r"/\*([^*]|\*+[^*/])*\**"),
        ("WS", r"[ \t\r\n]+"),
    ])
SKIP = {"LINE_COMMENT", "BLOCK_COMMENT", "WS"}
ERROR_TOKENS = {"ERROR", "BAD_NUMBER", "UNTERMINATED_STRING", "UNTERMINATED_COMMENT"}


def minilang():
    return Generated(MINILANG, SKIP)


# ------------------------------------------------------------------ 6. DOT
def to_dot(dfa, title="DFA"):
    """Описание ДКА на языке Graphviz DOT (можно отрисовать командой dot -Tpng)."""
    out = [f'digraph "{title}" {{', "  rankdir=LR;", '  node [shape=circle];',
           '  __start [shape=point];', f"  __start -> S{dfa.start};"]
    for s, a in enumerate(dfa.accept):
        if a is not None:
            out.append(f'  S{s} [shape=doublecircle, label="S{s}\\n{a[1]}"];')
    for s, tr in enumerate(dfa.trans):
        by_target = {}
        for c, t in tr.items():
            by_target.setdefault(t, []).append(c)
        for t, cls in by_target.items():
            label = describe([x for c in cls for x in dfa.classes[c]])
            out.append(f'  S{s} -> S{t} [label="{label}"];')
    out.append("}")
    return "\n".join(out)


def describe(codes):
    """Короткое описание множества символов для подписи дуги."""
    codes = sorted(set(codes))
    if len(codes) > 40:
        return "прочие"
    parts, i = [], 0
    while i < len(codes):
        j = i
        while j + 1 < len(codes) and codes[j + 1] == codes[j] + 1:
            j += 1
        name = lambda c: "иное" if c == OTHER else (repr(chr(c))[1:-1] if 32 < c < 127 else f"\\x{c:02x}")
        parts.append(name(codes[i]) if i == j else f"{name(codes[i])}-{name(codes[j])}")
        i = j + 1
    return ",".join(parts).replace('"', '\\"')


def main():
    if len(sys.argv) < 2:
        print("использование: python lexgen.py файл.ml   (лексер MiniLang, построенный генератором)")
        return 2
    gen = minilang()
    print(f"НКА: {gen.nfa_states} состояний, ДКА: {len(gen.dfa)}, минимальный ДКА: {len(gen.min)}",
          file=sys.stderr)
    with open(sys.argv[1], encoding="utf-8") as f:
        src = f.read()
    errors = 0
    for name, lexeme, line, col in gen.tokens(src):
        if name in ERROR_TOKENS:
            errors += 1
        print(f"{line}:{col:<4} {name:<8} {lexeme!r}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
