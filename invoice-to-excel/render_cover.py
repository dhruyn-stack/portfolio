"""Renders cover.png (1600x1000, Upwork portfolio cover) and dashboard.png from the sample run."""
import io
import pathlib

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt
import pymupdf
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from openpyxl import load_workbook
from PIL import Image

HERE = pathlib.Path(__file__).parent
INK, MUTED, ACC, BAD, BG = "#1F2937", "#6B7280", "#1F4E78", "#C2410C", "#F7F8FA"

wb = load_workbook(HERE / "invoices.xlsx")
inv = [r for r in wb["Invoices"].iter_rows(min_row=2, values_only=True)]
qa = [r for r in wb["QA"].iter_rows(min_row=2, values_only=True)]
lines = wb["LineItems"].max_row - 1
spend_sup, spend_month = {}, {}
for r in inv:
    spend_sup[r[1]] = spend_sup.get(r[1], 0) + r[8]
    m = r[3].strftime("%b")
    key = r[3].strftime("%Y-%m")
    spend_month[key] = spend_month.get(key, 0) + r[8]


def page_img(name):
    pix = pymupdf.open(HERE / "invoices" / name)[0].get_pixmap(dpi=60)
    return Image.open(io.BytesIO(pix.tobytes("png")))


fig = plt.figure(figsize=(16, 10), dpi=100, facecolor=BG)
fig.text(0.04, 0.93, "Invoice PDFs  →  clean Excel, checked", fontsize=34, weight="bold", color=INK)
fig.text(0.04, 0.885, "23 supplier PDFs in 3 different layouts  •  71 line items  •  3 problems caught before payment",
         fontsize=15, color=MUTED)

# left: three different invoice layouts, fanned
for i, name in enumerate(["NW-2601.pdf" if (HERE / "invoices" / "NW-2601.pdf").exists() else sorted((HERE / "invoices").glob("NW-*.pdf"))[0].name,
                          sorted((HERE / "invoices").glob("BB-*.pdf"))[0].name, sorted((HERE / "invoices").glob("CL-*.pdf"))[0].name]):
    ax = fig.add_axes([0.03 + i * 0.075, 0.12 + i * 0.05, 0.24, 0.62])
    ax.imshow(page_img(name if isinstance(name, str) else name))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#CBD5E1"); s.set_linewidth(1.5)
fig.patches.append(FancyArrowPatch((0.435, 0.47), (0.49, 0.47), transform=fig.transFigure, arrowstyle="-|>",
                                   mutation_scale=40, color=ACC, lw=4))

# right: KPI tiles
kpis = [("Invoices", f"{len(inv)}"), ("Total spend", f"${sum(r[8] for r in inv):,.0f}"), ("Need a decision", f"{len(qa)}")]
for i, (k, v) in enumerate(kpis):
    x = 0.51 + i * 0.16
    fig.patches.append(FancyBboxPatch((x, 0.70), 0.145, 0.12, boxstyle="round,pad=0.005,rounding_size=0.01",
                                      transform=fig.transFigure, fc="white", ec="#E5E7EB"))
    fig.text(x + 0.012, 0.785, k, fontsize=13, color=MUTED)
    fig.text(x + 0.012, 0.725, v, fontsize=26, weight="bold", color=BAD if k == "Need a decision" else INK)

ax1 = fig.add_axes([0.53, 0.40, 0.19, 0.24])
names = [n.replace(" Ltd", "").replace(" Supply", "").replace(" Diagnostics", "") for n in spend_sup]
ax1.barh(names, list(spend_sup.values()), color=ACC)
ax1.set_title("Spend by supplier", loc="left", fontsize=13, color=INK)
ax2 = fig.add_axes([0.77, 0.40, 0.19, 0.24])
ks = sorted(spend_month)
import datetime as _d
ax2.plot([_d.date(int(k[:4]), int(k[5:]), 1).strftime("%b") for k in ks], [spend_month[k] for k in ks], color=ACC, lw=2.5, marker="o")
ax2.set_title("Spend by month", loc="left", fontsize=13, color=INK)
for ax in (ax1, ax2):
    ax.set_facecolor("white")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=10, colors=MUTED)
ax1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:.0f}k"))
ax1.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(4))
ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"${v / 1000:.0f}k"))

# right: QA findings
fig.patches.append(FancyBboxPatch((0.51, 0.10), 0.45, 0.22, boxstyle="round,pad=0.005,rounding_size=0.01",
                                  transform=fig.transFigure, fc="#FFF7ED", ec="#FDBA74"))
fig.text(0.525, 0.285, "QA sheet — flagged for a human decision", fontsize=14, weight="bold", color=BAD)
for i, r in enumerate(qa[:3]):
    fig.text(0.525, 0.235 - i * 0.045, f"• {r[1]}: {r[2]}", fontsize=12.5, color=INK)
fig.text(0.04, 0.035, "Portfolio demo with fictional suppliers and figures. Python (PyMuPDF + openpyxl); dashboard uses live Excel formulas.",
         fontsize=11, color=MUTED)
fig.savefig(HERE / "cover.png", facecolor=BG)
print("cover.png written")
