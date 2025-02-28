#!/usr/bin/env python3

import logging
from random import randint, choice, random
from termcolor import colored
from gdpc import Block, Editor
from gdpc import geometry as geo
import math

# Set up logging and editor
logging.basicConfig(format=colored("%(name)s - %(levelname)s - %(message)s", color="yellow"))
ED = Editor(buffering=True)
BUILD_AREA = ED.getBuildArea()
STARTX, STARTY, STARTZ = BUILD_AREA.begin
LASTX, LASTY, LASTZ = BUILD_AREA.last
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)

# Enhanced materials palette with theme options
THEMES = {
    "rustic": {
        "foundation": ["cobblestone", "mossy_cobblestone", "stone_bricks"],
        "floor": ["spruce_planks", "dark_oak_planks"],
        "walls": ["spruce_planks", "stripped_spruce_log"],
        "trim": ["dark_oak_log", "spruce_log"],
        "roof": ["dark_oak_stairs", "spruce_stairs"],
        "accent": ["cobblestone", "mossy_cobblestone"],
        "details": ["lantern", "spruce_fence", "spruce_trapdoor"],
        "windows": ["glass_pane"]
    },
    "cottage": {
        "foundation": ["cobblestone", "stone_bricks", "mossy_stone_bricks"],
        "floor": ["oak_planks", "birch_planks"],
        "walls": ["white_terracotta", "light_gray_terracotta"],
        "trim": ["oak_log", "stripped_oak_log"],
        "roof": ["dark_oak_stairs", "spruce_stairs"],
        "accent": ["brick", "flower_pot", "oak_leaves"],
        "details": ["lantern", "oak_fence", "oak_trapdoor"],
        "windows": ["glass_pane"]
    },
    "medieval": {
        "foundation": ["stone_bricks", "mossy_stone_bricks", "cracked_stone_bricks"],
        "floor": ["oak_planks", "dark_oak_planks"],
        "walls": ["stripped_oak_log", "oak_planks", "white_wool"],
        "trim": ["dark_oak_log", "spruce_log"],
        "roof": ["dark_oak_stairs", "brick_stairs"],
        "accent": ["stone_bricks", "mossy_stone_bricks"],
        "details": ["lantern", "dark_oak_fence", "oak_trapdoor"],
        "windows": ["glass_pane"]
    },
    "nordic": {
        "foundation": ["spruce_planks", "stone_bricks", "andesite"],
        "floor": ["spruce_planks", "dark_oak_planks"],
        "walls": ["spruce_planks", "spruce_log"],
        "trim": ["spruce_log", "stripped_spruce_log"],
        "roof": ["spruce_stairs", "stone_stairs"],
        "accent": ["cobblestone", "andesite"],
        "details": ["lantern", "spruce_fence", "spruce_trapdoor"],
        "windows": ["glass_pane"]
    }
}

def get_random_block(block_list):
    """Select a random block from the provided list"""
    return Block(choice(block_list))

def get_weighted_random(block_list, primary_weight=0.7):
    """Get a block with weighting to prefer the primary option"""
    if random() < primary_weight:
        return Block(block_list[0])
    return Block(choice(block_list[1:]))

def create_terrain_adjustment_map(heights, xaxis, zaxis, width, length, target_y, STARTX, STARTZ):
    """Create a map of terrain adjustments needed"""
    adjustments = {}
    for dx in range(-width//2 - 3, width//2 + 4):
        for dz in range(-length//2 - 3, length//2 + 4):
            x, z = xaxis + dx, zaxis + dz
            if 0 <= x - STARTX < len(heights) and 0 <= z - STARTZ < len(heights[0]):
                current_height = heights[(x - STARTX, z - STARTZ)]
                adjustments[(x, z)] = target_y - current_height
    return adjustments

def create_garden(ED, xaxis, zaxis, y, width, length, theme_materials, adjustments):
    """Create a garden around the house"""
    print("Creating garden...")
    garden_radius = max(width, length) + 5
    
    # Add garden path from main door to edge
    path_length = garden_radius // 2
    path_width = 2
    
    # Determine door position (assumed to be at front center)
    door_x = xaxis - width//2
    door_z = zaxis
    
    # Create curved path
    for i in range(path_length):
        curve_factor = math.sin(i / path_length * math.pi) * 2
        center_x = door_x - i - 1
        for j in range(-path_width, path_width + 1):
            pz = door_z + int(curve_factor * j / path_width)
            if (center_x, pz) in adjustments:
                ED.placeBlock((center_x, y - 1, pz), get_random_block(["gravel", "cobblestone", "stone"]))
                
                # Add some flowers alongside path
                if abs(j) == path_width and random() < 0.4:
                    flowers = ["poppy", "dandelion", "blue_orchid", "allium", "azure_bluet"]
                    if (center_x, pz + j//abs(j)) in adjustments:
                        ED.placeBlock((center_x, y, pz + j//abs(j)), Block(choice(flowers)))
    
    # Add garden features
    for dx in range(-garden_radius, garden_radius + 1):
        for dz in range(-garden_radius, garden_radius + 1):
            x, z = xaxis + dx, zaxis + dz
            
            # Skip if inside house
            if -width//2 - 1 <= dx <= width//2 + 1 and -length//2 - 1 <= dz <= length//2 + 1:
                continue
                
            # Calculate distance from house for circular garden
            dist_from_house = max(
                abs(dx) - width//2,
                abs(dz) - length//2
            )
            
            if dist_from_house <= 10 and (x, z) in adjustments:
                # Grass base everywhere in garden
                if adjustments[(x, z)] <= 0:
                    ED.placeBlock((x, y - 1, z), Block("grass_block"))
                    
                    # Add features 
                    feature_chance = random()
                    if feature_chance < 0.03:  # Flowers
                        flowers = ["poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", 
                                  "orange_tulip", "red_tulip", "white_tulip", "pink_tulip"]
                        ED.placeBlock((x, y, z), Block(choice(flowers)))
                    elif feature_chance < 0.05:  # Bushes
                        ED.placeBlock((x, y, z), Block("oak_leaves"))
                    elif feature_chance < 0.06:  # Trees
                        if dist_from_house > 3:
                            tree_height = randint(4, 6)
                            for ty in range(tree_height):
                                ED.placeBlock((x, y + ty, z), Block("oak_log"))
                            # Canopy
                            for cx in range(-2, 3):
                                for cz in range(-2, 3):
                                    for cy in range(2):
                                        if abs(cx) == 2 and abs(cz) == 2:
                                            continue
                                        ED.placeBlock((x + cx, y + tree_height - 1 + cy, z + cz), Block("oak_leaves"))
                    elif feature_chance < 0.07:  # Garden decoration
                        deco_options = ["composter", "beehive", "barrel", "lantern"]
                        ED.placeBlock((x, y, z), Block(choice(deco_options)))
                    elif feature_chance < 0.08 and dist_from_house > 5:  # Pond
                        for px in range(-1, 2):
                            for pz in range(-1, 2):
                                if (x + px, z + pz) in adjustments:
                                    ED.placeBlock((x + px, y - 1, z + pz), Block("dirt"))
                                    ED.placeBlock((x + px, y, z + pz), Block("water"))
                                    
                                    # Add lilypads
                                    if px == 0 and pz == 0 and random() < 0.5:
                                        ED.placeBlock((x, y + 1, z), Block("lily_pad"))

def clear_space(ED, xaxis, zaxis, y, width, length, height, roof_style="pitched"):
    """Clear the space for the house"""
    print("Clearing interior space...")
    
    # Clear main room
    geo.placeCuboid(
        ED,
        (xaxis - width//2 + 1, y, zaxis - length//2 + 1),
        (xaxis + width//2 - 1, y + height - 1, zaxis + length//2 - 1),
        Block("air")
    )
    
    # Clear roof space based on style
    if roof_style == "pitched":
        for i in range(width//2 + 3):
            roof_height = min(i, width//2 + 2)
            geo.placeCuboid(
                ED,
                (xaxis - width//2 + i, y + height - 1, zaxis - length//2),
                (xaxis + width//2 - i, y + height + roof_height - 1, zaxis + length//2),
                Block("air")
            )
    elif roof_style == "dome":
        radius = width // 2
        for dx in range(-radius, radius + 1):
            for dy in range(0, radius + 1):
                for dz in range(-length//2, length//2 + 1):
                    if dx**2 + dy**2 <= radius**2:
                        ED.placeBlock((xaxis + dx, y + height + dy, zaxis + dz), Block("air"))

def build_foundation(ED, xaxis, zaxis, y, width, length, theme_materials, adjustments):
    """Build the house foundation with enhanced terrain adaptation"""
    print("Building foundation...")
    
    # Find the lowest terrain point
    min_height = y
    for dx in range(-width//2 - 1, width//2 + 2):
        for dz in range(-length//2 - 1, length//2 + 2):
            pos = (xaxis + dx, zaxis + dz)
            if pos in adjustments and adjustments[pos] > 0:
                current_height = y - adjustments[pos]
                min_height = min(min_height, current_height)
    
    # Base foundation with variable height pillars where needed
    for dx in range(-width//2 - 1, width//2 + 2):
        for dz in range(-length//2 - 1, length//2 + 2):
            pos = (xaxis + dx, zaxis + dz)
            if pos in adjustments:
                if adjustments[pos] > 0:
                    # Need to build up to level
                    current_height = y - adjustments[pos]
                    
                    # Determine if this is a corner pillar or edge
                    is_corner = (abs(dx) == width//2 + 1 and abs(dz) == length//2 + 1)
                    is_edge = (abs(dx) == width//2 + 1 or abs(dz) == length//2 + 1)
                    
                    material = get_random_block(theme_materials["foundation"])
                    
                    # Create foundation pillar
                    geo.placeCuboid(
                        ED,
                        (xaxis + dx, current_height, zaxis + dz),
                        (xaxis + dx, y - 1, zaxis + dz),
                        material
                    )
                    
                    # Add decorative elements to tall pillars
                    if is_corner and y - current_height > 3:
                        # Add wall section with different material
                        middle_y = current_height + (y - current_height) // 2
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, middle_y - 1, zaxis + dz),
                            (xaxis + dx, middle_y + 1, zaxis + dz),
                            Block(theme_materials["accent"][0])
                        )
                    
                    # Add supportive beams for very tall sections
                    if y - current_height > 5 and is_edge and not is_corner:
                        # Find nearest corners
                        corner_dx = width//2 + 1 if dx > 0 else -(width//2 + 1)
                        corner_dz = length//2 + 1 if dz > 0 else -(length//2 + 1)
                        
                        # Add support beam from pillar to nearby corners if on edge
                        if abs(dx) == width//2 + 1:
                            ED.placeBlock((xaxis + dx, current_height + 1, zaxis + dz), 
                                         Block("dark_oak_log", {"axis": "z"}))
                        elif abs(dz) == length//2 + 1:
                            ED.placeBlock((xaxis + dx, current_height + 1, zaxis + dz), 
                                         Block("dark_oak_log", {"axis": "x"}))
    
    # Main foundation platform
    for dx in range(-width//2 - 1, width//2 + 2):
        for dz in range(-length//2 - 1, length//2 + 2):
            # Mix materials to create interesting pattern
            if (dx + dz) % 3 == 0:
                material = get_random_block(theme_materials["foundation"])
            else:
                material = get_weighted_random(theme_materials["foundation"])
            
            ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), material)

def build_floor(ED, xaxis, zaxis, y, width, length, theme_materials):
    """Build the floor with complex patterns"""
    print("Adding floor...")
    floor_materials = theme_materials["floor"]
    
    # Determine the pattern type
    pattern_type = choice(["checkered", "herringbone", "bordered", "random"])
    
    if pattern_type == "checkered":
        # Simple checkerboard pattern
        for dx in range(-width//2 + 1, width//2):
            for dz in range(-length//2 + 1, length//2):
                if (dx + dz) % 2 == 0:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[0]))
                else:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[1]))
    
    elif pattern_type == "herringbone":
        # Herringbone pattern using blocks with directional textures
        for dx in range(-width//2 + 1, width//2):
            for dz in range(-length//2 + 1, length//2):
                if (dx + dz) % 2 == 0:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), 
                                 Block(floor_materials[0], {"axis": "x"}))
                else:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), 
                                 Block(floor_materials[0], {"axis": "z"}))
    
    elif pattern_type == "bordered":
        # Border with different material in center
        for dx in range(-width//2 + 1, width//2):
            for dz in range(-length//2 + 1, length//2):
                if (abs(dx) >= width//2 - 2 or abs(dz) >= length//2 - 2):
                    # Border
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[0]))
                else:
                    # Center
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[1]))
                    
        # Add corner accents
        for dx in [-width//2 + 2, width//2 - 2]:
            for dz in [-length//2 + 2, length//2 - 2]:
                ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), 
                             Block(choice(theme_materials["accent"])))
    
    else:  # random
        # Random mix of materials for a natural worn look
        for dx in range(-width//2 + 1, width//2):
            for dz in range(-length//2 + 1, length//2):
                if random() < 0.2:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[1]))
                else:
                    ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(floor_materials[0]))

def build_walls(ED, xaxis, zaxis, y, width, length, height, theme_materials):
    """Build walls with more sophisticated design"""
    print("Building walls...")
    wall_materials = theme_materials["walls"]
    trim_materials = theme_materials["trim"]
    
    # Frame construction with corner pillars
    for dx in [-width//2, width//2]:
        for dz in [-length//2, length//2]:
            geo.placeCuboid(
                ED,
                (xaxis + dx, y - 1, zaxis + dz),
                (xaxis + dx, y + height, zaxis + dz),
                Block(trim_materials[0], {"axis": "y"})
            )
    
    # Horizontal beams at top and middle
    for h in [0, height // 2, height]:
        for x in range(-width//2, width//2 + 1):
            ED.placeBlock((xaxis + x, y + h, zaxis - length//2), 
                         Block(trim_materials[0], {"axis": "x"}))
            ED.placeBlock((xaxis + x, y + h, zaxis + length//2), 
                         Block(trim_materials[0], {"axis": "x"}))
            
        for z in range(-length//2, length//2 + 1):
            ED.placeBlock((xaxis - width//2, y + h, zaxis + z), 
                         Block(trim_materials[0], {"axis": "z"}))
            ED.placeBlock((xaxis + width//2, y + h, zaxis + z), 
                         Block(trim_materials[0], {"axis": "z"}))
    
    # Vertical beams
    for x in range(-width//2 + 3, width//2, 3):
        geo.placeCuboid(
            ED,
            (xaxis + x, y, zaxis - length//2),
            (xaxis + x, y + height, zaxis - length//2),
            Block(trim_materials[1], {"axis": "y"})
        )
        geo.placeCuboid(
            ED,
            (xaxis + x, y, zaxis + length//2),
            (xaxis + x, y + height, zaxis + length//2),
            Block(trim_materials[1], {"axis": "y"})
        )
    
    for z in range(-length//2 + 3, length//2, 3):
        geo.placeCuboid(
            ED,
            (xaxis - width//2, y, zaxis + z),
            (xaxis - width//2, y + height, zaxis + z),
            Block(trim_materials[1], {"axis": "y"})
        )
        geo.placeCuboid(
            ED,
            (xaxis + width//2, y, zaxis + z),
            (xaxis + width//2, y + height, zaxis + z),
            Block(trim_materials[1], {"axis": "y"})
        )
    
    # Fill walls between the frame
    for h in range(height):
        for x in range(-width//2, width//2 + 1):
            for z in [-length//2, length//2]:
                # Skip if it's a beam position
                if (h == 0 or h == height // 2 or h == height) or \
                   (x == -width//2 or x == width//2) or \
                   (x % 3 == 0 and x != 0):
                    continue
                
                # Choose wall material
                if (x % 4 == 0 and h % 3 == 0) or (z % 4 == 0 and h % 3 == 0):
                    # Add some pattern/texture variation
                    material = Block(choice(theme_materials["accent"]))
                else:
                    material = get_random_block(wall_materials)
                
                ED.placeBlock((xaxis + x, y + h, zaxis + z), material)
        
        for z in range(-length//2, length//2 + 1):
            for x in [-width//2, width//2]:
                # Skip if it's a beam position
                if (h == 0 or h == height // 2 or h == height) or \
                   (z == -length//2 or z == length//2) or \
                   (z % 3 == 0 and z != 0):
                    continue
                
                # Choose wall material
                if (z % 4 == 0 and h % 3 == 0) or (x % 4 == 0 and h % 3 == 0):
                    # Add some pattern/texture variation
                    material = Block(choice(theme_materials["accent"]))
                else:
                    material = get_random_block(wall_materials)
                
                ED.placeBlock((xaxis + x, y + h, zaxis + z), material)

def build_roof(ED, xaxis, zaxis, y, width, length, height, theme_materials, style="pitched"):
    """Build a more complex roof"""
    print(f"Building {style} roof...")
    
    # Get trim materials from theme_materials
    trim_materials = theme_materials["trim"]
    
    if style == "pitched":
        # Advanced pitched roof with eaves
        eaves_extension = 1
        
        # Extended base for eaves
        for dx in range(-width//2 - eaves_extension, width//2 + eaves_extension + 1):
            for dz in range(-length//2 - eaves_extension, length//2 + eaves_extension + 1):
                # Skip if it's the actual open interior
                if -width//2 < dx < width//2 and -length//2 < dz < length//2:
                    continue
                
                # Base of eaves
                ED.placeBlock(
                    (xaxis + dx, y + height - 1, zaxis + dz),
                    Block(trim_materials[0], {"axis": "y"})
                )
        
        # Roof slopes with eaves
        max_height = width//2 + 2
        for i in range(max_height + 1):
            # Determine current y level
            current_y = y + height - 1 + i
            current_width = width - (i * 2) + (eaves_extension * 2)
            
            # Across the length of the house (long horizontal direction)
            for dz in range(-length//2 - eaves_extension, length//2 + eaves_extension + 1):
                if i == max_height:  # Center ridge beam
                    ED.placeBlock(
                        (xaxis, current_y, zaxis + dz),
                        get_random_block(theme_materials["accent"])
                    )
                else:
                    # West-facing side (negative x)
                    west_dx = -width//2 + i - eaves_extension
                    ED.placeBlock(
                        (xaxis + west_dx, current_y, zaxis + dz),
                        Block(theme_materials["roof"][0], {"facing": "east"})
                    )
                    
                    # East-facing side (positive x)
                    east_dx = width//2 - i + eaves_extension
                    ED.placeBlock(
                        (xaxis + east_dx, current_y, zaxis + dz),
                        Block(theme_materials["roof"][0], {"facing": "west"})
                    )
                    
                    # Fill the inside with solid blocks
                    for fill_dx in range(west_dx + 1, east_dx):
                        if i > 0:  # Only fill interior for non-ground level
                            ED.placeBlock(
                                (xaxis + fill_dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )
            
        # Add decorative gables at the front and back
        for z in [-length//2 - eaves_extension, length//2 + eaves_extension]:
            for i in range(max_height):
                current_y = y + height - 1 + i
                
                # Draw a triangular pattern
                for dx in range(-width//2 - eaves_extension + i, width//2 + eaves_extension + 1 - i):
                    # Use different materials for added detail
                    if i == 0 or i == max_height - 1 or dx == -width//2 - eaves_extension + i or dx == width//2 + eaves_extension - i:
                        # Frame
                        material = get_random_block(theme_materials["trim"])
                    else:
                        # Fill
                        material = get_random_block(theme_materials["walls"])
                    
                    ED.placeBlock((xaxis + dx, current_y, zaxis + z), material)
        
        # Add decorative chimney
        chimney_x = xaxis + width//2 - 2
        chimney_z = zaxis + length//3
        chimney_height = max_height + 2
        
        for h in range(chimney_height):
            ED.placeBlock(
                (chimney_x, y + height + h, chimney_z),
                get_random_block(theme_materials["accent"])
            )
        
        # Chimney top
        ED.placeBlock(
            (chimney_x, y + height + chimney_height, chimney_z),
            Block("campfire", {"lit": "true"})
        )
        
        # Surround chimney top with decorative blocks
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue
                ED.placeBlock(
                    (chimney_x + dx, y + height + chimney_height - 1, chimney_z + dz),
                    Block("cobblestone_wall")
                )
    
    elif style == "dome":
        # Create a dome roof
        roof_height = width // 2
        radius = width // 2 + 1
        
        for dy in range(roof_height + 1):
            circle_radius = int(math.sqrt(radius**2 - dy**2))
            for dx in range(-circle_radius, circle_radius + 1):
                for dz in range(-length//2, length//2 + 1):
                    # Only place blocks for the dome surface
                    if int(math.sqrt(dx**2 + ((dz/2)**2))) == circle_radius:
                        ED.placeBlock(
                            (xaxis + dx, y + height + dy, zaxis + dz),
                            get_random_block(theme_materials["accent"])
                        )

def add_windows(ED, xaxis, zaxis, y, width, length, height, theme_materials):
    """Add detailed windows to the house"""
    print("Adding windows...")
    
    # Windows with decorative frames
    window_positions = [
        # Side windows
        (xaxis + width//2, zaxis - length//3), (xaxis + width//2, zaxis), (xaxis + width//2, zaxis + length//3),
        (xaxis - width//2, zaxis - length//3), (xaxis - width//2, zaxis), (xaxis - width//2, zaxis + length//3),
        
        # Front and back windows
        (xaxis - width//3, zaxis + length//2), (xaxis + width//3, zaxis + length//2),
        (xaxis - width//3, zaxis - length//2), (xaxis + width//3, zaxis - length//2)
    ]
    
    for wx, wz in window_positions:
        # Determine window orientation
        is_side = (wx == xaxis + width//2 or wx == xaxis - width//2)
        
        # Set the facing direction for decorative blocks
        if wx == xaxis + width//2:
            facing = "west"
        elif wx == xaxis - width//2:
            facing = "east"
        elif wz == zaxis + length//2:
            facing = "north"
        else:
            facing = "south"
            
        # First, create the window frame
        frame_material = Block(theme_materials["trim"][1])
        
        # Create window shape based on style
        window_style = choice(["tall", "wide", "arched", "square"])
        
        if window_style == "tall":
            # Tall window
            window_height = 3
            window_width = 1
            
            start_y = y + 1
            
            # Build the window frame
            for dy in range(-1, window_height + 1):
                for dx in range(-1, window_width + 1):
                    # Determine position based on orientation
                    if is_side:
                        pos = (wx, start_y + dy, wz + dx)
                    else:
                        pos = (wx + dx, start_y + dy, wz)
                    
                    # If it's the frame edge, place frame material
                    if dy == -1 or dy == window_height or dx == -1 or dx == window_width:
                        ED.placeBlock(pos, frame_material)
                    else:
                        # Inside the frame, place the glass
                        ED.placeBlock(pos, Block(theme_materials["windows"][0]))
                
            # Add window decoration
            if is_side:
                # Add flower box
                ED.placeBlock((wx, start_y - 1, wz), 
                             Block("spruce_trapdoor", {"facing": facing, "half": "top"}))
                # Add a flower
                ED.placeBlock((wx - (1 if facing == "east" else -1), start_y - 1, wz), 
                             Block("potted_red_tulip"))
            else:
                # Add awning
                ED.placeBlock((wx, start_y + window_height, wz - (1 if facing == "south" else -1)), 
                             Block("spruce_trapdoor", {"facing": facing, "half": "top"}))
        
        elif window_style == "wide":
            # Wide window
            window_height = 2
            window_width = 2
            
            start_y = y + 1
            
            # Build the window frame
            for dy in range(-1, window_height + 1):
                for dx in range(-1, window_width + 1):
                    # Determine position based on orientation
                    if is_side:
                        pos = (wx, start_y + dy, wz + dx)
                    else:
                        pos = (wx + dx, start_y + dy, wz)
                    
                    # If it's the frame edge or center divider, place frame material
                    if dy == -1 or dy == window_height or dx == -1 or dx == window_width:
                        ED.placeBlock(pos, frame_material)
                    else:
                        # Inside the frame, place the glass
                        ED.placeBlock(pos, Block(theme_materials["windows"][0]))
            
            # Add decorations
            if is_side:
                # Add shutters
                ED.placeBlock((wx, start_y, wz - 1), 
                             Block("spruce_trapdoor", {"facing": "north", "open": "true"}))
                ED.placeBlock((wx, start_y, wz + window_width + 1), 
                             Block("spruce_trapdoor", {"facing": "south", "open": "true"}))
            else:
                # Add shutters
                ED.placeBlock((wx - 1, start_y, wz), 
                             Block("spruce_trapdoor", {"facing": "west", "open": "true"}))
                ED.placeBlock((wx + window_width + 1, start_y, wz), 
                             Block("spruce_trapdoor", {"facing": "east", "open": "true"}))
        
        elif window_style == "arched":
            # Arched window
            window_height = 3
            window_width = 1
            
            start_y = y + 1
            
            # Build the window frame
            for dy in range(window_height + 1):
                for dx in range(-1, window_width + 1):
                    # Determine position based on orientation
                    if is_side:
                        pos = (wx, start_y + dy, wz + dx)
                    else:
                        pos = (wx + dx, start_y + dy, wz)
                    
                    # If it's the frame edge or top arch, place frame material
                    if dx == -1 or dx == window_width or (dy == window_height and dx >= 0 and dx < window_width):
                        ED.placeBlock(pos, frame_material)
                    elif dy < window_height:
                        # Inside the frame, place the glass
                        ED.placeBlock(pos, Block(theme_materials["windows"][0]))
            
            # Add decorative stained glass on top
            if is_side:
                ED.placeBlock((wx, start_y + window_height - 1, wz), Block("yellow_stained_glass"))
            else:
                ED.placeBlock((wx, start_y + window_height - 1, wz), Block("yellow_stained_glass"))
        
        else:  # square
            # Square window
            window_size = 1
            
            start_y = y + 1
            
            # Build the window frame
            for dy in range(window_size):
                for dx in range(window_size):
                    # Determine position based on orientation
                    if is_side:
                        ED.placeBlock((wx, start_y + dy, wz + dx), Block(theme_materials["windows"][0]))
                    else:
                        ED.placeBlock((wx + dx, start_y + dy, wz), Block(theme_materials["windows"][0]))
                        
            # Simple wood frame
            if is_side:
                for dx in range(-1, window_size + 1):
                    ED.placeBlock((wx, start_y - 1, wz + dx), frame_material)
                    ED.placeBlock((wx, start_y + window_size, wz + dx), frame_material)
                
                ED.placeBlock((wx, start_y, wz - 1), frame_material)
                ED.placeBlock((wx, start_y, wz + window_size), frame_material)
            else:
                for dx in range(-1, window_size + 1):
                    ED.placeBlock((wx + dx, start_y - 1, wz), frame_material)
                    ED.placeBlock((wx + dx, start_y + window_size, wz), frame_material)
                
                ED.placeBlock((wx - 1, start_y, wz), frame_material)
                ED.placeBlock((wx + window_size, start_y, wz), frame_material)

def add_door(ED, xaxis, zaxis, y, width, length, theme_materials):
    """Add a detailed door with porch area"""
    print("Adding door...")
    
    # Position door at center of one of the edges
    door_x = xaxis - width//2
    door_z = zaxis
    
    # Door material based on theme
    door_material = "spruce_door"
    
    # Create door frame
    ED.placeBlock((door_x, y, door_z), Block(door_material, {"facing": "east", "half": "lower"}))
    ED.placeBlock((door_x, y + 1, door_z), Block(door_material, {"facing": "east", "half": "upper"}))
    
    # Add framing around door
    for dy in range(3):
        ED.placeBlock((door_x, y + dy, door_z - 1), Block(theme_materials["trim"][1]))
        ED.placeBlock((door_x, y + dy, door_z + 1), Block(theme_materials["trim"][1]))
    
    # Top of door frame
    ED.placeBlock((door_x, y + 2, door_z), Block(theme_materials["trim"][1], {"axis": "z"}))
    
    # Add porch area
    porch_width = 5
    porch_depth = 3
    
    # Porch floor
    for dx in range(1, porch_depth + 1):
        for dz in range(-porch_width//2, porch_width//2 + 1):
            ED.placeBlock(
                (door_x - dx, y - 1, door_z + dz),
                get_random_block(theme_materials["floor"])
            )
    
    # Porch steps
    for dx in range(1, 3):
        for dz in range(-porch_width//2 + 1, porch_width//2):
            ED.placeBlock(
                (door_x - porch_depth - dx, y - dx, door_z + dz),
                Block("spruce_stairs", {"facing": "east"})
            )
    
    # Porch railings
    for dz in range(-porch_width//2, porch_width//2 + 1):
        if dz != 0:  # Skip the entrance
            ED.placeBlock((door_x - porch_depth, y, door_z + dz), Block("spruce_fence"))
            
    for dx in range(-porch_depth, 0):
        ED.placeBlock((door_x + dx, y, door_z - porch_width//2), Block("spruce_fence"))
        ED.placeBlock((door_x + dx, y, door_z + porch_width//2), Block("spruce_fence"))
    
    # Porch roof
    for dx in range(1, porch_depth + 1):
        for dz in range(-porch_width//2 - 1, porch_width//2 + 2):
            ED.placeBlock(
                (door_x - dx, y + 3, door_z + dz),
                get_random_block(theme_materials["floor"])
            )
    
    # Porch support pillars
    for dz in [-porch_width//2, porch_width//2]:
        geo.placeCuboid(
            ED,
            (door_x - porch_depth, y, door_z + dz),
            (door_x - porch_depth, y + 2, door_z + dz),
            Block(theme_materials["trim"][0])
        )
    
    # Add decorative items to porch
    # Lanterns on pillars
    ED.placeBlock((door_x - porch_depth, y + 2, door_z - porch_width//2), Block("lantern"))
    ED.placeBlock((door_x - porch_depth, y + 2, door_z + porch_width//2), Block("lantern"))
    
    # Add a welcome mat
    ED.placeBlock((door_x - 1, y - 1, door_z), Block("brown_carpet"))
    
    # Add a bench on the porch
    ED.placeBlock((door_x - 2, y, door_z - porch_width//2 + 1), Block("spruce_stairs", {"facing": "south"}))
    ED.placeBlock((door_x - 2, y, door_z - porch_width//2 + 2), Block("spruce_stairs", {"facing": "north"}))

def add_interior_details(ED, xaxis, zaxis, y, width, length, height, theme_materials):
    """Add detailed interior decorations"""
    print("Adding interior details...")
    
    # Create interior walls to divide the space
    interior_wall_layout = choice(["open", "divided", "rooms"])
    
    if interior_wall_layout == "open":
        # Open floor plan - just add details
        pass
    
    elif interior_wall_layout == "divided":
        # Add a central dividing wall
        for dz in range(-length//2 + 2, length//2 - 1):
            for dy in range(height - 1):
                # Leave a doorway
                if dz == 0:
                    if dy < 2:
                        continue
                ED.placeBlock((xaxis, y + dy, zaxis + dz), get_random_block(theme_materials["walls"]))
    
    elif interior_wall_layout == "rooms":
        # Create multiple room divisions
        
        # Main hall divider
        for dx in range(-width//2 + 3, width//2 - 2):
            for dy in range(height - 1):
                # Leave doorways
                if dx == 0 or dx == -(width//4):
                    if dy < 2:
                        continue
                ED.placeBlock((xaxis + dx, y + dy, zaxis), get_random_block(theme_materials["walls"]))
        
        # Side room dividers
        for dz in range(1, length//2 - 1):
            for dy in range(height - 1):
                if dy < 2 and dz == length//4:
                    continue
                ED.placeBlock((xaxis - width//4, y + dy, zaxis + dz), get_random_block(theme_materials["walls"]))
                
        for dz in range(-length//2 + 2, 0):
            for dy in range(height - 1):
                if dy < 2 and dz == -length//4:
                    continue
                ED.placeBlock((xaxis + width//4, y + dy, zaxis + dz), get_random_block(theme_materials["walls"]))
    
    # Add a fireplace
    fireplace_x = xaxis + width//2 - 1
    fireplace_z = zaxis
    
    # Fireplace base
    for dz in range(-1, 2):
        ED.placeBlock((fireplace_x, y - 1, zaxis + dz), Block("cobblestone"))
        geo.placeCuboid(
            ED,
            (fireplace_x, y, zaxis + dz),
            (fireplace_x, y + 2, zaxis + dz),
            Block("cobblestone")
        )
    
    # Fireplace opening and fire
    ED.placeBlock((fireplace_x, y, zaxis), Block("air"))
    ED.placeBlock((fireplace_x, y + 1, zaxis), Block("air"))
    ED.placeBlock((fireplace_x, y, zaxis), Block("campfire", {"lit": "true"}))
    
    # Chimney mantel
    ED.placeBlock((fireplace_x, y + 2, zaxis - 1), Block("spruce_stairs", {"facing": "south"}))
    ED.placeBlock((fireplace_x, y + 2, zaxis + 1), Block("spruce_stairs", {"facing": "north"}))
    ED.placeBlock((fireplace_x, y + 2, zaxis), Block("spruce_planks"))
    
    # Add some decorative items on the mantel
    ED.placeBlock((fireplace_x - 1, y + 3, zaxis - 1), Block("flower_pot"))
    ED.placeBlock((fireplace_x - 1, y + 3, zaxis + 1), Block("lantern"))
    
    # Add living area with seating around fireplace
    ED.placeBlock((fireplace_x - 2, y, zaxis - 2), Block("spruce_stairs", {"facing": "south"}))
    ED.placeBlock((fireplace_x - 2, y, zaxis - 3), Block("spruce_stairs", {"facing": "east"}))
    ED.placeBlock((fireplace_x - 3, y, zaxis - 3), Block("spruce_stairs", {"facing": "north"}))
    
    ED.placeBlock((fireplace_x - 2, y, zaxis + 2), Block("spruce_stairs", {"facing": "north"}))
    ED.placeBlock((fireplace_x - 2, y, zaxis + 3), Block("spruce_stairs", {"facing": "east"}))
    ED.placeBlock((fireplace_x - 3, y, zaxis + 3), Block("spruce_stairs", {"facing": "south"}))
    
    # Add a table in the center
    ED.placeBlock((fireplace_x - 4, y, zaxis), Block("spruce_fence"))
    ED.placeBlock((fireplace_x - 4, y + 1, zaxis), Block("spruce_pressure_plate"))
    
    # Add bedroom features
    if interior_wall_layout == "rooms" or interior_wall_layout == "divided":
        # Bed
        bed_x = xaxis - width//2 + 2
        bed_z = zaxis + length//3
        
        ED.placeBlock((bed_x, y, bed_z), Block("red_bed", {"facing": "west", "part": "foot"}))
        ED.placeBlock((bed_x + 1, y, bed_z), Block("red_bed", {"facing": "west", "part": "head"}))
        
        # Nightstand
        ED.placeBlock((bed_x, y, bed_z + 1), Block("spruce_planks"))
        ED.placeBlock((bed_x, y + 1, bed_z + 1), Block("lantern"))
        
        # Chest at foot of bed
        ED.placeBlock((bed_x - 1, y, bed_z), Block("chest", {"facing": "east"}))
        
        # Carpet
        for dx in range(3):
            for dz in range(3):
                ED.placeBlock((bed_x - 1 + dx, y - 1, bed_z - 1 + dz), Block("light_gray_carpet"))
    
    # Add kitchen area
    kitchen_x = xaxis - width//3
    kitchen_z = zaxis - length//3
    
    # Kitchen counter
    for dx in range(3):
        ED.placeBlock((kitchen_x + dx, y, kitchen_z), Block("spruce_stairs", {"facing": "south"}))
    
    # Add cooking items
    ED.placeBlock((kitchen_x, y + 1, kitchen_z), Block("smoker", {"facing": "south"}))
    ED.placeBlock((kitchen_x + 1, y + 1, kitchen_z), Block("crafting_table"))
    ED.placeBlock((kitchen_x + 2, y + 1, kitchen_z), Block("barrel"))
    
    # Kitchen storage
    for dx in range(3):
        ED.placeBlock((kitchen_x + dx, y, kitchen_z - 1), Block("chest", {"facing": "north"}))
    
    # Add a dining area
    table_x = kitchen_x
    table_z = kitchen_z - 3
    
    # Table
    ED.placeBlock((table_x, y, table_z), Block("spruce_fence"))
    ED.placeBlock((table_x, y + 1, table_z), Block("spruce_trapdoor", {"facing": "north", "half": "top"}))
    
    # Chairs
    ED.placeBlock((table_x - 1, y, table_z), Block("spruce_stairs", {"facing": "east"}))
    ED.placeBlock((table_x + 1, y, table_z), Block("spruce_stairs", {"facing": "west"}))
    ED.placeBlock((table_x, y, table_z - 1), Block("spruce_stairs", {"facing": "south"}))
    ED.placeBlock((table_x, y, table_z + 1), Block("spruce_stairs", {"facing": "north"}))
    
    # Add lighting throughout the house
    for dx in range(-width//2 + 3, width//2 - 2, 4):
        for dz in range(-length//2 + 3, length//2 - 2, 4):
            # Skip if too close to fireplace
            if abs(dx - (width//2 - 1)) < 2 and abs(dz) < 2:
                continue
                
            ED.placeBlock((xaxis + dx, y + height - 2, zaxis + dz), Block("lantern", {"hanging": "true"}))
    
    # Add some plants and decorations
    plant_positions = [
        (xaxis - width//2 + 2, zaxis + length//2 - 2),
        (xaxis + width//2 - 2, zaxis - length//2 + 2),
        (xaxis, zaxis + length//2 - 2)
    ]
    
    for px, pz in plant_positions:
        plant_type = choice(["potted_fern", "potted_blue_orchid", "potted_bamboo", "potted_azalea_bush"])
        
        # Create a decorative plant stand
        ED.placeBlock((px, y, pz), Block("spruce_fence"))
        ED.placeBlock((px, y + 1, pz), Block(plant_type))

def create_basement(ED, xaxis, zaxis, y, width, length, theme_materials):
    """Add a basement level"""
    print("Creating basement...")
    
    basement_height = 4
    
    # Clear basement space
    geo.placeCuboid(
        ED,
        (xaxis - width//2 + 2, y - basement_height, zaxis - length//2 + 2),
        (xaxis + width//2 - 2, y - 2, zaxis + length//2 - 2),
        Block("air")
    )
    
    # Add basement walls
    for dx in range(-width//2 + 1, width//2):
        for dz in range(-length//2 + 1, length//2):
            for dy in range(-basement_height, -1):
                # Skip floor
                if dy == -basement_height:
                    continue
                
                # Only build the perimeter
                if dx == -width//2 + 1 or dx == width//2 - 1 or dz == -length//2 + 1 or dz == length//2 - 1:
                    ED.placeBlock(
                        (xaxis + dx, y + dy, zaxis + dz),
                        get_random_block(theme_materials["foundation"])
                    )
    
    # Add basement floor
    for dx in range(-width//2 + 2, width//2 - 1):
        for dz in range(-length//2 + 2, length//2 - 1):
            ED.placeBlock(
                (xaxis + dx, y - basement_height, zaxis + dz),
                get_random_block(theme_materials["floor"])
            )
    
    # Add stairs to the basement
    stairs_x = xaxis
    stairs_z = zaxis - length//4
    
    for i in range(1, basement_height):
        ED.placeBlock(
            (stairs_x - i, y - i, stairs_z),
            Block("spruce_stairs", {"facing": "east"})
        )
        
        # Add railings
        ED.placeBlock((stairs_x - i, y - i + 1, stairs_z + 1), Block("spruce_fence"))
        ED.placeBlock((stairs_x - i, y - i + 1, stairs_z - 1), Block("spruce_fence"))
    
    # Add storage area in basement
    for z in range(-length//2 + 3, length//2 - 2, 3):
        ED.placeBlock((xaxis - width//2 + 2, y - basement_height + 1, zaxis + z), Block("chest", {"facing": "east"}))
        ED.placeBlock((xaxis + width//2 - 2, y - basement_height + 1, zaxis + z), Block("barrel"))
    
    # Add basement lighting
    for dx in range(-width//2 + 4, width//2 - 3, 3):
        for dz in range(-length//2 + 4, length//2 - 3, 3):
            ED.placeBlock(
                (xaxis + dx, y - 2, zaxis + dz),
                Block("lantern", {"hanging": "true"})
            )
    
    # Add some themed basement details
    # Wine cellar section
    for dx in range(3):
        ED.placeBlock(
            (xaxis + width//2 - 4 - dx, y - basement_height + 1, zaxis + length//2 - 3),
            Block("barrel", {"facing": "north"})
        )
    
    # Add some cobwebs for atmosphere
    for _ in range(5):
        dx = randint(-width//2 + 2, width//2 - 2)
        dz = randint(-length//2 + 2, length//2 - 2)
        ED.placeBlock((xaxis + dx, y - 2, zaxis + dz), Block("cobweb"))
    
    # Add some ores in the walls to suggest a mine
    ore_types = ["coal_ore", "iron_ore", "gold_ore", "redstone_ore"]
    for _ in range(8):
        dx = choice([-width//2 + 1, width//2 - 1])
        dz = randint(-length//2 + 2, length//2 - 2)
        dy = randint(-basement_height, -2)
        ED.placeBlock((xaxis + dx, y + dy, zaxis + dz), Block(choice(ore_types)))

def build_luxury_mansion(enhance=True):
    """Build a luxury mansion with advanced features"""
    # Select a design theme
    theme_name = choice(list(THEMES.keys()))
    theme_materials = THEMES[theme_name]
    print(f"Building a {theme_name} style luxury mansion...")

    # Determine house dimensions
    width = randint(13, 19)
    length = randint(19, 27)
    height = randint(6, 9)
    
    # Ensure width and length are odd for better symmetry
    if width % 2 == 0: width += 1
    if length % 2 == 0: length += 1
    
    # Find build location
    xaxis = STARTX + (LASTX - STARTX) // 2
    zaxis = STARTZ + (LASTZ - STARTZ) // 2
    heights = WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    
    # Find average height in building footprint
    height_sum = 0
    count = 0
    for dx in range(-width//2 - 3, width//2 + 4):
        for dz in range(-length//2 - 3, length//2 + 4):
            if 0 <= xaxis + dx - STARTX < len(heights) and 0 <= zaxis + dz - STARTZ < len(heights[0]):
                height_sum += heights[(xaxis + dx - STARTX, zaxis + dz - STARTZ)]
                count += 1
    
    # Set y at average height, rounded up
    y = (height_sum // count) + 1 if count > 0 else 64
    
    # Create a map of terrain adjustments needed
    adjustments = create_terrain_adjustment_map(heights, xaxis, zaxis, width, length, y, STARTX, STARTZ)
    
    # Base building functions
    clear_space(ED, xaxis, zaxis, y, width, length, height, "pitched")
    build_foundation(ED, xaxis, zaxis, y, width, length, theme_materials, adjustments)
    build_floor(ED, xaxis, zaxis, y, width, length, theme_materials)
    build_walls(ED, xaxis, zaxis, y, width, length, height, theme_materials)
    build_roof(ED, xaxis, zaxis, y, width, length, height, theme_materials)
    
    # Add exterior features
    add_door(ED, xaxis, zaxis, y, width, length, theme_materials)
    add_windows(ED, xaxis, zaxis, y, width, length, height, theme_materials)
    
    # Add interior features
    add_interior_details(ED, xaxis, zaxis, y, width, length, height, theme_materials)
    
    # Optional enhanced features
    if enhance:
        create_basement(ED, xaxis, zaxis, y, width, length, theme_materials)
        create_garden(ED, xaxis, zaxis, y, width, length, theme_materials, adjustments)
    
    return (xaxis, y, zaxis, width, length, height)

def main():
    try:
        build_luxury_mansion(enhance=True)
        print("Your luxury mansion has been built! Enjoy your new home!")
    except KeyboardInterrupt:
        print("Build canceled!")

if __name__ == "__main__":
    main()
