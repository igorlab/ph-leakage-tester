"""Board holder of the tester enclosure, rebuilt as an exact solid: board_holder.STEP

The original CAD file was lost; only board_holder.STL remained.
The part is a profile in the YZ plane extruded 6 mm along X, with a 12 mm hole for the BNC
along X and two 3.6 mm holes through the base. All dimensions below were read from the STL
vertices; the coordinates are those of the STL, so both files lie in the same place.

Usage (from the repository root, FreeCAD 1.0):
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd hardware/enclosure/make_board_holder.py
"""
import os

import FreeCAD as App
import Part

V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "hardware/enclosure"

X0, WIDTH = 28.5127, 6.0               # extrusion along X, mm
L = 37.47213                           # length of the base along Y
BASE = 4.0                             # base thickness
TOWER = 20.0                           # width of the central tower, centered on L/2
SHOULDER, TOP = 12.0, 18.0             # tower height at the 45° chamfers and at the top
CHAMFER = TOP - SHOULDER
BNC_D, BNC_Z = 12.0, 10.4              # hole for the BNC, along X
SCREW_D, SCREW_Y = 3.6, 2.89519        # holes through the base, from each end

c = L / 2
y1, y2 = c - TOWER / 2, c + TOWER / 2
profile = [(0, 0), (L, 0), (L, BASE), (y2, BASE), (y2, SHOULDER), (y2 - CHAMFER, TOP),
           (y1 + CHAMFER, TOP), (y1, SHOULDER), (y1, BASE), (0, BASE), (0, 0)]
wire = Part.makePolygon([V(X0, y, z) for y, z in profile])
body = Part.Face(wire).extrude(V(WIDTH, 0, 0))
body = body.cut(Part.makeCylinder(BNC_D / 2, WIDTH, V(X0, c, BNC_Z), V(1, 0, 0)))
for y in (SCREW_Y, L - SCREW_Y):
    body = body.cut(Part.makeCylinder(SCREW_D / 2, BASE, V(X0 + WIDTH / 2, y, 0), V(0, 0, 1)))
body = body.removeSplitter()

out = os.path.join(HERE, "board_holder.STEP")
body.exportStep(out)
print("wrote", out, "volume %.3f mm3" % body.Volume, "valid", body.isValid())
