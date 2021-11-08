from types import SimpleNamespace as Measures

# FootBlock configuration for a pair of spacer blocks to support a specific toilet seat, in 
# addition to two similar spacer blocks that were already mounted to that toilet seat.
# Toilet seat material thickness: 17.5 mm. Screws may go up to 15 mm into the toilet seat.
measures = Measures(
    block = Measures(
        lower_width = 15.0, # Same as the original toilet seat supports.
        upper_width = 19.0, # Same as the original toilet seat supports.
        lower_depth = 94.0, # Twice the size of the original toilet seat supports.
        upper_depth = 94.0, # Twice the size of the original toilet seat supports.
        front_height = 16.6,
        back_height = 19.1,
        lower_edge_radius = 3.0,
    ),
    hole_1 = Measures(
        position = 23.5,
        # Hole for a 4 mm wood screw.
        # Use 5.4 to get 3.9-4.0 mm when printed with a 0.8 mm nozzle (which always shrink holes).
        # Use 4.5 to get 4.2 mm when printed with a 0.4 mm nozzle.
        hole_size = 5.4,
        # Hole to make a 4 mm wood screw's head flush with the surface.
        # Use 10.0 when printed with a 0.8 mm nozzle (which always shrink holes).
        # Use 9.2 when printed with a 0.4 mm nozzle.
        head_size = 10.0,
        head_angle = 90 # Suitable for wood screws with countersunk heads.
    ),
    hole_2 = Measures(
        position = 70.5,
        hole_size = 5.4, # See above.
        head_size = 10.0, # See above.
        head_angle = 90 # See above.
    ),
)
