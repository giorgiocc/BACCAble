# BACCAble DIY — Research, Hardware Plan & Step-by-Step Build (v2)

**Car:** 2022 Alfa Romeo Giulia Sprint Q4 · 2.0 petrol · MY22 cluster
**Goal:** BACCAble function set on loose FYSETC UCAN boards (one per CAN bus)
**SGW:** bypass cable already owned · **Case:** own box · **Shopping:** buy on eBay/Amazon
**Status:** research + hardware plan. **Nothing is flashed or installed yet.**
**v2 changes:** added the cross-check against the repos linked in the BACCAble README (canable-fw, GiUCAN, Alfaromeo-Giulia-Stelvio-PIDs), the repo's wiring diagrams and the Giulia DLC pinout. The build is now **2 boards minimum (C1 + BH), a 3rd (C2) optional**. Out of scope by request: macOS-specific flashing, idle-current measurement, 4WD-disabler logic analysis.

Evidence tags: **[Repo]** stated by BACCAble repo/manual v4.9 · **[GiUCAN]** from github.com/anegrin/GiUCAN · **[Schem]** read from a schematic · **[Diagram]** read from a diagram image · **[Infer]** my inference, verify · **[Unv]** not verified.

---

## 1. Summary

1. **Right repo:** `gaucho1978/BACCAble` (live; manual v4.9). `tr3ma-crew/BACCAble-firmware` is a stale firmware-only snapshot. [Repo]
2. **UCAN is a supported board.** The author ships cases `hardware/box/dual_fysect_ucan` and `single_fysect_ucan`, `UCAN_BOARD_LED_INVERSION` is on by default, and the author's own diagram (`ShowParamsOnDashboardConnections.png`) shows two UCANs as master (C1) + slave (BH) with the note that any STM32F072 board is equivalent. [Repo][Diagram]
3. **GiUCAN proves the UCAN approach on real cars.** It is a cut-down BACCAble written *only* for FYSETC UCAN (C1 + BH), derived from canable-fw. [GiUCAN]
4. **Minimum build = 2 boards:** C1 (master, OBD 6/14) + BH (slave, OBD 3/11), joined by one wire between their **CK pads**. **C2 (OBD 12/13) is only needed for ESC/TC, DYNO and front-brake override.** Everything else, including the 4WD disabler (runs on C1), works with two boards. [Repo][Diagram]
5. **Use FYSETC UCAN V1.0 (STM32F072CBT6, 128 KB flash).** GiUCAN's linker script for it is 64 K flash + 64 K "EEPROM" at 0x08010000 (= 128 KB). The BACCAble C1 image is ~73.6 KB, so a true 64 KB F072C8 will not fit. [GiUCAN][Repo][Schem]
6. **Power each board over USB-C, 5 V.** UCAN has no 12 V input. Two supported sources: car USB 5 V (switched, no drain) or a 12 V→5 V DC-DC feeding the USB-C inputs. See §5. [Repo][GiUCAN][Schem]
7. **Settings for your car:** GASOLINE in the setup menu, "My23 IPC" off. Both are runtime menu options. [Repo]
8. **Termination:** the car buses are already terminated, so the module must add none. On UCAN, R1+R2 (59 Ω + 59 Ω) are hard-wired across CAN H/L, so measure and, per the schematic, remove them. GiUCAN's docs don't mention this; ask the Telegram group. [Schem][Unv]
9. **Immobilizer function:** needs power that wakes with the RF hub (car USB 5 V or 12 V OBD). If you don't use it, any 5 V source that is up while driving works. [Repo]

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
| **C1** | Master / gateway | **6 (H) / 14 (L)** | 500 kbit/s | Start&Stop disabler, immobilizer, shift lights, LED strip, dashboard menu, ACC/HAS pads, 4WD disabler, ELM327, sniffer |
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

### 3.3 Adding C2 (three boards) [Infer — the repo's diagram only shows two]

- C2 CAN pair → OBD **12 (H) / 13 (L)**, grounds to OBD 4/5.
- C2 **CK pad** → the **same single wire** as C1 and BH (one shared serial net; the dedicated PCB does the same). Common GND.
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
| **C. Old single-CANable design** | `hardware/system_interconnection/SCHEMA_DI_INTERCONNESSIONE.png` | One CANable, 12 V→5 V regulator into the board's `+5V` terminal, LED strip control on PA11 (USB D−), and a **hardware Start&Stop bypass panel** (520 Ω / 2 kΩ / 1.5 kΩ / 7 kΩ + switch) on the car's 12-pin switch-panel connector, with a 1.5 kΩ resistor from PA14. Notes: ECU impedance before pin 5 = 910 Ω, pin 9 = 99 Ω; 470 Ω instead of 1.5 kΩ disables the parking acoustic signal. |

**Variant C is the legacy design — do not build it.** Current firmware disables Start&Stop by CAN message (`SMART_DISABLE_START_STOP`), and **PA14 is now the inter-board serial pin, so never hang a resistor on it.** The "+12 V" in that drawing comes from the switch-panel connector, not OBD pin 16 (switched/always-on is not stated). [Diagram][Infer]

---

## 4. Findings that shape the build

### 4.1 Flash size
| Evidence | Finding |
|---|---|
| Release ELFs (V.3.8.2, measured) | C1 = 73.6 KB, C2 = 35.8 KB, BH = 34.2 KB, ActAsCanable = 24.9 KB |
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
- PA11 (LED-strip data in firmware) = USB D− via R11. [Schem][Repo]

### 4.4 Clock
BACCAble builds with the **internal 48 MHz oscillator** (`INTERNAL_OSCILLATOR`, HSI48). UCAN's 8 MHz crystal is not needed; GiUCAN uses it by default but its BACCAble flavor builds with `DISABLE_EXTERNAL_OSCILLATOR`. Stock BACCAble images should run on UCAN as-is. [Repo][GiUCAN]

### 4.5 Sleep / low-consumption pins
| | Reset line to slaves | CAN transceiver silent |
|---|---|---|
| BACCAble `lowConsume.h` (dedicated PCB) | **PA4** | **PA5** |
| GiUCAN on UCAN (defaults) | **PA13 (DO pad)** → BH RES | **PC13** |

On loose UCANs the BACCAble sleep code points at pads that aren't wired. Choices: **(1)** build C1 with `DISABLE_LOW_CONSUME` (no sleep; use switched car USB so there is no drain); **(2)** optional firmware change to move the two pins to PA13/PC13 and wire DO→RES like GiUCAN (**untested**). [Repo][GiUCAN][Infer]

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
- The manual doesn't require USB power for loose boards; this is GiUCAN's and the author's diagram's approach. [Repo][GiUCAN]

---

## 6. Shopping list

### 6.1 Core
| # | Search | Qty | Check |
|---|---|---|---|
| 1 | "FYSETC UCAN USB to CAN adapter STM32F072" | **2 for the minimum build, 3 with C2, +1 spare** (you already bought them) | Photos show "UCAN V1.0", USB-C, green 3-pin terminal; MCU must read **STM32F072CBT6** |
| 2 | "OBD2 16 pin male plug to open end cable" / breakout | 1 | all pins wired (needs 3, 4, 5, 6, 11, 14, 16; add 12, 13 for C2) |
| 3 | "Twisted pair cable 22AWG" | ~3 m | |
| 4 | "USB-C charge-only cable" or data-blocker | 2–3 | power-only so the head unit isn't shown unknown devices [Infer] |
| 5 | "USB 1 to 3 splitter power only" (passive) | 1 | |
| 6 | 2.54 mm pin headers + jumper caps | 1 / 5 | CK, GND, BOOT0 pads; DFU jumper |
| 7 | Dupont wires, 24 AWG silicone wire, ferrules | 1 each | |
| 8 | ABS project box + cable glands + standoffs | 1 | own case; measure the boards first |
| 9 | Heat-shrink, Kapton tape, cable ties | | |

### 6.2 Tools
Multimeter (continuity, 10 A); temperature-controlled iron + flux + wick + tweezers + loupe (for R1/R2); 120 Ω resistors ×4 (bench CAN test); 5 V 2 A USB supply; 2 short USB-C data cables for DFU.

### 6.3 Optional
12 V→5 V DC-DC + fuse tap + 1–2 A fuse (variant B only). LED-strip parts (Appendix A).

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
Pin 16 ↔ 4 ≈ 12 V is not required for USB-powered builds.

**H8. Box.** Mount on standoffs, strain-relief with glands, keep USB-C, terminals and pads reachable. Away from pedals, steering column, knee-airbag path, heat and HVAC flaps. Label boards at both ends.

**H9. Pre-install checklist**
- [ ] Boards read STM32F072CBT6, 128 KB
- [ ] R1/R2 removed on installed boards
- [ ] CK + GND harness verified
- [ ] H7 table recorded (C1 + BH pass; C2 if used)
- [ ] Car USB 5 V present when doors unlock/key near, absent when car sleeps

**H10. In-car install.** Car off; OBD harness into the bypass port first with boards **unpowered**; re-measure each pair through the harness ≈ 60 Ω; connect power last. Do **not** power boards on the car with unknown firmware.

---

## 8. Build — Phase S (software)

| Step | Action | Gate |
|---|---|---|
| **S0** | Install STM32CubeProgrammer; decide LED strip yes/no | hardware gate passed |
| **S1** | Flash **ActAsCanable** (or GiUCAN SLCAN) on the SPARE; prove DFU flashing | spare works |
| **S2** | Sniff in silent mode (`M1`) on the car: C1 at 500 kbit/s, BH at 125 kbit/s (C2 at 500 kbit/s) | traffic on every bus |
| **S3 (recommended)** | Bench-prove the wiring with **GiUCAN C1CAN + BHCAN** (build with `build.sh`, flash from `dist/`): after a few seconds the SNS LED shows Start&Stop disabled; hold cruise RES ~2 s for the dashboard items | CK wiring + bypass proven |
| **S4** | Flash BACCAble V.3.8.x+ **C1, BH (and C2)** images; for C1 use a custom build with **`DISABLE_LOW_CONSUME`** (§4.5) | each board reports its flavor |
| **S5** | First start (manual §2.1): hold RES/DISTANCE ~2 s → SETUP menu. Select **GASOLINE**, leave **My23 IPC off** | menu opens |
| **S6** | Enable one at a time, ignition cycle + fault check after each: **Start&Stop disabler → immobilizer (optional) → dashboard parameters (petrol list) → shift lights → LED strip (if installed) → convenience (windows, park mirror, QV flap, seat-belt/odometer) → proxy-alignment features (ACC/HAS pads, race mask)** | no new faults |
| **S7** | **High-risk, last, stationary/closed course only:** 4WD disabler (C1); with C2: ESC/TC, DYNO, front-brake override. Prove rollback first (menu-disable, unplug, ignition cycle, Clear Faults) | rollback proven |

Build commands (BACCAble, GCC): from `firmware/ledsStripController`, copy `Core/Inc/user_config.h.sample` → `user_config.h` and add `-DINCLUDE_USER_CONFIG_H`; flavors via `-DRELEASE_FLAVOR=C1_FLAVOR -DC1_FLAVOR=1` (likewise `C2_FLAVOR`, `BH_FLAVOR`). Example C1: `CFLAGS='-DINCLUDE_USER_CONFIG_H -DIS_GASOLINE -DRELEASE_FLAVOR=C1_FLAVOR -DC1_FLAVOR=1' make clean all` with `#define DISABLE_LOW_CONSUME` in `user_config.h`. Flashing: STM32CubeProgrammer in USB-DFU mode with the `.elf` (the repo's flashing app is documented for the dedicated PCB; loose-module flashing is not documented by the repo). [Repo][Unv]

**Excluded:** REMOTE START, READ FAULTS, PEDAL BOOSTER (under development per manual). **Not for petrol:** DPF/regeneration alert. [Repo]

### Feature → chip → hardware
| Feature | Chip | Notes |
|---|---|---|
| Start&Stop disabler (2.3), Immobilizer (2.4) | C1 | switched USB 5 V |
| LED strip (2.5), Shift (2.6) | C1 | Appendix A |
| Dashboard parameters (2.8), Route (2.9) | C1 + BH | serial link |
| 4WD disabler (2.15) | C1 | – |
| ESC/TC (2.10), DYNO (2.11), brake override (2.16) | **C2** (+C1 menu) | 3rd board |
| ACC/HAS, park mirror, windows, QV flap, seat-belt, odometer | C1 | some need proxy alignment |
| Sniffer, ELM327 | any / C1 | USB **data** cable when used |

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
| Safety functions (DYNO, 4WD disable, brake override) | last; stationary/closed course; the repo is *"educational and research"* and prohibits use on public roads |
| Warranty/insurance/inspection | your responsibility |

---

## 10. Still uncertain
1. Whether UCAN users remove R1/R2; R1/R2 package size.
2. Whether your bypass cable passes C2 and BH (H7).
3. Three-board UCAN serial wiring is inferred from the dedicated PCB, not documented for UCAN.
4. Whether the optional PA13/PC13 sleep-pin change works with BACCAble.
5. Loose-module flashing procedure (repo documents only the PCB app).
6. Whether the car's USB ports follow the RF-hub wake for your 2022 car.

---

## Appendix A — LED strip (optional)
Driven by **C1 PA11 (TIM1_CH4)** = USB D− via R11 on UCAN. Parts: WS2811 IP65 strip (check 5/12 V and length), 74AHCT125 level shifter, 30 AWG wire, inline fuse; 12→5 V buck only for 5 V strips. Steps: C1 on a power-only USB cable so D− is free; thin wire to the MCU side of R11; level shifter to strip DIN; strip on a fused supply (never a USB port); common ground. [Infer]

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
