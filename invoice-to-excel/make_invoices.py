"""Generates 24 sample supplier invoices (3 different layouts, fictional companies) into invoices/.

Three problems are planted on purpose so the QA sheet has something real to catch:
  - one invoice is sent twice (same number, same supplier)
  - one invoice's stated total does not match its line items
  - one invoice has no PO number
"""
import datetime as dt
import pathlib
import random
import shutil

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

random.seed(24)
OUT = pathlib.Path(__file__).parent / "invoices"
OUT.mkdir(exist_ok=True)

SUPPLIERS = {
    "A": ("Northwind Medical Supply (fictional)", "NW", ["Nitrile gloves, box of 100", "Syringe 5 ml, pack of 50", "Gauze roll 10 cm",
                                                          "IV giving set", "Saline 0.9% 500 ml", "Digital thermometer"]),
    "B": ("Bluebay Office & Print Ltd (fictional)", "BB", ["A4 paper, box of 5 reams", "Toner cartridge 26A", "Label roll 62 mm",
                                                           "Binder clips, pack of 48", "Printed appointment cards x500"]),
    "C": ("Cedar Lab Diagnostics (fictional)", "CL", ["CBC reagent kit", "Glucose test strips x50", "Urine dipsticks x100",
                                                      "Specimen containers x100", "Pipette tips 200 ul x1000"]),
}
PRICES = [4.5, 7.25, 12.0, 18.9, 26.0, 39.5, 64.0, 88.0, 120.0]
TAX = 0.08


def lines_for(sup):
    items = random.sample(SUPPLIERS[sup][2], k=random.randint(2, 4))
    return [(it, random.randint(1, 24), random.choice(PRICES)) for it in items]


def money(x):
    return f"${x:,.2f}"


def draw(inv):
    c = canvas.Canvas(str(OUT / f"{inv['no']}.pdf"), pagesize=A4)
    w, h = A4
    name = SUPPLIERS[inv["sup"]][0]
    sub = round(sum(q * p for _, q, p in inv["lines"]), 2)
    tax = round(sub * TAX, 2)
    total = inv.get("total_override") or round(sub + tax, 2)
    if inv["sup"] == "A":  # layout A: header block left, meta right, classic table
        c.setFont("Helvetica-Bold", 16); c.drawString(20 * mm, h - 25 * mm, name)
        c.setFont("Helvetica", 9); c.drawString(20 * mm, h - 31 * mm, "12 Harbour Road, Springfield (fictional address)")
        c.setFont("Helvetica-Bold", 20); c.drawRightString(w - 20 * mm, h - 25 * mm, "INVOICE")
        c.setFont("Helvetica", 10)
        meta = [("Invoice No:", inv["no"]), ("Invoice Date:", inv["date"].strftime("%d/%m/%Y")), ("PO Number:", inv["po"] or "")]
        for i, (k, v) in enumerate(meta):
            c.drawRightString(w - 60 * mm, h - (35 + 6 * i) * mm, k); c.drawString(w - 57 * mm, h - (35 + 6 * i) * mm, v)
        y = h - 70 * mm
        cols = [20, 110, 135, 165]
        c.setFillColor(colors.HexColor("#DDEBF7")); c.rect(18 * mm, y - 2 * mm, w - 36 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 10)
        for x, t in zip(cols, ["Description", "Qty", "Unit Price", "Amount"]):
            c.drawString(x * mm, y, t)
    elif inv["sup"] == "B":  # layout B: centred title, meta as a line, different labels
        c.setFont("Helvetica-Bold", 14); c.drawCentredString(w / 2, h - 22 * mm, name)
        c.setFont("Helvetica-Bold", 12); c.drawCentredString(w / 2, h - 30 * mm, "TAX INVOICE")
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, h - 42 * mm, f"Bill No. {inv['no']}    Dated {inv['date'].strftime('%b %d, %Y')}    "
                                           f"Customer PO: {inv['po'] or '-'}")
        y = h - 58 * mm
        cols = [20, 115, 140, 168]
        c.setFont("Helvetica-Bold", 10)
        for x, t in zip(cols, ["Item", "Quantity", "Rate", "Line Total"]):
            c.drawString(x * mm, y, t)
        c.line(18 * mm, y - 2 * mm, w - 18 * mm, y - 2 * mm)
    else:  # layout C: meta on the left in a box, table further down
        c.setFont("Helvetica-Bold", 15); c.drawString(20 * mm, h - 22 * mm, name)
        c.rect(20 * mm, h - 52 * mm, 80 * mm, 24 * mm)
        c.setFont("Helvetica", 10)
        c.drawString(23 * mm, h - 34 * mm, f"Invoice #: {inv['no']}")
        c.drawString(23 * mm, h - 40 * mm, f"Date: {inv['date'].isoformat()}")
        c.drawString(23 * mm, h - 46 * mm, f"Purchase Order: {inv['po'] or ''}")
        y = h - 70 * mm
        cols = [20, 112, 138, 166]
        c.setFont("Helvetica-Bold", 10)
        for x, t in zip(cols, ["Product", "Units", "Price", "Total"]):
            c.drawString(x * mm, y, t)
        c.line(18 * mm, y - 2 * mm, w - 18 * mm, y - 2 * mm)
    c.setFont("Helvetica", 10)
    for i, (it, q, p) in enumerate(inv["lines"], 1):
        yy = y - 9 * mm * i
        c.drawString(cols[0] * mm, yy, it); c.drawString(cols[1] * mm, yy, str(q))
        c.drawString(cols[2] * mm, yy, money(p)); c.drawString(cols[3] * mm, yy, money(q * p))
    yy = y - 9 * mm * (len(inv["lines"]) + 2)
    for k, v in [("Subtotal", sub), (f"Tax ({int(TAX * 100)}%)", tax), ("TOTAL DUE", total)]:
        c.setFont("Helvetica-Bold" if k == "TOTAL DUE" else "Helvetica", 10)
        c.drawRightString(160 * mm, yy, k); c.drawRightString(w - 20 * mm, yy, money(v)); yy -= 7 * mm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, 15 * mm, "Sample invoice generated for a portfolio demo. Company, address and figures are fictional.")
    c.save()


invoices = []
start = dt.date(2026, 3, 2)
for i in range(22):
    sup = random.choice("ABC")
    no = f"{SUPPLIERS[sup][1]}-{2601 + i}"
    invoices.append({"sup": sup, "no": no, "date": start + dt.timedelta(days=random.randint(0, 180)),
                     "po": f"PO-{4100 + i}", "lines": lines_for(sup)})
invoices[6]["po"] = None                                   # planted: missing PO number
bad = invoices[11]
bad["total_override"] = round(sum(q * p for _, q, p in bad["lines"]) * (1 + TAX) + 50, 2)  # planted: total != lines
for inv in invoices:
    draw(inv)
# planted: the same invoice arrives twice, under a different file name, as supplier re-sends do
shutil.copy(OUT / f"{invoices[3]['no']}.pdf", OUT / f"{invoices[3]['no']}_resent.pdf")
print(f"{len(list(OUT.glob('*.pdf')))} invoices in {OUT}")
