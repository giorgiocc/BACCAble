#!/usr/bin/env bash
# Builds the three BACCAble images for loose FYSETC UCAN boards (C1 master, C2 and BH slaves).
# C1 image: low-consume (sleep) ON exactly like the author's device, with the reset line moved to the UCAN
# DO pad (PA13) -> wire C1.DO to C2.RES and BH.RES. Defaults that apply only on a blank settings flash page:
#   gasoline engine, immobilizer OFF, Start&Stop disabler OFF.
# Also builds C1_BENCH_ONLY.* (CAN in silent loopback with simulated frames): for testing the boards on a desk,
# NEVER for the car. SNIFFER_ActAsCanable.* is the plain SLCAN sniffer (SavvyCAN) for the spare board.
# Everything can still be changed at run time from the dashboard SETUP menu.
# Needs: gcc-arm-none-eabi (e.g. `apt install gcc-arm-none-eabi libnewlib-arm-none-eabi`).
# Usage: docs/build_ucan.sh [output_dir]      Extra flags: EXTRA_CFLAGS="-DLARGE_DISPLAY" docs/build_ucan.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/firmware/ucan_prebuilt}"
VER="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)"
C1_FLAGS="-DIS_GASOLINE -DUCAN_LOW_CONSUME_PINS -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP"

mkdir -p "$OUT"
cd "$ROOT/firmware/ledsStripController"

build() { # name flavor extra-flags
  local name="$1" flavor="$2" extra="$3"
  CFLAGS="$extra ${EXTRA_CFLAGS:-} -DBUILD_VERSION=\\\"ucan-$VER\\\" -DRELEASE_FLAVOR=${flavor}_FLAVOR -D${flavor}_FLAVOR=1" make clean all >/dev/null
  cp build/baccable-*.elf "$OUT/$name.elf"
  cp build/baccable-*.bin "$OUT/$name.bin"
  printf '%-4s %7s bytes  (%s)\n' "$flavor" "$(stat -c %s "$OUT/$name.bin")" "$name"
}

build C1 C1 "$C1_FLAGS"
build C1_BENCH_ONLY C1 "$C1_FLAGS -DDEBUG_CAN_RX_SIMULATION"
build C2 C2 ""
build BH BH ""
build SNIFFER_ActAsCanable CAN ""
make clean >/dev/null
echo "Images in $OUT (version ucan-$VER)"
