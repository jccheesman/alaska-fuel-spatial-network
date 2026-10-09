import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

INK, GREY = "#222", "#9e9e9e"
PURPLE, BLUE, GREEN, AMBER, RED = "#8a4a95", "#1565c0", "#2e7d32", "#ef8f00", "#c62828"
fig = plt.figure(figsize=(17, 20)); fig.patch.set_facecolor("white")
fig.text(0.5, 0.977, "The five skills: a recipe book for keeping the fuel-tank map honest", ha="center", fontsize=22, fontweight="bold")
fig.text(0.5, 0.957, "A 'skill' is a written procedure the AI assistant follows, with its own script and its own rules about what it must never do.",
         ha="center", fontsize=12, color="#444")

cards = [
 ("1. Ingest the inventory", PURPLE, "ingest-facility-inventory",
  "A new spreadsheet arrives from the state\n(a new year, or new columns).",
  "Reads only the columns we need (never the\ncontact details), renames them to our\nstandard, saves a copy under the year, and\nlists what changed since last year.",
  "A tracked snapshot and a diff: 71 rows\nremoved and 3,665 values edited between\n2022 and 2025.",
  "Never decides what is right or wrong.\nNever stores a phone number or email.",
  "01_ingest.py"),
 ("2. Validate the inventory", BLUE, "validate-facility-inventory",
  "Any time something changed: a new year,\na new decision, a new boundary file.",
  "Runs the seven checks in order — apply\nfixes, normalise names, run the detectors,\ncheck boundaries, build the review list,\npublish — and explains any failure.",
  "The clean table plus a short report, or a\nnamed failure with the file that owns the fix.",
  "Never loosens a check to make it pass.\nNever edits the output table by hand.",
  "validate_inventory.py [--publish]"),
 ("3. Record corrections", GREEN, "record-facility-corrections",
  "You hand back the review sheet with your\ndecisions filled in.",
  "Turns each decision into a line of the\ncorrections list: which row, old value,\nnew value, who approved it, when. Checks\nthe values. Asks when a decision is unclear.",
  "Correction lines ready for the next run\n(80 approved so far, 8 waiting).",
  "Never makes a decision itself. Never\noverwrites a decision already recorded.",
  "record_corrections.py REVIEW.xlsx [--write]"),
 ("4. Define the network profile", AMBER, "define-network-profile",
  "You want the hub builder to behave\ndifferently (a new rule, a new threshold).",
  "Edits the one settings file the builder\nreads: which layers exist, how hubs form,\nhow far a hub may snap, whether sites under\nreview are held out.",
  "A changed profile, validated before use.",
  "Never changes the engine code to get a\nregional result. Settings are data.",
  "workflows/02_network_build/profile.yaml"),
 ("5. Build and verify the network", RED, "build-and-verify-network",
  "The inventory is clean and the profile is\nset; time to rebuild the map.",
  "Runs the build, then reads the trail files:\nwhich records were held out, which hubs\nlanded where, which sites conflict. Runs the\nconnectivity proof.",
  "A connected network plus four trail files\nthat show where every record ended up.",
  "Never calls a build done without the proof.\nNever hides an unplaced hub by raising a cap.",
  "run_all.sh → 01_withheld · 02_hub_snaps …"),
]

def card(pos, title, color, name, when, does, gives, never, script):
    ax = fig.add_axes(pos); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.02,rounding_size=0.3", fc="#fafafa", ec=color, lw=1.8))
    ax.add_patch(FancyBboxPatch((0.1, 8.6), 9.8, 1.3, boxstyle="round,pad=0.02,rounding_size=0.3", fc=color, ec=color))
    ax.text(0.4, 9.25, title, fontsize=14, fontweight="bold", va="center", color="white")
    ax.text(9.6, 9.25, name, fontsize=8.5, va="center", ha="right", color="white", family="monospace")
    rows = [("WHEN YOU USE IT", when), ("WHAT IT DOES", does), ("WHAT YOU GET", gives), ("WHAT IT NEVER DOES", never)]
    y = 8.1
    for h, t in rows:
        ax.text(0.4, y, h, fontsize=8, fontweight="bold", color=color, va="top")
        ax.text(0.4, y - 0.42, t, fontsize=9.4, va="top", color=INK, linespacing=1.38)
        y -= 0.42 + 0.36 * (t.count("\n") + 1) + 0.38
    ax.text(0.4, 0.45, "script: " + script, fontsize=8, color=GREY, family="monospace", va="bottom")

W, H = 0.45, 0.285; xs = [0.03, 0.52]; ys = [0.635, 0.335, 0.035]
for i, c in enumerate(cards):
    card([xs[i % 2], ys[i // 2], W, H], *c)

# the loop panel in the sixth slot
ax = fig.add_axes([0.52, 0.035, 0.45, 0.285]); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.02,rounding_size=0.3", fc="#eef3f8", ec="#3b6ea5", lw=1.4))
ax.text(0.4, 9.3, "How they fit together each year", fontsize=14, fontweight="bold", va="top")
nodes = [(1.6, 6.6, "1 ingest", PURPLE), (4.4, 6.6, "2 validate", BLUE), (7.2, 6.6, "you review\nthe sheet", "#555"),
         (7.2, 3.6, "3 record", GREEN), (4.4, 3.6, "2 validate\n--publish", BLUE), (1.6, 3.6, "4 profile\n5 build", AMBER)]
for x, y, t, c in nodes:
    ax.add_patch(FancyBboxPatch((x - 1.1, y - 0.6), 2.2, 1.2, boxstyle="round,pad=0.02,rounding_size=0.2", fc="white", ec=c, lw=1.6))
    ax.text(x, y, t, ha="center", va="center", fontsize=9.5, color=c, fontweight="bold")
def arr(a, b, rad=0.0, c="#555"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color=c, lw=1.4, connectionstyle=f"arc3,rad={rad}"))
arr((2.7, 6.6), (3.3, 6.6)); arr((5.5, 6.6), (6.1, 6.6)); arr((7.2, 6.0), (7.2, 4.2)); arr((6.1, 3.6), (5.5, 3.6)); arr((3.3, 3.6), (2.7, 3.6))
arr((4.4, 4.2), (4.4, 6.0), rad=0.0, c="#999")
ax.text(4.75, 5.1, "still open items?\nback to the sheet", fontsize=7.5, color="#777", va="center")
ax.text(0.4, 1.9, "Undecided rows are held out of the map, so the build can run at any point in the loop.\nEvery arrow is one command; the only human step is the review sheet.",
        fontsize=9, va="top", color=INK, linespacing=1.4)
fig.savefig("skills_explainer.png", dpi=130, facecolor="white")
print("ok")
