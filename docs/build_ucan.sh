#!/usr/bin/env bash
# Builds the three BACCAble images for loose FYSETC UCAN boards (C1 master, C2 and BH slaves).
# Defaults baked into the C1 image (they apply only on a board whose settings flash page is blank):
#   gasoline engine, immobilizer OFF, Start&Stop disabler OFF, low-consume/sleep disabled.
# Everything can still be changed at run time from the dashboard SETUP menu.
# Needs: gcc-arm-none-eabi (e.g. `apt install gcc-arm-none-eabi libnewlib-arm-none-eabi`).
# Usage: docs/build_ucan.sh [output_dir]      Extra flags: EXTRA_CFLAGS="-DLARGE_DISPLAY" docs/build_ucan.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/firmware/ucan_prebuilt}"
VER="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo dev)"
C1_FLAGS="-DIS_GASOLINE -DDISABLE_LOW_CONSUME -DDISABLE_IMMOBILIZER -DDISABLE_THE_FUNCTION_SMART_DISABLE_START_STOP"

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
build C2 C2 ""
build BH BH ""
make clean >/dev/null
echo "Images in $OUT (version ucan-$VER)"
