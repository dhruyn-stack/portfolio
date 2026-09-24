"""Renders pipeline.mp4 (1280x720, ~40 s): an explainer of the Telegram -> Apps Script -> GitHub -> Obsidian -> Claude pipeline.
Pure Python (Pillow + OpenCV); every scene is drawn, so there is no fake app UI and no personal data."""
import pathlib

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).parent
W, H, FPS = 1280, 720, 30
BG, SURF, SUNK, LINE = (14, 21, 19), (21, 32, 28), (27, 40, 36), (42, 58, 53)
INK, MUTED, ACC, WARN = (228, 238, 234), (148, 168, 161), (60, 196, 162), (240, 160, 75)
F = "C:/Windows/Fonts/"


def font(name, size):
    return ImageFont.truetype(F + name, size)


H1, H2, BODY, SMALL = font("segoeuib.ttf", 58), font("segoeuib.ttf", 40), font("segoeui.ttf", 26), font("segoeui.ttf", 21)
MONO, MONO_S, LABEL = font("consola.ttf", 22), font("consola.ttf", 19), font("consolab.ttf", 17)

STEPS = [
    ("TELEGRAM", "Capture", "Send the bot one line from your phone.",
     [("bubble", "OP poisoning: atropine vs pralidoxime,\nwhich one fixes the weakness?"), ("bot", "✓ Note dropped into your Obsidian inbox.")]),
    ("APPS SCRIPT", "Relay", "A Google Apps Script web app receives it\nand writes a Markdown file through the GitHub API.",
     [("code", "doPost(e) → text, timestamp\n→ PUT /repos/…/contents/01_INBOX/\n  Raw_Note_20260924_132147.md\n201 Created")]),
    ("GITHUB", "Store", "Every capture becomes a commit in a private repo,\nso nothing is lost and every change has history.",
     [("code", 'commit a41f9c2\n"capture: Raw_Note_20260924_132147"\n01_INBOX/Raw_Note_20260924_132147.md  +3')]),
    ("OBSIDIAN", "Sync", "The Obsidian vault is the same repo.\nA git pull brings the note into the inbox.",
     [("code", "$ git pull\n✓ 01_INBOX/Raw_Note_20260924_132147.md\n---\ncaptured: 2026-09-24 13:21:47\nsource: telegram")]),
    ("CLAUDE", "Process", "On \"check my bot inbox\", Claude links the note\nto related notes. It never invents content.",
     [("bubble", "check my bot inbox"),
      ("bot", "1 new capture: OP poisoning.\nLinked, not rewritten:\n→ Forensic Medicine / Poisons\n→ Medicine / Toxicology\n[UNVERIFIED capture]")]),
]


def base():
    im = Image.new("RGB", (W, H), BG)
    return im, ImageDraw.Draw(im)


def title_card():
    im, d = base()
    d.text((90, 150), "PERSONAL PROJECT", font=LABEL, fill=ACC)
    d.text((90, 190), "A thought on the ward,", font=H1, fill=INK)
    d.text((90, 262), "a filed note by evening.", font=H1, fill=INK)
    d.text((90, 370), "Telegram  →  Apps Script  →  GitHub  →  Obsidian  →  Claude", font=BODY, fill=MUTED)
    for i, t in enumerate(["3 free services", "0 servers", "$0 / month"]):
        x = 90 + i * 230
        d.rounded_rectangle((x, 440, x + 210, 486), radius=23, outline=LINE, width=2, fill=SURF)
        d.text((x + 105, 463), t, font=MONO_S, fill=MUTED, anchor="mm")
    return im


def step_card(k):
    lane, name, caption, blocks = STEPS[k]
    im, d = base()
    # progress rail
    for j, (ln, nm, *_rest) in enumerate(STEPS):
        x = 90 + j * 222
        on = j == k
        d.rounded_rectangle((x, 60, x + 200, 104), radius=10, fill=(22, 57, 47) if on else SURF, outline=ACC if on else LINE, width=2)
        d.text((x + 100, 82), ln, font=LABEL, fill=ACC if on else MUTED, anchor="mm")
    d.text((90, 150), f"STEP {k + 1} OF 5", font=LABEL, fill=ACC)
    d.text((90, 178), name, font=H2, fill=INK)
    d.multiline_text((90, 250), caption, font=BODY, fill=MUTED, spacing=10)
    # content panel
    x0, y = 700, 150
    d.rounded_rectangle((x0 - 30, 130, 1190, 620), radius=18, fill=SURF, outline=LINE, width=2)
    for kind, text in blocks:
        f = MONO if kind == "code" else BODY
        box = d.multiline_textbbox((0, 0), text, font=f, spacing=10)
        w, h = box[2] - box[0], box[3] - box[1]
        if kind == "bubble":
            bx = 1160 - w - 28
            d.rounded_rectangle((bx, y, 1160, y + h + 28), radius=16, fill=(28, 58, 49))
            d.multiline_text((bx + 14, y + 10), text, font=f, fill=INK, spacing=10)
        elif kind == "bot":
            d.rounded_rectangle((x0, y, x0 + w + 28, y + h + 28), radius=16, fill=SUNK)
            for i, line in enumerate(text.split("\n")):
                col = WARN if line.startswith("[") else ACC if line.startswith(("→", "✓")) else INK
                d.text((x0 + 14, y + 10 + i * (h + 10) / max(1, text.count("\n") + 1)), line, font=f, fill=col)
        else:
            d.rounded_rectangle((x0, y, 1160, y + h + 32), radius=10, fill=SUNK)
            for i, line in enumerate(text.split("\n")):
                col = ACC if line.startswith(("201", "✓")) else INK
                d.text((x0 + 16, y + 14 + i * 31), line, font=f, fill=col)
            h = len(text.split("\n")) * 31
        y += h + 60
    return im


def guard_card():
    im, d = base()
    d.text((90, 110), "GUARDRAILS", font=LABEL, fill=WARN)
    d.text((90, 140), "Automation that refuses to make things up", font=H2, fill=INK)
    rules = [("No invented facts", "a one-line capture is linked, never padded into a fake full note"),
             ("Junk stays put", "greetings, /start, truncated or duplicate captures are skipped"),
             ("Delete only after it's safe", "a raw file goes only once it is represented elsewhere"),
             ("Marked unverified", "captures live in their own UNVERIFIED file, never on flashcards"),
             ("No identifiers", "study notes only; anything identifying a person is scrubbed")]
    for i, (a, b) in enumerate(rules):
        y = 240 + i * 78
        d.rounded_rectangle((90, y, 1190, y + 64), radius=12, fill=(58, 42, 22), outline=WARN, width=1)
        d.text((116, y + 18), a, font=font("segoeuib.ttf", 24), fill=INK)
        d.text((470, y + 21), b, font=SMALL, fill=MUTED)
    return im


def end_card():
    im, d = base()
    d.text((90, 200), "The same pattern works for your business", font=H2, fill=INK)
    for i, t in enumerate(["Field teams: text a finding, get a dated record",
                           "Sales calls: a one-line note becomes a CRM update",
                           "Clinics & offices: log issues from the phone, daily summary to the manager"]):
        d.text((90, 290 + i * 48), "•  " + t, font=BODY, fill=MUTED)
    d.text((90, 500), "dhruyn-stack.github.io/portfolio/telegram-capture-bot", font=MONO, fill=ACC)
    d.text((90, 545), "Personal project · sample note shown · built on free tiers", font=SMALL, fill=MUTED)
    return im


scenes = [(title_card(), 4.0)] + [(step_card(k), 5.0) for k in range(5)] + [(guard_card(), 6.0), (end_card(), 5.0)]
out = cv2.VideoWriter(str(HERE / "pipeline.mp4"), cv2.VideoWriter_fourcc(*"avc1"), FPS, (W, H))
frames = [cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR) for im, _ in scenes]
fade = int(0.5 * FPS)
for i, ((_, dur), fr) in enumerate(zip(scenes, frames)):
    hold = int(dur * FPS) - (fade if i < len(frames) - 1 else 0)
    for _ in range(hold):
        out.write(fr)
    if i < len(frames) - 1:
        for t in range(fade):
            a = (t + 1) / fade
            out.write(cv2.addWeighted(fr, 1 - a, frames[i + 1], a, 0))
out.release()
scenes[5][0].save(HERE / "poster.png")
print("pipeline.mp4 written,", round(sum(d for _, d in scenes), 1), "s")
