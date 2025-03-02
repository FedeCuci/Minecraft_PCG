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

def smooth_heightmap(heightmap, window_size=3, threshold=2):
    # Create a copy of the original heightmap
    smoothed = heightmap.copy()
    rows, cols = heightmap.shape
    pad = window_size // 2

    # Pad the array to handle edges
    padded = np.pad(heightmap, pad, mode='edge')

    # Iterate through each cell in the original heightmap
    for i in range(rows):
        for j in range(cols):
            # Extract the local window
            window = padded[i:i + window_size, j:j + window_size]
            
            # Calculate local statistics
            local_median = np.median(window)
            local_std = np.std(window)
            
            # Check if the center value is an outlier
            center_value = heightmap[i, j]
            if abs(center_value - local_median) > threshold * local_std:
                # Replace with local median if it's an outlier
                smoothed[i, j] = local_median

    return smoothed

def find_flattest_subarray(large_array, sub_array_size):
    # Get array dimensions
    num_rows, num_cols = large_array.shape
    smoothed_heightmap = None
    margin = random.randint(4, 8)  # Random margin between 4-8 blocks
    border_margin = 4  # Minimum distance from the border
    
    # Check if sub-array size plus margins is valid
    if sub_array_size + 2 * border_margin > num_rows or sub_array_size + 2 * border_margin > num_cols:
        print("Warning: Build area is too small with the requested margins.")
        # Adjust sub_array_size if needed
        sub_array_size = min(num_rows, num_cols) - 2 * border_margin
        if sub_array_size < 4:  # If it's too small to build anything meaningful
            raise ValueError("Build area is too small to place a house with the required margins.")
    
    # Calculate maximum starting positions with border margin
    max_start_row = num_rows - sub_array_size - border_margin
    max_start_col = num_cols - sub_array_size - border_margin
    
    # Initialize variables to track flattest sub-array
    flattest_subarray = None
    flattest_position = None
    min_gradient_magnitude = float('inf')  # Start with infinity

    water_array = WORLDSLICE.heightmaps['MOTION_BLOCKING'] - WORLDSLICE.heightmaps['OCEAN_FLOOR']
    leaves_array = WORLDSLICE.heightmaps['MOTION_BLOCKING'] - WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
    
    # Iterate over all valid starting positions, respecting the border margin
    for start_row in range(border_margin, max_start_row + 1):
        for start_col in range(border_margin, max_start_col + 1):
            # Extract the current sub-array
            current_subarray = large_array[start_row:start_row + sub_array_size, 
                                          start_col:start_col + sub_array_size]
            current_water_subarray = water_array[start_row:start_row + sub_array_size, 
                                               start_col:start_col + sub_array_size]
            
            # Calculate the gradient magnitude for this sub-array
            gy, gx = np.gradient(current_subarray)
            gradient_magnitude = np.sqrt(gx**2 + gy**2)
            avg_gradient = np.mean(gradient_magnitude)

            # If this sub-array is flatter than the flattest one found so far and there is no water, update
            if avg_gradient < min_gradient_magnitude and np.all(current_water_subarray == 0):
                min_gradient_magnitude = avg_gradient
                flattest_position = (start_row, start_col)
                flattest_subarray = current_subarray.copy()  # Make a copy to avoid

            # If this sub-array is flatter than the flattest one found so far and there is no water, update
            if avg_gradient < min_gradient_magnitude and np.all(current_water_subarray == 0):

                min_gradient_magnitude = avg_gradient
                flattest_position = (start_row, start_col)
                flattest_subarray = current_subarray.copy()  # Make a copy to avoid reference issues
    
    if flattest_position is None:
        print('There is not flat enough surface that is not on water')
        exit()

    # Check for leaves in the optimal area
    start_row, start_col = flattest_position
    optimal_area_leaves = leaves_array[start_row:start_row + sub_array_size, 
                                     start_col:start_col + sub_array_size]
    trees_present = np.any(optimal_area_leaves > 0)

    if trees_present:
        # Usage in your code:
        heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        smoothed_heightmap = smooth_heightmap(heightmap, window_size=7, threshold=2)

        print("Clearing trees in and around the optimal area...")
        
        # Get array dimensions
        rows, cols = smoothed_heightmap.shape
        
        # Clear everything above the foundation height in the expanded area
        for dx in range(max(0, start_row - margin), min(rows, start_row + sub_array_size + margin)):
            for dz in range(max(0, start_col - margin), min(cols, start_col + sub_array_size + margin)):
                world_x = STARTX + dx
                world_z = STARTZ + dz
                
                # Get the height from smoothed_heightmap at this position
                local_height = smoothed_heightmap[dx, dz]
                
                # Clear from local smoothed height up to a reasonable height
                for y in range(int(local_height), int(local_height) + 20):
                    ED.placeBlock((world_x, y, world_z), Block("air"))

    return flattest_position, smoothed_heightmap, flattest_subarray

def create_material_palettes():
    """Create a collection of different material palettes for house building."""
    return [
        {
            "foundation": "cobblestone",
            "floor_primary": "dark_oak_planks",
            "floor_secondary": "birch_planks",
            "walls": "stone",
            "pillars": "spruce_log",
            "roof_frame": "spruce_planks",
            "roof_material": "dark_oak_stairs",
            "roof_ridge": "dark_oak_planks",
            "door": "spruce_door",
            "window_pane": "glass_pane",
            "window_sill": "spruce_trapdoor",
            "chimney": "bricks"
        },
        {
            "foundation": "stone_bricks",
            "floor_primary": "oak_planks",
            "floor_secondary": "spruce_planks",
            "walls": "stripped_oak_log",
            "pillars": "oak_log",
            "roof_frame": "oak_planks",
            "roof_material": "spruce_stairs",
            "roof_ridge": "spruce_planks",
            "door": "oak_door",
            "window_pane": "glass_pane",
            "window_sill": "oak_trapdoor",
            "chimney": "stone_bricks"
        },
        {
            "foundation": "deepslate_bricks",
            "floor_primary": "spruce_planks",
            "floor_secondary": "dark_oak_planks",
            "walls": "deepslate_tiles",
            "pillars": "dark_oak_log",
            "roof_frame": "dark_oak_planks",
            "roof_material": "spruce_stairs",
            "roof_ridge": "spruce_planks",
            "door": "dark_oak_door",
            "window_pane": "tinted_glass",
            "window_sill": "dark_oak_trapdoor",
            "chimney": "deepslate_bricks"
        },
        {
            "foundation": "sandstone",
            "floor_primary": "smooth_sandstone",
            "floor_secondary": "cut_sandstone",
            "walls": "sandstone",
            "pillars": "birch_log",
            "roof_frame": "birch_planks",
            "roof_material": "birch_stairs",
            "roof_ridge": "smooth_sandstone",
            "door": "birch_door",
            "window_pane": "glass_pane",
            "window_sill": "birch_trapdoor",
            "chimney": "terracotta"
        }
    ]

def place_block(position, process_area, smoothed_heightmap):
    # Select a random material palette
    palettes = create_material_palettes()
    palette = random.choice(palettes)
    
    optimal_x = position[0] # x is the column
    optimal_z = position[1] # y is the row

    if smoothed_heightmap is not None:
        heights = smoothed_heightmap
    else:
        heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    max_local_height = 0

    # First, determine the maximum height in the area
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

    # Fill the entire optimal area with foundation material
    for dx in range(process_area):
        for dz in range(process_area):
            # Calculate world coordinates
            world_x = STARTX + optimal_x + dx
            world_z = STARTZ + optimal_z + dz
            
            # Get height at this position
            local_x = optimal_x + dx
            local_z = optimal_z + dz
            height = heights[(local_x, local_z)]  # Note: heightmap indices are (x,z)

            # Clear any existing blocks above the foundation
            for y in range(height + 1, height + 20):
                ED.placeBlock((world_x, y, world_z), Block("air"))
            
            # Place foundation blocks from the ground up to max_local_height
            for y in range(height, max_local_height + 1):  # +1 to ensure a flat top surface
                ED.placeBlock((world_x, y, world_z), Block(palette["foundation"]))
    
    # Calculate house dimensions - make it smaller than the foundation
    # Add a margin of at least 1 block on each side
    margin = 1
    house_width = process_area - 2 * margin
    house_length = process_area - 2 * margin
    
    # Ensure house dimensions are at least 4x4
    if house_width < 4 or house_length < 4:
        print("Warning: Foundation too small for a proper house. Adjusting dimensions.")
        house_width = max(4, house_width)
        house_length = max(4, house_length)
        margin = max(1, (process_area - house_width) // 2)
    
    # Calculate starting position for the house (centered on the foundation)
    start_x = STARTX + optimal_x + margin
    start_z = STARTZ + optimal_z + margin
    wall_height = random.randint(4, 7)  # You can adjust this value

    # Add checkered floor pattern for the house area
    for dx in range(house_width):
        for dz in range(house_length):
            world_x = start_x + dx
            world_z = start_z + dz
            # Place floor at max_local_height + 1 (one block above the foundation)
            if (dx + dz) % 2 == 0:
                ED.placeBlock((world_x, max_local_height, world_z), Block(palette["floor_primary"]))
            else:
                ED.placeBlock((world_x, max_local_height, world_z), Block(palette["floor_secondary"]))

    # Adjust the starting height for walls to be one block higher than the foundation
    floor_height = max_local_height + 1
    
    # Then pass the palette to your building functions with the adjusted dimensions
    build_walls(ED, start_x, start_z, floor_height, house_width - 1, house_length - 1, wall_height, palette)
    build_roof(ED, start_x, start_z, floor_height, house_width - 1, house_length - 1, wall_height, palette)
    add_details(ED, start_x, start_z, floor_height, house_width - 1, house_length - 1, wall_height, palette)
    add_interior(ED, start_x, start_z, floor_height, house_width - 1, house_length - 1, wall_height, palette)

def build_walls(ED, start_x, start_z, y, width, length, height, palette):
    """Build walls starting from the top-left corner."""
    print("Building walls...")
    
    # Front and back walls
    for x in range(start_x, start_x + width + 1):
        # Front wall
        geo.placeCuboid(
            ED,
            (x, y - 1, start_z),
            (x, y + height - 1, start_z),
            Block(palette["walls"])
        )
        # Back wall
        geo.placeCuboid(
            ED,
            (x, y - 1, start_z + length),
            (x, y + height - 1, start_z + length),
            Block(palette["walls"])
        )
    
    # Side walls
    for z in range(start_z, start_z + length + 1):
        # Left wall
        geo.placeCuboid(
            ED,
            (start_x, y - 1, z),
            (start_x, y + height - 1, z),
            Block(palette["walls"])
        )
        # Right wall
        geo.placeCuboid(
            ED,
            (start_x + width, y - 1, z),
            (start_x + width, y + height - 1, z),
            Block(palette["walls"])
        )
    
    # Corner pillars
    for x in [start_x, start_x + width]:
        for z in [start_z, start_z + length]:
            geo.placeCuboid(
                ED,
                (x, y - 1, z),
                (x, y + height - 1, z),
                Block(palette["pillars"], {"axis": "y"})
            )

def build_roof(ED, start_x, start_z, y, width, length, height, palette):
    print("Building roof...")
    # Triangular gables
    for i in range(width//2 + 1):
        # Front gable
        geo.placeCuboid(
            ED,
            (start_x + i, y + height - 1 + i, start_z),
            (start_x + width - i, y + height - 1 + i, start_z),
            Block(palette["roof_frame"])
        )
        # Back gable
        geo.placeCuboid(
            ED,
            (start_x + i, y + height - 1 + i, start_z + length),
            (start_x + width - i, y + height - 1 + i, start_z + length),
            Block(palette["roof_frame"])
        )
    
    # Roof slopes
    for i in range(width//2 + 2):
        if i == width//2 + 1:
            # Ridge beam
            geo.placeCuboid(
                ED,
                (start_x + width//2, y + height + i - 1, start_z - 1),
                (start_x + width//2, y + height + i - 1, start_z + length + 1),
                Block(palette["roof_ridge"])
            )
        else:
            # Left slope
            geo.placeCuboid(
                ED,
                (start_x + i, y + height + i, start_z - 1),
                (start_x + i, y + height + i, start_z + length + 1),
                Block(palette["roof_material"], {"facing": "east"})
            )
            # Right slope
            geo.placeCuboid(
                ED,
                (start_x + width - i, y + height + i, start_z - 1),
                (start_x + width - i, y + height + i, start_z + length + 1),
                Block(palette["roof_material"], {"facing": "west"})
            )

def add_details(ED, start_x, start_z, y, width, length, height, palette):
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
    
    # Calculate window height based on wall height
    window_height = max(2, height - 3)  # At least 2 blocks tall, but scales with wall height
    window_start_y = y + 1  # Start windows 1 block above the floor
    
    for wx, wz in window_positions:
        # Skip if it's the door position
        if not (wx == door_x and wz == door_z):
            # Place window panes with variable height
            for wy in range(window_start_y, window_start_y + window_height):
                ED.placeBlock((wx, wy, wz), Block(palette["window_pane"]))
            
            # Determine facing direction for window sills
            facing = "north"
            if wz == start_z: facing = "south"  # Front wall
            elif wz == start_z + length: facing = "north"  # Back wall
            elif wx == start_x: facing = "east"  # Left wall
            elif wx == start_x + width: facing = "west"  # Right wall
            
            # Add window sill at the bottom
            ED.placeBlock((wx, window_start_y - 1, wz), Block(palette["window_sill"], {"facing": facing, "half": "top"}))
            
            # Optionally add a decorative element above the window
            if window_height < height - 3:  # If there's space above the window
                ED.placeBlock((wx, window_start_y + window_height, wz), Block(palette["window_sill"], {"facing": facing, "half": "bottom"}))
    
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

def add_interior(ED, start_x, start_z, y, width, length, height, palette):
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
    
    sub_array_size = random.randint(10, 14)
    position, smoothed_heightmap, flattest_subarray = find_flattest_subarray(heightmap, sub_array_size)
    place_block(position, sub_array_size, smoothed_heightmap)

    # Visualize the results
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Plot the entire heightmap - transposed
    im0 = axes[0].imshow(heightmap.T, cmap='inferno')  # Added .T here
    axes[0].set_title("Original Heightmap")
    fig.colorbar(im0, ax=axes[0])

    # Highlight the flattest region
    start_row, start_col = position
    rect = plt.Rectangle((start_row - 0.5, start_col - 0.5), sub_array_size, sub_array_size,  # Swapped start_row and start_col
                        edgecolor='red', facecolor='none', linewidth=2)
    axes[0].add_patch(rect)

    # Plot the flattest sub-array - transposed
    im1 = axes[1].imshow(flattest_subarray.T, cmap='inferno')  # Added .T here
    axes[1].set_title(f"Flattest {sub_array_size}x{sub_array_size} Sub-array")
    fig.colorbar(im1, ax=axes[1])

    rect = plt.Rectangle((start_row - 0.5, start_col - 0.5), sub_array_size, sub_array_size,
                    edgecolor='red', facecolor='none', linewidth=2)
    axes[0].add_patch(rect)

    # # Add a rectangle showing the border margin
    # border_rect = plt.Rectangle((border_margin - 0.5, border_margin - 0.5), 
    #                         num_rows - 2 * border_margin, 
    #                         num_cols - 2 * border_margin,
    #                         edgecolor='blue', facecolor='none', linestyle='--', linewidth=1)
    # axes[0].add_patch(border_rect)

    plt.tight_layout()
    plt.show()