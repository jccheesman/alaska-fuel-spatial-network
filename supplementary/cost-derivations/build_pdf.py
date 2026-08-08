"""Assemble the blind-derivation markdown chapters into one styled HTML file
for printing to PDF via headless Chrome."""
import markdown
from pathlib import Path

DIR = Path(__file__).parent
FILES = [
    ("", "00_executive_summary.md"),
    ("Chapter 1", "01_road.md"),
    ("Chapter 2", "02_barge.md"),
    ("Chapter 3", "03_plane.md"),
    ("Chapter 4", "04_ice_road.md"),
]

CSS = """
@page { size: letter; margin: 0.9in 0.85in; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt;
       line-height: 1.45; color: #1a1a1a; max-width: 100%; }
h1 { font-size: 17pt; border-bottom: 2px solid #24435c; padding-bottom: 6px;
     color: #24435c; margin-top: 0; }
h2 { font-size: 13pt; color: #24435c; margin-top: 1.4em; }
h3 { font-size: 11.5pt; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0;
        font-size: 8.8pt; font-family: Helvetica, Arial, sans-serif; }
th, td { border: 1px solid #b8c4cc; padding: 4px 7px; text-align: left;
         vertical-align: top; }
th { background: #e8eef2; font-weight: bold; }
tr:nth-child(even) td { background: #f6f8fa; }
code { font-family: Menlo, monospace; font-size: 9pt; background: #f2f2f2;
       padding: 1px 3px; }
blockquote { border-left: 3px solid #24435c; margin-left: 0;
             padding-left: 12px; color: #333; }
a { color: #24435c; word-break: break-all; }
.chapter { page-break-before: always; }
.chaplabel { font-family: Helvetica, Arial, sans-serif; font-size: 9pt;
             letter-spacing: 2px; text-transform: uppercase; color: #7a8a96;
             margin-bottom: 4px; }
.cover { text-align: center; margin-top: 2.2in; page-break-after: always; }
.cover h1 { border: none; font-size: 24pt; }
.cover .sub { font-size: 13pt; color: #444; margin-top: 0.6em; }
.cover .meta { font-size: 10.5pt; color: #666; margin-top: 2.5in;
               font-family: Helvetica, Arial, sans-serif; line-height: 1.7; }
"""

COVER = """
<div class="cover">
  <h1>Blind Cost Derivations:<br>Alaska Bulk Fuel Delivery by Mode</h1>
  <div class="sub">Independent open-web derivation of USD per gallon-mile
  transport rates<br>for truck, barge, plane, and ice-road fuel delivery</div>
  <div class="meta">
    DOE MAS fuel-logistics routing model &mdash; cost-rate research<br>
    Four independent research agents, three-plus methods per mode,<br>
    with full derivation logs, source tables, and decision records<br><br>
    July 15, 2026
  </div>
</div>
"""

parts = [f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>", COVER]
for label, fname in FILES:
    html = markdown.markdown((DIR / fname).read_text(), extensions=["tables"])
    wrapper = "chapter" if label else ""
    chap = f"<div class='chaplabel'>{label}</div>" if label else ""
    parts.append(f"<div class='{wrapper}'>{chap}{html}</div>")
parts.append("</body></html>")

out = DIR / "combined.html"
out.write_text("\n".join(parts))
print(f"wrote {out}")
