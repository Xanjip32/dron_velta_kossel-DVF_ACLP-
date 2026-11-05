# DVF-ACLP: Doron Velta outer design for the Anycubic Kossel Linear Plus

This kit gives the Anycubic Kossel Linear Plus the outside look of [Doron Velta by rogerlz](https://github.com/rogerlz/Doron-Velta): boxed honeycomb skirts with the DV logo, a closed top and bottom section, tower pillars, a DV toolhead look and the original DV spool holder. It is resized to fit the stock Kossel 2020 frame, rails, arms, motors and bed. The controller is a BTT SKR Pico + Raspberry Pi 3B.

**Colour scheme (Doron Velta style):** printed parts in **black**. Files starting with **`[a]`** (accent) go in **red**: the slanted pillar bands and the logos. The stock Kossel parts stay **silver** (aluminium frame, rails, arms). **v0.5, not yet built or fit-tested.**

## What's in the repo

```
STLs/      print files, _xN = how many to print
STEP/DVF_ACLP_FULL_ASSEMBLY.step   whole printer assembled (open in SolidWorks / Fusion / FreeCAD)
STEP/parts/                        every printed part as an editable solid
STEP/panels_cut_3mm/               bottom, bed deck, top deck and lid panels: cut from 3 mm black ACM or plywood
```

## Print list

| Folder | Part | Qty |
|---|---|---:|
| 00_Fit_Test | deep_skirt_fit_test (print first, check on both lower rails) | 1 |
| Corners | corner_bottom_motor, corner_top_idler, corner_top_cap | 3 each |
| Pillars | pillar_lower, pillar_upper (black) | 3 each |
| Pillars | [a]pillar_band_lower, [a]pillar_band_upper (red, slanted ends like the DV pillars) | 3 each |
| Skirts_Bottom | bottom_skirt_grill_logo / fan60_intake / power_RIGHT | 4 / 1 / 1 |
| Skirts_Top | top_skirt_grill_logo / fan60_intake | 5 / 1 |
| DV_Logo | [a]dv_logo_insert (original DV logo, pushes into the skirt from behind) | 10 |
| DV_Logo | [a]dv_logo_badge_toolhead | 1 |
| Base_Power | power_inlet_box, psu_bracket, psu_terminal_cover / bed_standoff | 1 each / 3 |
| Top_Electronics | skr_pico_pi3b_tray, top_channel, top_channel_lid | 1 each |
| Toolhead | effector_v6, groove_clamp, dv_shroud / dv_duct_4010 | 1 each / 2 |
| Extruder | side_extruder_spool_mount (tower B top corner) + dv_spool_holder_ORIGINAL (unchanged DV file, 2× M5) | 1 + 1 |
| Misc | cable_clip_2020 | 8 |

Print the corners, skirts and spool mount in PETG or better, and the toolhead and power inlet box in ABS/ASA. The slanted pillar pieces are already turned so the flat end is on the bed. Every printed part fits the Kossel's Ø230 mm bed.

## Main bought parts

* BTT SKR Pico v1.0 and Raspberry Pi 3B
* 12 V 215 × 115 × 50 mm box PSU
* IEC C14 inlet with fuse + rocker switch (47.5 × 27.5 mm cut-out)
* 2× 60 mm 12 V fans (top and bottom intake), 1× 3010 fan, 2× 4010 blowers (toolhead)
* Inserts: M2.5, M3 and M4 heat-set inserts, plus M5 (Ø6.4) for the spool holder
* Screws: M3, M4 and M5 screws and M4 2020 T-nuts

The mains wiring (inlet → fuse/switch → PSU, earth to PSU and frame) must be done unplugged, with the terminal cover fitted.

## Credits and license

The outer design follows **Doron Velta by rogerlz** (GPL-3.0, fork: [Xanjip32/Doron-Velta](https://github.com/Xanjip32/Doron-Velta)). The DV logo insert and the spool holder are the original Doron Velta files. Every other part is remodelled to fit the Kossel Linear Plus. This kit is also GPL-3.0. It is not an official Voron, Doron Velta or Anycubic project.
