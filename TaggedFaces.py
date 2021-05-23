import cadquery as cq
from cadquery import selectors

# Demonstration of how tagging in CadQuery refers to a defined position in the history tree.
# Here, tagged square faces are not affected by subsequently creating a hole through these faces.

box = (
    cq
    .Workplane("XY")
    .box(10, 10, 10)
    .faces("|Z").tag("tagged")
    .faces(">Z").workplane().hole(4)
)

show_object(box,                       name = "box",    options = {"color": "lightgray"})

show_object(box.faces(tag = "tagged"), name = "tagged", options = {"color": "red"})
