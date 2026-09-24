#!/usr/bin/env python
"""Folder of supplier invoice PDFs (any of 3 layouts) -> one Excel workbook with a QA sheet and a live dashboard.

Usage:  python extract.py invoices/ invoices.xlsx
Sheets:
  Invoices   one row per PDF: supplier, invoice no, date, PO, subtotal, tax, total, and the sum of its own line items
  LineItems  every line: invoice no, description, qty, unit price, amount
  QA         what needs a human decision: duplicate invoices, totals that don't match their lines, missing PO numbers
  Dashboard  spend by supplier and by month, built from SUMIFS formulas and native Excel charts (updates if rows change)
"""
import datetime as dt
import pathlib
import re
import sys

import pymupdf as fitz
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill

MM = 72 / 25.4
HEAD = PatternFill("solid", fgColor="1F4E78")
RED = PatternFill("solid", fgColor="F8CBAD")
FIELDS = {
    "no": [r"Invoice No:\s*(\S+)", r"Bill No\.\s*(\S+)", r"Invoice #:\s*(\S+)"],
    "po": [r"PO Number:\s*(PO-\d+)", r"Customer PO:\s*(PO-\d+)", r"Purchase Order:\s*(PO-\d+)"],
    "date": [r"Invoice Date:\s*(\d{2}/\d{2}/\d{4})", r"Dated\s+([A-Z][a-z]{2} \d{2}, \d{4})", r"Date:\s*(\d{4}-\d{2}-\d{2})"],
}
DATE_FORMATS = ["%d/%m/%Y", "%b %d, %Y", "%Y-%m-%d"]


def money(s):
    return float(s.replace("$", "").replace(",", ""))


def first(patterns, text):
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def parse_date(s):
    for f in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, f).date()
        except (TypeError, ValueError):
            pass
    return None


def parse(pdf):
    page = fitz.open(pdf)[0]
    text = page.get_text()
    supplier = next(l for l in text.splitlines() if "(fictional)" in l and not l.startswith("Sample"))
    rec = {"file": pdf.name, "supplier": supplier.replace(" (fictional)", ""),
           "no": first(FIELDS["no"], text), "po": first(FIELDS["po"], text), "date": parse_date(first(FIELDS["date"], text))}
    for key, label in [("subtotal", "Subtotal"), ("tax", r"Tax \(\d+%\)"), ("total", "TOTAL DUE")]:
        m = re.search(label + r"\s*\n?\s*(\$[\d,]+\.\d{2})", text)
        rec[key] = money(m.group(1)) if m else None
    # line items: group words by baseline, then split into 4 columns by x position
    rows = {}
    for x0, y0, x1, y1, word, *_ in page.get_text("words"):
        rows.setdefault(round(y1), []).append((x0, word))
    lines = []
    for y in sorted(rows):
        cells = {"desc": [], "qty": [], "price": [], "amount": []}
        for x, w in sorted(rows[y]):
            col = "desc" if x < 105 * MM else "qty" if x < 133 * MM else "price" if x < 160 * MM else "amount"
            cells[col].append(w)
        q, p, a = (" ".join(cells[k]) for k in ("qty", "price", "amount"))
        if q.isdigit() and p.startswith("$") and a.startswith("$"):
            lines.append([rec["no"], " ".join(cells["desc"]), int(q), money(p), money(a)])
    rec["line_sum"] = round(sum(l[4] for l in lines), 2)
    return rec, lines


def style_header(ws):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
        c.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(42, max(11, max(len(str(c.value or "")) for c in col) + 2))


def build(folder, out):
    pdfs = sorted(pathlib.Path(folder).glob("*.pdf"))
    wb = Workbook()
    inv = wb.active
    inv.title = "Invoices"
    inv.append(["File", "Supplier", "Invoice No", "Date", "Month", "PO Number", "Subtotal", "Tax", "Total", "Lines + 8% tax", "Check"])
    li = wb.create_sheet("LineItems")
    li.append(["Invoice No", "Description", "Qty", "Unit price", "Amount"])
    qa = wb.create_sheet("QA")
    qa.append(["File", "Invoice No", "Issue", "What to decide"])
    seen = {}
    for pdf in pdfs:
        rec, lines = parse(pdf)
        r = inv.max_row + 1
        inv.append([rec["file"], rec["supplier"], rec["no"], rec["date"], None, rec["po"], rec["subtotal"], rec["tax"],
                    rec["total"], None, None])
        inv.cell(r, 5).value = f'=TEXT(D{r},"yyyy-mm")'
        inv.cell(r, 10).value = round(rec["line_sum"] * 1.08, 2)
        inv.cell(r, 11).value = f'=IF(ABS(I{r}-J{r})>0.01,"TOTAL MISMATCH","ok")'
        inv.cell(r, 4).number_format = "yyyy-mm-dd"
        for c in (7, 8, 9, 10):
            inv.cell(r, c).number_format = '"$"#,##0.00'
        for l in lines:
            li.append(l)
        key = (rec["supplier"], rec["no"])
        if key in seen:
            qa.append([rec["file"], rec["no"], f"Duplicate of {seen[key]}", "Same supplier + invoice number: pay once, file the copy"])
        else:
            seen[key] = rec["file"]
        if rec["total"] is not None and abs(rec["total"] - round(rec["line_sum"] * 1.08, 2)) > 0.01:
            qa.append([rec["file"], rec["no"], f"Stated total ${rec['total']:,.2f} vs lines + tax ${rec['line_sum'] * 1.08:,.2f}",
                       "Ask the supplier for a corrected invoice before paying"])
        if not rec["po"]:
            qa.append([rec["file"], rec["no"], "No PO number", "Match to a purchase order or get approval"])
    inv.conditional_formatting.add(f"K2:K{inv.max_row}", FormulaRule(formula=['K2<>"ok"'], fill=RED))
    for ws in (inv, li, qa):
        style_header(ws)
    for r in li.iter_rows(min_row=2, min_col=4, max_col=5):
        for c in r:
            c.number_format = '"$"#,##0.00'

    # Dashboard: formulas only, so it recalculates if the client edits or adds rows
    db = wb.create_sheet("Dashboard", 0)
    db["A1"] = "Supplier spend dashboard (sample data)"
    db["A1"].font = Font(bold=True, size=16, color="1F4E78")
    n = inv.max_row
    db["A3"], db["B3"] = "Invoices processed", f"=COUNTA(Invoices!C2:C{n})"
    db["A4"], db["B4"] = "Total spend", f"=SUM(Invoices!I2:I{n})"
    db["A5"], db["B5"] = "Items needing a decision", f"=COUNTA(QA!A2:A{qa.max_row})"
    db["B4"].number_format = '"$"#,##0.00'
    suppliers = sorted({c.value for c in inv["B"][1:]})
    db["A7"], db["B7"] = "Supplier", "Spend"
    for i, s in enumerate(suppliers, 8):
        db.cell(i, 1, s)
        db.cell(i, 2, f'=SUMIFS(Invoices!$I$2:$I${n},Invoices!$B$2:$B${n},A{i})').number_format = '"$"#,##0'
    months = sorted({c.value.strftime("%Y-%m") for c in inv["D"][1:] if c.value})
    m0 = 8 + len(suppliers) + 2
    db.cell(m0 - 1, 1, "Month"), db.cell(m0 - 1, 2, "Spend")
    for i, m in enumerate(months, m0):
        db.cell(i, 1, m)
        db.cell(i, 2, f'=SUMIFS(Invoices!$I$2:$I${n},Invoices!$E$2:$E${n},A{i})').number_format = '"$"#,##0'
    for c in (db["A7"], db["B7"], db.cell(m0 - 1, 1), db.cell(m0 - 1, 2)):
        c.font, c.fill = Font(bold=True, color="FFFFFF"), HEAD
    db.column_dimensions["A"].width, db.column_dimensions["B"].width = 34, 14
    bar = BarChart(); bar.title = "Spend by supplier"; bar.y_axis.title = "USD"; bar.legend = None
    bar.add_data(Reference(db, min_col=2, min_row=7, max_row=7 + len(suppliers)), titles_from_data=True)
    bar.set_categories(Reference(db, min_col=1, min_row=8, max_row=7 + len(suppliers)))
    bar.height, bar.width = 7, 14
    db.add_chart(bar, "D3")
    line = LineChart(); line.title = "Spend by month"; line.y_axis.title = "USD"; line.legend = None
    line.add_data(Reference(db, min_col=2, min_row=m0 - 1, max_row=m0 + len(months) - 1), titles_from_data=True)
    line.set_categories(Reference(db, min_col=1, min_row=m0, max_row=m0 + len(months) - 1))
    line.height, line.width = 7, 14
    db.add_chart(line, "D18")
    wb.save(out)
    return len(pdfs), li.max_row - 1, qa.max_row - 1


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "invoices"
    out = sys.argv[2] if len(sys.argv) > 2 else "invoices.xlsx"
    n, lines, issues = build(folder, out)
    print(f"{n} PDFs -> {out}: {lines} line items, {issues} QA issues")
