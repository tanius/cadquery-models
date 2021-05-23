import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures

log = logging.getLogger(__name__)

class Backplate:

    def __init__(self, workplane, measures):
        """
        A simple, parametric protective backplate for mobile devices or their cases, with a cutout 
        for an Armor-X X-Mount receptable glued to the device.

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Fix that the camera section cutout is slightly too narrow. Or rather, the corner 
            radius is too large in the design right now, which for concave corners like for this 
            cutout leads to too little material being removed.
        .. todo:: Fix that the current part cannot be printed properly, because removing small 
            amounts of support is never precise, contributing to a part that does not fit. Also, 
            overhangs never print precisely. So instead, the part should be printed with the back 
            surface on the print bed. So that surface must be made flat, including any covering for 
            the fingerprint sensor. It should be as high as the case edges, and maybe a bit higher 
            if necessary. The front surface should be ironed as part of the 3D printing, for the 
            tape to stick on well.
        .. todo:: Create a small slice (using XY cutting planes) of the design as separate part, to 
            use for printer calibration.
        .. todo:: For the xmount cutout, introduce a scaling parameter (adding extra space as an 
            absolute measure) that will only scale the xmount outer shape, not its hole. To allow 
            calibrating that cutout.
        .. todo:: Fix that the loop section does not have enough space to attach the loop. Keeping 
            the 45° ramp, it needs 4.0 mm more space.
        .. todo:: Make the cutout for the loop section narrower towards the bottom of the device, 
            but not narrower than the strap.
        .. todo:: Fix that currently the workplane is passed to this constructor as "workplane", 
            but selectors in this class use global axis directions. To fix this, create the 
            part in the XZ plane, and only when finished, rotate and translate it to be positioned 
            at the origin of the plane provided in the "workplane" parameter. Ideally, that action 
            would be provided by the part() method.
        .. todo:: Add a covering for the fingerprint sensor, to protect the thin film there. This 
            would automatically result when adding material over the fingerprint sensor and using 
            a suitable cutting depth for the cutter.
        """

        self.model = workplane
        self.debug = False
        self.measures = measures
        m = self.measures
        # TODO: Initialize missing measures with defaults.

        # TODO: Should better be "self.model = self.build(self.model)", as that enables other 
        #   methods using the same naming scheme, like "build_partname()". And actually, since 
        #   the positioning should be "naturally" at first and only adapted to the workplane of 
        #   the calling object in the end, there's no need to provide a parameter to build().
        self.build()


    def build(self):
        m = self.measures
        baseplane = self.model.workplane()

        base_shape = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.width, m.height, m.depth_1, centered = [False, False, False])
        )

        # A "bump" at the top of the box base shape. Needed to have enough material to 
        # reach into the side and top cutouts of the X-Mount shape, to help keep it in place.
        # TODO: Use a spline instead of a simple loft to create this bump.
        reinforcement_1 = (
            cq.Workplane()
            .copyWorkplane(baseplane)

            # Move to the center of the lower rectangle, draw it.
            .moveTo(
                x = m.reinforcement_1.bottom_left_1[0] + 0.5 * m.reinforcement_1.width_1,
                y = m.reinforcement_1.bottom_left_1[1] + 0.5 * m.reinforcement_1.height_1
            )
            .rect(m.reinforcement_1.width_1, m.reinforcement_1.height_1)

            # Move to the center of the lower rectangle, draw it.
            .workplane(offset = m.reinforcement_1.depth)
            .moveTo(
                x = m.reinforcement_1.bottom_left_2[0] + 0.5 * m.reinforcement_1.width_2,
                y = m.reinforcement_1.bottom_left_2[1] + 0.5 * m.reinforcement_1.height_2
            )
            .rect(m.reinforcement_1.width_2, m.reinforcement_1.height_2)

            .loft()

            # Translate to start at the back surface of the main part.
            .translate([0, -0.99 * m.depth_1, 0])
        )
        show_object(reinforcement_1, name = "reinforcement_1", options = {"color": "yellow", "alpha": 0.8})

        cutout_1 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_1.width, m.cutout_1.height, m.cutout_1.depth, centered = [False, False, False])
            # translate() does not require a workplane, as it works with global axis directions.
            .translate([m.cutout_1.bottom_left[0], 0, m.cutout_1.bottom_left[1]])
        )
        show_object(cutout_1, name = "cutout_1", options = {"color": "yellow", "alpha": 0.8})

        cutout_2 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_2.width, m.cutout_2.height, m.cutout_2.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_2.corner_radius)
            .translate([m.cutout_2.bottom_left[0], 0, m.cutout_2.bottom_left[1]])
        )
        show_object(cutout_2, name = "cutout_2", options = {"color": "yellow", "alpha": 0.8})

        cutout_3 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_3.width, m.cutout_3.height, m.cutout_3.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_3.corner_radius)
            .translate([m.cutout_3.bottom_left[0], 0, m.cutout_3.bottom_left[1]])
        )
        show_object(cutout_3, name = "cutout_3", options = {"color": "yellow", "alpha": 0.8})

        self.model = (
            base_shape
            .union(reinforcement_1)

            # TODO: Use cutThruAll() with 2D wires instead of cut(). The paradigm is not CSG! 
            #   However, this requires a way to fillet() the corners of the 2D wired before 
            #   using them for cutThruAll(), as otherwise selecting the edges to fillet afterwards 
            #   becomes complicated (at least needing tagging). And that way does not exist yet.
            .cut(cutout_1)
            .cut(cutout_2)
            .cut(cutout_3)
            
            # # Corner roundings.
            # # TODO: Fix that the corner angle where the cutouts intersect has to be smaller than this.
            .edges("|Y")
            .fillet(m.corner_radius)

            # Tapering off towards the face mounted to the device.
            .faces(">Y")
            .edges()
            # Due to a bug we cannot use asymmetric chamfering here, as the "length" and "length2"
            # parameters would be internally switched for some edges. So we do a simple 45° chamfer.
            .chamfer(0.95 * m.depth_1)
            # TODO: Report and fix the bug mentioned above, then do the chamfering like this:
            #.chamfer(length = 0.5 * m.front_edge_chamfer, length2 = 0.95 * m.depth_1)
            # TODO: Don't do the chamfer if the measure given is zero.
            # TODO: Also utilize back_edge_chamfer if present. If both are present, the part depth 
            #   has to be split half and half between them.
        )

        self.top = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = m.cutout_1.bottom_left[1] + 0.5 * m.cutout_1.height)
            .split(keepTop = True)
        )

        self.bottom = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = m.cutout_1.bottom_left[1] + 0.5 * m.cutout_1.height)
            .split(keepBottom = True)
        )

# =============================================================================
# Part Creation
# =============================================================================
measures = Measures(
    width = 69.50,
    height = 154.50, # Corrected from 155.20.
    depth_1 = 1.20, # Minimum depth without reinforcements.
    corner_radius = 2.50,
    front_edge_chamfer = 0.90, # Edge around the surface mounted to the device.
    back_edge_chamfer = 0.00, # Edge around the surface not mounted to the device.
    xmount_pos = (0.5 * 69.50, 0.5 * 155.20), # Center of the part.

    # Bump to thicken the material of the base plate in the area of the X-Mount cutout.
    # Measures for this do not have to be exact.
    # TODO: Due to a CAD kernel issue, the shape must not overlap with corners that are to be 
    # rounded afterwards. Otherwise no model can be calculated. This should be fixed at some time.
    reinforcement_1 = Measures(
        depth = 2.00, # Maximum depth, used in the center of the part.

        bottom_left_1 = (0, 3.0), # Positioning the bottom of the truncated pyramid.
        width_1 = 69.50, # The whole part width.
        height_1 = 121.0,

        bottom_left_2 = (0.5 * (69.50 - 42.00), 20.0), # Positioning the top of the truncated pyramid.
        width_2 = 42.00,
        height_2 = 75.00,
    ),

    # All positions and sizes of cutout must use measures on the face pointing away from the device, 
    # because that is where also height and width of the backplate are measured.
    #
    # Cutout that splits the backplate into upper and lower part.
    cutout_1 = Measures(
        bottom_left = (0.0, 127.60),
        width = 69.50, # The whole width.
        height = 10.40,
        depth = 10.0 # Enough to cut through everything.
    ),
    # Camera lens section cutout.
    cutout_2 = Measures(
        bottom_left = (14.40, 123.60),
        width = 40.90,
        height = 18.40,
        depth = 10.0, # Enough to cut through everything.
        corner_radius = 4.60
    ),
    # Fingerprint sensor cutout.
    cutout_3 = Measures(
        bottom_left = (24.80, 105.80),
        width = 20.0,
        height = 25.00,
        depth = 10.0, # Enough to cut through everything.
        corner_radius = 6.0
    )
)

backplate = Backplate(cq.Workplane("XZ"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(backplate.top, name = "backplate_top", options = show_options)
show_object(backplate.bottom, name = "backplate_bottom", options = show_options)
