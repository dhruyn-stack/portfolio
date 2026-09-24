"""Renders capture-pipeline.mp4: a red-and-white explainer built around REAL footage of the pipeline.

Real material (cropped, never edited in content):
  assets/telegram.mp4 source  -> the screen recording of sending a note to the bot (typing sped up 2.5x, labelled)
  assets/obsidian-note.png    -> the note as it landed in the Obsidian inbox
  assets/claude-triage.png    -> Claude processing the inbox ("check telegram message from bot")
Drawn material: the title, the Apps Script -> GitHub relay diagram (backend, nothing to film), the rules and end card.
Pure Python: Pillow draws, OpenCV encodes H.264.
"""
import math
import pathlib
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).parent
ASSETS = HERE / "assets"
REC = pathlib.Path(__import__("os").environ.get("REC") or (sys.argv[1] if len(sys.argv) > 1 else ASSETS / "telegram-recording.mp4"))
OUT = HERE / "capture-pipeline.mp4"
W, H, FPS = 1280, 720, 30

WHITE, PAPER, INK, GREY, RED, RED_SOFT, LINE = (255, 255, 255), (250, 247, 246), (17, 17, 17), (110, 104, 104), (214, 40, 57), (253, 234, 236), (232, 224, 224)
FD = "C:/Windows/Fonts/"
BLACK = __import__('functools').lru_cache(None)(lambda s: ImageFont.truetype(FD + "seguibl.ttf", s))     # Segoe UI Black: headlines
BOLD = __import__('functools').lru_cache(None)(lambda s: ImageFont.truetype(FD + "segoeuib.ttf", s))     # Segoe UI Bold
SEMI = __import__('functools').lru_cache(None)(lambda s: ImageFont.truetype(FD + "seguisb.ttf", s))      # Segoe UI Semibold
HAND = __import__('functools').lru_cache(None)(lambda s: ImageFont.truetype(FD + "segoeprb.ttf", s))     # Segoe Print Bold: red-pen notes
MONO = __import__('functools').lru_cache(None)(lambda s: ImageFont.truetype(FD + "consolab.ttf", s))


# ---------- easing + primitives ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def prog(t, start, dur):
    return clamp((t - start) / dur)


from functools import lru_cache


@lru_cache(maxsize=32)
def rounded_mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=r, fill=255)
    return m


def card(img, radius=16, border=RED, bw=0):
    """Returns (RGBA card with rounded corners, RGBA soft shadow) for pasting."""
    img = img.convert("RGBA")
    w, h = img.size
    m = rounded_mask((w, h), radius)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(img, (0, 0), m)
    if bw:
        ImageDraw.Draw(out).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, outline=border, width=bw)
    return out, shadow((w, h), radius)


@lru_cache(maxsize=32)
def shadow(size, radius):
    w, h = size
    pad = 40
    sh = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), radius=radius, fill=(120, 20, 30, 60))
    return sh.filter(ImageFilter.GaussianBlur(18))


def paste_card(canvas, c, sh, x, y):
    canvas.alpha_composite(sh, (int(x) - 40, int(y) - 40))
    canvas.alpha_composite(c, (int(x), int(y)))


def partial_rect(d, box, frac, color=RED, width=5, r=10):
    """Red-marker rectangle drawn clockwise up to `frac` of its perimeter."""
    x0, y0, x1, y1 = box
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(4)]
    total, left = sum(seg), sum(seg) * clamp(frac)
    path = [pts[0]]
    for i in range(4):
        if left <= 0:
            break
        step = min(seg[i], left)
        a, b = pts[i], pts[i + 1]
        f = step / seg[i]
        path.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        left -= step
    if len(path) > 1:
        d.line(path, fill=color, width=width, joint="curve")


def arrow(d, p0, p1, frac, color=RED, width=5, bend=0.18):
    """Hand-drawn curved arrow from p0 towards p1, drawn up to `frac`."""
    if frac <= 0:
        return
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = -(p1[1] - p0[1]), p1[0] - p0[0]
    c = (mx + nx * bend, my + ny * bend)
    n = 40
    k = max(2, int(n * clamp(frac)))
    pts = []
    for i in range(k):
        t = i / (n - 1)
        pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1]))
    d.line(pts, fill=color, width=width, joint="curve")
    if frac >= 0.98:
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        ang = math.atan2(by - ay, bx - ax)
        for s in (2.6, -2.6):
            d.line([(bx, by), (bx + 18 * math.cos(ang + s), by + 18 * math.sin(ang + s))], fill=color, width=width)


def type_text(d, xy, text, frac, font, fill=RED):
    n = int(len(text) * clamp(frac))
    if n:
        d.text(xy, text[:n], font=font, fill=fill)


def chip(d, xy, text, frac=1.0, fill=RED, fg=WHITE, font=None):
    font = font or BOLD(17)
    if frac <= 0:
        return
    x, y = xy
    w = d.textlength(text, font=font) + 28
    d.rounded_rectangle((x, y, x + w * ease_out(frac), y + 34), radius=17, fill=fill)
    if frac > 0.6:
        d.text((x + 14, y + 17), text, font=font, fill=fg, anchor="lm")


def slide_words(canvas, d, words_lines, x, y, t, start, font, lh, fill=INK, stagger=0.09, dur=0.45):
    """Headline words rising into place one by one."""
    k = 0
    for li, line in enumerate(words_lines):
        cx = x
        for word in line.split(" "):
            p = ease_out(prog(t, start + k * stagger, dur))
            if p > 0:
                col = tuple(int(255 + (c - 255) * p) for c in fill)
                d.text((cx, y + li * lh + (1 - p) * 26), word, font=font, fill=col)
            cx += d.textlength(word + " ", font=font)
            k += 1


def base(t=0.0):
    im = Image.new("RGBA", (W, H), WHITE + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 8), fill=RED)  # red top rule, the house mark
    return im, d


def step_head(d, t, num, label, title):
    chip(d, (60, 38), f"{num}  {label}", prog(t, 0.15, 0.4))
    slide_words(None, d, [title], 60, 86, t, 0.3, BLACK(40), 50)


# ---------- load real material ----------
tg_frames = []
cap = cv2.VideoCapture(str(REC))
while True:
    ok, f = cap.read()
    if not ok:
        break
    rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    comp = np.vstack([rgb[0:48, 0:640], np.full((3, 640, 3), 40, np.uint8), rgb[770:996, 0:640]])
    tg_frames.append(Image.fromarray(comp))
TG_SCALE = 1.55
TG_W, TG_H = int(640 * TG_SCALE), int(tg_frames[0].height * TG_SCALE)
SEND_F, REPLY_F = 412, 474          # measured: bubble appears at frame 412, bot reply at 474 (30 fps) -> 2.07 s
TYPE_SPEED = 2.5

claude = Image.open(ASSETS / "claude-triage.png").convert("RGB")      # 795 x 825 crop
obs = Image.open(ASSETS / "obsidian-note.png").convert("RGB")          # 1000 x 200 crop
CLAUDE_086 = claude  # shown at 100% so the text stays readable


# ---------- scenes: each returns an RGBA frame for local time t ----------
def s_title(t):
    im, d = base()
    chip(d, (60, 150), "PERSONAL PROJECT  ·  REAL FOOTAGE", prog(t, 0.1, 0.4), fill=INK)
    slide_words(im, d, ["From one line on Telegram", "to a filed, checked note."], 60, 205, t, 0.35, BLACK(64), 80)
    u = ease_out(prog(t, 1.5, 0.6))
    if u:
        x0 = 60 + d.textlength("From ", font=BLACK(64))
        x1 = x0 + d.textlength("one line", font=BLACK(64))
        d.line([(x0, 292), (x0 + (x1 - x0) * u, 290)], fill=RED, width=9)
    flow = "Telegram bot  →  Google Apps Script  →  GitHub  →  Obsidian  →  Claude"
    p = ease_out(prog(t, 1.9, 0.6))
    d.text((60, 400 + (1 - p) * 16), flow, font=SEMI(26), fill=tuple(int(255 + (c - 255) * p) for c in GREY))
    type_text(d, (60, 470), "everything you'll see next is real, just cropped", prog(t, 2.5, 1.2), HAND(30))
    return im


def s_capture(t):
    im, d = base()
    step_head(d, t, "01", "CAPTURE", "I type one line to my Telegram bot")
    enter = ease_out(prog(t, 0.2, 0.6))
    x, y = 144, 190 + (1 - enter) * 60
    tp = t - 0.6
    if tp < 0:
        fi = 0
    elif tp < SEND_F / 30 / TYPE_SPEED:
        fi = int(tp * TYPE_SPEED * 30)
    else:
        fi = int(SEND_F + (tp - SEND_F / 30 / TYPE_SPEED) * 30)
    fi = min(fi, len(tg_frames) - 1)
    frame = tg_frames[fi].resize((TG_W, TG_H), Image.BILINEAR)
    c, sh = card(frame, 14, bw=0)
    paste_card(im, c, sh, x, y)
    d = ImageDraw.Draw(im)
    typing_end = 0.6 + SEND_F / 30 / TYPE_SPEED
    reply_t = typing_end + (REPLY_F - SEND_F) / 30
    if 0.8 < t < typing_end:
        chip(d, (x + TG_W - 150, y + 60), "sped up 2.5×", 1.0, fill=INK)
    s = TG_SCALE
    ub = (x + 50 * s, y + (48 + 3 + 858 - 770) * s - 4, x + 485 * s, y + (48 + 3 + 905 - 770) * s + 4)
    rb = (x + 50 * s, y + (48 + 3 + 912 - 770) * s - 4, x + 386 * s, y + (48 + 3 + 948 - 770) * s + 4)
    if t > typing_end + 0.1:
        partial_rect(d, ub, prog(t, typing_end + 0.1, 0.6))
    if t > reply_t + 0.15:
        partial_rect(d, rb, prog(t, reply_t + 0.15, 0.6))
        arrow(d, (870, 668), (rb[2] + 14, (rb[1] + rb[3]) / 2), prog(t, reply_t + 0.5, 0.5))
        type_text(d, (890, 648), "bot confirms in 2 seconds", prog(t, reply_t + 0.9, 0.9), HAND(28))
    return im


NODES = [("Telegram bot", "sends the text\nto a webhook"), ("Google Apps Script", "doPost(e) adds a\ntimestamp"), ("GitHub repo", "saved as a commit in\n01_INBOX/Raw_Note_…md")]


def s_relay(t):
    im, d = base()
    step_head(d, t, "02", "RELAY", "Apps Script files it in GitHub. No server.")
    xs = [110, 500, 890]
    for i, (name, sub) in enumerate(NODES):
        p = ease_out(prog(t, 0.5 + i * 0.35, 0.5))
        if p <= 0:
            continue
        x, y = xs[i], 250 + (1 - p) * 40
        d.rounded_rectangle((x, y, x + 280, y + 150), radius=18, fill=WHITE, outline=RED, width=4)
        d.text((x + 140, y + 48), name, font=BOLD(26), fill=INK, anchor="mm")
        d.multiline_text((x + 140, y + 104), sub, font=SEMI(19), fill=GREY, anchor="mm", align="center", spacing=6)
    for i in range(2):
        a = prog(t, 1.5 + i * 0.5, 0.4)
        x0, x1 = xs[i] + 290, xs[i + 1] - 10
        if a:
            d.line([(x0, 325), (x0 + (x1 - x0) * ease_out(a), 325)], fill=INK, width=4)
            if a >= 1:
                d.polygon([(x1, 325), (x1 - 16, 315), (x1 - 16, 335)], fill=INK)
    # a red dot carries the note along the path, twice
    cyc = (t - 2.6) % 2.2 if t > 2.6 else -1
    if cyc >= 0:
        u = ease_io(clamp(cyc / 1.8))
        px = 250 + (1030 - 250) * u
        d.ellipse((px - 13, 312, px + 13, 338), fill=RED)
    type_text(d, (110, 470), "every note is a commit, so nothing is ever lost", prog(t, 3.0, 1.2), HAND(30))
    chip(d, (110, 560), "free tiers only  ·  $0 / month", prog(t, 3.6, 0.4), fill=INK)
    return im


def s_sync(t):
    im, d = base()
    step_head(d, t, "03", "SYNC", "It lands in my Obsidian vault")
    enter = ease_out(prog(t, 0.2, 0.6))
    cw, ch = 1100, 220
    z = ease_io(prog(t, 2.0, 2.6))
    fx0, fy0, fx1, fy1 = 0, 0, 1000, 200
    tx0, ty0, tx1, ty1 = 400, 88, 960, 200
    box = (fx0 + (tx0 - fx0) * z, fy0 + (ty0 - fy0) * z, fx1 + (tx1 - fx1) * z, fy1 + (ty1 - fy1) * z)
    view = obs.crop(tuple(int(v) for v in box)).resize((cw, ch), Image.BILINEAR)
    c, sh = card(view, 16, border=LINE, bw=2)
    x, y = 90, 200 + (1 - enter) * 60
    paste_card(im, c, sh, x, y)
    d = ImageDraw.Draw(im)
    if t > 4.8:
        partial_rect(d, (x + 20, y + 40, x + cw - 20, y + ch - 20), prog(t, 4.8, 0.6))
        arrow(d, (330, 572), (420, y + ch + 6), prog(t, 5.3, 0.4))
        type_text(d, (350, 548), "timestamped file, my exact words, nothing added", prog(t, 5.6, 1.1), HAND(28))
    return im


# source-crop highlight boxes in claude-triage.png (x0, y0, x1, y1), with the left-column note for each
HL = [((6, 124, 250, 154), "Reads every new capture", 0.9),
      ((16, 230, 300, 262), "Ignores junk like /start", 2.6),
      ((6, 442, 752, 494), "Too thin? Leaves it for me\ninstead of inventing a note", 5.2),
      ((6, 494, 786, 622), "Offers the next step;\nI decide", 8.0)]


def s_triage(t):
    im, d = base()
    step_head(d, t, "04", "TRIAGE", "Claude checks the inbox, and knows when to stop")
    scale = 1.0
    cw = int(claude.width * scale)
    vis_h = 560
    pan = ease_io(prog(t, 3.4, 2.2)) * 0.55 + ease_io(prog(t, 7.2, 1.8)) * 0.45
    max_off = claude.height * scale - vis_h
    off = pan * max_off
    full = CLAUDE_086
    view = full.crop((0, int(off), cw, int(off) + vis_h))
    enter = ease_out(prog(t, 0.2, 0.6))
    x, y = 470, 140 + (1 - enter) * 50
    c, sh = card(view, 16, border=LINE, bw=2)
    paste_card(im, c, sh, x, y)
    d = ImageDraw.Draw(im)
    for i, (bx, note, start) in enumerate(HL):
        if t < start:
            continue
        box = (x + bx[0] * scale - 4, y + bx[1] * scale - off - 4, x + bx[2] * scale + 4, y + bx[3] * scale - off + 4)
        if box[1] >= y and box[3] <= y + vis_h:
            partial_rect(d, box, prog(t, start, 0.6))
        ny = 175 + i * 118
        p = ease_out(prog(t, start + 0.2, 0.5))
        d.ellipse((60, ny + 4, 88, ny + 32), fill=RED)
        d.text((74, ny + 18), str(i + 1), font=BOLD(18), fill=WHITE, anchor="mm")
        col = tuple(int(255 + (cc - 255) * p) for cc in INK)
        d.multiline_text((104, ny), note, font=BOLD(26), fill=col, spacing=4)
    return im


RULES = ["Never invents facts", "Skips junk like /start", "Thin notes wait for a human", "No patient identifiers"]


def s_rules(t):
    im, d = base()
    chip(d, (60, 38), "RULES IT FOLLOWS", prog(t, 0.15, 0.4))
    slide_words(im, d, ["Guardrails, not guesswork"], 60, 86, t, 0.3, BLACK(48), 56)
    for i, r in enumerate(RULES):
        s = 0.9 + i * 0.5
        p = ease_out(prog(t, s, 0.5))
        if p <= 0:
            continue
        y = 200 + i * 105
        d.rounded_rectangle((60, y, 60 + 720 * p, y + 80), radius=16, fill=RED_SOFT)
        tk = prog(t, s + 0.25, 0.35)
        pts = [(92, y + 42), (106, y + 56), (132, y + 26)]
        if tk > 0:
            k = 2 if tk < 0.5 else 3
            d.line(pts[:k], fill=RED, width=7, joint="curve")
        if p > 0.5:
            d.text((160, y + 40), r, font=BOLD(30), fill=INK, anchor="lm")
    type_text(d, (840, 300), "written into the vault's\nrules file, so it follows\nthem every single time", 0, HAND(28))
    txt = "written into the vault's rules\nfile, followed every time"
    n = int(len(txt) * prog(t, 2.9, 1.2))
    d.multiline_text((840, 290), txt[:n], font=HAND(28), fill=RED, spacing=10)
    return im


def s_end(t):
    im, d = base()
    slide_words(im, d, ["Same pattern, your business."], 60, 120, t, 0.2, BLACK(54), 64)
    uses = ["Field notes from a phone  →  dated records", "One line after a sales call  →  CRM update", "Staff logs an issue  →  daily summary for the manager"]
    for i, u in enumerate(uses):
        p = ease_out(prog(t, 0.9 + i * 0.35, 0.45))
        if p:
            d.text((60 + (1 - p) * 30, 240 + i * 58), u, font=SEMI(30), fill=tuple(int(255 + (c - 255) * p) for c in INK))
    p = ease_out(prog(t, 2.2, 0.5))
    if p:
        d.rounded_rectangle((60, 470, 60 + 860 * p, 540), radius=14, fill=RED)
        if p > 0.9:
            d.text((86, 505), "dhruyn-stack.github.io/portfolio/telegram-capture-bot", font=MONO(26), fill=WHITE, anchor="lm")
    type_text(d, (60, 575), "Built by Dhruvin P.  ·  automation + medicine", prog(t, 2.8, 1.0), HAND(30), fill=INK)
    return im


SCENES = [(s_title, 4.6), (s_capture, 12.4), (s_relay, 6.6), (s_sync, 8.0), (s_triage, 11.4), (s_rules, 5.4), (s_end, 5.2)]
WIPE = 0.32


def render(path=OUT, fps=FPS):
    vw = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"avc1"), fps, (W, H))
    total = 0
    for si, (fn, dur) in enumerate(SCENES):
        nfr = int(dur * fps)
        for k in range(nfr):
            t = k / fps
            im = fn(t)
            d = ImageDraw.Draw(im)
            if si < len(SCENES) - 1 and t > dur - WIPE:            # red wipe in
                p = ease_io((t - (dur - WIPE)) / WIPE)
                d.rectangle((0, 0, W * p, H), fill=RED)
            if si > 0 and t < WIPE:                                  # red wipe out
                p = ease_io(t / WIPE)
                d.rectangle((W * p, 0, W, H), fill=RED)
            vw.write(cv2.cvtColor(np.array(im.convert("RGB")), cv2.COLOR_RGB2BGR))
            total += 1
    vw.release()
    return total / fps


if __name__ == "__main__":
    secs = render()
    # stills for the website and the Upwork cover
    s_capture(11.0).convert("RGB").save(HERE / "still-capture.png")
    s_triage(10.5).convert("RGB").save(HERE / "still-triage.png")
    s_title(4.5).convert("RGB").save(HERE / "still-title.png")
    print(f"{OUT.name}: {secs:.1f} s")
