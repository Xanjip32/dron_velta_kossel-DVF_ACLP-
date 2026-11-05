"""Doron Velta Fork for Anycubic Kossel Linear Plus (DVF-ACLP).

Parametric build of every printed part. Run with the Python bundled with FreeCAD 1.x:

    "<FreeCAD>/bin/python.exe" CAD/build_dvf.py            # uses CAD/params.json
    "<FreeCAD>/bin/python.exe" CAD/build_dvf.py my.json    # your own measurements

Outputs: STLs/<group>/<name>_x<qty>.stl, CAD/STEP/<name>.step, CAD/DVF_ACLP.FCStd
All parts are already laid flat in their print orientation (Z up).
"""
import json
import math
import sys
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part

V = App.Vector
ROOT = Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "CAD" / "params.json").read_text())
if __name__ == "__main__" and len(sys.argv) > 1:
    P.update(json.loads(Path(sys.argv[1]).read_text()))

M3, M3_TAP, M4, M5 = 3.4, 2.9, 4.5, 5.4
INSERT_M25 = 3.6  # heat-set insert bore for M2.5
INSERT_M3 = 4.2


# ---------------------------------------------------------------- helpers
def box(x, y, z, dx, dy, dz):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def cyl(r, h, x=0, y=0, z=0, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), V(*d))


def prism_xy(pts, z0, h):
    w = Part.makePolygon([V(x, y, z0) for x, y in list(pts) + [pts[0]]])
    return Part.Face(w).extrude(V(0, 0, h))


def hexagon(x, y, r, z0, h, rot=30):
    a = [math.radians(rot + 60 * i) for i in range(6)]
    return prism_xy([(x + r * math.cos(t), y + r * math.sin(t)) for t in a], z0, h)


def slot(x, y, d, travel, z0, h, axis="y"):
    r = d / 2
    if axis == "y":
        s = box(x - r, y - travel / 2, z0, d, travel, h)
        a, b = (x, y - travel / 2), (x, y + travel / 2)
    else:
        s = box(x - travel / 2, y - r, z0, travel, d, h)
        a, b = (x - travel / 2, y), (x + travel / 2, y)
    return s.fuse(cyl(r, h, a[0], a[1], z0)).fuse(cyl(r, h, b[0], b[1], z0))


def cut_all(shape, tools):
    for t in tools:
        shape = shape.cut(t)
    return shape


def fuse_all(shapes):
    s = shapes[0]
    for t in shapes[1:]:
        s = s.fuse(t)
    return s


def honeycomb(x0, y0, x1, y1, r, wall, z0, h, keepout=()):
    """Hex vents fully inside the rectangle and outside the keepout circles."""
    out = []
    dx = 2 * r * math.cos(math.radians(30)) + wall
    dy = dx * math.sin(math.radians(60))
    row, y = 0, y0 + r
    while y + r <= y1 + 1e-6:
        x = x0 + r + (dx / 2 if row % 2 else 0)
        while x + r <= x1 + 1e-6:
            if all(math.hypot(x - kx, y - ky) > kr + r for kx, ky, kr in keepout):
                out.append(hexagon(x, y, r, z0, h))
            x += dx
        y += dy
        row += 1
    return out


# ---------------------------------------------------------------- skirts
def skirt_blank(width, height, t, chamfer=1.0):
    """Flat panel, front face on the bed (z=0), DV-style chamfered top/bottom edges."""
    c = chamfer
    prof = [(0, c), (c, 0), (height - c, 0), (height, c), (height, t), (0, t)]  # (y, z)
    w = Part.makePolygon([V(0, y, z) for y, z in prof + [prof[0]]])
    return Part.Face(w).extrude(V(width, 0, 0))


def bottom_skirt(variant="plain"):
    s = P["skirt"]
    W = s["span"] / 2 - s["joint_gap"] / 2
    t = s["thickness"]
    pitch = P["frame"]["bottom_rail_pitch"]
    ext = P["frame"]["extrusion"]
    low = s["bottom_overlap_below"]          # panel edge below lower rail top-of-bottom-face
    H = low + pitch + ext + s["top_margin"]
    y_low = low + ext / 2                     # lower rail centre
    y_high = y_low + pitch                    # upper rail centre
    p = skirt_blank(W, H, t)
    # back stiffening rib across the gap between rails
    gap0, gap1 = y_low + ext / 2, y_high - ext / 2
    holes = []
    for x in (s["mount_inset"], W - s["mount_inset"]):
        for y in (y_low, y_high):
            holes.append(slot(x, y, M4, s["slot_travel"], -1, t + 2))
    keep = [(x, y, 7) for x in (s["mount_inset"], W - s["mount_inset"]) for y in (y_low, y_high)]
    vx0, vx1 = 6, W - 6
    if variant == "badge":
        bx, by = W - 4 - s["badge_r"], (gap0 + gap1) / 2   # sits next to the centre joint
        holes.append(hexagon(bx, by, s["badge_r"] + 0.2, -1, 1 + s["badge_depth"]))
        keep.append((bx, by, s["badge_r"] + 3))
    if variant == "ports":
        pw, ph = s["port_w"], min(s["port_h"], gap1 - gap0 - 2)
        px, py = W / 2 - pw / 2, (gap0 + gap1) / 2 - ph / 2
        holes.append(box(px, py, -1, pw, ph, t + 2))
        keep.append((W / 2, (gap0 + gap1) / 2, pw / 2 + 4))
    if gap1 - gap0 > 8:
        holes += honeycomb(vx0, gap0 + 1.5, vx1, gap1 - 1.5, s["hex_r"], s["hex_wall"],
                           -1, t + 2, keep)
    holes += honeycomb(vx0, 2.5, vx1, max(2.5, y_low - ext / 2 - 1.5), s["hex_r"],
                       s["hex_wall"], -1, t + 2, keep) if y_low - ext / 2 > 12 else []
    return cut_all(p, holes)


def top_skirt():
    s = P["skirt"]
    W = s["span"] / 2 - s["joint_gap"] / 2
    t = s["thickness"]
    ext = P["frame"]["extrusion"]
    H = s["top_overlap_below"] + ext + s["crown_rise"]
    y_rail = s["top_overlap_below"] + ext / 2
    p = skirt_blank(W, H, t)
    holes = [slot(x, y_rail, M4, s["slot_travel"], -1, t + 2)
             for x in (s["mount_inset"], W - s["mount_inset"])]
    v0 = y_rail + ext / 2 + 2
    holes += honeycomb(6, v0, W - 6, H - 4, s["hex_r"], s["hex_wall"], -1, t + 2)
    # stiffening rib on the back of the crown, above the rail
    rib = box(0, H - 3, t, W, 3, 3)
    return cut_all(p.fuse(rib), holes)


def logo_badge():
    s = P["skirt"]
    r = s["badge_r"]
    base = hexagon(0, 0, r, 0, s["badge_depth"] + 0.6)
    # stylised chevron + bar (original artwork, Velta-style)
    chev = prism_xy([(-6.5, 5), (-3.8, 5), (0, -2.2), (3.8, 5), (6.5, 5), (0, -6.5)],
                    s["badge_depth"] + 0.6, 1.2)
    bar = box(-6.5, -9, s["badge_depth"] + 0.6, 13, 1.6, 1.2)
    return base.fuse(chev).fuse(bar)


def fit_test():
    """Short slice of the bottom skirt: prints in ~20 min and checks both rail rows."""
    s = dict(P["skirt"])
    full = bottom_skirt("plain")
    return full.common(box(-1, -1, -1, 2 * s["mount_inset"] + 2, 400, 50))


# ---------------------------------------------------------------- frame bits
def foot():
    """Bolts under the two lower rails at a corner (60 deg apart), raises the frame."""
    f = P["foot"]
    ext = P["frame"]["extrusion"]
    c0, c1 = f["corner_clear"], f["corner_clear"] + f["arm_len"]
    pts, holes = [], []
    for ang in (-30, 30):
        a = math.radians(ang)
        for x, y in ((c0, -ext / 2), (c1, -ext / 2), (c1, ext / 2), (c0, ext / 2)):
            pts.append((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)))
        mx = (c0 + c1) / 2
        hx, hy = mx * math.cos(a), mx * math.sin(a)
        holes.append(cyl(M4 / 2, 50, hx, hy, -1))
        holes.append(cyl(4.6, f["thickness"] - 4, hx, hy, -1))  # screw head recess (bottom)
    # convex hull of both rail footprints = one stiff pad
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    hull = []
    for p in pts + pts[:2]:
        while len(hull) >= 2 and ((hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1]) -
                                  (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0])) <= 0:
            hull.pop()
        hull.append(p)
    hull = hull[:-2] if hull[-1] == hull[1] else hull
    uniq = []
    for p in hull:
        if p not in uniq:
            uniq.append(p)
    body = prism_xy(uniq, 0, f["thickness"])
    body = body.cut(cyl(16, 1.2, (c0 + c1) / 2, 0, -0.01))  # recess for a stick-on rubber pad
    return cut_all(body, holes).removeSplitter()


def endstop_mount():
    """Adjustable microswitch holder clamped to a vertical 2020 (stock endstop board)."""
    e = P["endstop"]
    ext = P["frame"]["extrusion"]
    base = box(-ext / 2, 0, 0, ext, 30, 4)
    base = base.cut(slot(0, 10, M4, 10, -1, 6))
    arm = box(-ext / 2, 26, 0, ext, 4, 4 + e["switch_drop"])
    s = base.fuse(arm)
    for x in (-e["hole_pitch"] / 2, e["hole_pitch"] / 2):
        s = s.cut(cyl(M3_TAP / 2, 8, x, 25, 4 + e["switch_drop"] - 4, (0, 1, 0)))
    return s


def cable_clip():
    ext = P["frame"]["extrusion"]
    base = box(-5, -ext / 2, 0, 10, ext, 2.4).cut(cyl(M4 / 2, 5, 0, -4, -1))
    loop = cyl(5, 10, -5, 5, 5, (1, 0, 0)).cut(cyl(3.4, 12, -6, 5, 5, (1, 0, 0)))
    loop = loop.cut(box(-6, 1, 5, 12, 8.5, 6)).fuse(box(-5, 0, 0, 10, 2, 5))
    return base.fuse(loop.common(box(-5, -12, 0, 10, 30, 20)))


# ---------------------------------------------------------------- toolhead
def tool_frame():
    """Angles (deg) of the three arm pairs and of the hotend entry slot."""
    return [90, 210, 330], 30


def effector():
    e = P["effector"]
    arms, slot_ang = tool_frame()
    t = e["plate_t"]
    R = e["offset"]
    body = cyl(R - 2, t)
    for a in arms:
        L = e["arm_spacing"] - 2 * e["joint_clear"]
        tab = box(R - 5, -L / 2, 0, 10, L, e["tab_h"])
        bore = cyl(M3_TAP / 2, L + 2, R, -L / 2 - 1, e["tab_h"] / 2, (0, 1, 0))
        tab = tab.cut(bore)
        tab.rotate(V(0, 0, 0), V(0, 0, 1), a)
        body = body.fuse(tab)
    # groove-mount slot (E3D V6 / stock Kossel hotend): 12 mm groove, slides in sideways
    g = e["groove_d"] + 0.2
    sl = cyl(g / 2, t + 2, 0, 0, -1).fuse(box(0, -g / 2, -1, R + 10, g, t + 2))
    sl.rotate(V(0, 0, 0), V(0, 0, 1), slot_ang)
    body = body.cut(sl)
    holes = []
    for k in (-1, 1):  # clamp/shroud screws
        a = math.radians(slot_ang + 90 * k)
        holes.append(cyl(M3 / 2, 40, e["clamp_r"] * math.cos(a), e["clamp_r"] * math.sin(a), -1))
    for a in arms:  # accessory holes (probe, lights, cable support)
        ar = math.radians(a + 60)
        if abs(((a + 60 - slot_ang) + 180) % 360 - 180) > 10:
            holes.append(cyl(M3_TAP / 2, 40, e["acc_r"] * math.cos(ar),
                             e["acc_r"] * math.sin(ar), -1))
    return cut_all(body, holes).removeSplitter()


def groove_clamp():
    e = P["effector"]
    _, slot_ang = tool_frame()
    t = e["collar_h"] + 2.5
    c = cyl(e["clamp_r"] + 4, t)
    c = c.cut(cyl(e["collar_d"] / 2 + 0.15, e["collar_h"], 0, 0, -0.01))  # top collar pocket
    c = c.cut(cyl(e["bowden_hole"] / 2, t + 2, 0, 0, -1))
    for k in (-1, 1):
        a = math.radians(slot_ang + 90 * k)
        x, y = e["clamp_r"] * math.cos(a), e["clamp_r"] * math.sin(a)
        c = c.cut(cyl(M3 / 2, t + 2, x, y, -1)).cut(cyl(3.1, 2, x, y, t - 2 + 0.01))
    # key that fills the effector entry slot so the hotend can't walk out
    g = e["groove_d"] + 0.2
    key = box(e["groove_d"] / 2 + 0.4, -g / 2 + 0.2, t, e["offset"] - 3 - e["groove_d"] / 2,
              g - 0.4, e["plate_t"] - 0.3)
    key.rotate(V(0, 0, 0), V(0, 0, 1), slot_ang)
    return c.fuse(key)


def hotend_shroud(printable=True):
    """30 mm fan shroud for the V6-style heatsink; hangs under the effector."""
    e = P["effector"]
    _, slot_ang = tool_frame()
    H = e["heatsink_h"]
    S = 32
    b = box(-S / 2, -S / 2, 0, S, S, H)
    b = b.cut(cyl(e["heatsink_d"] / 2 + 0.4, H + 2, 0, 0, -1))
    b = b.cut(cyl(13.5, S, 0, 0, H / 2, (1, 0, 0)))          # fan inlet (+X)
    b = b.cut(box(-S, -9, H / 2 - 9, S, 18, 18))               # exhaust (-X)
    for y in (-12, 12):
        for z in (H / 2 - 12, H / 2 + 12):
            b = b.cut(cyl(M3_TAP / 2, 10, S / 2 - 8, y, z, (1, 0, 0)))
    # screw bosses up into the effector clamp holes (rotated into the slot frame)
    b.rotate(V(0, 0, 0), V(0, 0, 1), slot_ang + 90)  # fan faces away from the slot
    for k in (-1, 1):
        a = math.radians(slot_ang + 90 * k)
        x, y = e["clamp_r"] * math.cos(a), e["clamp_r"] * math.sin(a)
        b = b.fuse(cyl(4, H, x, y, 0)).cut(cyl(M3_TAP / 2, H + 2, x, y, -1))
    # 5015 duct mounting ear (bottom, opposite the fan)
    a = math.radians(slot_ang + 90 + 180)
    ex, ey = 22 * math.cos(a), 22 * math.sin(a)
    ear = cyl(5, 5, ex, ey, 0).fuse(box(min(0, ex) - 4, min(0, ey) - 4, 0,
                                         abs(ex) + 8, abs(ey) + 8, 5).common(cyl(23, 5)))
    ear = ear.cut(cyl(M3_TAP / 2, 7, ex, ey, -1))
    b = b.fuse(ear).cut(cyl(e["heatsink_d"] / 2 + 0.4, H + 2, 0, 0, -1))
    # print upside down: flip so the effector face is on the bed
    if printable:
        b.rotate(V(0, 0, H / 2), V(1, 0, 0), 180)
    return b.removeSplitter()


def part_fan_duct(printable=True):
    """Slides onto a 5015 blower outlet and aims a flat jet at the nozzle tip."""
    d = P["duct"]
    w = 1.6
    iw, ih = d["outlet_w"] + 0.4, d["outlet_h"] + 0.4

    def rect(cx, cz, ww, hh, y, tilt=0):
        pts = [(-ww / 2, -hh / 2), (ww / 2, -hh / 2), (ww / 2, hh / 2), (-ww / 2, hh / 2)]
        c, s_ = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        vs = [V(cx + x, y + z * s_, cz + z * c) for x, z in pts]
        return Part.makePolygon(vs + [vs[0]])

    L = d["length"]
    outer = Part.makeLoft([rect(0, 0, iw + 2 * w, ih + 2 * w, 0),
                           rect(0, 0, iw + 2 * w, ih + 2 * w, 8),
                           rect(0, -d["drop"], d["nozzle_w"] + 2 * w, d["nozzle_h"] + 2 * w, L, 45)],
                          True, False)
    inner = Part.makeLoft([rect(0, 0, iw, ih, -1),
                           rect(0, 0, iw, ih, 8),
                           rect(0, -d["drop"], d["nozzle_w"], d["nozzle_h"], L + 0.5, 45)],
                          True, False)
    duct = outer.cut(inner)
    ear = box(iw / 2 + w, 0, -4, 10, 6, 8).cut(cyl(M3 / 2, 8, iw / 2 + w + 5, 3, -5, (0, 0, 1)))
    duct = duct.fuse(ear)
    if not printable:
        return duct
    duct.rotate(V(0, 0, 0), V(1, 0, 0), -90)  # inlet face down on the bed
    bb = duct.BoundBox
    duct.translate(V(0, 0, -bb.ZMin))
    return duct


# ---------------------------------------------------------------- electronics
def pico_pi_plate():
    """SKR Pico + Raspberry Pi 3B side by side. Both use the 58 x 49 mm M2.5 pattern."""
    el = P["electronics"]
    W, H, t = el["plate_w"], el["plate_h"], 4
    p = box(0, 0, 0, W, H, t)
    for i, cx in enumerate((W * 0.25, W * 0.75)):
        cy = H / 2
        # ventilation under each board
        p = p.cut(box(cx - 22, cy - 15, -1, 44, 30, t + 2))
        for sx in (-29, 29):
            for sy in (-24.5, 24.5):
                p = p.fuse(cyl(3.5, t + el["standoff_h"], cx + sx, cy + sy, 0))
                p = p.cut(cyl(INSERT_M25 / 2, t + el["standoff_h"] + 1, cx + sx, cy + sy, 1.5))
    for x in (6, W - 6):  # mount slots to two 2020 rails / the frame
        for y in (12, H - 12):
            p = p.cut(slot(x, y, M4, 12, -1, t + 2))
    # zip-tie anchors along the bottom edge
    for x in (W * 0.5, W * 0.12, W * 0.88):
        p = p.cut(box(x - 2, 3, -1, 4, 2, t + 2)).cut(box(x - 2, 8, -1, 4, 2, t + 2))
    return p.removeSplitter()


def fan_bracket_40():
    base = box(-12, 0, 0, 24, 20, 4).cut(cyl(M4 / 2, 6, 0, 10, -1))
    face = box(-21, 20, 0, 42, 4, 42)
    face = face.cut(cyl(19, 6, 0, 19, 21, (0, 1, 0)))
    for x in (-16, 16):
        for z in (5, 37):
            face = face.cut(cyl(M3_TAP / 2, 8, x, 19, z, (0, 1, 0)))
    return base.fuse(face)


# ---------------------------------------------------------------- extruder / spool
def bowden_mount():
    """NEMA17 plate for the stock Bowden extruder, bolts to a 2020 rail."""
    ext = P["frame"]["extrusion"]
    plate = box(-23, 0, 0, 46, 46, 5)
    plate = plate.cut(cyl(11.6, 7, 0, 23, -1))
    for x in (-15.5, 15.5):
        for y in (7.5, 38.5):
            plate = plate.cut(cyl(M3 / 2, 7, x, y, -1))
    foot = box(-23, -ext - 5, 0, 46, ext + 5, 5)
    wall = box(-23, -5, 0, 46, 5, 30)
    s = plate.fuse(foot.cut(slot(-12, -ext / 2 - 5, M4, 6, -1, 7, "x"))
                   .cut(slot(12, -ext / 2 - 5, M4, 6, -1, 7, "x"))).fuse(wall)
    return s.removeSplitter()


def spool_holder(printable=True):
    ext = P["frame"]["extrusion"]
    base = box(-ext / 2, 0, 0, ext, 50, 6)
    base = base.cut(cyl(M4 / 2, 8, 0, 12, -1)).cut(cyl(M4 / 2, 8, 0, 38, -1))
    arm = box(-8, 40, 0, 16, 10, 95)
    rod = cyl(9, 75, 0, 45, 90, (0, 1, 0)).cut(box(-10, 40, 90 - 10, 20, 100, 4))
    lip = cyl(16, 4, 0, 116, 90, (0, 1, 0))
    s = base.fuse(arm).fuse(rod).fuse(lip)
    if not printable:
        return s
    s.rotate(V(0, 0, 0), V(0, 1, 0), 90)  # print on its side for strength
    bb = s.BoundBox
    s.translate(V(-bb.XMin, 0, -bb.ZMin))
    return s


# ---------------------------------------------------------------- build
PARTS = [
    # group, name, qty, builder
    ("00_Fit_Test", "fit_test_coupon", 1, fit_test),
    ("Skirts", "bottom_skirt_half", 3, lambda: bottom_skirt("plain")),
    ("Skirts", "bottom_skirt_badge_half", 2, lambda: bottom_skirt("badge")),
    ("Skirts", "bottom_skirt_ports_half", 1, lambda: bottom_skirt("ports")),
    ("Skirts", "top_skirt_half", 6, top_skirt),
    ("Skirts", "logo_badge", 2, logo_badge),
    ("Frame", "foot", 3, foot),
    ("Frame", "endstop_mount", 3, endstop_mount),
    ("Frame", "cable_clip_2020", 12, cable_clip),
    ("Toolhead", "effector_v6", 1, effector),
    ("Toolhead", "groove_clamp", 1, groove_clamp),
    ("Toolhead", "hotend_shroud_3010", 1, hotend_shroud),
    ("Toolhead", "part_fan_duct_5015", 1, part_fan_duct),
    ("Electronics", "skr_pico_pi3b_plate", 1, pico_pi_plate),
    ("Electronics", "fan_bracket_4010", 1, fan_bracket_40),
    ("Extruder", "bowden_extruder_mount", 1, bowden_mount),
    ("Extruder", "spool_holder", 1, spool_holder),
]


def main():
    doc = App.newDocument("DVF_ACLP")
    report = []
    (ROOT / "CAD" / "STEP").mkdir(parents=True, exist_ok=True)
    for group, name, qty, fn in PARTS:
        shape = fn()
        if not shape.isValid():
            shape.fix(0.01, 0.01, 0.01)
        solids = len(shape.Solids)
        out = ROOT / "STLs" / group
        out.mkdir(parents=True, exist_ok=True)
        stl = out / f"{name}_x{qty}.stl"
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                      AngularDeflection=0.3, Relative=False)
        mesh.write(str(stl))
        shape.exportStep(str(ROOT / "CAD" / "STEP" / f"{name}.step"))
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        bb = shape.BoundBox
        report.append((group, name, qty, solids, round(shape.Volume / 1000, 1),
                       f"{bb.XLength:.0f}x{bb.YLength:.0f}x{bb.ZLength:.0f}",
                       mesh.isSolid() and not mesh.hasNonManifolds()))
    doc.saveAs(str(ROOT / "CAD" / "DVF_ACLP.FCStd"))
    for r in report:
        print("%-12s %-26s x%-2d solids=%d vol=%scm3 bbox=%s watertight=%s" % r)


if __name__ == "__main__":
    main()
