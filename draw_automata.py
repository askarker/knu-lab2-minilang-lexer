# draw_automata.py - рисунки автоматов для отчёта (matplotlib; Graphviz на машине не нужен).
# Запуск:  python draw_automata.py <каталог для PNG>
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"
R = 0.42


def draw(path, nodes, edges, size, title=None, note=None, pad=(2.2, 1.6, 2.0, 2.2)):
    """nodes: имя -> (x, y, подпись под кружком или '', допускающее?, начальное?)
    edges: (откуда, куда, метка, rad, цвет, пунктир, сдвиг_метки)"""
    fig, ax = plt.subplots(figsize=size, dpi=150)
    ax.set_aspect("equal")
    ax.axis("off")
    for name, (x, y, sub, acc, start) in nodes.items():
        ax.add_patch(Circle((x, y), R, fill=True, fc="white", ec="black", lw=1.4, zorder=3))
        if acc:
            ax.add_patch(Circle((x, y), R * 0.78, fill=False, ec="black", lw=1.1, zorder=4))
        ax.text(x, y, name, ha="center", va="center", fontsize=11, zorder=5)
        if sub and sub[0] == ">":                    # подпись справа от кружка
            ax.text(x + R + 0.15, y, sub[1:], ha="left", va="center", fontsize=8.5, color="#333333", zorder=5)
        elif sub and sub[0] == "<":                  # слева
            ax.text(x - R - 0.15, y, sub[1:], ha="right", va="center", fontsize=8.5, color="#333333", zorder=5)
        elif sub and sub[0] == "^":                  # сверху
            ax.text(x, y + R + 0.28, sub[1:], ha="center", va="center", fontsize=8.5, color="#333333", zorder=5)
        elif sub:
            ax.text(x, y - R - 0.28, sub, ha="center", va="center", fontsize=8.5, color="#333333", zorder=5)
        if start:
            ax.add_patch(FancyArrowPatch((x - 1.4, y), (x - R, y), arrowstyle="-|>", mutation_scale=14,
                                         lw=1.3, color="black", zorder=2))
    for (a, b, label, rad, color, dashed, shift) in edges:
        xa, ya = nodes[a][:2]
        xb, yb = nodes[b][:2]
        kw = dict(arrowstyle="-|>", mutation_scale=13, lw=1.2, color=color, zorder=1,
                  linestyle="--" if dashed else "-")
        if a == b:                                   # петля
            up = 1 if rad >= 0 else -1
            p = FancyArrowPatch((xa - 0.22, ya + up * R), (xa + 0.22, ya + up * R),
                                connectionstyle=f"arc3,rad={-up * 2.6}", **kw)
            ax.add_patch(p)
            ax.text(xa, ya + up * (R + 0.95) + shift[1], label, ha="center", va="center", fontsize=9,
                    color=color if color != "#999999" else "#555555", zorder=6)
            continue
        p = FancyArrowPatch((xa, ya), (xb, yb), connectionstyle=f"arc3,rad={rad}",
                            shrinkA=R * 36, shrinkB=R * 36, **kw)
        ax.add_patch(p)
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        dx, dy = xb - xa, yb - ya
        # середина дуги arc3 (квадратичная кривая Безье): mid + 0.5 * rad * (dy, -dx)
        mx += dy * rad * 0.5
        my += -dx * rad * 0.5
        ax.text(mx + shift[0], my + shift[1], label, ha="center", va="center", fontsize=9,
                color=color if color != "#999999" else "#555555", zorder=6,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))
    xs = [v[0] for v in nodes.values()]
    ys = [v[1] for v in nodes.values()]
    ax.set_xlim(min(xs) - pad[0], max(xs) + pad[1])
    ax.set_ylim(min(ys) - pad[2], max(ys) + pad[3])
    if title:
        ax.set_title(title, fontsize=11)
    if note:
        fig.text(0.5, 0.01, note, ha="center", fontsize=8.5, color="#333333")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


K = "black"


def nfa_variant1(path):
    """НКА Томпсона для (a|b)*bab (11 состояний)."""
    n = {"0": (0, 0, "", 0, 1), "1": (2.6, 0, "", 0, 0), "2": (5.2, 1.5, "", 0, 0), "3": (7.8, 1.5, "", 0, 0),
         "4": (5.2, -1.5, "", 0, 0), "5": (7.8, -1.5, "", 0, 0), "6": (10.4, 0, "", 0, 0),
         "7": (13, 0, "", 0, 0), "8": (15.6, 0, "", 0, 0), "9": (18.2, 0, "", 0, 0), "10": (20.8, 0, "", 1, 0)}
    e = [("0", "1", "ε", 0, K, 0, (0, 0.28)), ("1", "2", "ε", 0, K, 0, (-0.2, 0.0)), ("1", "4", "ε", 0, K, 0, (-0.2, 0.0)),
         ("2", "3", "a", 0, K, 0, (0, 0.28)), ("4", "5", "b", 0, K, 0, (0, -0.28)),
         ("3", "6", "ε", 0, K, 0, (0.2, 0.0)), ("5", "6", "ε", 0, K, 0, (0.2, 0.0)),
         ("6", "7", "ε", 0, K, 0, (0, 0.28)),
         ("0", "7", "ε", 0.42, K, 0, (0, -0.25)), ("6", "1", "ε", 0.75, K, 0, (0, 0.25)),
         ("7", "8", "b", 0, K, 0, (0, 0.28)), ("8", "9", "a", 0, K, 0, (0, 0.28)), ("9", "10", "b", 0, K, 0, (0, 0.28))]
    draw(path, n, e, (13, 4.8))


def dfa_variant1(path):
    n = {"A": (0, 0, "{0,1,2,4,7}", 0, 1), "B": (4.6, 2.4, ">{1,2,3,4,6,7}", 0, 0),
         "C": (4.6, -2.4, "<{1,2,4,5,6,7,8}", 0, 0), "D": (10.2, -2.4, "{1,2,3,4,6,7,9}", 0, 0),
         "E": (15.8, -2.4, "{1,2,4,5,6,7,8,10}", 1, 0)}
    e = [("A", "B", "a", 0.0, K, 0, (-0.3, 0.3)), ("A", "C", "b", 0.0, K, 0, (-0.3, -0.3)),
         ("B", "B", "a", 1, K, 0, (0, 0)), ("B", "C", "b", 0.0, K, 0, (0.3, 0)),
         ("C", "C", "b", -1, K, 0, (0, 0)), ("C", "D", "a", 0.0, K, 0, (0, 0.28)),
         ("D", "B", "a", 0.0, K, 0, (0.3, 0.3)), ("D", "E", "b", 0.25, K, 0, (0, 0.05)),
         ("E", "D", "a", 0.25, K, 0, (0, -0.05)), ("E", "C", "b", -0.36, K, 0, (0, -0.25))]
    draw(path, n, e, (11.5, 5.6), pad=(2.2, 1.6, 2.4, 2.4))


def dfa_min_variant1(path):
    n = {"M0": (0, 0, "", 0, 1), "M1": (4.2, 0, "", 0, 0), "M2": (8.4, 0, "", 0, 0),
         "M3": (6.3, -3.6, "", 1, 0)}
    e = [("M0", "M0", "a", 1, K, 0, (0, 0)), ("M0", "M1", "b", 0, K, 0, (0, 0.28)),
         ("M1", "M1", "b", 1, K, 0, (0, 0)), ("M1", "M2", "a", 0, K, 0, (0, 0.28)),
         ("M2", "M0", "a", -0.45, K, 0, (0, 0.2)), ("M2", "M3", "b", 0.2, K, 0, (0.5, 0.1)),
         ("M3", "M2", "a", 0.2, K, 0, (-0.1, 0.0)), ("M3", "M1", "b", -0.2, K, 0, (-0.9, -0.2))]
    draw(path, n, e, (9.5, 5.5), note="M0 = {A, B},  M1 = {C},  M2 = {D},  M3 = {E}  (состояния ДКА до минимизации)")


def numbers_dfa(path):
    """ДКА чисел (минимальный, 11 состояний, построен lexgen.py по правилам INT, FLOAT, BAD_NUMBER)."""
    n = {"Q0": (0, 0, "", 0, 1),
         "Q1": (3.4, 2.0, "^INT", 1, 0), "Q2": (3.4, -2.0, ">INT", 1, 0),
         "Q3": (7, 0, "", 0, 0), "Q6": (10.6, 0, "FLOAT", 1, 0),
         "Q8": (14.2, 0, "BAD", 1, 0), "Q9": (17.6, 2.2, "", 0, 0), "Q10": (21, 0, ">FLOAT", 1, 0),
         "Q5": (7, 4.8, "^BAD", 1, 0), "Q7": (11.5, 4.8, ">INT (hex)", 1, 0),
         "Q4": (10.6, -5.2, ">BAD_NUMBER", 1, 0)}
    G = "#999999"
    e = [("Q0", "Q1", "0", 0, K, 0, (-0.3, 0.2)), ("Q0", "Q2", "1–9", 0, K, 0, (-0.35, -0.2)),
         ("Q1", "Q2", "0–9", 0, K, 0, (0.55, 0)),
         ("Q1", "Q3", "«.»", 0, K, 0, (-0.3, 0.3)), ("Q2", "Q3", "«.»", 0, K, 0, (-0.3, -0.3)),
         ("Q2", "Q2", "0–9", -1, K, 0, (0, 0)),
         ("Q1", "Q5", "x, X", 0.0, K, 0, (-0.55, 0.0)),
         ("Q5", "Q7", "0–9, a–f, A–F", 0, K, 0, (0, 0.3)), ("Q7", "Q7", "0–9, a–f, A–F", 1, K, 0, (0, 0)),
         ("Q3", "Q6", "0–9", 0, K, 0, (0, 0.28)), ("Q6", "Q6", "0–9", 1, K, 0, (0, 0)),
         ("Q6", "Q8", "e, E", 0, K, 0, (0, 0.28)),
         ("Q8", "Q9", "+, −", 0, K, 0, (-0.4, 0.2)), ("Q8", "Q10", "0–9", 0, K, 0, (0, 0.28)),
         ("Q9", "Q10", "0–9", 0, K, 0, (0.45, 0.2)),
         ("Q10", "Q10", "0–9", -1, K, 0, (0, 0)),
         ("Q4", "Q4", "буква, цифра, _", -1, G, 1, (0, 0))]
    for src in ("Q1", "Q2", "Q5", "Q6", "Q7", "Q8", "Q10"):
        e.append((src, "Q4", "", 0.0, G, 1, (0, 0)))
    draw(path, n, e, (14, 7.2),
         note="Серые пунктирные дуги: по букве или «_», не указанной на других дугах (для Q5 - по g–z, G–Z, _), "
              "переход в Q4 - ошибка «некорректный числовой литерал».")


if __name__ == "__main__":
    out = sys.argv[1]
    nfa_variant1(f"{out}/nfa_variant1.png")
    dfa_variant1(f"{out}/dfa_variant1.png")
    dfa_min_variant1(f"{out}/dfa_min_variant1.png")
    numbers_dfa(f"{out}/dfa_numbers.png")
    print("готово")
