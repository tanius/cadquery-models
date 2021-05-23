import cadquery as cq
import logging
from types import SimpleNamespace as Measures

measures = Measures(
    width = 55.0,
    depth = 8.0,
    height = 5.5,
    radius = 3.99,
    hole_1 = Measures(
        position = 15.0,
        diameter = 3.3,
        cbore_diameter = 5.8,
        cbore_depth = 4.0
    ),
    hole_2 = Measures(
        position = 40.0,
        diameter = 3.3,
        cbore_diameter = 5.8,
        cbore_depth = 4.0
    )
)
m = measures

model = (
    cq.Workplane("XY")
    .box(m.width, m.depth, m.height)
    .translate((0.5 * m.width, 0, 0.5 * m.height))

    .faces(">Z").edges().fillet(m.radius)

    .edges("not %LINE").fillet(0.91 * m.radius)

    .faces(">Z").workplane()
    .pushPoints([(m.hole_1.position, 0)])
    .cboreHole(m.hole_1.diameter, m.hole_1.cbore_diameter, m.hole_1.cbore_depth)
    .pushPoints([(m.hole_2.position, 0)])
    .cboreHole(m.hole_2.diameter, m.hole_2.cbore_diameter, m.hole_2.cbore_depth)
)

show_options = {"color": "lightgray", "alpha": 0}
show_object(model, name = "model", options = show_options)
