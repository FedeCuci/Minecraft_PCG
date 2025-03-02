#!/usr/bin/env python3
import logging
import numpy as np
import random
from termcolor import colored
from gdpc import Block, Editor
from gdpc import geometry as geo
import atexit
import matplotlib.pyplot as plt

# Set up logging and editor
logging.basicConfig(format=colored("%(name)s - %(levelname)s - %(message)s", color="yellow"))
ED = Editor(buffering=True)
atexit.register(ED.flushBuffer)
BUILD_AREA = ED.getBuildArea()
STARTX, STARTY, STARTZ = BUILD_AREA.begin
LASTX, LASTY, LASTZ = BUILD_AREA.last
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)


def find_flattest_subarray(large_array, sub_array_size):
    # Get array dimensions
    num_rows, num_cols = large_array.shape
    
    # Check if sub-array size is valid
    if sub_array_size > num_rows or sub_array_size > num_cols:
        raise ValueError("Sub-array size is larger than the original array.")
    
    # Calculate maximum starting positions
    max_start_row = num_rows - sub_array_size
    max_start_col = num_cols - sub_array_size
    
    # Initialize variables to track flattest sub-array
    flattest_subarray = None
    flattest_position = None
    min_gradient_magnitude = float('inf')  # Start with infinity

    water_array = WORLDSLICE.heightmaps['MOTION_BLOCKING'] - WORLDSLICE.heightmaps['OCEAN_FLOOR']
    leaves_array = WORLDSLICE.heightmaps['MOTION_BLOCKING'] - WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
    
    # Iterate over all valid starting positions
    for start_row in range(max_start_row + 1):
        for start_col in range(max_start_col + 1):
            # Extract the current sub-array
            current_subarray = large_array[start_row:start_row + sub_array_size, start_col:start_col + sub_array_size]
            current_water_subarray = water_array[start_row:start_row + sub_array_size, start_col:start_col + sub_array_size]
            
            # Calculate the gradient magnitude for this sub-array
            gy, gx = np.gradient(current_subarray)
            gradient_magnitude = np.sqrt(gx**2 + gy**2)
            avg_gradient = np.mean(gradient_magnitude)

            # If this sub-array is flatter than the flattest one found so far and there is no water, update
            if avg_gradient < min_gradient_magnitude and np.all(current_water_subarray == 0):

                min_gradient_magnitude = avg_gradient
                flattest_position = (start_row, start_col)
    
    # Check for leaves in the optimal area
    start_row, start_col = flattest_position
    optimal_area_leaves = leaves_array[start_row:start_row + sub_array_size, start_col:start_col + sub_array_size]
    trees_present = np.any(optimal_area_leaves > 0)
    print(trees_present)
    
    if flattest_position is None:
        print('There is not flat enough surface that is not on water')
        exit()

    return flattest_position

def place_block(position, process_area):
    optimal_x = position[0] # x is the column
    optimal_z = position[1] # y is the row

    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    max_local_height = 0

    for dx in range(process_area):
        for dz in range(process_area):
            # Calculate world coordinates
            world_x = STARTX + optimal_x + dx
            world_z = STARTZ + optimal_z + dz
            
            # Get height at this position
            local_x = optimal_x + dx
            local_z = optimal_z + dz
            height = heights[(local_x, local_z)]

            if height > max_local_height:
                max_local_height = height

    # Fill the entire optimal area with cobblestone
    for dx in range(process_area):
        for dz in range(process_area):
            # Calculate world coordinates
            world_x = STARTX + optimal_x + dx
            world_z = STARTZ + optimal_z + dz
            
            # Get height at this position
            local_x = optimal_x + dx
            local_z = optimal_z + dz
            height = heights[(local_x, local_z)]  # Note: heightmap indices are (x,z)

            for y in range(height + 1, height + 20):
                ED.placeBlock((world_x, y, world_z), Block("air"))
            
            # Place cobblestone blocks from the ground up to 3 blocks high
            for y in range(height, max_local_height):  # You can adjust the +3 to change wall height
                ED.placeBlock((world_x, y, world_z), Block("cobblestone"))
    
    # Calculate cottage dimensions
    start_x = STARTX + optimal_x + 1  # Inset by 1 from the foundation edge
    start_z = STARTZ + optimal_z + 1
    width = process_area - 2  # Leave 1 block margin on each side
    length = process_area - 2
    wall_height = 4  # You can adjust this value

    # Build the cottage components
    build_walls(ED, start_x, start_z, max_local_height, width, length, wall_height)
    build_roof(ED, start_x, start_z, max_local_height, width, length, wall_height)
    add_details(ED, start_x, start_z, max_local_height, width, length, wall_height)
    add_interior(ED, start_x, start_z, max_local_height, width, length, wall_height)

def build_walls(ED, start_x, start_z, y, width, length, height):
    """Build walls starting from the top-left corner."""
    print("Building walls...")
    
    # Front and back walls
    for x in range(start_x, start_x + width + 1):
        # Front wall
        geo.placeCuboid(
            ED,
            (x, y - 1, start_z),
            (x, y + height - 1, start_z),
            Block("stone")
        )
        # Back wall
        geo.placeCuboid(
            ED,
            (x, y - 1, start_z + length),
            (x, y + height - 1, start_z + length),
            Block("stone")
        )
    
    # Side walls
    for z in range(start_z, start_z + length + 1):
        # Left wall
        geo.placeCuboid(
            ED,
            (start_x, y - 1, z),
            (start_x, y + height - 1, z),
            Block("stone")
        )
        # Right wall
        geo.placeCuboid(
            ED,
            (start_x + width, y - 1, z),
            (start_x + width, y + height - 1, z),
            Block("stone")
        )
    
    # Corner pillars
    for x in [start_x, start_x + width]:
        for z in [start_z, start_z + length]:
            geo.placeCuboid(
                ED,
                (x, y - 1, z),
                (x, y + height - 1, z),
                Block("spruce_log", {"axis": "y"})
            )

def build_roof(ED, start_x, start_z, y, width, length, height):
    print("Building roof...")
    # Triangular gables
    for i in range(width//2 + 1):
        # Front gable
        geo.placeCuboid(
            ED,
            (start_x + i, y + height - 1 + i, start_z),
            (start_x + width - i, y + height - 1 + i, start_z),
            Block("spruce_planks")
        )
        # Back gable
        geo.placeCuboid(
            ED,
            (start_x + i, y + height - 1 + i, start_z + length),
            (start_x + width - i, y + height - 1 + i, start_z + length),
            Block("spruce_planks")
        )
    
    # Roof slopes
    for i in range(width//2 + 2):
        if i == width//2 + 1:
            # Ridge beam
            geo.placeCuboid(
                ED,
                (start_x + width//2, y + height + i - 1, start_z - 1),
                (start_x + width//2, y + height + i - 1, start_z + length + 1),
                Block("dark_oak_planks")
            )
        else:
            # Left slope
            geo.placeCuboid(
                ED,
                (start_x + i, y + height + i, start_z - 1),
                (start_x + i, y + height + i, start_z + length + 1),
                Block("dark_oak_stairs", {"facing": "east"})
            )
            # Right slope
            geo.placeCuboid(
                ED,
                (start_x + width - i, y + height + i, start_z - 1),
                (start_x + width - i, y + height + i, start_z + length + 1),
                Block("dark_oak_stairs", {"facing": "west"})
            )

def add_details(ED, start_x, start_z, y, width, length, height):
    print("Adding details...")
    # Door (in the middle of the front wall)
    door_x = start_x
    door_z = start_z + length//2
    ED.placeBlock((door_x, y, door_z), Block("spruce_door", {"facing": "east", "half": "lower"}))
    ED.placeBlock((door_x, y + 1, door_z), Block("spruce_door", {"facing": "east", "half": "upper"}))
    
    # Windows
    window_positions = []
    
    # Side windows
    for z_offset in range(2, length - 1, 3):
        window_positions.append((start_x, start_z + z_offset))  # Left wall
        window_positions.append((start_x + width, start_z + z_offset))  # Right wall
    
    # Front and back windows
    for x_offset in range(2, width - 1, 3):
        window_positions.append((start_x + x_offset, start_z))  # Front wall
        window_positions.append((start_x + x_offset, start_z + length))  # Back wall
    
    for wx, wz in window_positions:
        # Skip if it's the door position
        if not (wx == door_x and wz == door_z):
            ED.placeBlock((wx, y + 1, wz), Block("glass_pane"))
            ED.placeBlock((wx, y + 2, wz), Block("glass_pane"))
            
            # Determine facing direction for trapdoors
            facing = "north"
            if wz == start_z: facing = "south"  # Front wall
            elif wz == start_z + length: facing = "north"  # Back wall
            elif wx == start_x: facing = "east"  # Left wall
            elif wx == start_x + width: facing = "west"  # Right wall
            
            ED.placeBlock((wx, y, wz), Block("spruce_trapdoor", {"facing": facing, "half": "top"}))
    
    # Chimney
    chimney_x = start_x + width - 2
    chimney_z = start_z + length - 2
    geo.placeCuboid(
        ED,
        (chimney_x, y - 1, chimney_z),
        (chimney_x, y + height + 3, chimney_z),
        Block("bricks")
    )
    ED.placeBlock(
        (chimney_x, y + height + 3, chimney_z),
        Block("campfire", {"lit": "true"})
    )

def add_interior(ED, start_x, start_z, y, width, length, height):
    print("Adding interior decorations...")
    
    # Plants with support blocks
    plant_positions = [
        ((start_x + width//2, y, start_z + 2), "oak_fence", "potted_fern"),
        ((start_x + width//2, y, start_z + length - 2), "oak_fence", "potted_bamboo")
    ]
    
    for pos, support, plant in plant_positions:
        ED.placeBlock(pos, Block(support))
        ED.placeBlock((pos[0], pos[1] + 1, pos[2]), Block(plant))
    
    # Bed
    ED.placeBlock((start_x + width - 2, y, start_z + length - 3), Block("red_bed", {"facing": "west", "part": "foot"}))
    ED.placeBlock((start_x + width - 3, y, start_z + length - 3), Block("red_bed", {"facing": "west", "part": "head"}))
    
    # Chests
    ED.placeBlock((start_x + width - 2, y, start_z + length - 4), Block("chest", {"facing": "south"}))
    ED.placeBlock((start_x + width - 3, y, start_z + length - 4), Block("chest", {"facing": "south"}))
    
    # Crafting area
    ED.placeBlock((start_x + 2, y, start_z + 2), Block("crafting_table"))
    ED.placeBlock((start_x + 3, y, start_z + 2), Block("furnace", {"facing": "south"}))
    
    # Dining area
    table_x = start_x + width//2
    table_z = start_z + length//2
    ED.placeBlock((table_x, y, table_z), Block("oak_fence"))  # Table leg
    ED.placeBlock((table_x, y + 1, table_z), Block("oak_pressure_plate"))  # Table top
    ED.placeBlock((table_x - 1, y, table_z), Block("oak_stairs", {"facing": "east"}))  # Chair
    ED.placeBlock((table_x + 1, y, table_z), Block("oak_stairs", {"facing": "west"}))  # Chair
    
    # Lighting
    for x_off in [width//4, width*3//4]:
        for z_off in [length//4, length*3//4]:
            ED.placeBlock((start_x + x_off, y + height - 2, start_z + z_off), 
                         Block("lantern", {"hanging": "true"}))

# Example usage
if __name__ == "__main__":

    heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"] # The top non-air solid blocks.
    
    # Find the flattest 10x10 sub-array
    sub_array_size = random.randint(12, 18)
    position = find_flattest_subarray(heightmap, sub_array_size)
    place_block(position, sub_array_size)