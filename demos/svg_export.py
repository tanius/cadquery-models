import cadquery as cq
BS = cq.selectors.BoxSelector

# Demonstration of exporting a 3D shape (here of a mold) to SVG. Observations:
# (1) Exporting directly from CadQuery to SVG exports an orthgraphic view as a line drawing 
#     with transparent background, and a small 3D coordinate system in black.
# (2) For better results, export from CadQuery to STEP, then import STEP in FreeCad, add 
#     measurements and colors, then export from there to SVG. This then includes measurements, 
#     face colors, object colors, all embedded in a technical drawing templte.

# Measures.
mw = 40 # mold width
mh = 13 # mold height
ml = 120 # mold length
#
wd = 6  # wire diameter (refers to cable inserted into the mold when using it)
rt = 7  # resin thickness
rl = 50  # resin length
rwpl = 10  # resin to wire pass length
#
pf = 18 # pocket fillet
#
mhd = 7  # mount hole diameter
mht = 3  # mount hole distance from edges
#
fhd = 6 # filling hole diameter

# Mold base shape.
base = cq.Workplane("XY").box(ml, mw, mh, (True, True, False))

# Mold cavity.
pocket = (
    cq.Workplane("XY", (0, 0, mh))
    .moveTo(-ml/2., 0)
    .line(0, wd/2.)
    .line((ml-rl)/2.-rwpl, 0)
    .line(rwpl, rt)
    .line(rl, 0)\
    .line(rwpl, -rt)
    .line((ml-rl)/2.-rwpl, 0)
    .line(0, -(wd/2.))
    .close()

    .revolve(axisEnd=(1, 0))

    .edges(BS((-rl/2.-rwpl-.1, -100, -100), (rl/2.+rwpl+.1, 100, 100)))
    .fillet(pf)
)

mold = base.cut(pocket)

# Mount holes in mold corner.
px = ml/2.-mht-mhd/2.
py = mw/2.-mht-mhd/2
mold = (
    mold
    .faces("<Z")
    .workplane()
    .pushPoints([
        ( px,  py),
        (-px,  py),
        (-px, -py),
        ( px, -py)
    ])
    .hole(mhd)
)

show_object(mold)

# Enable to export to a SVG file.
# r.exportSvg("test.svg")
