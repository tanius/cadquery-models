import cadquery as cq

# Two stacked boxes of different sizes, demonstrating how to create a face based on an existing face.

result = (cq.Workplane("XY")
    .box(2.0, 2.0, 1.0)
    .faces(">Y").wires().toPending().offset2D(-0.2)
    .end().end().workplane().extrude(2)
)

show_object(result)