import cadquery as cq

# Demonstration of the shell() method by creating a rounded open-top box.

result = cq.Workplane("front").box(2, 2, 2).faces("+Z").shell(0.5)
