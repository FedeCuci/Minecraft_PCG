#!/usr/bin/env python3

from gdpc import Editor, Block, geometry as geo
from gdpc.exceptions import InterfaceConnectionError, BuildAreaNotSetError

# Create editor
ED = Editor(buffering=True)

# Get build area
try:
    BUILD_AREA = ED.getBuildArea()
    STARTX, STARTY, STARTZ = BUILD_AREA.begin
    LASTX, LASTY, LASTZ = BUILD_AREA.last
except BuildAreaNotSetError:
    print("Please set a build area with /setbuildarea command")
    exit(1)

# Load world slice for height information
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)

def buildCozyHut():
    """Build a small cozy hut in the center of the build area."""
    # Calculate center position
    xaxis = STARTX + (LASTX - STARTX) // 2
    zaxis = STARTZ + (LASTZ - STARTZ) // 2
    
    # Get ground height at center
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    y = heights[(xaxis - STARTX, zaxis - STARTZ)]
    
    # Hut dimensions
    width = 5  # Small but cozy
    length = 6
    height = 4
    
    # Clear space and create foundation
    geo.placeCuboid(
        ED,
        (xaxis - width//2 - 1, y - 1, zaxis - length//2 - 1),
        (xaxis + width//2 + 1, y - 1, zaxis + length//2 + 1),
        Block("stone_bricks")
    )
    
    # Build walls
    geo.placeCuboidHollow(
        ED,
        (xaxis - width//2, y, zaxis - length//2),
        (xaxis + width//2, y + height - 1, zaxis + length//2),
        Block("spruce_planks")
    )
    
    # Add floor
    geo.placeCuboid(
        ED,
        (xaxis - width//2 + 1, y, zaxis - length//2 + 1),
        (xaxis + width//2 - 1, y, zaxis + length//2 - 1),
        Block("oak_planks")
    )
    
    # Build pitched roof
    for i in range(width//2 + 2):
        geo.placeCuboid(
            ED,
            (xaxis - width//2 + i, y + height + i, zaxis - length//2 - 1),
            (xaxis - width//2 + i, y + height + i, zaxis + length//2 + 1),
            Block("dark_oak_stairs", {"facing": "east"})
        )
        geo.placeCuboid(
            ED,
            (xaxis + width//2 - i, y + height + i, zaxis - length//2 - 1),
            (xaxis + width//2 - i, y + height + i, zaxis + length//2 + 1),
            Block("dark_oak_stairs", {"facing": "west"})
        )
    
    # Add door
    ED.placeBlock(
        (xaxis - width//2, y, zaxis),
        Block("spruce_door", {"facing": "east", "half": "lower"})
    )
    ED.placeBlock(
        (xaxis - width//2, y + 1, zaxis),
        Block("spruce_door", {"facing": "east", "half": "upper"})
    )
    
    # Add windows
    window_positions = [(xaxis + width//2, zaxis - 1), (xaxis + width//2, zaxis + 1)]
    for wx, wz in window_positions:
        geo.placeCuboid(
            ED,
            (wx, y + 1, wz),
            (wx, y + 2, wz),
            Block("glass_pane")
        )

def main():
    try:
        buildCozyHut()
        print("Your cozy hut is ready!")
    except KeyboardInterrupt:
        print("Build canceled!")

if __name__ == "__main__":
    main()