import cadquery as cq
import logging
from types import SimpleNamespace as Measures

log = logging.getLogger(__name__)

# A parametric mount for stepper motors shaped as an L-bracket.

class MotorMountL:

    def __init__(self, workplane, measures):
        """
        A parametric stepper motor mount in the shape of an L bracket.
        
        This is an adaptation of Eddie Liberato's design, as published at:
        https://eddieliberato.github.io/blog/2020-08-01-stepper-motor-bracket/

        :param workplane: The CadQuery workplane to create the chute on.
        :param measures: The measures to use for the parameters of this design. Expects a nested 
            [SimpleNamespace](https://docs.python.org/3/library/types.html#types.SimpleNamespace) 
            object, which may have the following attributes:
            - **``shell_thickness``:** Shell thickness of the tube element.
        """

        # todo
        self.model = workplane
        self.debug = False
        self.measures = measures

        self.build()

    def build(self):
        m = self.measures

        self.model = (
            cq.Workplane("front")
            .box(m.width, m.fplate_thickness, m.fplate_height + m.bplate_thickness)
            .faces(">Y")
            .workplane()
            .move(0, m.bplate_thickness / 2)
            .rect(m.fplate_between_holes, m.fplate_between_holes, forConstruction = True)
            .vertices()
            .cboreHole(m.fplate_screw_clearance, m.fplate_cbore_diameter, m.fplate_cbore_depth)
            .faces("<Y")
            .workplane()
            .move(0, m.bplate_thickness / 2)
            .cboreHole(m.main_bore_diameter, m.main_cbore_diameter, m.main_cbore_depth)
            .faces("<Y")
            .workplane(centerOption = 'CenterOfBoundBox')
            .move(0, -m.fplate_height / 2)
            .rect(m.width, m.bplate_thickness)
            .extrude(m.bplate_length)
            .faces("<Z[1]")
            .workplane()
            .move(0, m.bplate_holes_offset)
            .rect(m.bplate_between_holes, m.bplate_between_holes, forConstruction = True)
            .vertices()
            .cboreHole(m.bplate_screw_clearance, m.bplate_cbore_diameter, m.bplate_cbore_depth)
        )

        if m.gusset:
            self.model = (
                self.model
                .faces(">X")
                .workplane(centerOption = 'CenterOfBoundBox')
                .move(0, -(m.fplate_height + m.bplate_thickness) / 2)
                .line((m.bplate_length + m.fplate_thickness) / 2, 0)
                .line(0, m.fplate_height)
                .close()
                .extrude(-m.gusset_thickness)
                .faces("<X")
                .workplane(centerOption = 'CenterOfBoundBox')
                .move(0, -(m.fplate_height + m.bplate_thickness) / 2)
                .line(-(m.bplate_length + m.fplate_thickness) / 2, 0)
                .line(0, m.fplate_height)
                .close()
                .extrude(-m.gusset_thickness)
            )

def part(self, part_class, measures):
    """CadQuery plugin that provides a factory method for custom parts"""

    part = part_class(self, measures) # Dynamic instantiation from the type contained in part_class.

    return self.newObject(
        part.model.objects
    )


# =============================================================================
# Measures and Part Creation
# =============================================================================
cq.Workplane.part = part

measures = Measures(
    width = 66.0,
    fplate_height = 60.0,
    fplate_thickness = 10.0,
    # rectangular distance between stepper mounting holes (NEMA 23 = 47.1)
    fplate_between_holes = 47.1,
    fplate_screw_clearance = 5.0,
    fplate_cbore_diameter = 7.5,
    fplate_cbore_depth = 4.0,
    main_bore_diameter = 28.2,
    main_cbore_diameter = 40.0,
    main_cbore_depth = 2.0,
    bplate_length = 86.0,
    bplate_thickness = 4.0,
    bplate_between_holes = 50.0, # holes to mount it to the frame
    bplate_holes_offset = 5.0,
    bplate_screw_clearance = 5.0,
    bplate_cbore_diameter = 7.5,
    bplate_cbore_depth = 2.0,
    gusset_thickness = 3.0,
    gusset = True
)
show_options = {"color": "lightgray", "alpha": 0}

motor_mount = cq.Workplane("XY").part(MotorMountL, measures)
show_object(motor_mount, name = "motor_mount", options = show_options)
