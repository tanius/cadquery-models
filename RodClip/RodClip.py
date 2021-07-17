import cadquery as cq
from math import sin, cos, radians

# A parametric clip for a rod that can be wall mounted into a recess using a single bolt.
#
# Print with PETG and not too hot (≤245 °C) to get a material with a good amount of flexibility 
# rather than brittleness. The clip was originally designed as a spare part for the internal 
# freezer compartment of a fridge, but since it's parametric other uses are much more likely.
#
# To use this design, you need Python, CadQuery (https://cadquery.readthedocs.io/en/latest/) and 
# ideally also CQ-Editor, the CadQuery IDE (https://github.com/CadQuery/CQ-editor).
#
# License: Unlicence and Creative Commons Public Domain Dedication (CC-0).
#
# Published at:
# https://gist.github.com/tanius/b2ae1d3a89e4739f38eed8c33cd24724
# https://www.thingiverse.com/thing:4782666
#
# TODO: Introduce a parameter "clip_opening_angle" that makes the open section of the clip circle 
# configurable. Currently it is fixed at 90°.

base_width = 19.8
base_depth = 16.8
base_height = 3.2
base_corner_radius = 2.0
mounthole_diameter = 5.0
mounthole_center_y = 3.3 # Center of baseplate to center of hole.
mounthole_countersunk_diameter = 9.6
clip_hole_diameter = 9.0
clip_height = 11.0
clip_wall_thickness = 1.6 # Original: 1.6. 2.4 is definitely too strong for clip action in PETG.
clip_funnel_length = 4.0


def clip_shape(wall_thickness, height, hole_radius, circum_radius):
    left_endpoint = [cos(radians(-135)) * circum_radius, sin(radians(-135)) * circum_radius]
    right_endpoint = [cos(radians(-45)) * circum_radius, sin(radians(-45)) * circum_radius]

    left_arcpoint = [cos(radians(-135)) * hole_radius, sin(radians(-135)) * hole_radius]
    mid_arcpoint = [hole_radius, 0]
    right_arcpoint = [ cos(radians(-45)) * hole_radius, sin(radians(-45)) * hole_radius]

    path = (
        cq
        .Workplane("XY")
        .moveTo(*left_endpoint)
        .lineTo(*left_arcpoint)
        .threePointArc(mid_arcpoint, right_arcpoint)
        .lineTo(*right_endpoint)
        .wire() # Since we don't want a closed wire, close() will not create the wire. We have to.
    )

    # show_object(path, name = "path")

    result = (
        cq.Workplane("XY")
        # The safest option for sweep() is to place the wire to sweep at the startpoint of the path, 
        # orthogonal to the path.
        .center(*left_endpoint)
        .transformed(rotate = (90, -45, 0))
        .rect(wall_thickness, height)
        # The default transition = "right" leads to a nonmanifold desaster along a different path. 
        # Seems to be an issue in the CAD kernel.
        .sweep(path, transition = "round")
        .edges("|Z")
        # The CAD kernel cannot create radii touching each other, so we prevent that with factor 0.99.
        .fillet(wall_thickness / 2 * 0.99)
    )

    return result


clip = (
    cq
    .Workplane("XY")
    .rect(base_width, base_depth)
    .extrude(base_height)

    # Remember edges to fillet them later (when they will be hard to select otherwise).
    .edges("|Z").tag("base_corner_edges").end()

    # Create a workplane for the clip, with its center on the edge of the base.
    .faces(">Z")
    .workplane()
    .tag("base_workplane")
    .center(0, -base_depth / 2)

    # Add the clip itself.
    .union(
        clip_shape(
            wall_thickness = clip_wall_thickness, 
            height = clip_height, 
            hole_radius = clip_hole_diameter / 2 + clip_wall_thickness / 2, 
            circum_radius = clip_hole_diameter / 2 + clip_wall_thickness + clip_funnel_length
        )
        .translate((0, -base_depth / 2, base_height + clip_height / 2 - 0.01))
    )

    # Add a supporting chamfer around the clip.
    # Has to be adapted manually to not exceed the base plate edge, as that would produce the weirdest shapes.
    .faces(">Z[2]")
    .edges("%Circle and >>Y[-3]")
    .chamfer(3.79)

    # Add radii to the base plate.
    # Must be done after the fillet supporting the clip, as otherwise they collide and produce 
    # the weirdest shapes.
    .edges(tag = "base_corner_edges")
    .fillet(base_corner_radius)

    # Add the mount hole.
    .workplaneFromTagged("base_workplane")
    .center(0, mounthole_center_y)
    .circle(mounthole_diameter / 2)
    .cutThruAll()

    # Add the space for the head of the screw going into the base plate mount hole.
    .workplaneFromTagged("base_workplane")
    .center(0, mounthole_center_y)
    .circle(mounthole_countersunk_diameter / 2)
    .cutBlind(15)

    # Add a cutout to the base plate conforming to the clip hole, as found on the fridge.
    .workplaneFromTagged("base_workplane")
    .center(0, -base_depth / 2)
    .circle(clip_hole_diameter / 2 * 0.99) # Factor 0.99 to prevent CAD kernel from hanging.
    .cutThruAll()
)

show_object(clip)
