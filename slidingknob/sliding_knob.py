import cadquery as cq

# Sliding knob for a kitchen fume extraction unit found in our place.
#
# Current measures are the best effort for creating a fitting part and have been optimized further 
# after the print that was eventually used.

width = 90
height = 14
lw = 0.4 # "Line width". Wall thickness of a single-line 3D printed wall. Depends on nozzle choice.

def firstSolid(self):
    return self.newObject([self.findSolid()])

cq.Workplane.firstSolid = firstSolid

knob = (
    cq
    .Workplane("XZ")

    # Base shape.
    .rect(width, height)
    .extrude(2.4)

    # Default workplane, with the origin above the attachment knob.
    .faces(">Y")
    .workplane()
    .transformed(rotate = (0, 0, 180))
    .center(-0.5 * width + 29, 0)
    .tag("attachment_workplane")
    
    # Base shape corner rounding.
    .firstSolid()
    .edges("|Y")
    .fillet(3.2)

    # Base shape outer edge chamfering.
    .firstSolid()
    .faces("<Y")
    .chamfer(0.01) # Currently effectively disabled.

    # Attachment for knob in the vapor extractor.
    .workplaneFromTagged("attachment_workplane")
    .rect(2 * lw + 5.83 + 2 * lw, lw + 5.80 + lw)
    .extrude(8.5)
    .faces(">Y")
    .workplane()
    .rect(5.83, 5.80)
    #.extrude(20)
    .cutBlind(-5.5)

    # Looking hole.
    .workplaneFromTagged("attachment_workplane")    
    .center(36.7, 0)
    .circle(3)
    .firstSolid()
    .cutThruAll()
)

show_object(knob, options = {"color": "lightgray", "alpha": 0})


# Test parts to find out the right dimensions for the press-on tube.

# wall_t = 1 * lw
# height = 10

# attachment_tests = (
#     cq
#     .Workplane("XY")

#     .center(20, 0)
#     .rect(5.8 + 2 * wall_t, 5.8 + 2 * wall_t)
#     .rect(5.8, 5.8)
#     .extrude(height)

#     .center(20, 0)
#     .rect(5.9 + 2 * wall_t, 5.9 + 2 * wall_t)
#     .rect(5.9, 5.9)
#     .extrude(height)

#     .center(20, 0)
#     .rect(6.0 + 2 * wall_t, 6.0 + 2 * wall_t)
#     .rect(6.0, 6.0)
#     .extrude(height)

#     .center(20, 0)
#     .rect(6.1 + 2 * wall_t, 6.1 + 2 * wall_t)
#     .rect(6.1, 6.1)
#     .extrude(height)
# )
#show_object(attachment_tests, options = {"color": "lightgray", "alpha": 0})
