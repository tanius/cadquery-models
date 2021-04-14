import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures
import xmount_plug as xmp # local directory import
import utilities # local directory import

# Selective reloading to pick up changes made between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
# TODO: Only reload these imported libraries if their file changed.
importlib.reload(utilities)
importlib.reload(xmp)

log = logging.getLogger(__name__)


class WallMount:

    def __init__(self, workplane, measures):
        """
        A parametric wall mount for mobile devices, providing an X-Mount Type-M plug.

        3D printing: See part XMountPlug. Like that, this part is designed to be printed on one 
        side (XY plane).

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Add a second part above the top of the current wall holder, with a recess for the 
            top edge of the mobile device and its case. This is to help mounting the device into the 
            holder, by holding the top into the recess, then pushing on the back, and sliding the 
            device downwards. However, in this design the new part blocks the space over the 
            top of the device so that removing it with one hand becomes impossible. To compensate, 
            no clip lever should be used, instead the clip would be operated by sliding the device 
            in and out with some force.
        .. todo:: Adjust the base so that the gap to the lever is so small that bending 
            that lever will allow to unlock the device but not break or permanently deform the 
            lever. For the default lever of the X-Mount plug that would be approx. 5 mm way of 
            travel, as more will cause permanent bending (assuming printing in PETG).
        """

        cq.Workplane.csk_face_hole = utilities.csk_face_hole

        # workplane is unused while building the model, and only utilized towards the end 
        # to position the model. Because to keep the code simple, CAD models should be able to 
        # reference global axis directions inside their code. This is not possible if we already 
        # have to create the model positioned on workplane.
        self.workplane = workplane

        self.debug = False
        self.measures = measures

        m = self.measures
        # TODO: Initialize missing measures with defaults.

        self.build()


    def build(self):
        m = self.measures

        base_shape = (
            cq.Workplane("XZ")

            # Back surface of holder base, centered around the origin.
            .rect(m.base.back.width, m.base.back.height)

            # Front surface of holder base.
            .workplane(offset = m.base.depth)
            .transformed(offset = (0, m.base.front.height_pos_offset, 0)) # Local directions!
            .transformed(rotate = (-m.base.front.angle, 0, 0))
            .tag("xmount_plug_interface")
            .rect(m.base.front.width, m.base.front.height)

            .loft()

            # Edge treatment. Not with fillets, as that would need low support and not print well.
            .edges("not |X").edges("(not <Y) and (not >Y)")
            .chamfer(m.base.chamfer)

            # Drill the upper mount hole.
            .faces("(not |Y) and (not |X)").faces(">Z")
            .csk_face_hole(
                diameter = m.base.bolt_holes.hole_size, 
                csk_diameter = m.base.bolt_holes.head_size,
                csk_angle = m.base.bolt_holes.head_angle,
                offset = (0, m.base.bolt_holes.upper_hole_offset)
            )

            # Drill the lower mount hole.
            .faces("(not |Y) and (not |X)").faces("<Z")
            .csk_face_hole(
                diameter = m.base.bolt_holes.hole_size, 
                csk_diameter = m.base.bolt_holes.head_size,
                csk_angle = m.base.bolt_holes.head_angle,
                offset = (0, m.base.bolt_holes.lower_hole_offset)
            )
        )

        xmount_plug = (
            cq.Workplane()
            .copyWorkplane(base_shape.workplaneFromTagged("xmount_plug_interface"))
            .part(xmp.XMountPlug, xmp.measures)
        )
        # show_object(xmount_plug, name = "xmount_plug", options = {"color": "yellow", "alpha": 0.8})

        self.model = (
            base_shape
            # TODO: In the following, "clean = True" leads to non-manifold shapes if the chamfers 
            # along the base edges are much smaller than those at the stem. To be reported and fixed.
            .union(xmount_plug, clean = False)
        )


# =============================================================================
# Part Creation
# =============================================================================
cq.Workplane.part = utilities.part

measures = Measures(
    base = Measures(
        depth = 15.00,
        chamfer = 0.8,
        back = Measures(
            width = xmp.measures.plate.width,
            height = 75.00
        ),
        front = Measures(
            width = xmp.measures.plate.width,
            height = xmp.measures.lower_stem.depth,
            angle = -14, # Relative to being parallel to the back surface and wall. Positive for up.
            height_pos_offset = 0.00, # Relative to the center of the back surface.
        ),
        bolt_holes = Measures(
            upper_hole_offset = 5.00, # Vertical offset from center of face.
            lower_hole_offset = 0.00, # Vertical offset from center of face.
            hole_size = 4.5, # Good for 4 mm wood screws.
            head_size = 8.6, # Good for 4 mm wood screws.
            head_angle = 90 # Suitable for wood screws with countersunk heads.
        )
    ) 
)

wall_mount = WallMount(cq.Workplane("XZ"), measures)
# cq.Workplane("XZ").part(WallMount, measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(wall_mount.model, name = "wall_mount", options = show_options)
