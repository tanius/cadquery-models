import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures
import utilities # local directory import

# Outline shape of an X-Mount Type M socket for smartphones and other small mobile devices.

# Selective reloading to pick up changes made between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
importlib.reload(utilities)

log = logging.getLogger(__name__)

# Do-nothing definition of show_object() when not available, to prevent error messages when 
# including this module from another module. Obviously in such cases, show_object() calls inside 
# this file have no effect, but you'll want to control object visibility from the top level file anyway.
if "show_object" not in globals():
    def show_object(*args, **kwargs):
        pass


class XMountSocket:

    def __init__(self, workplane, measures):
        """
        An Armor-X X-Mount Type M socket (the newer version that includes a loop for a strap).

        X-Mount is a mount system for mobile devices; see https://armor-x.com/. Type M (shown here) 
        is meant for smartphones but has been discontinued by Armor-X and replaced with Type K. 
        Type T is larger and meant for tablets, and as of 2021-05 is still in production. The 
        socket part is to be glued to the mobile device, while the plug part (see xmount_plug.py) 
        becomes part of the various mounts.

        So far this design is only useful to cut holes for inserting an X-Mount socket, since the 
        shape is not yet finished (no center cutout, smaller back cutout, no strap loop but only a 
        bounding-box-like placeholder for it).

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Add the X-Mount cutout for mounting an X-Mount plug.
        .. todo:: Add the side holes in the X-Mount socket for the orange security clips.
        .. todo:: Create a separate design for the orange security clips.
        .. todo:: Support generating a positive X-Mount socket. It should be possible to select with 
            a parameter (in the usual Measures object) if to generate a hole cutter or a positive 
            part.
        .. todo:: Support generating only a cutter for the X-Mount hole, which can be used to cut 
            an X-Mount socket into a phone case etc..
        .. todo:: Create a variant that is much wider and also 10 mm deeper and instead of 
            plastic for the load-bearing rails uses a piece of 1.0 - 1.5 mm stainless steel 
            sheet metal. That should be a stripe of 20 mm width on both sides, or ideally as wide 
            as the phone, and would be glued to the 3D printed part with construction glue. The 
            3D printed part should prepare that by providing space for the construction glue but 
            also the spacers to position the metal piece in the correct position.
              This variant would be much more durable. 3D printing an X-Mount socket might otherwise 
            not lead to plastic parts that are strong enough, as the rails are only 1.0-1.5 mm thick 
            in the original part. To help produce this variant, create a template that can be 
            printed or 3D printed and glued on sheet metal to help cutting it to shape.
        .. todo:: Support holes for magnets (of configurable shape) in the back of the part, where 
            the original X-Mount part also has its magnet.
        """

        self.model = workplane
        self.debug = False
        self.measures = measures
        m = self.measures

        m.back_cutout.height = m.height_step_2 - m.back_cutout.height_step_1
        # Position of the center cutout's start edge, from the back of the part.
        m.center_cutout.depth_pos = m.clip_block.depth_pos + m.clip_block.depth

        # TODO: Initialize missing measures with defaults.

        self.build()


    def build(self):
        m = self.measures
        baseplane = self.model.workplane()

        topface_wire = (
            cq.Workplane("XY")
            .workplane(offset = m.height_step_2)
            .rect(m.width_step_2, m.depth_step_2)
            .extrude(-0.1) # Pro forma to get a solid.
            .edges("|Z")
            .fillet(m.corner_radius)
            .faces(">Z")
            .wires()
        )
        # show_object(topface_wire, name = "topface_wire", options = {"color": "yellow", "alpha": 0.8})

        base_shape = (
            cq.Workplane("XY")

            .rect(m.width_step_1, m.depth_step_1)
            .extrude(m.height_step_1)
            .edges("|Z")
            .fillet(m.corner_radius)

            # Loft from the top of the extrusion to an inset wire of the same shape.
            .faces(">Z").wires().toPending()
            .workplane() # Necessary to prevent a segfault. TODO: Report this issue.
            .add(topface_wire).toPending()
            .loft()

            .edges(">Z")
            .fillet(m.edge_fillet)
        )

        loop_placeholder = (
            cq.Workplane("XY")
            # Depth is 150% of actual loop depth to create a cutter of the full part height even 
            # in the section affected by the edge filleting of the main shape. Depth also includes 
            # a space of m.loop.thickness for the loop to pass through when mounted to the 
            # X-Mount part and that part is inserted into a part cut with this cutter.
            .box(m.loop.width_2, 1.5 * m.loop.depth + m.loop.thickness, m.height_step_2, centered = [True, False, False])
            # Chamfer the edge bordering the space we made for the fabric strap, so that the strap 
            # can easily ride up on the cut-out part when mounting it. Factor 0.99 because the CAD 
            # kernel cannot chamfer away whole faces, and to have vertical edges to round later.
            .edges("|X and <Z").chamfer(0.99 * m.height_step_2)
            # Small corner rounding for the hole this will cut.
            .edges("|Z").fillet(m.loop.corner_radius)
            # Put into place.
            .translate([
                0,
                -0.5 * m.depth_step_1 - m.loop.depth_offset - m.loop.thickness,
                0
            ])
        )

        back_cutout = (
            cq.Workplane("XY")
            # The cutout is only made half as deep as that of the positive X-Mount part. Because 
            # the front half of the back cutout should be kept as free space for clips.
            .box(m.back_cutout.width, 0.5 * m.back_cutout.depth, m.back_cutout.height, centered = [True, False, False])
            # Note, no corner radius here as we're creating only only the back part of the cutout.
            .translate([
                0,
                0.5 * m.depth_step_1 - 0.5 * m.back_cutout.depth,
                m.back_cutout.height_step_1
            ])
        )
        # show_object(back_cutout, name = "back_cutout", options = {"color": "yellow", "alpha": 0.8})

        left_cutout = (
            cq.Workplane("XZ")

            # Create a profile that we can extrude to get the cutout shape.
            # The profile will be in the first quadrant of the XZ plane, suitable for the left 
            # cutout after extruding and moving it in -x direction.
            .move(0, m.side_cutouts.height_step_1)
            .vLineTo(m.height_step_2) # Go to full part height.
            .hLineTo(m.side_cutouts.width_step_2) # Go to max. cutout depth.
            .lineTo(m.side_cutouts.width_step_1, m.side_cutouts.height_step_2)
            .close()

            # Use half the length, since "both" will extrude the given lenghth into EACH direction.
            # Also to simplify the shape, we use the inner depth measure and omit the tapering of 
            # the extrusion. That works because we're creating a cutter here, and it removes more 
            # material than the original positive shape has, so the positive shape will still fit.
            .extrude(0.5 * m.side_cutouts.depth_2, both = True)

            .translate([-0.5 * m.width_step_1, m.side_cutouts.depth_offset, 0])
        )
        # show_object(left_cutout, name = "left_cutout", options = {"color": "yellow", "alpha": 0.8})

        right_cutout = left_cutout.mirror("YZ")
        # show_object(right_cutout, name = "right_cutout", options = {"color": "yellow", "alpha": 0.8})

        self.model = (
            base_shape
            .union(loop_placeholder)
            .cut(back_cutout)
            .cut(left_cutout)
            .cut(right_cutout)

            # Move the model so that the origin is at the center of the area where a holder is 
            # fixed to the X-Mount. Helps positioning it when adding it to another model.
            .translate([
                0,
                -0.5 * m.depth_step_1 + m.center_cutout.depth_pos + 0.5 * m.center_cutout.depth_1,
                0
            ])
        )


# =============================================================================
# Measures and Part Creation
# =============================================================================
cq.Workplane.part = utilities.part

# Note, a lot of these measures are not in use yet as only a hole cutter is generated so far.
# TODO: Unify the parameter naming. Right now we have both the "width_1" style and "width_step_1"
#   style schemes, and they are overlapping.
measures = Measures(
    width_step_1 = 34.15, # At bottom of part.
    width_step_2 = 26.70, # At top of part.
    depth_step_1 = 64.65, # At bottom of part. Ignores belt loop attachment depth.
    depth_step_2 = 55.00, # At top of part.
    height_step_1 = 0.90,
    # Height is 3.90 for the newer Armor-X Type-M socket design, 4.90 for the older.
    height_step_2 = 3.90, # Ignores clip block height.
    corner_radius = 8.20,
    edge_fillet = 5.0, # Edges around the top of the part.

    side_cutouts = Measures(
        depth_offset = -0.9, # Offset from being centered along the left / right edge.
        width_step_1 = 3.00, # At the position where the cutting angle changes.
        width_step_2 = 4.00, # At the top surface of the part.
        depth_1 = 49.50, # Outer depth, imagined at the top surface of the part.
        depth_2 = 42.50, # Inner depth, at the top surface of the part.
        height_step_1 = 0.90, # The layer left uncut at the bottom of the part.
        height_step_2 = 1.70,
        corner_radius = 3.50, # TODO: To confirm after printing. Difficult to measure.
    ),

    # The front half of the back cutout should never be blocked by other parts, to keep the space 
    # for clips that passed the clip block.
    back_cutout = Measures(
        width = 18.00,
        depth = 7.00,
        height_step_1 = 1.32,
        corner_radius = 2.07,
    ),

    front_cutout = Measures(
        depth_step_1 = 4.66, # At the bottom of the cutout.
        depth_step_2 = 5.00, # At the top of the part.
        width = 18.00, # At the top of the part.
        height_step_1 = 1.10,
        corner_radius = 2.07 # Same as the top cutout.
    ),

    center_cutout = Measures(
        width_1 = 13.90,
        width_2 = 20.75,
        depth_1 = 22.5, # Towards the back of the part, where width == width_1.
        depth_2 = 23.2, # Towards the front of the part, where width == width_2.
        cover_height = 1.00,
        cut_depth = 3.20,
        corner_radius = 2.80,
        wedge_width = 9.70, # At the bottom of the cutout.
        wedge_depth = 10.0,
        wedge_chamfer = 0.8,
        wedge_corner_radius = 1.0
    ),

    clip_block = Measures(
        depth_pos = 7.00, # From back of part.
        width = 14.00,
        depth = 3.00, 
        height = 4.70,
        corner_radius = 0.80,
        chamfer_depth = 2.10,
        chamfer_height = 3.00
    ),

    loop = Measures(
        depth_offset = 4.75, # From front edge of the base shape.
        height_offset = 1.15, # From bottom of the main part.
        width_1 = 19.50, # At front side of loop.
        width_2 = 26.20, # At back side of loop.
        depth = 10.50,
        height = 2.35,
        height_cutoff = 0.70, # At its front section.
        thickness = 3.35, # Loop ring strength in the width and depth directions.
        corner_radius = 0.9
    )
)

xmount_socket = cq.Workplane("XY").part(XMountSocket, measures)
show_options = {"color": "lightgray", "alpha": 0}
show_object(xmount_socket, name = "xmount_socket", options = show_options)
