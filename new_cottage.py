#!/usr/bin/env python3
import logging
import numpy as np
from random import randint, choice, random
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

def find_best_location(large_array, sub_array_size):
    print("Analyzing terrain to find best building location...")
    
    # Get array dimensions
    num_rows, num_cols = large_array.shape
    
    # Check if sub-array size is valid
    if sub_array_size > num_rows or sub_array_size > num_cols:
        raise ValueError("Sub-array size is larger than the original array.")
    
    # Calculate maximum starting positions
    max_start_row = num_rows - sub_array_size
    max_start_col = num_cols - sub_array_size
    
    # Initialize variables to track flattest sub-array
    min_gradient_magnitude = float('inf')
    best_position = (0, 0)
    
    # Iterate over all valid starting positions
    for start_row in range(max_start_row + 1):
        for start_col in range(max_start_col + 1):
            # Extract the current sub-array
            current_subarray = large_array[start_row:start_row + sub_array_size, 
                                        start_col:start_col + sub_array_size]
            
            # Calculate the gradient magnitude for this sub-array
            gy, gx = np.gradient(current_subarray)
            gradient_magnitude = np.sqrt(gx**2 + gy**2)
            avg_gradient = np.mean(gradient_magnitude)
            avg_height = np.mean(current_subarray)
            
            # If this sub-array is flatter than the flattest one found so far, update
            if avg_gradient < min_gradient_magnitude:
                min_gradient_magnitude = avg_gradient
                best_position = (start_row, start_col)
    
    # Convert heightmap position to world coordinates
    world_x = best_position[1] + STARTX  # col = x
    world_z = best_position[0] + STARTZ  # row = z
    world_y = large_array[best_position]  # Get height at this position
    
    print(f"Found optimal building location at ({world_x}, {world_z}, {world_y})")
    return world_x, world_z, world_y
    
def clear_space(ED, start_x, start_z, y, width, length, height):
    print("Clearing interior space...")
    # Clear main room
    geo.placeCuboid(
        ED,
        (start_x + 1, y, start_z + 1),
        (start_x + width - 1, y + height - 1, start_z + length - 1),
        Block("air")
    )
    
    # Clear roof space
    for i in range(width//2 + 1):
        geo.placeCuboid(
            ED,
            (start_x + i, y + height - 1, start_z + 1),
            (start_x + width - i, y + height + i - 1, start_z + length - 1),
            Block("air")
        )

def build_foundation(ED, start_x, start_z, y, width, length, heightmap, STARTX, STARTZ):
    print("Building foundation...")
    # Foundation support
    for dx in range(width + 2):
        for dz in range(length + 2):
            x_coord = (start_x + dx) - STARTX
            z_coord = (start_z + dz) - STARTZ
            
            # Check if the coordinates are within the slice bounds
            if 0 <= x_coord < len(heightmap) and 0 <= z_coord < len(heightmap[0]):
                current_height = heightmap[(z_coord, x_coord)]
                if current_height < y - 1:
                    geo.placeCuboid(
                        ED,
                        (start_x + dx, current_height, start_z + dz),
                        (start_x + dx, y - 1, start_z + dz),
                        Block("cobblestone")
                    )
    
    # Base foundation
    geo.placeCuboid(
        ED,
        (start_x - 1, y - 2, start_z - 1),
        (start_x + width + 1, y - 2, start_z + length + 1),
        Block("cobblestone")
    )

def build_floor(ED, start_x, start_z, y, width, length):
    print("Adding floor...")
    for dx in range(width):
        for dz in range(length):
            if (dx + dz) % 2 == 0:
                ED.placeBlock((start_x + dx, y - 1, start_z + dz), Block("dark_oak_planks"))
            else:
                ED.placeBlock((start_x + dx, y - 1, start_z + dz), Block("oak_planks"))

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
    ED.placeBlock((door_x, y, door_z), Block("spruce_door", {"facing": "west", "half": "lower"}))
    ED.placeBlock((door_x, y + 1, door_z), Block("spruce_door", {"facing": "west", "half": "upper"}))
    
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
    
    # Rain water collection barrel
    barrel_x = start_x + width - 1
    barrel_z = start_z + length//4
    ED.placeBlock((barrel_x, y, barrel_z), Block("barrel"))
    # Add hopper above connected to roof gutter
    ED.placeBlock((barrel_x, y+height-1, barrel_z), Block("hopper", {"facing": "down"}))

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
    
    # Randomize some furniture
    if random() > 0.5:
        # Add bookshelf
        ED.placeBlock((start_x + 2, y, start_z + 3), Block("bookshelf"))
    else:
        # Add brewing stand
        ED.placeBlock((start_x + 2, y, start_z + 3), Block("brewing_stand"))
    
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

def add_fence(ED, start_x, start_z, y, width, length, heightmap, STARTX, STARTZ):
    print("Adding garden fence...")
    
    # Define fence margins (distance from house to fence)
    margin = 4
    
    # Calculate fence coordinates
    fence_start_x = start_x - margin
    fence_start_z = start_z - margin
    fence_end_x = start_x + width + margin
    fence_end_z = start_z + length + margin
    
    # Fence material
    fence_block = "spruce_fence"
    gate_block = "spruce_fence_gate"
    
    # Build front fence (including corners)
    for x in range(fence_start_x, fence_end_x + 1):
        # Get the height at this position from the heightmap
        x_coord = x - STARTX
        z_coord = fence_start_z - STARTZ
        if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
            fence_y = heightmap[(z_coord, x_coord)]
            
            # Ensure there's solid ground below the fence
            for y_check in range(fence_y - 3, fence_y):
                block = ED.getBlock((x, y_check, fence_start_z))
                if block is None or block.id == "air":
                    ED.placeBlock((x, y_check, fence_start_z), Block("dirt"))
            
            ED.placeBlock((x, fence_y, fence_start_z), Block(fence_block))
            
            # Add lantern on corners
            if x == fence_start_x or x == fence_end_x:
                ED.placeBlock((x, fence_y + 1, fence_start_z), Block("lantern"))
    
    # Build back fence (including corners)
    for x in range(fence_start_x, fence_end_x + 1):
        x_coord = x - STARTX
        z_coord = fence_end_z - STARTZ
        if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
            fence_y = heightmap[(z_coord, x_coord)]
            
            # Ensure there's solid ground below the fence
            for y_check in range(fence_y - 3, fence_y):
                block = ED.getBlock((x, y_check, fence_end_z))
                if block is None or block.id == "air":
                    ED.placeBlock((x, y_check, fence_end_z), Block("dirt"))
            
            ED.placeBlock((x, fence_y, fence_end_z), Block(fence_block))
            
            # Add lantern on corners
            if x == fence_start_x or x == fence_end_x:
                ED.placeBlock((x, fence_y + 1, fence_end_z), Block("lantern"))
    
    # Build left fence (excluding corners)
    for z in range(fence_start_z + 1, fence_end_z):
        x_coord = fence_start_x - STARTX
        z_coord = z - STARTZ
        if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
            fence_y = heightmap[(z_coord, x_coord)]
            
            # Ensure there's solid ground below the fence
            for y_check in range(fence_y - 3, fence_y):
                block = ED.getBlock((fence_start_x, y_check, z))
                if block is None or block.id == "air":
                    ED.placeBlock((fence_start_x, y_check, z), Block("dirt"))
            
            ED.placeBlock((fence_start_x, fence_y, z), Block(fence_block))
    
    # Build right fence (excluding corners)
    for z in range(fence_start_z + 1, fence_end_z):
        x_coord = fence_end_x - STARTX
        z_coord = z - STARTZ
        if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
            fence_y = heightmap[(z_coord, x_coord)]
            
            # Ensure there's solid ground below the fence
            for y_check in range(fence_y - 3, fence_y):
                block = ED.getBlock((fence_end_x, y_check, z))
                if block is None or block.id == "air":
                    ED.placeBlock((fence_end_x, y_check, z), Block("dirt"))
            
            ED.placeBlock((fence_end_x, fence_y, z), Block(fence_block))
    
    # Add front gate (centered)
    gate_x = start_x + width//2
    gate_z = fence_start_z
    x_coord = gate_x - STARTX
    z_coord = gate_z - STARTZ
    if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
        gate_y = heightmap[(z_coord, x_coord)]
        ED.placeBlock((gate_x, gate_y, gate_z), Block(gate_block, {"facing": "south"}))
    
    # Add back gate (centered)
    gate_x = start_x + width//2
    gate_z = fence_end_z
    x_coord = gate_x - STARTX
    z_coord = gate_z - STARTZ
    if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
        gate_y = heightmap[(z_coord, x_coord)]
        ED.placeBlock((gate_x, gate_y, gate_z), Block(gate_block, {"facing": "north"}))
    
    return fence_start_z  # Return the z-coordinate of the front fence for path building

def add_path(ED, start_x, start_z, y, width, fence_z, heightmap, STARTX, STARTZ):
    print("Adding entrance path...")
    path_x = start_x + width//2
    
    for z in range(fence_z, start_z):
        x_coord = path_x - STARTX
        z_coord = z - STARTZ
        if 0 <= x_coord < len(heightmap[0]) and 0 <= z_coord < len(heightmap):
            path_y = heightmap[(z_coord, x_coord)]
            ED.placeBlock((path_x, path_y, z), Block("cobblestone"))
            ED.placeBlock((path_x-1, path_y, z), Block("cobblestone"))

def place_tree(ED, x, y, z, tree_type):
    # Base trunk
    height = randint(4, 6)
    for dy in range(height):
        ED.placeBlock((x, y + dy, z), Block(f"{tree_type}_log"))
    
    # Simple leaf blob
    for dx in range(-2, 3):
        for dy in range(height-2, height+2):
            for dz in range(-2, 3):
                if abs(dx) + abs(dy-height) + abs(dz) <= 4:
                    block_x, block_y, block_z = x + dx, y + dy, z + dz
                    if not (dx == 0 and dz == 0 and dy < height):  # Don't replace trunk
                        ED.placeBlock((block_x, block_y, block_z), Block(f"{tree_type}_leaves"))

def add_landscaping(ED, start_x, start_z, y, width, length, heightmap, STARTX, STARTZ):
    print("Adding trees and flowers...")
    
    # Define garden area (larger than house footprint but smaller than fence)
    garden_width = width + 6  # Leave 1 block gap from fence
    garden_length = length + 6
    
    # Define possible flowers
    flowers = [
        "poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", 
        "red_tulip", "orange_tulip", "white_tulip", "pink_tulip", "oxeye_daisy"
    ]
    
    # Add random flowers around the garden area
    for _ in range(40):
        dx = randint(-3, garden_width + 3)
        dz = randint(-3, garden_length + 3)
        
        # Skip if inside or too close to house
        if (0 <= dx <= width) and (0 <= dz <= length):
            continue
            
        x = start_x + dx
        z = start_z + dz
        x_coord, z_coord = x - STARTX, z - STARTZ
        
        if 0 <= x_coord < len(heightmap) and 0 <= z_coord < len(heightmap[0]):
            flower_y = heightmap[(z_coord, x_coord)]
            flower = choice(flowers)
            
            # Don't place flowers too close to trees
            too_close_to_tree = False
            for tx, tz in tree_positions:
                if (dx - tx)**2 + (dz - tz)**2 < 4:
                    too_close_to_tree = True
                    break
            
            if not too_close_to_tree:
                ED.placeBlock((x, flower_y, z), Block(flower))
    
    # Add some tall grass for natural look
    for _ in range(60):
        dx = randint(-3, garden_width + 3)
        dz = randint(-3, garden_length + 3)
        
        # Skip if inside house
        if (0 <= dx <= width) and (0 <= dz <= length):
            continue
            
        x = start_x + dx
        z = start_z + dz
        x_coord, z_coord = x - STARTX, z - STARTZ
        
        if 0 <= x_coord < len(heightmap) and 0 <= z_coord < len(heightmap[0]):
            grass_y = heightmap[(z_coord, x_coord)]
            if random() < 0.7:
                ED.placeBlock((x, grass_y, z), Block("grass"))
            else:
                ED.placeBlock((x, grass_y, z), Block("tall_grass", {"half": "lower"}))
                ED.placeBlock((x, grass_y + 1, z), Block("tall_grass", {"half": "upper"}))

def buildCozyCottage():
    # Get height map for terrain analysis
    heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    
    # Find the best location for a 10x10 area
    area_size = 10
    start_x, start_z, start_y = find_best_location(heightmap, area_size)
    
    # Randomize dimensions but keep them reasonable
    width = randint(6, 14)
    length = randint(16, 24)
    height = randint(5, 7)
    
    # Level the terrain for a nice building site
    # y = level_terrain(ED, start_x, start_z, start_y, width, length, heightmap, STARTX, STARTZ)
    
    # Build everything from the top-left position
    clear_space(ED, start_x, start_z, start_y, width, length, height)
    build_foundation(ED, start_x, start_z, start_y, width, length, heightmap, STARTX, STARTZ)
    build_floor(ED, start_x, start_z, start_y, width, length)
    build_walls(ED, start_x, start_z, start_y, width, length, height)
    build_roof(ED, start_x, start_z, start_y, width, length, height)
    add_details(ED, start_x, start_z, start_y, width, length, height)
    add_interior(ED, start_x, start_z, start_y, width, length, height)
    fence_z = add_fence(ED, start_x, start_z, start_y, width, length, heightmap, STARTX, STARTZ)
    add_path(ED, start_x, start_z, start_y, width, fence_z, heightmap, STARTX, STARTZ)
    add_landscaping(ED, start_x, start_z, start_y, width, length, heightmap, STARTX, STARTZ)

def main():
    try:
        buildCozyCottage()
        print("Your cozy cottage with garden and fence is ready!")
    except KeyboardInterrupt:
        print("Build canceled!")
    except Exception as e:
        print(f"Error during construction: {e}")

if __name__ == "__main__":
    main()