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

            # print(current_subarray)
            # print(f'Max value: {np.max(current_subarray)}')
            # print(f'Average gradient: {avg_gradient}')
            # input()

            # If this sub-array is flatter than the flattest one found so far, update
            if avg_gradient < min_gradient_magnitude and np.all(current_water_subarray == 0):

                min_gradient_magnitude = avg_gradient
                flattest_subarray = current_subarray.copy()  # Make a copy to avoid reference issues
                flattest_position = (start_row, start_col)
                max_value = np.max(current_subarray)

                max_value = np.max(current_subarray)
    
    if flattest_position is None:
        print('There is not flat enough surface that is not on water')
        exit()

    # print(coordinate_array)

    return flattest_subarray, flattest_position, min_gradient_magnitude, max_value

def place_block(position, process_area):
    optimal_x = position[0] # x is the column
    optimal_z = position[1] # y is the row

    # relative_x = optimal_x - STARTX
    # relative_z = optimal_z - STARTY

    # print(relative_x, relative_z)

    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    # Fill the entire optimal area with cobblestone
    for dx in range(process_area):
        for dz in range(process_area):
            # Calculate world coordinates
            world_x = STARTX + optimal_x + dx
            world_z = STARTZ + optimal_z + dz
            
            # Get height at this position
            local_x = optimal_x + dx
            local_z = optimal_z + dz
            height = heights[(local_z, local_x)]  # Note: heightmap indices are (x,z)
            
            # Place cobblestone blocks from the ground up to 3 blocks high
            for y in range(height, height + 4):  # You can adjust the +3 to change wall height
                ED.placeBlock((world_x, y, world_z), Block("cobblestone"))

    


    # ED.placeBlock((relative_x, path_y, relative_z), Block("cobblestone"))

# Example usage
if __name__ == "__main__":

    available_height_maps = ["WORLD_SURFACE", "MOTION_BLOCKING", "MOTINO_BLOCKING_NO_LEAVES", "OCEAN_FLOOR"]

    heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"] # The top non-air solid blocks.
    
    # Find the flattest 10x10 sub-array
    sub_array_size = random.randint(6, 10)
    flattest_subarray, position, flatness_value, max_value = find_flattest_subarray(heightmap, sub_array_size)
    place_block(position, sub_array_size)
    
    print(f"The flattest {sub_array_size}x{sub_array_size} sub-array starts at position {position}")
    print(f"Average gradient magnitude (flatness value): {flatness_value:.4f}")
    
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

    plt.tight_layout()
    plt.show()