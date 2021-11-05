import cadquery as cq

def union_pending(self):
    """
    CadQuery plugin that replaces all pending wires with their 2D union. It requires all pending 
    wires to be co-planar.
    
    This supplements the CadQuery methods Workplane::combine() and Workplane::consolidateWires() and 
    Wire::combine(), which cannot deal with intersecting wires yet.

    :return: A Workplane object with the combined wire on the stack (besides nothing else) and in 
        its pending wires (besides nothing else).

    .. todo:: Enforce that all wires must be co-planar, raising an error otherwise. Or maybe in that 
        case only union those that are coplanar. This can be checked by making sure all normals are 
        parallel and the centers are all in one plane.
        https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.occ_impl.shapes.Mixin1D.normal
    """

    wires = self._consolidateWires()
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

    self.ctx.pendingEdges = []
    self.ctx.pendingWires = [combined_wire.val()]

    return self.newObject(combined_wire.vals())