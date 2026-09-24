"""Web assets from the REAL screen recording (cropped to the bot chat, nothing else changed):
  telegram-real.mp4   ~9 s muted loop for the page hero: typing at 2.5x, then the send and the bot reply at real speed
  assets/telegram-final.png   last frame: the sent note and the bot's confirmation
Usage: REC="<path to recording>" python make_web_assets.py
"""
import os
import pathlib

import cv2
import numpy as np

HERE = pathlib.Path(__file__).parent
REC = os.environ["REC"]
SEND_F = 412          # bubble appears (frame index at 30 fps)
TYPE_SPEED = 2.5
SCALE = 1.5

frames = []
cap = cv2.VideoCapture(REC)
while True:
    ok, f = cap.read()
    if not ok:
        break
    comp = np.vstack([f[0:48, 0:640], np.full((3, 640, 3), 40, np.uint8), f[770:996, 0:640]])
    frames.append(comp)
h, w = frames[0].shape[:2]
size = (int(w * SCALE) // 2 * 2, int(h * SCALE) // 2 * 2)

order = [int(i * TYPE_SPEED) for i in range(int(SEND_F / TYPE_SPEED))] + list(range(SEND_F, len(frames)))
order += [len(frames) - 1] * 45     # hold the confirmation for 1.5 s before the loop restarts
vw = cv2.VideoWriter(str(HERE / "telegram-real.mp4"), cv2.VideoWriter_fourcc(*"avc1"), 30, size)
for i in order:
    vw.write(cv2.resize(frames[i], size, interpolation=cv2.INTER_AREA))
vw.release()
(HERE / "assets").mkdir(exist_ok=True)
cv2.imwrite(str(HERE / "assets" / "telegram-final.png"), cv2.resize(frames[-1], size, interpolation=cv2.INTER_AREA))
print("telegram-real.mp4", size, round(len(order) / 30, 1), "s")
