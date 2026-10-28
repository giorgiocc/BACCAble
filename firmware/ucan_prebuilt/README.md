# Prebuilt images for a DIY BACCAble on FYSETC UCAN boards (C1 / C2 / BH)

Built from this repository with `docs/build_ucan.sh` (ARM GCC 13.2). **Not yet tested on hardware.**
Dashboard version string: `BACCABLE ucan-<git short hash>`. Full plan: `docs/BACCAble_Giulia_Q4_Full_Plan.md`.

| File | Board | OBD pins | CAN speed |
|---|---|---|---|
| `C1.elf` / `C1.bin` | C1 master | 6 (H) / 14 (L) | 500 kbit/s |
| `C2.elf` / `C2.bin` | C2 slave | 12 (H) / 13 (L) | 500 kbit/s |
| `BH.elf` / `BH.bin` | BH slave | 3 (H) / 11 (L) | 125 kbit/s |
| `SNIFFER_ActAsCanable.*` | spare board: plain SLCAN sniffer for SavvyCAN (any bus; set 500 k for C1/C2, 125 k for BH) | – | – |
| `C1_BENCH_ONLY.*` | C1, desk tests only (CAN silent loopback + simulated frames) — **never in the car** | – | – |

## C1 flags
`-DIS_GASOLINE -DUCAN_LOW_CONSUME_PINS -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP`

* sleep (low consume) **on**, as on the author's device; the reset line to the slaves leaves from the **DO pad (PA13)**: wire **C1.DO → C2.RES and BH.RES**
* serial line: wire **C1.CK ↔ C2.CK ↔ BH.CK**
* transceiver standby (author's PA5 line, firmware unchanged): fine wire from **C1 chip pin 15 (PA5)** to **pin 8 (S/RS) of the CAN transceiver on C2 and on BH**
* defaults on a blank settings page: gasoline, **immobilizer OFF**, **Start&Stop disabler OFF**; everything else as the author's release. LED strip: leave "Led Controller" deselected.
* a board that ran BACCAble before keeps its saved settings: use a full chip erase when flashing
* C2 and BH are the author's stock images

## Board preparation (every UCAN in the car)
* **remove R1 and R2** (59 Ω + 59 Ω fixed CAN terminator, always connected on the UCAN V1.0) and keep the JP1 header open: the car buses are already terminated (plan §6)
* full wire list, OBD pin table and pad map: plan §2.2–2.3

## Power (chosen design)
OBD pin 16 → 1 A fuse → 12→3.3 V buck → P3-1 3V3 + P3-4 G pads of each board through a 2-pin plug (author's topology). **Unplug a board's 3V3 plug before connecting USB to it.**

## Flashing (USB DFU)
Unplug the board's 3V3 plug, then hold the B0 button (B0 shorted to 3V3) while plugging a data USB-C cable; the chip appears as `0483:df11`. Then flash the `.elf` with STM32CubeProgrammer, or the `.bin` with
`sudo dfu-util -d 0483:df11 -c 1 -i 0 -a 0 -s 0x08000000:leave -D C1.bin` (the command the repo's Makefile uses).
Check first that every chip reports **128 KB** of flash. Flash C2 and BH before fitting the reset wire, or C1 will hold them in reset on the bench.

## Licence / attribution
Built from BACCAble, Copyright (c) 2025 Gaucholivido - Tr3ma (see `LICENSE.MD`): free to use, modify and distribute with attribution; commercial resale is prohibited.
