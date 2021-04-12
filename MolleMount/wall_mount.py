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

        Print on a side surface (XY plane in the model's original rendering), as only that lays
        the filament so that pushing the clip does not split layers. Everything else will result 
        in a part that is not strong enough. To facilitate printing in that orientation with 
        minimum support, the default measures make the part only as wide as the X-Mount plate.

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Implement drilling the holes into the holder. A good template for the technique 
            can be seen at https://github.com/CadQuery/cadquery/issues/713#issuecomment-814519752 .
            It would be adapted to drill a cskHole() into the center of the face, with an offset 
            and offset angle applied.
        """

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

            .edges("(not >Y) and (>X or <X)")
            .chamfer(m.base.chamfer) # Not a fillet, as that would need low support and not print well.
        )

        xmount_plug = (
            cq.Workplane()
            .copyWorkplane(base_shape.workplaneFromTagged("xmount_plug_interface"))
            .part(xmp.XMountPlug, xmp.measures)
            
            #.rotate((-1, 0, 0), (1, 0, 0), 90)
            # TODO: Rotate the X-Mount according to the inclination of the front surface. The 
            # most comfortable solution would be to create the X-Mount plug on an inclined workplane. 
            # That option has to be implemented in xmount_plug.py first.
        )
        # show_object(xmount_plug, name = "xmount_plug", options = {"color": "yellow", "alpha": 0.8})

        self.model = (
            base_shape
            .union(xmount_plug)
        )


# =============================================================================
# Part Creation
# =============================================================================
cq.Workplane.part = utilities.part

measures = Measures(
    base = Measures(
        depth = 15.00,
        chamfer = 2.80,
        back = Measures(
            width = xmp.measures.plate.width,
            height = 60.00
        ),
        front = Measures(
            width = xmp.measures.plate.width,
            height = xmp.measures.stem.depth,
            angle = -14, # Relative to being parallel to the back surface and wall. Positive for up.
            height_pos_offset = -10.00, # Relative to the center of the back surface.
        ),
        bolt_holes = Measures(
            lower_hole_pos = 10.00, # From lower end of part.
            upper_hole_pos = 10.00, # From upper end of part.
            hole_size = 4.5, # Good for 4 mm wood screws.
            headhole_size = 7.5, # TODO
            head_angle = 90 # Suitable for wood screws.
        )
    ) 
)

wall_mount = WallMount(cq.Workplane("XZ"), measures)
# cq.Workplane("XZ").part(WallMount, measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(wall_mount.model, name = "wall_mount", options = show_options)
