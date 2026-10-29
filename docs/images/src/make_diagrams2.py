#!/usr/bin/env python3
"""Explanatory drawings for the plan (second set): overview, message flow, flashing, meter checks,
board-check decision tree, dashboard menu and LED meanings.

Run:  python3 docs/images/src/make_diagrams2.py && node docs/images/src/render.js
"""
from make_diagrams import Svg, C

MUTED = C["muted"]


def box(s, x, y, w, h, title, lines=(), fill="#f8fafc", stroke=None, tsize=16, lsize=13, tcol="#111827"):
    s.rect(x, y, w, h, fill=fill, stroke=stroke or C["edge"], rx=10)
    s.text(x + w / 2, y + 26, title, tsize, tcol, anchor="middle", weight="bold")
    for i, l in enumerate(lines):
        s.text(x + w / 2, y + 48 + i * 19, l, lsize, MUTED, anchor="middle")


def arrow(s, pts, color, width=3.5, label=None, lx=None, ly=None, lcol=None):
    s.line(pts, color, width)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - 13 * math.cos(a - 0.45), y2 - 13 * math.sin(a - 0.45))
    p2 = (x2 - 13 * math.cos(a + 0.45), y2 - 13 * math.sin(a + 0.45))
    s.add(f'<polygon points="{x2},{y2} {p1[0]},{p1[1]} {p2[0]},{p2[1]}" fill="{color}"/>')
    if label:
        s.text(lx, ly, label, 13, lcol or color, anchor="middle", weight="bold")


def num(s, x, y, n, col="#2563eb"):
    s.circle(x, y, 15, col)
    s.text(x, y + 5, str(n), 15, "#fff", anchor="middle", weight="bold")


# ---------------------------------------------------------------- 1. overview
def overview():
    s = Svg(1500, 800)
    s.text(30, 42, "The big picture — what the BACCAble is and why it has three boards", 26, weight="bold")
    s.text(30, 70, "The car has three separate CAN networks. One UCAN board sits on each; C1 is the boss and talks to the other two over one wire.",
           15, MUTED)
    nets = [("C1 network", "OBD 6 / 14 · 500 kbit/s", ["engine, gearbox,", "steering-wheel buttons"], C["can_h"]),
            ("C2 network", "OBD 12 / 13 · 500 kbit/s", ["ESC / TC, ABS, brakes,", "parking sensors"], "#0891b2"),
            ("BH network", "OBD 3 / 11 · 125 kbit/s", ["dashboard text, mirrors,", "DNA selector"], "#16a34a")]
    s.text(170, 112, "YOUR CAR", 18, anchor="middle", weight="bold")
    for i, (t, sub, lines, col) in enumerate(nets):
        y = 130 + i * 190
        s.rect(30, y, 280, 160, fill="#fff", stroke=col, sw=3, rx=12)
        s.text(170, y + 32, t, 19, col, anchor="middle", weight="bold")
        s.text(170, y + 56, sub, 13, MUTED, anchor="middle")
        for j, l in enumerate(lines):
            s.text(170, y + 92 + j * 22, l, 15, anchor="middle")
    # SGW bypass + OBD
    s.rect(380, 180, 170, 400, fill="#f1f5f9", stroke=C["edge"], rx=12)
    s.text(465, 215, "SGW bypass", 17, anchor="middle", weight="bold")
    s.text(465, 238, "cable", 15, anchor="middle")
    s.text(465, 270, "gives a free", 13, MUTED, anchor="middle")
    s.text(465, 288, "OBD port with", 13, MUTED, anchor="middle")
    s.text(465, 306, "all 3 networks", 13, MUTED, anchor="middle")
    s.text(465, 324, "+ 12 V + ground", 13, MUTED, anchor="middle")
    s.rect(410, 470, 110, 70, fill="#fff", stroke=C["edge"], rx=8)
    s.text(465, 500, "OBD port", 14, anchor="middle", weight="bold")
    s.text(465, 522, "(female)", 12, MUTED, anchor="middle")
    for i, (_, _, _, col) in enumerate(nets):
        y = 210 + i * 190
        s.line([(310, y), (345, y), (345, 380 + i * 30), (380, 380 + i * 30)], col, 5)
    # our box
    s.rect(620, 110, 840, 660, fill="#fbfdff", stroke=C["edge"], sw=3, rx=16)
    s.text(1040, 145, "OUR BOX = the DIY BACCAble", 20, anchor="middle", weight="bold")
    s.rect(560, 470, 80, 70, fill="#fff", stroke=C["edge"], rx=8)
    s.text(600, 500, "OBD", 14, anchor="middle", weight="bold")
    s.text(600, 520, "plug", 12, MUTED, anchor="middle")
    s.line([(520, 505), (560, 505)], C["edge"], 6)
    boards = [("C1", "the BOSS", ["reads buttons, shows the menu,", "decides, sends orders,", "puts C2 + BH to sleep"], nets[0][3], 180),
              ("C2", "helper", ["ESC/TC, DYNO, brake override,", "park mute, ABS faults"], nets[1][3], 370),
              ("BH", "helper", ["writes text on the cluster,", "odometer blink, mirrors"], nets[2][3], 560)]
    for name, role, lines, col, y in boards:
        s.rect(760, y, 380, 150, fill="#fff", stroke=col, sw=3, rx=12)
        s.text(790, y + 38, name, 30, col, weight="bold")
        s.text(850, y + 36, f"UCAN board — {role}", 16, weight="bold")
        for j, l in enumerate(lines):
            s.text(790, y + 72 + j * 22, l, 14)
        s.line([(640, 505), (700, 505), (700, y + 75), (760, y + 75)], col, 5)
    # serial + sleep
    sx, zx = 1165, 1400
    s.line([(sx, 230), (sx, 640)], C["serial"], 5)
    for y in (230, 445, 640):
        s.line([(1140, y), (sx, y)], C["serial"], 5)
        s.dot(sx, y, C["serial"])
    s.text(1180, 335, "serial wire", 15, C["serial"], weight="bold")
    s.text(1180, 355, "C1 ↔ C2 ↔ BH", 13, C["serial"])
    s.text(1180, 373, "(orders + answers)", 13, C["serial"])
    s.line([(1140, 290), (zx, 290), (zx, 680), (1140, 680)], C["reset"], 4, dash="10,6")
    s.line([(zx, 480), (1140, 480)], C["reset"], 4, dash="10,6")
    s.text(1180, 560, "2 sleep wires", 15, C["reset"], weight="bold")
    s.text(1180, 580, "C1 → C2 + BH", 13, C["reset"])
    s.text(1180, 598, "(car parked → sleep)", 13, C["reset"])
    # power
    s.rect(1290, 170, 150, 110, fill="#fff7ed", stroke=C["edge"], rx=10)
    s.text(1365, 200, "Power", 16, anchor="middle", weight="bold")
    s.text(1365, 222, "OBD 16 (12 V)", 12, MUTED, anchor="middle")
    s.text(1365, 240, "→ fuse → 3.3 V", 12, MUTED, anchor="middle")
    s.text(1365, 258, "→ all 3 boards", 12, MUTED, anchor="middle")
    s.text(660, 755, "Each board also has its own USB-C port: for loading firmware, the ELM327 diagnostic mode and the sniffer.", 14, MUTED)
    s.save("system_overview.svg")


# ---------------------------------------------------------------- 2. message flow
def message_flow():
    s = Svg(1500, 900)
    s.text(30, 42, "How the three boards work together — two real examples from the code", 26, weight="bold")
    lanes = [("C1 network", C["can_h"], 130), ("C1 board", C["can_h"], 200), ("serial wire", C["serial"], 270),
             ("C2 / BH board", "#16a34a", 340), ("C2 / BH network", "#16a34a", 410)]

    def lane_bg(y0):
        for name, col, y in lanes:
            yy = y + y0
            s.rect(30, yy - 24, 1440, 48, fill="#f8fafc", rx=6)
            s.text(44, yy + 5, name, 14, col, weight="bold")
    # example 1
    s.text(30, 92, "Example 1 — you open the BACCAble menu and read it on the cluster", 17, weight="bold")
    lane_bg(0)
    steps1 = [
        (300, 130, "you hold RES ≈ 2 s:", "steering wheel sends 0x2FA"),
        (540, 200, "C1 sees the button,", "builds the menu text"),
        (790, 270, "C1 sends the text to BH", "(serial message 0x03)"),
        (1040, 340, "BH receives it", ""),
        (1290, 410, "BH sends the text to the", "cluster as 0x090 frames"),
    ]
    prev = None
    for i, (x, y, a, b) in enumerate(steps1):
        num(s, x - 100, y, i + 1, C["can_h"] if y < 260 else (C["serial"] if y == 270 else "#16a34a"))
        s.text(x - 78, y - 3, a, 13, weight="bold")
        s.text(x - 78, y + 14, b, 12, MUTED)
        if prev:
            arrow(s, [(prev[0] - 100 + 15, prev[1] + 10), (x - 100 - 12, y - 10)], "#94a3b8", 2.5)
        prev = (x, y)
    # example 2
    y0 = 400
    s.text(30, 92 + y0 - 10, "Example 2 — you switch ESC/TC in the menu", 17, weight="bold")
    lane_bg(y0)
    steps2 = [
        (300, 130, "you select ESC/TC:", "button frame 0x2FA"),
        (540, 200, "C1 handles the menu", "choice"),
        (790, 270, "C1 orders C2:", "\"toggle ESC/TC\""),
        (1040, 340, "C2 receives the order", ""),
        (1290, 410, "C2 sends its messages", "on the C2 network"),
    ]
    prev = None
    for i, (x, y, a, b) in enumerate(steps2):
        yy = y + y0
        num(s, x - 100, yy, i + 1, C["can_h"] if y < 260 else (C["serial"] if y == 270 else "#16a34a"))
        s.text(x - 78, yy - 3, a, 13, weight="bold")
        s.text(x - 78, yy + 14, b, 12, MUTED)
        if prev:
            arrow(s, [(prev[0] - 100 + 15, prev[1] + y0 + 10), (x - 100 - 12, yy - 10)], "#94a3b8", 2.5)
        prev = (x, y)
    s.text(30, 885, "Only C1 starts a conversation on the serial wire; C2 and BH only answer. Without C2 there is no ESC/TC; without BH no text on the cluster.",
           14, MUTED)
    s.save("message_flow.svg")


# ---------------------------------------------------------------- 3. flashing
def flashing():
    s = Svg(1500, 560)
    s.text(30, 42, "Loading the firmware into one board (repeat for C1, C2, BH)", 26, weight="bold")
    s.text(30, 70, "The chip's own USB loader (DFU) does the work. Nothing can be damaged by trying again.", 15, MUTED)
    steps = [
        ("Unplug its power plug", ["the 2-pin plug on P3", "(rule: never USB + plug", "on the same board)"], "#dc2626"),
        ("Hold its BOOT button", ["keep holding…"], C["boot"]),
        ("Plug the USB-C data cable", ["laptop ↔ board, while", "still holding BOOT"], C["serial"]),
        ("Release BOOT", ["PC sees \"STM32 BOOTLOADER\"", "(USB ID 0483:df11)"], C["boot"]),
        ("Load the image", ["C1.bin → C1, C2.bin → C2,", "BH.bin → BH", "first time: full chip erase"], "#7c3aed"),
        ("Unplug USB, then", ["reconnect the power plug"], "#16a34a"),
    ]
    w = 225
    for i, (t, lines, col) in enumerate(steps):
        x = 30 + i * (w + 16)
        s.rect(x, 100, w, 250, fill="#fff", stroke=col, sw=3, rx=12)
        num(s, x + 30, 132, i + 1, col)
        s.text(x + 52, 138, "", 1)
        words = t.split(" ")
        line1, line2 = " ".join(words[:3]), " ".join(words[3:])
        s.text(x + w / 2, 180, line1, 15, weight="bold", anchor="middle")
        if line2:
            s.text(x + w / 2, 200, line2, 15, weight="bold", anchor="middle")
        for j, l in enumerate(lines):
            s.text(x + w / 2, 236 + j * 20, l, 13, MUTED, anchor="middle")
        if i < len(steps) - 1:
            arrow(s, [(x + w + 2, 225), (x + w + 14, 225)], "#94a3b8", 3)
    # commands
    s.rect(30, 380, 1440, 160, fill="#0f172a", rx=12)
    s.text(50, 412, "Linux / macOS (dfu-util), the repo Makefile's own command:", 15, "#93c5fd", weight="bold")
    s.text(50, 442, "sudo dfu-util -d 0483:df11 -c 1 -i 0 -a 0 -s 0x08000000:leave -D C1.bin", 16, "#e2e8f0")
    s.text(50, 480, "Windows: STM32CubeProgrammer → USB → Connect → \"Erasing & Programming\" → choose the .elf → Start.", 15, "#e2e8f0")
    s.text(50, 508, "If the PC does not see the board: shorter cable, other port, flip the USB-C plug, hold BOOT until the plug is fully in (manual §1.11).",
           13, "#94a3b8")
    s.save("flashing_steps.svg")


# ---------------------------------------------------------------- 4. meter checks
def meter_checks():
    s = Svg(1500, 840)
    s.text(30, 42, "Every measurement in the build, with the value you should see", 26, weight="bold")
    s.text(30, 70, "Ω = resistance (board/car unpowered) · V = voltage · BEEP = continuity mode · mA = current (meter in series at the fuse)",
           15, MUTED)
    rows = [
        ("H0", "Ω", "CAN_H ↔ CAN_L on each board's terminal (unpowered, no jumper)", "118 Ω → remove R1+R2 · open → OK · 60 Ω → jumper on"),
        ("H0", "BEEP", "Each pad ↔ its chip pin (CK 37, DO 34, RES 7, B0 44, G, 3V3)", "every pad beeps to the pin listed in §2.2"),
        ("H0", "V", "U1 pin 3 (transceiver supply), board on USB only", "≈ 3.3 V → OK for our power · ≈ 5 V → 5 V transceiver, see §4.6"),
        ("H1", "Ω", "CAN_H ↔ CAN_L again, after removing R1 + R2", "well above 1 kΩ"),
        ("H1", "Ω", "U1 pin 8 ↔ G (after removing R4, if fitted)", "≈ 10 kΩ (R18 only)"),
        ("H6", "V", "Converter output, NO board connected, 12 V in", "3.30 V (3.2–3.4 V); never above 3.6 V"),
        ("H7", "V", "P3 3V3 pad of each board on the rail", "3.2–3.4 V, power LED on, nothing warm"),
        ("H8", "Ω / V", "Bypass port, car asleep: 6↔14 · 12↔13 · 3↔11 · 16↔4", "≈ 60 Ω · ≈ 60 Ω · low value · ≈ 12 V"),
        ("S4", "V", "C1 chip pin 15 / slave U1 pin 8 (bench, no car)", "≈ 0 V awake → ≈ 3.3 V asleep"),
        ("S4", "V", "CAN_H ↔ CAN_L DC on each slave while asleep", "≈ 0 V (safe); clearly above 0.5 V → stop"),
        ("H10", "Ω", "Each bus through the finished harness, in the car, unpowered", "≈ 60 Ω (≈ 40 Ω = a terminator is still on)"),
        ("H11", "mA", "12 V current at the fuse: awake, then ≈ 1 min after the car sleeps", "drops when asleep (author: ≈ 15 mA asleep, < 30 mA running)"),
    ]
    icon = {"Ω": "#0891b2", "V": "#dc2626", "BEEP": "#16a34a", "mA": "#7c3aed", "Ω / V": "#0891b2"}
    s.rect(30, 90, 1440, 40, fill="#e2e8f0", rx=6)
    for x, t in [(50, "Step"), (130, "Meter"), (230, "Where to put the probes"), (870, "What you should read")]:
        s.text(x, 116, t, 15, weight="bold")
    for i, (step, unit, where, read) in enumerate(rows):
        y = 140 + i * 56
        s.rect(30, y, 1440, 50, fill="#ffffff" if i % 2 else "#f8fafc", rx=6)
        s.text(50, y + 31, step, 16, weight="bold")
        s.rect(122, y + 11, 82, 28, fill=icon[unit], rx=14)
        s.text(163, y + 30, unit, 14, "#fff", anchor="middle", weight="bold")
        s.text(230, y + 31, where, 14)
        s.text(870, y + 31, read, 14, "#0f172a", weight="bold")
    s.save("meter_checks.svg")


# ---------------------------------------------------------------- 5. board check decision tree
def board_check():
    s = Svg(1500, 900)
    s.text(30, 42, "Checking one UCAN before it is used (do this on each board — step H0/H1)", 26, weight="bold")
    q = [
        ("1", "Chip marked STM32F072CB?", "yes → continue", "no → don't use this board", 110),
        ("2", "Transceiver U1: marked VP230 (SN65HVD230)? On USB only, U1 pin 3 ≈ 3.3 V?",
         "yes → OK for our 3.3 V power", "pin 3 ≈ 5 V → 5 V transceiver: feed this board 5 V (§4.6)", 250),
        ("3", "Unpowered, no jumper: CAN_H ↔ CAN_L on the terminal?",
         "≈ 118 Ω → remove R1 + R2", "open → nothing to remove · ≈ 60 Ω → remove the jumper, measure again", 390),
        ("4", "R4 fitted? (resistor beside R18; U1 pin 8 ≈ 1.6 V on USB)",
         "yes → remove R4 (keep R18)", "no → nothing to do", 530),
        ("5", "Every pad beeps to its chip pin (§2.2 table)?",
         "yes → solder the wires", "no → stop: your board differs from FYSETC V1.0", 670),
        ("6", "Later, in S1: CubeProgrammer reports 128 KB flash?",
         "yes → board is ready", "64 KB → don't use it", 790),
    ]
    for n, question, yes, no, y in q:
        num(s, 60, y + 30, n, "#2563eb")
        s.rect(90, y, 560, 64, fill="#eff6ff", stroke="#2563eb", sw=2, rx=10)
        words = question
        if len(words) > 60:
            cut = words.rfind(" ", 0, 60)
            s.text(110, y + 27, words[:cut], 14, weight="bold")
            s.text(110, y + 47, words[cut + 1:], 14, weight="bold")
        else:
            s.text(110, y + 38, words, 14, weight="bold")
        arrow(s, [(650, y + 22), (720, y + 22)], "#16a34a", 3)
        s.rect(720, y, 360, 44, fill="#f0fdf4", stroke="#16a34a", rx=8)
        s.text(735, y + 28, yes, 14, "#14532d", weight="bold")
        arrow(s, [(650, y + 50), (1100, y + 50), (1100, y + 30), (1110, y + 30)], "#dc2626", 2.5)
        s.rect(1110, y + 8, 360, 56 if len(no) > 44 else 44, fill="#fef2f2", stroke="#dc2626", rx=8)
        if len(no) > 44:
            cut = no.rfind(" ", 0, 44)
            s.text(1124, y + 32, no[:cut], 13, "#7f1d1d", weight="bold")
            s.text(1124, y + 50, no[cut + 1:], 13, "#7f1d1d", weight="bold")
        else:
            s.text(1124, y + 36, no, 13, "#7f1d1d", weight="bold")
        if n != "6":
            s.line([(60, y + 47), (60, y + 125)], "#93c5fd", 3)
    s.save("board_check_flow.svg")


# ---------------------------------------------------------------- 6. dashboard menu
def menu_nav():
    s = Svg(1500, 700)
    s.text(30, 42, "Using the BACCAble menu on the dashboard (cruise control and ACC must be OFF)", 26, weight="bold")
    # buttons
    s.rect(30, 80, 560, 420, fill="#f8fafc", stroke=C["edge"], rx=14)
    s.text(310, 112, "Cruise-control buttons on the steering wheel", 16, anchor="middle", weight="bold")
    s.circle(310, 290, 120, "#1f2937", "#475569", 4)
    s.text(310, 296, "cruise", 16, "#e2e8f0", anchor="middle")
    for (x, y, lab) in [(310, 190, "SPEED +"), (310, 395, "SPEED −"), (195, 290, "RES"), (425, 290, "DIST")]:
        s.rect(x - 48, y - 18, 96, 36, fill="#334155", stroke="#94a3b8", rx=10)
        s.text(x, y + 6, lab, 14, "#f8fafc", anchor="middle", weight="bold")
    s.text(60, 450, "Button names differ per wheel: RES or DISTANCE do the same here.", 13, MUTED)
    s.text(60, 472, "The exact layout of your wheel may differ from this sketch.", 13, MUTED)
    # actions
    acts = [("Hold RES (or DIST) ≈ 2 s", "show / hide the menu"), ("SPEED −", "next item"), ("SPEED +", "previous item"),
            ("Press firmly", "jump ±10 (numbers)"), ("Short press RES", "select / toggle the item")]
    for i, (a, b) in enumerate(acts):
        y = 120 + i * 62
        s.rect(630, y, 360, 50, fill="#eff6ff", stroke="#2563eb", rx=10)
        s.text(650, y + 31, a, 15, weight="bold")
        arrow(s, [(990, y + 25), (1030, y + 25)], "#2563eb", 3)
        s.text(1040, y + 31, b, 15)
    # menu tree
    s.rect(30, 530, 1440, 150, fill="#fff", stroke=C["edge"], rx=12)
    s.text(50, 560, "Main menu", 16, weight="bold")
    s.text(50, 584, "version · Show Params · Read/Clear Faults · Immobilizer ON/OFF · Dyno · ESC/TC · Front Brake · 4WD · SETUP MENU · PARAMS SETUP …", 13)
    s.text(50, 618, "SETUP MENU", 16, weight="bold")
    s.text(50, 642, "first item SAVE & EXIT · then one item per function: O = not selected, Ø = selected — choose, then SAVE & EXIT to store", 13)
    s.text(50, 666, "Only the functions selected in SETUP appear in the main menu. The menu hides ≈ 40 s after the engine stops.", 13, MUTED)
    s.save("menu_navigation.svg")


# ---------------------------------------------------------------- 7. LEDs
def leds():
    s = Svg(1500, 690)
    s.text(30, 42, "What the three LEDs on each board tell you", 26, weight="bold")
    s.text(30, 70, "LD3 = power · LD2 \"TX\" = the firmware's blue LED · LD1 \"RX\" = the firmware's red LED. They are dim by design.", 15, MUTED)
    rows = [
        ("LD3 power", "#22c55e", "steady", [(0, 1000)], "board has 3.3 V"),
        ("LD2 blue", "#3b82f6", "short pulses", [(60, 90), (330, 360), (610, 640), (880, 910)], "the board is acting on something (a CAN frame it handles, a serial order, a menu press, a save)"),
        ("LD2 blue", "#3b82f6", "2 blinks at power-up", [(40, 140), (240, 340)], "immobilizer is ON (with our defaults it is OFF, so no double blink)"),
        ("LD2 blue (C1)", "#3b82f6", "1 flash, then C2/BH go dark", [(80, 110)], "the car went quiet 3.5 s → C1 put C2 and BH to sleep (their power LED stays on)"),
        ("LD1 red", "#ef4444", "single short flash", [(500, 530)], "something needed attention (a serial error, a slow loop); a flash at start-up is normal"),
        ("LD1 red", "#ef4444", "8 or 9 blinks", [(i * 110, i * 110 + 55) for i in range(8)], "saving settings to flash failed (erase / write)"),
        ("LD1 red", "#ef4444", "blinking forever", [(i * 200, i * 200 + 100) for i in range(5)], "start-up error; the speed tells which (§11.3) → reflash"),
    ]
    for i, (name, col, pat, pulses, meaning) in enumerate(rows):
        y = 100 + i * 75
        s.rect(30, y, 1440, 64, fill="#f8fafc" if i % 2 == 0 else "#fff", rx=8)
        s.circle(60, y + 32, 12, col, C["edge"], 1.5)
        s.text(82, y + 28, name, 15, weight="bold")
        s.text(82, y + 48, pat, 12, MUTED)
        x0, w = 300, 420
        s.line([(x0, y + 44), (x0 + w, y + 44)], "#cbd5e1", 2)
        for a, b in pulses:
            xa, xb = x0 + a * w / 1000, x0 + b * w / 1000
            s.rect(xa, y + 18, max(4, xb - xa), 26, fill=col, rx=3)
        s.text(750, y + 38, meaning, 14)
    s.text(30, 670, "If C2 and BH never pulse on the bench, check the serial wire (S3). If they go dark ≈ 4 s after power-up with no car, that is sleep working (S4).",
           14, MUTED)
    s.save("led_meanings.svg")


if __name__ == "__main__":
    overview()
    message_flow()
    flashing()
    meter_checks()
    board_check()
    menu_nav()
    leds()
    print("ok")
