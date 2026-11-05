
# ================================================================ v2: corners, base, top bay
# (exec'd inside build_dvf.py so it shares its helpers and params)

def hull2d(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def frame_geo():
    """Derived frame numbers shared by parts, panels and the assembly."""
    f, c = P["frame"], P["corner"]
    edge = f["rail_len"] + 2 * f["rail_end_from_vertex"]       # vertex-to-vertex along a rail
    d_edge = edge / (2 * math.sqrt(3))                           # rail centre line to printer centre
    return dict(edge=edge, d_edge=d_edge, r_tower=2 * d_edge - c["tower_from_vertex"],
                visible=edge - 2 * c["arm_reach"])


def corner_outline():
    """Corner footprint in corner frame: vertex at origin, +X toward printer centre."""
    c, f = P["corner"], P["frame"]
    hw = f["extrusion"] / 2 + c["wall"]
    xt = c["tower_from_vertex"]
    pts = []
    for th in (30, -30):
        a = math.radians(th)
        d, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        for s_ in (c["truncate"], c["arm_reach"]):
            for k in (-hw, hw):
                pts.append((s_ * d[0] + k * n[0], s_ * d[1] + k * n[1]))
    pts += [(xt + dx, dy) for dx in (-15, 15) for dy in (-15, 15)]
    pts = [p for p in pts if p[0] >= c["truncate"] - 1e-6]
    pts += [(c["truncate"], y) for y in (-hw * 1.6, hw * 1.6)]
    return hull2d(pts)


def _rail_tool(th, z0, s0, s1, w, h):
    t = box(s0, -w / 2, z0, s1 - s0, w, h)
    t.rotate(V(0, 0, 0), V(0, 0, 1), th)
    return t


def _corner_common(H, rail_levels, tower_z0, tower_z1):
    c, f = P["corner"], P["frame"]
    ext = f["extrusion"] + 0.3
    xt = c["tower_from_vertex"]
    body = prism_xy(corner_outline(), 0, H)
    tools = [box(xt - ext / 2, -ext / 2, tower_z0, ext, ext, tower_z1 - tower_z0)]
    sm = (f["rail_end_from_vertex"] + c["arm_reach"]) / 2
    for th in (30, -30):
        a = math.radians(th)
        d, n = V(math.cos(a), math.sin(a), 0), V(-math.sin(a), math.cos(a), 0) * (1 if th > 0 else -1)
        for z0 in rail_levels:
            tools.append(_rail_tool(th, z0, f["rail_end_from_vertex"] - 0.5, c["arm_reach"] + 1, ext, ext))
            for s_ in (sm - 8, sm + 8):  # M4 from the outer face into the rail's outer slot
                p = d * s_ + n * 30 + V(0, 0, z0 + ext / 2)
                tools.append(Part.makeCylinder(M4 / 2, 22, p, n * -1))
                tools.append(Part.makeCylinder(4.2, 30 - f["extrusion"] / 2 - 4.5, p, n * -1))
    for z in (tower_z0 + 10, tower_z1 - 10):  # M4 from both sides into the tower side slots
        for k in (-1, 1):
            tools.append(cyl(M4 / 2, 60, xt, 0, z, (0, k, 0)))
            tools.append(cyl(4.2, 60, xt, k * (f["extrusion"] / 2 + 6), z, (0, k, 0)))
    # cable duct behind the tower (wiring channel runs through it)
    tools.append(box(c["truncate"] + 14, -7, -1, 14, 14, H + 2))
    return body, tools


def corner_bottom():
    """Motor corner: two lower rails, tower, NEMA17 (shaft toward the centre), feet."""
    c, f = P["corner"], P["frame"]
    xt, bd, pitch = c["tower_from_vertex"], c["base_drop"], f["bottom_rail_pitch"]
    zm = 4 + 1 + 21                                   # motor centre
    tz0 = zm + 21 + 5                                 # tower pocket bottom
    H = tz0 + c["tower_socket"]
    body, tools = _corner_common(H, (bd, bd + pitch), tz0, H + 1)
    xf = xt + 6                                       # motor face
    tools.append(box(c["truncate"] - 1, -21.6, 4, xf - c["truncate"] + 1, 43.2, 44))   # motor bay
    tools.append(cyl(11.6, 12, xf - 1, 0, zm, (1, 0, 0)))                            # boss
    for dy in (-15.5, 15.5):
        for dz in (-15.5, 15.5):
            tools.append(cyl(M3 / 2, 12, xf - 1, dy, zm + dz, (1, 0, 0)))
            tools.append(cyl(3.2, 30, xf + 5, dy, zm + dz, (1, 0, 0)))
    tools.append(box(xf + 5, -13, zm - 12, 40, 26, H))                               # pulley + belt
    for x, y in ((c["truncate"] + 12, 0), (xt + 22, 30), (xt + 22, -30)):            # rubber feet
        tools.append(cyl(8.2, 1.2, x, y, -0.01))
    return cut_all(body, tools).removeSplitter()


def corner_top():
    """Idler corner: top rails, tower socket, belt idler, endstop holes, top-panel inserts."""
    c, f = P["corner"], P["frame"]
    xt = c["tower_from_vertex"]
    H = c["top_h"]
    rz = H - 4 - f["extrusion"]
    body, tools = _corner_common(H, (rz,), -1, c["tower_socket"])
    tools.append(box(xt + 12, -13, -1, 30, 26, rz - 1))                     # belt + idler bay
    tools.append(box(xt + 9, -1.7, rz / 2 - 4, 40, 3.4, 8))                 # idler axle slot (M3)
    tools.append(cyl(1.5, 60, xt + 30, 0, H - 30))                          # tension screw M3 from top
    for y in (16, 16 + P["endstop"]["hole_pitch"]):                         # stock endstop board
        tools.append(cyl(M3_TAP / 2, 10, xt + 20, y, -0.01))
    for x, y in ((c["truncate"] + 8, 18), (c["truncate"] + 8, -18), (xt + 25, 0)):
        tools.append(cyl(INSERT_M3 / 2, 6, x, y, H - 5.99))                 # top panel inserts
    return cut_all(body, tools).removeSplitter()


def wiring_channel(length=None, flat=False):
    """U-channel for the 2020 tower (or flat on the top panel), press-fit lid separate."""
    ch = P["channel"]
    L = length or ch["seg_len"]
    w, h, t = ch["inner_w"], ch["depth"], 2.0
    u = box(-w / 2 - t, 0, 0, w + 2 * t, L, h + t)
    u = u.cut(box(-w / 2, -1, t, w, L + 2, h + 1))
    n = max(2, int(L // 60))
    for i in range(n):
        y = L * (i + 0.5) / n
        u = u.cut(slot(0, y, M4, 4, -1, t + 2))
    # zip tie slots
    for y in (L * 0.25, L * 0.75):
        for k in (-1, 1):
            u = u.cut(box(k * (w / 2 + t / 2) - 2, y, t + 3, 4, 3, 2.5))
    return u.removeSplitter()


def wiring_channel_lid(length=None):
    ch = P["channel"]
    L = length or ch["seg_len"]
    w = ch["inner_w"]
    lid = box(-w / 2 - 2, 0, 0, w + 4, L, 1.6).fuse(box(-w / 2 + 0.15, 0, 1.6, w - 0.3, L, 2))
    return lid


def power_inlet_box():
    """Bolts over the ports skirt; holds an IEC C14 inlet with fuse + rocker switch."""
    pw = P["power"]
    W, Hh, D, t = pw["box_w"], pw["box_h"], pw["box_d"], 2.5
    b = box(-W / 2, -Hh / 2, 0, W, Hh, D)
    b = b.cut(box(-W / 2 + t, -Hh / 2 + t, -1, W - 2 * t, Hh - 2 * t, D - t + 1))
    b = b.cut(box(-pw["iec_w"] / 2 - 0.2, -pw["iec_h"] / 2 - 0.2, D - t - 1,
                  pw["iec_w"] + 0.4, pw["iec_h"] + 0.4, t + 2))
    pwid = P["skirt"]["port_w"]
    for k in (-1, 1):  # flange bosses matching the skirt's M3 holes
        x = k * (pwid / 2 + 7)
        x0, x1 = sorted((x - k * 4, k * (W / 2 - t + 0.5)))
        b = b.fuse(box(x0, -4, 0, x1 - x0, 8, 8)).cut(cyl(M3_TAP / 2, 9, x, 0, -0.5))
    # print with the flange side on the bed: front face is a short bridge
    return b.removeSplitter()


def psu_bracket():
    """Pair of these hold a standard 12 V box PSU on the floor panel."""
    ps = P["power"]
    w = ps["psu_w"] + 1
    base = box(-w / 2 - 12, 0, 0, w + 24, 24, 4)
    base = base.cut(cyl(M4 / 2, 6, -w / 2 - 6, 12, -1)).cut(cyl(M4 / 2, 6, w / 2 + 6, 12, -1))
    end = box(-w / 2, 0, 4, w, 4, 14)
    sides = box(-w / 2 - 4, 0, 4, 4, 24, 20).fuse(box(w / 2, 0, 4, 4, 24, 20))
    return base.fuse(end).fuse(sides).removeSplitter()


def psu_terminal_cover():
    """Finger guard over the PSU screw terminals (mains side!). Prints top-down."""
    ps = P["power"]
    w, d, h, t = ps["psu_w"] + 6, 34, ps["psu_h"] + 6, 2.4
    c = box(-w / 2, 0, 0, w, d, h)
    c = c.cut(box(-w / 2 + t, t, -1, w - 2 * t, d, h - t + 1))
    for x in (-w / 4, w / 4):  # cable exits in the outer wall, at the bottom edge
        c = c.cut(box(x - 9, -1, h - 14, 18, t + 2, 15))
    for k in (-1, 1):  # floor tabs (bottom edge = z h, part prints roof-down)
        c = c.fuse(box(k * (w / 2 + 6) - 6, d - 12, h - 3, 12, 12, 3)
                   .cut(cyl(M4 / 2, 5, k * (w / 2 + 6), d - 6, h - 4)))
    return c.removeSplitter()


def top_cover_half(with_fan=False):
    """Covers one board on the top electronics tray. Open end meets the other half."""
    el = P["electronics"]
    t = 2.4
    L, W, H = el["plate_w"] / 2 + 2, el["plate_h"] + 6 + 2 * t, P["top_bay"]["cover_h"]
    c = box(0, -W / 2, 0, L, W, H)
    c = c.cut(box(t, -W / 2 + t, t, L, W - 2 * t, H))          # open end at x = L and bottom
    vents = honeycomb(10, -W / 2 + 10, L - 10, W / 2 - 10, 4.2, 1.8, -1, t + 2,
                      [(L / 2, 0, 21)] if with_fan else [])
    c = cut_all(c, vents)
    if with_fan:
        c = c.cut(cyl(19, t + 2, L / 2, 0, -1))
        for dx in (-16, 16):
            for dy in (-16, 16):
                c = c.cut(cyl(M3_TAP / 2, t + 2, L / 2 + dx, dy, -1))
        c = c.cut(box(-1, -10, H - 14, t + 2, 20, 15))            # cable entry notch
    for k in (-1, 1):  # foot tabs
        c = c.fuse(box(t, k * (W / 2 + 5) - 5, H - 3, 14, 10, 3)
                   .cut(cyl(M4 / 2, 5, t + 7, k * (W / 2 + 5), H - 4)))
    # tabs are on the open bottom edge; part prints top-face down (z = 0 is the roof)
    return c.removeSplitter()


def _panel_face(kind):
    """2D panel (world XY) as a Part.Face, plus a list of (x, y, d) holes."""
    g = frame_geo()
    c = P["corner"]
    ext = P["frame"]["extrusion"]
    R = 2 * (g["d_edge"] + ext / 2)
    tri = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in (90, 210, 330)]
    face = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in tri + [tri[0]]]))
    holes = []
    for a in (90, 210, 330):
        vtx = V(*[2 * g["d_edge"] * f(math.radians(a)) for f in (math.cos, math.sin)], 0)
        ex, ey = V(-math.cos(math.radians(a)), -math.sin(math.radians(a)), 0), None
        ey = V(-ex.y, ex.x, 0)
        if kind == "bottom":
            pts = [vtx + ex * x + ey * y for x, y in corner_outline()]
            cutp = Part.Face(Part.makePolygon(pts + [pts[0]]))
            cutp = cutp.makeOffset2D(0.8)
            p0 = vtx + ex * (c["truncate"] + 0.8)
            face = face.cut(Part.Face(Part.makePolygon([p0 + ey * 300, p0 - ey * 300,
                                                        p0 - ey * 300 - ex * 300,
                                                        p0 + ey * 300 - ex * 300, p0 + ey * 300])))
        else:  # top panel covers the corners, trimmed at their flat outer face
            p0 = vtx + ex * c["truncate"]
            cutp = Part.Face(Part.makePolygon([p0 + ey * 300, p0 - ey * 300,
                                               p0 - ey * 300 - ex * 300, p0 + ey * 300 - ex * 300,
                                               p0 + ey * 300]))
            for x, y in ((c["truncate"] + 8, 18), (c["truncate"] + 8, -18),
                         (c["tower_from_vertex"] + 25, 0)):
                p = vtx + ex * x + ey * y
                holes.append((p.x, p.y, M3))
            if a == 210:  # cable duct of tower A
                p = vtx + ex * (c["truncate"] + 21)
                holes.append((p.x, p.y, 13))
        face = face.cut(cutp)
    # rail screw holes (into the bottom slot of the lower rails / top slot of top rails)
    for f_ in (270, 30, 150):
        n = V(math.cos(math.radians(f_)), math.sin(math.radians(f_)), 0)
        u = V(-n.y, n.x, 0)
        for k in (-1, -0.33, 0.33, 1):
            p = n * g["d_edge"] + u * (k * (g["visible"] / 2 - 15))
            holes.append((p.x, p.y, M4))
    ps = P["power"]
    if kind == "bottom":
        n = V(math.cos(math.radians(150)), math.sin(math.radians(150)), 0)
        u = V(-n.y, n.x, 0)
        cen = n * (g["d_edge"] - ext / 2 - 8 - ps["psu_w"] / 2)
        for j in (-1, 1):  # bracket at the -u end
            p = cen - u * (ps["psu_l"] / 2 - 8) + n * (j * (ps["psu_w"] / 2 + 6.5))
            holes.append((p.x, p.y, M4))
        for k in (-1, 1):  # terminal cover at the +u end (towards the power inlet)
            p = cen + u * (ps["psu_l"] / 2 - 14) + n * (k * (ps["psu_w"] / 2 + 9))
            holes.append((p.x, p.y, M4))
        for x, y in ((0, 0), (-50, 30), (50, 30)):  # airflow under the bed
            holes.append((x, y, 25))
    else:
        el = P["electronics"]
        for x in (6, el["plate_w"] - 6):
            for y in (12, el["plate_h"] - 12):
                holes.append((x - el["plate_w"] / 2, y - el["plate_h"] / 2, M4))
        W = el["plate_h"] + 6 + 4.8
        for sx in (-1, 1):
            for k in (-1, 1):
                holes.append((sx * (el["plate_w"] / 2 + 2 - 9.4), k * (W / 2 + 5), M4))
        holes.append((0, 0, 30))  # centre cable pass-through (extruder / toolhead wiring)
    for x, y, d in holes:
        face = face.cut(Part.Face(Part.Wire(Part.makeCircle(d / 2, V(x, y, 0)))))
    return face


def panel(kind):
    return _panel_face(kind).extrude(V(0, 0, P["panel"]["thickness"]))


def write_dxf(face, path):
    """Minimal R12 DXF: every wire as a polyline (circles as CIRCLE)."""
    out = ["0", "SECTION", "2", "ENTITIES"]
    for w in face.Wires:
        if len(w.Edges) == 1 and hasattr(w.Edges[0].Curve, "Radius"):
            cc = w.Edges[0].Curve
            out += ["0", "CIRCLE", "8", "0", "10", f"{cc.Center.x:.4f}", "20", f"{cc.Center.y:.4f}",
                    "30", "0", "40", f"{cc.Radius:.4f}"]
            continue
        pts = w.discretize(Deflection=0.05)
        out += ["0", "POLYLINE", "8", "0", "66", "1", "70", "1"]
        for p in pts[:-1]:
            out += ["0", "VERTEX", "8", "0", "10", f"{p.x:.4f}", "20", f"{p.y:.4f}", "30", "0"]
        out += ["0", "SEQEND"]
    out += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(out) + "\n")
