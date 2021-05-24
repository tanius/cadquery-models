import cadquery as cq
import cadquery.selectors as cqs
import logging
from math import degrees as degrees
from math import atan as atan
from types import SimpleNamespace as Measures

# A parametric 3D CAD model for a foot block / spacer block, made with CadQuery.
# 
# The block can have configurable height, width and depth, vertical corner rounding, edge 
# rounding, two hole positions, hole sizes, including the space for countersunk wood scre heads.
# Height can be different at both ends of the spacer block, allowing to create an inclined version.
# Width can be different between top and bottom, allowing to create a tapering shape.
# Can be used for example for: furniture feet, toilet seat supports, glider feet for chairs, 
# feet for boxes, bumpers for various items.

# Configuration Section
#
# Initial configuration is for a pair of spacer blocks to support a specific toilet seat, in 
# addition to two similar spacer blocks that were already mounted to that toilet seat.
# Toilet seat material thickness: 17.5 mm. Screws may go up to 15 mm into the toilet seat.
measures = Measures(
    lower_width = 15.0, # Same as the original toilet seat supports.
    upper_width = 19.0, # Same as the original toilet seat supports.
    depth = 94.0, # Twice the size of the original toilet seat supports.
    front_height = 16.6,
    back_height = 19.1,
    edge_radius = 3.0,
    hole_1 = Measures(
        position = 23.5,
        # Hole for a 4 mm wood screw.
        # Use 5.4 to get 3.9-4.0 mm when printed with a 0.8 mm nozzle (which always shrink holes).
        # Use 4.5 to get 4.2 mm when printed with a 0.4 mm nozzle.
        hole_size = 5.4,
        # Hole to make a 4 mm wood screw's head flush with the surface.
        # Use 10.0 when printed with a 0.8 mm nozzle (which always shrink holes).
        # Use 9.2 when printed with a 0.4 mm nozzle.
        head_size = 10.0,
        head_angle = 90 # Suitable for wood screws with countersunk heads.
    ),
    hole_2 = Measures(
        position = 70.5,
        hole_size = 5.4, # See above.
        head_size = 10.0, # See above.
        head_angle = 90 # See above.
    ),
    cutoff_height = 1.6
)
m = measures

# Calculating derived measures.
m.corner_radius = (m.lower_width - 0.5) / 2
m.slope_angle = degrees(atan((m.back_height - m.front_height) / m.depth))

# Creating the CAD model.
model = (
    cq.Workplane("XY")

    # Lower face, resting on the floor or on another object.
    .move(xDist = -m.lower_width / 2)
    .rect(m.lower_width, m.depth, centered = False)
    # TODO: Fix that centered = (True, False) does not work in CadQuery, 
    # then use that instead of the .move().

    # Upper face, mounted to the object.
    .transformed(offset = (0, 0, m.front_height), rotate = (m.slope_angle, 0, 0))
    .move(xDist = -m.upper_width / 2)
    .rect(m.upper_width, m.depth, centered = False)

    .loft()

    # Round the corners.
    .edges("(not |Y) and (not |X)")
    .edges(">Y or <Y")
    .fillet(m.corner_radius)

    # Round the lower edges.
    .faces("<Z").edges().fillet(m.edge_radius)

    # Drill the mounting holes.
    .copyWorkplane(cq.Workplane("XY"))
    # cskHole() drills into negative workplane normal direction, so to drill into global +Z direction 
    # from below, we have to invert the XY plane.
    .workplane(invert = True)
    .pushPoints([(0, -m.hole_1.position)]) # Negative coordinate due to inverted plane.
    .cskHole(m.hole_1.hole_size, m.hole_1.head_size, m.hole_1.head_angle)
    .pushPoints([(0, -m.hole_2.position)]) # Negative coordinate due to inverted plane.
    .cskHole(m.hole_2.hole_size, m.hole_2.head_size, m.hole_2.head_angle)
)

# Displaying the CAD model. Only works when opening the file in CQ-Editor.
show_options = {"color": "lightgray", "alpha": 0}
show_object(model, name = "model", options = show_options)
