# Giulia Q4 / FYSETC UCAN: wiring review — NOT APPROVED FOR VEHICLE USE

> **STOP:** A vehicle EOBD fuse blew during earlier testing. No existing generated illustration is an approved wiring diagram. Disconnect the assembly from the vehicle and do not refit the EOBD fuse to repeat a test until the source of the short has been found and the harness independently checked. This document is a *netlist for review* and is not an install authorization.

## Source status and limitations
- **Giulia bus assignments**: original BACCAble developer's repository [interconnections section](https://github.com/tr3ma-crew/BACCAble-firmware#the-interconnections-canable-connections-to-the-car) identifies C1 = OBD 6/14, C2 = 12/13, BH = 3/11.
- **UCAN P1 terminal identity**: FYSETC [UCAN official documentation](https://wiki.fysetc.com/docs/UCAN) confirms a 3-pin CANH/CANL/GND terminal. The [FYSETC UCAN V1.0 schematic](https://github.com/FYSETC/UCAN/blob/main/Hardware/UCAN%20V1.0%20SCH.pdf) and physical silkscreen must be checked on the actual board. The branch plan §2.2 labels schematic P1-1 CAN_L, P1-2 CAN_H, P1-3 GND. **Use actual H/L/G labeling to avoid counting the terminal from the wrong end.**
- **Manual**: [BACCAble English manual PDF](https://github.com/giorgiocc/BACCAble/blob/claude/peaceful-ritchie-aii7fs/manuals/Baccable_manual_EN.pdf) was identified but could not be read as a PDF by the GitHub connector in this review. It must be inspected by the original author/installer; do not attribute unverified diagram details to the PDF.
- **Pigtail colors** are seller claims, not standard OBD assignments. Check *actual metal contacts* with an ohmmeter; note front/back views are mirrored.

## CAN NETLIST: three distinct unconnected vehicle networks

| Net | From connector metal pin | To board CAN terminal | Must remain isolated from |
|---|---|---|---|
| C1_H | male OBD 6 | C1 CAN_H | C2_H, BH_H, every other CAN signal, ground, power |
| C1_L | male OBD 14 | C1 CAN_L | C2_L, BH_L, every other CAN signal, ground, power |
| C2_H | male OBD 12 | C2 CAN_H | C1_H, BH_H, every other CAN signal, ground, power |
| C2_L | male OBD 13 | C2 CAN_L | C1_L, BH_L, every other CAN signal, ground, power |
| BH_H | male OBD 3 | BH CAN_H | C1_H, C2_H, every other CAN signal, ground, power |
| BH_L | male OBD 11 | BH CAN_L | C1_L, C2_L, every other CAN signal, ground, power |

Each CAN_H/CAN_L pair is separate; **do not join the three CAN buses together**. The ground reference may be common; it is **not** a CAN_H or CAN_L signal.

## Power and grounds: review needed after blown fuse

- OBD 4 (chassis ground) and 5 (signal ground) → reviewed common ground node and board grounds according to the intended design.
- OBD 16 (+12 V) → correctly rated fuse near connector → **automotive protected 12 V-to-5 V supply** → power-only USB-C connectors for the three UCANs. Independently confirm input/output polarity and the exact power arrangement with the BACCAble author and electrical expert before vehicle use.
- **Never apply 12 V or 5 V to a pad marked 3V3.** The 3V3 pad is the board's 3.3 V rail, *not* its standard USB 5 V input. Previous suggested 12 V-to-3.3 V P3 power option is **NOT APPROVED** for this installation without transceiver variant and backfeed verification. Normal UCAN board input is **5 V at USB-C**.
- Do not connect a board's service USB data cable at the same time as another external power arrangement unless a reviewed power-isolation design explicitly permits it.
- **Do not replace the vehicle EOBD fuse and retry** without finding the electrical fault. An automotive technician should check the fuse circuit, vehicle connector, harness and grounds.

## Inter-board control (separate from CAN nets)
- W15 serial: C1.P2.CK ↔ C2.P2.CK ↔ BH.P2.CK.
- W16 low-consume reset: C1.P2.DO → C2.P2.RES and BH.P2.RES; **NOT YET FITTED**, not a CAN bus connection.
- W17 transceiver standby: C1 MCU PA5 (pin 15) → C2 CAN transceiver RS/S pin 8 and BH transceiver RS/S pin 8; **NOT YET FITTED**, not a CAN bus connection.
- The W16/W17 wires must be validated on the bench with the exact firmware before any final install. Their absence is a **vehicle-safety / parked-current concern**, not an excuse to bypass safety tests.
- Boot controls must not tie unrelated 3V3 rails together during USB service.

## UNPOWERED meter inspection checklist (each board disconnected from car)
1. Photograph both sides of connector and boards to verify mating-face orientation, pin labels and soldered connections.
2. Check continuity of all six CAN netlist entries, one end at actual OBD contact and one at correct labeled UCAN terminal.
3. Prove all three CAN_H conductors are **separate** from the other two CAN_H conductors, likewise all three CAN_L conductors; also check every cross-pair cross-network combination for unintended continuity.
4. Check OBD 16 is NOT shorted to 4/5 ground, to any CAN conductor, or to converter output.
5. Confirm no CAN signal conductor is shorted to ground/power; account for normal semiconductor/protection diode readings versus hard wire shorts.
6. Verify no unintended CAN termination remains on boards (R1/R2 removed and JP1 open, with resistance confirmed).
7. Have the original BACCAble author or qualified automotive electronics technician review the as-built wiring **and** power design.

**A passing meter test is necessary but does not certify the vehicle CAN bus is safe.** Proceed with separate controlled bench tests and qualified review. No vehicle reconnection until the blown-fuse root cause and standby behavior have been resolved.
