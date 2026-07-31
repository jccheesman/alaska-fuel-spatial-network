"""Render the transfer-fee chapters to a standalone styled HTML for printing
to PDF. Reuses the CSS from build_pdf.py so the transfer-fee book matches the
existing blind-derivation styling.

Assembles two chapters into one document:
  05_transfer_fees.md    - original through-storage fee research
  06_connection_costs.md - storage-free rate-aware re-derivation + worked examples
"""
import markdown
from pathlib import Path

from build_pdf import CSS

DIR = Path(__file__).parent

FILES = [
    ("Chapter 5", "05_transfer_fees.md"),
    ("Chapter 6", "06_connection_costs.md"),
]

COVER = """
<div class="cover">
  <h1>Intermodal Transfer &amp; Connection Fees:<br>Alaska Bulk Fuel Delivery</h1>
  <div class="sub">Blind multi-method derivation with adversarial verification<br>
  of USD per gallon modal-handoff fees, plus the storage-free<br>
  rate-aware re-derivation and worked routing examples</div>
  <div class="meta">
    DOE MAS fuel-logistics routing model &mdash; cost-rate research<br>
    Chapters 5&ndash;6, extending the four per-gallon-mile transport-rate chapters<br>
    Blind tariff / operational / revealed-cost methods, skeptic panels,<br>
    local-document cross-check, and end-to-end route sanity checks<br><br>
    July 28, 2026
  </div>
</div>
"""

parts = [f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>", COVER]
for label, fname in FILES:
    html = markdown.markdown((DIR / fname).read_text(), extensions=["tables"])
    parts.append(f"<div class='chapter'><div class='chaplabel'>{label}</div>{html}</div>")
parts.append("</body></html>")

out = DIR / "transfer_fees.html"
out.write_text("\n".join(parts))
print(f"wrote {out}")
