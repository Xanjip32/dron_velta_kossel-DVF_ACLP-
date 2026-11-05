
# ================================================================ v3: enclosed DV sections
# (exec'd inside build_dvf.py after v2_parts.py)

def _sec():
    """Heights of the bottom and top sections, from the corner geometry (Z = 0 at the table)."""
    c, f, en = P["corner"], P["frame"], P["enclosure"]
    zlow = c["base_drop"] + f["extrusion"] / 2
    zhigh = zlow + f["bottom_rail_pitch"]
    tz0 = 26 + 21 + 5
    z_tc = tz0 + f["tower_len"] - c["tower_socket"]
    z_top_rail = z_tc + c["top_h"] - 4 - f["extrusion"] / 2
    z_deck_top = z_tc + c["top_h"] + P["panel"]["thickness"]
    return dict(zlow=zlow, zhigh=zhigh, tz0=tz0, z_tc=z_tc, z_top_rail=z_top_rail,
                bottom_z0=en["bottom_skirt_z0"], bottom_z1=zhigh + f["extrusion"] / 2 + en["bottom_rise"],
                bed_deck=zhigh + f["extrusion"] / 2,
                top_z0=z_top_rail - f["extrusion"] / 2 - 2, z_deck_top=z_deck_top,
                lid_z=z_deck_top + en["top_bay_h"])


def deep_skirt(section="bottom", variant="plain"):
    """DV-style boxed skirt: chamfered front with honeycomb grill, 20 mm deep, open back
    against the rails. Fan variant holds a 60 mm fan inside, in front of the rails."""
    s, en = P["skirt"], P["enclosure"]
    g = _sec()
    W = s["span"] / 2 - s["joint_gap"] / 2
    D, t, wall, c = en["skirt_depth"], 2.4, 2.4, 2.5
    if section == "bottom":
        H = g["bottom_z1"] - g["bottom_z0"]
        rails = [g["zlow"] - g["bottom_z0"], g["zhigh"] - g["bottom_z0"]]
    else:
        H = g["lid_z"] - g["top_z0"]
        rails = [g["z_top_rail"] - g["top_z0"]]
    prof = [(0, c), (c, 0), (H - c, 0), (H, c), (H, D), (0, D)]       # (y, z), front at z = 0
    body = Part.Face(Part.makePolygon([V(0, y, z) for y, z in prof + [prof[0]]])).extrude(V(W, 0, 0))
    body = body.cut(box(wall, wall, t, W - 2 * wall, H - 2 * wall, D))
    mi = s["mount_inset"]
    keep, tools = [], []
    for x in (mi, W - mi):
        for y in rails:
            body = body.fuse(cyl(6, D - t, x, y, t))
            tools += [cyl(M4 / 2, D + 2, x, y, -1), cyl(4.4, D - 6 + 1, x, y, -1)]
            keep.append((x, y, 8))
    cx, cy = W / 2, H / 2 + (4 if section == "top" else 0)
    if variant == "fan":
        for dx in (-25, 25):
            for dy in (-25, 25):
                body = body.fuse(cyl(3.5, 4, cx + dx, cy + dy, t))
                tools.append(cyl(M3_TAP / 2, 8, cx + dx, cy + dy, -1))
                keep.append((cx + dx, cy + dy, 4))
    if variant == "badge":
        bx = W - 6 - s["badge_r"]
        tools.append(hexagon(bx, cy, s["badge_r"] + 0.2, -1, 1 + s["badge_depth"]))
        keep.append((bx, cy, s["badge_r"] + 3))
    if variant == "power":
        pw, ph = s["port_w"], s["port_h"]
        py = (rails[0] + rails[1]) / 2
        tools.append(box(cx - pw / 2, py - ph / 2, -1, pw, ph, t + 2))
        for k in (-1, 1):
            tools.append(cyl(M3 / 2, t + 2, cx + k * (pw / 2 + 7), py, -1))
        keep.append((cx, py, pw / 2 + 12))
    tools += honeycomb(7, 7, W - 7, H - 7, en["grill_hex_r"], en["grill_wall"], -1, t + 2, keep)
    return cut_all(body, tools).removeSplitter()


def deep_fit_test():
    return deep_skirt("bottom", "plain").common(box(-1, -1, -1, 2 * P["skirt"]["mount_inset"] + 4, 400, 60))


def corner_cap():
    """Hollow cap on each top corner, between the deck and the lid; closes the corner gap."""
    c, en = P["corner"], P["enclosure"]
    H = en["top_bay_h"]
    out = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in corner_outline() + [corner_outline()[0]]]))
    inner = out.makeOffset2D(-3.0)
    cap = out.extrude(V(0, 0, H)).cut(inner.extrude(V(0, 0, H - 3)))      # roof at top
    for x, y in ((c["truncate"] + 8, 18), (c["truncate"] + 8, -18), (c["tower_from_vertex"] + 25, 0)):
        cap = cap.fuse(cyl(4.5, H, x, y, 0))
        cap = cap.cut(cyl(M3 / 2, H + 2, x, y, -1)).cut(cyl(3.3, H - 6, x, y, 6))  # M3 from top into the corner insert
    for x, y in ((c["truncate"] + 22, 26), (c["truncate"] + 22, -26)):
        cap = cap.fuse(cyl(4.5, H, x, y, 0)).cut(cyl(INSERT_M3 / 2, 6, x, y, H - 5.99))  # lid inserts
    cap = cap.cut(box(c["truncate"] + 40, -14, -1, 60, 28, 16))            # cable / air passage inward
    return cap.removeSplitter()


def pillar_cover():
    """Clip-on cover for the outer face of a tower, hollow for cables (DV pillar look)."""
    c, en = P["corner"], P["enclosure"]
    xt = c["tower_from_vertex"]
    L = en["pillar_seg"]
    f0 = xt - 10                                                           # tower outer face
    tr = c["truncate"]
    hw = (P["frame"]["extrusion"] / 2 + c["wall"]) * 1.6
    pts = [(f0, 13), (tr + 10, hw), (tr, hw - 6), (tr, -hw + 6), (tr + 10, -hw), (f0, -13)]
    outer = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in pts + [pts[0]]]))
    inner = outer.makeOffset2D(-2.4)
    p = outer.extrude(V(0, 0, L)).cut(inner.extrude(V(0, 0, L)).translated(V(0, 0, 0)))
    p = p.fuse(box(f0 - 2.6, -10, 0, 2.6, 20, L))                          # flange on the tower face
    for z in (L * 0.25, L * 0.75):
        p = p.cut(cyl(M4 / 2, 20, f0 - 5, 0, z, (1, 0, 0)))
        p = p.cut(cyl(5, 12, tr - 1, 0, z, (1, 0, 0)))                    # screwdriver access
    p.translate(V(-f0, 0, 0))   # local: x <= 0 points outward from the tower face
    return p.removeSplitter()


def side_spool_extruder(printable=True):
    """Bolts to the flat outer face of a top corner: NEMA17 Bowden extruder + spool arm."""
    b = box(0, -24, 0, 5, 48, 56)
    for y in (-14, 14):
        for z in (14, 42):
            b = b.cut(cyl(M4 / 2, 7, -1, y, z, (1, 0, 0))).cut(cyl(4.3, 3, 4.99 - 3 + 3, y, z, (1, 0, 0)))
    ep = box(5, 19, 2, 46, 5, 46)                                          # extruder plate (motor on +y)
    ep = ep.cut(cyl(11.6, 7, 28, 18, 25, (0, 1, 0)))
    for dx in (-15.5, 15.5):
        for dz in (-15.5, 15.5):
            ep = ep.cut(cyl(M3 / 2, 7, 28 + dx, 18, 25 + dz, (0, 1, 0)))
    gus = prism_xy([(5, 0), (40, 0), (5, 35)], 0, 4)
    gus.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    gus.translate(V(0, 19, 2 + 35))
    # flat-bar spool arm (DV style): runs sideways along the frame face, 30 deg off the plate
    sa = P["spool_arm"]
    L, bw, bh, z0 = sa["length"], sa["width"], sa["height"], sa["z"]
    beam = box(0, -bw / 2, z0, L, bw, bh)
    n_h = int((L - 40) // 26)
    for k in range(n_h):                                      # lightening windows
        beam = beam.cut(box(22 + k * 26, -bw / 2 - 1, z0 + 6, 16, bw + 2, bh - 12))
    beam = beam.fuse(box(L - 6, -bw / 2, z0, 6, bw, bh + sa["lip"]))   # spool end stop
    web = prism_xy([(0, z0 + 2), (sa["brace"], z0 + 2), (0, 4)], 0, bw - 4)
    web.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    web.translate(V(0, bw / 2 - 2, 0))
    arm = beam.fuse(web)
    arm.rotate(V(0, 0, 0), V(0, 0, 1), -30)
    arm.translate(V(2, -15, 0))
    s = fuse_all([b, ep, arm]).removeSplitter()
    if printable:   # lie on the back of the mounting plate: arm rises at 60 deg, no supports
        s.rotate(V(0, 0, 0), V(0, 1, 0), -90)
        bb = s.BoundBox
        s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def bed_standoff():
    s = cyl(8, P["enclosure"]["bed_gap"], 0, 0, 0)
    return s.cut(cyl(M4 / 2, 20, 0, 0, -1))


def deck_face():
    """Bottom deck under the bed (inner cover of the bottom section)."""
    face = _panel_face("bottom")
    # rebuild without the PSU / floor holes: start again from the outline only
    g = frame_geo()
    ext = P["frame"]["extrusion"]
    c = P["corner"]
    R = 2 * (g["d_edge"] + ext / 2)
    tri = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in (90, 210, 330)]
    face = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in tri + [tri[0]]]))
    for a in (90, 210, 330):
        vtx = V(*[2 * g["d_edge"] * f(math.radians(a)) for f in (math.cos, math.sin)], 0)
        ex = V(-math.cos(math.radians(a)), -math.sin(math.radians(a)), 0)
        ey = V(-ex.y, ex.x, 0)
        pts = [vtx + ex * x + ey * y for x, y in corner_outline()]
        face = face.cut(Part.Face(Part.makePolygon(pts + [pts[0]])).makeOffset2D(0.8))
        p0 = vtx + ex * (c["truncate"] + 0.8)
        face = face.cut(Part.Face(Part.makePolygon([p0 + ey * 300, p0 - ey * 300, p0 - ey * 300 - ex * 300,
                                                    p0 + ey * 300 - ex * 300, p0 + ey * 300])))
    holes = []
    for a in (90, 210, 330):                       # bed standoffs
        holes.append((P["enclosure"]["bed_mount_r"] * math.cos(math.radians(a)),
                      P["enclosure"]["bed_mount_r"] * math.sin(math.radians(a)), M4))
    holes.append((0, -60, 20))                    # bed heater / thermistor wires
    for f_ in (270, 30, 150):
        n = V(math.cos(math.radians(f_)), math.sin(math.radians(f_)), 0)
        u = V(-n.y, n.x, 0)
        for k in (-1, -0.33, 0.33, 1):
            p = n * g["d_edge"] + u * (k * (g["visible"] / 2 - 15))
            holes.append((p.x, p.y, M4))
    for x, y, d in holes:
        face = face.cut(Part.Face(Part.Wire(Part.makeCircle(d / 2, V(x, y, 0)))))
    return face


def lid_face():
    """Top lid: same outline as the top deck, with a hex vent field over the boards."""
    face = _panel_face("top")
    # drop the deck's own holes: rebuild outline-only, then add lid holes
    g = frame_geo()
    c = P["corner"]
    ext = P["frame"]["extrusion"]
    R = 2 * (g["d_edge"] + ext / 2)
    tri = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in (90, 210, 330)]
    face = Part.Face(Part.makePolygon([V(x, y, 0) for x, y in tri + [tri[0]]]))
    for a in (90, 210, 330):
        vtx = V(*[2 * g["d_edge"] * f(math.radians(a)) for f in (math.cos, math.sin)], 0)
        ex = V(-math.cos(math.radians(a)), -math.sin(math.radians(a)), 0)
        ey = V(-ex.y, ex.x, 0)
        p0 = vtx + ex * c["truncate"]
        face = face.cut(Part.Face(Part.makePolygon([p0 + ey * 300, p0 - ey * 300, p0 - ey * 300 - ex * 300,
                                                    p0 + ey * 300 - ex * 300, p0 + ey * 300])))
        for x, y in ((c["truncate"] + 22, 26), (c["truncate"] + 22, -26)):
            p = vtx + ex * x + ey * y
            face = face.cut(Part.Face(Part.Wire(Part.makeCircle(M3 / 2, p))))
    r, wall = 5.0, 2.5
    dx = 2 * r * math.cos(math.radians(30)) + wall
    dy = dx * math.sin(math.radians(60))
    row, y = 0, -45.0
    while y <= 45:
        x = -95 + (dx / 2 if row % 2 else 0)
        while x <= 95:
            a = [math.radians(30 + 60 * i) for i in range(6)]
            vs = [V(x + r * math.cos(t), y + r * math.sin(t), 0) for t in a]
            face = face.cut(Part.Face(Part.makePolygon(vs + [vs[0]])))
            x += dx
        y += dy
        row += 1
    return face
