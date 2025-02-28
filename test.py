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

def find_flattest_subarray(large_array, water_array, sub_array_size):
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
    min_gradient_magnitude = float('inf')
    
    # Iterate over all valid starting positions
    for start_row in range(max_start_row + 1):
        for start_col in range(max_start_col + 1):
            # Extract the current sub-arrays
            current_ground = large_array[start_row:start_row + sub_array_size, 
                                      start_col:start_col + sub_array_size]
            current_water = water_array[start_row:start_row + sub_array_size, 
                                     start_col:start_col + sub_array_size]
            
            # Skip if there's water (where water height > ground height)
            if np.any(current_water > current_ground):
                continue
            
            # Calculate the gradient magnitude for this sub-array
            gy, gx = np.gradient(current_ground)
            gradient_magnitude = np.sqrt(gx**2 + gy**2)
            avg_gradient = np.mean(gradient_magnitude)

            # If this sub-array is flatter than the flattest one found so far, update
            if avg_gradient < min_gradient_magnitude:
                min_gradient_magnitude = avg_gradient
                flattest_subarray = current_ground.copy()
                flattest_position = (start_row, start_col)
                max_value = np.max(current_ground)

    return flattest_subarray, flattest_position, min_gradient_magnitude, max_value

# Example usage
if __name__ == "__main__":
    # Get both heightmaps
    ground_heightmap = WORLDSLICE.heightmaps["OCEAN_FLOOR"]  # Excludes water
    water_heightmap = WORLDSLICE.heightmaps["MOTION_BLOCKING"]  # Includes water
    
    # Find the flattest 10x10 sub-array
    sub_array_size = 10
    flattest_subarray, position, flatness_value, max_value = find_flattest_subarray(
        ground_heightmap, 
        water_heightmap, 
        sub_array_size
    )
    
    if position is None:
        print("No suitable location found (all areas contain water)")
    else:
        print(f"The flattest {sub_array_size}x{sub_array_size} sub-array starts at position {position}")
        print(f"Average gradient magnitude (flatness value): {flatness_value:.4f}")
        
        # Visualize the results
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # Plot the ground heightmap
        im0 = axes[0].imshow(ground_heightmap, cmap='terrain')
        axes[0].set_title("Ground Heightmap (OCEAN_FLOOR)")
        fig.colorbar(im0, ax=axes[0])
        
        # Plot the water heightmap
        im1 = axes[1].imshow(water_heightmap, cmap='terrain')
        axes[1].set_title("Water Heightmap (MOTION_BLOCKING)")
        fig.colorbar(im1, ax=axes[1])
        
        # Plot water detection (difference between heightmaps)
        water_detection = water_heightmap > ground_heightmap
        im2 = axes[2].imshow(water_detection, cmap='binary')
        axes[2].set_title("Water Detection (white = water)")
        
        # Highlight the flattest region on all plots
        if position is not None:
            start_row, start_col = position
            for ax in axes:
                rect = plt.Rectangle(
                    (start_col - 0.5, start_row - 0.5),
                    sub_array_size, sub_array_size,
                    edgecolor='red',
                    facecolor='none',
                    linewidth=2
                )
                ax.add_patch(rect)
        
        plt.tight_layout()
        plt.show()