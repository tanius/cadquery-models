import cadquery as cq

# Written by Jean-Paul. Taken from https://github.com/CadQuery/cadquery/issues/35 and adapted.
# 
# The intention seems to be a sweep() that allows start and end wires to be different. However, it 
# would not allow multiple sections (i.e. more than two wires to sweep between). This is unlike 
# the currently implemented Workplane::sweep(path, multisection = True).
#
# However, the implementation below so far fails to provide sweeping with different start and 
# end wires.

def pgSweepFromListOfWires(self, path, makeSolid=True, isFrenet=False,
                           combine=True, clean=True):
    """
    Use list of un-extruded wires in the parent chain to create a swept solid.
    It differs from sweep that creates multiple solid
    This creates one solid with shape following list of wires

    Usage example :
    path = cq.Workplane("XZ").moveTo(10, 0).threePointArc((0, 10), (-10, 0))
    s = cq.Workplane("XY").moveTo(10, 0).circle(3).moveTo(-10, 0).circle(1)
    s = s.sweepFromListOfWires(path)

    :param path: A wire along which the pending wires will be swept
    :param boolean combine: True to combine the resulting solid with parent solids if found.
    :param boolean clean: call :py:meth:`clean` afterwards to have a clean shape
    :return: a CQ object with the resulting solid selected.
    """

    # returns a Solid (or a compound if there were multiple)
    r = self._sweepFromListOfWires(path.wire(), makeSolid, isFrenet)

    if combine:
        newS = self._combineWithBase(r)
    else:
        newS = self.newObject([r])
    if clean:
        newS = newS.clean()
    return newS


def _sweepFromListOfWires(self, path, makeSolid = True, isFrenet = False):
    """
    Makes a swept solid from an existing set of pending wires.

    :param wires: A list of wire along which the pending wires will be swept
    :param path: A wire along which the pending wires will be swept
    :return:a FreeCAD solid, suitable for boolean operations
    """

    # group wires together into faces based on which ones are inside the others
    # result is a list of lists
    #wireSets = cq.sortWiresByBuildOrder(list(self.ctx.pendingWires),self.plane, [])
    # Simplification to accommodate changes in sortWiresByBuildOrder: no inner wires allowed.
    wireSets = [ [wire] for wire in self.ctx.pendingWires]

    # now all of the wires have been used to create an extrusion
    self.ctx.pendingWires = []

    toFuse = []
    section = []
    for ws in wireSets:
        for i in range(0, len(ws)):
            section.append(ws[i])

    # implementation
    outW = cq.Wire(section[0].wrapped)
    inW = section[1:]
    thisObj = cq.Solid.sweep(outW, inW, path.val(), makeSolid, isFrenet)
    toFuse.append(thisObj)

    return cq.Compound.makeCompound(toFuse)


# link the plugin into cadQuery
cq.Workplane.pgSweepFromListOfWires = pgSweepFromListOfWires
cq.Workplane._sweepFromListOfWires = _sweepFromListOfWires

# Example
path = (
    cq.Workplane("XZ")
    .moveTo(-10, 9)
    .lineTo(0, 9)
    .threePointArc((9, 0), (0, -9))
    .lineTo(-10, -9)
)
s = (
    cq.Workplane("YZ")

    .workplane(offset = -10)
    .moveTo(0, 9)
    .circle(4)
    .circle(2)

    # .workplane(offset = 10)
    # .moveTo(0, 9)
    # .circle(2)

    .moveTo(0, -18)
    .circle(2)
    .circle(1)

    # .workplane(offset = -10)
    # .circle(2)
)
s = s.pgSweepFromListOfWires(path, makeSolid = True, isFrenet = False)
