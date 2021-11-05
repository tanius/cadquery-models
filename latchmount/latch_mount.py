import cadquery as cq
import logging
from types import SimpleNamespace as Measures

# ===== (1) Measures =====

measures = Measures(
    edge_smoothing = 3.0,
    panel_depth = 8.0, # Distance between baseplate and counterplate.
    hole_positions = Measures(
        # Hole measures are relative to assembly origin, same as baseplate origin.
        left_edge_offset = 24.21,
        right_edge_offset = 10.21,
        vertical_edge_offset = 7.66,
    ),
    baseplate = Measures(
        width = 79.0,
        height = 38.0, # Same height as 1.5 inch butyl tape, used as seal and load distribution cushioning.
        depth = 17.0,
        left_chamfer = 8.5,
        right_chamfer = 5.0,
        holes_diameter = 4.0,
        edge_groove_height = 2.1, # 1.4 mm for latch, 0.5 mm b/c latch is 1 mm narrower than baseplate, 0.3 mm for tolerance.
        edge_groove_depth = 1.2, # Measured as 0.8±0.1 mm. Some tolerance to make sure contact is at bolt positions.
    ),
    counterplate = Measures(
        width = 92.5, # To the edge of the door / window pane on the outside. Depends on your frame type. Corrected from 89.0.
        width_offset = 0.0, # Offset of left edge against left edge of baseplate. For hole alignment.
        height_offset = 0.0, # Offset of top edge against top edge of baseplate. For hole alignment.
        height = 38.0,
        depth = 1.2, # Creating a cutting template only. 1.2 mm = three layers with a 0.8 mm nozzle.
        holes_diameter = 3.5, # For this drill template, we use a small hole and enlarge later to 6.0.
    ),
)


# ===== (2) Derived measures =====

width_min_extent = min(0, measures.counterplate.width_offset)
width_max_extent = max(measures.baseplate.width, measures.counterplate.width + measures.counterplate.width_offset)
measures.width = abs(width_min_extent) + abs(width_max_extent)

height_min_extent = min(0, measures.counterplate.height_offset)
height_max_extent = max(measures.baseplate.height, measures.counterplate.height + measures.counterplate.height_offset)
measures.height = abs(height_min_extent) + abs(height_max_extent)

measures.depth = measures.baseplate.depth + measures.panel_depth + measures.counterplate.depth

log = logging.getLogger(__name__)


# ===== (3) Implementation =====

class LatchMount:

    def __init__(self, workplane, measures):
        """
        A parametric mount for a deadbolt latch, consisting of baseplate and counterplate.

        The baseplate allows to adapt the latch mounting depth to the required position, and 
        also includes chamfers to prevent injuries when accidentally hitting with the raised latch.
        The counterplate allows pressure distribution on the other side of the door or window 
        to which the latch is mounted, which can be important to prevent cracking of materials 
        like polycarbonate. You may want to use this only as a template to cut the counterplate 
        from sheet metal.

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.

        .. todo:: Add an option to add finger grip pits to the base plate, one on the top and 
            one on the bottom. For cases where the baseplate is high enough (≥15 mm), this 
            provides a good way to pull a door or window pane shut in order to close the latch.
        """

        # workplane is unused while building the model, and only utilized towards the end 
        # to position the model. Because to keep the code simple, CAD models should be able to 
        # reference global axis directions inside their code. This is not possible if we already 
        # have to create the model positioned on the workplane.
        self.workplane = workplane

        self.debug = False
        self.measures = measures

        m = self.measures

        self.build()


    def build(self):
        m = self.measures
        # Create a local coordinate system positioned so that parts created from this base will 
        # stack up from a global +Y position to the XZ plane, putting everything into first octant.
        baseplane = (
            cq.Workplane("XZ")
            .transformed(offset = (0, 0, -m.depth)) # Local directions!

            # Mark hole positions for later, needed for both parts.
            .transformed(offset = (m.hole_positions.left_edge_offset, m.hole_positions.vertical_edge_offset, 0)) # Local directions!
            .rect(
                m.baseplate.width - m.hole_positions.left_edge_offset - m.hole_positions.right_edge_offset,
                m.baseplate.height - 2 * m.hole_positions.vertical_edge_offset,
                centered = False,
                forConstruction = True
            )
            .vertices()
            .tag("hole_positions")
            .end(3) # Set top of stack to before three stack-changing operations. tag() is not stack-changing.
        )

        baseplate = (
            baseplane
            .transformed(offset = (0, 0, m.counterplate.depth + m.panel_depth)) # Local directions!

            .box(m.baseplate.width, m.baseplate.height, m.baseplate.depth, centered = False)

            # Half-circle on the left side.
            .edges("|Y and <X") # Global directions!
            .fillet(0.49 * m.baseplate.height)

            # Cut the holes.
            .faces(">Y")
            .workplane() # hole() needs a workplane to know what to cut.
            .vertices(tag = "hole_positions")
            .hole(diameter = m.baseplate.holes_diameter)

            # Chamfer along the right edge.
            .edges("(>X and <Y)")
            .chamfer(m.baseplate.right_chamfer)

            # Chamfer along the left edge.
            .copyWorkplane(baseplane)
            .transformed(offset = (0, 0, m.depth - m.baseplate.left_chamfer)) # Local directions!
            .transformed(rotate = (0, -45, 0)) # Local axes!
            #.box(10, 10, 1)
            .split(keepBottom = True)

            # # Edge smoothing of the right edges in depth direction.
            .edges("(>X and |Y)")
            .fillet(m.edge_smoothing)

            # Edge smoothing of the right edge resulting from chamfering.
            # TODO: Fix the CadQuery bug that this results in additional filleting of non-selected 
            # edges, then re-enable this section.
            # .edges("|Z and >X and (not >Y)")
            # .fillet(m.edge_smoothing)

            # Cutoffs for bent edges of the latch.
            .copyWorkplane(baseplane)
            .transformed(offset = (0, 0, m.depth)) # Move to front face of baseplate.
            .transformed(rotate = (0, 90, 0))
            .transformed(offset = (0, 0.5 * m.baseplate.height, 0))
            .pushPoints([
                (0, -0.5 * m.baseplate.height),
                (0, 0.5 * m.baseplate.height)
            ])
            .rect(2 * m.baseplate.edge_groove_depth, 2 * m.baseplate.edge_groove_height)
            .cutThruAll()
        )

        counterplate = (
            baseplane
            .box(m.counterplate.width, m.counterplate.height, m.counterplate.depth, centered = False)

            # Half-circle on the left side.
            .edges("|Y and <X") # Global directions!
            .fillet(0.49 * m.counterplate.height)

            # Cut the holes.
            .faces(">Y")
            .workplane() # hole() needs a workplane to know what to cut.
            .vertices(tag = "hole_positions")
            .hole(diameter = m.counterplate.holes_diameter)
        )

        self.baseplate = baseplate
        self.counterplate = counterplate

        # TODO: Move all parts to self.workplane.


# ===== (4) Part creation =====

latch_mount = LatchMount(cq.Workplane("XZ"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(latch_mount.baseplate, name = "baseplate", options = show_options)
show_object(latch_mount.counterplate, name = "counterplate", options = show_options)
