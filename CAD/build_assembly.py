"""Full DVF-ACLP assembly: simplified stock Kossel Linear Plus + every printed part in place.

    "<FreeCAD>/bin/python.exe" CAD/build_assembly.py

Writes CAD/DVF_ACLP_Assembly.step and CAD/DVF_ACLP_Assembly.FCStd.
Stock parts (frame, corners, rails, bed, arms, motors, boards, fans, hotend) are simple
reference blocks for visualising fit, not exact Anycubic geometry.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import FreeCAD as App  # noqa: E402
import Import  # noqa: E402
import Part  # noqa: E402

import build_dvf as D  # noqa: E402

V, P, box, cyl = App.Vector, D.P, D.box, D.cyl
ext = P["frame"]["extrusion"]
s_ = P["skirt"]
e_ = P["effector"]

# ---- stock frame geometry (approximate Kossel Linear Plus) ----
R_TOWER = 195.0            # tower extrusion centre radius
D_EDGE = 135.0             # horizontal rail centre-line distance from centre
FOOT = P["foot"]["thickness"]
Z_LOW = FOOT + ext / 2     # lower bottom rail centre
Z_HIGH = Z_LOW + P["frame"]["bottom_rail_pitch"]
TOWER_H = 720.0
Z_TOP = FOOT + TOWER_H - 15
Z_BED = Z_HIGH + ext / 2 + 8
ARM = 269.0
DELTA_R = 134.4
TOWERS = {"A": 210, "B": 330, "C": 90}
FACES = [270, 30, 150]     # outward normals of the three sides


def unit(a):
    return V(math.cos(math.radians(a)), math.sin(math.radians(a)), 0)


def place(shape, o, ex, ey, ez):
    s = shape.copy()
    m = App.Matrix(ex.x, ey.x, ez.x, o.x, ex.y, ey.y, ez.y, o.y,
                   ex.z, ey.z, ez.z, o.z, 0, 0, 0, 1)
    s.transformShape(m)
    return s


def bar(p0, p1, r):
    d = p1 - p0
    return Part.makeCylinder(r, d.Length, p0, d)


Z = V(0, 0, 1)
groups = {}


def add(group, name, shape):
    groups.setdefault(group, []).append((name, shape))


# ================================================================ stock frame
for t, a in TOWERS.items():
    c = unit(a) * R_TOWER
    add("Stock_Frame", f"tower_{t}", box(c.x - 10, c.y - 10, FOOT, 20, 20, TOWER_H))
    r, tn = unit(a), unit(a + 90)
    rail_c = c - r * 14
    add("Stock_Frame", f"mgn12_rail_{t}",
        place(box(-6, 0, -4, 12, Z_TOP - 60 - Z_HIGH, 8), rail_c + Z * (Z_HIGH + 20), tn, Z, r))
vertex = {f: unit(f) for f in FACES}
for i, f in enumerate(FACES):
    n = unit(f)
    u = V(math.sin(math.radians(f)), -math.cos(math.radians(f)), 0)
    L = 2 * D_EDGE * math.sqrt(3)
    rail_len = 300.0
    for zc, tag in ((Z_LOW, "low"), (Z_HIGH, "high"), (Z_TOP, "top")):
        add("Stock_Frame", f"rail_{tag}_{i}",
            place(box(-rail_len / 2, -10, -10, rail_len, 20, 20), n * D_EDGE + Z * zc, u, n.cross(u) * -1 if False else n, Z)
            if False else place(box(-rail_len / 2, -10, -10, rail_len, 20, 20), n * D_EDGE + Z * zc, u, Z.cross(u), Z))

# corner housings: hull of the tower and both rail ends
for t, a in TOWERS.items():
    vtx = unit(a) * (2 * D_EDGE)
    pts = []
    for da in (150, -150):
        d = unit(a + da)
        side = unit(a + da + 90)
        for k in (-1, 1):
            for L in (0, 83):
                p = vtx + d * L + side * (12 * k)
                pts.append((p.x, p.y))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    hull = []
    for p in pts:
        while len(hull) >= 2 and ((hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1]) -
                                  (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0])) <= 0:
            hull.pop()
        hull.append(p)
    hull2 = []
    for p in hull:
        while len(hull2) >= 2 and ((hull2[-1][0] - hull2[-2][0]) * (p[1] - hull2[-2][1]) -
                                   (hull2[-1][1] - hull2[-2][1]) * (p[0] - hull2[-2][0])) <= 0:
            hull2.pop()
        hull2.append(p)
    add("Stock_Frame", f"corner_bottom_{t}", D.prism_xy(hull2, FOOT, Z_HIGH + 12 - FOOT))
    add("Stock_Frame", f"corner_top_{t}", D.prism_xy(hull2, Z_TOP - 14, 28))
    # stepper (bottom) and idler (top) blocks inside the corners
    c = unit(a) * (R_TOWER - 30)
    add("Stock_Motion", f"nema17_{t}",
        place(box(-21, -21, 0, 42, 42, 40), c + Z * (Z_HIGH - 10), unit(a + 90), Z.cross(unit(a + 90)) * -1, Z)
        if False else box(c.x - 21, c.y - 21, FOOT + 4, 42, 42, 40))

add("Stock_Bed", "heated_bed_230", cyl(115, 3, 0, 0, Z_BED))
add("Stock_Bed", "glass_220", cyl(110, 3, 0, 0, Z_BED + 3))

# ================================================================ motion system
Z_EFF = Z_BED + 6 + 90            # effector bottom face
joint_z_eff = Z_EFF + e_["tab_h"] / 2
dz = math.sqrt(ARM ** 2 - DELTA_R ** 2)
for t, a in TOWERS.items():
    r, tn = unit(a), unit(a + 90)
    jz = joint_z_eff + dz
    cj = r * (DELTA_R + e_["offset"])
    add("Stock_Motion", f"carriage_{t}",
        place(box(-13.5, -22.5, 0, 27, 45, 13), r * (R_TOWER - 10 - 8) + Z * jz, tn, Z, r * -1))
    add("Stock_Motion", f"carriage_joint_bar_{t}",
        place(box(-(e_["arm_spacing"] / 2 + 6), -6, 0, e_["arm_spacing"] + 12, 12, 16),
              cj + Z * jz, tn, Z, r))
    for k in (-1, 1):
        p0 = r * e_["offset"] + tn * (k * e_["arm_spacing"] / 2) + Z * joint_z_eff
        p1 = cj + tn * (k * e_["arm_spacing"] / 2) + Z * jz
        add("Stock_Motion", f"arm_{t}{'LR'[k > 0]}", bar(p0, p1, 3))
    # top endstop boards
    add("Stock_Motion", f"endstop_switch_{t}",
        place(box(-13, -8, 0, 26, 16, 6), r * (R_TOWER - 22) + Z * (Z_TOP - 62), tn, Z, r * -1))

# hotend (V6-style) + fans
Z_NOZ = Z_EFF - e_["heatsink_h"] - 22
add("Stock_Toolhead", "hotend_heatsink", cyl(e_["heatsink_d"] / 2, e_["heatsink_h"], 0, 0, Z_EFF - e_["heatsink_h"]))
add("Stock_Toolhead", "hotend_groove", cyl(6, e_["plate_t"], 0, 0, Z_EFF))
add("Stock_Toolhead", "hotend_collar", cyl(8, e_["collar_h"], 0, 0, Z_EFF + e_["plate_t"]))
add("Stock_Toolhead", "heater_block", box(-8, -10, Z_NOZ + 5, 16, 20, 11))
add("Stock_Toolhead", "nozzle", Part.makeCone(0.6, 4, 5, V(0, 0, Z_NOZ), Z))
slot_ang = D.tool_frame()[1]
fan_dir = unit(slot_ang + 90 + 180) * -1  # shroud inlet faces +X rotated by slot+90
fan_dir = unit(slot_ang + 90)
add("Stock_Toolhead", "fan_3010",
    place(box(-15, -15, 0, 30, 30, 10), fan_dir * 16 + Z * (Z_EFF - e_["heatsink_h"] / 2),
          unit(slot_ang + 180), Z, fan_dir))
duct_dir = unit(slot_ang + 90 + 180)
add("Stock_Toolhead", "fan_5015",
    place(box(-7.5, -25, 0, 15, 50, 50), duct_dir * 42 + Z * (Z_NOZ + 19 + 8),
          Z.cross(duct_dir * -1) * -1, duct_dir, Z))
add("Stock_Toolhead", "bowden_tube", cyl(2, 260, 0, 0, Z_EFF + 12))

# ================================================================ printed parts
t = s_["thickness"]
W = s_["span"] / 2 - s_["joint_gap"] / 2
bottom_set = [("plain", "badge"), ("plain", "badge"), ("plain", "ports")]
shapes = {v: D.bottom_skirt(v) for v in ("plain", "badge", "ports")}
top = D.top_skirt()
badge = D.logo_badge()
y_low = s_["bottom_overlap_below"] + ext / 2
z0_bottom = Z_LOW - y_low
z0_top = Z_TOP - (s_["top_overlap_below"] + ext / 2)
for i, f in enumerate(FACES):
    n = unit(f)
    ex = V(math.sin(math.radians(f)), -math.cos(math.radians(f)), 0)
    front = n * (D_EDGE + ext / 2 + t)
    for j, (variant, xoff) in enumerate(zip(bottom_set[i], (-s_["span"] / 2, s_["joint_gap"] / 2))):
        o = front + ex * xoff + Z * z0_bottom
        add("Printed_Skirts", f"bottom_skirt_{variant}_{i}{j}", place(shapes[variant], o, ex, Z, n * -1))
        if variant == "badge":
            pitch = P["frame"]["bottom_rail_pitch"]
            by = y_low + pitch / 2
            bx = W - 4 - s_["badge_r"]
            c = o + ex * bx + Z * by - n * s_["badge_depth"]
            add("Printed_Skirts", f"logo_badge_{i}", place(badge, c, ex * -1, Z, n))
        o = front + ex * xoff + Z * z0_top
        add("Printed_Skirts", f"top_skirt_{i}{j}", place(top, o, ex, Z, n * -1))

for tname, a in TOWERS.items():
    vtx = unit(a) * (2 * D_EDGE)
    add("Printed_Frame", f"foot_{tname}",
        place(D.foot(), vtx, unit(a + 180), unit(a + 270), Z).translated(V(0, 0, 0)))
    r, tn = unit(a), unit(a + 90)
    add("Printed_Frame", f"endstop_mount_{tname}",
        place(D.endstop_mount(), unit(a) * (R_TOWER - 10) + Z * (Z_TOP - 30), tn, Z * -1, r * -1))
    clip = D.cable_clip()
    for k, zc in enumerate((200, 420)):
        add("Printed_Frame", f"cable_clip_{tname}{k}",
            place(clip, unit(a) * (R_TOWER + 10) + Z * zc, tn, Z, r))

# feet go under the frame: shift the whole frame up already accounted (FOOT)

# toolhead
add("Printed_Toolhead", "effector_v6", D.effector().translated(V(0, 0, Z_EFF)))
clamp = D.groove_clamp()
ax = unit(slot_ang)
clamp.rotate(V(0, 0, 0), ax, 180)
ct = e_["collar_h"] + 2.5
add("Printed_Toolhead", "groove_clamp", clamp.translated(V(0, 0, Z_EFF + ct + e_["plate_t"] - 0.3)))
add("Printed_Toolhead", "hotend_shroud_3010",
    D.hotend_shroud(printable=False).translated(V(0, 0, Z_EFF - e_["heatsink_h"])))
rd = duct_dir
add("Printed_Toolhead", "part_fan_duct_5015",
    place(D.part_fan_duct(printable=False), rd * 42 + Z * (Z_NOZ + 19), V(-rd.y, rd.x, 0) * -1, rd * -1, Z))

# electronics on the inside of the ports face (FACES[2])
f = FACES[2]
n = unit(f)
ex = V(math.sin(math.radians(f)), -math.cos(math.radians(f)), 0)
el = P["electronics"]
zc = (Z_LOW + Z_HIGH) / 2 - el["plate_h"] / 2
o = n * (D_EDGE - ext / 2) - ex * (el["plate_w"] / 2) + Z * zc
add("Printed_Electronics", "skr_pico_pi3b_plate", place(D.pico_pi_plate(), o, ex, Z, n * -1))
for k, (nm, xc) in enumerate((("SKR_Pico", el["plate_w"] * 0.25), ("Raspberry_Pi_3B", el["plate_w"] * 0.75))):
    pcb = box(xc - 42.5, el["plate_h"] / 2 - 28, 4 + el["standoff_h"], 85, 56, 1.6)
    add("Stock_Electronics", nm, place(pcb, o, ex, Z, n * -1))
    comp = box(xc - 30, el["plate_h"] / 2 - 20, 5.6 + el["standoff_h"], 50, 40, 12 if k else 6)
    add("Stock_Electronics", nm + "_components", place(comp, o, ex, Z, n * -1))
fb = D.fan_bracket_40()
o2 = n * (D_EDGE - ext / 2 - 24) + ex * (el["plate_w"] / 2 + 25) + Z * (Z_HIGH + ext / 2)
add("Printed_Electronics", "fan_bracket_4010", place(fb, o2, ex, n * -1, Z.cross(ex).cross(n * -1) * 0 + Z)
    if False else place(fb, n * (D_EDGE + 0) + ex * (el["plate_w"] / 2 + 25) + Z * (Z_HIGH + ext / 2),
                        ex * -1, n * -1, Z))

# extruder on the top rail of FACES[0], spool holder on FACES[1]
for f, nm in ((FACES[0], "bowden_extruder_mount"), (FACES[1], "spool_holder")):
    n = unit(f)
    ex = V(math.sin(math.radians(f)), -math.cos(math.radians(f)), 0)
    if nm == "bowden_extruder_mount":
        o = n * (D_EDGE + ext / 2 + 5) + Z * (Z_TOP + ext / 2)
        add("Printed_Extruder", nm, place(D.bowden_mount(), o + ex * 60, ex, n, Z))
        add("Stock_Extruder", "extruder_nema17", place(box(-21, 2, 5, 42, 42, 40), o + ex * 60, ex, n, Z))
    else:
        o = n * (D_EDGE - 10) + Z * (Z_TOP + ext / 2)
        add("Printed_Extruder", nm, place(D.spool_holder(printable=False), o, ex, n, Z))
        add("Stock_Extruder", "filament_spool",
            cyl(100, 65, 0, 0, 0, (0, 1, 0)).cut(cyl(28, 70, 0, -1, 0, (0, 1, 0))).transformGeometry(
                App.Matrix(ex.x, n.x, 0, 0, ex.y, n.y, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)).translated(
                o + n * 52 + Z * 90 + Z * 0 - Z * 0))

# ================================================================ export
doc = App.newDocument("DVF_ACLP_Assembly")
roots = []
for g, items in groups.items():
    grp = doc.addObject("App::Part", g)
    roots.append(grp)
    for nm, sh in items:
        o = doc.addObject("Part::Feature", nm)
        o.Shape = sh
        grp.addObject(o)
doc.recompute()
root = Path(__file__).resolve().parent
doc.saveAs(str(root / "DVF_ACLP_Assembly.FCStd"))
Import.export(roots, str(root / "DVF_ACLP_Assembly.step"))
for g, items in groups.items():
    print(f"{g:22s} {len(items):3d} parts")
print("frame height", round(FOOT + TOWER_H), "effector z", round(Z_EFF), "nozzle z", round(Z_NOZ))
