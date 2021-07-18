import cadquery as cq
import cadquery.selectors as cqs
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
# Tasks for later
# TODO: Add documentation for all methods.
# TODO: Re-add corner rounding of the lower corners.
# TODO: Add the general edge chamfering. That's very impractical though for a design like this, 
#     as edge selection is very difficult here.
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
    thickness = 1.6, # For FDM, that's 4 walls with a 0.4 mm nozzle. Corrected from 0.8.
    edge_smoothing = 0.4, # For all edges, to make them nicer to the touch.
    lens_cover = Measures(
        # Lens width 58.3 mm + stem corner width 5.6 mm - stem cover width 6.1 mm.
        # Corrected from 55.5 mm
        width = 57.8,
        height = 35.3, # Corrected from 33.5
        vertical_arc_height = 1.7, # TODO: Implement that this is utilized, then reduce hook_depth.
        horizontal_arc_height = 2.3,
        # Only small radii possible due to a bug. Cornercase radii may may result in non-manifoldness.
        lower_corner_radius = 2.0, 
        hook_depth = 4.6, # Lens thickness 2.9 mm, vertical arc height 1.7 mm.
        hook_height = 8.0,
        frame_attachment_depth = 1.4, # Provides additional hook depth at outer side of lens, for frame.
        overhang_angle_start = 45,
        # Visually adapted to achieve the same lower endpoint position compared to a shape with 
        # frame_attachment_depth = 0.
        overhang_angle_end = 48,
        overhang_size_start = 7.0,
        # Visually adapted to achieve the same lower endpoint position compared to a shape with 
        # frame_attachment_depth = 0.
        overhang_size_end = 7.5
    ),
    corner_cover = Measures(
        height = 35.3,
        hook_depth = 5.0, # Adapted visually to create a corner. Corrected from 7.0.
        # TODO: Calculate hook_height always automatically as the midpoint between lens cover and 
        # hinge cover height, as when forgetting to do this manually, the interpolation can create 
        # shapes that let the lofts partially fail.
        hook_height = 8.0, # Midpoint between lens cover and hinge cover hook heights.
        hook_height_infill = 2.7, # Midpoint between lens cover and stem cover hook heights. Avoids interpolation issues.
        overhang_angle = 45,
        overhang_size = 7.0
    ),
    hinge_cover = Measures(
        depth = 18.0, # Measured from the lens cover back plane.
        height = 35.3,
        path_angle = 100,
        lower_corner_radius = 12.0,
        hook_depth = 4.5, # Measured glasses stem width is 3.8 mm.
        hook_height = 8.0,
        hook_height_infill = 5.4,
        overhang_angle = 45,
        overhang_size = 7.0
    ),
    stem_cover = Measures(
        depth = 22.0, # Measured from the lens cover back plane.
        height = 35.3,
        path_angle = 100,
        lower_corner_radius = 12.0,
        hook_depth = 4.5, # Measured glasses stem width is 3.8 mm.
        hook_height = 14.0,
        hook_height_infill = 5.4,
        overhang_angle = 45,
        overhang_size = 7.0
    ),
)


# Selective reloading to pick up changes made between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
importlib.reload(utilities)

class LensCover:

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
        m.hinge_startpoint = (-m.lens_cover.width, -m.lens_cover.hook_depth - 2 * m.thickness)
        # toTuple() yields a (x,y,z) coordinate, but we only want (x,y) here.
        # When slicing in Python "[0:2]", the specified end element (index 2) will not be in the result.
        m.stem_startpoint =self.hinge_path().val().positionAt(1).toTuple()[0:2]

        self.build()

    
    def profile_wire(self, height, hook_depth, hook_height, hook_height_infill = 0.1, 
        overhang_angle = 90, overhang_size = 0.1, debug_name = None
    ):
        """
        Object of class Wire, representing the base shape of the hook.

        A multi-section sweep requires wires placed along the path to use for the shape-adapted 
        sweeping. These wires should be orthogonal to the path to get the desired shape.
        """
        # hook_height_infill is by default 0.1 just because the CAD kernel cannot handle 0 here.

        # TODO: Create a profile with a curved section. Proposal: Use swipe() and 
        # convert a face of the resulting 3D shape back into a wire.
        
        m = self.measures

        # Remember that translate() uses global (!) coordinates.
        wire = (
            cq.Workplane("YZ")

            # Covering outer element of the profile.
            .rect(m.thickness, height, forConstruction = True)
            .translate((0, -0.5 * m.thickness, -0.5 * height))
            .toPending()
            
            # Horizontal element of the hook, including hook infill if any.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(hook_depth + 2 * m.thickness, m.thickness + hook_height_infill, forConstruction = True)
            .translate((0, -0.5 * (hook_depth + 2 * m.thickness), -0.5 * (m.thickness + hook_height_infill)))
            .toPending()
            
            # Vertical element of the hook with the tip.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(m.thickness, hook_height + m.thickness, forConstruction = True)
            # -0.499 instead of -0.5 due to a malfunction of union_pending() when having a complete 
            # intersection in this corner. Strangely, only for this corner.
            .translate((0, -hook_depth - 1.5 * m.thickness, -0.499 * (hook_height + m.thickness)))
            .toPending()

            # Overhang at the bottom of the profile shape.
            .copyWorkplane(cq.Workplane("YZ"))
            .rect(m.thickness, overhang_size, forConstruction = True)
            # 0.499 because otherwise union_pending() cannot create a correct result. This happens due to 
            # the CAD kernel limitations of unioning shapes that share one corner exactly.
            .translate((0, -0.5 * m.thickness, -height - 0.499 * overhang_size))
            .rotate((1, 0, -height), (-1, 0, -height), overhang_angle)
            .toPending()

            .union_pending()
            .ctx.pendingWires[0]
        )

        if m.debug and debug_name is not None:
            showable_wire = cq.Workplane().newObject([wire]).wires().val()
            show_object(showable_wire, name = debug_name)

        return wire

    
    # Wire at the start of the sweep, defining the lens cover cross-section next to the nose.
    def lens_start_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([
                self.profile_wire(
                    height = m.lens_cover.height,
                    hook_depth = m.lens_cover.hook_depth,
                    hook_height = m.lens_cover.hook_height,
                    overhang_angle = m.lens_cover.overhang_angle_start,
                    overhang_size = m.lens_cover.overhang_size_start
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
                hook_depth = m.lens_cover.hook_depth + m.lens_cover.frame_attachment_depth,
                hook_height = m.lens_cover.hook_height,
                overhang_angle = m.lens_cover.overhang_angle_end,
                overhang_size = m.lens_cover.overhang_size_end
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
                hook_height = m.corner_cover.hook_height,
                hook_height_infill = m.corner_cover.hook_height_infill,
                overhang_angle = m.corner_cover.overhang_angle,
                overhang_size = m.corner_cover.overhang_size
            )])
            # Move the wire to the +y part so we can rotate around origin to rotate around the 
            # back edge.
            .translate((0, m.corner_cover.hook_depth + 2 * m.thickness, 0))
            # Rotate around the back edge of the initial wire, now at origin.
            # Rotate by half the angle that the hinge start wire will have.
            .rotate((0, 0, 1), (0, 0, -1), 0.5 * (-90 + (m.hinge_cover.path_angle - 90)))
            # Bring the wire into its final position.
            .translate((*m.lens_endpoint, 0))
            .translate((0, -m.lens_cover.hook_depth - 2 * m.thickness, 0))
            .val()
        )

        if m.debug: show_object(wire, name = "corner_center_wire")
        return wire


    # Wire at the start of the stem cover / end of the bent section.
    # Position is slightly approximate as it treats the path as made from straight lines.
    def hinge_start_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.hinge_cover.height,
                hook_depth = m.hinge_cover.hook_depth,
                hook_height = m.hinge_cover.hook_height,
                hook_height_infill = m.hinge_cover.hook_height_infill,
                overhang_angle = m.hinge_cover.overhang_angle,
                overhang_size = m.hinge_cover.overhang_size
            )])
            .wires()
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.hinge_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.hinge_cover.hook_depth - 2 * m.thickness, -1), 
                -90 + (m.hinge_cover.path_angle - 90)
            )
            # Move so that the original back edge is at the origin, to prepare the move along the path.
            .translate((0, m.hinge_cover.hook_depth + 2 * m.thickness, 0))
            # Easiest to find the point at the very start of the path is via positionAt(0)
            .translate(self.hinge_path().val().positionAt(0).toTuple())
            .val()
        )

        if m.debug: show_object(wire, name = "hinge_start_wire")
        return wire


    def hinge_end_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.hinge_cover.height,
                hook_depth = m.hinge_cover.hook_depth,
                hook_height = m.hinge_cover.hook_height,
                hook_height_infill = m.hinge_cover.hook_height_infill,
                overhang_angle = m.hinge_cover.overhang_angle,
                overhang_size = m.hinge_cover.overhang_size
            )])
            .wires()
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.hinge_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.hinge_cover.hook_depth - 2 * m.thickness, -1), 
                -90 + (m.hinge_cover.path_angle - 90)
            )
            # Move so that the original back edge is at the origin, to prepare the move along the path.
            .translate((0, m.hinge_cover.hook_depth + 2 * m.thickness, 0))
            # Easiest to find the point at the very end of the path is via positionAt(1)
            .translate(self.hinge_path().val().positionAt(1).toTuple())
            .val()
        )

        if m.debug: show_object(wire, name = "hinge_end_wire")
        return wire


    def stem_start_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.stem_cover.height,
                hook_depth = m.stem_cover.hook_depth,
                hook_height = m.stem_cover.hook_height,
                hook_height_infill = m.stem_cover.hook_height_infill,
                overhang_angle = m.stem_cover.overhang_angle,
                overhang_size = m.stem_cover.overhang_size
            )])
            .wires()
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, -1), 
                -90 + (m.stem_cover.path_angle - 90)
            )
            # Move so that the original back edge is at the origin, to prepare the move along the path.
            .translate((0, m.stem_cover.hook_depth + 2 * m.thickness, 0))
            # Easiest to find the point at the very beginning of the path is via positionAt(0)
            # But not exactly at the beginning as that would place the wire into the same position 
            # as the hinge end wire, and we can't loft wires in the same position.
            .translate(self.stem_path().val().positionAt(0.01).toTuple())
            .val()
        )

        if m.debug: show_object(wire, name = "stem_end_wire")
        return wire

        
    def stem_end_wire(self):
        m = self.measures

        wire = (
            cq.Workplane().newObject([self.profile_wire(
                height = m.stem_cover.height,
                hook_depth = m.stem_cover.hook_depth,
                hook_height = m.stem_cover.hook_height,
                hook_height_infill = m.stem_cover.hook_height_infill,
                overhang_angle = m.stem_cover.overhang_angle,
                overhang_size = m.stem_cover.overhang_size
            )])
            .wires()
            # Rotate around the back (-y) edge of the initial wire.
            .rotate(
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, 1), 
                (0, -m.stem_cover.hook_depth - 2 * m.thickness, -1), 
                -90 + (m.stem_cover.path_angle - 90)
            )
            # Move so that the original back edge is at the origin, to prepare the move along the path.
            .translate((0, m.stem_cover.hook_depth + 2 * m.thickness, 0))
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


    def hinge_path(self):
        m = self.measures

        path = (
            cq
            .Workplane("XY")
            .moveTo(*m.hinge_startpoint)
            .polarLine(m.hinge_cover.depth, 360 - m.hinge_cover.path_angle)
            .wire() # Since we don't want a closed wire, close() will not create the wire. We have to.
        )

        if m.debug: show_object(path, name = "hinge_path")
        return path


    def stem_path(self):
        m = self.measures

        path = (
            cq
            .Workplane("XY")
            .moveTo(*m.stem_startpoint)
            .polarLine(m.stem_cover.depth, 360 - m.stem_cover.path_angle)
            .wire() # Since we don't want a closed wire, close() will not create the wire. We have to.
        )

        if m.debug: show_object(path, name = "stem_path")
        return path


    def build(self):
        cq.Workplane.union_pending = utilities.union_pending
        m = self.measures

        # Sweeping along the path sections.
        # Due to CadQuery issue #808 (https://github.com/CadQuery/cadquery/issues/808), we cannot 
        # simply do one multi-section sweep along a single path with all six wires along it.
        # And, the default transition = "right" would crash CadQuery-Editor due to a CAD kernel bug.
        lens_cover = cq.Workplane("YZ")
        lens_cover.ctx.pendingWires.extend([
            self.lens_start_wire(), 
            self.lens_end_wire()
        ])
        lens_cover = lens_cover.sweep(
            self.lens_path(), 
            multisection = True, 
            transition = "round"
        )

        corner_cover = cq.Workplane("YZ")
        corner_cover.ctx.pendingWires.extend([
            self.lens_end_wire(), 
            self.corner_center_wire(),
            self.hinge_start_wire()
        ])
        corner_cover = corner_cover.loft()

        hinge_and_stem_cover = cq.Workplane("YZ")
        hinge_and_stem_cover.ctx.pendingWires.extend([
            self.hinge_start_wire(),
            self.hinge_end_wire(),
            self.stem_start_wire(),
            self.stem_end_wire()
        ])
        hinge_and_stem_cover = hinge_and_stem_cover.loft(ruled = True)

        # The internal combine function of loft() and sweep() is a bit fragile, so instead to obtain 
        # a singel solid we created the individual parts first and then union() them together here.
        self.model = (
            cq.Workplane("YZ")
            .union(lens_cover)
            .union(corner_cover)
            .union(hinge_and_stem_cover)
        )

        # Rounding the lower corners.
        # TODO: Reimplement this, as it does not work when having the 45° overhang at the bottom.
        # self.model = (
        #     self.model
        #
        #     # Rounding the lower corner of the lens cover.
        #     .faces(">X")
        #     .edges("<Z")
        #     # TODO: Fix that only small radii are possible here. This is probably because the part 
        #     # is curved.
        #     .fillet(m.lens_cover.lower_corner_radius)
        #
        #     # Rounding the lower corner of the stem cover.
        #     .faces("<Y")
        #     .edges("<Z")
        #     .fillet(m.stem_cover.lower_corner_radius)
        # )


# =============================================================================
# Part Creation
# =============================================================================
    
part = LensCover(cq.Workplane(), measures)
show_options = {"color": measures.color, "alpha": measures.alpha}
show_object(part.model, name = measures.part_name, options = show_options)
