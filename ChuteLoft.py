import cadquery as cq

# A chute created from a loft between two U-shaped profiles.

lower_profile = (cq
    .Workplane("XY").workplane(offset = 0)
    # Draw a very thin U profile. Cannot be zero-width as offset2D() cannot deal 
    # with that yet due to a bug (https://github.com/CadQuery/cadquery/issues/508).
    .hLine(10).threePointArc((20, 15), (10, 30)).hLine(-10)
    .vLine(-0.1)
    .hLine(10).threePointArc((20 - 0.1, 15), (10, 0 + 0.1)).hLine(-10)
    .close()
    .offset2D(3)
)

upper_profile = (cq
    .Workplane("XY").transformed(offset = cq.Vector(40, 0, 60), rotate = cq.Vector(0, 90, 0))
    # Draw a very thin U profile. Cannot be zero-width as offset2D() cannot deal 
    # with that yet due to a bug (https://github.com/CadQuery/cadquery/issues/508).
    .hLine(10).threePointArc((20, 15), (10, 30)).hLine(-10)
    .vLine(-0.1)
    .hLine(10).threePointArc((20 - 0.1, 15), (10, 0 + 0.1)).hLine(-10)
    .close()
    .offset2D(3)
)

chute = cq.Workplane("XY")
# Special technique needed to add pending wires created independently. See:
# https://github.com/CadQuery/cadquery/issues/327#issuecomment-616127686
chute.ctx.pendingWires.extend(lower_profile.ctx.pendingWires)
chute.ctx.pendingWires.extend(upper_profile.ctx.pendingWires)

chute = chute.loft(combine=True)
