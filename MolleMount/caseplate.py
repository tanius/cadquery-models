import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures

# A plate for the Fansteck Galaxy Note9 case providing a Mollemount interface.

log = logging.getLogger(__name__)

class Caseplate:

    def __init__(self, workplane, measures):
        """
        A simple, parametric backplate for cases of smartphones and phablets, adding a Mollemount 
        interface to the case and also adding an extra level of protection to cases that use only 
        thin material on the backside.

        Mollemount is an open design mount system for smartphones and other mobile devices, 
        compatible with the U.S. military PALS / MOLLE system.

        The initial parameters make this suitable for the following case model: RedPepper DOT+ 
        Series waterproof case for Samsung Galaxy Note9, and identical cases from other traders. 
        As offered at:
        * https://www.aliexpress.com/item/4000271146538.html (9.87 EUR incl. shipping)
        * https://www.aliexpress.com/item/32916521981.html (11.06 EUR incl. shipping)
        * https://www.amazon.com/dp/B07G33YSJR (16.59 USD + 9.61 international shipping from USA)
        * https://www.lightinthebox.com/en/p/_p8357432.html (out of stock)

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Add the actual Mollemount interface elements to this design.
        .. todo:: Add mockup parts for the Mollemount straps.
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

        plate_1 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.plate_1.width, m.plate_1.height, m.plate_1.depth, centered = [False, False, False])

            # Corner roundings.
            # TODO: Fix that the corner angle where the cutouts intersect has to be smaller than this.
            .edges("|Y")
            .fillet(m.plate_1.corner_radius)

            # Tapering off towards the face mounted to the device.
            .faces(">Y")
            .edges()
            # Due to a bug we cannot use asymmetric chamfering here, as the "length" and "length2"
            # parameters would be internally switched for some edges. So we do a simple 45° chamfer.
            .chamfer(m.plate_1.edge_chamfer)
            # TODO: Report and fix the bug mentioned above, then do the chamfering like this:
            #.chamfer(length = 0.5 * m.front_edge_chamfer, length2 = 0.95 * m.depth_1)
            # TODO: Don't do the chamfer if the measure given is zero.
            # TODO: Also utilize back_edge_chamfer if present. If both are present, the part depth 
            #   has to be split half and half between them.

            # Translate according to the specified offsets of its bottom left corner.
            .translate([
                m.plate_1.bottom_left[0], 
                0, 
                m.plate_1.bottom_left[1]
            ])
        )

        plate_2 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.plate_2.width, m.plate_2.height, m.plate_2.depth, centered = [False, False, False])

            # Corner roundings.
            # TODO: Fix that the corner angle where the cutouts intersect has to be smaller than this.
            .edges("|Y")
            .fillet(m.plate_2.corner_radius)

            # Tapering off towards the face mounted to the device.
            # (See analogous step for plate_1 for hints and TODO items.)
            .faces("<Y")
            .edges()
            .chamfer(m.plate_2.edge_chamfer)

            # Translate according to the specified offsets of its bottom left corner (x and z 
            # components) and to start at the back surface of plate_1 (y component).
            .translate([
                m.plate_2.bottom_left[0], 
                -0.99 * m.plate_1.depth,
                m.plate_2.bottom_left[1]
            ])
        )

        # A "bump" at the top of the box base shape. Needed to have enough material to 
        # reach into the side and top cutouts of the X-Mount shape, to help keep it in place.
        # TODO: Use a spline instead of a simple loft to create this bump.
        if (m.plate_3 is not None):
            plate_3 = (
                cq.Workplane()
                .copyWorkplane(baseplane)

                # Move to the center of the lower rectangle, then draw it.
                .moveTo(
                    x = m.plate_3.bottom_left_1[0] + 0.5 * m.plate_3.width_1,
                    y = m.plate_3.bottom_left_1[1] + 0.5 * m.plate_3.height_1
                )
                .rect(m.plate_3.width_1, m.plate_3.height_1)

                # Move to the center of the lower rectangle, then draw it.
                .workplane(offset = m.plate_3.depth)
                .moveTo(
                    x = m.plate_3.bottom_left_2[0] + 0.5 * m.plate_3.width_2,
                    y = m.plate_3.bottom_left_2[1] + 0.5 * m.plate_3.height_2
                )
                .rect(m.plate_3.width_2, m.plate_3.height_2)

                .loft()

                # Translate to start at the back surface of the plate_1 + plate_2 combination.
                .translate([0, -0.99 * (m.plate_1.depth + m.plate_2.depth), 0])
            )
            show_object(plate_3, name = "plate_3", options = {"color": "yellow", "alpha": 0.8})

        # TODO: Create the cutouts iteratively.

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

        cutout_4 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_4.width, m.cutout_4.height, m.cutout_4.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_4.corner_radius)
            .translate([m.cutout_4.bottom_left[0], 0, m.cutout_4.bottom_left[1]])
        )
        show_object(cutout_4, name = "cutout_4", options = {"color": "yellow", "alpha": 0.8})

        cutout_5 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_5.width, m.cutout_5.height, m.cutout_5.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_5.corner_radius)
            .translate([m.cutout_5.bottom_left[0], 0, m.cutout_5.bottom_left[1]])
        )
        show_object(cutout_5, name = "cutout_5", options = {"color": "yellow", "alpha": 0.8})

        cutout_6 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_6.width, m.cutout_6.height, m.cutout_6.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_6.corner_radius)
            .translate([m.cutout_6.bottom_left[0], 0, m.cutout_6.bottom_left[1]])
        )
        show_object(cutout_6, name = "cutout_6", options = {"color": "yellow", "alpha": 0.8})

        # Create the main shape.
        self.model = plate_1.union(plate_2)
        if (m.plate_3 is not None):
            self.model = self.model.union(plate_3)

        # Create the cutouts.
        # TODO: Use cutThruAll() with 2D wires instead of cut(). The paradigm is not CSG! 
        #   However, this requires a way to fillet() the corners of the 2D wired before 
        #   using them for cutThruAll(), as otherwise selecting the edges to fillet afterwards 
        #   becomes complicated (at least needing tagging). And that way does not exist yet.
        self.model = (
            self.model
            .cut(cutout_1)
            .cut(cutout_2)
            .cut(cutout_3)
            .cut(cutout_4)
            .cut(cutout_5)
            .cut(cutout_6)
        )

        # Split the model into two at a place where a MOLLE strap boundary is expected.
        self.top = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = 3 * m.molle_width + m.molle_offset)
            .split(keepTop = True)
        )
        self.bottom = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = 3 * m.molle_width + m.molle_offset)
            .split(keepBottom = True)
        )

# =============================================================================
# Part Creation
# =============================================================================

# All parts are meant to be glued with a certain glue thickness, so will be created hovering by 
# that amount.
glue_thickness = 0.50

measures = Measures(
    molle_width = 25.40,
    # Start of the MOLLE loops from the lower edge of the model. Here offset to accommodate the 
    # rounded edges, which are too close together to allow two MOLLE loops in between.
    molle_offset = 3.20,

    # PLATES

    # Front-facing (towards the screen) plate element, mounted into the recess at the case back.
    plate_1 = Measures(
        width = 69.50,
        height = 154.50, # Corrected from 155.20.
        # 1.92 mm is the max. concave depth at the back of this case. We don't want glue at the 
        # very edge of the backplate for optical reasons, so use 1.92 for the height of the inner 
        # plate element.
        depth = 1.90 - glue_thickness, # Results in 1.4, means 7 layers at 0.2 mm thickness.
        bottom_left = (7.00, 7.50), # To center it within plate_2.
        corner_radius = 2.50,
        edge_chamfer = 1.35, # Edge around the surface touching the device.
    ),

    # Back-facing (away from screen) plate element, covering the whole back.
    plate_2 = Measures(
        width = 83.50, 
        height = 169.50, 
        depth = 1.4, # Means 7 layers at 0.2 mm thickness.
        bottom_left = (0.00, 0.00), # It's the largest plate, against which others are offset.
        corner_radius = 9.00,
        edge_chamfer = 0.95, # Edge around the surface pointing away from the device.
    ),

    # Plate to thicken the material on top of plate 1 and plate 2 in the shape of a truncated 
    # pyramid. Can be used to reinforce or level out an area for inserting a mount system attachment. 
    # Optional. Set to "None" to not use.
    # TODO: Due to a CAD kernel issue, the shape must not overlap with corners that are to be 
    # rounded afterwards. Otherwise no model can be calculated. This should be fixed at some time.
    # plate_3 = Measures(
    #     depth = 2.00, # Maximum depth, used in the center of the part.
    #     bottom_left_1 = (0, 3.0), # Positioning the bottom of the truncated pyramid.
    #     width_1 = 69.50, # The whole part width.
    #     height_1 = 121.0,
    #     bottom_left_2 = (0.5 * (69.50 - 42.00), 20.0), # Positioning the top of the truncated pyramid.
    #     width_2 = 42.00,
    #     height_2 = 75.00,
    # ),
    plate_3 = None,

    # CUTOUTS
    # All cutouts are cut with equal cross-section over theor whole depth. All bottom_left corner 
    # positions refer to the largest plate (here plate_2) as defining the origin.
    # TODO: Support an arbitrary amount of cutouts, all with the same parameters.

    # Cutout that splits the backplate into upper and lower part.
    cutout_1 = Measures(
        bottom_left = (7.0, 135.20),
        width = 69.50, # The whole width.
        height = 12.20,
        # 1.2 mm is the physical depth of the shape to make room for, but the plate to be glued 
        # here hovers by glue_thickness.
        depth = 1.2 - glue_thickness
    ),
    # Camera lens section cutout.
    cutout_2 = Measures(
        bottom_left = (20.50, 130.20),
        width = 42.70,
        height = 20.20,
        # 1.2 mm is the physical depth of the shape to make room for, but the plate to be glued 
        # here hovers by glue_thickness.
        depth = 1.2 - glue_thickness,
        corner_radius = 4.60
    ),
    # Fingerprint sensor cutout.
    cutout_3 = Measures(
        bottom_left = (30.90, 112.40),
        width = 21.80,
        height = 26.80,
        # 1.2 mm is the physical depth of the shape to make room for, but the plate to be glued 
        # here hovers by glue_thickness.
        depth = 1.20 - glue_thickness,
        corner_radius = 6.00
    ),
    # Left camera cutout (as seen when looking at the device back).
    cutout_4 = Measures(
        bottom_left = (25.90, 136.30),
        width = 9.00,
        height = 9.00,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 4.40
    ),
    # Right camera cutout (as seen when looking at the device back).
    cutout_5 = Measures(
        bottom_left = (36.80, 136.30),
        width = 9.00,
        height = 9.00,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 4.40
    ),
    # Camera LED cutout (as seen when looking at the device back).
    cutout_6 = Measures(
        bottom_left = (47.30, 135.50),
        width = 10.50,
        height = 10.50,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 2.00
    ),
)

caseplate = Caseplate(cq.Workplane("XZ"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(caseplate.top, name = "caseplate_top", options = show_options)
show_object(caseplate.bottom, name = "caseplate_bottom", options = show_options)
