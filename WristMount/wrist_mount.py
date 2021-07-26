import cadquery as cq
import cadquery.selectors as cqs
import logging, importlib
from types import SimpleNamespace as Measures
import xmount # local directory import
import utilities # local directory import

# Selective reloading to pick up changes made between script executions.
# See: https://github.com/CadQuery/CQ-editor/issues/99#issue-525367146
importlib.reload(utilities)

log = logging.getLogger(__name__)


class WristMount:

    def __init__(self, workplane, measures):
        """
        A parametric holder to mount a mobile device to the wrist or lower arm. UNFINISHED.

        The design can be adapted to the individual arm and to the device size. The actual part 
        to mount this to a phone is not (yet) part of this design; instead there is a recess for 
        using an X-Mount Type-M male connector part as fount in X-Mount belt holders.

        :param workplane: The CadQuery workplane to create this part on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object.
        """

    def build(self):
        m = self.measures
        baseplane = self.model.workplane()

        # TODO: Write the actual implementation.



# =============================================================================
# Part Creation
# =============================================================================
cq.Workplane.part = utilities.part

measures = Measures(
    wrist_ring = Measures(
        # TODO
    ),
    arm_ring = Measures(
        # TODO
    ),
    bar = Measures(
        width = 40.00,
        depth = 120.00,
        height = 8.00
    ),
    interface = Measures(
        width = 20.00,
        depth = 22.00,
        height = 1.80,
        arc_height = 5.35,
        corner_chamfer = 3.50, # Measured 3.20, but better be generous.
        bolthole_1 = , # TODO
        bolthole_2 = , # TODO
        bolthole_3 = , # TODO
        release_pit = Measured(
            depth_pos = 65.00, # From front of the bar. TODO: More exact position.
            width = 15.00, # Release lever width is 13.0. 
            # Release lever depth is 23.3. But we need a channel going to the end of the bar part 
            # to be able to reach in and release the device with the index finger.
            depth = 55.00, # TODO: Correct depending on depth_pos and bar.depth.
            height_1 = 2.7, # Release lever bottom position is 2.54 mm below mount surface.
            height_2 = 2.7 + 5.5, # Releasing the device needs pressing the lever ≥5.2 mm down.
            corner_radius = 2.50 # Just as the release lever above it.
        )
        # Access groove from the left side, for operating the release lever with the index finger.
        finger_pit = Measures(
            channel_width = 19.0, # Index finger width is 18.7.
            # Index finger height is 15.8 mm at 20 mm from the tip. But just cutting out the bar 
            # part height is enough, as there is always some way to push a finger between the arm 
            # and another part.
            channel_height = 16.0,
            channel_depth = # TODO: Half the bar width + half the lever width (6.5). Calculated symbolically.
        )
    )
)

wrist_mount = WristMount(cq.Workplane("XZ"), measures)

show_options = {"color": "lightgray", "alpha": 0}
show_object(wrist_mount.wrist_ring, name = "wrist_ring", options = show_options)
show_object(wrist_mount.arm_ring, name = "arm_ring", options = show_options)
