import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

C = {"raw": ("#f6e7c8", "#9a7b3c"), "cfg": ("#dfe9f7", "#3b6ea5"), "step": ("#ffffff", "#555555"),
     "out": ("#e3f1e1", "#4a8a44"), "human": ("#fde6e6", "#b84a4a")}
fig, ax = plt.subplots(figsize=(16, 21.5)); ax.set_xlim(0, 16); ax.set_ylim(0.3, 21.8); ax.axis("off")

def box(x, y, w, h, text, kind, fs=9.5, bold_first=True):
    fc, ec = C[kind]
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=1.4))
    lines = text.split("\n")
    if bold_first:
        ax.text(x + w/2, y + h - 0.28, lines[0], ha="center", va="top", fontsize=fs+0.5, fontweight="bold")
        ax.text(x + w/2, y + h - 0.62, "\n".join(lines[1:]), ha="center", va="top", fontsize=fs, linespacing=1.35)
    else:
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, linespacing=1.35)
    return (x, y, w, h)

def group(x, y, w, h, title):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.2", fc="none", ec="#8a4a95", lw=1.3, ls=(0, (5, 3))))
    ax.text(x + 0.15, y + h - 0.12, title, ha="left", va="top", fontsize=10.5, color="#8a4a95", fontweight="bold")

def arrow(a, b, side="v", color="#333", lw=1.4, rad=0.0):
    if side == "v":
        p0 = (a[0] + a[2]/2, a[1]); p1 = (b[0] + b[2]/2, b[1] + b[3])
    elif side == "h":
        p0 = (a[0] + a[2], a[1] + a[3]/2); p1 = (b[0], b[1] + b[3]/2)
    elif side == "hl":
        p0 = (a[0], a[1] + a[3]/2); p1 = (b[0] + b[2], b[1] + b[3]/2)
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14, color=color, lw=lw, connectionstyle=f"arc3,rad={rad}"))

# --- band 1: raw + ingest
raw = box(0.6, 19.3, 4.6, 1.3, "AEA / DCRA download\nUtilities_Bulk_Fuel_Inventory.csv\ncontact columns never read", "raw")
group(5.8, 19.05, 4.6, 2.0, "skill: ingest-facility-inventory")
i01 = box(6.0, 19.25, 4.2, 1.3, "01_ingest.py\ncolumn_map.csv → clean schema\n+ diff vs previous release", "step")
rel = box(11.0, 19.3, 4.4, 1.3, "inputs/raw_facility_data/<year>/\naea_inventory_<year>.csv\n(tracked snapshot)", "out")
arrow(raw, i01, "h"); arrow(i01, rel, "h")

# --- band 2: QC chain + config
group(0.4, 11.2, 10.3, 7.75, "skill: validate-facility-inventory   ·   validate_inventory.py [--publish]")
steps = [
    ("02_apply_corrections.py", "approved rows only, old_value-guarded;\nexclusions may be guarded column=value"),
    ("03_normalise.py", "community_key (canonical + aliases),\ndelivery flags"),
    ("04_detect.py", "detector registry: shared farm id, shared point,\none-digit typo, within-farm copies, spelling…"),
    ("05_boundary_check.py", "label vs city/CDP boundary — verify only:\ncommunity_distance_km · located_in_place · community_relation"),
    ("06_review_queue.py", "open flags → owner sheet (review_queue.xlsx)"),
    ("07_publish.py", "contract checks · declared derived columns · qc_status"),
]
y = 17.3; sb = []
for t, d in steps:
    sb.append(box(0.7, y, 9.7, 1.0, f"{t}\n{d}", "step", fs=9)); y -= 1.17
for a, b in zip(sb, sb[1:]): arrow(a, b)
arrow(rel, sb[0], "v")
cfg = box(11.0, 13.0, 4.4, 4.3, "inputs/inventory_qc/  (owner-controlled)\n\ncorrections.csv\naliases.csv\nremote_sites.csv\nthresholds.csv\nboundaries/*.zip\nderived_columns.csv\n\nthe ONLY place a record\nis ever changed", "cfg")
for s in sb[:4]:
    ax.add_patch(FancyArrowPatch((11.0, 15.15), (s[0] + s[2], s[1] + s[3]/2), arrowstyle="-|>", mutation_scale=12, color="#3b6ea5", lw=1.1, connectionstyle="arc3,rad=0.0"))

# --- band 3: human loop
queue = box(11.0, 9.9, 4.4, 1.1, "review_queue.xlsx\n61 open rows (2025)", "out")
owner = box(11.0, 8.1, 4.4, 1.2, "owner decides\napprove · approve with my value · reject\nremote site · exclude · ask publisher", "human")
group(11.0 - 0.2, 5.85, 4.8, 2.2, "skill: record-facility-corrections")
rec = box(11.0, 6.05, 4.4, 1.3, "record_corrections.py REVIEW.xlsx [--write]\nvalidates values + dates, reads old_value,\nasks instead of guessing", "step", fs=9)
ax.add_patch(FancyArrowPatch((sb[4][0] + sb[4][2], sb[4][1] + sb[4][3]/2), (11.0, 10.45), arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4, connectionstyle="arc3,rad=-0.25"))
arrow(queue, owner); arrow(owner, rec)
ax.add_patch(FancyArrowPatch((15.4, 6.7), (15.4, 13.0), arrowstyle="-|>", mutation_scale=14, color="#b84a4a", lw=1.6, connectionstyle="arc3,rad=-0.55"))
ax.text(15.55, 9.9, "decisions become\nrows of the config", fontsize=9, color="#b84a4a", va="center")

# --- band 4: published table
clean = box(0.7, 9.4, 9.7, 1.4, "outputs/00_inventory_qc/<year>/facilities_clean.csv   (tracked)\ncommunity_name (service community, never changed by rule) · located_in_place · community_relation\ncommunity_distance_km · qc_status (clean | pending_review) · member trail keys", "out", fs=9)
arrow(sb[5], clean)

# --- band 5: hub build
group(0.4, 0.55, 10.3, 8.75, "skills: define-network-profile  →  build-and-verify-network")
prof = box(0.7, 7.45, 9.7, 1.3, "workflows/02_network_build/profile.yaml  (hub knobs, all data)\ngroup_by [community] · cannot_link_across_community · remote_site_km 20\nmax_snap_dist_m 25000 · withhold_pending_review ON", "cfg", fs=9)
b = [prof]
for t, d in [
    ("00_normalize_raw.py", "reads the published clean table — never the raw CSV\ncarries every declared derived column"),
    ("consolidate  (mmnet/steps/consolidate.py)", "withhold pending_review → 01_withheld.csv\n50 m merge with cannot-link → 01_site_members.csv"),
    ("tag  (steps/tag.py)", "TIGER place + borough; every labelled site tested\nconflicts kept + reported → 01b_conflicts.csv"),
    ("hubs  (steps/hubs.py)", "one hub per corrected label; far site = own remote_site hub; blobs for unlabelled\n→ 02_hubs.gpkg + 02_hub_members.csv"),
    ("assemble  (assemble.py / build.py)", "snap to road/ice ≤ cap, collisions merge → 02_hub_snaps.csv\nR nodes + Python connects → 03_network"),
]:
    y = b[-1][1] - 1.3
    b.append(box(0.7, y, 9.7, 1.15, f"{t}\n{d}", "step", fs=9))
for p, q in zip(b, b[1:]): arrow(p, q)
arrow(clean, prof)
net = box(11.0, 1.3, 4.4, 1.5, "network of record\nfinal_network/ (one rebuild on the\nowner's machine; not yet run)", "out")
ax.add_patch(FancyArrowPatch((b[-1][0] + b[-1][2], b[-1][1] + b[-1][3]/2), (11.0, 2.05), arrowstyle="-|>", mutation_scale=14, color="#333", lw=1.4))

# legend
lx = 11.0; ly = 5.2
for i, (k, lab) in enumerate([("raw", "raw download"), ("cfg", "owner-controlled config"), ("step", "script / function"), ("out", "tracked or generated output"), ("human", "the one human step")]):
    fc, ec = C[k]; ax.add_patch(FancyBboxPatch((lx, ly - i*0.42), 0.5, 0.3, boxstyle="round,pad=0.01", fc=fc, ec=ec))
    ax.text(lx + 0.65, ly - i*0.42 + 0.15, lab, va="center", fontsize=9)
ax.text(8, 21.45, "Facility inventory → hubs: skills, scripts and data", ha="center", fontsize=15, fontweight="bold")
fig.savefig("inventory_flow.png", dpi=140, bbox_inches="tight", facecolor="white")
print("ok")
