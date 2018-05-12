PIXELS_PER_BU = 8  # For the terrain map

# Rendering
HIGHRES_MULTIPLIER = 16

# Mesh generation
NUM_TILES = 5
ANGLE_LIMIT = 4 * 3.14 / 180 # Amount of simplification: min degrees per vert
MERGE_DISTANCE = 0.005
SVG_SCALE_FACTOR = PIXELS_PER_BU / HIGHRES_MULTIPLIER * 8 * 1.384
