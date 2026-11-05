# DVF-ACLP: Doron Velta Fork for the Anycubic Kossel Linear Plus

A Doron Velta style rebuild of the **Anycubic Kossel Linear Plus**. It uses new printed corners, a closed power base, a top electronics bay and skirts. It keeps the stock **2020 aluminium extrusions, MGN12 rails, motors, belts, arms, bed and hotend**. The controller changes to **BTT SKR Pico v1.0 + Raspberry Pi 3B (Klipper)**. The sides stay open, with no doors or side panels.

![assembly](images/assembly_full.png)

| Bottom section | Top section (lid on) | Toolhead |
|---|---|---|
| ![](images/assembly_base.png) | ![](images/assembly_top.png) | ![](images/assembly_toolhead.png) |

> ⚠️ **v0.3, not yet built or fit-tested.** All parts are generated from [`CAD/params.json`](CAD/params.json), and several values are estimates (see below). Print `00_Fit_Test` and **one bottom corner** first.

Colours: **red = printed parts, black = stock/bought parts** (frame, rails, motors, arms, bed, PSU, boards, fans, panels).

## What's new in v0.3: enclosed Doron Velta sections

* **Deep boxed skirts**, 20 mm deep with a chamfered front and a full hex grill, the same style as the original. They bolt to the rails from the front.
  * **Bottom section:** 6 halves from floor to bed height. One holds a **60 mm intake fan**, and one is the **power half (right side)** with the IEC inlet + switch box.
  * **Top section:** 6 halves from the top rail up to the lid. One holds a **60 mm intake fan** blowing across the SKR Pico and Pi.
* **Closed top and bottom:**
  * Bottom: `bed_deck` panel under the bed (the inner cover), with 3 bed standoffs and a hole for the bed wires.
  * Top: the top deck panel holds the electronics, `corner_top_cap` ×3 fill the corners, and a **`lid`** panel with a hex vent field covers everything.
* **Pillar covers:** 12 clip-on segments, 4 per tower, cover the outer face of each tower. They are hollow, so the 12 V and toolhead cables run inside the tower A pillar.
* **Side spool + extruder bracket:** bolts to the flat outer face of the tower B top corner and carries the stock NEMA17 Bowden extruder and the spool arm.

### Airflow

| Section | In | Out |
|---|---|---|
| Bottom (PSU) | 60 mm fan in the rear-face skirt (always on with power) | Hex grills on the other 5 halves + floor vents. The PSU's own fan circulates the air. |
| Top (Pico + Pi) | 60 mm fan in the right top skirt (Klipper `controller_fan`, FAN3) | Hex grills on the other 5 halves + the lid's hex vent over the boards |

The bed deck separates the warm PSU compartment from the print area.

## Measure these before printing

| Parameter | Default | What it is |
|---|---|---|
| `frame.rail_len` | 300 | Length of the horizontal 2020s (Anycubic manual) |
| `frame.tower_len` | 720 | Length of the vertical 2020s. **Measure.** |
| `frame.bottom_rail_pitch` | 45 | Centre-to-centre of the two lower rails. **Measure.** |
| `corner.tower_from_vertex` | 70 | Sets the tower position, and so the delta radius |
| `power.psu_*` | 215 / 115 / 50 | Your PSU's size |
| `power.iec_*` | 47.5 × 27.5 | Panel cut-out of your IEC inlet/switch module |
| `effector.arm_spacing` | 46 | Ball-joint spacing of your stock arms/carriages |

With these defaults, Klipper starts at `delta_radius ≈ 122.8` with `arm_length 269`. Then run `DELTA_CALIBRATE`.

## Print / cut list

| Folder | Part | Qty | Notes |
|---|---|---:|---|
| 00_Fit_Test | deep_skirt_fit_test | 1 | Slice of a bottom skirt. Check it on both lower rails. |
| Corners | corner_bottom_motor / corner_top_idler | 3 / 3 | 4–5 walls, 25 % gyroid |
| Corners | corner_top_cap | 3 | Between the top deck and the lid. M3 into the corner inserts. |
| Corners | pillar_cover | 12 | 4 per tower, M4 + T-nut into the tower's outer slot |
| Skirts_Bottom | bottom_skirt_grill / badge / fan60_intake / power_RIGHT | 2 / 2 / 1 / 1 | Front face down. M4 × 10 through the front holes. |
| Skirts_Top | top_skirt_grill / fan60_intake | 5 / 1 | |
| Skirts_Top | logo_badge | 3 | 2 skirts + toolhead |
| Base_Power | power_inlet_box, psu_bracket, psu_terminal_cover, bed_standoff | 1, 1, 1, 3 | |
| Top_Electronics | skr_pico_pi3b_tray, top_channel + lid | 1, 1 + 1 | |
| Toolhead | effector_v6, groove_clamp, dv_shroud, dv_duct_4010 | 1, 1, 1, 2 | ABS/ASA |
| Extruder | side_spool_extruder_bracket | 1 | Tower B top corner, 4× M4 into heat-set inserts |
| Misc | cable_clip_2020 | 8 | |
| **DXFs** | bottom_panel, bed_deck_panel, top_panel, lid_panel | 1 each | 3 mm black ACM or plywood, about 430 × 370 mm |

All printed parts fit the Kossel's Ø230 mm print area. Use PETG at minimum, and ABS/ASA for the toolhead and the power box.

## Toolhead (DV style, stock arms)

Doron Velta R2 uses **[CraneFly by chirpy](https://github.com/chirpy2605/voron/tree/main/general/CraneFly)**, which needs FLSUN Q5-style magnetic arms. This kit has its own **Doron Velta style toolhead that keeps your stock 269 mm Kossel arms and full print size**:

* `effector_v6` + `groove_clamp`: the stock arm joints bolt on (`effector.arm_spacing`). The V6-style hotend slides in sideways and the clamp locks it.
* `dv_shroud`: a chamfered hex shroud that hides the heatsink and heater block. It has a front **3010** fan, two faces for **4010 blowers**, and a pocket for the logo badge. Print it effector-face down.
* `dv_duct_4010` ×2: push-fit on each blower outlet, giving two jets at the nozzle.
* `logo_badge_toolhead`: glue into the shroud pocket.

Wire both blowers in parallel to FAN1 (part cooling) and the 3010 to FAN2.

## Files

```
CAD/build_dvf.py, CAD/v2_parts.py   parametric part generator (FreeCAD 1.x Python)
CAD/build_assembly.py               full printer assembly
CAD/params.json                     all dimensions
CAD/DVF_ACLP_Assembly.step / .FCStd full assembled printer (open in SolidWorks/Fusion/FreeCAD)
CAD/DVF_ACLP_Assembly.obj / .mtl   same assembly in colour (red printed / black stock) for 3D Viewer or Blender
CAD/DVF_ACLP.FCStd                  all parts in print orientation
CAD/STEP/*.step                     each part (and both panels) as editable solids
DXFs/*.dxf                          bottom and top panel cut files
STLs/**                             print files, _xN = quantity
Firmware/printer.cfg, Docs/wiring.md, BOM.md
```

Rebuild after changing params:

```
"C:\Program Files\FreeCAD 1.1\bin\python.exe" CAD/build_dvf.py
"C:\Program Files\FreeCAD 1.1\bin\python.exe" CAD/build_assembly.py
```

## Printed parts

![parts](images/parts_overview.png)

## Credits and license

Inspired by [Doron Velta by rogerlz](https://github.com/rogerlz/Doron-Velta) (fork: [Xanjip32/Doron-Velta](https://github.com/Xanjip32/Doron-Velta)). The parts are new designs in that style, sized for Kossel 2020 extrusions. The Klipper config is based on Klipper's `printer-anycubic-kossel-plus-2017.cfg`. GPL-3.0. This is not an official Voron, Doron Velta or Anycubic project.
