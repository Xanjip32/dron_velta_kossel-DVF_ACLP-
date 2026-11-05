"""Full DVF-ACLP assembly: printed corners, power base, top electronics bay, skirts and
toolhead on the stock Kossel Linear Plus extrusions, rails, arms and bed.

    "<FreeCAD>/bin/python.exe" CAD/build_assembly.py

Writes CAD/DVF_ACLP_Assembly.step and CAD/DVF_ACLP_Assembly.FCStd.
Stock/bought parts (extrusions, rails, motors, PSU, boards, fans, hotend, arms) are
simple reference blocks for checking fit and layout.
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
Z = V(0, 0, 1)
ext = P["frame"]["extrusion"]
s_, e_, c_, el, pw, ch = (P[k] for k in ("skirt", "effector", "corner", "electronics", "power", "channel"))
g = D.frame_geo()
D_EDGE, R_TOWER = g["d_edge"], g["r_tower"]
PANEL_T = P["panel"]["thickness"]

# ---- heights (all derived from the printed corners) ----
BD = c_["base_drop"]
Z_LOW, Z_HIGH = BD + ext / 2, BD + P["frame"]["bottom_rail_pitch"] + ext / 2
ZM = 26                                   # motor centre in the bottom corner
TZ0 = ZM + 21 + 5                         # tower bottom
TOWER_TOP = TZ0 + P["frame"]["tower_len"]
Z_TC = TOWER_TOP - c_["tower_socket"]     # top corner bottom
Z_TOP_RAIL = Z_TC + c_["top_h"] - 4 - ext / 2
Z_TOP_PANEL = Z_TC + c_["top_h"]
Z_BED = Z_HIGH + ext / 2 + PANEL_T + P["enclosure"]["bed_gap"]
ARM = 269.0
TOWERS = {"A": 210, "B": 330, "C": 90}
FACES = [270, 30, 150]

groups = {}


def add(group, name, shape):
    groups.setdefault(group, []).append((name, shape))


def unit(a):
    return V(math.cos(math.radians(a)), math.sin(math.radians(a)), 0)


def place(shape, o, ex, ey, ez):
    s = shape.copy()
    s.transformShape(App.Matrix(ex.x, ey.x, ez.x, o.x, ex.y, ey.y, ez.y, o.y,
                                ex.z, ey.z, ez.z, o.z, 0, 0, 0, 1))
    return s


def corner_frame(a, z=0):
    return unit(a) * (2 * D_EDGE) + Z * z, unit(a + 180), unit(a + 270), Z


def bar(p0, p1, r):
    d = p1 - p0
    return Part.makeCylinder(r, d.Length, p0, d)


# ================================================================ printed corners + stock inside them
cb, ct = D.corner_bottom(), D.corner_top()
for t, a in TOWERS.items():
    o, ex, ey, ez = corner_frame(a)
    add("Printed_Corners", f"corner_bottom_{t}", place(cb, o, ex, ey, ez))
    add("Printed_Corners", f"corner_top_{t}", place(ct, o + Z * Z_TC, ex, ey, ez))
    xt = c_["tower_from_vertex"]
    add("Stock_Frame", f"tower_{t}", place(box(xt - 10, -10, TZ0, 20, 20, TOWER_TOP - TZ0), o, ex, ey, ez))
    add("Stock_Frame", f"mgn12_rail_{t}",
        place(box(xt + 10, -6, TZ0 + 45, 8, 12, Z_TC - TZ0 - 55), o, ex, ey, ez))
    add("Stock_Motion", f"nema17_{t}", place(box(xt + 6 - 40, -21, 5, 40, 42, 42), o, ex, ey, ez))
    add("Stock_Motion", f"pulley_{t}", place(cyl(8, 10, xt + 16, 0, ZM, (1, 0, 0)), o, ex, ey, ez))
    add("Stock_Motion", f"idler_{t}", place(cyl(5, 8, xt + 16, 0, Z_TC + 18, (1, 0, 0)), o, ex, ey, ez))
    for k in (-1, 1):
        add("Stock_Motion", f"belt_{t}{k}",
            place(box(xt + 18, k * 7 - 0.5, ZM, 6, 1, Z_TC + 18 - ZM), o, ex, ey, ez))
    add("Stock_Motion", f"endstop_board_{t}", place(box(xt + 14, 12, Z_TC - 6, 12, 28, 6), o, ex, ey, ez))

for i, f in enumerate(FACES):
    n = unit(f)
    u = unit(f + 90)
    for zc, tag in ((Z_LOW, "low"), (Z_HIGH, "high"), (Z_TOP_RAIL, "top")):
        add("Stock_Frame", f"rail_{tag}_{i}",
            place(box(-P["frame"]["rail_len"] / 2, -10, -10, P["frame"]["rail_len"], 20, 20),
                  n * D_EDGE + Z * zc, u, Z.cross(u), Z))

# panels (ACM / plywood from DXFs)
add("Panels", "bottom_panel", D.panel("bottom").translated(V(0, 0, BD - PANEL_T)))
add("Panels", "top_panel", D.panel("top").translated(V(0, 0, Z_TOP_PANEL)))
add("Stock_Bed", "heated_bed_230", cyl(115, 3, 0, 0, Z_BED))
add("Stock_Bed", "glass_220", cyl(110, 3, 0, 0, Z_BED + 3))

# ================================================================ enclosed DV sections
G = D._sec()
en = P["enclosure"]
DEP = en["skirt_depth"]
W = s_["span"] / 2 - s_["joint_gap"] / 2
badge = D.logo_badge()
bottom_set = [("plain", "badge"), ("fan", "badge"), ("power", "plain")]   # index 0 = viewer's right
top_set = [("plain", "plain"), ("plain", "plain"), ("fan", "plain")]
cache = {}
for i, f in enumerate(FACES):
    n = unit(f)
    ex = unit(f - 90)
    front = n * (D_EDGE + ext / 2 + DEP)
    for sec, sets, z0 in (("bottom", bottom_set, G["bottom_z0"]), ("top", top_set, G["top_z0"])):
        for j, (variant, xoff) in enumerate(zip(sets[i], (-s_["span"] / 2, s_["joint_gap"] / 2))):
            key = (sec, variant)
            if key not in cache:
                cache[key] = D.deep_skirt(sec, variant)
            sk = cache[key]
            o = front + ex * xoff + Z * z0
            add("Printed_Skirts", f"{sec}_skirt_{variant}_{i}{j}", place(sk, o, ex, Z, n * -1))
            Hs = G["bottom_z1"] - G["bottom_z0"] if sec == "bottom" else G["lid_z"] - G["top_z0"]
            cy = Hs / 2 + (4 if sec == "top" else 0)
            if variant == "fan":
                add("Stock_Fans", f"fan60_{sec}", place(box(W / 2 - 30, cy - 30, 2.4, 60, 60, 15), o, ex, Z, n * -1))
            if variant == "badge":
                c = o + ex * (W - 6 - s_["badge_r"]) + Z * cy - n * s_["badge_depth"]
                add("Printed_Skirts", f"logo_badge_{i}", place(badge, c, ex * -1, Z, n))
            if variant == "power":
                pc = o + ex * (W / 2) + Z * ((G["zlow"] + G["zhigh"]) / 2 - z0)
                add("Printed_Power", "power_inlet_box", place(D.power_inlet_box(), pc, ex * -1, Z, n))
                add("Stock_Power", "iec_c14_switch_inlet",
                    place(box(-pw["iec_w"] / 2, -pw["iec_h"] / 2, pw["box_d"] - 30, pw["iec_w"],
                              pw["iec_h"], 33), pc, ex * -1, Z, n))

# decks, lid, corner caps, pillars
add("Panels", "bed_deck", D.deck_face().extrude(V(0, 0, PANEL_T)).translated(V(0, 0, G["bed_deck"])))
add("Panels", "lid", D.lid_face().extrude(V(0, 0, PANEL_T)).translated(V(0, 0, G["lid_z"])))
bs = D.bed_standoff()
for a in (90, 210, 330):
    p_ = unit(a) * en["bed_mount_r"] + Z * (G["bed_deck"] + PANEL_T)
    add("Printed_Power", f"bed_standoff_{a}", bs.translated(p_))
cap, pil = D.corner_cap(), D.pillar_cover()
for tn_, a in TOWERS.items():
    o, ex, ey, ez = corner_frame(a)
    add("Printed_Corners", f"corner_cap_{tn_}", place(cap, o + Z * (Z_TOP_PANEL + PANEL_T), ex, ey, ez))
    for k in range(int((Z_TC - TZ0 - c_["tower_socket"]) // en["pillar_seg"])):
        z = TZ0 + c_["tower_socket"] + k * en["pillar_seg"]
        add("Printed_Corners", f"pillar_{tn_}{k}",
            place(pil, o + ex * (c_["tower_from_vertex"] - 10) + Z * z, ex, ey, ez))

# ================================================================ power base (face 150)
n = unit(150)
u = unit(240)
cen = n * (D_EDGE - ext / 2 - 8 - pw["psu_w"] / 2)
add("Stock_Power", "psu_12v_360w",
    place(box(-pw["psu_l"] / 2, -pw["psu_w"] / 2, 0, pw["psu_l"], pw["psu_w"], pw["psu_h"]),
          cen + Z * BD, u * -1, n, Z))
add("Printed_Power", "psu_bracket",
    place(D.psu_bracket(), cen - u * (pw["psu_l"] / 2 + 4) + Z * BD, n, u, Z))
cover = D.psu_terminal_cover()
cover.rotate(V(0, 0, 0), V(1, 0, 0), 180)
cover.translate(V(0, 0, pw["psu_h"] + 6))
add("Printed_Power", "psu_terminal_cover",
    place(cover, cen + u * (pw["psu_l"] / 2 + 14) + Z * BD, n, u, Z))

# ================================================================ top electronics bay (under the lid)
zt = Z_TOP_PANEL + PANEL_T
add("Printed_Top_Bay", "skr_pico_pi3b_tray",
    D.pico_pi_plate().translated(V(-el["plate_w"] / 2, -el["plate_h"] / 2, zt)))
for k, (nm, xc) in enumerate((("SKR_Pico", -el["plate_w"] / 4), ("Raspberry_Pi_3B", el["plate_w"] / 4))):
    zb = zt + 4 + el["standoff_h"]
    add("Stock_Electronics", nm, box(xc - 42.5, -28, zb, 85, 56, 1.6))
    add("Stock_Electronics", nm + "_components", box(xc - 30, -20, zb + 1.6, 50, 40, 16 if k else 6))
aA = TOWERS["A"]
r = unit(aA)
duct = r * (2 * D_EDGE - (c_["truncate"] + 21)) + Z * zt
dvec = V(-el["plate_w"] / 2, 0, zt) - duct
dvec.normalize()
tl = ch["top_len"]
add("Printed_Top_Bay", "top_channel", place(D.wiring_channel(tl), duct, dvec.cross(Z), dvec, Z))
add("Printed_Top_Bay", "top_channel_lid",
    place(D.wiring_channel_lid(tl), duct + Z * (ch["depth"] + 2 + 1.6), dvec.cross(Z) * -1, dvec, Z * -1))

# ================================================================ side spool + extruder (tower B top corner)
aB = TOWERS["B"]
o, ex, ey, ez = corner_frame(aB)
bo = o + ex * c_["truncate"] + Z * Z_TC
bx_, by_ = ex * -1, ey * -1
add("Printed_Extruder", "side_spool_extruder_bracket", place(D.side_spool_extruder(), bo, bx_, by_, Z))
add("Stock_Extruder", "extruder_nema17", place(box(7, 24, 4, 42, 40, 42), bo, bx_, by_, Z))
spool = cyl(100, 65, 42, -10, 46, (1, 0, 0)).cut(cyl(27, 70, 40, -10, 46, (1, 0, 0)))
add("Stock_Extruder", "filament_spool_1kg", place(spool, bo, bx_, by_, Z))

# ================================================================ motion + toolhead
xt = c_["tower_from_vertex"]
cj_r = 2 * D_EDGE - (xt + 10 + 8 + 13 + 6)          # carriage joint radius
delta_r = cj_r - e_["offset"]
dz = math.sqrt(ARM ** 2 - delta_r ** 2)
Z_EFF = Z_BED + 6 + 100 + e_["heatsink_h"] + 22
jz_e = Z_EFF + e_["tab_h"] / 2
for tn_, a in TOWERS.items():
    rr, tn = unit(a), unit(a + 90)
    jz = jz_e + dz
    add("Stock_Motion", f"carriage_{tn_}",
        place(box(-13.5, -22.5, 0, 27, 45, 13), rr * (2 * D_EDGE - xt - 10 - 8) + Z * jz, tn * -1, Z, rr * -1))
    add("Stock_Motion", f"carriage_joint_bar_{tn_}",
        place(box(-(e_["arm_spacing"] / 2 + 6), -6, 0, e_["arm_spacing"] + 12, 12, 6),
              rr * cj_r + Z * jz, tn, Z, rr))
    for k in (-1, 1):
        p0 = rr * e_["offset"] + tn * (k * e_["arm_spacing"] / 2) + Z * jz_e
        p1 = rr * cj_r + tn * (k * e_["arm_spacing"] / 2) + Z * jz
        add("Stock_Motion", f"arm_{tn_}{k}", bar(p0, p1, 3))

Z_NOZ = Z_EFF - e_["heatsink_h"] - 22
add("Stock_Toolhead", "hotend_heatsink", cyl(e_["heatsink_d"] / 2, e_["heatsink_h"], 0, 0, Z_EFF - e_["heatsink_h"]))
add("Stock_Toolhead", "heater_block", box(-8, -10, Z_NOZ + 5, 16, 20, 11))
add("Stock_Toolhead", "nozzle", Part.makeCone(0.6, 4, 5, V(0, 0, Z_NOZ), Z))
tf = D._th_frame()
th = P["toolhead_dv"]
ap = th["hex_r"] * math.cos(math.radians(30))
fd = unit(tf["fan"])
add("Stock_Toolhead", "fan_3010",
    place(box(-15, -15, 0, 30, 30, 10), fd * ap + Z * (Z_EFF - th["fan_z"]), fd.cross(Z) * -1, Z, fd))
for k, b in enumerate(tf["blowers"]):
    rb, tb = unit(b), unit(b + 90)
    zb = Z_EFF - th["blower_z"]
    add("Stock_Toolhead", f"blower_4010_{k}",
        place(box(-20, -20, 0, 40, 40, 10), rb * ap + Z * zb, tb, Z, rb))
    out = rb * (ap + 5) + tb * (th["blower_out_offset"] * (1 if k else -1)) + Z * (zb - 20)
    dvec = V(-out.x, -out.y, 0)
    dvec.normalize()
    add("Printed_Toolhead", f"dv_duct_{k}", place(D.th_duct(printable=False), out, dvec.cross(Z), dvec, Z))
add("Printed_Toolhead", "effector_v6", D.effector().translated(V(0, 0, Z_EFF)))
clamp = D.groove_clamp()
clamp.rotate(V(0, 0, 0), unit(tf["slot"]), 180)
add("Printed_Toolhead", "groove_clamp",
    clamp.translated(V(0, 0, Z_EFF + e_["collar_h"] + 2.5 + e_["plate_t"] - 0.3)))
add("Printed_Toolhead", "dv_shroud", D.th_shroud(printable=False).translated(V(0, 0, Z_EFF)))
rl, tl_ = unit(tf["logo"]), unit(tf["logo"] + 90)
add("Printed_Toolhead", "logo_badge_toolhead",
    place(D.logo_badge(), rl * (ap - s_["badge_depth"]) + Z * (Z_EFF - th["height"] / 2 + 2), tl_, Z, rl))

# ================================================================ export
doc = App.newDocument("DVF_ACLP_Assembly")
roots = []
for gname, items in groups.items():
    grp = doc.addObject("App::Part", gname)
    roots.append(grp)
    for nm, sh in items:
        ob = doc.addObject("Part::Feature", nm)
        ob.Shape = sh
        grp.addObject(ob)
doc.recompute()
root = Path(__file__).resolve().parent
doc.saveAs(str(root / "DVF_ACLP_Assembly.FCStd"))
Import.export(roots, str(root / "DVF_ACLP_Assembly.step"))
# colour OBJ (+MTL): printed parts red, stock parts black
import MeshPart  # noqa: E402
obj, vi = ["mtllib DVF_ACLP_Assembly.mtl"], 1
for gname, items in groups.items():
    mat = "printed_red" if gname.startswith("Printed") else "stock_black"
    for nm, sh in items:
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.4, AngularDeflection=0.4)
        obj.append(f"o {nm}")
        obj.append(f"usemtl {mat}")
        pts, fcs = m.Topology
        obj += [f"v {p.x:.2f} {p.y:.2f} {p.z:.2f}" for p in pts]
        obj += [f"f {a + vi} {b + vi} {c + vi}" for a, b, c in fcs]
        vi += len(pts)
(root / "DVF_ACLP_Assembly.obj").write_text(chr(10).join(obj) + chr(10))
(root / "DVF_ACLP_Assembly.mtl").write_text(chr(10).join([
    "newmtl printed_red", "Kd 0.80 0.08 0.06", "", "newmtl stock_black", "Kd 0.06 0.06 0.07", ""]))
for gname, items in groups.items():
    print(f"{gname:20s} {len(items):3d}")
print(f"lid height {G['lid_z'] + PANEL_T:.0f} mm, delta_radius ~{delta_r:.1f}, nozzle z {Z_NOZ:.0f}")
