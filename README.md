# Portfolio — data cleanup, document conversion, spreadsheet & workflow automation

Four small, real, runnable samples. Each is the kind of thing I deliver in 24–72 hours with documentation.

| Sample | What it shows | Run it |
|---|---|---|
| [`pdf-to-excel/`](pdf-to-excel) | PDF tables → clean Excel: one sheet per table, numbers parsed from `$1,234.50`, bold headers, frozen panes, a **QA sheet** flagging duplicates and empty cells. `demo/input.pdf` → `demo/output.xlsx` | `python convert.py demo/input.pdf demo/output.xlsx` |
| [`excel-dashboard/`](excel-dashboard) | Sales dashboard driven entirely by live `SUMIFS/COUNTIFS/AVERAGEIFS` over a 360-row Data sheet, with a monthly trend chart and a category chart. Change the data, the dashboard updates. | `python build_dashboard.py` → `sales_dashboard.xlsx` |
| [`n8n-lead-router/`](n8n-lead-router) | Importable n8n workflow: web form → normalise → qualify (email + budget) → append to Google Sheets → Gmail alert with an A/B/C lead tier; rejected leads logged separately. | Import `lead-router.json` in n8n, set the sheet ID and credentials |
| [`scraper/`](scraper) | Polite catalogue scraper (1 req/s, retries, custom user-agent) → `books.csv` with title, price, rating, stock. Target site is published for scraping practice. | `python scrape_books.py 3` |

Requirements: Python 3.10+, `pip install pymupdf openpyxl reportlab`. No API keys needed for any sample.

How I work: scope in one message → free sample on anything ambiguous → deliver with a short README → you own
everything (scripts, workbooks, workflows) and can run them without me.
