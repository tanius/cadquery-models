import cadquery as cq
import logging
from types import SimpleNamespace as Measures
from math import sin, cos, radians

log = logging.getLogger(__name__)

# An eye cover that can be hooked to the top edge of eyeglasses.
#
# To use this design, you need Python, CadQuery (https://cadquery.readthedocs.io/en/latest/) and 
# ideally also CQ-Editor, the CadQuery IDE (https://github.com/CadQuery/CQ-editor).
#
# License: Unlicence and Creative Commons Public Domain Dedication (CC-0).

class EyeCover:

    def __init__(self, workplane, measures):
        """
        A parametric eye cover that can be hooked to the top edge of eyeglasses.
        
        :param workplane: The CadQuery workplane to create the chute on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object, which may have the following attributes:
            - **``shell_thickness``:** Shell thickness of the tube element.
        """

        # todo
        self.model = workplane
        self.debug = False
        self.measures = measures

        self.build()

    def clip_shape(self, wall_thickness, height, hole_radius, circum_radius):
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

    def build(self):
        m = self.measures

        self.model = (
            cq.Workplane("front")
            .union(
                self.clip_shape(
                    wall_thickness = m.clip_wall_thickness,
                    height = m.clip_height,
                    hole_radius = m.clip_hole_diameter / 2 + m.clip_wall_thickness / 2, 
                    circum_radius = m.clip_hole_diameter / 2 + m.clip_wall_thickness + m.clip_funnel_length
                )
            )
        )

def part(self, part_class, measures):
    """CadQuery plugin that provides a factory method for custom parts"""

    part = part_class(self, measures) # Dynamic instantiation from the type contained in part_class.

    return self.newObject(
        part.model.objects
    )


# =============================================================================
# Measures and Part Creation
# =============================================================================
cq.Workplane.part = part

measures = Measures(
    clip_funnel_length = 4.0,
    clip_hole_diameter = 9.0,
    clip_height = 11.0,
    clip_wall_thickness = 1.6
)
show_options = {"color": "lightgray", "alpha": 0}

eye_cover = cq.Workplane("XY").part(EyeCover, measures)
show_object(eye_cover, name = "eye_cover", options = show_options)
