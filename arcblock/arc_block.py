import cadquery as cq
from math import sin, cos, acos, radians, degrees
from types import SimpleNamespace as Measures

# A parametric arc-shaped mountable block, for example as furniture foot, guide or similar.
#
# To use this design, you need Python, CadQuery (https://cadquery.readthedocs.io/en/latest/) and 
# ideally also CQ-Editor, the CadQuery IDE (https://github.com/CadQuery/CQ-editor).
#
# License: Unlicence and Creative Commons Public Domain Dedication (CC-0).

m = Measures(
    linear_width = 50.0,
    depth = 15.0,
    height = 15.0,
    arc_outer_diameter = 100.0,
    top_fillets = 3.7,
    vertical_fillets = 2.5,
    
    # Hole positions are just eyeballed for now. Position visually after defining the arc.
    # TODO: Calculate hole positions on the arc centerline based on fractions of the arc angle (say, at 30% and 70%).
    holes = Measures(
        hole_1_width_offset = 15.0,
        hole_1_depth_offset = 7.0,
        hole_2_width_offset = 35.0,
        hole_2_depth_offset = 7.0,
        head_diameter = 7.0,
        head_height = 4.0,
        bolt_diameter = 4.2
    )
)

# Derived measures.
m.arc_outer_radius = 0.5 * m.arc_outer_diameter
m.arc_center_diameter = m.arc_outer_diameter - m.depth
m.arc_center_radius = 0.5 * m.arc_center_diameter
# Using law of cosines in a triangle "radius, secant, radius" to determine the center angle:
m.arc_center_angle = degrees(acos((2 * m.arc_center_radius**2 - m.linear_width**2) / (2 * m.arc_center_radius**2)))
# Using the fact that all angles in a triangle are 180°, one is known, and the two others are the same:
m.arc_secant_angle = 0.5 * (180 - m.arc_center_angle)

path = (
    cq
    .Workplane("XY")
    .radiusArc((m.linear_width, 0.0), m.arc_center_radius)
    .wire() # Since we don't want a closed wire, there is no close() creating the wire. We have to.
)

# show_object(path, name = "path")

model = (
    cq.Workplane("XY")

    # The safest option for sweep() is to place the wire to sweep at the startpoint of the path and 
    # orthogonal to the path. To do so, we adjust the workplane according to the arc-to-secant angle.
    .transformed(rotate = (90, - m.arc_secant_angle, 0))
    .rect(m.depth, m.height)
    
    # Sweep along the path. (The default transition = "right" leads to a nonmanifold desaster and along a 
    # different path. Seems to be an issue in the CAD kernel.)
    .sweep(path, transition = "round")
    
    .edges("|Z")
    .fillet(m.vertical_fillets)
    
    .edges(">Z")
    .fillet(m.top_fillets)
    
    .faces(">Z")
    .workplane()

    # Hole 1.
    .center(m.holes.hole_1_width_offset, m.holes.hole_1_depth_offset)
    .cboreHole(m.holes.bolt_diameter, m.holes.head_diameter, m.holes.head_height)
    .center(- m.holes.hole_1_width_offset, - m.holes.hole_1_depth_offset) # Undo the last center to get back to (0,0).
    
    # Hole 2.
    .center(m.holes.hole_2_width_offset, m.holes.hole_2_depth_offset)
    .cboreHole(m.holes.bolt_diameter, m.holes.head_diameter, m.holes.head_height)
)

# Display the CAD model. Only works when opening the file in CQ-Editor.
show_options = {"color": "lightgray", "alpha": 0.0}
show_object(model, name = "model", options = show_options)
