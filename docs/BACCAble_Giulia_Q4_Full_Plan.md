# DIY BACCAble — Full Plan, Build Steps and Firmware (v4)

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
| Sleep ("low consume") | C1 **PA4** holds C2/BH in reset; C1 **PA5** puts the C2/BH transceivers in standby; C1 keeps listening and wakes them on CAN activity | C1 **DO pad (PA13)** → **RES pads** of C2 and BH, firmware flag `UCAN_LOW_CONSUME_PINS` (§5) | ✅ chips; ⚠️ slave transceivers are not put in standby (§5) |
| Power | 12 V from OBD pin 16 → fuse → buck (4.5–35 V in); ≈ 15 mA asleep, < 30 mA running | 12 V from OBD pin 16 → fuse → **automotive 12 → 5 V buck** → USB-C of each UCAN (§4) | ✅ (consumption to be measured) |
| Programming button | one button pulling BOOT0 of all three chips | one push button **B0 ↔ 3V3** per UCAN | ✅ |
| USB port per chip (flash, sniffer, ELM327, pen drive) | J10/J20/J30 USB-C | each UCAN's own USB-C | ✅ |
| Status LEDs | green power + red (PA0) + white/blue/yellow (PA1) per chip | UCAN power LED + its two LEDs on PA0/PA1 (`UCAN_BOARD_LED_INVERSION` is the build default) | ✅ |
| No CAN termination | none on the PCB | UCAN termination header left **open**; measure (§6) | ✅ |
| OBD plug through the SGW bypass | the PCB is the OBD plug | OBD male breakout harness into the bypass port | ✅ |
| LED-strip output (PA11) | OBD pin 8 | **not built** (mission) | ➖ excluded |
| Aftermarket exhaust-valve remote outputs (C1 PA8 = Q10, PA7 = Q11) | transistors on the PCB, OBD pins 1/2/15 | optional: two transistors on fine wires to the C1 chip (§10) — only if you fit aftermarket valves with a radio remote | ⚪ optional |
| Pedal-booster serial (C1 USART1 on PB6) | cable to "schizzaForte" | optional fine-wire on C1 pin 42 (§10); the manual says the pedal booster is "under development, do not activate" | ⚪ optional |
| STS inputs, GSM footprint | on the PCB | **not used by the firmware** (no code reads them) | — nothing to copy |

**What is not the same (honestly):** loose boards in our own box instead of the moulded OBD plug; slave transceivers not put in standby during sleep (slightly higher sleep current than the author's ≈ 15 mA); one boot button per board instead of one shared button.

---

## 2. Architecture and wiring

### 2.1 Buses (manual §1.2, DLC pinout image)
| Board | Role | OBD H / L | Bus speed | Main functions |
|---|---|---|---|---|
| **C1** | master/gateway | **6 / 14** | 500 kbit/s | dashboard menu and settings, Start&Stop, immobilizer, shift, 4WD disabler, ACC/HAS pads, windows, seat-belt, read faults (BODY/ECM), ELM327, sniffer, sleep control |
| **C2** | slave | **12 / 13** | 500 kbit/s | ESC/TC, DYNO, front-brake override, front park mute, ABS faults |
| **BH** | slave | **3 / 11** | 125 kbit/s | text on the cluster, odometer blink, park mirror, DNA Memory |

GND = OBD 4 and 5, +12 V = OBD 16. [Repo]

![DLC pinout](images/dlc_pinout.png)

The picture is drawn from the car side (pins 1–8 bottom row, 9–16 top row): trust the numbers on your plug.

### 2.2 UCAN pads (read from the silkscreen in the repo's photos)
From `hardware/system_interconnection/ShowParamsOnDashboardConnections.png` and GiUCAN's diagrams, USB-C at the bottom:
- **CAN terminal:** CAN_L · CAN_H · GND.
- **Right pad column, from the USB end up:** **CK** (PA14, serial) · **DO** (PA13) · **RES** (reset) · **G** · **B0** (BOOT0) · **3V3**.
- **Left pad column, from the USB end up:** RX · TX · G · 3V3 (not used).
- A **2-pin termination header** beside the CAN terminal (keep it open).
Check these against your own boards before soldering. [Repo][GiUCAN]

### 2.3 Complete wiring (the author's PCB rebuilt)
```
                         OBD male plug (into the SGW bypass port)
  pin 6 ─ C1.CAN_H    pin 12 ─ C2.CAN_H    pin 3  ─ BH.CAN_H
  pin 14 ─ C1.CAN_L   pin 13 ─ C2.CAN_L    pin 11 ─ BH.CAN_L
  pins 4/5 (GND) ─ C1.GND, C2.GND, BH.GND (CAN terminals) and buck GND
  pin 16 (+12 V) ─ fuse 1 A ─ buck IN+ ; buck OUT 5 V ─ 3 × USB-C power leads ─ C1, C2, BH

  Serial (author's "Serial" net):     C1.CK ──── C2.CK ──── BH.CK      (one wire)
  Sleep reset (author's PA4 line):    C1.DO ──┬─ C2.RES
                                              └─ BH.RES                (one wire)
  Boot buttons:                       B0 ↔ 3V3 push button on each board
```
No series resistors on the serial or reset wires (the author's PCB and diagrams use bare nets; the firmware drives both open-drain). Keep both wires short (≤ ~30 cm). [Repo][Infer]

---

## 3. Boards to use

- **FYSETC UCAN V1.0 ×3 + 1 spare.** It is one of the four boards the README lists as compatible ("important that the chip is an STM32F072"); the author ships cases for it (`hardware/box/dual_fysect_ucan`, `single_fysect_ucan`) and the firmware's LED default is for it. [Repo]
- **All three need 128 KB of flash**: C1 is 79,004 bytes [Built]; C2 and BH keep a 64 KB FAT area and their settings in flash up to `0x0801FFFF` (§11.4). The author's own chips are labelled C8T6 (64 KB on paper, see the datasheet in `hardware/canable/`) yet run these images with a 96 KB code region and settings at `0x0801F800`, so they behave as 128 KB; the UCAN's CB chip is 128 KB on paper. **Read the flash size of every board in STM32CubeProgrammer before flashing.** [Repo][GiUCAN]
- Other boards the README lists (MKS CANable, DykbRadio Nano, candleLight) work only with a 128 KB STM32F072; CANable-type boards need `-DDISABLE_UCAN_BOARD_LED_INVERSION` (their LEDs are active-low on PA0/PA1, see the MKS schematic in the repo). Not needed for this build. [Repo]

---

## 4. Power — same as the author: always-on 12 V with sleep

**Recommended (parity):** OBD pin 16 → **1 A fuse** → **12 V → 5 V automotive buck converter** (input rating well above 14 V, e.g. ≥ 30 V, for load-dump spikes; ≥ 1 A out; low no-load current because it is always on) → three USB-C power leads to C1, C2, BH. Buck ground to OBD 4/5. This is GiUCAN's OBD-powered layout extended to three boards; the author confirmed "12 V requires a DC-DC, 5 V can directly power a CANable" and that both work for the immobilizer. [Repo][GiUCAN][Author][Infer]

Why always-on matters for parity: with the boards kept powered and sleeping, everything the author's device remembers in RAM survives a parked car — **DNA Memory** (manual: "the stored style is lost if the BACCABLE is disconnected"), the **exhaust-flap remembered choice**, and — if you ever enable it — the immobilizer stays armed while the car sleeps. [Repo]

**Alternative (simpler, not full parity):** take 5 V from the car USB in the centre console or the port near the cigarette lighter (manual §1.7/§2.4: switched on when you get in and when the RF hub is woken). The boards then lose power when the car sleeps, so DNA Memory and the remembered exhaust choice do not work; everything else does. [Repo]

Rules: **never put 12 V on a UCAN**; all boards share one ground; use power-only USB-C leads (C2/BH show up as USB pen drives on a data connection, §11.4).

---

## 5. Sleep (low consume) on UCAN boards — our one firmware change

**Author's design** (`lowConsume.c`, schematic): C1 never sleeps; after **3.5 s without CAN frames** on its bus it pulls **PA4** low (open-drain) to hold C2 and BH in reset, drives **PA5** to put their transceivers in standby, pauses the serial line and lights its blue LED; when frames come back it releases both, restarts the serial line, re-sends every function setting to the slaves (≈ 3.5 s later) and arms DNA Memory. Sleep is blocked while a sniffer/ELM327/pen-drive USB session is active. [Repo]

**Problem on a UCAN:** PA4 and PA5 have no pads.
**Fix in this fork:** new compile flag **`UCAN_LOW_CONSUME_PINS`** in `Core/Inc/lowConsume.h` moves the reset line to **PA13 = the DO pad** (the pin GiUCAN uses for exactly this, wired to the other board's RES pad). Default builds are unchanged. Verified in the C1 image's disassembly: PA13 open-drain output. [Repo][GiUCAN][Built]
- PA13 is SWDIO: SWD debugging of C1 is no longer possible; USB-DFU flashing is unaffected. At C1 power-up and during C1 flashing PA13 floats high, so the slaves run. [Infer]
- **Slave transceivers:** on a UCAN each transceiver's standby pin is driven by its own chip (PC13 per GiUCAN), so C1 cannot reach it. While a slave is held in reset its pins are undriven — the same state GiUCAN's BH board is in during its standby on real cars — so the bus is left alone, but the transceiver may keep drawing a few mA. Measure the sleep current (§7 H11). [GiUCAN][Infer]
- **Bench gotcha:** with no car, C1 sees no CAN frames and holds C2/BH in reset after 3.5 s. Flash and test the slaves **before** fitting the reset wire, or power C1 off, or use the `C1_BENCH_ONLY` image (§8).

---

## 6. Termination

The car buses are already terminated, so no board may add a terminator. The repo never says to desolder anything: the author's diagrams say "TERMINATION NOT INSERTED", his PCB has no terminator, and the UCAN pictures show the termination header **without a jumper**. Whether a UCAN also has fixed resistors across CAN H/L is **not documented in the repo** (that claim came from outside research). So: **measure** (H0); if a fixed value is present, removing it is consistent with the author's PCB — practise on the spare. Through the full harness every bus must read **≈ 60 Ω**. [Repo][Diagram]

---

## 7. Hardware build steps (no firmware yet)

**Parts:** 3 UCAN + 1 spare (owned); OBD2 male plug with all 16 pins wired (needs 3, 4, 5, 6, 11, 12, 13, 14, 16); 12 → 5 V automotive buck (§4) + inline fuse holder + 1 A fuse; 3 power-only USB-C leads (or USB-C plugs wired to the buck); 22 AWG twisted pairs (~3 m) and 24–26 AWG wire for serial/reset; 2.54 mm pin headers; 4 small momentary push buttons (boot); 1 short USB-C **data** cable for flashing; project box, standoffs, cable glands, heat-shrink, ferrules. Tools: multimeter, fine-tip iron, flux, wick, tweezers, loupe; a 5 V USB supply for the bench.

| Step | Action | Pass when |
|---|---|---|
| **H0** | Inspect every board: chip marking **STM32F072CB**; label C1, C2, BH, SPARE. Unpowered, termination header open: measure CAN_H↔CAN_L. | open circuit (or note the value for H1) |
| **H1** | Termination per §6 (practise on the spare). Keep the header open. | CAN_H↔CAN_L open on each board |
| **H2** | Flash check comes in S1 (needs USB). Solder headers to **CK, DO, RES, B0, 3V3, G** on each board. Fit a push button across **B0–3V3** on each board, reachable from outside the box. | pads clean, no bridges |
| **H3** | **Serial wire:** C1.CK ↔ C2.CK ↔ BH.CK. | continuity CK-CK-CK, no short to G/3V3 |
| **H4** | **Reset wire:** C1.DO ↔ C2.RES and C1.DO ↔ BH.RES. *(Leave unplugged until the slaves are flashed — §5 bench gotcha.)* | continuity, no short |
| **H5** | **CAN harness** to each terminal (P1: 1 = CAN_L, 2 = CAN_H, 3 = GND): C1 → 6/14, C2 → 12/13, BH → 3/11; terminal GND → OBD 4/5. Twist pairs, mark every H wire. | H/L not swapped (swapped = warning lights, manual §1.5) |
| **H6** | **Power harness:** OBD 16 → fuse → buck → three power-only USB-C leads; buck GND → OBD 4/5. Bench-check the buck output = 5 V before connecting boards. | 5.0 V ± 0.25 V, no load drop |
| **H7** | **Bench power test:** each board alone on 5 V: power LED on, 3V3 pad ≈ 3.3 V. Then all three on the harness. | no short, no hot parts |
| **H8** | **Bypass cable check** (car asleep ≥ 10 min, boards unplugged): 6↔14, 12↔13 ≈ 60 Ω; 3↔11 low value; 16↔4 ≈ 12 V; 4/5↔chassis continuity. | all present (owner already confirmed the buses) |
| **H9** | **Box:** standoffs, glands, strain relief; USB-C ports and boot buttons reachable; away from pedals, steering column, knee-airbag path, heat and HVAC flaps. Label boards at both ends. | nothing loose |
| **H10** | **In-car, unpowered:** plug into the bypass port, re-measure every bus ≈ 60 Ω through the harness, connect power last. Do not power the boards on the car with unknown firmware. | ≈ 60 Ω each |
| **H11** | After the firmware is in (S5): measure the 12 V current at the fuse with the car awake and ≈ 1 min after it sleeps (author's device: ≈ 15 mA asleep, < 30 mA running). | sleep current settles; boards wake when you unlock |

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

Checked with the preprocessor: `LOW_CONSUME` defined; `IMMOBILIZER_ENABLED`, `SMART_DISABLE_START_STOP`, `IS_DIESEL` undefined. The defaults apply only to a board whose settings flash page is blank, so **erase the whole chip** when flashing a board that ran BACCAble before. The fork's "Build Beta Version" GitHub workflow accepts the same flags in its `CFLAGS` input. [Repo][Built]

**Flash a UCAN** (documented in the repo for loose boards): hold the **B0** button while plugging the **data** USB-C cable (the chip appears as `0483:df11`), then either
```bash
sudo dfu-util -d 0483:df11 -c 1 -i 0 -a 0 -s 0x08000000:leave -D C1.bin
```
(the Makefile's own `flash` target, `MAKEFILE.md`) or STM32CubeProgrammer → USB → "Erasing & Programming" with the `.elf` (GiUCAN's docs). On Windows install the WinUSB driver with Zadig if CubeProgrammer/DfuSe is not installed (manual §1.11.1). Weak LED or no detection: shorter cable, another port, a slow USB hub, flip the USB-C plug (manual). The firmware has no software jump to the bootloader, so the button is the only way in. [Repo][GiUCAN]

---

## 9. Bring-up steps

| Step | Action | Pass when |
|---|---|---|
| **S1** | On the **spare**: read device ID and **flash size = 128 KB** in CubeProgrammer, flash `BH`, unplug, replug. | it runs (blue LED activity) and appears as a USB drive "BACCABLE BH" with `Version.txt` on a data cable |
| **S2** | Read and flash all boards: `C1`→C1 board, `C2`→C2, `BH`→BH (full chip erase). Reset wire **not** fitted yet. | each starts; C2/BH show their USB drive label |
| **S3** | **Bench serial test:** flash `C1_BENCH_ONLY` on C1, fit the CK wire, power all three. | after ~3 s the blue LEDs of C2 and BH pulse about once a second (C1 polling them) |
| **S4** | **Bench sleep test:** flash the real `C1`, fit the reset wire, power all three with no car. | ~4 s after power-up the status LEDs of C2 and BH stop (held in reset; their power LEDs stay on) and C1's blue LED flashes once: the reset wire works. **Bus-safety check:** while they are held in reset, measure DC volts between CAN_H and CAN_L on each slave's terminal (nothing else connected): **≈ 0 V = recessive, safe**; ≈ 1.5–3 V = the slave would hold its bus dominant — do not install, report it (§5) |
| **S5** | **Car, silent sniff (optional but recommended):** flash `SNIFFER_ActAsCanable` on the spare and use SavvyCAN in silent mode (`M1`) on each bus (500 k C1/C2, 125 k BH); the IDs in §11.5 should appear — on the BH bus look specifically for `0x256` and `0x46C`, which DNA Memory needs (§11.12). Then install the three boards (H10) and power them. | no warning lights; on unlock the boards wake |
| **S6** | **First start:** engine running, cruise control and ACC off → hold **RES** (or DISTANCE) ~2 s → version `BACCABLE ucan-…` on the cluster. With our defaults there is **no** double blue blink and no cluster flash at power-up (those mean "immobilizer active"). Open **SETUP MENU** (§11.7): check **Diesel Params = O** (gasoline), **My23 IPC = O**, Start&Stop = O. | menu works |
| **S7** | Enable functions **one at a time**, SAVE & EXIT, ignition cycle, check for faults after each: dashboard parameters → shift → seat-belt/odometer → windows, park mirror, park mute → proxy-alignment features (ACC pad, HAS pad, race mask) → DNA Memory (needs §4 always-on power). | no new faults |
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
Enable ELM327 in SETUP, connect a data USB cable to **C1**, then the OBD side. It answers as "ELM327 v1.4" for MultiECUScan/AlfaOBD and forwards requests for ECUs on the other buses over the serial wire to **C2/BH** — this is why all three boards matter for proxy alignment. While a host is connected the dashboard buttons are ignored; the mode switches itself off after 120 s without commands. With always-on power, unplug C1's power lead while the laptop powers it (never two 5 V sources on one board). [Repo][Infer]

### 11.10 Functions that need more than the boards
ESC/TC and the race screen need race mode enabled by **proxy alignment** (manual §2.19, which also explains keeping the pedal maps); ACC pad needs ACC hardware + proxy; HAS pad needs MY20+ hardware + proxy; park mirror needs mirror encoders; DNA Memory needs a monostable DNA selector on BH **and** always-on power; DPF/regen alert is diesel-only; Remote start and Pedal booster are "do not activate". [Repo]

### 11.11 Things to know in the code
- Gasoline parameter "OVER RPM: sec" has reply ID `0xDA18F110` instead of `0x18DAF110` (probable typo, that page may not update) — left unchanged.
- Dormant "pump force" test code (ECM security access) exists but its only start line is commented out, so it never runs; re-check if you merge newer upstream code.
- `user_config.h.sample` calls READ FAULTS experimental while the manual documents it.
- Licence (`LICENSE.MD`): use, modify and share with attribution to Gaucholivido - Tr3ma; **commercial resale prohibited**. [Repo]

---

### 11.12 DNA Memory — how it works and what it needs (`functions_C1baccable.c`, `functions_BHbaccable.c`, `lowConsume.c`, manual §2.34)
**How it works**
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
| "DNA Memory" selected in SETUP + SAVE & EXIT | off by default | enable in S7 |
| One drive first | right after installing nothing is memorized yet | first restore happens on the drive after the next sleep |

---

## 12. Risks and stop conditions
| Risk | Rule |
|---|---|
| Board with 64 KB flash | do not use it |
| Extra termination on a bus | each bus must read ≈ 60 Ω through the harness |
| H/L swapped | warning lights → unplug at once |
| 12 V on a UCAN / two 5 V sources on one board | never |
| Reset wire fitted while flashing slaves on the bench | C1 will hold them in reset — fit it after S2, or use `C1_BENCH_ONLY` |
| Parked drain with always-on power | measure in H11; if it does not drop after the car sleeps, check the reset wire and the sleep LED |
| Immobilizer turned on later | it reacts to any diagnostic session on the RF hub; turn it off before MultiECUScan/AlfaOBD work |
| DYNO, 4WD disable, brake override | stationary/closed course only; the repo is "educational and research", not for public roads |
| Warranty/insurance/inspection | your responsibility |

## 13. Still open (only the hardware can answer)
1. Real flash size and any fixed CAN termination on **your** UCANs (H0, S1).
2. First boot of the prebuilt images and the `UCAN_LOW_CONSUME_PINS` sleep on real boards (S3, S4).
3. Sleep current of the three-UCAN build (H11).
4. Behaviour of the slave transceivers while their chips are held in reset: expected recessive/harmless as in GiUCAN's standby — **checked with a voltmeter in S4** before installing.

## Sources (all in or linked from this fork)
`README.md`, `LICENSE.MD`, `manuals/Baccable_manual_*.pdf` (v4.9), `hardware/newBaccableDedicatedPcb/*`, `hardware/system_interconnection/*`, `hardware/canable/*` (MKS schematics, STM32F072 datasheet), `hardware/box/*`, `firmware/ledsStripController/{Core,Makefile,MAKEFILE.md,*.ld,baccable.ioc,.cproject}`, `.github/workflows/*`, `tools/*.xlsx` · GiUCAN https://github.com/anegrin/GiUCAN · canable-fw https://github.com/normaldotcom/canable-fw · PIDs https://github.com/danardi78/Alfaromeo-Giulia-Stelvio-PIDs · upstream issue #34 (author on power and three boards).
