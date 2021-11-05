from types import SimpleNamespace as Measures

# TODO Support a symmetrical recess in the top surface. Always centered in that surface, with 
#   configurable width, depth, height, upper and lower corner radii, lower edge radius. So 
#   basically like another foot block, subtracted from the top.
# TODO Switch to using different corner radii on top and bottom surface, with the adaptive fillet 
#   automatically created via the lofting. This allows to have a half-circle end on both ends, and 
#   on both top and bottom.

# FootBlock configuration for height extensions of Mitraset Classic cases, raising them enough to 
# allow opening and closing the lid when multiple boxes are stacked.
measures = Measures(
    block = Measures(
        lower_width = 15.0,
        upper_width = 36.4,
        lower_depth = 160.0,
        upper_depth = 180.4,
        front_height = 10.7,
        back_height = 10.7,
        # If not set, corner radius will be maximized. This only works when lower and upper surfaces 
        # are identical, otherwise you have to figure out a value by trial&error to enable a successful 
        # geometry calculation.
        corner_radius_front = 10.0,
        corner_radius_back = 10.0,
        edge_radius = 8.0, # For a fillet around the lower edge.
    ),
    recess = Measures(
        # TODO
    )
)
