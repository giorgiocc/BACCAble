# DIY BACCAble — Full Plan, Build Steps and Firmware (v4.4)

**Mission:** build our own BACCAble from loose boards instead of buying the author's ready-made device, and make it **behave the same as the author's device in every way except the WS281x LED strip** (not built, not wired, left disabled).
**Car:** 2022 Alfa Romeo Giulia Sprint Q4 · 2.0 petrol · MY22 cluster · SGW with an owned bypass cable (owner confirmed it passes all three buses).
**Owner's default choices:** gasoline parameters, **immobilizer OFF** and **Start&Stop disabler OFF** at first start (both still available: Start&Stop in the SETUP menu, immobilizer with the long button press).
**Status:** research, design and firmware build done; **nothing flashed or installed yet; the images are untested on hardware.**

Evidence tags: **[Repo]** read in this fork (manual v4.9, code, schematic, diagrams, build files) · **[GiUCAN]** anegrin/GiUCAN, linked from the README · **[Author]** author's answer in upstream issue #34 · **[Infer]** my engineering inference — verify · **[Built]** compiled and checked in this session.

---

## 1. What "the same as the author's device" means — parity table

The author's device (schematic `hardware/newBaccableDedicatedPcb/BACCABLE_SCHEMATIC.pdf`) is one PCB in an OBD plug with three STM32F072 chips. We rebuild it from three FYSETC UCAN boards.

| Part of the author's device | How the author does it [Repo] | How we do it | Same? |
|---|---|---|---|
| Three chips, one per CAN bus (C1, C2, BH) | U10/U20/U30, STM32F072, one transceiver each, CAN on PB8/PB9 | **Three UCAN boards** (STM32F072CB + CAN transceiver, CAN on PB8/PB9) | ✅ — **all three are required** |
| Firmware | `baccableC1/C2/BH` images from this repo | Same source; C1 built with our flags (§8), C2/BH unchanged | ✅ |
| Serial link between chips | one `Serial` net on PA14 of all three chips (USART2, 38400 baud, half-duplex, open-drain) | one wire joining the **CK pads** (PA14) of the three UCANs | ✅ |
| Sleep ("low consume") | C1 **PA4** holds C2/BH in reset; C1 **PA5** puts the C2/BH transceivers in standby; C1 keeps listening and wakes them on CAN activity | **Reset line:** C1 **DO pad (PA13)** → **RES pads** of C2 and BH (flag `UCAN_LOW_CONSUME_PINS`). **Standby line:** C1 **PA5** (unchanged author pin, fine wire on chip pin 15) → **pin 8 (S/RS) of the CAN transceiver** on C2 and BH (§5.1) | ✅ identical behaviour (same firmware logic, same two lines) |
| Power | 12 V from OBD pin 16 → fuse F1 → buck U1 (4.5–35 V in) → **3.3 V straight to the chips**; USB 5 V can also feed the buck input through diode D2; ≈ 15 mA asleep, < 30 mA running | **Chosen — Option B:** pin 16 → fuse 1 A → **12→3.3 V buck → 3V3 + G pads** of the three UCANs (§4) | ✅ identical topology; rule: unplug a board's 3V3 plug before plugging USB into it (no D2 diode on a UCAN) |
| Programming button | one button pulling BOOT0 of all three chips | one push button **B0 ↔ 3V3** per UCAN | ✅ |
| USB port per chip (flash, sniffer, ELM327, pen drive) | J10/J20/J30 USB-C | each UCAN's own USB-C | ✅ |
| Status LEDs | green power + red (PA0) + white/blue/yellow (PA1) per chip | UCAN power LED + its two LEDs on PA0/PA1 (`UCAN_BOARD_LED_INVERSION` is the build default) | ✅ |
| No CAN termination | none on the PCB | UCAN termination header left **open**; measure (§6) | ✅ |
| OBD plug through the SGW bypass | the PCB is the OBD plug | OBD male breakout harness into the bypass port | ✅ |
| LED-strip output (PA11) | OBD pin 8 | **not built** (mission) | ➖ excluded |
| Aftermarket exhaust-valve remote outputs (C1 PA8 = Q10, PA7 = Q11) | transistors on the PCB, OBD pins 1/2/15 | optional: two transistors on fine wires to the C1 chip (§10) — only if you fit aftermarket valves with a radio remote | ⚪ optional |
| Pedal-booster serial (C1 USART1 on PB6) | cable to "schizzaForte" | optional fine-wire on C1 pin 42 (§10); the manual says the pedal booster is "under development, do not activate" | ⚪ optional |
| STS inputs, GSM footprint | on the PCB | **not used by the firmware** (no code reads them) | — nothing to copy |

**What is not the same (honestly):** loose boards in our own box instead of the moulded OBD plug; the reset line leaves from PA13 instead of PA4 (same signal, a pad instead of a chip pin); one boot button per board instead of one shared button; each UCAN keeps its own power LED and regulator (bypassed by the 3.3 V rail).

**The author's device we are copying** (manual §1.11): one box, three USB-C ports (one per chip: BH, C2, C1 from left to right) and one programming button.

![Author's BACCAble: USB-C per bus and programming button](images/manual_programming_button_usb_ports.png)

*Source: `manuals/Baccable_manual_EN.pdf`, page 16.*

---

## 2. Architecture and wiring

### 2.1 Buses (manual §1.2, DLC pinout image)
| Board | Role | OBD H / L | Bus speed | Main functions |
|---|---|---|---|---|
| **C1** | master/gateway | **6 / 14** | 500 kbit/s | dashboard menu and settings, Start&Stop, immobilizer, shift, 4WD disabler, ACC/HAS pads, windows, seat-belt, read faults (BODY/ECM), ELM327, sniffer, sleep control |
| **C2** | slave | **12 / 13** | 500 kbit/s | ESC/TC, DYNO, front-brake override, front park mute, ABS faults |
| **BH** | slave | **3 / 11** | 125 kbit/s | text on the cluster, odometer blink, park mirror, DNA Memory (not usable on the owner's car) |

GND = OBD 4 and 5, +12 V = OBD 16. [Repo]

![DLC pinout](images/dlc_pinout.png)

The picture is drawn from the car side (pins 1–8 bottom row, 9–16 top row): trust the numbers on your plug.

The author's own OBD plug pinout (what his PCB uses on each pin — we only use 3, 4, 5, 6, 11, 12, 13, 14, 16):

![Author's BACCAble OBD pinout](../hardware/newBaccableDedicatedPcb/pinout.png)

*Source: `hardware/newBaccableDedicatedPcb/pinout.png` (also manual page 5). CMD1–3, STS1–3 and LED CTRL are the author's extra I/O (§10); not used here.*

### 2.2 UCAN pads (read from the silkscreen in the repo's photos)
From `hardware/system_interconnection/ShowParamsOnDashboardConnections.png` and GiUCAN's diagrams, USB-C at the bottom:
- **CAN terminal:** CAN_L · CAN_H · GND.
- **Right pad column, from the USB end up:** **CK** (PA14, serial) · **DO** (PA13) · **RES** (reset) · **G** · **B0** (BOOT0) · **3V3**.
- **Left pad column, from the USB end up:** RX · TX · G · 3V3 (not used).
- A **2-pin termination header** beside the CAN terminal (keep it open).
Check these against your own boards before soldering. [Repo][GiUCAN]

![UCAN pad labels, zoomed](images/ucan_pads_zoom.png)

*Zoom of the author's diagram below: left board seen from the bottom (CAN_L · CAN_H · GND terminal; right column CK · DO · RES · G · B0 · 3V3, the blue serial wire on CK; left column RX · TX · G · 3V3); right board seen from the top (TX/RX LEDs, chip, termination header next to the green terminal).*

![Author's two-UCAN wiring](../hardware/system_interconnection/ShowParamsOnDashboardConnections.png)

*Source: `hardware/system_interconnection/ShowParamsOnDashboardConnections.png` — the author's two-board example (C1 master + BH slave, one wire on the SWCLK/CK pad, USB 5 V). Our build adds C2 on the same wire (author, issue #34), the reset wire, and the 3.3 V rail of §4.*

### 2.3 Complete wiring (the author's PCB rebuilt)
```
                         OBD male plug (into the SGW bypass port)
  pin 6 ─ C1.CAN_H    pin 12 ─ C2.CAN_H    pin 3  ─ BH.CAN_H
  pin 14 ─ C1.CAN_L   pin 13 ─ C2.CAN_L    pin 11 ─ BH.CAN_L
  pins 4/5 (GND) ─ C1.GND, C2.GND, BH.GND (CAN terminals), buck GND, G pads
  pin 16 (+12 V) ─ fuse 1 A ─ 12→3.3 V buck ─ 2-pin plugs ─ 3V3 + G pads of C1, C2, BH

  Serial (author's "Serial" net):     C1.CK ──── C2.CK ──── BH.CK      (one wire)
  Sleep reset (author's PA4 line):    C1.DO ──┬─ C2.RES
                                              └─ BH.RES                (one wire)
  Sleep standby (author's PA5 line):  C1 chip pin 15 (PA5) ──┬─ C2 transceiver pin 8 (S/RS)
                                                             └─ BH transceiver pin 8 (S/RS)   (one wire)
  Boot buttons:                       B0 ↔ 3V3 push button on each board
```
No series resistors on the serial or reset wires (the author's PCB and diagrams use bare nets; the firmware drives both open-drain). Keep both wires short (≤ ~30 cm). [Repo][Infer]

---

## 3. Boards to use

- **FYSETC UCAN V1.0 ×3 + 1 spare.** It is one of the four boards the README lists as compatible ("important that the chip is an STM32F072"); the author ships cases for it (`hardware/box/dual_fysect_ucan`, `single_fysect_ucan`) and the firmware's LED default is for it. [Repo]
- **All three need 128 KB of flash**: C1 is 79,004 bytes [Built]; C2 and BH keep a 64 KB FAT area and their settings in flash up to `0x0801FFFF` (§11.4). The author's own chips are labelled C8T6 (64 KB on paper, see the datasheet in `hardware/canable/`) yet run these images with a 96 KB code region and settings at `0x0801F800`, so they behave as 128 KB; the UCAN's CB chip is 128 KB on paper. **Read the flash size of every board in STM32CubeProgrammer before flashing.** [Repo][GiUCAN]
- Other boards the README lists (MKS CANable, DykbRadio Nano, candleLight) work only with a 128 KB STM32F072; CANable-type boards need `-DDISABLE_UCAN_BOARD_LED_INVERSION` (their LEDs are active-low on PA0/PA1, see the MKS schematic in the repo). Not needed for this build. [Repo]

The author's own 3D cases for the UCAN (we build our own box, but they show how he mounts the board and the 2-pin header next to the green terminal):

| Two UCANs (`hardware/box/dual_fysect_ucan/preview.png`) | One UCAN (`hardware/box/single_fysect_ucan/preview.png`) |
|---|---|
| ![Dual UCAN case](../hardware/box/dual_fysect_ucan/preview.png) | ![Single UCAN case](../hardware/box/single_fysect_ucan/preview.png) |

---

## 4. Power — chosen design: Option B, identical to the author (always-on 12 V → 3.3 V rail)

### 4.1 The chain
Only the car's OBD port is used, through your SGW bypass cable: **pin 16 = +12 V** (the pin the author's device is powered from, manual §1.2; the manual's immobilizer section relies on it being live with the car off) and **pins 4/5 = ground**. No other wire in the car is tapped.
```
OBD pin 16 (+12 V) ─ inline fuse 1 A ─ 12→3.3 V buck IN+ ; OUT 3.3 V ─┬─ 2-pin plug ─ C1: 3V3 pad + G pad
OBD pins 4/5 (GND) ─────────────────── buck IN− / OUT−               ├─ 2-pin plug ─ C2: 3V3 pad + G pad
                                                                      └─ 2-pin plug ─ BH: 3V3 pad + G pad
(no USB-C power leads — the USB-C ports stay free for flashing, ELM327 and the sniffer)
```
This is the author's topology: his PCB has fuse **F1** → buck **U1** making **3.3 V directly** (feedback divider 69.8 kΩ / 22.1 kΩ ≈ 3.3 V) for all three chips and transceivers. Feeding the UCANs on their **3V3 pads** bypasses each UCAN's own 5 V → 3.3 V regulator, exactly like the author's single 3.3 V rail, and gives the lowest parked current. [Repo: schematic sheet 1, manual §1.2/§1.10][Infer]

![Author's schematic sheet 1: OBD connector, power and programming button](images/author_schematic_sheet1_connectors_power.png)

*Source: `hardware/newBaccableDedicatedPcb/BACCABLE_SCHEMATIC.pdf`, sheet 1. Top: OBD plug J1 (pin 16 = 12 V, 4/5 = GND, CAN pins). Middle: **12 V → fuse F1 → buck U1 → 3.3 V** (R1 69.8 kΩ / R2 22.1 kΩ set the output), **D2 from the 5 V (USB) net into the buck input**, green power LED D1. Right: programming button **S1** pulling **BOOT** high for all three chips (R4 10 kΩ pull-down).*

### 4.2 Parts and settings
- **Fuse:** inline fuse holder + **1 A** fuse, as close to the OBD plug as possible.
- **Buck:** automotive **12 → 3.3 V** step-down module (fixed 3.3 V, or adjustable set to 3.3 V): input rated well above 14 V (≈ 30 V or more, for load-dump spikes — the author's U1 is rated 4.5–35 V), output **≥ 0.5 A**, **low no-load current** (it is never switched off).
- **Set and check the output at 3.30 V (3.2–3.4 V) with no board connected.** The STM32F072 and the CAN transceivers must never see more than 3.6 V (datasheet in `hardware/canable/`). Re-check after the box is closed if the module has a trim pot.
- **Per board:** a small **2-pin plug** (3V3 + G) so each board can be disconnected from the rail on its own; 22–24 AWG wire.
- **Ground:** buck ground, the three G pads and the three CAN-terminal GND pins all go to OBD 4/5 (one common ground).

### 4.3 The one rule this design adds
The author's PCB can take a PC's USB 5 V at the same time because USB feeds his buck through **diode D2** (my reading of the drawing [Infer]); **a UCAN has no such diode**. So:
> **Never plug a USB cable into a board while its 3V3 plug is connected.** First unplug that board's 3V3 plug, then connect USB (the board then runs from the PC), and reconnect the 3V3 plug only after removing the USB cable.

Otherwise the board's own regulator and the buck would both drive its 3.3 V rail. This applies to flashing (§8), ELM327 and the built-in sniffer (§11.9). [Infer]

**Bench check of the back-feed path (H7):** with a board fed on its 3V3 pad and nothing in its USB-C, measure the USB-C **VBUS** (e.g. with a USB-C breakout or at the regulator input): a reading near 0 V means the UCAN regulator blocks reverse current; a reading of a few volts means 3.3 V leaks back to VBUS — harmless while nothing is plugged in, and the rule above already covers it. [Infer]

### 4.4 Checks before relying on it
- **Bypass cable carries pin 16:** car off, measure **pin 16 ↔ pin 4 ≈ 12 V** on the bypass cable's OBD port (some bypass cables carry only the CAN pins and ground). First action of H6.
- Why always-on: with the boards powered and sleeping, what the author's device keeps in RAM survives a parked car (DNA Memory, the exhaust-flap remembered choice) and — if you ever enable it — the immobilizer stays armed. On your car DNA Memory does not apply (§11.12) and there are no exhaust valves, but always-on 12 V is the author's design and keeps those options open. [Repo]
- **Parked current:** measure in H11 (author's device ≈ 15 mA asleep).

### 4.5 Fallbacks (not chosen)
- **Option A:** pin 16 → fuse → 12→5 V buck (≥ 1 A) → power-only USB-C leads. Same source, one extra regulator stage per board (a bit more parked current); USB service is just swapping leads.
- **Car USB:** 5 V from the console USB or the port near the cigarette lighter (manual §1.7/§2.4: switched on when you get in and when the RF hub wakes) → passive splitter → power-only USB-C leads. Boards lose power when the car sleeps, so DNA Memory and remembered states are lost; otherwise works.

  ![USB-A pinout from the manual](images/manual_usb_hub_5v_pinout.png)

  *Source: manual §1.7, page 10 — pin 1 = +5 V, pin 4 = GND of the car's USB-A socket (the manual's way to tap the console USB hub).*

Rules for every option: **never put 12 V on a UCAN**; one common ground; C2/BH show up as USB pen drives on a data connection (§11.4), so USB-C power leads, if used, must be power-only.

---

## 5. Sleep (low consume) on UCAN boards — identical to the author

**Author's design** (`lowConsume.c`, schematic): C1 never sleeps; after **3.5 s without CAN frames** on its bus it pulls **PA4** low (open-drain) to hold C2 and BH in reset, drives **PA5** to put their transceivers in standby, pauses the serial line and flashes its blue LED; when frames come back it releases both, restarts the serial line, re-sends every function setting to the slaves (≈ 3.5 s later) and arms DNA Memory. Sleep is blocked while a sniffer/ELM327/pen-drive USB session is active. [Repo]

**Problem on a UCAN:** PA4 and PA5 have no pads. Solved line by line below.

### 5.1 Reset line (author's PA4)
**Fix in this fork:** new compile flag **`UCAN_LOW_CONSUME_PINS`** in `Core/Inc/lowConsume.h` moves the reset line to **PA13 = the DO pad** (the pin GiUCAN uses for exactly this, wired to the other board's RES pad). Default builds are unchanged. Verified in the C1 image's disassembly: PA13 open-drain output. [Repo][GiUCAN][Built]
- PA13 is SWDIO: SWD debugging of C1 is no longer possible; USB-DFU flashing is unaffected. At C1 power-up and during C1 flashing PA13 floats high, so the slaves run. [Infer]
### 5.2 Standby line (author's PA5) — no firmware change needed
- The firmware **already drives PA5 exactly as the author's**: push-pull output, **low = slave transceivers active** (set at start-up and on every wake), **high = standby** (set when C1 goes to sleep). Our flag only moved the reset line; PA5 is untouched. [Repo: `lowConsume.c`]
- On the author's PCB PA5 runs to the **RS pin (pin 8)** of the C2 and BH transceivers (schematic sheets 3/4, `CanLowConsumeCmd`, with a 10 kΩ pull-down). On a UCAN the transceiver's standby/silent pin (**pin 8, "S"/"RS"**) is wired to that board's own **PC13** (GiUCAN calls it `CAN_S`, "can silent pin"); the BACCAble C2/BH firmware **never drives PC13**, so an external line can control it without a conflict. [Repo][GiUCAN]
- **Wiring:** one thin wire (30 AWG wire-wrap or enamelled) from **C1's chip pin 15 = PA5** (LQFP48 numbering from the MKS CANable schematic in the repo: PA4 = 14, PA5 = 15) to **pin 8 of the CAN transceiver** (the 8-pin chip next to the green terminal) on **C2** and on **BH**. Pin 15 is on the 0.5 mm-pitch side of the chip: use flux, a fine tip, and check with a loupe that pins 14/16 are not bridged.
- **Before soldering, identify pin 8 on your boards:** pin 1 is marked by the dot; pin 8 is the pin beside pin 1 on the opposite row. Confirm with the multimeter: **continuity between transceiver pin 8 and the board's chip pin 2 (PC13)**. If there is no continuity, stop and re-check (the board differs from GiUCAN's). [Infer]
- **Result:** during sleep the slaves are held in reset **and** their transceivers are in standby/silent mode — the author's exact behaviour and the lowest sleep current. At start-up, before C1's firmware sets PA5, the line floats for a few ms (the author's PCB has a pull-down for this; the UCAN keeps its own default on that pin). [Infer]
- *Optional, fully pin-identical variant:* also take the reset line from C1's chip **pin 14 (PA4)** instead of the DO pad and build C1 **without** `-DUCAN_LOW_CONSUME_PINS` (the author's stock pins). Same behaviour, but one more fine-pitch joint next to pin 15; the DO-pad route is the easier one.
- **Bench gotcha:** with no car, C1 sees no CAN frames and holds C2/BH in reset after 3.5 s. Flash and test the slaves **before** fitting the reset wire, or power C1 off, or use the `C1_BENCH_ONLY` image (§8).

![Author's schematic sheet 2: the C1 chip](images/author_schematic_sheet2_C1.png)

*Source: `BACCABLE_SCHEMATIC.pdf`, sheet 2 (C1). On the left of the chip: **PA0 red LED, PA1 white LED, PA4 `ChipLowConsumeCmd`** (reset of C2/BH — our DO-pad wire), **PA5 `CanLowConsumeCmd`** (standby of the C2/BH transceivers — not reproduced), PA6 STS_1, PA8 → Q10 → CMD_1, PA11 `Led_Control_Pin` (LED strip, excluded), PA11/PA12 USB-C J10, **PA14 `Serial`** (our CK wire), BOOT0 ← BOOT. Right: CAN on **PB8/PB9** to transceiver U11. Sheets 3 and 4 repeat this for C2 (blue LED, plus an unused GSM footprint) and BH (yellow LED); there `ChipLowConsumeCmd` arrives on the chip's **NRST** and `CanLowConsumeCmd` on the transceiver's **RS** pin.*

---

## 6. Termination

The car buses are already terminated, so no board may add a terminator. The repo never says to desolder anything: the author's diagrams say "TERMINATION NOT INSERTED", his PCB has no terminator, and the UCAN pictures show the termination header **without a jumper**. Whether a UCAN also has fixed resistors across CAN H/L is **not documented in the repo** (that claim came from outside research). So: **measure** (H0); if a fixed value is present, removing it is consistent with the author's PCB — practise on the spare. Through the full harness every bus must read **≈ 60 Ω**. [Repo][Diagram]

The author's older single-CANable diagram is where "TERMINATION NOT INSERTED" comes from (the CANable's termination jumper left open). It is a **legacy design — do not build it**: its Start&Stop resistor panel and the 1.5 kΩ resistor on PA14 are obsolete (Start&Stop is now done over CAN and PA14 is the serial wire), and its LED-strip output is out of scope.

![Legacy single-CANable wiring (do not build)](../hardware/system_interconnection/SCHEMA_DI_INTERCONNESSIONE.png)

*Source: `hardware/system_interconnection/SCHEMA_DI_INTERCONNESSIONE.png`.*

---

## 7. Hardware build steps (no firmware yet)

**Parts:** 3 UCAN + 1 spare (owned); OBD2 male plug with all 16 pins wired (needs 3, 4, 5, 6, 11, 12, 13, 14, 16); 12 → 3.3 V automotive buck (§4.2) + inline fuse holder + 1 A fuse; 3 small 2-pin plugs (3V3 + G, one per board); 22 AWG twisted pairs (~3 m) and 24–26 AWG wire for serial/reset; 2.54 mm pin headers; 4 small momentary push buttons (boot); 1 short USB-C **data** cable for flashing; project box, standoffs, cable glands, heat-shrink, ferrules. Tools: multimeter, fine-tip iron, flux, wick, tweezers, loupe; a 12 V bench supply (or 12 V battery) to run the buck on the bench, and a 5 V USB supply for single-board tests.

| Step | Action | Pass when |
|---|---|---|
| **H0** | Inspect every board: chip marking **STM32F072CB**; label C1, C2, BH, SPARE. Unpowered, termination header open: measure CAN_H↔CAN_L. | open circuit (or note the value for H1) |
| **H1** | Termination per §6 (practise on the spare). Keep the header open. | CAN_H↔CAN_L open on each board |
| **H2** | Flash check comes in S1 (needs USB). Solder headers to **CK, DO, RES, B0, 3V3, G** on each board. Fit a push button across **B0–3V3** on each board, reachable from outside the box. | pads clean, no bridges |
| **H3** | **Serial wire:** C1.CK ↔ C2.CK ↔ BH.CK. | continuity CK-CK-CK, no short to G/3V3 |
| **H4** | **Reset wire:** C1.DO ↔ C2.RES and C1.DO ↔ BH.RES. **Standby wire (§5.2):** first check continuity *transceiver pin 8 ↔ chip pin 2* on C2 and BH, then wire C1 chip pin 15 (PA5) → transceiver pin 8 of C2 and of BH; check pins 14/16 of C1 are not bridged. *(Leave unplugged until the slaves are flashed — §5 bench gotcha.)* | continuity, no short |
| **H5** | **CAN harness** to each terminal (P1: 1 = CAN_L, 2 = CAN_H, 3 = GND): C1 → 6/14, C2 → 12/13, BH → 3/11; terminal GND → OBD 4/5. Twist pairs, mark every H wire. | H/L not swapped (swapped = warning lights, manual §1.5) |
| **H6** | **Power harness** (§4): first measure **pin 16 ↔ pin 4 ≈ 12 V** on the bypass cable's port (no 12 V → fallback car USB, §4.5). Then OBD 16 → fuse 1 A → 12→3.3 V buck → three 2-pin plugs (3V3 + G); buck GND → OBD 4/5. On the bench, with **no board connected**, power the buck from 12 V and set/check its output. | 12 V on pin 16; buck out **3.30 V ± 0.1 V** |
| **H7** | **Bench power test:** connect one board's 3V3 plug (USB-C empty): power LED on, 3V3 pad 3.3 V; measure its USB-C VBUS (back-feed check, §4.3). Then all three plugs. Separately confirm each board also runs from USB alone with its 3V3 plug **removed**. | no short, no hot parts, rail stays 3.2–3.4 V |
| **H8** | **Bypass cable check** (car asleep ≥ 10 min, boards unplugged): 6↔14, 12↔13 ≈ 60 Ω; 3↔11 low value; 16↔4 ≈ 12 V; 4/5↔chassis continuity. | all present (owner already confirmed the buses) |
| **H9** | **Box:** standoffs, glands, strain relief; USB-C ports and boot buttons reachable; away from pedals, steering column, knee-airbag path, heat and HVAC flaps. Label boards at both ends. | nothing loose |
| **H10** | **In-car, unpowered:** plug into the bypass port, re-measure every bus ≈ 60 Ω through the harness, connect power last. Do not power the boards on the car with unknown firmware. | ≈ 60 Ω each |
| **H11** | (Always-on option) after the firmware is in (S5): measure the 12 V current at the fuse with the car awake and ≈ 1 min after it sleeps (author's device: ≈ 15 mA asleep, < 30 mA running). | sleep current settles; boards wake when you unlock |

---

## 8. Firmware — what we build and how to flash it

**Only change to the author's code:** the `UCAN_LOW_CONSUME_PINS` flag (§5). Everything else is the author's firmware. [Repo]

**Build** (tested, ARM GCC 13.2; `apt install gcc-arm-none-eabi libnewlib-arm-none-eabi`): run `docs/build_ucan.sh`. It writes `firmware/ucan_prebuilt/` (prebuilt copies are committed there):

| Image | Flags (besides `-DRELEASE_FLAVOR=…`) | Size [Built] |
|---|---|---|
| `C1` | `-DIS_GASOLINE -DUCAN_LOW_CONSUME_PINS -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP` | 79,004 B |
| `C1_BENCH_ONLY` | same + `-DDEBUG_CAN_RX_SIMULATION` (CAN in silent loopback, simulated frames; **never in the car**) | 79,080 B |
| `C2`, `BH` | none (stock) | 37,532 B / 36,800 B |
| `SNIFFER_ActAsCanable` | `CAN_FLAVOR` (plain SLCAN sniffer for SavvyCAN, for the spare) | 25,644 B |

Checked with the preprocessor: `LOW_CONSUME` defined; `IMMOBILIZER_ENABLED`, `SMART_DISABLE_START_STOP`, `IS_DIESEL` undefined. The defaults apply only to a board whose settings flash page is blank, so **erase the whole chip** when flashing a board that ran BACCAble before (CubeProgrammer "Full chip erase"; with dfu-util the DfuSe option `-s 0x08000000:mass-erase:force:leave` should do the same [Infer]). A new UCAN's settings pages are expected to be blank. The fork's "Build Beta Version" GitHub workflow accepts the same flags in its `CFLAGS` input. [Repo][Built]

**Flash a UCAN** (documented in the repo for loose boards): **unplug the board's 3V3 plug first** (§4.3), then hold the **B0** button while plugging the **data** USB-C cable (the chip appears as `0483:df11`), then either
```bash
sudo dfu-util -d 0483:df11 -c 1 -i 0 -a 0 -s 0x08000000:leave -D C1.bin
```
(the Makefile's own `flash` target, `MAKEFILE.md`) or STM32CubeProgrammer → USB → "Erasing & Programming" with the `.elf` (GiUCAN's docs). On Windows install the WinUSB driver with Zadig if CubeProgrammer/DfuSe is not installed (manual §1.11.1). Weak LED or no detection: shorter cable, another port, a slow USB hub, flip the USB-C plug (manual). The firmware has no software jump to the bootloader, so the button is the only way in. [Repo][GiUCAN]

**Building in STM32CubeIDE instead** (the author's way): open `firmware/ledsStripController`, pick the build configuration from the hammer menu, and add our C1 flags to that configuration's preprocessor symbols (or use a "+ user_config" configuration with a `user_config.h`).

![STM32CubeIDE build configurations](../hardware/system_interconnection/compileOptions.jpg)

*Source: `hardware/system_interconnection/compileOptions.jpg` (README). The screenshot is older: today's `.cproject` has ReleaseC1/C2/BH BACCAble, each also "+ user_config", and ReleaseCANable; diesel/gasoline is now a menu setting (or `-DIS_GASOLINE`).*

---

## 9. Bring-up steps

| Step | Action | Pass when |
|---|---|---|
| **S1** | On the **spare**: read device ID and **flash size = 128 KB** in CubeProgrammer, flash `BH`, unplug, replug. | on the data cable it appears as a USB drive "BACCABLE BH" with `Version.txt` (that proves it booted); no steady red blinking |
| **S2** | Read and flash all boards: `C1`→C1 board, `C2`→C2, `BH`→BH (full chip erase). Reset wire **not** fitted yet. | no steady red blinking on any board; C2/BH show their USB drive label on a data cable |
| **S3** | **Bench serial test:** flash `C1_BENCH_ONLY` on C1, fit the CK wire, power all three. | after ~3 s the blue LEDs of C2 and BH pulse about once a second (C1 polling them) |
| **S4** | **Bench sleep test:** flash the real `C1`, fit the reset wire, power all three with no car. | ~4 s after power-up the status LEDs of C2 and BH stop (held in reset; their power LEDs stay on) and C1's blue LED flashes once: the reset wire works. **Standby check:** C1 pin 15 / slave transceiver pin 8 read ≈ 0 V while awake and ≈ 3.3 V once asleep (the standby wire works). **Bus-safety check:** while they are held in reset, measure DC volts between CAN_H and CAN_L on each slave's terminal (nothing else connected): **≈ 0 V = recessive, safe**; anything clearly above ≈ 0.5 V means the slave would hold its bus dominant — do not install it (§5) |
| **S5** | **Car, silent sniff (optional but recommended):** flash `SNIFFER_ActAsCanable` on the spare and use SavvyCAN in silent mode (`M1`) on each bus (500 k C1/C2, 125 k BH); the IDs in §11.5 should appear — on the BH bus look specifically for `0x256` and `0x46C`, which DNA Memory needs (§11.12). Then install the three boards (H10) and power them. | no warning lights; with always-on power the boards wake on unlock (blue LEDs active again) |
| **S6** | **First start:** engine running, cruise control and ACC off → hold **RES** (or DISTANCE) ~2 s → version `BACCABLE ucan-…` on the cluster. With our defaults there is **no** double blue blink and no cluster flash at power-up (those mean "immobilizer active"). Open **SETUP MENU** (§11.7): check **Diesel Params = O** (gasoline), **My23 IPC = O**, Start&Stop = O. | menu works |
| **S7** | Enable functions **one at a time**, SAVE & EXIT, ignition cycle, check for faults after each: dashboard parameters → shift → seat-belt/odometer → windows, park mirror, park mute → proxy-alignment features (ACC pad, HAS pad, race mask). Leave **DNA Memory off** (selector not compatible, §11.12). | no new faults |
| **S8** | **Last, stationary / closed course only:** 4WD disabler (C1), ESC/TC, DYNO, front-brake override (C2). Prove the way back first: disable in the menu, ignition cycle, Clear Faults. | rollback works |

---

## 10. Optional author I/O (not needed for the car functions)

- **Aftermarket exhaust-valve remote** ("Exhaust Flap" with non-QV radio-remote valves; manual §2.30, upstream issue #40): the author's C1 drives two transistors from **PA8 (Q10, "open")** and **PA7 (Q11, "close")** that press the remote's buttons for ≈ 1 s. On a UCAN these pins have no pad: solder a fine wire to the C1 chip's **pin 29 (PA8)** and **pin 17 (PA7)** (LQFP48 numbering from the MKS schematic in the repo), each through a base resistor to a small NPN transistor across the remote's button. Only if you fit such valves; your 2.0 Sprint has no factory valves, so the CAN "QV" mode does not apply. [Repo][Infer]
- **Pedal booster ("schizzaForte")** on C1 **USART1, PB6 = pin 42**, half-duplex 9600 baud: manual says "under development, do not activate". Not wired. [Repo]
- **LED strip (PA11): excluded by the mission.** Leave "Led Controller" deselected in SETUP.

---

## 11. Reference — how the firmware works (read from this fork)

### 11.1 Start-up and main loop
Clocks (internal HSI48, no crystal) → LEDs → CAN init → C1 loads settings from flash → serial (USART2 on PA14) → C2/BH format/mount their flash drive and start USB at power-on → C1 and C2 open CAN at 500 k, BH at 125 k (accept-all filter). Main loop: LEDs, CAN transmit queue, serial queue, flavor periodic function, CAN receive → per-ID handlers. A loop iteration longer than 2 ms lights the red LED. [Repo]

### 11.2 Serial protocol between the boards
Fixed-length frames, first byte = destination (C1 0x01, C2 0x02, BH text 0x03, BH status 0x08, BH 0x0A, C2+BH 0x0B, C1+BH 0x0C, C1+C2 0x0D; ELM327 bridge 0x0E–0x10). Only C1 starts: one message every ≈ 250 ms; C2/BH may answer only within ≈ 200 ms of a message to them; for "both slaves" messages only C2 answers. After a 2 s quiet period C1 polls C2 every ≈ 1.0 s and BH every ≈ 1.26 s, and ≈ 3.5 s after boot/wake it sends all function settings. C1 never waits for an answer. [Repo]

### 11.3 LEDs
Blue (PA1) short pulses = activity (CAN frames handled, serial frames, settings saved, wake). Red (PA0) = attention (serial error, failed flash save, slow loop). Red blinking 8× / 9× = flash erase / write failed. Red blinking forever = start-up error (rate shows which: 500 ms serial, 750 ms USART1, 1000/1500/2000/2500 ms USB clock, system clock, oscillator, DMA). Blue blinks twice at power-up only when the immobilizer is active. [Repo]

### 11.4 Flash map and USB
C1 settings `0x0801F800` (33 values), statistics `0x0801F000`, shown parameters `0x0801E800`. C2/BH: 60 KB code region, a 64 KB FAT drive at `0x08010000–0x0801FFFF` ("BACCABLE C2/BH", `Version.txt`), BH mirror positions at `0x0801F800`. C1 starts USB only for sniffer/ELM327; C2/BH start their USB drive at power-on (not after a reset). PA14 is the serial line, so SWD is not usable on any board. [Repo]

### 11.5 CAN IDs each board reads (for the S5 sniff)
C1 bus: 0x101, 0x107, 0x192, 0x1F7, 0x2EF, 0x412, 0x41A, 0x41E, 0x420, 0x4AF, 0x4B1, 0x4B2, 0x545, 0x5A5, 0x5A8, 0x5AE. BH bus: 0x090, 0x256, 0x25A, 0x2EE, 0x354, 0x356, 0x3E6, 0x3E8, 0x46C, 0x5A0, 0x5A6, 0x5A8, 0x5AC. C2 bus: 0x0FA, 0x1F5, 0x1FC, 0x3E7, 0x4AF, 0x4B4, 0x54A, 0x5B0. All boards: 0x0FC, 0x116, 0x1EF, 0x1F0, 0x226, 0x2ED, 0x2FA, 0x358, 0x384. [Repo]

### 11.6 How functions act on the car
The boards are bus participants, not a gateway: to change something they receive a frame and immediately send a modified copy with the same ID and a recomputed CRC (drive style 0x384, shift 0x2ED, key fob 0x1EF, steering buttons 0x2FA), or use UDS requests (parameters, seat-belt, read/clear faults, DYNO, exhaust QV). Engine "on" = rpm > 400 from 0x0FC; most functions wait ≈ 5 s of engine running. [Repo]

### 11.7 Dashboard menu
Driven by the steering-wheel buttons (0x2FA), only with cruise control and ACC off. Hold RES/DISTANCE ≈ 2 s to show/hide; short press selects; speed-down = next, speed-up = previous, firm press = ±10. **Main menu:** version · Show Params · Read Faults · Clear Faults · Immobilizer ON/OFF · Dyno · ESC/TC · Front Brake · 4WD · SETUP MENU · PARAMS SETUP MENU · HAS · Exhaust Flap · "Save Log" (test stub, ignore) · Reset statistics · Max Hold (disabled functions are skipped). **SETUP MENU:** SAVE & EXIT · Start&Stop · Launch Torque · Led Controller (leave off) · Shift indicator · Shift RPM · My23 IPC · Regen alert · Seat-belt alarm · Route · ESC/TC · Dyno · ACC pad · Brakes override · 4WD disabler · Clear faults · Read faults · Remote start (do not enable) · **Diesel Params** · Odometer blink · Pedal booster (do not enable) · Pedal power · Park mirror · ACC autostart · Close windows · Open windows · HAS pad · Exhaust flap · Front park mute · Sniffer · ELM327 · DNA Memory. There is no immobilizer item: toggle it with engine running, cruise/ACC off, gear in neutral, holding cruise **speed-up** ≈ 20 s (manual says 30–40 s) until the cluster blinks (3 blinks = ON, 6 = OFF). The menu hides ≈ 40 s after the engine stops. [Repo]

### 11.8 Fresh-board defaults (`readFromFlash()`), with our C1 flags
Immobilizer **OFF**, Start&Stop disabler **OFF**, gasoline, Clear Faults ON, seat-belt alarm "enabled"; everything else OFF. Note: the seat-belt setting has no "leave untouched" choice — about 2 s after each engine start after a board power-up, C1 writes it to the cluster (`2F 55A0 03 01` = chime on, stock behaviour; `00` if you deselect it). [Repo]

### 11.9 ELM327 mode (manual §2.32)
Enable ELM327 in SETUP, connect a data USB cable to **C1**, then the OBD side. It answers as "ELM327 v1.4" for MultiECUScan/AlfaOBD and forwards requests for ECUs on the other buses over the serial wire to **C2/BH** — this is why all three boards matter for proxy alignment. While a host is connected the dashboard buttons are ignored; the mode switches itself off after 120 s without commands (and a lost host is waited for 3 min). **The host must enumerate the USB within 10 s of the function starting** (`SNIFFER_ACTIVATION_TIMEOUT_MS`), which happens at board start-up — that is why the manual says "USB cable first, then the OBD connector". With our boards: (1) unplug the OBD plug (everything off); (2) unplug the **3V3 plug** of the board you want (C1 for ELM327; C1, C2 or BH for the built-in sniffer) and connect the laptop's data cable to it instead — that board now runs from the laptop; (3) plug the OBD plug back so all boards start together. Never USB and the 3V3 plug on the same board at once. Afterwards remove the USB cable, then reconnect the 3V3 plug. [Repo][Infer]

### 11.10 Functions that need more than the boards
ESC/TC and the race screen need race mode enabled by **proxy alignment** (manual §2.19, which also explains keeping the pedal maps); ACC pad needs ACC hardware + proxy; HAS pad needs MY20+ hardware + proxy; park mirror needs mirror encoders; DNA Memory needs a monostable DNA selector on BH **and** always-on power (owner's car: selector not monostable → not available); DPF/regen alert is diesel-only; Remote start and Pedal booster are "do not activate". [Repo]

**Route** (manual §2.9) lets an OBD app read native CAN frames through C1: a UDS request to `0x18DABAF1` with `22 xz yyyyyyyy` makes C1 answer on `0x18DAF1BA` with 5 bytes of the requested frame:

![Route handshake](../hardware/system_interconnection/route.png)

*Source: `hardware/system_interconnection/route.png`.*

### 11.11 Things to know in the code
- Gasoline parameter "OVER RPM: sec" has reply ID `0xDA18F110` instead of `0x18DAF110` (probable typo, that page may not update) — left unchanged.
- Dormant "pump force" test code (ECM security access) exists but its only start line is commented out, so it never runs; re-check if you merge newer upstream code.
- `user_config.h.sample` calls READ FAULTS experimental while the manual documents it.
- Licence (`LICENSE.MD`): use, modify and share with attribution to Gaucholivido - Tr3ma; **commercial resale prohibited**. [Repo]


### 11.12 DNA Memory — how it works and what it needs
**Owner's car: the DNA selector is not monostable, so DNA Memory does not apply.** The manual (§2.34) and the BH code say that with another selector type BH sees no usable `0x256` frames and sends nothing, so leaving it enabled would be harmless but useless — leave it **deselected**. The S5 sniff confirms it (no `0x256` on the BH bus, or not the press pattern described below). Everything else that uses the drive style (ESC/TC race, shift, exhaust DR, pedal booster) reads it from `0x384`/`0x46C`, not from the selector, so it is unaffected. [Repo]

**How it works** (`functions_C1baccable.c`, `functions_BHbaccable.c`, `lowConsume.c`, manual §2.34)
1. **C1 remembers** the drive style from frame `0x384` on the C1 bus while the engine runs (> 400 rpm); when the engine stops the memory is frozen. It is kept only in **RAM** (`dnaMemoryStyle`, starts as "none").
2. **The car sleeps:** C1's bus goes quiet for > 3.5 s, so C1 enters low consume.
3. **The car wakes:** frames come back, C1 leaves low consume and sets `dnaMemoryWakeUp` — this is the *only* place the restore is armed.
4. **First engine start after that:** 2 s after the engine is running, if the current style differs from the memorized one, C1 sends BH one serial command ("set A/N/D/R").
5. **BH moves the selector:** on the BH bus it re-sends the DNA selector's own frame `0x256` with "up" (0x40) or "down" (0x20) pressed, one step per frame; D→R is a 2 s long press. It reads the current style from `0x46C` and the rpm from `0x3E6` (both BH bus). 1 s after the sequence it checks the style and repeats once if needed. It aborts if you touch the selector or the engine stops.
6. Afterwards nothing more until the next sleep/wake; Start&Stop engine stops do not trigger it.

**What it needs**
| Need | Why | Our build |
|---|---|---|
| **C1 and BH boards** with the serial wire | C1 decides, BH presses | ✅ |
| **Continuous power through the parked period** | the memorized style is in RAM; losing power erases it | ✅ with §4 always-on 12 V power; ❌ with car-USB power |
| **Low consume enabled on C1** | the wake from low consume is what arms the restore | ✅ (`UCAN_LOW_CONSUME_PINS`; a build with `DISABLE_LOW_CONSUME` never restores) |
| Reset wire | **not** needed for DNA Memory (it only lowers the sleep current; BH just keeps running without it) | fitted anyway |
| **A monostable DNA selector that sends `0x256` on the BH bus** | its frames are the trigger for every press; with another selector type BH sees no `0x256` and does nothing (code comment cites such a car) | **check in S5:** sniff the BH bus at 125 kbit/s and look for `0x256` (every ≈ 250 ms) and `0x46C` |
| "DNA Memory" selected in SETUP + SAVE & EXIT | off by default | **leave off on the owner's car** |
| One drive first | right after installing nothing is memorized yet | first restore happens on the drive after the next sleep |

---

## 12. Risks and stop conditions
| Risk | Rule |
|---|---|
| Board with 64 KB flash | do not use it |
| Extra termination on a bus | each bus must read ≈ 60 Ω through the harness |
| H/L swapped | warning lights → unplug at once |
| 12 V on a UCAN / more than 3.6 V on the 3V3 rail / USB plugged into a board whose 3V3 plug is connected | never |
| Reset wire fitted while flashing slaves on the bench | C1 will hold them in reset — fit it after S2, or use `C1_BENCH_ONLY` |
| Parked drain | measure in H11; if it does not drop after the car sleeps, check the reset wire and the sleep LED |
| Immobilizer turned on later | it reacts to any diagnostic session on the RF hub; turn it off before MultiECUScan/AlfaOBD work |
| DYNO, 4WD disable, brake override | stationary/closed course only; the repo is "educational and research", not for public roads |
| Warranty/insurance/inspection | your responsibility |

## 13. Still open (only the hardware can answer)
1. Real flash size and any fixed CAN termination on **your** UCANs (H0, S1).
2. First boot of the prebuilt images and the `UCAN_LOW_CONSUME_PINS` sleep on real boards (S3, S4).
3. Sleep current of the three-UCAN build (H11).
4. Standby wire on your boards: transceiver pin 8 ↔ chip pin 2 continuity (H4) and ≈ 0 V awake / ≈ 3.3 V asleep (S4); bus recessive while asleep (S4 voltmeter check).

## Sources (all in or linked from this fork)
`README.md`, `LICENSE.MD`, `manuals/Baccable_manual_*.pdf` (v4.9), `hardware/newBaccableDedicatedPcb/*`, `hardware/system_interconnection/*`, `hardware/canable/*` (MKS schematics, STM32F072 datasheet), `hardware/box/*`, `firmware/ledsStripController/{Core,Makefile,MAKEFILE.md,*.ld,baccable.ioc,.cproject}`, `.github/workflows/*`, `tools/*.xlsx` · GiUCAN https://github.com/anegrin/GiUCAN · canable-fw https://github.com/normaldotcom/canable-fw · PIDs https://github.com/danardi78/Alfaromeo-Giulia-Stelvio-PIDs · upstream issue #34 (author on power and three boards).
