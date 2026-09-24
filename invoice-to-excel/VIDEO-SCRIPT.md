# 60-second screen recording — Invoice PDFs → Excel

Record with Windows Game Bar: **Win + Alt + R** to start/stop (saves to Videos\Captures). Full screen, no webcam.
Speak slowly or skip voice and use the on-screen text below as captions. Close WhatsApp/Gmail/other personal tabs first.

| Time | Show on screen | Say / caption |
|---|---|---|
| 0–8 s | File Explorer: the `invoices` folder with 23 PDFs; open 2 of them side by side (different layouts) | "23 supplier invoices, three different layouts." |
| 8–18 s | Terminal: `python extract.py invoices invoices.xlsx` → the one-line result | "One command reads every PDF." |
| 18–32 s | Excel: **Invoices** sheet, scroll; point at the red "TOTAL MISMATCH" cell | "Every invoice becomes a row, and every total is re-checked." |
| 32–44 s | Excel: **QA** sheet, the 3 rows | "Anything that needs a decision lands here: a duplicate, a wrong total, a missing PO." |
| 44–56 s | Excel: **Dashboard** with both charts | "And a dashboard that updates itself when rows change." |
| 56–60 s | Back to the dashboard | "Your invoices, your layouts — same result." |

Before recording: run `python extract.py invoices invoices.xlsx` once so the workbook is fresh.
Folder: `Desktop\venture-investigation\build\portfolio\invoice-to-excel\`
