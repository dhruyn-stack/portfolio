"""Generates demo/input.pdf — a two-page supplier statement with tables — so the converter can be demonstrated end to end."""
import pathlib
import random

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

random.seed(7)
out = pathlib.Path(__file__).parent / "demo"
out.mkdir(exist_ok=True)
doc = SimpleDocTemplate(str(out / "input.pdf"), pagesize=A4)
styles = getSampleStyleSheet()
items = ["Nitrile gloves (box)", "Syringe 5 ml", "Gauze roll", "IV set", "Saline 500 ml", "Thermometer", "Mask N95", "Cotton 500 g"]
rows = [["Invoice", "Date", "Item", "Qty", "Unit price", "Amount"]]
for i in range(28):
    q = random.randint(1, 40)
    p = random.choice([3.5, 12.0, 45.0, 120.0, 8.25, 15.0])
    rows.append([f"INV-{2400 + i}", f"2026-0{random.randint(1, 9)}-{random.randint(10, 28)}", random.choice(items), q, f"${p:,.2f}", f"${q * p:,.2f}"])
rows.append(rows[5])  # deliberate duplicate for the QA sheet
style = TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBF7")), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8)])
story = [Paragraph("Supplier statement — Q3 2026", styles["Title"]), Spacer(1, 8), Table(rows[:16], style=style),
         Spacer(1, 12), Paragraph("Continued", styles["Normal"]), Table([rows[0]] + rows[16:], style=style)]
doc.build(story)
print(out / "input.pdf")
