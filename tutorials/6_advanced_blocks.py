# ... (keep imports and basic setup) ...

def buildHut():
    """Build a simple wooden hut in the center of the build area."""
    # Calculate center position
    xaxis = STARTX + (LASTX - STARTX) // 2
    zaxis = STARTZ + (LASTZ - STARTZ) // 2
    
    # Get height at center position
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    y = heights[(xaxis - STARTX, zaxis - STARTZ)]
    
    print("Building wooden hut...")
    
    # Define dimensions
    width = 7
    length = 9
    height = 5
    
    # Create palette for walls with mostly oak planks and some spruce
    wallPalette = [Block("oak_planks")] * 4 + [Block("spruce_planks")]
    
    # Clear space and create platform
    geo.placeCuboid(
        ED,
        (xaxis - width//2, y, zaxis - length//2),
        (xaxis + width//2, y + height + 2, zaxis + length//2),
        Block("air")
    )
    geo.placeCuboid(
        ED,
        (xaxis - width//2 - 1, y - 1, zaxis - length//2 - 1),
        (xaxis + width//2 + 1, y - 1, zaxis + length//2 + 1),
        Block("cobblestone")
    )
    
    # Build walls
    geo.placeCuboidHollow(
        ED,
        (xaxis - width//2, y, zaxis - length//2),
        (xaxis + width//2, y + height - 1, zaxis + length//2),
        wallPalette
    )
    
    # Add floor
    geo.placeCuboid(
        ED,
        (xaxis - width//2 + 1, y, zaxis - length//2 + 1),
        (xaxis + width//2 - 1, y, zaxis + length//2 - 1),
        Block("oak_planks")
    )
    
    # Build roof
    for i in range(width//2 + 2):
        geo.placeCuboid(
            ED,
            (xaxis - width//2 + i, y + height + i, zaxis - length//2 - 1),
            (xaxis - width//2 + i, y + height + i, zaxis + length//2 + 1),
            Block("spruce_stairs", {"facing": "east"})
        )
        geo.placeCuboid(
            ED,
            (xaxis + width//2 - i, y + height + i, zaxis - length//2 - 1),
            (xaxis + width//2 - i, y + height + i, zaxis + length//2 + 1),
            Block("spruce_stairs", {"facing": "west"})
        )
    
    # Add door
    ED.placeBlock(
        (xaxis - width//2, y, zaxis),
        Block("oak_door", {"facing": "east", "half": "lower"})
    )
    ED.placeBlock(
        (xaxis - width//2, y + 1, zaxis),
        Block("oak_door", {"facing": "east", "half": "upper"})
    )
    
    # Add windows
    for z in [zaxis - 2, zaxis + 2]:
        geo.placeCuboid(
            ED,
            (xaxis - width//2, y + 2, z),
            (xaxis - width//2, y + 3, z),
            Block("glass_pane")
        )
        geo.placeCuboid(
            ED,
            (xaxis + width//2, y + 2, z),
            (xaxis + width//2, y + 3, z),
            Block("glass_pane")
        )

def main():
    try:
        buildHut()
        print("Done!")
    except KeyboardInterrupt:
        print("Pressed Ctrl-C to kill program.")

# ... (keep the if __name__ == '__main__': block) ...