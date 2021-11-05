import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures

# A plate for the Fansteck Galaxy Note9 case providing a Mollemount interface.

log = logging.getLogger(__name__)

class Caseplate:

    def __init__(self, workplane, measures):
        """
        A parametric backplate for cases of smartphones and phablets with a Mollemount interface.
        
        Mollemount is an open design mount system for smartphones and other mobile devices, 
        compatible with the U.S. military PALS / MOLLE system. In addition to providing that, a 
        caseplate like this also adds an extra level of protection to cases that use only 
        thin material on the backside and / or protect sensitive phones with a glass case.

        The design is parametric and can be adapted to most cases by defining plate shapes and sizes 
        and cutout positions and sizes. However, the initial parameters are made for the RedPepper 
        DOT+ Series waterproof case for Samsung Galaxy Note9, allowing to quickly create various 
        shapes and types of backplates for this case. This and identical cases offered by traders 
        under other names can be found at:
        * https://www.aliexpress.com/item/4000271146538.html (9.87 EUR incl. shipping)
        * https://www.aliexpress.com/item/32916521981.html (11.06 EUR incl. shipping)
        * https://www.amazon.com/dp/B07G33YSJR (16.59 USD + 9.61 international shipping from USA)
        * https://www.lightinthebox.com/en/p/_p8357432.html (out of stock)

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Add rounded corners for the cutout that corresponds to the horizontal bar at the 
            back of the case.
        .. todo:: Fix that currently the workplane is passed to this constructor as "workplane", 
            but selectors in this class use global axis directions. To fix this, create the 
            part in the XZ plane, and only when finished, rotate and translate it to be positioned 
            at the origin of the plane provided in the "workplane" parameter. Ideally, that action 
            would be provided by the part() method.
        .. todo:: Add mockup parts for the Mollemount straps, for illustration.
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

        cutout_7 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_7.width, m.cutout_7.height, m.cutout_7.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_7.corner_radius)
            .translate([m.cutout_7.bottom_left[0], 0, m.cutout_7.bottom_left[1]])
        )
        show_object(cutout_7, name = "cutout_7", options = {"color": "yellow", "alpha": 0.8})

        cutout_8 = (
            cq.Workplane()
            .copyWorkplane(baseplane)
            .box(m.cutout_8.width, m.cutout_8.height, m.cutout_8.depth, centered = [False, False, False])
            .edges("|Y").fillet(m.cutout_8.corner_radius)
            .translate([m.cutout_8.bottom_left[0], 0, m.cutout_8.bottom_left[1]])
        )
        show_object(cutout_8, name = "cutout_8", options = {"color": "yellow", "alpha": 0.8})

        # Create the main shape.
        self.model = plate_1.union(plate_2)
        if (m.plate_3 is not None):
            self.model = self.model.union(plate_3)

        # Create the cutouts.
        # TODO: Create these cutouts in a for loop, not in a sequence.
        # TODO: Use cutThruAll() with 2D wires instead of cut(). The paradigm is not CSG! 
        #   This still allowed tapered cutting, giving the same effect as chamfered edges.
        #   However, this also requires a way to fillet() the corners of the 2D wires before 
        #   using them for cutThruAll(), as otherwise selecting the edges to fillet afterwards 
        #   becomes complicated (at least needing tagging). And that way does not exist yet.
        if (m.cutout_1.enabled): self.model = self.model.cut(cutout_1)
        if (m.cutout_2.enabled): self.model = self.model.cut(cutout_2)
        if (m.cutout_3.enabled): self.model = self.model.cut(cutout_3)
        if (m.cutout_4.enabled): self.model = self.model.cut(cutout_4)
        if (m.cutout_5.enabled): self.model = self.model.cut(cutout_5)
        if (m.cutout_6.enabled): self.model = self.model.cut(cutout_6)
        if (m.cutout_7.enabled): self.model = self.model.cut(cutout_7)
        if (m.cutout_8.enabled): self.model = self.model.cut(cutout_8)

        # Create the cutouts for stitching between the two MOLLE columns.
        for row in range(m.molle_rows):
            cutout = (
                cq.Workplane()
                .copyWorkplane(baseplane)
                .box(m.molle_stitching_width, m.molle_stitching_height, 10.00, centered = [False, False, False])
                # Create a slot-like shape with rounded ends, emulated by rounding the corners nearly 
                # as much as possible, that is each corner radius covering half the width of the shape.
                .edges("|Y").fillet(0.49 * m.molle_stitching_width)
                .translate([
                    0.5 * m.width - 0.5 * m.molle_stitching_width, 
                    0, 
                    m.molle_offset + (0.5 * (m.molle_height - m.molle_stitching_height)) + row * m.molle_height
                ])
            )
            self.model = self.model.cut(cutout)
            # show_object(cutout_8, name = "cutout_…", options = {"color": "yellow", "alpha": 0.8})
            # TODO: In the above, dynamically generate the right name for the cutout.

        self.model = (
            self.model
            # .faces("<Y")
            # .workplane()
            # TODO: Move workplane origin to global origin.
            # TODO: Create three lines of sewing holes in m.sewing_step distance, starting at 
            # m.molle_offset. Lines should be in m.molle_width distance.
        )

        # Split the model into two at a place where a MOLLE strap boundary is expected.
        self.top = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = m.split_height)
            .split(keepTop = True)
        )
        self.bottom = (
            self.model
            .copyWorkplane(cq.Workplane("XY"))
            .workplane(offset = m.split_height)
            .split(keepBottom = True)
        )

# =============================================================================
# Part Creation
# =============================================================================

# Measures that you can reference when defining the other measures below.
m = Measures()
# Total width at the widest point. Covering the case's chamfered section, and close enough to two 
# MOLLE columns (76 mm).
m.width = 77.30
m.glue_thickness = 0.5 # All parts are meant to be glued with a certain glue thickness, to be subtracted from part height.
m.molle_depth = 1.00 # Thickness of the MOLLE straps used.
m.molle_height = 25.40 # MOLLE belt material is 1 inch high.
m.molle_rows = 5
# Start of the MOLLE loops from the lower edge of the model. Here offset to accommodate the 
# rounded edges, which are too close together to allow two MOLLE loops in between.
m.molle_offset = 3.20

# Main measures definition section.
# TODO: Let all coordinates refer to the bottom left corner of the case's back as (0,0). Otherwise, 
# adapting the size of one plate requires adjusting all offsets.
measures = Measures(
    # Include the measures that were defined first. Can also be done this way in other places.
    # It's redundant but makes sure all measures are accessible from one data structure.
    width = m.width,
    glue_thickness = m.glue_thickness,
    molle_height = m.molle_height,
    molle_depth = m.molle_depth,
    molle_offset = m.molle_offset,
    molle_rows = m.molle_rows,
    
    molle_column_width = 25.40 * 1.5, # MOLLE columns are 1.5 inches wide.
    # Width of cutout for the seam between MOLLE columns. The typical seam is a very dense zigzag 
    # type of 3.0 mm width.
    molle_stitching_width = 3.50,
    molle_stitching_height = 18.00, # Width of cutout for the seam between MOLLE columns.

    split = True,
    split_height = 131.75, # Split at the bottom of cutout_1.

    # PLATES
    # To simplify the shape we need:
    # (1) For simplicity, no m.molle_depth is deducted from any depth measures. Since in practice the 
    # whole part is raised by m.molle_depth because it is mounted on top of a layer of MOLLE straps, 
    # this only influences the part's position but not geometry, so can be ignored.
    # (2) The inner plate "plate_1" is made flat, only cut by the camera section cutout. Everything 
    # else will be filled by glue when mounting. This means there is 1.2 mm space below that plate 
    # initially, raised by 1.0 mm due to MOLLE straps lifting the upper plate, and lowered by 1.0 mm 
    # by the MOLLE straps below the lower plate. This means 1.2 mm glue, which is fine.

    # Front-facing (towards the screen) plate element, mounted into the recess at the case back.
    plate_1 = Measures(
        # Width is reduced by the thickness of MOLLE strap material to make room for it passing 
        # this plate to go under it.
        width = 69.50 - 2 * m.molle_depth,
        height = 154.50, # Corrected from 155.20.
        # 1.90 mm is the max. concave depth at the back of this case, from the highest point around 
        # the edges to the lowest point at the transparent parts. Plate_2 will be created above 
        # this level, in effect protruding over the case's back.

        # Plate_1 height is just the distance from inserts on the case back to case edge height.
        depth = 0.70,
        bottom_left = (3.90, 4.25), # To center it within plate_2.
        corner_radius = 2.50,
        edge_chamfer = 0.65, # Edge around the surface touching the device.
    ),

    # Back-facing (away from screen) plate element, covering the back up to the edge of the chamfered 
    # section of the case, leaving an edge of the original case visible.
    plate_2 = Measures(
        width = m.width,
        height = 163.00,
        depth = 1.0, # Means 5 layers at 0.2 mm thickness.
        bottom_left = (0.00, 0.00), # Largest plate, defines origin against which others are offset.
        corner_radius = 6.00,
        edge_chamfer = 0.50, # For the edge on the face pointing away from the device. Cannot be 0.
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
    # TODO: Support giving the cutouts names as part of their definitions. This is useful to 
    # generate and name corresponding visible cutter shapes.
    # TODO: Support an arbitrary amount of cutouts, all with the same parameters.
    # TODO: Support edge chamfering of the back edge of these cutouts. To not be limited to 45° 
    # angles, this requires creating the cutters as loft between two wires, or to use cutThruAll() 
    # with a wire and the tapering option.
    # TODO: Support 0.00 for the corner radii of cutouts, by capturing that case and not doing any 
    # filletting in such a case.

    # Cutout that splits the case back into upper and lower parts.
    cutout_1 = Measures(
        enabled = False,
        bottom_left = (3.9, 131.75),
        width = 69.50, # The whole width of plate_1.
        height = 12.20,
        # 1.2 mm is the physical depth of the shape to make room for, but the plate to be glued 
        # here hovers by glue_thickness.
        depth = 1.20 - m.glue_thickness
        # TODO: Adapt to include a glue layer at the top of this part.
    ),
    # Camera lens section cutout, sized according to the Redpepper case insert at the back.
    cutout_2 = Measures(
        enabled = False,
        bottom_left = (17.40, 126.75),
        width = 42.70,
        height = 20.20,
        depth = 10.0, # Generous amount, making sure to cut through everything.
        corner_radius = 2.20 # Corrected from 4.60.
    ),
    # Camera lens section cutout, minimum size to not obstruct the camera or LED.
    # Size is kept inside cutout_1, so not obstructing the space reserved for MOLLE loops.
    cutout_3 = Measures(
        enabled = True,
        bottom_left = (19.40, 131.75),
        width = 38.70,
        height = 12.20,
        depth = 10.0, # Generous amount, making sure to cut through everything.
        corner_radius = 2.20
    ),
    # Fingerprint sensor cutout.
    cutout_4 = Measures(
        enabled = False,
        bottom_left = (27.80, 108.95),
        width = 21.80,
        height = 26.80,
        # 1.2 mm is the physical depth of the shape to make room for, but the plate to be glued 
        # here hovers by glue_thickness.
        depth = 1.20 - m.glue_thickness,
        corner_radius = 6.00
    ),
    # Left camera cutout (as seen when looking at the device back).
    # Has no effect when letting the camera lens section cut through everything.
    cutout_5 = Measures(
        enabled = False,
        bottom_left = (22.80, 133.30),
        width = 9.00,
        height = 9.00,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 4.40
    ),
    # Right camera cutout (as seen when looking at the device back).
    # Has no effect when letting the camera lens section cut through everything.
    cutout_6 = Measures(
        enabled = False,
        bottom_left = (33.70, 133.30),
        width = 9.00,
        height = 9.00,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 4.40
    ),
    # Camera LED cutout (as seen when looking at the device back).
    # Has no effect when letting the camera lens section cut through everything.
    cutout_7 = Measures(
        enabled = False,
        bottom_left = (44.20, 132.50),
        width = 10.50,
        height = 10.50,
        depth = 10.00, # To be sure to cut through everything.
        corner_radius = 2.00
    ),
    # Cutout to make space for the overlapping MOLLE loops at the bottom of the device.
    cutout_8 = Measures(
        enabled = True,
        bottom_left = (0.5 * m.width - 0.5 * 1.2 * m.molle_height, m.molle_offset),
        width = 1.2 * m.molle_height, # To create a 25×25 mm section where MOLLE loops are sewn together.
        height = m.molle_rows * m.molle_height,
        # Since there is already a total of 2.20 mm space below plate_1 without this coutout, we only 
        # need to add very little depth to have some more space for glue.
        depth = 0.40,
        corner_radius = 0.10 # Cannot be zero.
    ),
)

caseplate = Caseplate(cq.Workplane("XZ"), measures)

show_options = {"color": "lightgray", "alpha": 0}

if not measures.split:
    show_object(caseplate.model, name = "caseplate", options = show_options)
else:
    show_object(caseplate.top, name = "caseplate_top", options = show_options)
    show_object(caseplate.bottom, name = "caseplate_bottom", options = show_options)
