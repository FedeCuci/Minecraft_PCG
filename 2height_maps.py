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

    # print(row_indices, col_indices)
    
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
    
    if flattest_position is None:
        print('There is not flat enough surface that is not on water')
        exit()

    return flattest_subarray, flattest_position, min_gradient_magnitude, max_value

# Example usage
if __name__ == "__main__":
    # Define available heightmaps
    available_heightmaps = ["WORLD_SURFACE", "MOTION_BLOCKING", "MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR"]
    
    # Store results for each heightmap
    results = {}
    sub_array_size = 10
    
    # Run analysis for each heightmap
    for heightmap_name in available_heightmaps:
        heightmap = WORLDSLICE.heightmaps[heightmap_name]
        flattest_subarray, position, flatness_value, max_value = find_flattest_subarray(
            heightmap,
            sub_array_size
        )
        results[heightmap_name] = {
            'subarray': flattest_subarray,
            'position': position,
            'flatness': flatness_value,
            'max_value': max_value,
            'heightmap': heightmap
        }

    # print(WORLDSLICE.heightmaps['WORLD_SURFACE'])
    # print(WORLDSLICE.heightmaps['OCEAN_FLOOR'])

    
    
    # Create visualization - modified to show pairs side by side
    fig = plt.figure(figsize=(15, 5*len(available_heightmaps)))
    
    # Create a grid of subplots
    gs = fig.add_gridspec(len(available_heightmaps), 2, hspace=0.3)
    
    # Plot results for each heightmap
    for idx, heightmap_name in enumerate(available_heightmaps):
        result = results[heightmap_name]
        
        # Create subplot for full heightmap
        ax0 = fig.add_subplot(gs[idx, 0])
        im0 = ax0.imshow(result['heightmap'], cmap='inferno')
        ax0.set_title(f"{heightmap_name} - Full Heightmap")
        fig.colorbar(im0, ax=ax0)
        
        # Create subplot for flattest subarray
        ax1 = fig.add_subplot(gs[idx, 1])
        if result['subarray'] is not None:
            im1 = ax1.imshow(result['subarray'], cmap='inferno')
            ax1.set_title(f"{heightmap_name} - Flattest {sub_array_size}x{sub_array_size} Area\nFlatness: {result['flatness']:.4f}")
            fig.colorbar(im1, ax=ax1)
            
            # Highlight the flattest region on the full heightmap
            if result['position'] is not None:
                start_row, start_col = result['position']
                rect = plt.Rectangle(
                    (start_col - 0.5, start_row - 0.5),
                    sub_array_size, sub_array_size,
                    edgecolor='red',
                    facecolor='none',
                    linewidth=2
                )
                ax0.add_patch(rect)
        
        # Print results
        # print(f"\nResults for {heightmap_name}:")
        # print(f"Position: {result['position']}")
        # print(f"Flatness value: {result['flatness']:.4f}")
        # print(f"Max height: {result['max_value']}")

        # print(WORLDSLICE.heightmaps['MOTION_BLOCKING'] - WORLDSLICE.heightmaps['OCEAN_FLOOR'])
    
    plt.tight_layout()
    plt.show()