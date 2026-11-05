# DVF-ACLP: Doron Velta Fork for the Anycubic Kossel Linear Plus

A Doron Velta style conversion kit for the **Anycubic Kossel Linear Plus**. It keeps as much of the stock printer as possible and changes the controller to a **BTT SKR Pico v1.0 + Raspberry Pi 3B running Klipper**.

* **Open sides, no closing lid.** No ACM side panels, doors or top covers. Only skirts on the frame rails.
* **Stock hardware stays:** 2020 frame, plastic corners, MGN12 linear rails and carriages, 269 mm diagonal arms, motors, belts, heated bed, hotend, Bowden extruder, 12 V PSU and clip-on probe.
* **Everything is parametric.** Measure your printer, edit [`CAD/params.json`](CAD/params.json), and run one script to rebuild every STL/STEP file.

![parts](images/parts_overview.png)

> ⚠️ **Status: v0.1, not fit-tested on a real printer.** Dimensions come from the Anycubic manual, Klipper's Kossel Plus config and common part standards (2020, E3D V6 groove mount, 5015/3010/4010 fans, Pi hole pattern). **Print `00_Fit_Test` first** and check the measurements below before printing everything.

## Measure these before printing

| Parameter (`params.json`) | Default | What to measure |
|---|---|---|
| `frame.bottom_rail_pitch` | 45 | Centre-to-centre distance between the two lower horizontal 2020 rails |
| `skirt.span` | 240 | Free outer rail length between two corner housings (skirt = 2 halves) |
| `effector.arm_spacing` | 46 | Centre-to-centre distance between the two ball joints of one arm pair, **measured on your stock carriage** (it must match) |
| `effector.offset` | 30 | Effector centre to the arm-joint axis |
| `foot.corner_clear` | 55 | Corner vertex to the first exposed spot on a bottom rail |

## Print list

| Folder | File | Qty | Notes |
|---|---|---:|---|
| 00_Fit_Test | fit_test_coupon | 1 | Print first. Bolt it to both lower rails. |
| Skirts | bottom_skirt_half | 3 | Covers both lower rails, honeycomb between them |
| Skirts | bottom_skirt_badge_half | 2 | Has a pocket for the logo badge next to the joint |
| Skirts | bottom_skirt_ports_half | 1 | Opening for USB / power / cables. Put it on the electronics side. |
| Skirts | top_skirt_half | 6 | Crown above the top rails, hides the idlers |
| Skirts | logo_badge | 2 | Glue into the badge pocket. Print in an accent colour. |
| Frame | foot | 3 | Bolts under the two lower rails at each corner. Add a 32 mm rubber pad. |
| Frame | endstop_mount | 3 | Optional, adjustable holder for the stock microswitch boards |
| Frame | cable_clip_2020 | 12 | M4 + T-nut |
| Toolhead | effector_v6 | 1 | New effector. The hotend slides in from the side into the 12 mm groove. |
| Toolhead | groove_clamp | 1 | Locks the top collar. Its key fills the entry slot. |
| Toolhead | hotend_shroud_3010 | 1 | Under the effector. 30 mm heatsink fan. |
| Toolhead | part_fan_duct_5015 | 1 | Push-fit on the 5015 outlet, screws to the shroud ear |
| Electronics | skr_pico_pi3b_plate | 1 | SKR Pico + Pi 3B side by side, M2.5 heat-set inserts |
| Electronics | fan_bracket_4010 | 1 | Electronics cooling fan |
| Extruder | bowden_extruder_mount | 1 | NEMA17 plate for the stock extruder, bolts to 2020 |
| Extruder | spool_holder | 1 | Top-rail spool arm |

Print settings: PETG or ABS/ASA, 0.2 mm layers, 4 walls, 30–40 % infill. Use ABS/ASA for the toolhead parts. The skirts print **front face down**.

## Files

```
CAD/build_dvf.py      parametric generator (FreeCAD 1.x Python)
CAD/params.json       all dimensions
CAD/DVF_ACLP.FCStd    FreeCAD document with every part
CAD/STEP/*.step       editable solids (import into SolidWorks / Fusion / Onshape)
STLs/**               print files, _xN = quantity
Firmware/printer.cfg  Klipper config for SKR Pico on the Kossel Linear Plus
Docs/wiring.md        SKR Pico + Pi 3B wiring
BOM.md                hardware list
```

Rebuild after changing params:

```
"C:\Program Files\FreeCAD 1.1\bin\python.exe" CAD/build_dvf.py
```

## Credits and license

Inspired by [Doron Velta by rogerlz](https://github.com/rogerlz/Doron-Velta) (forked at [Xanjip32/Doron-Velta](https://github.com/Xanjip32/Doron-Velta)). The Doron Velta frame is a 2040/ACM build, so its parts cannot bolt onto a Kossel. These parts are new designs in the same style, sized for the Kossel. The SKR Pico/Pi hole pattern (58 × 49 mm) was measured from the original `skr_pico_mount`. The Klipper config is based on Klipper's `printer-anycubic-kossel-plus-2017.cfg`. GPL-3.0, same as Doron Velta. This is not an official Voron, Doron Velta or Anycubic project.
