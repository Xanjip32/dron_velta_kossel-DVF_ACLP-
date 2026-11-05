"""Build the bolt-on Kossel trim with the Python bundled with FreeCAD 1.1."""
import argparse
import math
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part

THICKNESS = 3.2
M4_CLEARANCE = 4.6
BOLT_TRAVEL = 6
HEX_RADIUS = 8.6


def prism(points, base, height):
    wire = Part.makePolygon([App.Vector(x, y, base) for x, y in (*points, points[0])])
    return Part.Face(wire).extrude(App.Vector(0, 0, height))


def mounting_slot(x, y):
    radius = M4_CLEARANCE / 2
    low = y - BOLT_TRAVEL / 2
    high = y + BOLT_TRAVEL / 2
    depth = THICKNESS + 2
    bridge = Part.makeBox(M4_CLEARANCE, BOLT_TRAVEL, depth, App.Vector(x - radius, low, -1))
    first = Part.makeCylinder(radius, depth, App.Vector(x, low, -1))
    second = Part.makeCylinder(radius, depth, App.Vector(x, high, -1))
    return bridge.fuse(first).fuse(second)


def hex_vent(x, y, radius):
    angles = [math.radians(30 + 60 * i) for i in range(6)]
    return prism([(x + radius * math.cos(a), y + radius * math.sin(a))
                  for a in angles], -1, THICKNESS + 2)


def accent(x, y):
    # Three raised segments echo the Velta emblem on an independent flat skirt.
    segments = [
        [(-9, -8), (-1, 8), (3, 8), (-5, -8)],
        [(4, 7), (9, -1), (7, -5), (2, 3)],
        [(-3, -9), (-1, -6), (6, -6), (4, -9)],
    ]
    return [prism([(x + u, y + v) for u, v in points], THICKNESS - 0.2, 1)
            for points in segments]


def panel(width, reach, lip, *, badge=False, single_mount=False):
    height = reach + lip
    outline = [(4, 0), (width - 4, 0), (width, 4), (width, height),
               (0, height), (0, 4)]
    blank = prism(outline, 0, THICKNESS)
    bolt_positions = [width / 2] if single_mount else [14, width - 14]
    holes = [mounting_slot(x, reach) for x in bolt_positions]
    badge_x = width - 15
    radius = HEX_RADIUS if reach >= 40 else 7.2
    y = radius + 3
    row = 0
    while y + radius + 3 <= reach - BOLT_TRAVEL / 2 - M4_CLEARANCE / 2:
        x = 12 + (9.5 if row % 2 else 0)
        while x <= width - 12:
            if not badge or abs(x - badge_x) > 19:
                holes.append(hex_vent(x, y, radius))
            x += 19
        row += 1
        y += 15
    shape = blank.cut(Part.makeCompound(holes))
    if badge:
        shape = shape.fuse(accent(badge_x, (reach - 5) / 2))
    return shape.removeSplitter()


def pico_plate():
    outline = [(3, 0), (113, 0), (116, 3), (116, 59),
               (113, 62), (3, 62), (0, 59), (0, 3)]
    blank = prism(outline, 0, THICKNESS)
    holes = [mounting_slot(7, 31), mounting_slot(109, 31)]
    for x in (18.5, 76.5):
        for y in (6.5, 55.5):
            holes.append(Part.makeCylinder(1.4, THICKNESS + 2, App.Vector(x, y, -1)))
    return blank.cut(Part.makeCompound(holes)).removeSplitter()


def export(out, name, shape):
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError(f"Invalid CAD solid for {name}")
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=0.15)
    if not mesh.isSolid() or mesh.CountFacets == 0:
        raise ValueError(f"Open or empty mesh for {name}")
    mesh.write(str(out / (name + ".stl")))
    shape.exportStep(str(out / (name + ".step")))
    box = shape.BoundBox
    print(f"{name}: {box.XLength:.1f} x {box.YLength:.1f} x {box.ZLength:.1f} mm, closed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--span", type=float, default=200, help="covered width per frame face")
    parser.add_argument("--base-reach", type=float, default=44, help="skirt drop below slot center")
    parser.add_argument("--top-reach", type=float, default=28, help="top trim rise above slot center")
    parser.add_argument("--rear-gap", type=float, default=32, help="clear cable gap between rear halves")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "models")
    args = parser.parse_args()
    if not 140 <= args.span <= 300 or not 12 <= args.rear_gap <= args.span - 84:
        parser.error("span must be 140-300 mm with at least 42 mm per rear half")
    if not 28 <= args.base_reach <= 60 or not 24 <= args.top_reach <= 60:
        parser.error("base reach must be 28-60 mm and top reach must be 24-60 mm")
    args.out.mkdir(parents=True, exist_ok=True)
    half = (args.span - 1) / 2
    rear_half = (args.span - args.rear_gap) / 2
    models = {
        "00_M4_Fit_Test": panel(48, args.base_reach, 10, single_mount=True),
        "01_Base_Half": panel(half, args.base_reach, 10),
        "02_Base_Badge_Half": panel(half, args.base_reach, 10, badge=True),
        "03_Rear_Cable_Half": panel(rear_half, args.base_reach, 10),
        "04_Top_Half": panel(half, args.top_reach, 10),
        "05_Upper_Corner_Accent": panel(34, args.top_reach, 10, single_mount=True),
        "06_Optional_SKR_Pico_Plate": pico_plate(),
    }
    for name, shape in models.items():
        export(args.out, name, shape)


if __name__ == "__main__":
    main()



