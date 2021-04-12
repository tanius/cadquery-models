import cadquery as cq

def combine_wires(self):
    """
    CadQuery plugin that replaces all wires on the stack with their 2D union. It requires all wires 
    on the stack to be co-planar.
    
    To use this, you must place multiple wires on the stack. That is only possible with 
    Workplane::add(), as .rect() etc. will clear the stack before adding a single new wire. Example:

    ```
    model = (
        cq.Workplane("XY")
        .add( cq.Workplane("XY").rect(40, 40, forConstruction = True) )
        .add( cq.Workplane("XY").rect(20, 16, forConstruction = True).translate((0,20)) )
        .combine_wires()
        .toPending()
        .extrude(12)
    )
    ```

    :return: A Workplane object with the combined wire on the stack (besides nothing else) but not 
        yet in its pending wires.

    .. todo:: Remove this method and its uses. It is now replaced by union_pending().
    """

    #log.info("DEBUG: combine_wires: stack size: %s", self.size())
    #log.info("DEBUG: combine_wires: pending wires: %s", len(self.ctx.pendingWires))

    wires = [obj for obj in self.objects if isinstance(obj, cq.Wire)]
    if len(wires) < 2: return self # Nothing to union for 0 or 1 pending wires.

    extrude_direction = wires[0].normal()
    solids = (
        cq.Workplane("XY")
        # Create a workplane coplanar with the wires, as this will define the extrude() direction.
        .add(cq.Face.makeFromWires(wires[0]))
        .workplane()
    )

    # Extrude all wires into solids.
    # This detour via 3D union'ing is the only way right now to reliably union wires.
    for wire in wires:
        solids = solids.add(wire).toPending().extrude(1)

    combined_wire = (
        solids
        .combine() # 3D union of all the solids.
        # Select the bottom face, as that contains the wires in their original local z position.
        .faces(cq.DirectionMinMaxSelector(extrude_direction, directionMax = False))
        .wires()
    )

    # Since combined_wire was started from a cq.Workplane("XY") above and no by modifying self, 
    # there is no need to "return self.newObject(combined_wire.objects)". If we'd do that, with 
    # some combined wires we'd run into issues extruding them later. This indicates a bug in 
    # Workplane::newObject() which prevents the new object from having an identical wire to the 
    # one used to initialize it.
    # TODO: Get the bug described above fixed in CadQuery. It happens for shapes where a polyLine() 
    # shape of for example a triangle shares an edge with a rect() shape. In this case, the 
    # triangle shape will be missing from the extrusion of the combined wire.
    return combined_wire


def part(self, part_class, measures):
    """
    CadQuery plugin that provides a factory method for custom parts, allowing to create these in a 
    similar manner to how primitives are created in CadQuery's fluid (means, JQuery-like) API.
    
    The custom part has to be defined in a custom class that (1) stores the part geometry as a 
    CadQuery Workplane object in attribute `model` and (2) has a constructor with two required 
    parameters: `workplane` to hand the CadQuery workplane object to build on, and `measures` for 
    the part specs. The part will be created in the local coordinate system.

    Usage example:
    
    ```
    import utilities
    cq.Workplane.part = utilities.part
    my_part = cq.Workplane("XY").part(MyPart, measures).translate((0,0,5))
    ```

    :param self: The CadQuery Workplane object to which this plugin will be attached at runtime.
    :param part_class: Your class used to create your custom part. Provided not as a string, but 
        as the type. If your class has the name "MyPart", you write `MyPart`, not `"MyPart"`.
    :param measures: A class-specific object with the specifications defining the part, to be 
        provided to the constructor of the given class.

    .. todo:: Use the **kwargs mechanism to pass all parameters after part_class to the class, 
        instead of just measures.
    .. todo:: To help with interactive debugging in the console, add a mixin attribute to every 
        object in part.model.objects that has been added by doing part_class(self, measures). 
        Otherwise there is no way to access the underlaying model objects from a CQ Workplane object.
    """
    part = part_class(self, measures) # Dynamic instantiation from the type contained in part_class.

    # In CadQuery plugins, it is good practice to not modify self, but to return a new object linked 
    # to self as a parent: https://cadquery.readthedocs.io/en/latest/extending.html#preserving-the-chain
    return self.newObject(
        part.model.objects
    )
