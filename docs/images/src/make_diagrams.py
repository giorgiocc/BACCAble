#!/usr/bin/env python3
"""Draws the plan's wiring diagrams as SVG (docs/images/src/*.svg).

Run:  python3 docs/images/src/make_diagrams.py && node docs/images/src/render.js
render.js turns every SVG into the PNG that the plan embeds (docs/images/*.png).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

C = {
    "can_h": "#d97706", "can_l": "#15803d", "gnd": "#111827", "v12": "#dc2626",
    "v33": "#e11d48", "serial": "#2563eb", "reset": "#ea580c", "standby": "#7c3aed",
    "boot": "#0f766e", "board": "#f1f5f9", "edge": "#334155", "muted": "#64748b",
    "remove": "#dc2626", "pcb": "#1f2937",
}
FONT = "DejaVu Sans, Arial, sans-serif"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []

    def add(self, s):
        self.items.append(s)

    def line(self, pts, color, width=3, dash=None):
        d = " ".join(f"{x},{y}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{da}/>')

    def rect(self, x, y, w, h, fill="#fff", stroke=None, sw=2, rx=6, dash=None):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{da}/>')

    def circle(self, x, y, r, fill, stroke=None, sw=2):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{st}/>')

    def text(self, x, y, s, size=15, color="#111827", anchor="start", weight="normal", italic=False):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color}" '
                 f'text-anchor="{anchor}" font-weight="{weight}"{st}>{s}</text>')

    def dot(self, x, y, color):
        self.circle(x, y, 5, color)

    def cross(self, x, y, r=11, color=None):
        color = color or C["remove"]
        self.line([(x - r, y - r), (x + r, y + r)], color, 4)
        self.line([(x - r, y + r), (x + r, y - r)], color, 4)

    def save(self, name):
        body = "\n".join(self.items)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}">\n<rect width="100%" height="100%" fill="#ffffff"/>\n'
               f'{body}\n</svg>\n')
        with open(os.path.join(HERE, name), "w") as f:
            f.write(svg)


# ---------------------------------------------------------------- full wiring
def wiring_full():
    s = Svg(2000, 1190)
    s.text(30, 42, "DIY BACCAble — complete wiring, three FYSETC UCAN boards (C1 + C2 + BH)", 26, weight="bold")
    s.text(30, 70, "Logical drawing (not to scale). Pads are named by their silkscreen label; check each one with the meter (plan §2.2).",
           15, C["muted"])

    # OBD plug column
    pin_y = {n: 120 + (n - 1) * 52 for n in range(1, 17)}
    s.rect(30, 92, 270, 16 * 52 + 8, fill="#f8fafc", stroke=C["edge"])
    s.text(165, 1052 - 120 + 140, "", 1)
    names = {1: "CMD_1", 2: "CMD_3", 3: "BH CAN_H", 4: "GND (chassis)", 5: "GND (signal)", 6: "C1 CAN_H",
             7: "STS_3", 8: "LED strip", 9: "STS_1", 10: "STS_2", 11: "BH CAN_L", 12: "C2 CAN_H",
             13: "C2 CAN_L", 14: "C1 CAN_L", 15: "CMD_2", 16: "+12 V always on"}
    used = {3, 4, 5, 6, 11, 12, 13, 14, 16}
    for n, y in pin_y.items():
        u = n in used
        s.circle(272, y, 9, "#fff" if not u else "#111827", C["edge"], 2)
        s.text(48, y + 6, f"{n:>2}", 17, "#111827" if u else C["muted"], weight="bold" if u else "normal")
        s.text(84, y + 6, names[n] + ("" if u else "  — empty"), 15, "#111827" if u else C["muted"])
    s.text(165, 1070, "OBD male plug", 18, anchor="middle", weight="bold")
    s.text(165, 1092, "into the SGW bypass port", 14, C["muted"], anchor="middle")

    # boards
    bx, bw, bh = 880, 600, 262
    boards = [("C1", 108, "master · 500 kbit/s · OBD 6/14"),
              ("C2", 418, "slave · 500 kbit/s · OBD 12/13"),
              ("BH", 728, "slave · 125 kbit/s · OBD 3/11")]
    term = {}
    for name, y0, sub in boards:
        s.rect(bx, y0, bw, bh, fill=C["board"], stroke=C["edge"], sw=2.5, rx=10)
        s.text(bx + 300, y0 + 30, f"{name}  —  FYSETC UCAN", 20, anchor="middle", weight="bold")
        s.text(bx + 300, y0 + 52, sub, 14, C["muted"], anchor="middle")
        # P1 terminal
        s.rect(bx - 8, y0 + 64, 92, 112, fill="#bbf7d0", stroke="#15803d", rx=4)
        for i, lab in enumerate(["CAN_L", "CAN_H", "GND"]):
            yy = y0 + 84 + i * 36
            s.circle(bx, yy, 6, "#fff", C["edge"])
            s.text(bx + 12, yy + 5, lab, 13)
        s.text(bx + 38, y0 + 190, "P1", 12, C["muted"], anchor="middle")
        # P3 power pads
        for i, lab in enumerate(["3V3", "G"]):
            yy = y0 + 214 + i * 28
            s.circle(bx, yy, 6, "#fff", C["edge"])
            s.text(bx + 12, yy + 5, f"P3 {lab}", 13)
        term[name] = {"L": y0 + 84, "H": y0 + 120, "GND": y0 + 156, "3V3": y0 + 214, "G": y0 + 242}
        # removed / open parts
        s.rect(bx + 110, y0 + 70, 150, 58, fill="#fff", stroke=C["remove"], rx=4, dash="5,4")
        s.text(bx + 185, y0 + 92, "R1 + R2 (2×59 Ω)", 13, C["remove"], anchor="middle", weight="bold")
        s.text(bx + 185, y0 + 114, "REMOVE", 13, C["remove"], anchor="middle", weight="bold")
        s.text(bx + 110, y0 + 148, "JP1: open (no jumper)", 13, C["muted"])
        s.text(bx + 110, y0 + 168, "R4: remove if fitted", 13, C["remove"])
        # transceiver + chip
        s.rect(bx + 280, y0 + 70, 110, 70, fill="#fff", stroke=C["edge"], rx=4)
        s.text(bx + 335, y0 + 96, "U1", 14, anchor="middle", weight="bold")
        s.text(bx + 335, y0 + 116, "SN65HVD230", 12, C["muted"], anchor="middle")
        s.rect(bx + 280, y0 + 158, 110, 70, fill="#fff", stroke=C["edge"], rx=4)
        s.text(bx + 335, y0 + 186, "U3", 14, anchor="middle", weight="bold")
        s.text(bx + 335, y0 + 206, "STM32F072CB", 12, C["muted"], anchor="middle")
        # LEDs
        for i, (lab, col) in enumerate([("LD1 RX", "#ef4444"), ("LD2 TX", "#3b82f6"), ("LD3 3V3", "#22c55e")]):
            xx = bx + 120 + i * 58
            s.circle(xx, y0 + 206, 8, col, C["edge"], 1.5)
            s.text(xx, y0 + 232, lab, 11, anchor="middle")
        s.text(bx + 178, y0 + 252, "LEDs: no wiring, keep visible", 11, C["muted"], anchor="middle")
        # P2 pads on the right edge
        for i, lab in enumerate(["CK", "DO", "RES", "G", "B0", "3V3"]):
            yy = y0 + 76 + i * 30
            s.circle(bx + bw - 60, yy, 6, "#fff", C["edge"])
            s.text(bx + bw - 76, yy + 5, lab, 13, anchor="end")
        s.text(bx + bw - 60, y0 + 64, "P2", 12, C["muted"], anchor="middle")
        # boot button between B0 and 3V3
        b0, v3 = y0 + 76 + 4 * 30, y0 + 76 + 5 * 30
        s.line([(bx + bw - 54, b0), (bx + bw - 20, b0), (bx + bw - 20, b0 + 8)], C["boot"], 2.5)
        s.line([(bx + bw - 54, v3), (bx + bw - 20, v3), (bx + bw - 20, v3 - 8)], C["boot"], 2.5)
        s.line([(bx + bw - 30, b0 + 9), (bx + bw - 10, v3 - 9)], C["boot"], 2.5)
        s.text(bx + bw + 4, b0 + 20, "BOOT", 11, C["boot"], weight="bold")
        # USB
        s.rect(bx + 420, y0 + 196, 74, 30, fill="#e2e8f0", stroke=C["edge"], rx=8)
        s.text(bx + 457, y0 + 216, "USB-C", 12, anchor="middle")
        s.text(bx + 457, y0 + 242, "free", 11, C["muted"], anchor="middle")

    # CAN wires: (obd pin, board, net, colour, lane x)
    can = [(6, "C1", "H", C["can_h"], 470), (14, "C1", "L", C["can_l"], 490),
           (12, "C2", "H", C["can_h"], 540), (13, "C2", "L", C["can_l"], 560),
           (3, "BH", "H", C["can_h"], 610), (11, "BH", "L", C["can_l"], 630)]
    for pin, b, net, col, lx in can:
        ty = term[b][net]
        s.line([(281, pin_y[pin]), (lx, pin_y[pin]), (lx, ty), (bx - 6, ty)], col, 3.5)
    tags = {"C1": "W1 / W2", "C2": "W3 / W4", "BH": "W5 / W6"}
    for b, t in tags.items():
        s.text(bx - 34, term[b]["L"] - 10, t, 12, C["muted"], anchor="middle")

    # ground star and ground lane
    gx = 700
    star = (360, (pin_y[4] + pin_y[5]) // 2)
    s.line([(281, pin_y[4]), (330, pin_y[4]), (330, pin_y[5]), (281, pin_y[5])], C["gnd"], 3.5)
    s.line([(330, star[1]), (gx, star[1])], C["gnd"], 3.5)
    s.dot(330, star[1], C["gnd"])
    s.circle(star[0], star[1], 10, "#fff", C["gnd"], 3)
    s.text(372, star[1] - 16, "star W7", 13, weight="bold")
    for b in ("C1", "C2", "BH"):
        ty = term[b]["GND"]
        s.line([(gx, ty), (bx - 6, ty)], C["gnd"], 3)
        s.dot(gx, ty, C["gnd"])
    s.text(bx - 34, term["C1"]["GND"] + 20, "W8–W10", 12, C["muted"], anchor="middle")

    # fuse + buck at the bottom
    fy = 1010
    s.line([(281, pin_y[16]), (330, pin_y[16]), (330, fy), (372, fy)], C["v12"], 3.5)
    s.rect(372, fy - 14, 70, 28, fill="#fee2e2", stroke=C["v12"], rx=6)
    s.text(407, fy + 5, "1 A", 14, C["v12"], anchor="middle", weight="bold")
    s.text(407, fy - 22, "fuse (W11)", 12, C["v12"], anchor="middle")
    s.line([(442, fy), (500, fy)], C["v12"], 3.5)
    s.rect(500, 960, 170, 130, fill="#fff7ed", stroke=C["edge"], rx=8)
    s.text(585, 990, "12 → 3.3 V buck", 15, anchor="middle", weight="bold")
    s.text(585, 1010, "set 3.30 V before", 12, C["muted"], anchor="middle")
    s.text(585, 1026, "connecting boards", 12, C["muted"], anchor="middle")
    s.text(508, fy + 5 - 22, "", 1)
    s.text(506, 1055, "IN+", 12)
    s.text(506, 1080, "IN−", 12)
    s.text(664, 1055, "OUT+", 12, anchor="end")
    s.text(664, 1080, "OUT−", 12, anchor="end")
    s.line([(500, fy), (490, fy), (490, 1050), (500, 1050)], C["v12"], 3)
    # IN- to ground lane
    s.line([(500, 1076), (480, 1076), (480, 1120), (gx, 1120), (gx, star[1])], C["gnd"], 3)
    s.dot(gx, star[1], C["gnd"])
    s.text(590, 1140, "W12: buck IN− to the ground star", 12, C["muted"], anchor="middle")
    # outputs
    v3x, gox = 760, 800
    s.line([(670, 1050), (v3x, 1050), (v3x, term["C1"]["3V3"])], C["v33"], 3.5)
    s.line([(670, 1076), (gox, 1076), (gox, term["C1"]["G"])], C["gnd"], 3.5, dash="9,5")
    for b in ("C1", "C2", "BH"):
        y3, yg = term[b]["3V3"], term[b]["G"]
        s.line([(v3x, y3), (bx - 6, y3)], C["v33"], 3)
        s.line([(gox, yg), (bx - 6, yg)], C["gnd"], 3, dash="9,5")
        s.dot(v3x, y3, C["v33"])
        s.dot(gox, yg, C["gnd"])
        s.rect(836, y3 - 12, 26, yg - y3 + 24, fill="#fff", stroke=C["edge"], rx=4)
    s.text(830, 1165, "W13 3.3 V / W14 G — one polarised 2-pin plug per board", 12, C["muted"])

    # inter-board signal lanes on the right
    lanes = {"serial": 1560, "reset": 1610, "standby": 1660}
    pad_x = bx + bw - 54
    def p2(b, lab):
        y0 = dict((n, y) for n, y, _ in boards)[b]
        return y0 + 76 + ["CK", "DO", "RES", "G", "B0", "3V3"].index(lab) * 30
    # serial: CK of all three
    ys = [p2(b, "CK") for b in ("C1", "C2", "BH")]
    for y in ys:
        s.line([(pad_x, y), (lanes["serial"], y)], C["serial"], 3)
        s.dot(lanes["serial"], y, C["serial"])
    s.line([(lanes["serial"], ys[0]), (lanes["serial"], ys[-1])], C["serial"], 3.5)
    # reset: C1 DO -> C2 RES, BH RES
    yd = p2("C1", "DO")
    yr = [p2("C2", "RES"), p2("BH", "RES")]
    s.line([(pad_x, yd), (lanes["reset"], yd), (lanes["reset"], yr[-1])], C["reset"], 3.5)
    for y in yr:
        s.line([(pad_x, y), (lanes["reset"], y)], C["reset"], 3)
        s.dot(lanes["reset"], y, C["reset"])
    # standby: C1 chip pin 15 -> slaves U1 pin 8, along the bottom edge of each board
    y0s = dict((n, y) for n, y, _ in boards)
    def standby_tap(b, y, label):
        yb = y0s[b] + 256
        s.circle(bx + 390, y, 6, "#fff", C["standby"], 2.5)
        s.text(bx + 398, y - 10, label, 12, C["standby"])
        s.line([(bx + 396, y), (bx + 405, y), (bx + 405, yb), (lanes["standby"], yb)], C["standby"], 3)
        return yb
    yb1 = standby_tap("C1", y0s["C1"] + 193, "chip pin 15 (PA5)")
    yb2 = standby_tap("C2", y0s["C2"] + 100, "U1 pin 8 (RS)")
    yb3 = standby_tap("BH", y0s["BH"] + 100, "U1 pin 8 (RS)")
    s.line([(lanes["standby"], yb1), (lanes["standby"], yb3)], C["standby"], 3.5)
    s.dot(lanes["standby"], yb2, C["standby"])
    s.dot(lanes["standby"], yb3, C["standby"])
    s.text(lanes["serial"], 100, "W15", 13, C["serial"], anchor="middle", weight="bold")
    s.text(lanes["reset"], 100, "W16", 13, C["reset"], anchor="middle", weight="bold")
    s.text(lanes["standby"], 100, "W17", 13, C["standby"], anchor="middle", weight="bold")

    # legend
    lx, ly = 1715, 150
    s.rect(lx - 15, ly - 30, 290, 186, fill="#fff", stroke="#cbd5e1", rx=8)
    s.text(lx, ly - 8, "Legend", 15, weight="bold")
    items = [("CAN_H (twisted with CAN_L)", C["can_h"], None), ("CAN_L", C["can_l"], None),
             ("ground", C["gnd"], None), ("+12 V (fused)", C["v12"], None), ("+3.3 V rail", C["v33"], None),
             ("serial PA14 (CK)", C["serial"], None), ("reset: C1 DO → RES", C["reset"], None),
             ("standby: C1 PA5 → U1 pin 8", C["standby"], None)]
    for i, (lab, col, _) in enumerate(items):
        y = ly + 14 + i * 18
        s.line([(lx, y - 4), (lx + 34, y - 4)], col, 4)
        s.text(lx + 44, y + 1, lab, 12)
    s.save("wiring_full_3ucan.svg")


# ---------------------------------------------------------------- board prep
def board_prep():
    # coordinates follow the FYSETC component-position drawing (top side, USB on the left)
    s = Svg(1500, 730)
    s.text(30, 40, "UCAN V1.0 — what to change on C1, C2 and BH (top side, USB on the left)", 24, weight="bold")
    s.text(30, 66, "Simplified redraw after FYSETC's component-position drawing. Pad labels are printed on the bottom side; confirm every pad with the meter.",
           14, C["muted"])
    ox, oy, k = 30, 110, 0.72
    def P(x, y):
        return ox + (x - 25) * k, oy + (y - 425) * k
    x0, y0 = P(25, 425)
    x1, y1 = P(1980, 990)
    s.rect(x0, y0, x1 - x0, y1 - y0, fill=C["pcb"], stroke="#0f172a", sw=3, rx=10)
    # USB
    ux, uy = P(25, 545)
    s.rect(ux - 14, uy, 150 * k + 14, 330 * k, fill="#cbd5e1", stroke="#475569", rx=10)
    s.text(ux + 50, uy + 130 * k, "USB-C", 15, "#0f172a", anchor="middle", weight="bold")
    # U3
    cx, cy = P(505, 580)
    s.rect(cx, cy, 225 * k, 225 * k, fill="#111827", stroke="#94a3b8", sw=2, rx=3)
    s.text(cx + 112 * k, cy + 105 * k, "U3", 16, "#e2e8f0", anchor="middle", weight="bold")
    s.text(cx + 112 * k, cy + 130 * k, "STM32F072CB", 11, "#cbd5e1", anchor="middle")
    # LQFP48 pins: 12 per side, pin 1 next to the dot in the bottom-right corner (FYSETC render)
    side = 225 * k
    step = side / 13
    for i in range(12):
        t = (i + 1) * step
        col_top = "#a78bfa" if i == 2 else "#9ca3af"          # top side right->left = pins 13..24
        s.rect(cx + side - t - 1.5, cy - 9, 3, 9, fill=col_top, rx=1)
        s.rect(cx + t - 1.5, cy + side, 3, 9, fill="#60a5fa" if i == 0 else "#9ca3af", rx=1)
        s.rect(cx - 9, cy + t - 1.5, 9, 3, fill="#fb923c" if i == 9 else "#9ca3af", rx=1)
        s.rect(cx + side, cy + side - t - 1.5, 9, 3, fill="#fde047" if i == 0 else "#9ca3af", rx=1)
    s.circle(cx + side - 14, cy + side - 14, 5, "#e5e7eb")
    s.text(cx + side + 14, cy + side - 8, "1", 12, "#fde047", weight="bold")
    p15x = cx + side - 3 * step
    s.text(p15x, cy - 16, "15 = PA5 (C1 standby wire)", 12, "#c4b5fd", anchor="middle", weight="bold")
    s.text(cx - 14, cy + 10 * step + 4, "34 = DO", 11, "#fdba74", anchor="end", weight="bold")
    s.text(cx + step, cy + side + 24, "37 = CK", 11, "#93c5fd", anchor="middle", weight="bold")
    s.text(cx + 112 * k, cy + 150 * k, "dot = pin 1", 10, "#cbd5e1", anchor="middle")
    # P2 (top row) and P3 (bottom row)
    for i, lab in enumerate(["CK", "DO", "RES", "G", "B0", "3V3"]):
        x, y = P(803 + i * 90, 482)
        s.circle(x, y, 13, "#d4d4d8", "#a1a1aa", 2)
        s.circle(x, y, 5, "#52525b")
        s.text(x, y - 20, lab, 14, "#f8fafc", anchor="middle", weight="bold")
    s.text(P(803, 482)[0] - 30, P(803, 482)[1] + 5, "P2", 13, "#e2e8f0", anchor="end")
    for i, lab in enumerate(["RX", "TX", "G", "3V3"]):
        x, y = P(713 + i * 90, 932)
        s.circle(x, y, 13, "#d4d4d8", "#a1a1aa", 2)
        s.circle(x, y, 5, "#52525b")
        s.text(x, y + 30, lab, 14, "#f8fafc", anchor="middle", weight="bold")
    s.text(P(713, 932)[0] - 30, P(713, 932)[1] + 5, "P3", 13, "#e2e8f0", anchor="end")
    # LEDs
    for (x, y, lab, col) in [(935, 562, "LD1 RX", "#ef4444"), (1037, 562, "LD2 TX", "#3b82f6"), (1340, 925, "LD3 3V3", "#22c55e")]:
        px, py = P(x, y)
        s.rect(px - 14, py - 8, 28, 16, fill=col, stroke="#e5e7eb", sw=1.5, rx=3)
        s.text(px, py + (28 if y > 900 else -14), lab, 12, "#f8fafc", anchor="middle")
    # U1 with pins
    ux1, uy1 = P(1180, 620)
    s.rect(ux1, uy1, 65 * k, 180 * k, fill="#111827", stroke="#94a3b8", sw=2, rx=3)
    s.text(ux1 + 32 * k, uy1 + 95 * k, "U1", 13, "#e2e8f0", anchor="middle", weight="bold")
    for i in range(4):
        lx, ly = P(1128, 642 + i * 45)
        rx_, ry = P(1298, 642 + i * 45)
        s.rect(lx - 22, ly - 6, 34, 12, fill="#9ca3af", rx=2)
        s.rect(rx_ - 12, ry - 6, 34, 12, fill="#a78bfa" if i == 0 else "#9ca3af", rx=2)
        s.text(lx - 28, ly + 5, str(i + 1), 11, "#e2e8f0", anchor="end")
        s.text(rx_ + 28, ry + 5, str(8 - i), 11, "#e2e8f0")
    p8x, p8y = P(1298, 642)
    s.text(p8x + 104, p8y - 56, "U1 pin 8 (RS)", 13, "#c4b5fd", weight="bold")
    s.text(p8x + 104, p8y - 40, "C2/BH: standby wire in", 12, "#c4b5fd")
    s.line([(p8x + 14, p8y - 4), (p8x + 98, p8y - 52)], "#c4b5fd", 2)
    # R4 / R18
    for x, lab, rem in [(1258, "R4", True), (1325, "R18", False)]:
        px, py = P(x, 597)
        s.rect(px - 12, py - 6, 24, 12, fill="#e5e7eb", rx=2)
        s.text(px, py - 12, lab, 12, "#f8fafc", anchor="middle")
        if rem:
            s.cross(px, py, 9, "#f87171")
    # R1, R2, C4
    for y, lab in [(667, "R1"), (752, "R2")]:
        px, py = P(1395, y)
        s.rect(px - 22, py - 13, 44, 26, fill="#e5e7eb", stroke="#f87171", sw=2, rx=3)
        s.text(px + 40, py + 5, lab, 13, "#f8fafc")
        s.cross(px, py, 13, "#ef4444")
    c4x, c4y = P(1455, 711)
    s.rect(c4x - 8, c4y - 5, 16, 10, fill="#d6d3d1", rx=2)
    # TVS
    tx, ty = P(1555, 711)
    s.rect(tx - 20, ty - 26, 40, 52, fill="#374151", stroke="#9ca3af", rx=3)
    s.text(tx, ty + 44, "TVS1", 11, "#e2e8f0", anchor="middle")
    # JP1 + R3
    jx, jy = P(1868, 472)
    s.circle(jx - 30 * k, jy, 11, "#d4d4d8", "#a1a1aa", 2)
    s.circle(jx + 30 * k, jy, 11, "#d4d4d8", "#a1a1aa", 2)
    s.text(jx, jy + 32, "JP1 open", 12, "#fde68a", anchor="middle", weight="bold")
    rx3, ry3 = P(1715, 490)
    s.rect(rx3 - 22, ry3 - 12, 44, 24, fill="#e5e7eb", rx=3)
    s.text(rx3 - 30, ry3 + 5, "R3", 11, "#e2e8f0", anchor="end")
    # P1
    px1, py1 = P(1652, 530)
    s.rect(px1, py1, (1980 - 1652) * k, (935 - 530) * k, fill="#22c55e", stroke="#14532d", sw=2, rx=4)
    for y, lab in [(607, "GND"), (732, "CAN_H"), (857, "CAN_L")]:
        x, yy = P(1700, y)
        s.circle(x, yy, 14, "#14532d")
        s.text(x + 26, yy + 5, lab, 14, "#052e16", weight="bold")
    s.text(px1 + 300 * k, py1 + 395 * k, "P1", 14, "#052e16", anchor="middle", weight="bold")

    # callouts (below the board)
    by = y1 + 40
    notes = [
        ("1", "R1 + R2 (59 Ω each, ≈118 Ω terminator, on by default): REMOVE on C1, C2, BH when H0 reads ≈118 Ω", C["remove"]),
        ("2", "R4 (10 kΩ pull-up on U1 pin 8): REMOVE if fitted; keep R18 (10 kΩ to GND)", C["remove"]),
        ("3", "JP1: leave open (no jumper) — R3 stays, it only acts when the jumper is fitted", "#b45309"),
        ("4", "Wire P2: CK on all; DO on C1 only; RES on C2/BH; button B0 ↔ 3V3 on all", C["serial"]),
        ("5", "Power plug on P3: 3V3 and G (adjacent pads at the end away from USB)", C["v33"]),
        ("6", "P1 order: read the print on your terminal (bottom side: CAN_L · CAN_H · GND)", "#15803d"),
    ]
    for i, (n, t, col) in enumerate(notes):
        y = by + i * 26
        s.circle(46, y - 5, 10, col)
        s.text(46, y, n, 12, "#fff", anchor="middle", weight="bold")
        s.text(66, y, t, 15)
    s.save("ucan_board_prep.svg")


# ---------------------------------------------------------------- OBD plug
def obd_plug():
    s = Svg(1100, 560)
    s.text(30, 40, "OBD male plug — the pins we populate", 24, weight="bold")
    s.text(30, 66, "Seen from the wire (solder) side = same layout as looking into the car's socket. Pins 1–8 on the long side. Trust the numbers moulded on your plug.",
           14, C["muted"])
    # trapezoid
    s.add('<path d="M 120 110 L 980 110 L 930 330 L 170 330 Z" fill="#f8fafc" stroke="#334155" stroke-width="3"/>')
    nets = {3: ("BH H", C["can_h"]), 4: ("GND", C["gnd"]), 5: ("GND", C["gnd"]), 6: ("C1 H", C["can_h"]),
            11: ("BH L", C["can_l"]), 12: ("C2 H", C["can_h"]), 13: ("C2 L", C["can_l"]),
            14: ("C1 L", C["can_l"]), 16: ("+12 V", C["v12"])}
    for n in range(1, 17):
        row = 0 if n <= 8 else 1
        i = (n - 1) % 8
        x = 220 + i * 94
        y = 170 if row == 0 else 270
        if n in nets:
            lab, col = nets[n]
            s.circle(x, y, 22, col, "#0f172a", 2)
            s.text(x, y + 6, str(n), 16, "#fff", anchor="middle", weight="bold")
            s.text(x, y + (-32 if row == 0 else 46), lab, 14, col, anchor="middle", weight="bold")
        else:
            s.circle(x, y, 22, "#fff", "#94a3b8", 2)
            s.text(x, y + 6, str(n), 15, "#94a3b8", anchor="middle")
    rows = [
        ("C1 bus 500 kbit/s", "6 = CAN_H, 14 = CAN_L", "→ C1 terminal (W1/W2)"),
        ("C2 bus 500 kbit/s", "12 = CAN_H, 13 = CAN_L", "→ C2 terminal (W3/W4)"),
        ("BH bus 125 kbit/s", "3 = CAN_H, 11 = CAN_L", "→ BH terminal (W5/W6)"),
        ("Ground", "4 + 5 joined", "→ ground star (W7)"),
        ("Power", "16 = +12 V always on", "→ 1 A fuse → 3.3 V buck (W11)"),
        ("Empty", "1, 2, 7, 8, 9, 10, 15", "author's extra I/O and LED strip — not used"),
    ]
    for i, (a, b, c) in enumerate(rows):
        y = 390 + i * 26
        s.text(60, y, a, 15, weight="bold")
        s.text(260, y, b, 15)
        s.text(520, y, c, 15, C["muted"])
    s.save("obd_plug_pins.svg")


# ---------------------------------------------------------------- power chain
def power_chain():
    s = Svg(1200, 430)
    s.text(30, 40, "Power — Option B, the author's topology (always-on 12 V → one 3.3 V rail)", 22, weight="bold")
    y = 150
    s.rect(30, y - 40, 150, 80, fill="#f8fafc", stroke=C["edge"])
    s.text(105, y - 8, "OBD pin 16", 15, anchor="middle", weight="bold")
    s.text(105, y + 14, "+12 V always on", 13, C["muted"], anchor="middle")
    s.line([(180, y), (260, y)], C["v12"], 4)
    s.rect(260, y - 22, 90, 44, fill="#fee2e2", stroke=C["v12"], rx=8)
    s.text(305, y + 6, "1 A fuse", 14, C["v12"], anchor="middle", weight="bold")
    s.line([(350, y), (430, y)], C["v12"], 4)
    s.rect(430, y - 60, 220, 150, fill="#fff7ed", stroke=C["edge"], rx=10)
    s.text(540, y - 26, "12 → 3.3 V buck", 17, anchor="middle", weight="bold")
    s.text(540, y, "input ≥ 30 V rated", 13, C["muted"], anchor="middle")
    s.text(540, y + 20, "output ≥ 0.5 A, low idle current", 13, C["muted"], anchor="middle")
    s.text(540, y + 44, "set 3.30 V with no board", 13, C["v12"], anchor="middle", weight="bold")
    s.text(540, y + 62, "(3.2–3.4 V, never > 3.6 V)", 12, C["muted"], anchor="middle")
    for i, b in enumerate(["C1", "C2", "BH"]):
        yy = 90 + i * 90
        s.line([(650, y - 20), (720, y - 20), (720, yy), (840, yy)], C["v33"], 3.5)
        s.line([(650, y + 30), (700, y + 30), (700, yy + 26), (840, yy + 26)], C["gnd"], 3, dash="9,5")
        s.rect(840, yy - 14, 30, 54, fill="#fff", stroke=C["edge"], rx=4)
        s.text(855, yy + 54, "plug", 11, C["muted"], anchor="middle")
        s.line([(870, yy), (930, yy)], C["v33"], 3.5)
        s.line([(870, yy + 26), (930, yy + 26)], C["gnd"], 3, dash="9,5")
        s.rect(930, yy - 22, 220, 62, fill=C["board"], stroke=C["edge"], rx=8)
        s.text(945, yy + 5, f"{b}: P3 3V3", 14)
        s.text(945, yy + 31, f"{b}: P3 G", 14)
    s.rect(30, 270, 150, 70, fill="#f8fafc", stroke=C["edge"])
    s.text(105, 300, "OBD pins 4 + 5", 15, anchor="middle", weight="bold")
    s.text(105, 322, "ground", 13, C["muted"], anchor="middle")
    s.line([(180, 305), (330, 305)], C["gnd"], 4)
    s.circle(340, 305, 10, "#fff", C["gnd"], 3)
    s.text(326, 345, "ground star", 13, anchor="end", weight="bold")
    s.line([(350, 305), (500, 305), (500, y + 90)], C["gnd"], 3.5)
    s.text(510, 290, "buck IN− / OUT−", 12, C["muted"])
    s.line([(340, 315), (340, 380), (930, 380)], C["gnd"], 3)
    s.text(935, 385, "and each board's P1 GND (CAN cable)", 13)
    s.text(30, 418, "Rule: never plug USB into a board while its 3.3 V plug is connected — unplug the plug first (no diode on a UCAN).",
           14, C["v12"], weight="bold")
    s.save("power_chain.svg")


# ---------------------------------------------------------------- box layout
def box_layout():
    s = Svg(1200, 640)
    s.text(30, 40, "Box — suggested layout (three UCANs side by side, like the author's three USB-C ports)", 22, weight="bold")
    # front panel
    s.text(30, 84, "Front panel", 16, weight="bold")
    s.rect(30, 96, 700, 170, fill="#f1f5f9", stroke=C["edge"], sw=3, rx=12)
    for i, b in enumerate(["BH", "C2", "C1"]):
        cx = 150 + i * 230
        s.rect(cx - 45, 140, 90, 34, fill="#cbd5e1", stroke="#475569", rx=14)
        s.text(cx, 162, "USB-C", 12, anchor="middle")
        s.circle(cx, 215, 16, "#0f766e", "#134e4a", 2)
        s.text(cx + 26, 220, "BOOT", 12, C["boot"], weight="bold")
        s.text(cx, 128, b, 18, anchor="middle", weight="bold")
    s.text(30, 290, "Order BH · C2 · C1 from the left, as on the author's device (manual §1.11). Each button only works at power-up.",
           13, C["muted"])
    # lid
    s.text(780, 84, "Lid (top view)", 16, weight="bold")
    s.rect(780, 96, 390, 250, fill="#f8fafc", stroke=C["edge"], sw=3, rx=12)
    for i, b in enumerate(["BH", "C2", "C1"]):
        y = 140 + i * 66
        s.text(800, y + 6, b, 16, weight="bold")
        for j, (lab, col) in enumerate([("RX", "#ef4444"), ("TX", "#3b82f6"), ("3V3", "#22c55e")]):
            x = 880 + j * 90
            s.circle(x, y, 13, col, C["edge"], 2)
            s.text(x + 20, y + 5, lab, 12)
    s.text(780, 370, "Nine 3 mm windows or light pipes over LD1 / LD2 / LD3,", 13, C["muted"])
    s.text(780, 388, "or a clear lid. The LEDs are dim by design.", 13, C["muted"])
    # inside
    s.text(30, 340, "Inside", 16, weight="bold")
    s.rect(30, 352, 700, 250, fill="#ffffff", stroke=C["edge"], sw=3, rx=12)
    for i, b in enumerate(["BH", "C2", "C1"]):
        x = 60 + i * 150
        s.rect(x, 372, 120, 150, fill=C["board"], stroke=C["edge"], rx=6)
        s.text(x + 60, 400, b, 16, anchor="middle", weight="bold")
        s.text(x + 60, 420, "UCAN", 12, C["muted"], anchor="middle")
        s.rect(x + 30, 372 - 10, 60, 14, fill="#cbd5e1", stroke="#475569", rx=5)
        s.rect(x + 25, 500, 70, 22, fill="#bbf7d0", stroke="#15803d", rx=3)
        s.text(x + 60, 516, "P1", 11, anchor="middle")
    s.rect(520, 380, 180, 70, fill="#fff7ed", stroke=C["edge"], rx=8)
    s.text(610, 410, "3.3 V buck", 14, anchor="middle", weight="bold")
    s.text(610, 430, "+ 1 A fuse", 12, C["muted"], anchor="middle")
    s.rect(520, 470, 180, 40, fill="#f8fafc", stroke=C["edge"], rx=8)
    s.text(610, 495, "ground star", 13, anchor="middle")
    s.circle(380, 585, 14, "#e2e8f0", C["edge"], 2)
    s.text(400, 590, "one cable gland → OBD plug (≤ 30 cm)", 13)
    s.text(780, 440, "Mount away from pedals, steering column,", 13, C["muted"])
    s.text(780, 458, "knee-airbag path, heat and HVAC flaps.", 13, C["muted"])
    s.text(780, 476, "Standoffs; nothing can touch the PCB bottoms.", 13, C["muted"])
    s.save("box_layout.svg")


# ---------------------------------------------------------------- sleep lines
def sleep_lines():
    s = Svg(1200, 520)
    s.text(30, 40, "Sleep (low consume) — what C1 does on the two lines (lowConsume.c)", 22, weight="bold")
    x0, x1 = 300, 1160
    marks = [(300, "car awake"), (520, "last CAN frame"), (690, "+3.5 s: sleep"), (930, "frames again: wake"), (1100, "")]
    for x, lab in marks[:-1]:
        s.line([(x, 70), (x, 470)], "#e2e8f0", 2, dash="4,4")
        s.text(x + 4, 86, lab, 12, C["muted"])
    rows = [
        ("CAN frames on the C1 bus", "#111827", [(300, 1), (520, 1), (520, 0), (930, 0), (930, 1), (1160, 1)], "activity", "quiet"),
        ("C1 DO → C2/BH RES (reset)", C["reset"], [(300, 1), (690, 1), (690, 0), (930, 0), (930, 1), (1160, 1)], "high = slaves run", "low = held in reset"),
        ("C1 PA5 → U1 pin 8 (standby)", C["standby"], [(300, 0), (690, 0), (690, 1), (930, 1), (930, 0), (1160, 0)], "high = standby", "low = transceiver active"),
        ("C2 / BH chips", C["serial"], [(300, 1), (690, 1), (690, 0), (930, 0), (930, 1), (1160, 1)], "running", "in reset"),
    ]
    for i, (lab, col, pts, hi, lo) in enumerate(rows):
        base = 150 + i * 90
        s.text(30, base - 6, lab, 15, weight="bold")
        s.text(30, base + 14, f"top: {hi}", 12, C["muted"])
        s.text(30, base + 30, f"bottom: {lo}", 12, C["muted"])
        s.line([(x, base - 20 if v else base + 20) for x, v in pts], col, 4)
    s.text(30, 505, "After the wake C1 restarts the serial line and ≈ 3.5 s later sends every setting to C2/BH again. "
           "Sleep is blocked while a USB sniffer / ELM327 / pen-drive session is open.", 13, C["muted"])
    s.save("sleep_lines.svg")


if __name__ == "__main__":
    wiring_full()
    board_prep()
    obd_plug()
    power_chain()
    box_layout()
    sleep_lines()
    print("svg written to", HERE)
