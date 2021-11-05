import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from math import asin as asin, degrees as degrees
from math import atan as atan

# Choose where to load the measures from (always a module, from the local directory). 
# Choose one or create your own measures file.
#measures_modulename = "measures__toilet_seat_support"
measures_modulename = "measures__mitraset_foot"

# Since Python syntax for importing modules differs depending if there is a current package, 
# we need a little hack. CQ-Editor does not set a current package, but does not set 
# __name__ == '__main__' either. See:
# https://stackoverflow.com/a/49480246 and for details https://stackoverflow.com/a/14132912
if __package__ is None or __package__ == '':
    # uses current directory visibility
    measures_module = importlib.import_module(measures_modulename)
else:
    # uses current package visibility
    measures_module = importlib.import_module('.' + measures_modulename)
# Selective reloading to pick up changes made in imported files between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
importlib.reload(measures_module)
m = measures_module.measures


# A parametric 3D CAD model for a foot block / spacer block, made with CadQuery.
# 
# The block can have configurable height, width and depth, vertical corner rounding, edge 
# rounding, two hole positions, hole sizes, including the space for countersunk wood screw heads.
# Height can be different at both ends of the spacer block, allowing to create an inclined version.
# Width can be different between top and bottom, allowing to create a tapering shape.
# Can be used for example for: furniture feet, toilet seat supports, glider feet for chairs, 
# feet for boxes, bumpers for various items.
#
# TODO Rename m.edge_radius to m.lower_edge_radius.
# TODO As an alternative to m.lower_width and m.upper_width, also support m.width for when both are 
#   the same measure. Then internally, set m.lower_width and m.upper_width accordingly. And similarly 
#   for the other pairs of related parameters.

# Calculating derived measures.
if getattr(m, 'hole_1', None) is None: m.hole_1 = None # Make sure key exists.
if getattr(m, 'hole_2', None) is None: m.hole_2 = None # Make sure key exists.
# Note, upper_depth is measured along the sloped surface, not the axis direction. So use asin(), not atan().
m.block.slope_angle = degrees(asin((m.block.back_height - m.block.front_height) / m.block.upper_depth))
if getattr(m, 'corner_radius_front', None) is None:
    m.block.corner_radius_front = (min(m.block.lower_width, m.block.upper_width) - 0.5) / 2
if getattr(m, 'corner_radius_back', None) is None:
    m.block.corner_radius_back = (min(m.block.lower_width, m.block.upper_width)  - 0.5) / 2

# Creating the CAD model.
model = (
    cq.Workplane("XY")

    # Lower face, always resting horizontally on the floor or on another object.
    .move(xDist = -m.block.lower_width / 2, yDist = max(0, (m.block.upper_depth - m.block.lower_depth) / 2))
    .rect(m.block.lower_width, m.block.lower_depth, centered = False)
    # TODO: Fix that centered = (True, False) does not work in CadQuery, 
    # then use that instead of the .move().

    # Upper face, on which the foot block is mounted to its object.
    .transformed(offset = (0, 0, m.block.front_height), rotate = (m.block.slope_angle, 0, 0))
    .move(xDist = -m.block.upper_width / 2, yDist = max(0, (m.block.lower_depth - m.block.upper_depth) / 2))
    .rect(m.block.upper_width, m.block.upper_depth, centered = False)

    .loft()

    # Round the front and back corners.
    .edges("(not |Y) and (not |X)").edges("<Y").fillet(m.block.corner_radius_front)
    .edges("(not |Y) and (not |X)").edges(">Y").fillet(m.block.corner_radius_back)

    # Round the lower edges.
    .faces("<Z").edges().fillet(m.block.edge_radius)
)

# Drill the mounting holes, if so desired.
if m.hole_1 is not None:
    model = (
        model
        .copyWorkplane(cq.Workplane("XY"))
        # cskHole() drills into negative workplane normal direction, so to drill into global +Z direction 
        # from below, we have to invert the XY plane.
        .workplane(invert = True)
        .pushPoints([(0, -m.hole_1.position)]) # Negative coordinate due to inverted plane.
        .cskHole(m.hole_1.hole_size, m.hole_1.head_size, m.hole_1.head_angle)
    )

if m.hole_2 is not None:
    model = (
        model
        .copyWorkplane(cq.Workplane("XY"))
        # cskHole() drills into negative workplane normal direction, so to drill into global +Z direction 
        # from below, we have to invert the XY plane.
        .workplane(invert = True)
        .pushPoints([(0, -m.hole_2.position)]) # Negative coordinate due to inverted plane.
        .cskHole(m.hole_2.hole_size, m.hole_2.head_size, m.hole_2.head_angle)
    )

# Displaying the CAD model. Only works when opening the file in CQ-Editor.
show_options = {"color": "lightgray", "alpha": 0}
show_object(model, name = "model", options = show_options)
