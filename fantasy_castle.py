#!/usr/bin/env python3

import logging
from random import randint
from termcolor import colored
from gdpc import Block, Editor
from gdpc import geometry as geo
from gdpc import minecraft_tools as mt

# Set up logging
logging.basicConfig(format=colored("%(name)s - %(levelname)s - %(message)s", color="yellow"))

# Create editor and get build area
ED = Editor(buffering=True)
BUILD_AREA = ED.getBuildArea()
STARTX, STARTY, STARTZ = BUILD_AREA.begin
LASTX, LASTY, LASTZ = BUILD_AREA.last
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)

def buildCastle():
    # Calculate center and base height
    xaxis = STARTX + (LASTX - STARTX) // 2
    zaxis = STARTZ + (LASTZ - STARTZ) // 2
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    y = heights[(xaxis - STARTX, zaxis - STARTZ)]

    print("Building castle foundation...")
    # Main castle platform (40x40)
    geo.placeCuboid(
        ED,
        (xaxis - 20, y - 2, zaxis - 20),
        (xaxis + 20, y, zaxis + 20),
        Block("stone_bricks")
    )

    print("Building central keep...")
    # Central keep (20x20)
    keep_height = 25
    geo.placeCuboidHollow(
        ED,
        (xaxis - 10, y + 1, zaxis - 10),
        (xaxis + 10, y + keep_height, zaxis + 10),
        Block("deepslate_bricks")
    )

    # Keep floors
    for floor in range(5):
        floor_y = y + 5 * floor + 1
        geo.placeCuboid(
            ED,
            (xaxis - 9, floor_y, zaxis - 9),
            (xaxis + 9, floor_y, zaxis + 9),
            Block("dark_oak_planks")
        )

    print("Building corner towers...")
    # Corner towers
    tower_positions = [
        (xaxis - 18, zaxis - 18),
        (xaxis - 18, zaxis + 18),
        (xaxis + 18, zaxis - 18),
        (xaxis + 18, zaxis + 18)
    ]

    for tx, tz in tower_positions:
        buildTower(tx, y, tz, 30)

    print("Building castle walls...")
    # Connecting walls
    wall_height = 15
    # North wall
    geo.placeCuboidHollow(
        ED,
        (xaxis - 18, y + 1, zaxis - 18),
        (xaxis + 18, y + wall_height, zaxis - 18),
        Block("stone_bricks")
    )
    # South wall
    geo.placeCuboidHollow(
        ED,
        (xaxis - 18, y + 1, zaxis + 18),
        (xaxis + 18, y + wall_height, zaxis + 18),
        Block("stone_bricks")
    )
    # East wall
    geo.placeCuboidHollow(
        ED,
        (xaxis + 18, y + 1, zaxis - 18),
        (xaxis + 18, y + wall_height, zaxis + 18),
        Block("stone_bricks")
    )
    # West wall
    geo.placeCuboidHollow(
        ED,
        (xaxis - 18, y + 1, zaxis - 18),
        (xaxis - 18, y + wall_height, zaxis + 18),
        Block("stone_bricks")
    )

    print("Adding decorative elements...")
    # Main entrance
    buildGatehouse(xaxis, y, zaxis - 18)

def buildTower(x, y, z, height):
    """Build a circular tower with a conical roof."""
    radius = 5
    # Tower body
    geo.placeCylinder(ED, (x, y + 1, z), radius, height, Block("deepslate_tiles"), tube=True)
    
    # Tower roof
    for i in range(radius + 3):
        geo.placeCylinder(
            ED,
            (x, y + height + i, z),
            radius - (i * 0.8),
            1,
            Block("dark_prismarine")
        )
    
    # Windows
    for floor in range(height // 5):
        window_y = y + 3 + (floor * 5)
        for facing in ["north", "south", "east", "west"]:
            if facing in ["north", "south"]:
                window_x = x
                window_z = z + (radius if facing == "south" else -radius)
            else:
                window_x = x + (radius if facing == "east" else -radius)
                window_z = z
            ED.placeBlock((window_x, window_y, window_z), Block("glass"))
            ED.placeBlock((window_x, window_y + 1, window_z), Block("glass"))

def buildGatehouse(x, y, z):
    """Build an impressive castle entrance."""
    width = 6
    height = 12
    depth = 8
    
    # Main structure
    geo.placeCuboidHollow(
        ED,
        (x - width, y + 1, z - depth),
        (x + width, y + height, z + 1),
        Block("stone_bricks")
    )
    
    # Gateway
    geo.placeCuboid(
        ED,
        (x - 2, y + 1, z - depth),
        (x + 2, y + 6, z + 1),
        Block("air")
    )
    
    # Portcullis (iron bars)
    geo.placeCuboid(
        ED,
        (x - 2, y + 1, z - depth + 1),
        (x + 2, y + 6, z - depth + 1),
        Block("iron_bars")
    )

def main():
    try:
        print("Starting castle construction...")
        buildCastle()
        print("Castle completed!")
    except KeyboardInterrupt:
        print("Construction cancelled!")

if __name__ == "__main__":
    main()