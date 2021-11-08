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
# TODO Support to create small studs on the side walls inside the recess, to position the foot block 
#   centered around the original foot, guaranteeing equal glue thickness. However, this might not 
#   be needed in practice.
# TODO Switch to using different corner radii on top and bottom surface, with the adaptive fillet 
#   automatically created via the lofting. This allows to have a half-circle end on both ends, and 
#   on both top and bottom.
# TODO As an alternative to m.lower_width and m.upper_width, also support m.width for when both are 
#   the same measure. Then internally, set m.lower_width and m.upper_width accordingly. And similarly 
#   for the other pairs of related parameters.

# Make sure SimpleNamespace attributes keys exist for unused configuration parameters.
if getattr(m, 'recess', None) is None: m.recess = None
if getattr(m, 'hole_1', None) is None: m.hole_1 = None
if getattr(m, 'hole_2', None) is None: m.hole_2 = None
if getattr(m, 'parts', None) is None: m.parts = "all"
if getattr(m.block, 'corner_radius_front', None) is None: m.block.corner_radius_front = 0.0
if getattr(m.block, 'corner_radius_back', None) is None: m.block.corner_radius_back = 0.0
if getattr(m.block, 'lower_edge_radius', None) is None: m.block.lower_edge_radius = 0.0
if getattr(m.recess, 'backfill_section_height', None) is None: m.recess.backfill_section_height = 0.0
if getattr(m.recess, 'backfill_section_depth', None) is None: m.recess.backfill_section_depth = 0.0

# Calculate derived measures.
# Note, upper_depth is measured along the sloped surface, not the axis direction. So use asin(), not atan().
m.block.slope_angle = degrees(asin((m.block.back_height - m.block.front_height) / m.block.upper_depth))
m.block.width = max(m.block.upper_width, m.block.lower_width)
m.block.depth = max(m.block.upper_depth, m.block.lower_depth)
m.block.height = max(m.block.front_height, m.block.back_height)

# Create the foot block base shape.
model = (
    cq.Workplane("XY")

    # Lower face, always resting horizontally on the floor or on another object.
    .center(x = 0, y = 0.5 * m.block.depth)
    .rect(m.block.lower_width, m.block.lower_depth, centered = True)

    # Upper face, on which the foot block is mounted to its object.
    .transformed(offset = (0, 0, m.block.front_height), rotate = (m.block.slope_angle, 0, 0))
    .tag("upper_face_workplane")
    .rect(m.block.upper_width, m.block.upper_depth, centered = True)

    .loft()
)

# Round the front and back corners and lower edge, where necessary.
if m.block.corner_radius_front > 0:
    model = model.edges("(not |Y) and (not |X)").edges("<Y").fillet(m.block.corner_radius_front)
if m.block.corner_radius_back > 0:
    model = model.edges("(not |Y) and (not |X)").edges(">Y").fillet(m.block.corner_radius_back)
if m.block.lower_edge_radius > 0:
    model = model.faces("<Z").edges().fillet(m.block.lower_edge_radius)

# Create the recess shape and cut the recess into the model.
if m.recess is not None:
    recess = (
        model

        # Upper face, created in the workplane of the foot block's upper face.
        .workplaneFromTagged("upper_face_workplane")
        .rect(m.recess.upper_width, m.recess.upper_depth, centered = True)

        # Lower face.
        .transformed(offset = (0, 0, -m.recess.height))
        .tag("recess_bottom_workplane")
        .rect(m.recess.lower_width, m.recess.lower_depth, centered = True)

        .loft(combine = False) # Replaces foot block parent solid, instead of combining with it.
    )

    # Reduce the recess by a backfill section in its bottom center, if needed.
    if m.recess.backfill_section_height > 0.0 and m.recess.backfill_section_depth > 0.0:
        recess = (
            recess
            .workplaneFromTagged("recess_bottom_workplane")
            .rect(m.recess.upper_width, m.recess.backfill_section_depth, centered = True)
            .cutBlind(m.recess.backfill_section_height)

            # Round the lower edges.
            .faces("<Z[-2]").edges("<X or >X").fillet(m.recess.backfill_edge_radius)
        )

    # Round the corners and lower edges of the recess base shape.
    # (Rounding lower edges must be done after the backfilling, as otherwise overlapping fillets 
    # lead to CAD kernel crashes.)
    recess = (
        recess
        # Round the corners.
        .edges("(not |Y) and (not |X)").edges("<Y or >Y").fillet(m.recess.corner_radius)
        # Round the lower edges.
        .faces("<Z").edges("(not |X) or (<Y or >Y)").fillet(m.recess.lower_edge_radius)
    )

    # Cut the recess into the model.
    model = model.cut(recess)

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

# Split the model in half (for 3D printing), if desired.
if m.parts != "all":
    model = (
        model
        .copyWorkplane(cq.Workplane("XZ").workplane(invert = True))
        .workplane(offset = 0.5 * m.block.depth)
    )
    model = model.split(
        keepBottom = True if m.parts == "front half" else False,
        keepTop =    True if m.parts == "back half"  else False,
    )

# Display the recess shape. (Debug only.)
# show_options = {"color": "red", "alpha": 0}
# show_object(recess, name = "recess", options = show_options)

# Display the CAD model. Only works when opening the file in CQ-Editor.
show_options = {"color": "lightgray", "alpha": 0.0}
show_object(model, name = "model", options = show_options)
