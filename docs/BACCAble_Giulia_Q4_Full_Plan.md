# BACCAble DIY — Research, Hardware Plan & Step-by-Step Build (v3)

**Car:** 2022 Alfa Romeo Giulia Sprint Q4 · 2.0 petrol · MY22 cluster
**Goal:** BACCAble function set on loose FYSETC UCAN boards (one per CAN bus)
**SGW:** bypass cable already owned · **Case:** own box · **Shopping:** buy on eBay/Amazon
**Status:** research + hardware plan + tested firmware build. **Nothing is flashed or installed yet; the prebuilt images are untested on hardware.**
**v3 changes (this version):** firmware read through and built (§8c–8g, build section), fresh-board defaults (§8e) with **immobilizer and Start&Stop disabler OFF by default**, flash/USB behaviour of each board (§8f), CAN IDs per bus (§8g), programming/reset buttons and LEDs (§8b), build script and prebuilt images in `firmware/ucan_prebuilt/`. **v2 changes:** added the cross-check against the repos linked in the BACCAble README (canable-fw, GiUCAN, Alfaromeo-Giulia-Stelvio-PIDs), the repo's wiring diagrams and the Giulia DLC pinout. The build is now **2 boards minimum (C1 + BH), a 3rd (C2) optional**. Out of scope by request: macOS-specific flashing, idle-current measurement, 4WD-disabler logic analysis.

Evidence tags: **[Repo]** stated by BACCAble repo/manual v4.9 · **[GiUCAN]** from github.com/anegrin/GiUCAN · **[Schem]** read from a schematic · **[Diagram]** read from a diagram image · **[Infer]** my inference, verify · **[Unv]** not verified.

---

## 1. Summary

1. **Right repo:** `gaucho1978/BACCAble` (live; manual v4.9). `tr3ma-crew/BACCAble-firmware` is a stale firmware-only snapshot. [Repo]
2. **UCAN is a supported board.** The author ships cases `hardware/box/dual_fysect_ucan` and `single_fysect_ucan`, `UCAN_BOARD_LED_INVERSION` is on by default, and the author's own diagram (`ShowParamsOnDashboardConnections.png`) shows two UCANs as master (C1) + slave (BH) with the note that any STM32F072 board is equivalent. [Repo][Diagram]
3. **GiUCAN proves the UCAN approach on real cars.** It is a cut-down BACCAble written *only* for FYSETC UCAN (C1 + BH), derived from canable-fw. [GiUCAN]
4. **Minimum build = 2 boards:** C1 (master, OBD 6/14) + BH (slave, OBD 3/11), joined by one wire between their **CK pads**. **C2 (OBD 12/13) is only needed for ESC/TC, DYNO and front-brake override.** Everything else, including the 4WD disabler (runs on C1), works with two boards. [Repo][Diagram]
5. **Use FYSETC UCAN V1.0 (STM32F072CBT6, 128 KB flash).** GiUCAN's linker script for it is 64 K flash + 64 K "EEPROM" at 0x08010000 (= 128 KB). The BACCAble C1 image is 78.6 KB (built here), so a true 64 KB F072C8 will not fit; C2 and BH also use flash up to `0x0801FFFF` (§8f). The author's own PCB uses F072C8T6 chips and runs the same images, so those parts behave as 128 KB — still read the flash size in CubeProgrammer before flashing. [GiUCAN][Repo][Schem]
6. **Power each board over USB-C, 5 V.** UCAN has no 12 V input. Two supported sources, both confirmed by the author for the immobilizer: car USB 5 V (powers a CANable directly) or a 12 V→5 V DC-DC feeding the USB-C inputs (the author's own board runs on both). See §5. [Repo: issue #34][GiUCAN][Schem]
7. **Settings for your car:** GASOLINE in the setup menu, "My23 IPC" off. Both are runtime menu options. [Repo]
8. **Termination:** the car buses are already terminated, so the module must add none. On UCAN, R1+R2 (59 Ω + 59 Ω) are hard-wired across CAN H/L, so measure and, per the schematic, remove them. GiUCAN's docs don't mention this; ask the Telegram group. [Schem][Unv]
9. **Immobilizer and Start&Stop disabler are OFF by default in our build** (owner's choice); both can still be switched on later in the SETUP menu. The immobilizer needs power that wakes with the RF hub (car USB 5 V or 12 V OBD); with it off, any 5 V source that is up while driving works. [Repo]

---

## 2. What the linked repos are

| Repo | Role | Use in this project |
|---|---|---|
| `normaldotcom/canable-fw` | Original SLCAN firmware (STM32F042, ~3.7k lines): CAN init, USB CDC, `O/C/S/M/T` commands. No car logic. | Ancestor of BACCAble and GiUCAN. Only the sniffer. |
| `anegrin/GiUCAN` | Minimal BACCAble for **FYSETC UCAN only**: C1 + BH, Start&Stop disabling, DPF warnings, dashboard values. Docs, wiring diagrams, `build.sh`, settings via `settings.ini`. | **Reference for UCAN wiring, power and sleep; bench-test firmware.** |
| `danardi78/Alfaromeo-Giulia-Stelvio-PIDs` | UDS parameter list (CarScanner `.csp`/`.csv`) tested on a 2.2 diesel MY2016. Columns: header, PID, formula, unit, min/max. | Same fields as BACCAble's parameter array (reqId, reqData, replyOffset, scale…). Many entries are diesel-only. |

PID notes from that repo: BACCAble uses the special unused header **`DABAF1`**. **Do not read tire-pressure PIDs with header `DAC7F1` while the immobilizer function is active** — it engages the immobilizer and stops the car. [Repo: PIDs README]

---

## 3. Architecture

Three chips, one per CAN bus; one firmware build per chip (**C1, C2, BH**) plus ActAsCanable (plain SLCAN sniffer). [Repo]

| Chip | Role | OBD-II pins | Speed | Functions |
|---|---|---|---|---|
| **C1** | Master / gateway | **6 (H) / 14 (L)** | 500 kbit/s | Start&Stop disabler, immobilizer, shift lights, dashboard menu, ACC/HAS pads, 4WD disabler, ELM327, sniffer |
| **BH** | Slave | **3 (H) / 11 (L)** | **125 kbit/s** | dashboard parameters, odometer blink |
| **C2** *(optional)* | Slave | **12 (H) / 13 (L)** | 500 kbit/s | ESC/TC, DYNO, front-brake override |

GND = OBD pins 4/5, +12 V = pin 16. [Repo]

### 3.1 OBD (DLC) pinout — Giulia/Stelvio

![DLC pinout](images/dlc_pinout.png)

| Bus | High (+) | Low (−) |
|---|---|---|
| CAN-C1 | pin 6 | pin 14 |
| CAN-C2 | pin 12 | pin 13 |
| CAN-BH | pin 3 | pin 11 |

Matches the manual, GiUCAN and the BACCAble diagram. [Diagram] Pins 1–8 are the bottom row, 9–16 the top row in the picture (view from the car side) — **trust the numbers printed on your plug, not the picture's left-to-right order.**

### 3.2 Two-board wiring (author's diagram)

`hardware/system_interconnection/ShowParamsOnDashboardConnections.png` [Diagram]:
- UCAN #1 = **BACCAble master** → CAN to OBD **6(H)/14(L)** (C1).
- UCAN #2 = **BACCAble slave** → CAN to OBD **3(H)/11(L)** (BH).
- **Half-duplex single-wire serial between the boards on the SWCLK pad (the board's "CK" pad = PA14, USART2).**
- Each board's USB goes to a 5 V source ("USB hub").
- Note on the diagram: UCAN, CANable, DykbRadio Nano or candleLight are equivalent *if they mount an STM32F072*.

### 3.3 Adding C2 (three boards) [Repo: author, issue #34]
The author confirmed (BACCAble issue #34, 7 Dec 2025) that the two-UCAN diagram "was just an example" and that **three CANable/UCAN boards communicate through the same single wire, a half-duplex serial line**, one master and two slaves.

- C2 CAN pair → OBD **12 (H) / 13 (L)**, grounds to OBD 4/5.
- C2 **CK pad** → the **same single wire** as C1 and BH (one shared half-duplex serial net, as the author confirmed). Common GND.
- Third power-only USB-C cable from the same 5 V source.
- Flash it with the **C2** image.
- Prerequisite: your bypass cable must pass pins 12/13 (step H7).

```
   OBD 6/14 → C1 ─┐
   OBD 3/11 → BH ─┼── one shared wire (CK/SWCLK pads) + common GND
   OBD 12/13 → C2 ─┘   (optional)
   each board: USB-C 5 V power only
```

### 3.4 Wiring variants in the repos

| Variant | Source | What it shows |
|---|---|---|
| **A. USB-powered, 2 UCAN** | `ShowParamsOnDashboardConnections.png`; GiUCAN `docs/images/schema_usb.png` | CK↔CK wire + CAN pairs + USB 5 V. **Recommended for you.** |
| **B. OBD-powered, 2 UCAN, with sleep** | GiUCAN `docs/images/schema_obd2.png`, docs | As A, plus C1 **DO pad → BH RES pad**, plus a 12 V→5 V DC-DC from OBD pin 16 and 4/5 feeding USB-C plugs. C1 holds BH in reset and silences the transceivers when the car sleeps (≈7 mA at 12 V, per the author). |
| **C. Old single-CANable design** | `hardware/system_interconnection/SCHEMA_DI_INTERCONNESSIONE.png` | One CANable, 12 V→5 V regulator into the board's `+5V` terminal, an LED-strip output (not used in this plan), and a **hardware Start&Stop bypass panel** (520 Ω / 2 kΩ / 1.5 kΩ / 7 kΩ + switch) on the car's 12-pin switch-panel connector, with a 1.5 kΩ resistor from PA14. Notes: ECU impedance before pin 5 = 910 Ω, pin 9 = 99 Ω; 470 Ω instead of 1.5 kΩ disables the parking acoustic signal. |

**Variant C is the legacy design — do not build it.** Current firmware disables Start&Stop by CAN message (`SMART_DISABLE_START_STOP`), and **PA14 is now the inter-board serial pin, so never hang a resistor on it.** The "+12 V" in that drawing comes from the switch-panel connector, not OBD pin 16 (switched/always-on is not stated). [Diagram][Infer]

---

## 4. Findings that shape the build

### 4.1 Flash size
| Evidence | Finding |
|---|---|
| Release ELFs (V.3.8.2, measured) | C1 = 73.6 KB, C2 = 35.8 KB, BH = 34.2 KB, ActAsCanable = 24.9 KB (our current builds: C1 78.6 KB, C2 37.5 KB, BH 36.8 KB) |
| `STM32F072C8TX_FLASH_C1.ld` | C1 code region 96 KB |
| `globalVariables.h` | settings in last pages `0x0801E800–0x0801FFFF` (top of a 128 KB bank) |
| Makefile | `-DSTM32F072xB` (128 KB variant) |
| GiUCAN `STM32F072CBTX_FLASH.ld` | UCAN's CB part: 64K + 64K |

Treat any "C8T6"-labelled board as unproven. [Repo][GiUCAN]

### 4.2 Candidate modules
| Module | MCU | Verdict |
|---|---|---|
| **FYSETC UCAN V1.0** | STM32F072**CB**T6, SN65HVD230 | ✅ buy (used by GiUCAN and the author's cases) |
| MKS CANable V1.0 | STM32F072C8T6 | ⚠️ only if chip proven 128 KB |
| MKS CANable V2.0 / candleLightFD | STM32G4 / G0 | ❌ wrong family |
| DykbRadio Nano | unverified | ❓ |

### 4.3 UCAN V1.0 facts
- P1 screw terminal: **1 = CAN_L, 2 = CAN_H, 3 = GND** [Schem]. P2 pads include **CK (PA14)**, **DO (PA13/SWDIO)**, **RES (reset)**, BOOT0, 3V3, GND — verify against the silkscreen. [Schem][GiUCAN]
- DFU: short **BOOT0 to 3V3** while powering up (GiUCAN: "BO and 3V3"). [GiUCAN]
- Power only via USB-C. R1+R2 = 59 Ω + 59 Ω hard-wired across CAN H/L; JP1 adds a further 120 Ω. [Schem]

### 4.4 Clock
BACCAble builds with the **internal 48 MHz oscillator** (`INTERNAL_OSCILLATOR`, HSI48). UCAN's 8 MHz crystal is not needed; GiUCAN uses it by default but its BACCAble flavor builds with `DISABLE_EXTERNAL_OSCILLATOR`. Stock BACCAble images should run on UCAN as-is. [Repo][GiUCAN]

### 4.5 Sleep / low-consumption pins
| | Reset line to slaves | CAN transceiver silent |
|---|---|---|
| BACCAble `lowConsume.h` (dedicated PCB) | **PA4** | **PA5** |
| GiUCAN on UCAN (defaults) | **PA13 (DO pad)** → BH RES | **PC13** |

On loose UCANs the BACCAble sleep code points at pads that aren't wired. Note (§8d.B): a build with sleep disabled also disables **DNA Memory**. Choices: **(1)** build C1 with `DISABLE_LOW_CONSUME` (no sleep; use switched car USB so there is no drain); **(2)** optional firmware change to move the two pins to PA13/PC13 and wire DO→RES like GiUCAN (**untested**). [Repo][GiUCAN][Infer]

### 4.6 SGW
Closed (you own a bypass). Remaining check: that **your** cable passes all buses you use — C1 and BH always, C2 if you build it (step H7). [Repo manual §1.8]

---

## 5. Power

| | Car USB 5 V (recommended) | 12 V OBD + DC-DC (variants B/C) |
|---|---|---|
| Works without immobilizer | yes | yes |
| Works with immobilizer | yes (wakes with RF hub) | yes |
| Parked drain | none (switched) | continuous unless boards sleep |
| Parts | passive splitter, power-only USB-C cables | DC-DC 12→5 V, fuse, USB-C leads |

- Manual §1.7: the USB hub in the console storage compartment (next to the handbrake) is live when you enter the car and when someone wakes the RF hub. Tap method (opening the hub PCB) is documented but not recommended here. The manual also mentions the USB port in the central area near the cigarette lighter. [Repo]
- **Never feed 12 V to a UCAN.** Every board powered from the same source; boards share ground and the serial wire. [Schem]
- Author (issue #34): "12 V requires a DC-DC; 5 V can directly power a CANable. Both solutions work fine for the immobilizer." Open question from that thread, **not answered by the author**: whether the *armrest-front* USB port is powered when the RF hub wakes. The manual names the console-storage hub (next to the handbrake) and the USB port near the cigarette lighter — use one of those, and verify it with a multimeter before relying on it. [Repo][Unv]
- The manual doesn't require USB power for loose boards; this is GiUCAN's and the author's diagram's approach. [Repo][GiUCAN]

---

## 6. Shopping list

### 6.1 Core
| # | Search | Qty | Check |
|---|---|---|---|
| 1 | "FYSETC UCAN USB to CAN adapter STM32F072" | **2 for the minimum build, 3 with C2, +1 spare** (you already bought them) | Photos show "UCAN V1.0", USB-C, green 3-pin terminal; MCU must read **STM32F072CBT6** |
| 2 | "OBD2 16 pin male plug to open end cable" / breakout | 1 | all pins wired (needs 3, 4, 5, 6, 11, 14, 16; add 12, 13 for C2) |
| 3 | "Twisted pair cable 22AWG" | ~3 m | |
| 4 | "USB-C charge-only cable" or data-blocker | 2–3 | power-only: **C2 and BH enumerate as a USB pen drive** (§8f), so the car's head unit must never see them [Repo] |
| 5 | "USB 1 to 3 splitter power only" (passive) | 1 | |
| 6 | 2.54 mm pin headers + jumper caps | 1 / 5 | CK, GND, BOOT0 pads; DFU jumper |
| 7 | Dupont wires, 24 AWG silicone wire, ferrules | 1 each | |
| 8 | ABS project box + cable glands + standoffs | 1 | own case; measure the boards first |
| 9 | Heat-shrink, Kapton tape, cable ties | | |

### 6.2 Tools
Multimeter (continuity, 10 A); temperature-controlled iron + flux + wick + tweezers + loupe (for R1/R2); 120 Ω resistors ×4 (bench CAN test); 5 V 2 A USB supply; 2 short USB-C data cables for DFU.

### 6.3 Optional
12 V→5 V DC-DC + fuse tap + 1–2 A fuse (variant B only).

### 6.4 Do not buy
MKS CANable V2.0, candleLightFD, DykbRadio Nano (unverified), any board without a readable MCU marking, a desktop powered USB hub, 3D-printed case files.

---

## 7. Build — Phase H (hardware, no firmware)

**H0. Receive and inspect.** Read each MCU marking (**STM32F072CBT6**). Label C1 / BH / (C2) / SPARE. Read-only DFU check: BOOT0↔3V3, plug in USB-C, STM32CubeProgrammer → USB → Connect, read device ID and **flash size (expect 128 KB)**; do not erase/write. 64 KB → return it. Bare board CAN_H↔CAN_L ≈ **118 Ω**.

**H1. Remove termination.** Practise on the SPARE: find R1/R2 on "UCAN V1.0 Component Position.pdf" (FYSETC/UCAN `Hardware/`), flux, lift each resistor, clean. Verify H↔L is open; leave JP1 open; re-check DFU still works. Ask `t.me/baccable` whether UCAN users do this. [Schem][Unv]

**H2. Serial tap.** Solder a pin on each board's **CK pad (PA14)** and a GND pin. One short harness (≤ ~30 cm): C1.CK ↔ BH.CK (↔ C2.CK), plus common GND. **No series resistor** (the repo diagram shows a bare wire). Check no shorts.

**H3. CAN harness.**
| Board | OBD H → P1.2 | OBD L → P1.1 | GND |
|---|---|---|---|
| C1 | 6 | 14 | OBD 4/5 |
| BH | 3 | 11 | OBD 4/5 |
| C2 (opt.) | 12 | 13 | OBD 4/5 |

Twist each pair, keep short, tape-mark H wires. H/L swapped = warning lights at power-up (manual §1.5).

**H4. Power.** Car USB-A → passive splitter → power-only USB-C cables → boards. Never 12 V into a UCAN.

**H5. Bench test A — power.** Each board alone from a 5 V supply: 3V3 LED on. Then all together on the shared harness: no short.

**H6. Bench test B — CAN wiring (optional).** Two modules H↔H, L↔L with a 120 Ω resistor at each end → ≈ 60 Ω; with your resistors removed the pair alone must read open.

**H7. Verify the SGW bypass cable passively (boards disconnected).** Car off, ≥ 10 min asleep:
| Check | Expected |
|---|---|
| Pin 4/5 ↔ chassis | continuity |
| Pin 6 ↔ 14 (C1) | ≈ 60 Ω |
| Pin 3 ↔ 11 (BH) | low value (exact value unverified) |
| Pin 12 ↔ 13 (C2, only if building C2) | ≈ 60 Ω |
**Status (user confirmed): the owner's bypass cable passes all buses.** Keep the passive test as a wiring sanity check.
Pin 16 ↔ 4 ≈ 12 V is not required for USB-powered builds.

**H8. Box.** Mount on standoffs, strain-relief with glands, keep USB-C, terminals and pads reachable. Away from pedals, steering column, knee-airbag path, heat and HVAC flaps. Label boards at both ends.

**H9. Pre-install checklist**
- [ ] Boards read STM32F072CBT6, 128 KB
- [ ] R1/R2 removed on installed boards
- [ ] CK + GND harness verified
- [ ] Bypass cable passes all buses (confirmed by owner)
- [ ] BOOT0 (and optional RES) push buttons fitted, USB-C ports reachable
- [ ] Car USB 5 V present when doors unlock/key near, absent when car sleeps

**H10. In-car install.** Car off; OBD harness into the bypass port first with boards **unpowered**; re-measure each pair through the harness ≈ 60 Ω; connect power last. Do **not** power boards on the car with unknown firmware.

---

## 8. Build — Phase S (software)

| Step | Action | Gate |
|---|---|---|
| **S0** | Install STM32CubeProgrammer | hardware gate passed |
| **S1** | Flash **ActAsCanable** (or GiUCAN SLCAN) on the SPARE; prove DFU flashing | spare works |
| **S2** | Sniff in silent mode (`M1`) on the car: C1 at 500 kbit/s, BH at 125 kbit/s (C2 at 500 kbit/s) | traffic on every bus |
| **S3 (optional)** | Bench-prove the wiring with **GiUCAN C1CAN + BHCAN** (build with `build.sh`, flash from `dist/`): note GiUCAN disables Start&Stop by default after ~20 s — add `#define DISABLE_SNS_AUTO_OFF` to its `inc/user_config.h` (and build with `-DINCLUDE_USER_CONFIG_H`, see its `build.sh`) so it stays off, as you want; hold cruise RES ~2 s for the dashboard items | CK wiring + bypass proven |
| **S4** | Flash the **C1, BH (and C2)** images from `firmware/ucan_prebuilt/` (or build them with `docs/build_ucan.sh`; C1 is built with `DISABLE_LOW_CONSUME`, immobilizer OFF, Start&Stop disabler OFF — §4.5, §8e). Use **Full chip erase** so no old settings survive. Hold BOOT0 while powering each board | each board starts (blue LED pulses; C1 menu shows the version `ucan-…`) |
| **S5** | First start (manual §2.1): engine running, cruise control off → hold RES/DISTANCE ~2 s → main menu → **SETUP MENU** (§8h). Our build is already gasoline: check that the item **"Diesel Params" shows O (deselected)**, and that **"My23 IPC" is deselected**. Check the defaults in §8e (immobilizer, seat-belt write) | menu opens |
| **S6** | Enable one at a time, ignition cycle + fault check after each: **dashboard parameters (petrol list; Start&Stop disabler and immobilizer stay off unless you choose to enable them) → shift lights → convenience (windows, park mirror, QV flap, seat-belt/odometer) → proxy-alignment features (ACC/HAS pads, race mask)** | no new faults |
| **S7** | **High-risk, last, stationary/closed course only:** 4WD disabler (C1); with C2: ESC/TC, DYNO, front-brake override. Prove rollback first (menu-disable, unplug, ignition cycle, Clear Faults) | rollback proven |

**Build — tested.** Use `docs/build_ucan.sh` (it holds the flags below and writes the images to `firmware/ucan_prebuilt/`; prebuilt copies are committed there, **not yet tested on hardware**). Toolchain: `gcc-arm-none-eabi` 13.2 (`apt install gcc-arm-none-eabi libnewlib-arm-none-eabi`; any recent ARM GNU toolchain works). By hand, from `firmware/ledsStripController`:
```bash
# C1 master: gasoline, sleep disabled, immobilizer OFF, Start&Stop disabler OFF
CFLAGS="-DIS_GASOLINE -DDISABLE_LOW_CONSUME -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP -DRELEASE_FLAVOR=C1_FLAVOR -DC1_FLAVOR=1" make clean all
# slaves (BH on OBD 3/11, C2 on OBD 12/13)
CFLAGS="-DRELEASE_FLAVOR=BH_FLAVOR -DBH_FLAVOR=1" make clean all
CFLAGS="-DRELEASE_FLAVOR=C2_FLAVOR -DC2_FLAVOR=1" make clean all
```
Output: `build/baccable-*.elf`, `.bin`, `.hex`. **Built and verified:** C1 = **78,624 bytes** (needs > 64 KB flash; fits the 96 KB C1 linker region), C2 = 37,532, BH = 36,800. Checked with the preprocessor that these flags leave `IMMOBILIZER_ENABLED`, `SMART_DISABLE_START_STOP`, `IS_DIESEL` and `LOW_CONSUME` undefined. C1 also compiles with `-DDEBUG_CAN_RX_SIMULATION` (bench build, not for the car). The Makefile picks the C1 linker script automatically when the flags contain `C1_FLAVOR`. The release workflows build the same three flavors, and the fork's "Build Beta Version" workflow accepts the same flags in its `CFLAGS` input, so GitHub can build them for you. **These defaults apply only when the settings flash page is blank:** a board that already ran BACCAble keeps its saved settings, so do a full chip erase when flashing (or change the items in the SETUP menu). Flashing: STM32CubeProgrammer in USB-DFU mode with the `.elf` (or `.bin` at `0x08000000`); the repo's own flashing app is documented for the dedicated PCB only. [Repo][built]

**Excluded:** REMOTE START and PEDAL BOOSTER ("under development, do not activate" per manual v4.9). **Not for petrol:** DPF/regeneration alert. [Repo]

### Feature → chip → hardware
| Feature | Chip | Notes |
|---|---|---|
| Start&Stop disabler (2.3), Immobilizer (2.4) | C1 | switched USB 5 V; **OFF by default in our build** |
| Shift lights (2.6) | C1 | – |
| Dashboard parameters (2.8), Route (2.9) | C1 + BH | serial link |
| 4WD disabler (2.15) | C1 | – |
| ESC/TC (2.10), DYNO (2.11), brake override (2.16) | **C2** (+C1 menu) | 3rd board |
| ACC/HAS, park mirror, windows, QV flap, seat-belt, odometer | C1 | some need proxy alignment |
| Sniffer, ELM327 | any / C1 | USB **data** cable when used |

---

## 8b. Programming button, reset button and status LEDs

### Programming (DFU) button — add one per board
- The dedicated BACCAble PCB has a **programming button** next to each USB port. Update procedure (manual §1.11): **hold the button, plug in USB, release when the green LED is lit**; the board shows up as "STM32 Bootloader". [Repo]
- A bare UCAN has **no button** — only the BOOT0 and 3V3 pads on P2 (pads 5 and 6, adjacent; verify on the silkscreen). So **solder a small momentary push button (or a 2-pin header + jumper) across BOOT0 ↔ 3V3, one per board**, and bring it to the box wall. Hold it while the board powers up → DFU. [Schem][GiUCAN]
- The firmware has **no software jump to the bootloader** (no bootloader/DFU code in `Core/`), so a button or jumper is the *only* way to reflash. [Repo: code search]
- Optional second button: **RES pad ↔ GND** (reset). Holding BOOT0 and tapping RESET enters DFU without unplugging USB. [Infer]
- Mechanical: keep each board's **USB-C port reachable** (short USB-C extension or panel-mount port), because the boards are powered from the car USB and you must move the cable to the PC to flash. After flashing, release the button and replug normally.
- Troubleshooting from the manual: weak LED / flaky detection → shorter or better USB cable; try another PC port or a slow USB hub; rotate the USB-C plug 180°. [Repo]

### Status LEDs — already on the UCAN
- The firmware drives two LEDs: **red = PA0**, **blue = PA1** (`onboardLed.h`). UCAN uses the same pins for its TX/RX LEDs (GiUCAN defaults: LED_RX = PA0, LED_TX = PA1) and the build defaults to `UCAN_BOARD_LED_INVERSION`, so the **UCAN's onboard LEDs work as-is**. The green **3V3** LED is the power indicator (the "green LED" in the manual). So you already have 3 status LEDs per board; extra external LEDs are not needed. [Repo][GiUCAN][Infer]
- What the code does (each LED pulse is 25 ms, `LED_DURATION`): [Repo: code]
  | LED | Meaning (from the code) |
  |---|---|
  | **Blue** short pulses | activity: CAN bus enabled, CAN messages processed, inter-board UART traffic sent/received, a setting saved to flash successfully, wake-up from low-consume. **Blue flashes twice at start-up when the immobilizer function is active** (manual) |
  | **Red** pulse | something needs attention: CAN configuration/disable, UART error, a setting could **not** be saved to flash, or **main-loop iteration took > 2 ms** (the author's debug check — continuous red = the loop is overloaded) |
  | **Red blinks 8×** | flash page erase failed while saving settings |
  | **Red blinks 9×** | flash write failed while saving settings |
  | **Green (3V3)** | board powered |
- Blue-only flicker on a running car is normal; steady/frequent red is a fault to investigate.

---

## 8c. How the firmware is organised (read from the source)
- **One codebase, flavor chosen at compile time** (`C1baccable`, `C2baccable`, `BHbaccable`, `ACT_AS_CANABLE`) in `compile_time_defines.h`; one image per board. [Repo]
- **Start-up (`main.c`):** clocks → LEDs → `can_init()` → (C1) `C1baccableInitCheck()` (loads saved settings from flash, starts low-consume if enabled) → `uart_init()` (inter-chip serial on USART2/PA14) → (BH/C2) `storage_init()` → (C2/BH/sniffer builds) USB device init **only on first power-up, not after a reset** (avoids hanging from condensation) → C1 and C2 open CAN at **500 kbit/s** → (BH) `BHbaccableInitCheck()`.
- **Main loop:** `onboardLed_process()` → `can_process()` (receive → per-ID handlers `processingMessage0x…c` / `processingStandardMessage.c` / `processingExtendedMessage.c`) → the flavor's periodic function (e.g. `C1baccablePeriodicCheck()`, which runs `lowConsume_process()` unless disabled) → UART queue to the other chips.
- **Master/slave:** C1 sends commands to BH/C2 over the single-wire UART (`uart.c` command codes like `C2cmdFunct…`, `BHcmdFunct…`); the setup menu on the dashboard (C1) enables functions, and the choice is stored in the last flash pages (`0x0801E800–0x0801FFFF`, `saveOnflash()`).
- **Sniffer/ELM327** are compiled into the normal firmware and stay off until enabled in the SETUP menu; they take over USB and the inter-chip line while in use. [Repo]
- BH opens CAN at 125 kbit/s in `BHbaccableInitCheck()` (read). Not yet read in detail: the per-function CAN message contents.

---

## 8d. Verified from the files of this repo (v3 read-through)

Everything below was read directly from `manuals/Baccable_manual_EN.pdf` (v4.9), `hardware/newBaccableDedicatedPcb/` (schematic + pinout), `firmware/ledsStripController/Core/{Src,Inc}` and the build workflows.

### A. How the author's own PCB is built (schematic `BACCABLE_SCHEMATIC.pdf`) — this is the design our three UCANs copy
- **Three identical STM32F072C8T6 chips (U10 = C1, U20 = C2, U30 = BH)**, one CAN transceiver each (U11, U21, U31), one USB-C connector each (J10, J20, J30 with 5.1 kΩ CC resistors). Manual: from left to right on the case the USB ports are **BH, C2, C1**. [Schem][Repo]
- **CAN pins:** each chip's CAN uses **PB8 (RX) / PB9 (TX)** to its transceiver — the same pins GiUCAN uses on the UCAN. **No termination resistor** is drawn across CANH/CANL on any bus: the transceivers connect straight to the OBD pins. (Supports removing R1/R2 on the UCANs.) [Schem]
- **One shared serial net called `Serial`** goes to **PA14 of all three chips** (the same pin as the UCAN CK pad). [Schem] Firmware: USART2, **38400 baud, 8N1, half-duplex, open-drain with pull-up on PA14**. [Repo: `uart.c`]
- **LEDs on every chip:** PA0 (red) and PA1 (second LED: **white on C1, blue on C2, yellow on BH**), 280 Ω / 100 Ω series resistors. The firmware's `LED_RED`=PA0, `LED_BLUE`=PA1. [Schem][Repo]
- **Power:** 12 V from OBD pin 16 → fuse F1 → one buck converter (4.5–35 V input) → 3.3 V for all chips; each USB-C VBUS also meets the board's 5 V net. Manual: input 4.5–35 V, **~15 mA at 12 V asleep, < 30 mA running**; pin 16 can also take 5 V. [Schem][Repo manual §1.10, §1.2]
- **Programming:** **one** push button (S1) pulls BOOT0 of **all three chips** high (10 kΩ pull-down), because everything shares one 3.3 V rail. You flash one chip at a time through its own USB-C port, holding the button while plugging in; release when the green LED is lit. [Schem][Repo manual §1.11]
- **Sleep wiring on the PCB:** C1's **PA4** (`ChipLowConsumeCmd`) goes to the **reset pins of C2 and BH**; C1's **PA5** (`CanLowConsumeCmd`) goes to the **RS (standby) pins of the C2 and BH transceivers**; C1's own transceiver RS is just pulled low. [Schem][Repo: `lowConsume.c`]
- **Extra I/O (not needed for us):** three open-collector outputs CMD1–3 (PA8 via a transistor), three inputs STS1–3, LED CTRL (PA11), exposed on the spare OBD-plug pins 1, 2, 15 / 9, 10, 7 / 8. The author's PCB is an OBD plug, and **he declines to publish the Gerber files**, so the dedicated PCB cannot be rebuilt from this repo — only the schematic is public. [Schem][upstream issue #29]
- **Flash size:** the author's own PCB uses the **F072C8T6** and runs this firmware; settings are written to the last flash pages at `0x0801F800` (settings), `0x0801F000` (statistics), `0x0801E800` (shown params) via the HAL's `FLASH_BANK1_END` for a 128 KB part. So the chips on that PCB behave as 128 KB. A C8T6 board is therefore plausible, but still check the flash size in STM32CubeProgrammer before flashing; a true 64 KB chip would fail every settings save (red LED blinks 8× or 9×). [Schem][Repo: `globalVariables.h`, `functions_C1baccable.c`]

### B. Firmware facts that matter for the build
- **Clock:** the CAN timing (prescaler 12, 1+4+3 time quanta = 500 kbit/s; prescaler 48 = 125 kbit/s) assumes a **48 MHz** peripheral clock, i.e. the internal HSI48. The Makefile sets `INTERNAL_OSCILLATOR` by default, so the UCAN's crystal is not needed. [Repo: `can.c`, Makefile]
- **Start-up order:** clocks → LEDs → CAN init → C1 reads its settings from flash → UART init → USB: **C1 only on demand** (sniffer/ELM327), while **C2 and BH start their pen-drive USB at power-on** (§8f) → C1 and C2 open CAN at 500 kbit/s; **BH opens CAN at 125 kbit/s** and loads the park-mirror positions from flash. The CAN receive filter accepts every frame. [Repo: `main.c`, `functions_BHbaccable.c`]
- **Single-wire protocol (`uart.c`, `uart.h`):** fixed-length frames, first byte = destination (C1=0x01, C2=0x02, BH string=0x03, BH status=0x08, BH=0x0A, C2+BH=0x0B, C1+BH=0x0C, C1+C2=0x0D). Rules: **only C1 starts a conversation** — every ≈250 ms it sends one queued message; **C2 and BH may answer only within ≈200 ms after a message addressed to them**; for messages sent to both slaves only C2 answers, so they never collide. After a 2 s start-up quiet period C1 asks C2 for status about every 1.0 s and BH about every 1.26 s. Receivers re-synchronise on the start byte, and the transmitter switches its own receiver off while sending. [Repo]
- **Consequence for the two-board build:** C1 never waits for a reply, so **C1 + BH works without C2**; messages meant for C2 (ESC/TC toggle, dyno, brake) are simply not answered. [Repo: `uart.c`]
- **Settings are pushed to the slaves once** about 3.5 s after C1 boots (and after every wake-up from sleep): ESC/TC state, pedal-booster state, odometer blink, race mask, park mirror, etc. [Repo: `functions_C1baccable.c`]
- **`DISABLE_LOW_CONSUME` side effect:** the wake-up code in `lowConsume.c` also arms the **DNA Memory** restore (`dnaMemoryWakeUp`). Without low-consume that flag is never set, so **DNA Memory (manual §2.34) will not restore the drive style** on a build with sleep disabled. Everything else the code reads is unaffected. [Repo: grep of `dnaMemoryWakeUp`]
- **C1 also opens USART1 on PB6 for the pedal booster (schizzaForte)**; with no booster connected this has no effect. [Repo]

### C. Bench test without the car (from the source)
- **`-DDEBUG_CAN_RX_SIMULATION`** puts the CAN controller in *silent loopback* (nothing drives the bus, no ACK needed) and injects a test frame every 100 ms, so a board boots and runs its normal receive path on a desk. **`-DDEBUG_START_SNIFFER`** and **`-DDEBUG_START_ELM327`** auto-enable those functions 10 s after boot. All three are marked DO NOT USE for normal builds. [Repo: `user_config.h.sample`, `main.c`]
- On the bench with C1 + BH (+ C2) wired by the CK wire, the **blue LEDs pulse on every UART frame**, so you can see the serial link working: C1's status requests (about 1 s) make BH and C2 answer. [Repo: `uart.c`]

### D. Facts from the manual that change or confirm the plan
- Manual v4.9 §2 describes: Start&Stop disabler, immobilizer, shift, parameters, route, ESC/TC, DYNO, ACC pad, clear faults, 4WD disabler, brake override, **read faults (§2.18)**, odometer blink, seat-belt alarm, park mirror, ACC autostart, windows, HAS pad, exhaust flap, front park mute, ELM327, Max Hold, DNA Memory. Only **REMOTE START** and **PEDAL BOOSTER** are marked "under development, do not activate". Note `user_config.h.sample` still calls READ FAULTS "experimental: doesn't work yet" while the manual documents it — treat READ FAULTS as untested and leave it off. [Repo]
- ESC/TC needs the car's **race mode enabled by proxy alignment**; enabling race this way loses the pedal maps unless race is disabled again on the engine ECU only (manual §2.19). ACC pad and HAS pad also need proxy alignment. [Repo manual]
- **Immobilizer test:** a theft attempt can be simulated with an ELM327 + AlfaOBD/MultiECUScan connecting to the RF hub; the car then cannot be started until you unplug the ELM327 and wait ~30 s. [Repo manual §2.4]
- **SGW:** "if the vehicle has an SGW, the OBD pins cannot be used — use an SGW bypass cable, or tap the CAN wires upstream of the SGW" (manual §1.8, with four tapping examples on the body computer). Reports from other users confirm that a car with an SGW but no bypass can show wrong values (e.g. oil pressure 0.00 bar). [Repo manual][upstream issue #41]
- **Compatibility:** the author reports one user on a MY23; MY22 is not reported either way. [upstream issue #5]
- **Menu basics:** hold RES (or DISTANCE) ~2 s with the engine running and cruise control off; use SETUP MENU → select functions → SAVE & EXIT; the menu hides 40 s after the engine stops. [Repo manual §2.1]

---

## 8e. What a freshly flashed board does (defaults, from `readFromFlash()` and `compile_time_defines.h`)

On a blank flash page every setting falls back to its compile-time default. With the stock release (no `user_config.h`) and no extra flags:

| Setting | Fresh-board default | Notes |
|---|---|---|
| **Immobilizer** | **ON** in the stock release; **OFF in our build** (`-DDISABLE_IMMOBILIZER`) | blocks RF-hub connections (ignition dead, horn alarm, ~10 s). Build with `-DDISABLE_IMMOBILIZER` to start OFF, or toggle at run time — **it is not in the SETUP menu**: engine running (> 400 rpm), cruise control and ACC off, gear in neutral (or gear unknown with the car steady 2 s), hold the cruise **speed-up** button; the code toggles after ≈ 20 s (620 message cycles; the manual says 30–40 s, so hold until the dashboard blinks: 6 half-cycles = 3 blinks = now ON, 12 = 6 blinks = now OFF), and the choice is saved to flash at once. `-DPERMANENTLY_DISABLE_IMMO` removes it for good. Use OFF before any ELM327/AlfaOBD/MultiECUScan session that touches the RF hub. [Repo] |
| **Start&Stop disabler** | **ON** in the stock release; **OFF in our build** (`-DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP`) | when enabled it acts only after 10 s from board start and with the engine running > 5 s; does nothing if the car already has S&S off. [Repo] |
| **Clear Faults** | **ON** | adds the menu item. |
| **Engine type** | **DIESEL** unless built with `-DIS_GASOLINE` | can also be changed in the SETUP menu (saved). |
| **Seat-belt alarm** | "enabled" | **no "leave untouched" option:** about 2 s after the engine starts, on every board power-up, C1 opens an extended session with the instrument cluster (`0x18DA60F1`) and sends IO-control `2F 55A0 03 xx` — `01` to enable the chime (default) or `00` to disable it (if the setting is deselected). The status is never read first. Harmless in a stock car, but it is a write to the cluster at every start. [Repo: `functions_C1baccable.c`, `processingExtendedMessage.c`] |
| LED strip, shift lights, MY23, route, DYNO, ACC pad, front-brake forcer, **4WD disabler**, ESC/TC, remote start, read faults, regen alert, pedal booster, odometer-blink hide, race mask, park mirror, ACC autostart, windows, HAS pad, exhaust flap, front park mute, sniffer, ELM327, DNA Memory | **OFF** | enable one at a time in SETUP. |

Other behaviour confirmed in the code:
- **Settings are saved by SAVE & EXIT** into the last flash page (33 values); a failed erase/write is signalled by the red LED blinking 8×/9×. The "shown parameters" selection and best 0–100 / 100–200 km/h times are stored in two other flash pages.
- **Dashboard menu** is updated every 500 ms; the menu hides ~39 s after the engine stops.
- **ELM327 and sniffer** use the same USB port, are mutually exclusive, and when ELM327 runs C1 stops its own bus traffic and dashboard refresh. [Repo]

---

## 8f. Flash map, USB behaviour and what each board needs (from the source)

- **All three boards need flash up to `0x0801FFFF` (128 KB).** C1 keeps settings in the last three pages (`0x0801F800` settings, `0x0801F000` statistics, `0x0801E800` shown params). **C2 and BH use a 64 KB FAT "pen drive" at `0x08010000–0x0801FFFF`** (`USB_FLASH_START_ADDRESS`, `TOTAL_USB_DEVICE_SIZE`), and BH saves its park-mirror positions at `0x0801F800`; the generic slave linker script limits their code to 60 KB so the images stay below it. A true 64 KB chip cannot work for the slaves either. [Repo: `diskio.c`, `compile_time_defines.h`, `*.ld`]
- **C2 and BH expose that pen drive over USB** (label `BACCABLE C2` / `BACCABLE BH`, file `Version.txt`, formatted automatically on first boot; USB is brought up at power-on). C1 does not start USB at boot (only when the sniffer or ELM327 is enabled). **Use power-only USB-C cables for all boards** so the car's head unit never sees a storage device; keep a data cable for flashing only. [Repo: `main.c`, `functions_Common.c`]
- **PA14 is both the serial pin and SWCLK**, so SWD debugging is not possible once the firmware runs; flashing uses USB-DFU (BOOT0), which is unaffected. [Repo]
- **Clock:** `SystemClock_Config()` uses the internal HSI48 directly (no PLL, no crystal), also for USB. [Repo: `functions_Common.c`]
- **Error indication:** an unrecoverable init error makes the **red LED blink forever** at a fixed rate (halfPeriod 500 ms = serial init, 750 ms = USART1 init on C1, 1000/1500/2000/2500 ms = USB clock, system clock, oscillator, DMA); useful for diagnosing a board that does nothing. [Repo: `Error_Handler()` callers]

## 8g. CAN IDs each board reads (use these to check the buses during the sniff step S2)

From the `case` labels in `processingStandardMessage.c` (11-bit IDs). Frames guarded for one flavor only are listed under that board; the rest are handled by all flavors:
- **C1 bus (500 kbit/s):** 0x101, 0x107, 0x192, 0x1F7, 0x2EF (gear), 0x412 (accelerator pedal), 0x41A, 0x41E, 0x420, 0x4B1, 0x4B2, 0x545, 0x5A5, 0x5A8 (TCM), 0x5AE, plus 0x4AF.
- **BH bus (125 kbit/s):** 0x090 (radio text on the cluster), 0x256 (DNA selector), 0x25A, 0x2EE, 0x354, 0x356, 0x3E6, 0x3E8, 0x46C (drive style), 0x5A0, 0x5A6, 0x5A8, 0x5AC.
- **C2 bus (500 kbit/s):** 0x0FA, 0x1F5, 0x1FC, 0x3E7 (PDC beeping), 0x4AF, 0x4B4, 0x54A (PDC button/LED), 0x5B0.
- Common to all: 0x0FC, 0x116, 0x1EF, 0x1F0, 0x226, 0x2ED, 0x2FA (steering-wheel button handling), 0x358, 0x384.
If a bus is silent in the S2 sniff, the cable or pair is wrong: these IDs are what the firmware waits for. [Repo — read from the source, not yet seen on a car]

---

## 8h. Dashboard menu map (from `processingMessage0x000002FA.c` and the manual)

- **How it is driven:** the C1 board reads the steering-wheel buttons from CAN ID `0x2FA` on the C1 bus. The menu works **only with cruise control and ACC both off** (`cruiseControlDisabled && ACC_status==0`). Hold **RES** (or **DISTANCE**) for ≈ 2 s (about 50 message cycles) to show/hide it; a short press selects. **Speed-down** = next item, **speed-up** = previous item; a firm press jumps 10 items. Build with `-DHIDE_DASHBOARD_MENU` to remove the menu permanently. [Repo]
- **Main menu (index → item):** 0 version · 1 Show Params · 2 Read Faults · 3 Clear Faults · 4 Immobilizer (shows ON/OFF) · 5 Dyno · 6 ESC/TC · 7 Front Brake · 8 4WD · 9 **SETUP MENU** · 10 PARAMS SETUP MENU · 11 HAS · 12 Exhaust Flap · 13 "Save Log to filesystem" (writes only a test file `hello.txt` on C2/BH — a stub, do not use) · 14 Reset statistics · 15 Max Hold. Items for functions that are disabled are skipped automatically. [Repo]
- **SETUP MENU (page → item):** 0 SAVE & EXIT · 1 Start&Stop · 2 Launch Torque (25 Nm steps, 25–600) · 3 LED controller · 4 Shift indicator · 5 Shift RPM (1500–6000, +250) · 6 My23 IPC · 7 Regen alert · 8 Seat-belt alarm · 9 Route messages · 10 ESC/TC · 11 Dyno · 12 ACC virtual pad · 13 Brakes override · 14 4WD disabler · 15 Clear faults · 16 Read faults · 17 Remote start · 18 **Diesel params** (selected = diesel; deselect for gasoline) · 19 Odometer blink · 20 Pedal booster · 21 Pedal power · 22 Park mirror · 23 ACC autostart · 24 Close windows · 25 Open windows · 26 HAS pad · 27 Exhaust flap · 28 Front park mute · 29 Sniffer · 30 ELM327 · 31 DNA memory. **There is no Immobilizer entry** (see §8e). [Repo]
- **Saving:** SAVE & EXIT writes to flash only if something differs from what is stored; sniffer/ELM327 changes take effect (USB bring-up) only at SAVE & EXIT. PARAMS SETUP MENU is saved separately (it hides/shows individual dashboard parameters). [Repo]
- **Safety interlocks in the menu code:** DYNO, 4WD disable and front-brake actions run only when the car has been steady for ≥ 1 s (otherwise the dashboard shows "STOP THE CAR"); the front brake also needs speed 0 and DYNO enabled first ("ENABLE DYNO"). [Repo]

---

## 8i. ELM327 mode — why the second and third board matter (from `elm327.c`, `elmlink.h`, manual §2.32)

- **What it is:** with ELM327 enabled (SETUP item 30, then SAVE & EXIT), C1's USB port behaves like an ELM327 adapter (ISO 15765-4) for MultiECUScan, AlfaOBD and similar tools. The code includes the programmable parameters MultiECUScan uses to choose bus speed and a raw mode (`ATCAF0`) for AlfaOBD. [Repo]
- **One USB port, three networks:** when the ECU being addressed is not on C1's own bus, C1 forwards the frame over the single-wire serial line (USART2, 38400 baud) to **C2 or BH**, which transmits it on their bus and return the answers. So the bridge reaches **C2 and BH only if those boards are fitted**; with the two-board build you reach C1 and BH. The design explicitly handles long UDS writes ("7F xx 78 response pending"), such as the **proxy alignment** that ESC/TC race mode, the ACC pad and the HAS pad require. [Repo]
- **Line discipline:** while the bridge runs, C1 stops its own dashboard refresh and UDS requests and the master never transmits until the slave says it is done (END block), to keep the single wire in sync. [Repo]
- **How to use it with loose boards (inference — the manual describes the PCB):** connect a USB **data** cable from the PC to **C1**, and only then connect the OBD side, as the manual says; 10 s after the cable is removed the board returns to normal. Do **not** let two 5 V sources feed the same board: **unplug C1's car-USB power lead while the PC powers it**, and keep C2/BH on the car USB (all grounds are common through the OBD ground). Leave the function disabled when not in use: the manual warns it can interfere with the immobilizer in the first seconds after power-up. [Repo manual][Infer]
- **Immobilizer interaction:** with the immobilizer function ON, any diagnostic session that connects to the RF hub triggers the theft response (§8e), so keep it OFF (our default) before MultiECUScan/AlfaOBD sessions. [Repo]

---

## 8j. How the functions act on the car, and dormant code found (from the per-message handlers)

- **BACCAble is a bus participant, not a gateway.** The boards do not sit between two halves of a bus. To change a value, they **receive the original frame and immediately transmit a modified copy with the same ID** (e.g. drive-style `0x384` for ESC/TC "race" on C1/C2, shift-light `0x2ED`, key-fob `0x1EF` for windows, steering buttons `0x2FA` for the ACC/HAS pads, always with the CRC recomputed). So each board simply needs a good tap on its bus (CAN H/L + ground), and the car's own ECUs keep running. [Repo: `processingMessage0x000001EF.c`, `…384.c`, `…2ED.c`, `…2FA.c`]
- **Engine-state logic comes from the rpm frame `0x0FC`** (every ~10 ms): engine on = rpm > 400; C1 counts 500 frames (≈ 5 s) before functions such as the Start&Stop disabler act; below 400 rpm C1 re-arms them, cancels the 4WD disable and starts the 40 s timer that hides the menu. [Repo: `…0FC.c`]
- **Start&Stop status** is read from `0x226` (byte 2 bits 3–2 = 1 means "disabled in the car"). [Repo]
- **Immobilizer** (when enabled and the engine is off) watches the C1 bus for diagnostic requests/replies between a tester and the **RF hub (address `0xC7`)**: services 0x10, 0x27, 0x29, 0x3E, 0x2E, 0x3D. On a match it floods the reset message every 10 ms, starts the panic alarm after 1 s and stops after 10 s. Any ELM327/AlfaOBD session on the RF hub looks the same, hence the advice in §8e. [Repo: `processingExtendedMessage.c`]
- **Dormant "pump force" test code.** `function_pump_force_enabled` is hard-coded to 1 ("enabled for test") and a handler can run an ECM security-access handshake (seed/key algorithm `MM10JA`) and then send `2F 50 11 03 FF` every 200 ms. **The only line that starts the sequence is commented out** in `C1baccablePeriodicCheck()`, and nothing in the menu sets the state machine, so it stays idle (`pumpForceStateMachine = 0xFF`) in the current source. It is not part of any manual function. Keep this in mind if you ever merge a newer upstream version: re-check that it is still inert. [Repo]
- **Other stubs:** main-menu item 13 "Save Log to filesystem" only writes `hello.txt`; the REMOTE START logic in `0x1EF` is commented out. [Repo]

---

## 9. Risks and stop conditions
| Risk | Rule |
|---|---|
| 64 KB flash board | return; never flash |
| Termination left on | stop; each bus must read ≈ 60 Ω through the harness |
| H/L swapped | warning lights → unplug immediately |
| Parked drain | switched USB only; no always-on feed without sleep wiring |
| Resistor on PA14 | never — it is the serial wire |
| Immobilizer + `DAC7F1` tire PIDs | do not read those PIDs with the immobilizer active |
| Seat-belt cluster write at every start | accepted default (writes "enable"); no setting leaves it untouched (§8e) |
| Prebuilt images untested | verify DFU flashing on the SPARE first; sniff before any function is enabled |
| Safety functions (DYNO, 4WD disable, brake override) | last; stationary/closed course; the repo is *"educational and research"* and prohibits use on public roads |
| Warranty/insurance/inspection | your responsibility |

---

## 10. Still uncertain
1. R1/R2 package size on your UCANs. (The author's own PCB has no termination across CANH/CANL, which supports removing them; no UCAN user report found.)
2. ~~Whether the bypass cable passes C2 and BH~~ — confirmed by the owner.
3. Exact CK-to-CK wire length/layout for three UCANs (the author's PCB shares one `Serial` net on PA14 across all three chips and he confirms a single wire; no drawing for loose boards).
4. Whether the optional PA13/PC13 sleep-pin change works with BACCAble.
5. Loose-module flashing procedure (repo documents only the PCB app).
6. Whether the car's USB ports follow the RF-hub wake for your 2022 car (matters only if you later enable the immobilizer).
7. The prebuilt images have not run on a UCAN: first flash and boot behaviour (LED pattern, `Version.txt` on C2/BH) is unconfirmed.
8. Files not read word for word: most of `elm327.c`, `elmlink.c` (headers and top read), `vuMeter.c` (LED strip, out of scope), the middle of `processingStandardMessage.c`, the middle of `processingExtendedMessage.c` and `uds_parameters.c`. Read in full or in the relevant parts: everything else in `Core/Src`.
9. Powering C1 from a PC for ELM327 use while C2/BH stay on car USB (§8i) is my inference, not a documented procedure.

---

## Appendix A — LED strip: out of scope
The WS281x LED-strip function is **not part of this plan** (no strip, level shifter or PA11 wiring). Leave it disabled in the SETUP menu.

## Appendix B — UCAN vs dedicated PCB
| | UCAN boards | Dedicated PCB |
|---|---|---|
| Status | "partial testing, with limitations" | primary, supported |
| Serial link | hand-wired | on board |
| Low-power sleep | not with stock firmware | yes (≈11 mA @12 V) |
| Expansion I/O, pedal-booster port | no | yes |
| Flashing | DFU per board | author's app (Windows/Android) |

## Sources
BACCAble https://github.com/gaucho1978/BACCAble (README, manual v4.9, `hardware/system_interconnection/*`, `Core/Inc/{lowConsume.h,compile_time_defines.h,user_config.h.sample}`, `Core/Src/lowConsume.c`, `Makefile`) · GiUCAN https://github.com/anegrin/GiUCAN (README, `docs/index.md`, `inc/config.h`, `src/{main.c,uart.c}`, `build.sh`, `STM32F072CBTX_FLASH.ld`) · canable-fw https://github.com/normaldotcom/canable-fw · PIDs https://github.com/danardi78/Alfaromeo-Giulia-Stelvio-PIDs · FYSETC UCAN https://github.com/FYSETC/UCAN · Giulia DLC pinout (user-supplied FCA diagram, `images/dlc_pinout.png`) · SGW: https://alfaobd.com/ · https://www.youcanic.com/fca-security-gateway/
