import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures
import utilities # local directory import

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


class XMountPlug:

    def __init__(self, workplane, measures):
        """
        A parametric plug for the Armor-X X-Mount Type-M mounting system.

        Multiple variants of plugs are or will be supported, and can be chosen by adapting the 
        parameters.
        
        During part creation, the origin is at "plate top, plate center". When the part is 
        returned, the origin is however at "stem bottom, stem center" because that helps dependent 
        designs to place the part.

        :param workplane: The CadQuery workplane to create this part on. You can provide a workplane 
            with any rotation and offset, and the part will be mounted on it, with its origin at 
            the origin of the workplane, workplane x axis pointing to the right of the part and 
            workplane y axis pointing to the top of the part.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Simplify the clip mechanism. Instead of letting it go in a 90° bend for the step, 
            let it go straight into the stem. That allows to make the clip lever as wide as the 
            plate above, which avoids the need for support when 3D printing. Also it avoids the 
            need for the slots in the base plate, and the support they need when printing.
        .. todo:: Create a variant with a M3 countersunk bolt going through the stem to mount it 
            somewhere, with the bolt head flush with the plate surface.
        .. todo: Create a variant with a M3 hex bolt embedded, flush with the plate surface. Allows 
            tensioned mechanisms as seen in the Armor-X suction cup holder.
        .. todo:: Support creating dummy objects for mobile device and wall to be able to simulate 
            if the device will fit and can be mounted without hitting the wall.
        """

        cq.Workplane.combine_wires = utilities.combine_wires

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

        plate = (
            cq.Workplane("XY")

            # Adjust the workplane so the plate outline can be placed into its first quadrant.
            .center(-0.5 * m.plate.width, -0.5 * m.plate.depth)

            # Create the plate outline, with the origin in its left bottom corner. CCW direction.
            .polyline([
                (0, 0),
                (0.5 * m.plate.width - 0.5 * m.cutout.width_1, 0),
                (0.5 * m.plate.width - 0.5 * m.cutout.width_2, m.cutout.depth),
                (0.5 * m.plate.width + 0.5 * m.cutout.width_2, m.cutout.depth),
                (0.5 * m.plate.width + 0.5 * m.cutout.width_1, 0),
                (m.plate.width, 0),
                (m.plate.width, m.plate.depth),
                (0, m.plate.depth)
            ])
            .close()
            .extrude(-m.plate.height)

            # Round the corners of the short end of the cutout.
            .edges("|Z and (not <Y) and (not >Y)")
            .fillet(m.cutout.corner_radius)

            # Round the corners of the rectangular base shape.
            .edges("|Z and (<X or >X)")
            .fillet(m.plate.corner_radius)

            .edges(">Z")
            .chamfer(m.plate.chamfer)

            # Cut the slots at the back. Slots are created twice as long, extending past the 
            # plate shape, to have only one end rounded.
            .pushPoints([
                (m.plate.slot_width_pos + 0.5 * m.plate.slot_width, m.plate.depth),
                (m.plate.width - m.plate.slot_width_pos - 0.5 * m.plate.slot_width, m.plate.depth),
            ])
            .slot2D(2 * m.plate.slot_depth, m.plate.slot_width, angle = 90)
            .cutThruAll()
        )

        cutout = (
            cq.Workplane("XY")

            # Adjust the workplane so the plate outline can be placed into its first quadrant.
            .center(-0.5 * m.plate.width, -0.5 * m.plate.depth)

            .polyline([
                (0.5 * m.plate.width - 0.5 * m.cutout.width_1, 0),
                (0.5 * m.plate.width - 0.5 * m.cutout.width_2, m.cutout.depth),
                (0.5 * m.plate.width + 0.5 * m.cutout.width_2, m.cutout.depth),
                (0.5 * m.plate.width + 0.5 * m.cutout.width_1, 0)
            ])
            .close()
            .extrude(-m.cutout.height)

            # Round the corners at the ends of its back edge.
            .edges("|Z and >Y")
            .fillet(m.cutout.corner_radius)
        )

        stem = (
            cq.Workplane("XY")
            .box(m.stem.width, m.stem.depth, m.stem.height, centered = [True, False, False])

            .edges("|Z")
            .fillet(m.stem.corner_radius)

            .translate([0, -0.5 * m.plate.depth + m.stem.depth_pos, - m.stem.height - m.plate.height])

            .cut(cutout)
        )

        # YZ workplane in the center plane of the clip, with the origin at the clip's front top 
        # and the y axis pointing along the global y axis.
        clip_plane = (
            cq.Workplane("XY")
            .transformed(rotate = (0, 90, 0))
            .center(m.plate.height, 0.5 * m.plate.depth - m.clip.thickness)
        )
        clip = (
            clip_plane

            # TODO Due to a bug in combine_wires(), the result of combining wires will be unpredictable 
            # and wrong if there's no object on the stack yet, seemingly because then each add() will 
            # also modify the workplane origin. To be fixed. As a workaround, we provide a wire 
            # pro forma that will be overlapped by whatever wires are added afterwards.
            .rect(0.1, 0.1, centered = False, forConstruction = True)

            # Step height outline.
            .add( 
                clip_plane
                .rect(m.clip.step_height, m.clip.thickness, centered = False, forConstruction = True)
            )
            # Step depth outline.
            .add(
                clip_plane
                .move(m.clip.step_height - m.clip.thickness, 0)
                .rect(m.clip.thickness, m.clip.step_depth, centered = False, forConstruction = True)
            )
            # Clip lever.
            .add(
                clip_plane
                # Go to the future top front corner of the clip lever cross-section.
                .move(m.clip.step_height - m.clip.thickness, m.clip.step_depth)
                .rect(m.clip.thickness, m.clip.lever_length, centered = False, forConstruction = True)
                # Note that rotate() uses global coordinates.
                .rotate(
                    axisStartPoint = (-1, 0.5 * m.plate.depth - m.clip.thickness + m.clip.step_depth, -m.plate.height - m.clip.step_height + m.clip.thickness),
                    axisEndPoint =   ( 1, 0.5 * m.plate.depth - m.clip.thickness + m.clip.step_depth, -m.plate.height - m.clip.step_height + m.clip.thickness),
                    angleDegrees = -m.clip.lever_angle
                )
            )
            # Clip ridge.
            .add(
                clip_plane
                # Draw first the inclined and then the vertical slope of the ridge element.
                .polyline([
                    # Back bottom point.
                    (m.clip.step_height - m.clip.thickness, m.clip.step_depth),
                    # Top of ridge point.
                    (m.clip.step_height - m.clip.thickness - m.clip.ridge_height, m.clip.step_depth - m.clip.ridge_depth),
                    # Front bottom point.
                    (m.clip.step_height - m.clip.thickness, m.clip.step_depth - m.clip.ridge_depth)
                ])
                .close()
            )

            .combine_wires()
            .toPending()
            .extrude(0.5 * m.clip.width, both = True)

            # Chamfer all side edges.
            .edges("(not >Z) and (not |X)")
            .chamfer(m.clip.chamfer)

            # Chamfer the clip step's corner.
            # Filter the edges, then filter the result again. Different from filtering with 
            # "|X and <Y and <Z" in one step, as that would act on all the part's edges.
            .edges("|X and <Y").edges("<Z")
            .chamfer(m.clip.chamfer)

            # Chamfer the clip's back.
            .edges("|X and (>Y or <Z)")
            .chamfer(m.clip.chamfer)
        )

        xmount_plug = (
            plate
            .union(stem)
            .union(clip)

            # Switch the origin from "plate top, plate center" to "stem bottom, stem center".
            # Because this helps dependent code mount our part.
            .translate([
                0, 
                0.5 * m.plate.depth - m.stem.depth_pos - 0.5 * m.stem.depth, 
                m.plate.height + m.stem.height
            ])
        )

        # Move the part from the XY workplane where it was created to the input workplane.
        # Source for this technique: https://github.com/CadQuery/cadquery/issues/425#issuecomment-672977767
        self.model = (
            self.workplane
            .newObject(
                xmount_plug
                .val() # The whole model is a single solid by now, so taking only one value is ok.
                .moved( cq.Location(self.workplane.plane) )
            )
        )


# =============================================================================
# Part Creation
# =============================================================================
cq.Workplane.part = utilities.part

measures = Measures(
    plate = Measures(
        width = 20.40,
        depth = 22.40,
        height = 2.00,
        slot_width = 1.30,
        slot_depth = 8.25,
        slot_width_pos = 2.55,
        corner_radius = 2.80,
        chamfer = 0.60,
    ),
    stem = Measures(
        depth_pos = 1.20, # From front edge of plate.
        width = 13.85,
        depth = 15.50,
        # Height is min. 1.70 to accommodate plate.cutout_height and min. 9.00 to accommodate the 
        # clip's step shape in unclipped position without hitting a flat surface on which the stem 
        # would be mounted.
        height = 9.00,
        corner_radius = 2.80
    ),
    cutout = Measures(
        width_1 = 10.00,
        width_2 = 7.40,
        depth = 9.70,
        height = 3.75,
        corner_radius = 2.80
    ),
    clip = Measures(
        width = 12.70,
        thickness = 2.50, # Measured 2.43 - 2.50 depending on the part.
        chamfer = 0.80,
        step_height = 5.10, # From lower face of baseplate.
        step_depth = 9.50,
        lever_length = 15.00, # Of a rectangular cross-section shape that can be merged with the rest.
        lever_angle = 45,
        ridge_height = 2.20,
        ridge_depth = 2.40
    )
)

xmount_plug = XMountPlug(cq.Workplane("XY"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(xmount_plug.model, name = "xmount_plug", options = show_options)
