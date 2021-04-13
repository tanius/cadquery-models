import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib, copy
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

        .. todo:: Add the guiding chamfers at the back edges of the upper stem again. They are 
            probably needed to guide the plug into the socket.
        .. todo:: Attach the clip lower, and to compensate let the clip shape go up in a 90° bend 
            below the ridge part. The lever would still be attached in its current position, 
            directly to the ridge. That change allows easier removal of support in the variant 
            printed upside down, and allows to use the 45° chamfer between upper and lower stem 
            as the default design. With this, the plug part will have less friction with the 
            socket and will not get stuck when trying to slide it.
        .. todo:: Create a variant that can be printed upside down, with the plate surface on the 
            print bed. That is necessary if the typical damage mode for parts printed on the side 
            is from shearing the layers apat where the plate meets the stem. The only change needed 
            for that is a gradual change between upper and lower stem width, so be printable without 
            support. That is best achieved with appropriately shaped cutters and only one stem 
            (see todo item below). The clip can be configured more narrow and will then not 
            interfere with the change in stem width.
              However, even this way of printing it might not be strong enough, as now rattling on 
            the mount still tries to delaminate the layers, but by pull rather than shear and with a 
            larger area. It might be better to directly go to the variant with a stainless steel 
            plate (see below).
        .. todo:: Create a variant where the plate is missing and instead only two guiding 
            edges along the left and right cutout edges are present. The plate would then be 
            provided as a stainless steel or aluminium part made with an angle grinder, mounted 
            with a countersunk M3 bolt and a nut inserted into the part. With the current stem 
            depth, there is (barely) enough space for a M3 bolt going through the plate and stem.
            So it should work with the same bending-plastic clip mechanism.
            This variant should be much more durable, as the current one translates rattling on the 
            mobile device in its holder into shear action between the layers at the section where 
            the plate meets the stem.
        .. todo:: Create a variant using a clip made from a spring steel plate rather than from 
            bending plastic. That should be much more durable.
        .. todo:: Instead of upper and lower stem, have only one stem but also cutters for cutting 
            the rail outlines into that one stem. That's simpler, avoiding all the issues of 
            knowing where the clip will meet the stems.
        .. todo:: Create a variant with a M3 countersunk bolt going through the stem to mount it 
            somewhere, with the bolt head flush with the bottom of the cutout. An M3 countersunk 
            bolt will fit in there without having to enlarge the hole.
        .. todo: Create a variant with a hex bolt embedded, flush with the cutout bottom. Allows 
            tensioned mechanisms as seen in the Armor-X suction cup holder. An M3 or M4 hex bolt 
            will fit in the cutout without having to enlarge it.
        .. todo:: Support creating dummy objects for mobile device and wall to be able to simulate 
            if the device will fit and can be mounted without hitting the wall. The dummy objects 
            should be shown transparent by default.
        .. todo:: Support to create the straight part and lever part of the clip with different 
            thicknesses. That allows to make the straight part more suited for bending, while 
            keeping the lever part stiff.
        .. todo:: Introduce a parameter clip.ridge_depth_pos to position the top of the ridge. This 
            is an important measure, but currently has to be given indirectly by specifying both 
            clip.straight_depth and clip.ridge_depth.
        """

        cq.Workplane.combine_wires = utilities.combine_wires

        # workplane is unused while building the model, and only utilized towards the end 
        # to position the model. Because to keep the code simple, CAD models should be able to 
        # reference global axis directions inside their code. This is not possible if we already 
        # have to create the model positioned on workplane.
        self.workplane = workplane

        self.debug = False

        # Since we're going to modify measures, we need our own version. Otherwise there will be 
        # nasty side effects by repeated modification, for example when creating the default 
        # model in this file and then when creating another model after importing this file.
        self.measures = copy.deepcopy(measures)
        m = self.measures

        # Adapt the straight depth part of the clip by adding 0.5 the plate depth and determining 
        # the clip start position accordingly. Starting from the center of the plate will never be 
        # wrong, as the stem should have its widest part around there.
        m.clip.depth_pos = 0.5 * m.plate.depth
        m.clip.straight_depth += m.plate.depth - m.clip.depth_pos

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

        upper_stem = (
            cq.Workplane("XY")
            .box(m.upper_stem.width, m.upper_stem.depth, m.upper_stem.height, centered = [True, False, False])
            .translate([
                0,
                -0.5 * m.plate.depth + m.upper_stem.depth_pos,
                -m.plate.height - m.upper_stem.height
            ])
            .cut(cutout)
        )

        lower_stem = (
            cq.Workplane("XY")
            .box(m.lower_stem.width, m.lower_stem.depth, m.lower_stem.height, centered = [True, False, False])
            .translate([
                0,
                -0.5 * m.plate.depth + m.lower_stem.depth_pos,
                -m.plate.height - m.upper_stem.height - m.lower_stem.height
            ])
            .cut(cutout)

            .edges("|Z")
            .chamfer(m.lower_stem.corner_chamfer)
        )

        # YZ workplane in the center plane of the clip, with the origin at the plate top and 
        # at the front of the clip, and the y axis pointing along the global y axis.
        clip_plane = (
            cq.Workplane("XY")
            .transformed(rotate = (0, 90, 0))
            .center(0, -0.5 * m.plate.depth + m.clip.depth_pos)
        )
        clip = (
            clip_plane

            # TODO Due to a bug in combine_wires(), the result of combining wires will be unpredictable 
            # and wrong if there's no object on the stack yet, seemingly because then each add() will 
            # also modify the workplane origin. To be fixed. As a workaround, we provide a wire 
            # pro forma that will be overlapped by whatever wires are added afterwards.
            .move(m.clip.height_pos, 0)
            .rect(0.1, 0.1, centered = False, forConstruction = True)

            # Straight part.
            .add(
                clip_plane
                .move(m.clip.height_pos, 0)
                .rect(m.clip.thickness, m.clip.straight_depth, centered = False, forConstruction = True)
            )
            # Angled lever.
            .add(
                clip_plane
                # Go to the future top front corner of the clip lever cross-section.
                .move(m.clip.height_pos, m.clip.straight_depth)
                .rect(m.clip.thickness, m.clip.lever_length, centered = False, forConstruction = True)
                # Note that rotate() uses global coordinates.
                .rotate(
                    axisStartPoint = (-1, m.clip.straight_depth, -m.clip.height_pos),
                    axisEndPoint =   ( 1, m.clip.straight_depth, -m.clip.height_pos),
                    angleDegrees = -m.clip.lever_angle
                )
            )
            # Clip ridge.
            # TODO: Adjust the clip ridge to be of limited widt, with a 45° start from the sides 
            # to be 3D printable without support.
            # .add(
            #     clip_plane
            #     # Draw first the inclined and then the vertical slope of the ridge element.
            #     .polyline([
            #         # Back bottom point.
            #         (m.clip.height_pos - m.clip.thickness, m.clip.straight_depth),
            #         # Top of ridge point.
            #         (m.clip.height_pos - m.clip.thickness - m.clip.ridge_height, m.clip.straight_depth - m.clip.ridge_depth),
            #         # Front bottom point.
            #         (m.clip.height_pos - m.clip.thickness, m.clip.straight_depth - m.clip.ridge_depth)
            #     ])
            #     .close()
            # )

            .combine_wires()
            .toPending()
            .extrude(0.5 * m.clip.width, both = True)

            # Chamfer all side edges except at the attachment.
            .edges("(not |X) and (not <Y)")
            .chamfer(m.clip.chamfer)

            # Chamfer the clip's back.
            .edges("|X and (>Y or <Z)")
            .chamfer(m.clip.chamfer)

            # Add the ridge.
            .add(
                clip_plane
                # Going CCW, draw (1) the inclined slope upwards, (2) a tiny edge in depth direction so 
                # we can chamfer it away to get the 45° lead-ins, (3) the vertical ridge slope downward. 
                .polyline([
                    # Back bottom point.
                    (m.clip.height_pos, m.clip.straight_depth),
                    # Top of ridge point at back.
                    (m.clip.height_pos - m.clip.ridge_height, m.clip.straight_depth - m.clip.ridge_depth),
                    # Top of ridge point at front.
                    (m.clip.height_pos - m.clip.ridge_height, m.clip.straight_depth - m.clip.ridge_depth - 0.1),
                    # Front bottom point.
                    (m.clip.height_pos, m.clip.straight_depth - m.clip.ridge_depth)
                ])
                .close()
                .extrude(0.5 * m.clip.ridge_width, both = True)

                .edges("|Y and >Z")
                .chamfer(0.99 * m.clip.ridge_height)
            )
        )

        xmount_plug = (
            plate
            .union(upper_stem)
            .union(lower_stem)
            .union(clip)
        )

        # Moving and aligning.
        self.model = (
            self.workplane

            # We need Shape.moved() below. Now wrapping Shape to get a workplane for self.model.
            .newObject(
                xmount_plug

                # Switch the origin from "plate top, plate center" to "stem bottom, stem center".
                # Because this helps dependent code mount our part.
                .translate([
                    0, 
                    0.5 * m.plate.depth - m.lower_stem.depth_pos - 0.5 * m.lower_stem.depth, 
                    m.plate.height + m.upper_stem.height + m.lower_stem.height
                ])

                # Convert from Workplane to Shape.
                # The whole model is a single solid by now, so taking only one value is ok.
                .val()

                # Move the part from the XY workplane where it was created to the input workplane.
                # Source for this technique: https://github.com/CadQuery/cadquery/issues/425#issuecomment-672977767
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
        # Original X-Mount height 1.90 - 2.00. Max. 2.55 for zero-play fit in the socket. But better 
        # a bit more and then grinding down the plate with sandpaper than a wobbly mount.
        height = 2.60,
        slot_width = 1.30,
        slot_depth = 8.25,
        slot_width_pos = 2.55,
        corner_radius = 2.80,
        chamfer = 0.60,
    ),
    cutout = Measures(
        width_1 = 10.00,
        width_2 = 7.40,
        depth = 9.70,
        height = 3.75,
        corner_radius = 2.80
    ),
    upper_stem = Measures(
        depth_pos = 0.00, # From front edge of plate. X-Mount original uses 1.20.
        width = 13.85,
        depth = 15.50,
        height = 1.70 # 1.70 to be flush with clip. Min. 1.50 to provide space for sliding into the mount socket.
    ),
    lower_stem = Measures(
        depth_pos = 0.00, # From front edge of plate.
        width = 20.40, # Same as plate.width.
        depth = 15.50,
        # Constraint 1: upper_stem.height + lower_stem.height ≥ 1.70 to accommodate cutout.height.
        # Constraint 2: upper_stem.height + lower_stem.height ≥ 9.00 for the clip's horizontal 
        # part (up to the clip ridge) to not hit a flat surface below it while unlocking.
        height = 6.30,
        corner_chamfer = 3.00
    ),
    clip = Measures(
        width = 20.40, # Same as plate.width. 
        thickness = 2.50, # Measured 2.43 - 2.50 depending on the part.
        chamfer = 0.80,
        height_pos = 4.30, # From upper face of baseplate to upper face of clip.
        straight_depth = 5.00, # Necessarily horizontal section, from the end of the plate outline to the end of the clip ridge.
        lever_length = 15.00, # Of a rectangular cross-section shape that can be merged with the rest.
        lever_angle = 45,
        ridge_width = 13.50, # Max. 13.90. Original X-Mount has 12.70.
        ridge_height = 2.30, # Max. 3.80 to reach the bottom of the socket counterpart when aligned parallel and touching.
        ridge_depth = 2.40
    )
)

xmount_plug = XMountPlug(cq.Workplane("XY"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(xmount_plug.model, name = "xmount_plug", options = show_options)
