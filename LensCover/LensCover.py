import cadquery as cq
import logging
import importlib
import utilities
from types import SimpleNamespace as Measures
from math import sin, cos, radians

# An eye cover that can be hooked to the top edge of eyeglasses.
#
# To use this design, you need Python, CadQuery (https://cadquery.readthedocs.io/en/latest/) and 
# ideally also CQ-Editor, the CadQuery IDE (https://github.com/CadQuery/CQ-editor).
#
# License: Unlicence and Creative Commons Public Domain Dedication (CC-0).
#
# Tasks for now
# TODO: Add a 45° section at the lower edge of all cross-section profiles that allows to sew on a 
#   flexible element for blocking out light below the eye.
#
# Tasks for later
# TODO: Add documentation for all methods.
# TODO: Add the general edge chamfering.
# TODO: Add sewing holes along the upper horizontal surface and on the lower 45° angled surface, 
#  for sewing on flexible parts that block out light entering from below and above the glasses.
# TODO: Implement vertical arcing for the outside of the cover. But not really needed in practice.
# TODO: Add the chamfers to the lower corner of the lens.
# TODO: Improve how space is made for the stem-to-lens frame element of 1.2 mm additional thickness.
# TODO: Add a clip that connects to the bottom of the glasses lens. Can be done by 
#     adjusting the shape of the "hook" profile used for the sweep.
# TODO: Replace the bent section between lens and stem cover with a spline that smoothly 
#     continues to both the lens and stem cover sections.

measures = Measures(
    part_name = "lens_cover",
    color = "steelblue",
    alpha = 0.0,
    debug = True,

    side = "left", # "left" or "right". TODO: Implement "right" using mirroring.
    thickness = 1.6, # For FDM, that's two walls with a 0.4 mm nozzle. Corrected from 0.8.
    edge_smoothing = 0.4, # For all edges, to make them nicer to the touch.
    lens_cover = Measures(
        # Lens width 58.3 mm + stem corner width 5.6 mm - stem cover width 6.1 mm.
        # Corrected from 55.5 mm
        width = 57.8,
        height = 35.3, # Corrected from 33.5
        vertical_arc_height = 1.7, # TODO: Implement that this is utilized, then reduce hook_depth.
        horizontal_arc_height = 2.3,
        inner_edge_chamfer_x = 5.0,
        inner_edge_chamfer_y = 25.0,
        # Only small radii possible due to a bug. Cornercase radii may may result in non-manifoldness.
        lower_corner_radius = 2.0, 
        hook_depth = 4.6, # Lens thickness 2.9 mm, vertical arc height 1.7 mm.
        hook_height = 8.0,
    ),
    corner_cover = Measures(
        height = 33.5,
        hook_depth = 4.6, # Adapted visually to create a corner. Corrected from 7.0.
        hook_height = 11.0, # Middle between lens cover and stem cover hook heights.
    ),
    stem_cover = Measures(
        depth = 40.0, # Measured from the lens cover back plane.
        height = 33.5,
        stem_angle = 100,
        lower_corner_radius = 12.0,
        hook_depth = 4.5, # Measured glasses stem width is 3.8 mm.
        hook_height = 14.0,
        hook_height_infill = 5.4,
    ),
)


# Selective reloading to pick up changes made between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
importlib.reload(utilities)

class EyeCover:

    def __init__(self, workplane, measures):
        """
        A parametric eye cover that can be hooked to the top edge of eyeglasses.
        
        :param workplane: The CadQuery workplane to create the eye cover on. This workplane is 
            assumed to be coplanar with the face of the eyeglass user, with the plane's normal 
            pointing into the "front" direction of the model.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object. See example above for the possible attributes.
        """

        self.model = workplane
        self.measures = measures
        self.log = logging.getLogger(__name__)
        m = self.measures

        # Points on the sweep path that we'll need repeatedly.
        m.lens_startpoint = (0, 0)
        # We create a space for the rounded edge that is 60-70% of the wrap radius, to achieve a 
        # smooth shape transition for angles slightly larger than 90°.
        m.lens_endpoint = (-m.lens_cover.width, 0)
        m.stem_startpoint = (-m.lens_cover.width, -m.lens_cover.hook_depth - 2 * m.thickness)

        self.build()

    
    def profile_wire(self, height, hook_depth, hook_height, hook_height_infill = 0.1):
        """
        Object of class Wire, representing the base shape of the hook.

        A multi-section sweep requires wires placed along the path to use for the shape-adapted 
        sweeping. These wires should be orthogonal to the path to get the desired shape.
        """
        # Note that translate() uses global (!) coordinates.
        # hook_height_infill is by default 0.1 just because the CAD kernel cannot handle 0 here.

        # TODO: Create a profile with a curved section. Proposal: Use swipe() and 
        # convert a face of the resulting 3D shape back into a wire.
        
        m = self.measures

        wire = (
            cq.Workplane("YZ")

            # Covering outer element of the profile.
            .rect(m.thickness, height, forConstruction = True)
            .translate((0, -0.5 * m.thickness, -0.5 * height))
            .toPending()
            
            # Horizontal element of the hook.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(hook_depth + 2 * m.thickness, m.thickness, forConstruction = True)
            .translate((0, -0.5 * (hook_depth + 2 * m.thickness), -0.5 * m.thickness))
            .toPending()
            
            # Vertical element of the hook with the tip.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(m.thickness, hook_height + m.thickness, forConstruction = True)
            # -0.499 instead of -0.5 due to a malfunction of union_pending() when having a complete 
            # intersection in this corner. Strangely, only for this corner.
            .translate((0, -hook_depth - 1.5 * m.thickness, -0.499 * (hook_height + m.thickness)))
            .toPending()

            # Infill for the hook.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(hook_depth + 2 * m.thickness, hook_height_infill, forConstruction = True)
            # 0.99 because otherwise union_pending() cannot create a result. This happens due to 
            # the CAD kernel limitations of unioning edges that are exactly in the same location.
            .translate((0, -0.5 * (hook_depth + 2 * m.thickness), - 0.5 * hook_height_infill - 0.99 * m.thickness))
            .toPending()

            .union_pending()
            .ctx.pendingWires[0]
        )

        return wire

    
    # Wire at the start of the sweep, defining the lens cover cross-section next to the nose.
    def lens_start_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([
                self.profile_wire(
                    height = m.lens_cover.height,
                    hook_depth = m.lens_cover.hook_depth,
                    hook_height = m.lens_cover.hook_height
                )
            ])
            .wires()
            .val()
        )

        if m.debug: show_object(wire, name = "lens_start_wire")
        return wire

    
    # Wire at the end of the lens / start of the bent section.
    # Position is slightly approximate as it treats the path as made from straight lines.
    def lens_end_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.lens_cover.height,
                # TODO: Make a parameter out of the "+ 1.4" in the following.
                hook_depth = m.lens_cover.hook_depth + 1.4, # 1.2 mm for frame attachmemt.
                hook_height = m.lens_cover.hook_height
            )])
            .translate((*m.lens_endpoint, 0))
            .translate((0, 1.4, 0)) # TODO: Make this parametric.
            .val()
        )

        if m.debug: show_object(wire, name = "lens_end_wire")
        return wire


    # Wire at the end of the lens / start of the bent section.
    # Position is slightly approximate as it treats the path as made from straight lines.
    def corner_center_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.corner_cover.height,
                hook_depth = m.corner_cover.hook_depth,
                hook_height = m.corner_cover.hook_height
            )])
            # Move the wire to the +y part so we can rotate around origin to rotate around the 
            # back edge.
            .translate((0, m.corner_cover.hook_depth + 2 * m.thickness, 0))
            # Rotate around the back edge of the initial wire, now at origin.
            .rotate((0, 0, 1), (0, 0, -1), -45)
            # Bring the wire into its final position.
            .translate((*m.lens_endpoint, 0))
            .translate((0, -m.lens_cover.hook_depth - 2 * m.thickness, 0))
            .val()
        )

        if m.debug: show_object(wire, name = "corner_center_wire")
        return wire

        
    # Wire at the start of the stem cover / end of the bent section.
    # Position is slightly approximate as it treats the path as made from straight lines.
    def stem_start_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.stem_cover.height,
                hook_depth = m.stem_cover.hook_depth,
                hook_height = m.stem_cover.hook_height,
                hook_height_infill = m.stem_cover.hook_height_infill
            )])
            .wires()
        )
        if m.debug: show_object(wire, name = "stem_start_wire_unrotated")
        wire = (
            wire
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, -1), 
                -90
            )
            # Counter the translating effect of the above rotation.
            .translate((0, +m.stem_cover.hook_depth + 2 * m.thickness, 0))
            # Bring the wire to its start position.
            .translate((*m.stem_startpoint, 0))
            .val()
        )

        if m.debug: show_object(wire, name = "stem_start_wire")
        return wire

        
    def stem_end_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.stem_cover.height,
                hook_depth = m.stem_cover.hook_depth,
                hook_height = m.stem_cover.hook_height,
                hook_height_infill = m.stem_cover.hook_height_infill
            )])
            .wires()
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, -1), 
                -90 + (m.stem_cover.stem_angle - 90)
            )
            # Easiest to find the point at the very end of the path is via positionAt(1)
            .translate(self.stem_path().val().positionAt(1).toTuple())
            .val()
        )

        if m.debug: show_object(wire, name = "stem_end_wire")
        return wire


    def lens_path(self):
        """
        The sweeping path follows the planar upper edge of the eye cover shape.
        Points are defined in the XY plane, drawing a cover for the left lens from origin to -x.
        """
        m = self.measures

        path = (
            cq
            .Workplane("XY")
            .moveTo(*m.lens_startpoint)
            .sagittaArc(m.lens_endpoint, -m.lens_cover.horizontal_arc_height)
            .wire() # Since we don't want a closed wire, close() will not create the wire. We have to.
        )

        if m.debug: show_object(path, name = "lens_path")
        return path


    def stem_path(self):
        m = self.measures

        path = (
            cq
            .Workplane("XY")
            .moveTo(*m.stem_startpoint)
            .polarLine(m.stem_cover.depth, 360 - m.stem_cover.stem_angle)
            .wire() # Since we don't want a closed wire, close() will not create the wire. We have to.
        )

        if m.debug: show_object(path, name = "stem_path")
        return path


    def build(self):
        cq.Workplane.union_pending = utilities.union_pending
        m = self.measures

        self.model = cq.Workplane("YZ")

        # Sweeping along the path sections.
        # Due to CadQuery issue #808 (https://github.com/CadQuery/cadquery/issues/808), we cannot 
        # simply do one multi-section sweep along a single path with all four wires along it.
        # And, the default transition = "right" would crash CadQuery-Editor due to a CAD kernel bug.
        self.model.ctx.pendingWires.extend([self.lens_start_wire(), self.lens_end_wire()])
        self.model = self.model.sweep(self.lens_path(), multisection = True, transition = "round")

        self.model.ctx.pendingWires.extend([
            self.lens_end_wire(), 
            self.corner_center_wire(),
            self.stem_start_wire()
        ])
        self.model = self.model.loft() # TODO: Make "ruled = True" work here.

        # TODO: Replace the stem cover section with a loft, since that's easier.
        self.model.ctx.pendingWires.extend([self.stem_start_wire(), self.stem_end_wire()])
        self.model = self.model.sweep(self.stem_path(), multisection = True, transition = "round")

        # Rounding the lower corners.
        self.model = (
            self.model

            # Rounding the lower corner of the lens cover.
            .faces(">X")
            .edges("<Z")
            # TODO: Fix that only small radii are possible here. This is probably because the part 
            # is curved.
            .fillet(m.lens_cover.lower_corner_radius)

            # Rounding the lower corner of the stem cover.
            .faces("<Y")
            .edges("<Z")
            .fillet(m.stem_cover.lower_corner_radius)
        )


# =============================================================================
# Part Creation
# =============================================================================
    
part = EyeCover(cq.Workplane(), measures)
show_options = {"color": measures.color, "alpha": measures.alpha}
show_object(part.model, name = measures.part_name, options = show_options)
