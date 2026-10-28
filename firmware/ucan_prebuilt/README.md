# Prebuilt images for loose FYSETC UCAN boards (C1 / C2 / BH)

Built from this repository with `docs/build_ucan.sh` (ARM GCC 13.2, Ubuntu `gcc-arm-none-eabi`). **Not yet tested on hardware.**
Firmware version string on the dashboard: `BACCABLE ucan-<git short hash>`.

| File | Board | OBD pins | CAN speed | Size |
|---|---|---|---|---|
| `C1.elf` / `C1.bin` | C1 master | 6 (H) / 14 (L) | 500 kbit/s | 78,624 bytes |
| `BH.elf` / `BH.bin` | BH slave | 3 (H) / 11 (L) | 125 kbit/s | 36,800 bytes |
| `C2.elf` / `C2.bin` | C2 slave (optional) | 12 (H) / 13 (L) | 500 kbit/s | 37,532 bytes |

## Defaults baked into C1 (apply only when the board's settings flash page is blank)
`-DIS_GASOLINE -DDISABLE_LOW_CONSUME -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP`

* gasoline parameters, **immobilizer OFF**, **Start&Stop disabler OFF**, sleep (low-consume) disabled
* every other function is OFF until enabled in the dashboard SETUP menu
* if the board already ran BACCAble before, its saved settings win over these defaults: do a full chip erase when flashing, or change the items in the SETUP menu

## Flashing (USB DFU)
Hold B0 to 3V3 while powering the board over USB-C (the chip then appears as USB device `0483:df11`), then flash the `.elf` with STM32CubeProgrammer, or the `.bin` with `sudo dfu-util -d 0483:df11 -c 1 -i 0 -a 0 -s 0x08000000:leave -D C1.bin` (the command the repo's Makefile uses). Check first that the chip reports **128 KB** of flash: all three images need the flash up to `0x0801FFFF`.

## Licence / attribution
Built from BACCAble, Copyright (c) 2025 Gaucholivido - Tr3ma (see `LICENSE.MD`): free to use, modify and distribute with attribution; commercial resale is prohibited.
