import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

RED, GREEN, BLUE, GREY, INK = "#c62828", "#2e7d32", "#1565c0", "#9e9e9e", "#222"
fig = plt.figure(figsize=(17, 22)); fig.patch.set_facecolor("white")
fig.text(0.5, 0.975, "What was wrong in the fuel-tank list, and how we fixed it", ha="center", fontsize=22, fontweight="bold")
fig.text(0.5, 0.955, "The state keeps a spreadsheet of every bulk fuel tank in Alaska: a name, a town, and a map point. Some rows had the wrong town, the wrong point, or were copies.",
         ha="center", fontsize=12, color="#444")

cards = [
 ("1. Two towns' names got swapped",
  "Rows labelled 'Unalaska' sat on Norton Sound, 1,000 km\nfrom Unalaska. Rows labelled 'Unalakleet' sat in the\nAleutians. The points were right; the names were swapped.",
  "Swap the names back. 2 communities fixed.",
  "swap"),
 ("2. One wrong digit in a coordinate",
  "Bethel's tank was typed at 67.8° N instead of 60.8° N,\nputting it above the Arctic Circle. Coldfoot landed in\nCanada. Change one digit and the point goes home.",
  "Retype the coordinate. 8 tanks moved home.",
  "typo"),
 ("3. Right place, wrong town name",
  "A tank sitting in Fort Yukon was labelled 'Fairbanks'.\nOne in Seward was labelled 'Fort Wainwright'. The map\npoint was fine; the town column was not.",
  "Correct the town name. About 17 rows fixed.",
  "label"),
 ("4. The same town spelled two ways",
  "'Saint Marys' and \"St. Mary's\" were counted as two\ndifferent towns, so one village got two fuel hubs.\nSame with Clarks Point / Clark's Point and others.",
  "Pick one spelling; keep an alias list so the\nnext download fixes itself. 7 alias pairs.",
  "spell"),
 ("5. One tank farm copied under many villages",
  "A farm's point and size were pasted into rows for 2 to 6\nneighbouring villages. Five villages 'shared' one spot,\nso the builder stacked them all in one place.",
  "Keep the row whose village matches the spot;\ndrop the copies. 27 copies removed on 16 farms.",
  "stack"),
 ("6. A village row with no home left",
  "After the copies, some farms had NO row with the\nright village name. We relabelled one row each for\nIliamna and Kwethluk; 4 farms still need a decision.",
  "Relabel when there is a clear winner; otherwise\nhold the row out of the map until decided.",
  "orphan"),
]

def card(ax_pos, title, problem, fix, kind):
    ax = fig.add_axes(ax_pos); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.02,rounding_size=0.3", fc="#fafafa", ec="#bbb", lw=1.2))
    ax.text(0.4, 9.4, title, fontsize=13.5, fontweight="bold", va="top", color=INK)
    ax.text(0.4, 8.55, "THE PROBLEM", fontsize=8.5, color=RED, fontweight="bold", va="top")
    ax.text(0.4, 8.15, problem, fontsize=9.6, va="top", color=INK, linespacing=1.4)
    ax.text(0.4, 2.1, "THE FIX", fontsize=8.5, color=GREEN, fontweight="bold", va="top")
    ax.text(0.4, 1.7, fix, fontsize=9.6, va="top", color=INK, linespacing=1.4)
    # mini map: before (left) and after (right)
    def frame(x0):
        ax.add_patch(FancyBboxPatch((x0, 2.9), 4.2, 2.6, boxstyle="round,pad=0.01,rounding_size=0.1", fc="white", ec="#ccc", lw=0.8))
    frame(0.5); frame(5.3)
    ax.text(0.6, 5.45, "before", fontsize=8, color=RED, va="bottom"); ax.text(5.4, 5.45, "after", fontsize=8, color=GREEN, va="bottom")
    ax.add_patch(FancyArrowPatch((4.8, 4.2), (5.2, 4.2), arrowstyle="-|>", mutation_scale=14, color=GREY))
    def dot(x, y, label, c, ax_=ax, shape="o"):
        ax_.scatter(x, y, s=70, color=c, marker=shape, zorder=5, edgecolor="white", linewidth=0.8)
        ax_.text(x, y - 0.42, label, ha="center", fontsize=7.5, color=c)
    if kind == "swap":
        dot(1.4, 4.6, "'Unalaska'", RED); dot(3.8, 3.7, "'Unalakleet'", RED); ax.text(1.4, 5.1, "Norton Sound (north)", fontsize=6.5, ha="center", color=GREY); ax.text(3.8, 3.05, "Aleutians (south)", fontsize=6.5, ha="center", color=GREY)
        dot(6.2, 4.6, "Unalakleet", GREEN); dot(8.6, 3.7, "Unalaska", GREEN)
    elif kind == "typo":
        dot(2.6, 5.0, "Bethel  67.8° N", RED); ax.scatter(2.6, 3.4, s=70, facecolor="none", edgecolor=GREY, zorder=4); ax.text(2.6, 3.0, "real Bethel", fontsize=7, ha="center", color=GREY)
        dot(7.4, 3.4, "Bethel  60.8° N", GREEN)
    elif kind == "label":
        dot(2.6, 4.2, '"Fairbanks"', RED); ax.text(2.6, 4.75, "point is in Fort Yukon", fontsize=7, ha="center", color=GREY)
        dot(7.4, 4.2, "Fort Yukon", GREEN)
    elif kind == "spell":
        dot(1.9, 4.2, "Saint Marys", RED); dot(3.3, 4.2, "St. Mary's", RED); ax.text(2.6, 3.2, "2 hubs, 1 village", fontsize=7, ha="center", color=GREY)
        dot(7.4, 4.2, "St. Mary's", GREEN); ax.text(7.4, 3.2, "1 hub", fontsize=7, ha="center", color=GREEN)
    elif kind == "stack":
        for i, n in enumerate(["Kipnuk", "Chefornak", "Tununak", "Nightmute"]):
            ax.scatter(2.6, 4.2, s=70, color=RED, zorder=5, alpha=0.6)
            ax.text(0.8, 5.0 - i * 0.5, n, fontsize=7, color=RED)
        ax.text(2.9, 4.3, "all on one point", fontsize=7, color=GREY)
        dot(7.4, 4.2, "Atmautluak (the real farm)", GREEN); ax.text(7.4, 3.2, "copies removed", fontsize=7, ha="center", color=GREY)
    elif kind == "orphan":
        ax.scatter(2.6, 4.2, s=70, color=RED, zorder=5); ax.text(2.6, 3.75, "'Nightmute'", fontsize=7.5, ha="center", color=RED)
        ax.text(2.6, 4.75, "farm is really Iliamna's", fontsize=7, ha="center", color=GREY)
        dot(7.4, 4.2, "Iliamna", GREEN); ax.scatter(8.9, 3.3, s=60, marker="s", color="#fbc02d", zorder=5); ax.text(8.9, 2.95, "held", fontsize=7, ha="center", color="#8d6e00")

W, H = 0.45, 0.235; x = [0.03, 0.52]; y = [0.69, 0.44, 0.19]
for i, c in enumerate(cards):
    card([x[i % 2], y[i // 2], W, H], *c)

# bottom strip: how fixes are kept
ax = fig.add_axes([0.03, 0.02, 0.94, 0.15]); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.1, 0.2), 9.8, 9.6, boxstyle="round,pad=0.02,rounding_size=0.3", fc="#e8f0fb", ec="#3b6ea5", lw=1.2))
ax.text(0.4, 9.0, "How every fix is kept honest", fontsize=13.5, fontweight="bold", va="top")
steps = [("1  Never edit the download", "The original spreadsheet stays untouched.\nEach fix is one line in a 'corrections' list."),
         ("2  Every line says who and why", "Which row, what was wrong, the new value,\nwho approved it, and the date."),
         ("3  The computer re-applies them", "Each run starts from the original and\napplies the approved lines again."),
         ("4  Fixes retire themselves", "If the state fixes a row upstream, our line\nno longer matches and is set aside."),
         ("5  Undecided rows wait", "A row still under review is kept out of\nthe map, not guessed. Decided → it joins.")]
for i, (h, t) in enumerate(steps):
    xx = 0.4 + i * 1.95
    ax.text(xx, 6.6, h, fontsize=9.5, fontweight="bold", va="top", color="#1b3a63")
    ax.text(xx, 5.2, t, fontsize=8.6, va="top", color=INK, linespacing=1.35)
fig.savefig("inventory_errors_explainer.png", dpi=130, facecolor="white")
print("ok")
