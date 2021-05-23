import cadquery as cq

# Demonstration of the CadQuert split() method.
#
# Based on the official documentation of split():
# https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Workplane.split

# Create a cube with a vertical hole.
part = cq.Workplane("XY").box(1, 1, 1).faces(">Z").workplane().circle(0.25).cutThruAll()

# Cut the cube into a back and front half.
part = part.faces(">Y").workplane(-0.5).split(keepTop = True)

show_object(part, options = {"alpha": 0.5, "color": (64, 164, 223)})
