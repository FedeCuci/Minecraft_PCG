from gdpc import Editor, Block, Box
from gdpc.vector_tools import addY
from gdpc import geometry as geo
import random

def find_flat_area(editor, width, length, max_search=100):
    """Find the flattest area near the player for building."""
    # Get build area boundaries from the editor
    build_area = editor.getBuildArea()
    build_rect = build_area.toRect()
    
    # Load a slice of the world to get height data
    world_slice = editor.loadWorldSlice(build_rect)
    # Get the height map excluding trees and leaves
    heights = world_slice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    
    best_variance = float('inf')  # Initialize with infinity to find minimum variance
    best_pos = None
    
    # Search through the build area in steps of 2 blocks
    for x in range(build_rect.begin.x, build_rect.end.x - width, 2):
        for z in range(build_rect.begin.z, build_rect.end.z - length, 2):
            # Get heights at each corner of potential building location
            corner_heights = [
                heights[(x - build_rect.begin.x, z - build_rect.begin.z)],  # Front-left corner
                heights[(x - build_rect.begin.x + width, z - build_rect.begin.z)],  # Front-right corner
                heights[(x - build_rect.begin.x, z - build_rect.begin.z + length)],  # Back-left corner
                heights[(x - build_rect.begin.x + width, z - build_rect.begin.z + length)]  # Back-right corner
            ]
            
            # Calculate max height difference between corners
            variance = max(corner_heights) - min(corner_heights)
            # Update if this is the flattest area found so far
            if variance < best_variance:
                best_variance = variance
                best_pos = (x, min(corner_heights), z)
    
    return best_pos

def build_foundation(editor, x, y, z, width, length):
    """Build a solid foundation down to ground level."""
    # Build foundation pillars at each position
    for dx in range(width):
        for dz in range(length):
            # Start from current height and build down until solid ground
            for dy in range(y - 10, y):
                block = editor.getBlock((x + dx, dy, z + dz))
                if block.id != "minecraft:air":
                    break
                editor.placeBlock((x + dx, dy, z + dz), Block("stone_bricks"))

def build_cottage(editor):
    """Build a cozy cottage with random dimensions."""
    # Generate random dimensions for the cottage
    width = random.randint(8, 12)
    length = random.randint(10, 14)
    wall_height = random.randint(4, 5)
    
    # Find suitable flat location for building
    pos = find_flat_area(editor, width, length)
    if not pos:  # If no suitable location found
        editor.placeBlock((0, 100, 0), Block("red_concrete"))  # Place error marker
        return
    
    x, y, z = pos
    
    # Build the foundation first
    build_foundation(editor, x, y, z, width, length)
    
    # Create checkered floor pattern with white and yellow wool
    for dx in range(width):
        for dz in range(length):
            color = (dx + dz) % 2  # Alternate colors based on position
            wool_color = 0 if color == 0 else 4  # 0=white, 4=yellow
            editor.placeBlock((x + dx, y, z + dz), Block("wool", {"color": wool_color}))
    
    # Build the walls
    wall_material = Block("oak_planks")
    for dy in range(wall_height):
        for dx in range(width):
            for dz in range(length):
                # Leave space for door
                if dy < 2 and dx == width//2 and dz == 0:
                    continue
                # Only build walls around perimeter
                if dx in [0, width-1] or dz in [0, length-1]:
                    editor.placeBlock((x + dx, y + dy + 1, z + dz), wall_material)
    
    # Add main door (two blocks tall)
    editor.placeBlock((x + width//2, y + 1, z), Block("oak_door", {"half": "lower"}))
    editor.placeBlock((x + width//2, y + 2, z), Block("oak_door", {"half": "upper"}))
    
    # Add windows around the cottage
    window_positions = [
        (2, 0), (width-3, 0),  # Front windows
        (2, length-1), (width-3, length-1),  # Back windows
        (0, length//2), (width-1, length//2)  # Side windows
    ]
    
    # Place glass panes for each window (2 blocks tall)
    for wx, wz in window_positions:
        editor.placeBlock((x + wx, y + 2, z + wz), Block("glass_pane"))
        editor.placeBlock((x + wx, y + 3, z + wz), Block("glass_pane"))
    
    # Build pitched roof using stairs
    roof_material = Block("dark_oak_stairs")
    for dx in range(-1, width + 1):
        for dy in range((width + 2) // 2):
            # Front slope of roof
            if 0 <= dx < width:
                editor.placeBlock(
                    (x + dx, y + wall_height + dy + 1, z - dy),
                    roof_material.with_data({"facing": "south"})
                )
            # Back slope of roof
            if 0 <= dx < width:
                editor.placeBlock(
                    (x + dx, y + wall_height + dy + 1, z + length + dy - 1),
                    roof_material.with_data({"facing": "north"})
                )

def main():
    # Initialize editor with buffering for better performance
    editor = Editor(buffering=True)
    
    # Build the cottage
    build_cottage(editor)
    editor.flushBuffer()  # Make sure all blocks are placed
    
    print("Cottage built!")

if __name__ == "__main__":
    main()
