import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib, copy
from types import SimpleNamespace as Measures
import utilities # local directory import

# Outline shape of an X-Mount Type M plug for smartphones and other small mobile devices.

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
        An Armor-X X-Mount Type M plug.

        X-Mount is a mount system for mobile devices; see https://armor-x.com/. Type M (shown here) 
        is meant for smartphones but has been discontinued by Armor-X and replaced with Type K. 
        Type T is larger and meant for tablets, and as of 2021-05 is still in production. The 
        socket part (see xmount_socket.py) is to be glued to the mobile device, while the plug part 
        becomes part of the various mounts.

        Multiple variants of plugs are or will be supported, and can be chosen by adapting the 
        parameters. With the default parameters and 3D printing in PETG, it needs a relatively 
        strong but still acceptable bending force on the lever to release the device. You can 
        adjust this after printing by successively sanding down the clip ridge and testing until 
        you have a part with the desired holding force.
        
        During part creation, the origin is at "plate top, plate center". When the part is 
        returned, the origin is however at "stem bottom, stem center" because that helps dependent 
        designs to place the part.

        Status: Already includes all corrections from the second test print.

        3D printing: (1) Print this on a side surface (YZ plane in the model's original rendering), as 
        only that lays the filament so that pushing the clip does not split layers. Everything else 
        will result in a part that is not strong enough. (2) Support is only needed inside the cutout 
        of the holder's plate. Carefully remove every last bit of support material from there 
        afterwards, as the plug will otherwise not fit in. (3) It is better to print the whole 
        part raised into the air by 2.0 mm using support, as that prevents the elephant foot effect. 
        Otherwise, the plate will be too thick on one side and has to be sanded down to fit into 
        an X-Mount socket. A raise of 2.0 mm is the minimum that guarantees that the support can 
        later be broken off in one piece. (4) A good material for this is PETG. Don't print it too 
        hot, as that will make it brittle so that the lever will break rather than bend. 243 °C is 
        the perfect spot for MyDroid filament, for example, while 250 °C is too hot.

        Failure modes: When printed on a side surface (YZ plane) in PETG at 245 °C, a 2.5 mm thick 
        lever will bend nicely and not break for at least 10 mm way of travel. A 2.3 mm thick 
        mounting plate will be the weak point. But it can take 30-40 kg of pulling force before 
        breaking, which should be enough for mounting a mobile device. And even then, the break line 
        will not be between two layers, so it's the plastic itself that is breaking, not the layers 
        delaminating.

        :param workplane: The CadQuery workplane to create this part on. You can provide a workplane 
            with any rotation and offset, and the part will be mounted on it, with its origin at 
            the origin of the workplane, workplane x axis pointing to the right of the part and 
            workplane y axis pointing to the top of the part.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        Optional TODOs for later:

        .. todo:: Add something to the end of the lever, such as a near-vertical piece with a circular 
            recess, that simplifies pushing the lever with a single finger to open it when grabbing 
            the device with two other fingers from the top to release it. That enabled one-hand 
            use of the mechanism.
        .. todo:: Add little protruding dots or other elements on the grip surface of the clip 
            lever to provide friction for better grip.
        .. todo:: Add another horizontal piece to the end of the lever, to allow better downward 
            pressure without gliding off with the finger. Or probably better not, as that would 
            interfere with the proposal of adding a part that helps operating the lever from the 
            top edge of the device.
        .. todo:: Create a parameter for ridge top position relative to the top of the plate. 
            Because that's what one wants to configure, while clip height position etc. would be 
            dependent on that. Or even better, make the parameter for configuring locking overlap 
            of the ridge with the counterpart, i.e. necessary ridge movement for unlocking.
        .. todo:: Support creating dummy objects for mobile device and wall to be able to simulate 
            if the device will fit and can be mounted without hitting the wall. The dummy objects 
            should be shown transparent by default.
        .. todo:: Introduce a parameter clip.ridge_depth_pos to position the top of the ridge. This 
            is an important measure, but currently has to be given indirectly by specifying both 
            clip.straight_depth and clip.ridge_base_depth.
        .. todo:: Instead of upper and lower stem, have only one stem but also cutters for cutting 
            the rail outlines into that one stem. That's simpler, avoiding all the issues of 
            knowing where the clip will meet the stems.
        .. todo:: Create a variant without a lever and where the clip ridge has two 45° angles. 
            It is operated by sliding the device in and out with some force. Of course it holds 
            not very tightly to the device then, but for some types of indoor holders that's fine, 
            and it means that operating the mechanism is faster and more comfortable.
        .. todo:: Create a variant with a M3 countersunk bolt going through the stem to mount it 
            somewhere, with the bolt head flush with the bottom of the cutout. An M3 countersunk 
            bolt will fit in there without having to enlarge the hole.
        .. todo: Create a variant with a hex bolt embedded, flush with the cutout bottom. Allows 
            tensioned mechanisms as seen in the Armor-X suction cup holder. An M3 or M4 hex bolt 
            will fit in the cutout without having to enlarge it.

        Optional TODOs for much later:

        .. Add a fillet below the clip lever, where it joins with the stem. That will protect 
            against permanent bending of the lever. Permanent bending was observed at this point.
        .. todo:: Create a variant using a clip made from a spring steel plate rather than from 
            bending plastic. That should be much more durable. However, even the current plastic 
            variant is quite ok.
        .. todo:: Create a variant that can be printed upside down, with the plate surface on the 
            print bed. That is necessary if the typical damage mode for parts printed on the side 
            is from shearing the layers apat where the plate meets the stem. The only change needed 
            for that is a gradual change between upper and lower stem width, to be printable without 
            support. That is best achieved with appropriately shaped cutters and only one stem 
            (see todo item below). The clip can be configured more narrow and will then not 
            interfere with the change in stem width.
              However, even this way of printing it might not be strong enough, as now rattling on 
            the mount still tries to delaminate the layers, but by pull rather than shear and with a 
            larger area. It might be better to directly go to the variant with a stainless steel 
            plate (see below).
        .. todo:: Create a variant where the stem is missing and instead only two guiding 
            edges along the left and right cutout edges are present. The plate would then be 
            provided as a stainless steel or aluminium part made with an angle grinder, mounted 
            with a countersunk M3 bolt and a nut inserted into the part. With the current stem 
            depth, there is (barely) enough space for a M3 bolt going through the plate and stem.
            So it should work with the same bending-plastic clip mechanism.
            This variant should be much more durable, as the current one translates rattling on the 
            mobile device in its holder into shear action between the layers at the section where 
            the plate meets the stem.
        .. todo:: Modify the holder to make it more durable when FDM 3D printed. The holders will 
            then no longer be compatible with X-Mount Type-M, but that is no issue when both plug 
            and socket are 3D printed and because all products with X-Mount Type-M have been 
            discontinued anyway (and there are very few available used), so there is no benefit in 
            keeping up that compatibility. The successor standard X-Mount Type-K should not be 
            used as it's probably patent protected, and the Type-M mount should be modified enough 
            to not fall under any patent protections. That allows commercial use of the design, then. 
            Proposed improvements include:
            (1) No cutout inside the plate. This is more durable, and magnets are not a good idea 
            anyway as it interferes with smartphone pen digitizers. 
            (2) a 45° chamfer instead of a horizontal lower surface of the plate, which will make it 
            much less likely that the plate breaks and allows 3D printing upright without support; 
            (3) a longer plate that inserts into a wedge-shaped socket purely horizontally, which 
            will be more comfortable to insert without looking.
            (4) a wider plate to have a single mount system for both smartphones and tablets, 
            allowing to reuse the holders for all devices e.g. for car navigation.
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

            # Chamfer the lower back edge to help guiding the plate into the X-Mount socket.
            # Using corner radius for this is intended, in order to achieve a guide effect for the 
            # whole front edge incl. around the rounded corners.
            .edges("<Z and >Y")
            .chamfer(length = m.plate.chamfer, length2 = m.plate.corner_radius)

            # Round the corners of the short end of the cutout.
            .edges("|Z and (not <Y) and (not >Y)")
            .fillet(m.cutout.corner_radius)

            # Round the corners of the rectangular base shape.
            .edges("|Z and (<X or >X)")
            .fillet(m.plate.corner_radius)

            # Chamfer all around the upper edges.
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
            .box(m.upper_stem.width, m.upper_stem.upper_depth, m.upper_stem.height, centered = [True, False, False])
            .translate([
                0,
                -0.5 * m.plate.depth + m.upper_stem.depth_pos,
                -m.plate.height - m.upper_stem.height
            ])
            .cut(cutout)

            # Chamfering the vertical back edges as guides when sliding into the X-Mount socket.
            .edges("|Z and >Y")
            .chamfer(m.upper_stem.corner_chamfer)

            # Chamfering the lower back edge to adjust to the required lower depth measure.
            .edges("|X and >Y and <Z")
            .chamfer(length = m.upper_stem.upper_depth - m.upper_stem.lower_depth, length2 = 0.99 * m.upper_stem.height)
            #.fillet(- max(m.upper_stem.upper_depth - m.upper_stem.lower_depth, 0.99 * m.upper_stem.height))
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

            .edges("|Z and (<X or >X)")
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
                    (m.clip.height_pos - m.clip.ridge_height, m.clip.straight_depth - m.clip.ridge_base_depth + m.clip.ridge_top_depth),
                    # Top of ridge point at front.
                    (m.clip.height_pos - m.clip.ridge_height, m.clip.straight_depth - m.clip.ridge_base_depth),
                    # Front bottom point.
                    (m.clip.height_pos, m.clip.straight_depth - m.clip.ridge_base_depth)
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
        depth = 22.20, # Corrected from 22.40, which did not fit in.
        # X-Mount plate heights:
        # – As found in original plugs / mounts: 1.85 - 2.00 mm. 4.03 - 1.56 = 
        # – Available space in X-Mount Type-M v1 sockets: 2.20 - 2.26 mm. Good plate height up to 2.15 mm.
        # – Available space in X-Mount Type-M v2 sockets: 2.55 mm. Good plate height up to 2.40 mm.
        # The v1 sockets are chosen as our standard, as all available original plates mount in there 
        # with minimum wiggle room. Accordingly, we use ~2.15 mm plate thickness.
        height = 1.93, # Prints as 2.12, which is perfect (easy gliding, no play).
        slot_width = 1.30,
        slot_depth = 8.25,
        slot_width_pos = 2.55,
        corner_radius = 2.80,
        chamfer = 0.60,
    ),
    cutout = Measures(
        width_1 = 10.00,
        width_2 = 7.40,
        depth = 10.50, # Corrected from 9.70, which was too short to fit.
        height = 3.75,
        corner_radius = 2.80
    ),
    upper_stem = Measures(
        depth_pos = 0.00, # From front edge of plate. X-Mount original uses 1.20.
        width = 13.85,
        upper_depth = 19.30,
        lower_depth = 15.50, # Same as lower stem depth.
        height = 2.97, # Making it flush with the clip. Min. 1.50 to provide space for sliding into the mount socket.
        corner_chamfer = 2.50
    ),
    lower_stem = Measures(
        depth_pos = 0.00, # From front edge of plate.
        width = 20.40, # Same as plate.width.
        depth = 15.50,
        # Constraint 1: upper_stem.height + lower_stem.height ≥ 1.70 to accommodate cutout.height.
        # Constraint 2: upper_stem.height + lower_stem.height ≥ 9.00 for the clip's horizontal 
        # part (up to the clip ridge) to not hit a flat surface below it while unlocking.
        height = 5.70,
        corner_chamfer = 3.00
    ),
    clip = Measures(
        width = 20.40, # Same as plate.width. 
        thickness = 2.30, # Good for PETG full-width levers. Measured 2.43 - 2.50 on original X-Mount parts, depending on the part.
        chamfer = 0.80,
        # height_pos = 4.90 and ridge_height = 2.30 give a locking overlap of 1.1 mm of the ridge, 
        # which is teh right amount of force for locking / unlocking with a 2.30 mm PETG lever.
        height_pos = 4.90, # From upper face of baseplate to upper face of clip.
        straight_depth = 7.25, # Necessarily horizontal section, from the end of the plate outline to the end of the clip ridge.
        lever_length = 15.00, # Of a rectangular cross-section shape that can be merged with the rest.
        lever_angle = 45,
        ridge_width = 13.50, # Max. 13.90. Original X-Mount has 12.70.
        ridge_height = 2.30, # Max. 3.80 to reach the bottom of the socket counterpart when aligned parallel and touching.
        # Sufficient ridge top depth instead of a pointy ridge means the ridge cannot be worn down 
        # as easily, and will still work when worn a bit.
        ridge_top_depth = 1.50,
        ridge_base_depth = 4.1

        # Another good clip option: height_pos = 4.30, ridge_height = 1.10, thickness = 2.30. With 
        # this, the clip is under slight tension when clipped in, stabilizing the phone in the 
        # holder. Also the opening and closing force is right with PETG. In the original X-Mount, 
        # the clip also does only move 1.10 - 1.30 mm, so that seems enough.
    )
)

xmount_plug = XMountPlug(cq.Workplane("XY"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(xmount_plug.model, name = "xmount_plug", options = show_options)
