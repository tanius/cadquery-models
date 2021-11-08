from types import SimpleNamespace as Measures

# FootBlock configuration for height extensions of Mitraset Classic cases, raising them enough to 
# allow opening and closing the lid when multiple boxes are stacked.
#
# Measures of the original foot on the box are difficult to measure because of radii on the bent 
# metal. They have been determined experimentally with a test print so that the included 1.2 mm 
# for glue on all sides are also 1.2 mm in natura, and so that the upper part of the foot will 
# fit tightly around the original foot of the box, while not riding up on its slopes. This enables 
# to easily position the foot extension part by pressing it on, as it is self-centering this way.
#
# 3D printing:
# – The part needs a bit of support, just below the overhangs at each of the four corners. Because 
#   a bend in a 45° overhanging section is an overhang >45°. It will finish the print also without 
#   support, but will often have holes in these corner locations.
# – If you have to print the long part (both halves) diagonally on your printbed, adjust 
#   the 100% infill pattern so it creates lines diagonally to the part, not to the printbed. The 
#   latter would create lines side to side on the part every second layer, which can rattle the part 
#   loose, esp. when the first layer gap was a bit too small and there is scratching on subsequent 
#   layers. (Other fixes: 95% infill instead of 100%, and add a brim to the first layer.)
# ­– If you have to print the long part (both halves) diagonally on a Creality Ender 2 printer, 
#   print from the corner at the origin to the one diagonally opposite. The other diagnonal is less 
#   suitable as the print bed leveling for the "min x, max y" corner involves a seesaw mechanism 
#   and thus the print bed adhesion in that corner is often not perfect.
# 
# After printing:
# (1) Clean up the lower edge from the elephant foot phenomenon, means so that the 
#   edge is flush with the inclines side wall. It is best to use sandpaper. This cleanup is important 
#   around the semi-circular ends of the foot extensions, to create a good fit for the recesses of 
#   the box below and distribute the load well. 
# (2) Optionally, you can also add a small chamfer to the lower edge that will be on the outside of 
#   the mounted parts, by scraping with a knife.
# (3) When printing halves, also remove the elephant foot from the edge on which the halves will 
#   meet by sanding that face plane.
# (4) It helps with PU glue curing to drill a few 2-3 mm holes into the part, as PU glue needs 
#   humidity from the air to cure.

# Fix for sagging due to the thin 45° overhanging walls, on an otherwise calibrated printer.
# You may need an experiment with your own materials.
# Values used, with results:
# – print 1 (v1, yourDroid PETG, 240 °C, 0.8 mm nozzle): 1.0 (model 10.70 mm, print 9.9 mm)
# – print 2 (v2, yourDroid PETG, 240 °C, 0.8 mm nozzle): 1.08 (model 11.56 mm, print 10.9 mm)
# – print 3 (v2, yourDroid PLA, 215 °C, 0.8 mm nozzle): 1.08 (model 11.56 mm, print 11.18 mm)
# – print 4 (v4, 3DJake eco PLA, 210 °C, 1.0 mm nozzle): 1.0336 (model 11.06 mm, print 10.23 mm)
# – print 5 (v4, yourDroid PLA, 215 °C, 1.0 mm nozzle): 1.0336 (model 11.06 mm, print 10.30 mm)
z_calibration = 1.0 # For adjusting in the slicer software by z scaling. Works fine in practice for 
    # a part like this where the height is dominated by the sagging elements. Though strictly, the 
    # calibration should be applied to the thin overhaning walls only as it is material dependent 
    # (so not a hardware calibration issue but sagging).
# z_calibration = 1.0737 # For yourDroid PLA 301011, 215 °C, 1.0 mm nozzle.
# z_calibration = 1.0336 # For yourDroid PLA 301011, 215 °C, 0.8 mm nozzle.
# z_calibration = 1.0610 # For yourDroid PETG 103011, 240 °C, 0.8 mm nozzle.

glue_thickness = 1.2

measures = Measures(

    # Base shape of the boot block.
    block = Measures(
        upper_width = 34.7,
        lower_width = 13.3,
        upper_depth = 178.6,
        lower_depth = 155.5,
        front_height = 10.7 * z_calibration,
        back_height = 10.7 * z_calibration,

        # Radii for the front resp. back near-vertical edges of the foot block.
        # You have to figure out a value by trial and error to enable a successful geometry calculation.
        corner_radius_front = 9.5,
        corner_radius_back = 9.5,
        
        # Radius around the lower outline of the foot block.
        # No edge radius here to avoid needing support for 3D printing. The width has been determined 
        # experimentally for a good fit with a flat foot, but you can also do some manual sanding 
        # of the edges for an even better fit. A 7.5 mm edge radius would otherwise be a good fit.
        lower_edge_radius = 0.0,
    ),

    # A recess in the foot block to fit around an original foot or other shape.
    recess = Measures(
        upper_width = 28.9 + 2 * glue_thickness, # Original foot width plus glue.
        lower_width = 13.9 + 2 * glue_thickness, # Original foot width plus glue.
        upper_depth = 172.6 + 2 * glue_thickness, # Original foot depth plus glue.
        lower_depth = 156.1 + 2 * glue_thickness, # Original foot depth plus glue.
        height = 7.5 * z_calibration, # No glue here, to make the box rest on solid plastic.

        # Reduce the cutout in a section centered between front and back.
        #   Needed so that we can glue that center section without much glue. Backfill up to the 
        #   metal would be 7.5 mm - 5.0 mm = 2.5 mm.
        backfill_section_height = (2.5 - glue_thickness) * z_calibration,
        backfill_section_depth = 156.1 - 2 * 22.5, # Lower depth less high parts of original feet.

        # Radius along the (near) vertical edges.
        corner_radius = 8.0,

        # Radius to follow that of the lower foot outline of the original foot fitting into the recess.
        # The original Mitraset box foot has nearly no radius due to the protruding parts resting 
        # on the ground. But since the recess is 1.2 mm larger all around due to the glue thickness, 
        # we can give it a radius for force transition, without reducing glue thickness. Radius 
        # determined experimentally with a test print.
        lower_edge_radius = 6.0,

        # Radius to follow that of the less-than-foot-high section in the center of the original foot.
        # For the magnitude for the Mitraset box foot design, see on lower_edge_radius.
        backfill_edge_radius = 6.0,
    ),

    # Options: "front half", "back half", "all".
    parts = "front half"
)
