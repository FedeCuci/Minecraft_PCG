#!/usr/bin/env python3
import logging
import numpy as np
import math
from random import randint, choice, random, seed, uniform
from termcolor import colored
from gdpc import Block, Editor
from gdpc import geometry as geo
from gdpc.vector_tools import addY
import time

# Seed the random generator with time for true procedural generation
seed(int(time.time()))

# Set up logging and editor
logging.basicConfig(format=colored("%(name)s - %(levelname)s - %(message)s", color="yellow"))
ED = Editor(buffering=True)
BUILD_AREA = ED.getBuildArea()
STARTX, STARTY, STARTZ = BUILD_AREA.begin
LASTX, LASTY, LASTZ = BUILD_AREA.last
WORLDSLICE = ED.loadWorldSlice(BUILD_AREA.toRect(), cache=True)

# Get biome information for environmental adaptation
try:
    biomes = WORLDSLICE.getBiomes()
    center_biome = biomes[len(biomes)//2, len(biomes[0])//2]
    print(f"Center biome: {center_biome}")
except:
    center_biome = "plains"
    print("Could not get biome information. Defaulting to plains.")

# Enhanced materials palette with biome-adaptive themes
THEMES = {
    "plains": {
        "foundation": ["cobblestone", "stone_bricks", "mossy_stone_bricks"],
        "floor": ["oak_planks", "spruce_planks"],
        "walls": ["oak_planks", "oak_log", "stripped_oak_log"],
        "trim": ["dark_oak_log", "spruce_log"],
        "roof": ["dark_oak_stairs", "oak_stairs"],
        "accent": ["cobblestone", "stone_bricks"],
        "details": ["lantern", "oak_fence", "oak_trapdoor"],
        "windows": ["glass_pane"]
    },
    "forest": {
        "foundation": ["cobblestone", "mossy_cobblestone", "stone_bricks"],
        "floor": ["spruce_planks", "dark_oak_planks"],
        "walls": ["spruce_planks", "stripped_spruce_log"],
        "trim": ["dark_oak_log", "spruce_log"],
        "roof": ["dark_oak_stairs", "spruce_stairs"],
        "accent": ["cobblestone", "mossy_cobblestone"],
        "details": ["lantern", "spruce_fence", "spruce_trapdoor"],
        "windows": ["glass_pane"]
    },
    "desert": {
        "foundation": ["sandstone", "cut_sandstone", "smooth_sandstone"],
        "floor": ["terracotta", "orange_terracotta", "yellow_terracotta"],
        "walls": ["sandstone", "smooth_sandstone", "terracotta"],
        "trim": ["birch_log", "acacia_log"],
        "roof": ["smooth_sandstone_stairs", "acacia_stairs"],
        "accent": ["terracotta", "yellow_terracotta"],
        "details": ["lantern", "birch_fence", "birch_trapdoor"],
        "windows": ["glass_pane"]
    },
    "taiga": {
        "foundation": ["cobblestone", "andesite", "stone_bricks"],
        "floor": ["spruce_planks", "dark_oak_planks"],
        "walls": ["spruce_planks", "spruce_log"],
        "trim": ["spruce_log", "stripped_spruce_log"],
        "roof": ["spruce_stairs", "stone_stairs"],
        "accent": ["cobblestone", "andesite"],
        "details": ["lantern", "spruce_fence", "spruce_trapdoor"],
        "windows": ["glass_pane"]
    },
    "swamp": {
        "foundation": ["mossy_cobblestone", "mossy_stone_bricks", "cobblestone"],
        "floor": ["dark_oak_planks", "oak_planks"],
        "walls": ["dark_oak_planks", "stripped_dark_oak_log"],
        "trim": ["dark_oak_log", "oak_log"],
        "roof": ["dark_oak_stairs", "oak_stairs"],
        "accent": ["mossy_cobblestone", "mossy_stone_bricks"],
        "details": ["lantern", "dark_oak_fence", "dark_oak_trapdoor"],
        "windows": ["glass_pane"]
    },
    "savanna": {
        "foundation": ["cobblestone", "terracotta", "acacia_planks"],
        "floor": ["acacia_planks", "terracotta"],
        "walls": ["acacia_planks", "stripped_acacia_log", "terracotta"],
        "trim": ["acacia_log", "stripped_acacia_log"],
        "roof": ["acacia_stairs", "dark_oak_stairs"],
        "accent": ["terracotta", "orange_terracotta"],
        "details": ["lantern", "acacia_fence", "acacia_trapdoor"],
        "windows": ["glass_pane"]
    }
}

# Architectural styles that adapt to environment and the chosen theme
HOUSE_STYLES = [
    "cottage",      # Simple, homely structure with pitched roof
    "longhouse",    # Extended rectangular design inspired by nordic architecture
    "split-level",  # Multi-level structure adapting to hillsides
    "compound",     # Multiple small buildings connected by paths/courtyards
    "tower",        # Taller structure with smaller footprint
    "courtyard",    # Building around a central open space
    "platform"      # Raised structure on stilts (good for water/uneven terrain)
]

def get_theme_for_biome(biome_name):
    """Select appropriate theme based on biome"""
    # Map biome names to themes
    biome_map = {
        "plains": "plains",
        "sunflower_plains": "plains",
        "forest": "forest",
        "flower_forest": "forest",
        "birch_forest": "forest",
        "dark_forest": "forest",
        "desert": "desert",
        "desert_hills": "desert",
        "desert_lakes": "desert",
        "taiga": "taiga",
        "taiga_hills": "taiga",
        "snowy_taiga": "taiga",
        "swamp": "swamp",
        "swamp_hills": "swamp",
        "savanna": "savanna",
        "savanna_plateau": "savanna",
        "shattered_savanna": "savanna",
        # Add more mappings as needed
    }
    
    # Default to plains if biome not recognized
    return biome_map.get(biome_name, "plains")

def get_random_block(block_list):
    """Select a random block from the provided list"""
    return Block(choice(block_list))

def get_weighted_random(block_list, primary_weight=0.7):
    """Get a block with weighting to prefer the primary option"""
    if random() < primary_weight:
        return Block(block_list[0])
    return Block(choice(block_list[1:]))

def analyze_terrain(margin=10):
    """
    Thoroughly analyzes terrain to identify interesting features and building opportunities.
    Returns a list of potential building sites with their characteristics.
    """
    print("Analyzing terrain for interesting building opportunities...")
    
    # Get heightmaps
    terrain_hmap = np.array(WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
    water_hmap = np.array(WORLDSLICE.heightmaps["OCEAN_FLOOR"])
    water_diff = terrain_hmap - water_hmap
    
    # Calculate terrain gradients (slopes)
    gradient_x = np.zeros(terrain_hmap.shape)
    gradient_z = np.zeros(terrain_hmap.shape)
    
    # Calculate gradients (slopes) for the terrain
    for x in range(1, terrain_hmap.shape[0]-1):
        gradient_x[x, :] = terrain_hmap[x+1, :] - terrain_hmap[x-1, :]
    
    for z in range(1, terrain_hmap.shape[1]-1):
        gradient_z[:, z] = terrain_hmap[:, z+1] - terrain_hmap[:, z-1]
    
    # Calculate slope magnitude
    slope_magnitude = np.sqrt(gradient_x**2 + gradient_z**2)
    
    # Find local terrain features
    potential_sites = []
    
    # Scan the terrain in chunks to identify different types of building sites
    chunk_size = 10
    for x in range(margin, terrain_hmap.shape[0]-chunk_size-margin, chunk_size//2):
        for z in range(margin, terrain_hmap.shape[1]-chunk_size-margin, chunk_size//2):
            # Extract local region
            local_terrain = terrain_hmap[x:x+chunk_size, z:z+chunk_size]
            local_water = water_diff[x:x+chunk_size, z:z+chunk_size]
            local_slope = slope_magnitude[x:x+chunk_size, z:z+chunk_size]
            
            # Calculate features
            mean_height = np.mean(local_terrain)
            height_variance = np.std(local_terrain)
            max_slope = np.max(local_slope)
            has_water = np.any(local_water > 0)
            near_water = np.any(local_water[1:-1, 1:-1] > 0) 
            
            # Calculate properties for different building styles
            center_x, center_z = x + chunk_size//2, z + chunk_size//2
            
            # Different site types for different building styles
            site_type = "undefined"
            site_quality = 0
            
            # Flat areas (good for standard buildings)
            if height_variance < 1.5 and not has_water:
                site_type = "flat"
                site_quality = 10 - height_variance
            
            # Hillside areas (good for multi-level or embedded structures)
            elif 1.5 <= height_variance <= 5 and max_slope > 0.5 and not has_water:
                site_type = "hillside"
                site_quality = 5 + min(height_variance, 5)
                
                # Determine slope direction (building orientation)
                avg_grad_x = np.mean(gradient_x[x:x+chunk_size, z:z+chunk_size])
                avg_grad_z = np.mean(gradient_z[x:x+chunk_size, z:z+chunk_size])
                
                # Direction of steepest ascent
                slope_direction = math.degrees(math.atan2(avg_grad_z, avg_grad_x))
            
            # Waterfront areas (good for docks, platforms)
            elif near_water and not has_water:
                site_type = "waterfront"
                site_quality = 8
            
            # Water areas (for structures on stilts)
            elif has_water and np.mean(local_water) > 0:
                water_depth = np.mean(local_water[local_water > 0])
                if water_depth < 5:  # Not too deep
                    site_type = "shallow_water"
                    site_quality = 7
            
            # Elevated/Cliff areas
            elif height_variance > 5 and np.max(local_terrain) - np.min(local_terrain) > 7:
                site_type = "elevated"
                site_quality = 6 + min(height_variance/2, 4)
            
            # Add valid sites to our list
            if site_type != "undefined" and site_quality > 5:
                # Find highest and lowest points for multi-level building planning
                min_height = np.min(local_terrain)
                max_height = np.max(local_terrain)
                
                potential_sites.append({
                    "x": STARTX + center_x,
                    "z": STARTZ + center_z,
                    "y": int(mean_height),
                    "type": site_type,
                    "quality": site_quality,
                    "height_variance": height_variance,
                    "has_water": has_water,
                    "near_water": near_water,
                    "max_slope": max_slope,
                    "min_height": int(min_height),
                    "max_height": int(max_height),
                    "local_x": center_x,
                    "local_z": center_z,
                    "size": chunk_size
                })
    
    # Sort sites by quality
    potential_sites.sort(key=lambda site: site['quality'], reverse=True)
    
    # Make sure we have at least one site
    if not potential_sites:
        print("No optimal building sites found. Creating a default site.")
        center_x = terrain_hmap.shape[0] // 2
        center_z = terrain_hmap.shape[1] // 2
        mean_height = int(np.mean(terrain_hmap[
            max(0, center_x-5):min(terrain_hmap.shape[0], center_x+5),
            max(0, center_z-5):min(terrain_hmap.shape[1], center_z+5)
        ]))
        
        potential_sites.append({
            "x": STARTX + center_x,
            "z": STARTZ + center_z,
            "y": mean_height,
            "type": "default",
            "quality": 5,
            "height_variance": 0,
            "has_water": False,
            "near_water": False,
            "max_slope": 0,
            "min_height": mean_height,
            "max_height": mean_height,
            "local_x": center_x,
            "local_z": center_z,
            "size": 10
        })
    
    print(f"Found {len(potential_sites)} potential building sites.")
    return potential_sites

def choose_building_style(site, biome_name):
    """Select an appropriate building style based on terrain and biome"""
    site_type = site["type"]
    
    # Weight different styles based on site characteristics
    style_weights = {
        "cottage": 10,      # Default weight
        "longhouse": 5,
        "split-level": 5,
        "compound": 5,
        "tower": 5,
        "courtyard": 5, 
        "platform": 5
    }
    
    # Adjust weights based on terrain type
    if site_type == "flat":
        style_weights["cottage"] += 5
        style_weights["longhouse"] += 10
        style_weights["compound"] += 10
        style_weights["courtyard"] += 15
    
    elif site_type == "hillside":
        style_weights["split-level"] += 20
        style_weights["compound"] += 5
        
    elif site_type == "waterfront":
        style_weights["cottage"] += 5
        style_weights["platform"] += 10
        
    elif site_type == "shallow_water":
        style_weights["platform"] += 25
        
    elif site_type == "elevated":
        style_weights["tower"] += 15
        style_weights["split-level"] += 10
    
    # Adjust weights based on biome
    if biome_name == "taiga" or biome_name == "forest":
        style_weights["cottage"] += 5
        style_weights["longhouse"] += 10
    
    elif biome_name == "desert":
        style_weights["courtyard"] += 10
        style_weights["compound"] += 5
        
    elif biome_name == "swamp":
        style_weights["platform"] += 15
        
    elif biome_name == "savanna":
        style_weights["compound"] += 10
        style_weights["tower"] += 5
    
    # Convert weights to probabilities
    total_weight = sum(style_weights.values())
    style_probs = {style: weight/total_weight for style, weight in style_weights.items()}
    
    # Select a style using weighted probabilities
    rand_val = random()
    cumulative_prob = 0
    chosen_style = HOUSE_STYLES[0]  # Default
    
    for style, prob in style_probs.items():
        cumulative_prob += prob
        if rand_val <= cumulative_prob:
            chosen_style = style
            break
    
    print(f"Chose {chosen_style} style for {site_type} site in {biome_name} biome")
    return chosen_style

def create_terrain_adaptation_plan(site, width, length, height, building_style):
    """Create a detailed plan for how the building should adapt to the terrain"""
    print("Creating terrain adaptation plan...")
    
    # Get heightmaps for the specific site area
    terrain_hmap = np.array(WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
    water_hmap = np.array(WORLDSLICE.heightmaps["OCEAN_FLOOR"])
    water_diff = terrain_hmap - water_hmap
    
    # Extract local heightmap from site
    site_x, site_z = site["local_x"], site["local_z"]
    local_radius = max(width, length) // 2 + 5
    
    # Define boundaries of our area of interest
    x_min = max(0, site_x - local_radius)
    x_max = min(terrain_hmap.shape[0], site_x + local_radius)
    z_min = max(0, site_z - local_radius)
    z_max = min(terrain_hmap.shape[1], site_z + local_radius)
    
    # Extract local terrain data
    local_terrain = terrain_hmap[x_min:x_max, z_min:z_max].copy()
    local_water = water_diff[x_min:x_max, z_min:z_max].copy()
    
    # Compute a normalized version for easier calculations
    local_terrain_normalized = local_terrain - np.min(local_terrain)
    
    # Create the adaptation plan based on building style
    adaptation_plan = {
        "style": building_style,
        "foundation_mode": "standard",  # standard, elevated, embedded, stilts
        "tiers": 1,                     # How many vertical levels
        "rotation": 0,                  # Building rotation in degrees
        "water_features": [],           # Coordinates of water features
        "landscaping": [],              # Areas for gardens, paths, etc.
        "terrain_adjustments": {},      # Areas that need leveling or building up
        "foundation_height": 0,
        "multi_level_heights": [],
        "outline_shape": "rectangle"    # rectangle, L-shape, irregular, circular
    }
    
    # Determine the site's average height for the building footprint
    footprint_heights = []
    for dx in range(-width//2, width//2 + 1):
        for dz in range(-length//2, length//2 + 1):
            local_x = site_x + dx - x_min
            local_z = site_z + dz - z_min
            if 0 <= local_x < local_terrain.shape[0] and 0 <= local_z < local_terrain.shape[1]:
                footprint_heights.append(local_terrain[local_x, local_z])
    
    avg_footprint_height = int(np.median(footprint_heights)) if footprint_heights else site["y"]
    adaptation_plan["base_height"] = avg_footprint_height
    
    # Adapt foundation mode based on site type and building style
    if site["type"] == "shallow_water" or (site["type"] == "waterfront" and building_style == "platform"):
        adaptation_plan["foundation_mode"] = "stilts"
        # Determine how high above water to build
        water_level = int(np.mean(local_terrain[local_water > 0])) if np.any(local_water > 0) else avg_footprint_height
        adaptation_plan["foundation_height"] = water_level + randint(2, 4)
    
    elif site["type"] == "hillside" and building_style == "split-level":
        adaptation_plan["foundation_mode"] = "embedded"
        adaptation_plan["tiers"] = 2 + int(site["height_variance"] // 2)  # More tiers for more varied terrain
        
        # Calculate heights for different tiers
        height_range = site["max_height"] - site["min_height"]
        tier_height = height_range / adaptation_plan["tiers"]
        adaptation_plan["multi_level_heights"] = [site["min_height"] + int(tier_height * i) for i in range(adaptation_plan["tiers"])]
    
    elif site["type"] == "elevated":
        if building_style == "tower":
            adaptation_plan["foundation_mode"] = "embedded"
            # Find a local peak
            local_peaks = []
            for dx in range(1, local_terrain.shape[0]-1):
                for dz in range(1, local_terrain.shape[1]-1):
                    if (local_terrain[dx, dz] >= local_terrain[dx-1, dz] and
                        local_terrain[dx, dz] >= local_terrain[dx+1, dz] and
                        local_terrain[dx, dz] >= local_terrain[dx, dz-1] and
                        local_terrain[dx, dz] >= local_terrain[dx, dz+1]):
                        local_peaks.append((dx, dz, local_terrain[dx, dz]))
            
            if local_peaks:
                # Choose the highest peak
                local_peaks.sort(key=lambda p: p[2], reverse=True)
                peak_x, peak_z, peak_height = local_peaks[0]
                
                # Adjust building center to peak
                adaptation_plan["center_offset"] = (peak_x + x_min - site_x, peak_z + z_min - site_z)
                adaptation_plan["base_height"] = int(peak_height)
    
    # Adjust outline shape based on style
    if building_style == "compound":
        shapes = ["L-shape", "irregular", "rectangle"]
        adaptation_plan["outline_shape"] = choice(shapes)
    elif building_style == "courtyard":
        adaptation_plan["outline_shape"] = "courtyard"
    elif building_style == "longhouse":
        # Determine the best orientation for a longhouse
        # If the terrain slopes in one direction, align the long axis along the contour line
        terrain_gradient_x = np.gradient(local_terrain, axis=0)
        terrain_gradient_z = np.gradient(local_terrain, axis=1)
        avg_gradient_x = np.mean(terrain_gradient_x)
        avg_gradient_z = np.mean(terrain_gradient_z)
        
        # If there's a significant gradient, rotate the building
        if abs(avg_gradient_x) > 0.2 or abs(avg_gradient_z) > 0.2:
            # Calculate the angle of the gradient
            gradient_angle = math.degrees(math.atan2(avg_gradient_z, avg_gradient_x))
            # Rotate the building 90 degrees from the gradient (to align with contour)
            adaptation_plan["rotation"] = (gradient_angle + 90) % 360
    
    # Identify areas for gardens, farms, or other landscaping
    if building_style != "platform" and building_style != "tower":
        # Look for flatter areas near the building site for gardens
        for dx in range(-local_radius, local_radius):
            for dz in range(-local_radius, local_radius):
                local_x = site_x + dx - x_min
                local_z = site_z + dz - z_min
                
                # Skip if out of bounds
                if not (0 <= local_x < local_terrain.shape[0] and 0 <= local_z < local_terrain.shape[1]):
                    continue
                
                # Skip if too close to the building
                if abs(dx) < width//2 + 2 and abs(dz) < length//2 + 2:
                    continue
                
                # Look for flat areas at a reasonable distance for gardens
                if (width//2 + 2 <= abs(dx) <= width//2 + 10 or 
                    length//2 + 2 <= abs(dz) <= length//2 + 10):
                    
                    # If it's flat and not water
                    if (local_water[local_x, local_z] == 0 and
                        abs(local_terrain[local_x, local_z] - avg_footprint_height) < 3):
                        adaptation_plan["landscaping"].append((dx, dz))
    
    # Identify water features we can incorporate
    if site["near_water"]:
        for dx in range(-local_radius, local_radius):
            for dz in range(-local_radius, local_radius):
                local_x = site_x + dx - x_min
                local_z = site_z + dz - z_min
                
                # Skip if out of bounds
                if not (0 <= local_x < local_terrain.shape[0] and 0 <= local_z < local_terrain.shape[1]):
                    continue
                
                # If there's water near the building, add it as a feature
                if local_water[local_x, local_z] > 0:
                    adaptation_plan["water_features"].append((dx, dz))
    
    # Return the completed plan
    return adaptation_plan

def create_house_layout(width, length, style, site_plan):
    """Generate a house layout based on style and site plan"""
    print(f"Creating {style} house layout...")
    
    # Default room layout (will be modified based on style)
    layout = {
        "rooms": [],
        "walls": [],
        "doors": [],
        "windows": [],
        "special_features": []
    }
    
    outline_shape = site_plan.get("outline_shape", "rectangle")
    tiers = site_plan.get("tiers", 1)
    
    # Create different layouts based on building style
    if style == "cottage":
        # Simple cottage with main room, bedroom, and kitchen
        layout["rooms"] = [
            {"name": "main_room", "x1": -width//4, "z1": -length//4, "x2": width//4, "z2": length//4, "tier": 0},
            {"name": "bedroom", "x1": -width//2 + 1, "z1": length//4, "x2": width//4, "z2": length//2 - 1, "tier": 0},
            {"name": "kitchen", "x1": width//4, "z1": -length//2 + 1, "x2": width//2 - 1, "z2": length//4, "tier": 0}
        ]
        
        # Add walls between rooms
        layout["walls"] = [
            # Bedroom divider
            {"x1": -width//4, "z1": length//4, "x2": width//4, "z2": length//4},
            # Kitchen divider
            {"x1": width//4, "z1": -length//4, "x2": width//4, "z2": length//4}
        ]
        
        # Add doors between rooms
        layout["doors"] = [
            # Door to bedroom
            {"x": 0, "z": length//4, "facing": "north"},
            # Door to kitchen
            {"x": width//4, "z": 0, "facing": "west"},
            # Main entrance
            {"x": -width//2, "z": 0, "facing": "east", "is_entrance": True}
        ]
        
        # Add windows
        window_positions = [
            {"x": width//2, "z": -length//3, "facing": "west"},
            {"x": width//2, "z": length//3, "facing": "west"},
            {"x": -width//2, "z": length//3, "facing": "east"},
            {"x": -width//3, "z": length//2, "facing": "north"},
            {"x": width//3, "z": length//2, "facing": "north"},
            {"x": width//3, "z": -length//2, "facing": "south"},
            {"x": -width//3, "z": -length//2, "facing": "south"}
        ]
        layout["windows"] = window_positions
        
        # Add special features
        layout["special_features"] = [
            {"type": "fireplace", "x": width//2 - 1, "z": 0},
            {"type": "bookshelf", "x": 0, "z": -length//2 + 1},
            {"type": "table", "x": width//3, "z": -length//3}
        ]
    
    elif style == "longhouse":
        # Long central hall with rooms along the sides
        central_hall_width = width//3
        
        layout["rooms"] = [
            {"name": "great_hall", "x1": -central_hall_width//2, "z1": -length//2 + 1, 
             "x2": central_hall_width//2, "z2": length//2 - 1, "tier": 0},
        ]
        
        # Add side rooms
        num_side_rooms = randint(3, 5)
        room_length = length // num_side_rooms
        
        for i in range(num_side_rooms):
            # Left side rooms
            z_start = -length//2 + 1 + i * room_length
            z_end = z_start + room_length - 1
            if z_end > length//2 - 1:
                z_end = length//2 - 1
                
            layout["rooms"].append({
                "name": f"left_room_{i}", 
                "x1": -width//2 + 1, "z1": z_start,
                "x2": -central_hall_width//2 - 1, "z2": z_end,
                "tier": 0
            })
            
            # Right side rooms
            layout["rooms"].append({
                "name": f"right_room_{i}", 
                "x1": central_hall_width//2 + 1, "z1": z_start,
                "x2": width//2 - 1, "z2": z_end,
                "tier": 0
            })
            
            # Add doors to side rooms
            layout["doors"].append({
                "x": -central_hall_width//2, "z": z_start + room_length//2, "facing": "east"
            })
            
            layout["doors"].append({
                "x": central_hall_width//2, "z": z_start + room_length//2, "facing": "west"
            })
        
        # Add walls for the central hall
        layout["walls"].extend([
            {"x1": -central_hall_width//2, "z1": -length//2 + 1, "x2": -central_hall_width//2, "z2": length//2 - 1},
            {"x1": central_hall_width//2, "z1": -length//2 + 1, "x2": central_hall_width//2, "z2": length//2 - 1}
        ])
        
        # Main entrances at each end of the hall
        layout["doors"].extend([
            {"x": 0, "z": -length//2, "facing": "south", "is_entrance": True},
            {"x": 0, "z": length//2, "facing": "north", "is_entrance": True}
        ])
        
        # Add windows on the sides
        for z in range(-length//2 + room_length//2, length//2, room_length):
            layout["windows"].extend([
                {"x": -width//2, "z": z, "facing": "east"},
                {"x": width//2, "z": z, "facing": "west"}
            ])
        
        # Add special features
        layout["special_features"] = [
            {"type": "hearth", "x": 0, "z": 0},
            {"type": "table", "x": 0, "z": -length//4, "length": central_hall_width - 2},
            {"type": "table", "x": 0, "z": length//4, "length": central_hall_width - 2}
        ]
    
    elif style == "split-level":
        # Create a split-level structure with rooms on different tiers
        tier_heights = site_plan.get("multi_level_heights", [0])
        if len(tier_heights) < tiers:
            # Fill in missing tiers
            for i in range(len(tier_heights), tiers):
                tier_heights.append(tier_heights[-1] + randint(2, 4))
                
        # Main level common area
        layout["rooms"].append({
            "name": "common_area",
            "x1": -width//3, "z1": -length//3,
            "x2": width//3, "z2": length//3,
            "tier": 0
        })
        
        # Decide how to distribute remaining rooms across tiers
        # For simplicity, we'll do one room per additional tier
        directions = ["north", "south", "east", "west"]
        tier_directions = []
        
        for i in range(1, tiers):
            direction = choice(directions)
            tier_directions.append(direction)
            directions.remove(direction)  # Don't reuse the same direction
            
            if direction == "north":
                layout["rooms"].append({
                    "name": f"north_room_tier_{i}",
                    "x1": -width//3, "z1": length//3,
                    "x2": width//3, "z2": length//2 - 1,
                    "tier": i
                })
                # Add steps between tiers
                layout["special_features"].append({
                    "type": "stairs",
                    "x": 0, "z": length//3 - 1,
                    "facing": "north",
                    "to_tier": i
                })
            elif direction == "south":
                layout["rooms"].append({
                    "name": f"south_room_tier_{i}",
                    "x1": -width//3, "z1": -length//2 + 1,
                    "x2": width//3, "z2": -length//3,
                    "tier": i
                })
                layout["special_features"].append({
                    "type": "stairs",
                    "x": 0, "z": -length//3 + 1,
                    "facing": "south",
                    "to_tier": i
                })
            elif direction == "east":
                layout["rooms"].append({
                    "name": f"east_room_tier_{i}",
                    "x1": width//3, "z1": -length//3,
                    "x2": width//2 - 1, "z2": length//3,
                    "tier": i
                })
                layout["special_features"].append({
                    "type": "stairs",
                    "x": width//3 - 1, "z": 0,
                    "facing": "east",
                    "to_tier": i
                })
            elif direction == "west":
                layout["rooms"].append({
                    "name": f"west_room_tier_{i}",
                    "x1": -width//2 + 1, "z1": -length//3,
                    "x2": -width//3, "z2": length//3,
                    "tier": i
                })
                layout["special_features"].append({
                    "type": "stairs",
                    "x": -width//3 + 1, "z": 0,
                    "facing": "west",
                    "to_tier": i
                })
        
        # Add entrance
        main_entrance_candidates = [d for d in ["north", "south", "east", "west"] if d not in tier_directions]
        if not main_entrance_candidates:
            main_entrance_candidates = ["south"] # Default
        
        main_entrance = choice(main_entrance_candidates)
        if main_entrance == "south":
            layout["doors"].append({"x": 0, "z": -length//2, "facing": "south", "is_entrance": True})
        elif main_entrance == "north":
            layout["doors"].append({"x": 0, "z": length//2, "facing": "north", "is_entrance": True})
        elif main_entrance == "east":
            layout["doors"].append({"x": width//2, "z": 0, "facing": "east", "is_entrance": True})
        elif main_entrance == "west":
            layout["doors"].append({"x": -width//2, "z": 0, "facing": "west", "is_entrance": True})
        
        # Add windows for each room
        for room in layout["rooms"]:
            tier = room["tier"]
            center_x = (room["x1"] + room["x2"]) // 2
            center_z = (room["z1"] + room["z2"]) // 2
            
            # Add windows on external walls
            if room["x1"] == -width//2 + 1:  # West wall
                layout["windows"].append({"x": -width//2, "z": center_z, "facing": "east", "tier": tier})
            if room["x2"] == width//2 - 1:  # East wall
                layout["windows"].append({"x": width//2, "z": center_z, "facing": "west", "tier": tier})
            if room["z1"] == -length//2 + 1:  # South wall
                layout["windows"].append({"x": center_x, "z": -length//2, "facing": "south", "tier": tier})
            if room["z2"] == length//2 - 1:  # North wall
                layout["windows"].append({"x": center_x, "z": length//2, "facing": "north", "tier": tier})
    
    elif style == "compound":
        # Multiple small buildings connected by paths
        # Main building in the center
        main_building_width = width * 2 // 3
        main_building_length = length * 2 // 3
        
        layout["rooms"].append({
            "name": "main_building",
            "x1": -main_building_width//2, "z1": -main_building_length//2,
            "x2": main_building_width//2, "z2": main_building_length//2,
            "tier": 0,
            "is_separate": True
        })
        
        # Add smaller outbuildings
        num_outbuildings = randint(2, 4)
        outbuilding_positions = []
        
        # Define potential outbuilding positions
        potential_positions = [
            {"x": -width//2 + main_building_width//4, "z": -length//2 + main_building_length//4, "name": "northwest"},
            {"x": width//2 - main_building_width//4, "z": -length//2 + main_building_length//4, "name": "northeast"},
            {"x": -width//2 + main_building_width//4, "z": length//2 - main_building_length//4, "name": "southwest"},
            {"x": width//2 - main_building_width//4, "z": length//2 - main_building_length//4, "name": "southeast"}
        ]
        
        # Choose positions for outbuildings
        for i in range(min(num_outbuildings, len(potential_positions))):
            position = potential_positions.pop(randint(0, len(potential_positions)-1))
            outbuilding_positions.append(position)
        
        # Create outbuildings
        for i, position in enumerate(outbuilding_positions):
            outbuilding_size = randint(4, 6)
            x_center, z_center = position["x"], position["z"]
            
            layout["rooms"].append({
                "name": f"outbuilding_{position['name']}",
                "x1": x_center - outbuilding_size//2, "z1": z_center - outbuilding_size//2,
                "x2": x_center + outbuilding_size//2, "z2": z_center + outbuilding_size//2,
                "tier": 0,
                "is_separate": True
            })
            
            # Add a path from main building to outbuilding
            layout["special_features"].append({
                "type": "path",
                "x1": 0, "z1": 0,  # Center of main building
                "x2": x_center, "z2": z_center  # Center of outbuilding
            })
            
            # Add a door to the outbuilding facing the main building
            door_facing = "north"  # Default
            if x_center > 0 and abs(x_center) > abs(z_center):
                door_facing = "west"
            elif x_center < 0 and abs(x_center) > abs(z_center):
                door_facing = "east"
            elif z_center > 0:
                door_facing = "south"
            
            door_x, door_z = x_center, z_center
            if door_facing == "north":
                door_z = z_center - outbuilding_size//2
            elif door_facing == "south":
                door_z = z_center + outbuilding_size//2
            elif door_facing == "east":
                door_x = x_center - outbuilding_size//2
            elif door_facing == "west":
                door_x = x_center + outbuilding_size//2
            
            layout["doors"].append({"x": door_x, "z": door_z, "facing": door_facing})
            
            # Add windows to outbuildings
            layout["windows"].append({
                "x": x_center, "z": z_center + (outbuilding_size//2 * (1 if door_facing != "south" else -1)),
                "facing": "south" if door_facing != "south" else "north"
            })
            layout["windows"].append({
                "x": x_center + (outbuilding_size//2 * (1 if door_facing != "west" else -1)), "z": z_center,
                "facing": "west" if door_facing != "west" else "east"
            })
        
        # Add main building doors and windows
        layout["doors"].append({
            "x": 0, "z": -main_building_length//2, 
            "facing": "south", "is_entrance": True
        })
        
        layout["windows"].extend([
            {"x": -main_building_width//4, "z": -main_building_length//2, "facing": "south"},
            {"x": main_building_width//4, "z": -main_building_length//2, "facing": "south"},
            {"x": -main_building_width//2, "z": 0, "facing": "east"},
            {"x": main_building_width//2, "z": 0, "facing": "west"},
            {"x": 0, "z": main_building_length//2, "facing": "north"}
        ])
        
        # Add special features to main building
        layout["special_features"].append({
            "type": "fireplace",
            "x": 0, "z": main_building_length//4
        })
    
    elif style == "tower":
        # Tall structure with smaller footprint
        # Make it square for simplicity
        tower_size = min(width, length) - 2
        
        # Create a circular or square tower
        is_circular = random() > 0.5
        layout["is_circular"] = is_circular
        
        # One room per floor
        num_floors = randint(3, 5)
        for i in range(num_floors):
            layout["rooms"].append({
                "name": f"floor_{i}",
                "x1": -tower_size//2, "z1": -tower_size//2,
                "x2": tower_size//2, "z2": tower_size//2,
                "tier": i
            })
            
            # Add stairs between floors
            if i < num_floors - 1:
                stair_x = tower_size//4 if i % 2 == 0 else -tower_size//4
                layout["special_features"].append({
                    "type": "stairs",
                    "x": stair_x, "z": 0,
                    "facing": "east" if i % 2 == 0 else "west",
                    "to_tier": i + 1
                })
        
        # Add entrance door
        layout["doors"].append({
            "x": 0, "z": -tower_size//2, "facing": "south", "is_entrance": True, "tier": 0
        })
        
        # Add windows to each floor
        for i in range(num_floors):
            for direction in ["north", "south", "east", "west"]:
                # Skip entrance for ground floor south
                if i == 0 and direction == "south":
                    continue
                
                if direction == "north":
                    layout["windows"].append({"x": 0, "z": tower_size//2, "facing": "north", "tier": i})
                elif direction == "south":
                    layout["windows"].append({"x": 0, "z": -tower_size//2, "facing": "south", "tier": i})
                elif direction == "east":
                    layout["windows"].append({"x": tower_size//2, "z": 0, "facing": "east", "tier": i})
                elif direction == "west":
                    layout["windows"].append({"x": -tower_size//2, "z": 0, "facing": "west", "tier": i})
        
        # Add roof features
        layout["special_features"].append({
            "type": "tower_top", 
            "x": 0, "z": 0, 
            "tier": num_floors - 1,
            "is_circular": is_circular
        })
    
    elif style == "courtyard":
        # Building around a central courtyard
        courtyard_width = width // 3
        courtyard_length = length // 3
        
        # Add the central courtyard (not a room, but a reference)
        layout["special_features"].append({
            "type": "courtyard",
            "x1": -courtyard_width//2, "z1": -courtyard_length//2,
            "x2": courtyard_width//2, "z2": courtyard_length//2
        })
        
        # Add rooms around the courtyard
        # North wing
        layout["rooms"].append({
            "name": "north_wing",
            "x1": -width//2 + 1, "z1": courtyard_length//2,
            "x2": width//2 - 1, "z2": length//2 - 1,
            "tier": 0
        })
        
        # South wing
        layout["rooms"].append({
            "name": "south_wing",
            "x1": -width//2 + 1, "z1": -length//2 + 1,
            "x2": width//2 - 1, "z2": -courtyard_length//2,
            "tier": 0
        })
        
        # East wing
        layout["rooms"].append({
            "name": "east_wing",
            "x1": courtyard_width//2, "z1": -courtyard_length//2,
            "x2": width//2 - 1, "z2": courtyard_length//2,
            "tier": 0
        })
        
        # West wing
        layout["rooms"].append({
            "name": "west_wing",
            "x1": -width//2 + 1, "z1": -courtyard_length//2,
            "x2": -courtyard_width//2, "z2": courtyard_length//2,
            "tier": 0
        })
        
        # Add entrance door
        layout["doors"].append({
            "x": 0, "z": -length//2, "facing": "south", "is_entrance": True
        })
        
        # Add doors to courtyard
        layout["doors"].extend([
            {"x": 0, "z": -courtyard_length//2, "facing": "north"},  # South door to courtyard
            {"x": 0, "z": courtyard_length//2, "facing": "south"},   # North door to courtyard
            {"x": -courtyard_width//2, "z": 0, "facing": "east"},    # West door to courtyard
            {"x": courtyard_width//2, "z": 0, "facing": "west"}      # East door to courtyard
        ])
        
        # Add windows to exterior and courtyard
        # Exterior windows
        layout["windows"].extend([
            {"x": width//4, "z": length//2, "facing": "north"},
            {"x": -width//4, "z": length//2, "facing": "north"},
            {"x": width//4, "z": -length//2, "facing": "south"},
            {"x": -width//4, "z": -length//2, "facing": "south"},
            {"x": width//2, "z": length//4, "facing": "west"},
            {"x": width//2, "z": -length//4, "facing": "west"},
            {"x": -width//2, "z": length//4, "facing": "east"},
            {"x": -width//2, "z": -length//4, "facing": "east"}
        ])
        
        # Courtyard windows
        layout["windows"].extend([
            {"x": width//4, "z": courtyard_length//2, "facing": "south"},
            {"x": -width//4, "z": courtyard_length//2, "facing": "south"},
            {"x": width//4, "z": -courtyard_length//2, "facing": "north"},
            {"x": -width//4, "z": -courtyard_length//2, "facing": "north"},
            {"x": courtyard_width//2, "z": courtyard_length//4, "facing": "west"},
            {"x": courtyard_width//2, "z": -courtyard_length//4, "facing": "west"},
            {"x": -courtyard_width//2, "z": courtyard_length//4, "facing": "east"},
            {"x": -courtyard_width//2, "z": -courtyard_length//4, "facing": "east"}
        ])
        
        # Add special features
        layout["special_features"].extend([
            {"type": "well", "x": 0, "z": 0},  # Well in the center
            {"type": "garden", "x": courtyard_width//4, "z": -courtyard_length//4},
            {"type": "garden", "x": -courtyard_width//4, "z": courtyard_length//4}
        ])
    
    elif style == "platform":
        # Elevated structure on stilts
        stilt_height = site_plan.get("foundation_height", 3) - site_plan.get("base_height", 0)
        layout["stilt_height"] = stilt_height
        
        # Make the platform slightly smaller than the maximum dimensions
        platform_width = width - 2
        platform_length = length - 2
        
        # Main platform
        layout["rooms"].append({
            "name": "main_platform",
            "x1": -platform_width//2, "z1": -platform_length//2,
            "x2": platform_width//2, "z2": platform_length//2,
            "tier": 0
        })
        
        # Interior divisions - simple 2x2 grid
        layout["walls"].extend([
            {"x1": 0, "z1": -platform_length//2, "x2": 0, "z2": platform_length//2},
            {"x1": -platform_width//2, "z1": 0, "x2": platform_width//2, "z2": 0}
        ])
        
        # Name the four rooms
        layout["rooms"].extend([
            {"name": "northwest_room", "x1": -platform_width//2, "z1": 0, 
             "x2": 0, "z2": platform_length//2, "tier": 0, "is_sub_room": True},
            {"name": "northeast_room", "x1": 0, "z1": 0, 
             "x2": platform_width//2, "z2": platform_length//2, "tier": 0, "is_sub_room": True},
            {"name": "southwest_room", "x1": -platform_width//2, "z1": -platform_length//2, 
             "x2": 0, "z2": 0, "tier": 0, "is_sub_room": True},
            {"name": "southeast_room", "x1": 0, "z1": -platform_length//2, 
             "x2": platform_width//2, "z2": 0, "tier": 0, "is_sub_room": True}
        ])
        
        # Add doors between rooms and entrance
        layout["doors"].extend([
            {"x": 0, "z": platform_length//4, "facing": "west"},
            {"x": 0, "z": -platform_length//4, "facing": "west"},
            {"x": platform_width//4, "z": 0, "facing": "south"},
            {"x": -platform_width//4, "z": 0, "facing": "south"},
            # Main entrance
            {"x": -platform_width//2, "z": -platform_length//4, "facing": "east", "is_entrance": True}
        ])
        
        # Add a porch/deck area
        layout["special_features"].append({
            "type": "deck",
            "x1": -platform_width//2 - 3, "z1": -platform_length//4 - 2,
            "x2": -platform_width//2, "z2": -platform_length//4 + 2,
            "tier": 0
        })
        
        # Add stairs down to ground
        layout["special_features"].append({
            "type": "stairs_down",
            "x": -platform_width//2 - 2, "z": -platform_length//4,
            "facing": "east",
            "length": stilt_height
        })
        
        # Windows around perimeter
        for z_pos in range(-platform_length//2 + platform_length//6, platform_length//2, platform_length//3):
            layout["windows"].extend([
                {"x": platform_width//2, "z": z_pos, "facing": "west"},
                {"x": -platform_width//2, "z": z_pos, "facing": "east"}
            ])
            
        for x_pos in range(-platform_width//2 + platform_width//6, platform_width//2, platform_width//3):
            layout["windows"].extend([
                {"x": x_pos, "z": platform_length//2, "facing": "north"},
                {"x": x_pos, "z": -platform_length//2, "facing": "south"}
            ])
        
        # Function features
        layout["special_features"].extend([
            {"type": "fireplace", "x": platform_width//2 - 1, "z": platform_length//4},
            {"type": "bed", "x": platform_width//4, "z": platform_length//4},
            {"type": "storage", "x": -platform_width//4, "z": platform_length//4},
            {"type": "kitchen", "x": -platform_width//4, "z": -platform_length//4},
            {"type": "table", "x": platform_width//4, "z": -platform_length//4}
        ])
        
        # Add railing all around
        layout["special_features"].append({
            "type": "railing",
            "x1": -platform_width//2, "z1": -platform_length//2,
            "x2": platform_width//2, "z2": platform_length//2
        })
    
    # Calculate rough dimensions of layout for later use
    min_x = min([room["x1"] for room in layout["rooms"]])
    max_x = max([room["x2"] for room in layout["rooms"]])
    min_z = min([room["z1"] for room in layout["rooms"]])
    max_z = max([room["z2"] for room in layout["rooms"]])
    
    layout["outer_width"] = max_x - min_x
    layout["outer_length"] = max_z - min_z
    
    return layout

def build_foundation(ED, xaxis, zaxis, y, width, length, building_style, site_plan, theme_materials):
    """Build the house foundation with enhanced terrain adaptation"""
    print("Building foundation...")
    
    foundation_mode = site_plan.get("foundation_mode", "standard")
    heights = np.array(WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
    water_hmap = np.array(WORLDSLICE.heightmaps["OCEAN_FLOOR"])
    water_diff = heights - water_hmap
    
    # Create terrain adjustment map
    adjustments = {}
    for dx in range(-width//2 - 3, width//2 + 4):
        for dz in range(-length//2 - 3, length//2 + 4):
            x, z = xaxis + dx, zaxis + dz
            local_x, local_z = x - STARTX, z - STARTZ
            if 0 <= local_x < heights.shape[0] and 0 <= local_z < heights.shape[1]:
                current_height = heights[local_x, local_z]
                is_water = water_diff[local_x, local_z] > 0 if local_x < water_diff.shape[0] and local_z < water_diff.shape[1] else False
                adjustments[(x, z)] = {
                    "adjustment": y - current_height,
                    "is_water": is_water,
                    "orig_height": current_height
                }
    
    # Apply different foundation strategies based on site plan
    if foundation_mode == "stilts":
        # Build stilts/pillars for elevated structures
        foundation_height = site_plan.get("foundation_height", y + 3)
        
        # Only build stilts at key structural points
        stilt_positions = []
        
        # Corner stilts and boundary stilts
        for dx in range(-width//2, width//2 + 1, max(2, width//6)):
            for dz in range(-length//2, length//2 + 1, max(2, length//6)):
                # Ensure corners are always included
                if dx in [-width//2, width//2] or dz in [-length//2, length//2]:
                    stilt_positions.append((dx, dz))
        
        # Add some internal support stilts for larger structures
        if width > 10 or length > 10:
            for dx in range(-width//4, width//4 + 1, width//4):
                for dz in range(-length//4, length//4 + 1, length//4):
                    if (dx, dz) not in stilt_positions:
                        stilt_positions.append((dx, dz))
                        
        # Build the stilts
        for dx, dz in stilt_positions:
            pos = (xaxis + dx, zaxis + dz)
            if pos in adjustments:
                stilt_bottom = adjustments[pos]["orig_height"]
                stilt_material = choice(theme_materials["foundation"])
                
                # Create column of foundation material from the ground up
                geo.placeCuboid(
                    ED,
                    (xaxis + dx, stilt_bottom, zaxis + dz),
                    (xaxis + dx, foundation_height - 1, zaxis + dz),
                    Block(stilt_material)
                )
                
                # Add decorative elements on tall stilts
                if foundation_height - stilt_bottom > 6:
                    # Add a band in the middle
                    middle_y = stilt_bottom + (foundation_height - stilt_bottom) // 2
                    ED.placeBlock(
                        (xaxis + dx, middle_y, zaxis + dz),
                        Block(choice(theme_materials["accent"]))
                    )
        
        # Add cross-bracing between nearby stilts for stability and aesthetics
        for i, (dx1, dz1) in enumerate(stilt_positions):
            for j, (dx2, dz2) in enumerate(stilt_positions[i+1:], i+1):
                # Only brace between nearby stilts
                if abs(dx2 - dx1) <= 5 and abs(dz2 - dz1) <= 5:
                    pos1 = (xaxis + dx1, zaxis + dz1)
                    pos2 = (xaxis + dx2, zaxis + dz2)
                    
                    if pos1 in adjustments and pos2 in adjustments:
                        stilt1_bottom = adjustments[pos1]["orig_height"]
                        stilt2_bottom = adjustments[pos2]["orig_height"]
                        
                        # Only add bracing on tall enough stilts
                        if min(foundation_height - stilt1_bottom, foundation_height - stilt2_bottom) > 4:
                            # Add a couple of cross-braces
                            for offset in [0.3, 0.7]:
                                brace_y = int(min(stilt1_bottom, stilt2_bottom) + 
                                             offset * (foundation_height - min(stilt1_bottom, stilt2_bottom)))
                                
                                # Determine brace orientation
                                if abs(dx2 - dx1) > abs(dz2 - dz1):
                                    # X-axis oriented brace
                                    for x in range(min(dx1, dx2), max(dx1, dx2) + 1):
                                        ED.placeBlock(
                                            (xaxis + x, brace_y, zaxis + dz1),
                                            Block(choice(theme_materials["trim"]), {"axis": "x"})
                                        )
                                else:
                                    # Z-axis oriented brace
                                    for z in range(min(dz1, dz2), max(dz1, dz2) + 1):
                                        ED.placeBlock(
                                            (xaxis + dx1, brace_y, zaxis + z),
                                            Block(choice(theme_materials["trim"]), {"axis": "z"})
                                        )
        
        # Add platform at the top
        for dx in range(-width//2 - 1, width//2 + 2):
            for dz in range(-length//2 - 1, length//2 + 2):
                ED.placeBlock(
                    (xaxis + dx, foundation_height - 1, zaxis + dz),
                    Block(choice(theme_materials["floor"]))
                )
        
        # Update the base height
        site_plan["base_height"] = foundation_height
    
    elif foundation_mode == "embedded":
        # For structures embedded into hillsides
        # Determine the lowest level that needs foundation
        min_height = min([adj["orig_height"] for adj in adjustments.values()])
        
        # Build a multi-tiered foundation using the natural terrain
        for tier in range(site_plan.get("tiers", 1)):
            tier_y = site_plan.get("multi_level_heights", [y])[tier]
            
            # For each position in the foundation
            for dx in range(-width//2 - 1, width//2 + 2):
                for dz in range(-length//2 - 1, length//2 + 2):
                    pos = (xaxis + dx, zaxis + dz)
                    
                    if pos in adjustments:
                        orig_height = adjustments[pos]["orig_height"]
                        
                        # Only build foundation if this area is for this tier
                        # Simple division of building into tiers front-to-back
                        tier_z_min = -length//2 + (tier * length // site_plan.get("tiers", 1))
                        tier_z_max = -length//2 + ((tier + 1) * length // site_plan.get("tiers", 1))
                        
                        if tier_z_min <= dz < tier_z_max:
                            # If the terrain is below our desired tier height, build up
                            if orig_height < tier_y:
                                # Create foundation pillar
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + dx, orig_height, zaxis + dz),
                                    (xaxis + dx, tier_y - 1, zaxis + dz),
                                    Block(choice(theme_materials["foundation"]))
                                )
                            
                            # If this is the edge of a tier, build a retaining wall
                            is_tier_edge = (dz == tier_z_min or dz == tier_z_max - 1)
                            if is_tier_edge and tier > 0:
                                # Extend wall upward to create nice division between tiers
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + dx, tier_y, zaxis + dz),
                                    (xaxis + dx, tier_y + 2, zaxis + dz),
                                    Block(choice(theme_materials["foundation"]))
                                )
            
            # Create floor for this tier
            for dx in range(-width//2, width//2 + 1):
                for dz in range(-length//2, length//2 + 1):
                    tier_z_min = -length//2 + (tier * length // site_plan.get("tiers", 1))
                    tier_z_max = -length//2 + ((tier + 1) * length // site_plan.get("tiers", 1))
                    
                    if tier_z_min <= dz < tier_z_max:
                        ED.placeBlock(
                            (xaxis + dx, tier_y - 1, zaxis + dz),
                            Block(choice(theme_materials["floor"]))
                        )
    
    else:  # standard foundation
        # Find the lowest terrain point under the footprint
        min_height = min([adj["orig_height"] for adj in adjustments.values() if 
                         -width//2 - 1 <= (adj[0] - xaxis) <= width//2 + 1 and 
                         -length//2 - 1 <= (adj[1] - zaxis) <= length//2 + 1])
        
        # Build foundation columns as needed
        for dx in range(-width//2 - 1, width//2 + 2):
            for dz in range(-length//2 - 1, length//2 + 2):
                pos = (xaxis + dx, zaxis + dz)
                
                if pos in adjustments:
                    orig_height = adjustments[pos]["orig_height"]
                    
                    # If terrain is below target height, build up
                    if orig_height < y:
                        # Determine if this is a corner pillar or edge
                        is_corner = (abs(dx) == width//2 + 1 and abs(dz) == length//2 + 1)
                        is_edge = (abs(dx) == width//2 + 1 or abs(dz) == length//2 + 1)
                        
                        # Choose foundation material with some variation
                        if is_corner:
                            material = Block(theme_materials["accent"][0])
                        elif is_edge:
                            material = Block(choice(theme_materials["foundation"]))
                        else:
                            material = Block(choice(theme_materials["foundation"]))
                        
                        # Create foundation column
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, orig_height, zaxis + dz),
                            (xaxis + dx, y - 1, zaxis + dz),
                            material
                        )
                        
                        # Add decorative elements to tall pillars
                        if y - orig_height > 3:
                            # Add a different material in the middle
                            middle_y = orig_height + (y - orig_height) // 2
                            ED.placeBlock(
                                (xaxis + dx, middle_y, zaxis + dz),
                                Block(choice(theme_materials["accent"]))
                            )
        
        # Add floor on top of foundation
        floor_materials = theme_materials["floor"]
        floor_pattern_type = choice(["checkered", "bordered", "random"])
        
        for dx in range(-width//2, width//2 + 1):
            for dz in range(-length//2, length//2 + 1):
                if floor_pattern_type == "checkered":
                    material = floor_materials[0] if (dx + dz) % 2 == 0 else floor_materials[1]
                elif floor_pattern_type == "bordered":
                    # Border with different material in center
                    if (abs(dx) >= width//2 - 2 or abs(dz) >= length//2 - 2):
                        material = floor_materials[0]  # Border
                    else:
                        material = floor_materials[1]  # Center
                else:  # random
                    material = floor_materials[0] if random() > 0.2 else floor_materials[1]
                
                ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(material))
    
    # Return the adjustments map for later use
    return adjustments

def build_walls_and_structure(ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials):
    """Build walls with framing and other structural elements"""
    print("Building walls and structure...")
    
    tiers = site_plan.get("tiers", 1)
    wall_materials = theme_materials["walls"]
    trim_materials = theme_materials["trim"]
    
    # Determine if we're building a circular structure (for tower style)
    is_circular = layout.get("is_circular", False)
    
    # Build different wall types based on the building style
    if building_style == "platform":
        # For platform houses, build walls on the elevated platform
        base_y = site_plan.get("base_height", y)
        
        # Build pillars for stilts first
        build_pillars(ED, xaxis, zaxis, layout, site_plan, theme_materials)
        
        # Then build walls
        for dx in range(-width//2, width//2 + 1):
            for dz in range(-length//2, length//2 + 1):
                # Only build walls on the perimeter
                if dx == -width//2 or dx == width//2 or dz == -length//2 or dz == length//2:
                    # Check if there's a door at this position
                    has_door = False
                    for door in layout["doors"]:
                        if door.get("is_entrance", False) and (dx, dz) == (door["x"], door["z"]):
                            has_door = True
                            break
                    
                    if not has_door:
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, base_y, zaxis + dz),
                            (xaxis + dx, base_y + height - 1, zaxis + dz),
                            Block(choice(wall_materials))
                        )
        
        # Add a railing where specified
        for feature in layout["special_features"]:
            if feature.get("type") == "railing":
                x1, z1 = feature.get("x1", -width//2), feature.get("z1", -length//2)
                x2, z2 = feature.get("x2", width//2), feature.get("z2", length//2)
                
                # Build railing posts and connections
                for dx in range(x1, x2 + 1, 2):
                    for dz in [z1, z2]:
                        if dx > x1 and dx < x2:  # Skip corners
                            ED.placeBlock(
                                (xaxis + dx, base_y, zaxis + dz),
                                Block(choice(theme_materials["details"][1]))  # fence
                            )
                
                for dz in range(z1, z2 + 1, 2):
                    for dx in [x1, x2]:
                        if dz > z1 and dz < z2:  # Skip corners
                            ED.placeBlock(
                                (xaxis + dx, base_y, zaxis + dz),
                                Block(choice(theme_materials["details"][1]))  # fence
                            )
    
    elif building_style == "compound":
        # For compound buildings, build multiple separate structures
        for room in layout["rooms"]:
            if room.get("is_separate", False):
                # Get room dimensions
                room_x1, room_z1 = room["x1"], room["z1"]
                room_x2, room_z2 = room["x2"], room["z2"]
                room_width = room_x2 - room_x1
                room_length = room_z2 - room_z1
                
                # Build walls for this room
                for dx in range(room_x1, room_x2 + 1):
                    for dz in range(room_z1, room_z2 + 1):
                        # Only build on perimeter
                        if dx == room_x1 or dx == room_x2 or dz == room_z1 or dz == room_z2:
                            # Check for doors and windows
                            has_opening = False
                            for door in layout["doors"]:
                                if (dx, dz) == (door["x"], door["z"]):
                                    has_opening = True
                                    break
                                    
                            for window in layout["windows"]:
                                if (dx, dz) == (window["x"], window["z"]):
                                    has_opening = True
                                    break
                            
                            # Build wall if no opening
                            if not has_opening:
                                # Use different materials for corners
                                if (dx == room_x1 and dz == room_z1) or (dx == room_x2 and dz == room_z1) or \
                                   (dx == room_x1 and dz == room_z2) or (dx == room_x2 and dz == room_z2):
                                    # Corner post
                                    geo.placeCuboid(
                                        ED,
                                        (xaxis + dx, y, zaxis + dz),
                                        (xaxis + dx, y + height - 1, zaxis + dz),
                                        Block(trim_materials[0], {"axis": "y"})
                                    )
                                else:
                                    # Regular wall
                                    geo.placeCuboid(
                                        ED,
                                        (xaxis + dx, y, zaxis + dz),
                                        (xaxis + dx, y + height - 1, zaxis + dz),
                                        Block(choice(wall_materials))
                                    )
                
                # Add framing to the building
                for h in [0, height // 2, height - 1]:
                    for x in range(room_x1, room_x2 + 1):
                        ED.placeBlock(
                            (xaxis + x, y + h, zaxis + room_z1),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        ED.placeBlock(
                            (xaxis + x, y + h, zaxis + room_z2),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        
                    for z in range(room_z1, room_z2 + 1):
                        ED.placeBlock(
                            (xaxis + room_x1, y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
                        ED.placeBlock(
                            (xaxis + room_x2, y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
    
    elif building_style == "tower":
        # For circular tower
        if is_circular:
            radius = min(width, length) // 2
            
            # Build circular walls for each tier
            for tier in range(site_plan.get("tiers", 1)):
                tier_y = y
                if tier > 0:
                    tier_y = y + (height * tier)
                
                # Circles for each floor
                for h in range(height):
                    current_y = tier_y + h
                    for angle in range(0, 360, 5):  # 5-degree increments for smoother circle
                        rad = math.radians(angle)
                        dx = int(radius * math.cos(rad))
                        dz = int(radius * math.sin(rad))
                        
                        # Check for doors and windows
                        has_opening = False
                        for door in layout["doors"]:
                            if door.get("tier", 0) == tier and abs(dx - door["x"]) <= 1 and abs(dz - door["z"]) <= 1:
                                has_opening = (current_y - tier_y) < 3  # Door is 2 blocks high
                                break
                                
                        for window in layout["windows"]:
                            if window.get("tier", 0) == tier and abs(dx - window["x"]) <= 1 and abs(dz - window["z"]) <= 1:
                                has_opening = (current_y - tier_y) > 1 and (current_y - tier_y) < 4  # Window position
                                break
                        
                        if not has_opening:
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(choice(wall_materials))
                            )
                
                # Add decorative bands at floor levels
                for angle in range(0, 360, 5):
                    rad = math.radians(angle)
                    dx = int(radius * math.cos(rad))
                    dz = int(radius * math.sin(rad))
                    
                    ED.placeBlock(
                        (xaxis + dx, tier_y, zaxis + dz),
                        Block(choice(theme_materials["accent"]))
                    )
        else:
            # Regular square tower
            # Similar to standard buildings but with multiple tiers
            for tier in range(site_plan.get("tiers", 1)):
                tier_y = y
                if tier > 0:
                    tier_y = y + (height * tier)
                
                # Build perimeter walls for this tier
                for dx in range(-width//2, width//2 + 1):
                    for dz in range(-length//2, length//2 + 1):
                        if dx == -width//2 or dx == width//2 or dz == -length//2 or dz == length//2:
                            # Check for doors and windows in this tier
                            has_opening = False
                            for door in layout["doors"]:
                                if door.get("tier", 0) == tier and (dx, dz) == (door["x"], door["z"]):
                                    has_opening = True
                                    # Build door frame
                                    if dz == door["z"] and ((dx == door["x"] - 1) or (dx == door["x"] + 1)):
                                        geo.placeCuboid(
                                            ED,
                                            (xaxis + dx, tier_y, zaxis + dz),
                                            (xaxis + dx, tier_y + 2, zaxis + dz),
                                            Block(choice(trim_materials))
                                        )
                                    if dx == door["x"] and ((dz == door["z"] - 1) or (dz == door["z"] + 1)):
                                        geo.placeCuboid(
                                            ED,
                                            (xaxis + dx, tier_y, zaxis + dz),
                                            (xaxis + dx, tier_y + 2, zaxis + dz),
                                            Block(choice(trim_materials))
                                        )
                                    break
                                    
                            for window in layout["windows"]:
                                if window.get("tier", 0) == tier and (dx, dz) == (window["x"], window["z"]):
                                    has_opening = True
                                    # Build window frame
                                    if window["facing"] in ["north", "south"]:
                                        geo.placeCuboid(
                                            ED,
                                            (xaxis + dx, tier_y + 1, zaxis + dz),
                                            (xaxis + dx, tier_y + 2, zaxis + dz),
                                            Block(choice(theme_materials["windows"]))
                                        )
                                    else:
                                        geo.placeCuboid(
                                            ED,
                                            (xaxis + dx, tier_y + 1, zaxis + dz),
                                            (xaxis + dx, tier_y + 2, zaxis + dz),
                                            Block(choice(theme_materials["windows"]))
                                        )
                                    break
                            
                            if not has_opening:
                                # Build wall
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + dx, tier_y, zaxis + dz),
                                    (xaxis + dx, tier_y + height - 1, zaxis + dz),
                                    Block(choice(wall_materials))
                                )
                
                # Add corner posts
                for dx in [-width//2, width//2]:
                    for dz in [-length//2, length//2]:
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, tier_y, zaxis + dz),
                            (xaxis + dx, tier_y + height - 1, zaxis + dz),
                            Block(trim_materials[0], {"axis": "y"})
                        )
                
                # Add horizontal beams at top and middle of this tier
                for h in [0, height // 2, height - 1]:
                    for x in range(-width//2 + 1, width//2):
                        ED.placeBlock(
                            (xaxis + x, tier_y + h, zaxis - length//2),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        ED.placeBlock(
                            (xaxis + x, tier_y + h, zaxis + length//2),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        
                    for z in range(-length//2 + 1, length//2):
                        ED.placeBlock(
                            (xaxis - width//2, tier_y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
                        ED.placeBlock(
                            (xaxis + width//2, tier_y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
                
                # Add floor for the next tier if needed
                if tier < tiers - 1:
                    next_tier_y = tier_y + height
                    for dx in range(-width//2 + 1, width//2):
                        for dz in range(-length//2 + 1, length//2):
                            # Create floor for next tier, leaving space for stairs
                            is_stair_area = False
                            for feature in layout["special_features"]:
                                if feature.get("type") == "stairs" and feature.get("to_tier", 0) == tier + 1:
                                    stair_x, stair_z = feature["x"], feature["z"]
                                    # Leave open area around stairs
                                    if abs(dx - stair_x) <= 1 and abs(dz - stair_z) <= 1:
                                        is_stair_area = True
                                        break
                            
                            if not is_stair_area:
                                ED.placeBlock(
                                    (xaxis + dx, next_tier_y - 1, zaxis + dz),
                                    Block(choice(theme_materials["floor"]))
                                )
    
    elif building_style == "courtyard":
        # For courtyard structure, build around the open central area
        courtyard_area = None
        for feature in layout["special_features"]:
            if feature.get("type") == "courtyard":
                courtyard_area = feature
                break
                
        if courtyard_area:
            courtyard_x1, courtyard_z1 = courtyard_area["x1"], courtyard_area["z1"]
            courtyard_x2, courtyard_z2 = courtyard_area["x2"], courtyard_area["z2"]
            
            # Build perimeter walls and walls around courtyard
            for dx in range(-width//2, width//2 + 1):
                for dz in range(-length//2, length//2 + 1):
                    is_outer_perimeter = (dx == -width//2 or dx == width//2 or dz == -length//2 or dz == length//2)
                    is_courtyard_perimeter = (
                        (dx == courtyard_x1 or dx == courtyard_x2) and courtyard_z1 <= dz <= courtyard_z2 or
                        (dz == courtyard_z1 or dz == courtyard_z2) and courtyard_x1 <= dx <= courtyard_x2
                    )
                    
                    if is_outer_perimeter or is_courtyard_perimeter:
                        # Check for doors and windows
                        has_opening = False
                        for door in layout["doors"]:
                            if (dx, dz) == (door["x"], door["z"]):
                                has_opening = True
                                break
                                
                        for window in layout["windows"]:
                            if (dx, dz) == (window["x"], window["z"]):
                                has_opening = True
                                break
                        
                        if not has_opening:
                            # Build wall
                            geo.placeCuboid(
                                ED,
                                (xaxis + dx, y, zaxis + dz),
                                (xaxis + dx, y + height - 1, zaxis + dz),
                                Block(choice(wall_materials))
                            )
            
            # Add corner posts
            for dx in [-width//2, width//2, courtyard_x1, courtyard_x2]:
                for dz in [-length//2, length//2, courtyard_z1, courtyard_z2]:
                    # Skip non-corner positions of the courtyard
                    if (dx in [courtyard_x1, courtyard_x2] and dz in [courtyard_z1, courtyard_z2]):
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, y, zaxis + dz),
                            (xaxis + dx, y + height - 1, zaxis + dz),
                            Block(trim_materials[0], {"axis": "y"})
                        )
                    elif dx in [-width//2, width//2] and dz in [-length//2, length//2]:
                        geo.placeCuboid(
                            ED,
                            (xaxis + dx, y, zaxis + dz),
                            (xaxis + dx, y + height - 1, zaxis + dz),
                            Block(trim_materials[0], {"axis": "y"})
                        )
            
            # Add horizontal beams
            for h in [0, height // 2, height - 1]:
                # Exterior perimeter
                for x in range(-width//2 + 1, width//2):
                    if not (courtyard_x1 < x < courtyard_x2 and (courtyard_z1 <= -length//2 or courtyard_z2 >= length//2)):
                        ED.placeBlock(
                            (xaxis + x, y + h, zaxis - length//2),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        ED.placeBlock(
                            (xaxis + x, y + h, zaxis + length//2),
                            Block(trim_materials[0], {"axis": "x"})
                        )
                        
                for z in range(-length//2 + 1, length//2):
                    if not (courtyard_z1 < z < courtyard_z2 and (courtyard_x1 <= -width//2 or courtyard_x2 >= width//2)):
                        ED.placeBlock(
                            (xaxis - width//2, y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
                        ED.placeBlock(
                            (xaxis + width//2, y + h, zaxis + z),
                            Block(trim_materials[0], {"axis": "z"})
                        )
                
                # Courtyard perimeter
                for x in range(courtyard_x1 + 1, courtyard_x2):
                    ED.placeBlock(
                        (xaxis + x, y + h, zaxis + courtyard_z1),
                        Block(trim_materials[0], {"axis": "x"})
                    )
                    ED.placeBlock(
                        (xaxis + x, y + h, zaxis + courtyard_z2),
                        Block(trim_materials[0], {"axis": "x"})
                    )
                    
                for z in range(courtyard_z1 + 1, courtyard_z2):
                    ED.placeBlock(
                        (xaxis + courtyard_x1, y + h, zaxis + z),
                        Block(trim_materials[0], {"axis": "z"})
                    )
                    ED.placeBlock(
                        (xaxis + courtyard_x2, y + h, zaxis + z),
                        Block(trim_materials[0], {"axis": "z"})
                    )
            
            # Add courtyard floor - make it different from the main floor
            for dx in range(courtyard_x1 + 1, courtyard_x2):
                for dz in range(courtyard_z1 + 1, courtyard_z2):
                    if (dx + dz) % 2 == 0:
                        ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(choice(theme_materials["accent"])))
                    else:
                        ED.placeBlock((xaxis + dx, y - 1, zaxis + dz), Block(choice(theme_materials["floor"])))
    
    else:  # Default wall building (cottage, longhouse, split-level)
        # Build walls for each tier
        for tier in range(site_plan.get("tiers", 1)):
            tier_y = y
            if tier > 0:
                tier_y = site_plan.get("multi_level_heights", [y])[tier]
            
            # Find rooms for this tier
            tier_rooms = [room for room in layout["rooms"] if room.get("tier", 0) == tier and not room.get("is_sub_room", False)]
            
            # If no specific rooms for tier, use default size
            if not tier_rooms:
                tier_x_min, tier_z_min = -width//2, -length//2
                tier_x_max, tier_z_max = width//2, length//2
            else:
                # Find bounds of all rooms in this tier
                tier_x_min = min([room["x1"] for room in tier_rooms])
                tier_x_max = max([room["x2"] for room in tier_rooms])
                tier_z_min = min([room["z1"] for room in tier_rooms])
                tier_z_max = max([room["z2"] for room in tier_rooms])
            
            # Build perimeter walls
            for dx in range(tier_x_min, tier_x_max + 1):
                for dz in range(tier_z_min, tier_z_max + 1):
                    is_perimeter = (dx == tier_x_min or dx == tier_x_max or dz == tier_z_min or dz == tier_z_max)
                    
                    if is_perimeter:
                        # Check for openings (doors, windows)
                        has_opening = False
                        for door in layout["doors"]:
                            if door.get("tier", 0) == tier and (dx, dz) == (door["x"], door["z"]):
                                has_opening = True
                                break
                                
                        for window in layout["windows"]:
                            if window.get("tier", 0) == tier and (dx, dz) == (window["x"], window["z"]):
                                has_opening = True
                                
                                # Build decorative window frame
                                if "facing" in window:
                                    frame_material = Block(trim_materials[1])
                                    if window["facing"] == "north" or window["facing"] == "south":
                                        ED.placeBlock((xaxis + dx, tier_y + 1, zaxis + dz), Block(theme_materials["windows"][0]))
                                        ED.placeBlock((xaxis + dx, tier_y + 2, zaxis + dz), Block(theme_materials["windows"][0]))
                                        
                                        # Window frame
                                        ED.placeBlock((xaxis + dx, tier_y, zaxis + dz), frame_material)
                                        ED.placeBlock((xaxis + dx, tier_y + 3, zaxis + dz), frame_material)
                                    else:  # east or west
                                        ED.placeBlock((xaxis + dx, tier_y + 1, zaxis + dz), Block(theme_materials["windows"][0]))
                                        ED.placeBlock((xaxis + dx, tier_y + 2, zaxis + dz), Block(theme_materials["windows"][0]))
                                        
                                        # Window frame
                                        ED.placeBlock((xaxis + dx, tier_y, zaxis + dz), frame_material)
                                        ED.placeBlock((xaxis + dx, tier_y + 3, zaxis + dz), frame_material)
                                break
                        
                        if not has_opening:
                            # Build wall
                            if (dx == tier_x_min and dz == tier_z_min) or \
                               (dx == tier_x_max and dz == tier_z_min) or \
                               (dx == tier_x_min and dz == tier_z_max) or \
                               (dx == tier_x_max and dz == tier_z_max):
                                # Corner post
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + dx, tier_y, zaxis + dz),
                                    (xaxis + dx, tier_y + height - 1, zaxis + dz),
                                    Block(trim_materials[0], {"axis": "y"})
                                )
                            else:
                                # Regular wall
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + dx, tier_y, zaxis + dz),
                                    (xaxis + dx, tier_y + height - 1, zaxis + dz),
                                    Block(choice(wall_materials))
                                )
            
            # Add horizontal beams
            for h in [0, height // 2, height - 1]:
                # Along x-axis (north and south walls)
                for x in range(tier_x_min + 1, tier_x_max):
                    ED.placeBlock(
                        (xaxis + x, tier_y + h, zaxis + tier_z_min),
                        Block(trim_materials[0], {"axis": "x"})
                    )
                    ED.placeBlock(
                        (xaxis + x, tier_y + h, zaxis + tier_z_max),
                        Block(trim_materials[0], {"axis": "x"})
                    )
                
                # Along z-axis (east and west walls)
                for z in range(tier_z_min + 1, tier_z_max):
                    ED.placeBlock(
                        (xaxis + tier_x_min, tier_y + h, zaxis + z),
                        Block(trim_materials[0], {"axis": "z"})
                    )
                    ED.placeBlock(
                        (xaxis + tier_x_max, tier_y + h, zaxis + z),
                        Block(trim_materials[0], {"axis": "z"})
                    )
            
            # Build interior walls if specified
            for wall in layout["walls"]:
                wall_tier = wall.get("tier", 0)
                if wall_tier == tier:
                    x1, z1 = wall["x1"], wall["z1"]
                    x2, z2 = wall["x2"], wall["z2"]
                    
                    if x1 == x2:  # Vertical wall (along z-axis)
                        for z in range(z1, z2 + 1):
                            # Check for doors in this wall
                            has_door = False
                            for door in layout["doors"]:
                                if door.get("tier", 0) == tier and door["x"] == x1 and door["z"] == z:
                                    has_door = True
                                    break
                            
                            if not has_door:
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + x1, tier_y, zaxis + z),
                                    (xaxis + x1, tier_y + height - 1, zaxis + z),
                                    Block(choice(wall_materials))
                                )
                    
                    elif z1 == z2:  # Horizontal wall (along x-axis)
                        for x in range(x1, x2 + 1):
                            # Check for doors in this wall
                            has_door = False
                            for door in layout["doors"]:
                                if door.get("tier", 0) == tier and door["x"] == x and door["z"] == z1:
                                    has_door = True
                                    break
                            
                            if not has_door:
                                geo.placeCuboid(
                                    ED,
                                    (xaxis + x, tier_y, zaxis + z1),
                                    (xaxis + x, tier_y + height - 1, zaxis + z1),
                                    Block(choice(wall_materials))
                                )
            
            # Add doors
            for door in layout["doors"]:
                door_tier = door.get("tier", 0)
                if door_tier == tier:
                    door_x, door_z = door["x"], door["z"]
                    facing = door["facing"]
                    is_entrance = door.get("is_entrance", False)
                    
                    # Position door block
                    door_block = Block("oak_door", {"facing": facing, "half": "lower"})
                    ED.placeBlock((xaxis + door_x, tier_y, zaxis + door_z), door_block)
                    
                    # Upper half of the door
                    door_block_upper = Block("oak_door", {"facing": facing, "half": "upper"})
                    ED.placeBlock((xaxis + door_x, tier_y + 1, zaxis + door_z), door_block_upper)
                    
                    # If it's an entrance, add some decorative elements
                    if is_entrance:
                        # Door frame
                        if facing == "north" or facing == "south":
                            ED.placeBlock((xaxis + door_x - 1, tier_y, zaxis + door_z), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x + 1, tier_y, zaxis + door_z), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x - 1, tier_y + 1, zaxis + door_z), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x + 1, tier_y + 1, zaxis + door_z), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x, tier_y + 2, zaxis + door_z), Block(trim_materials[1]))
                        else:  # east or west
                            ED.placeBlock((xaxis + door_x, tier_y, zaxis + door_z - 1), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x, tier_y, zaxis + door_z + 1), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x, tier_y + 1, zaxis + door_z - 1), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x, tier_y + 1, zaxis + door_z + 1), Block(trim_materials[1]))
                            ED.placeBlock((xaxis + door_x, tier_y + 2, zaxis + door_z), Block(trim_materials[1]))
                        
                        # Lantern beside the entrance
                        if facing == "north":
                            ED.placeBlock((xaxis + door_x + 1, tier_y + 2, zaxis + door_z), Block("lantern"))
                        elif facing == "south":
                            ED.placeBlock((xaxis + door_x - 1, tier_y + 2, zaxis + door_z), Block("lantern"))
                        elif facing == "east":
                            ED.placeBlock((xaxis + door_x, tier_y + 2, zaxis + door_z + 1), Block("lantern"))
                        else:  # west
                            ED.placeBlock((xaxis + door_x, tier_y + 2, zaxis + door_z - 1), Block("lantern"))
                        
                        # Add steps if needed
                        if tier_y > y:
                            # Calculate number of steps needed
                            steps_needed = tier_y - y
                            for step in range(steps_needed):
                                step_y = y + step
                                
                                # Position based on facing direction
                                if facing == "north":
                                    step_z = door_z + step + 1
                                    for dx in range(-1, 2):
                                        ED.placeBlock(
                                            (xaxis + door_x + dx, step_y, zaxis + step_z),
                                            Block("stone_brick_stairs", {"facing": "south"})
                                        )
                                elif facing == "south":
                                    step_z = door_z - step - 1
                                    for dx in range(-1, 2):
                                        ED.placeBlock(
                                            (xaxis + door_x + dx, step_y, zaxis + step_z),
                                            Block("stone_brick_stairs", {"facing": "north"})
                                        )
                                elif facing == "east":
                                    step_x = door_x - step - 1
                                    for dz in range(-1, 2):
                                        ED.placeBlock(
                                            (xaxis + step_x, step_y, zaxis + door_z + dz),
                                            Block("stone_brick_stairs", {"facing": "east"})
                                        )
                                else:  # west
                                    step_x = door_x + step + 1
                                    for dz in range(-1, 2):
                                        ED.placeBlock(
                                            (xaxis + step_x, step_y, zaxis + door_z + dz),
                                            Block("stone_brick_stairs", {"facing": "west"})
                                        )

def build_pillars(ED, xaxis, zaxis, layout, site_plan, theme_materials):
    """Build pillars or stilts for elevated structures"""
    if site_plan.get("foundation_mode") != "stilts":
        return
        
    print("Building structural pillars...")
    
    # Get terrain heights
    heights = np.array(WORLDSLICE.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
    base_y = site_plan.get("base_height", 0)  # Platform height
    
    # Find the key structural points that need pillars
    stilt_positions = []
    
    # First, add corners
    stilt_positions.extend([
        (-layout["outer_width"]//2, -layout["outer_length"]//2),
        (-layout["outer_width"]//2, layout["outer_length"]//2),
        (layout["outer_width"]//2, -layout["outer_length"]//2),
        (layout["outer_width"]//2, layout["outer_length"]//2)
    ])
    
    # Add intermediate pillars if the span is large
    if layout["outer_width"] > 8:
        for z in [-layout["outer_length"]//2, layout["outer_length"]//2]:
            stilt_positions.append((0, z))
    
    if layout["outer_length"] > 8:
        for x in [-layout["outer_width"]//2, layout["outer_width"]//2]:
            stilt_positions.append((x, 0))
    
    # Add more intermediate pillars for very large structures
    if layout["outer_width"] > 16 or layout["outer_length"] > 16:
        for x in range(-layout["outer_width"]//2, layout["outer_width"]//2 + 1, 6):
            for z in range(-layout["outer_length"]//2, layout["outer_length"]//2 + 1, 6):
                if (x, z) not in stilt_positions:
                    stilt_positions.append((x, z))
    
    # Add pillars wherever there are special structural features
    for feature in layout["special_features"]:
        if feature.get("type") == "stairs_down":
            stilt_positions.append((feature["x"], feature["z"]))
        elif feature.get("type") == "deck":
            deck_x1, deck_z1 = feature.get("x1", 0), feature.get("z1", 0)
            deck_x2, deck_z2 = feature.get("x2", 0), feature.get("z2", 0)
            stilt_positions.append((deck_x1, deck_z1))
            stilt_positions.append((deck_x1, deck_z2))
            stilt_positions.append((deck_x2, deck_z1))
            stilt_positions.append((deck_x2, deck_z2))
    
    # Build each pillar
    for dx, dz in stilt_positions:
        local_x = xaxis + dx - STARTX
        local_z = zaxis + dz - STARTZ
        
        if 0 <= local_x < heights.shape[0] and 0 <= local_z < heights.shape[1]:
            ground_y = heights[local_x, local_z]
            
            # Build pillar from ground to platform
            pillar_material = choice(theme_materials["foundation"])
            trim_material = choice(theme_materials["trim"])
            
            # Main pillar
            geo.placeCuboid(
                ED,
                (xaxis + dx, ground_y, zaxis + dz),
                (xaxis + dx, base_y - 1, zaxis + dz),
                Block(pillar_material)
            )
            
            # Add decorative bands every few blocks
            for y_pos in range(ground_y + 2, base_y - 1, 4):
                ED.placeBlock(
                    (xaxis + dx, y_pos, zaxis + dz),
                    Block(trim_material, {"axis": "y"})
                )
            
            # Add cross-bracing to nearby pillars
            if dx != 0 or dz != 0:  # Skip for the center pillar
                # Find closest pillar toward center
                center_dist_x = abs(dx)
                center_dist_z = abs(dz)
                
                brace_y = ground_y + (base_y - ground_y) // 2
                
                if center_dist_x >= center_dist_z:
                    # Brace along x-axis
                    step_x = 1 if dx < 0 else -1
                    for x in range(dx + step_x, 0, step_x):
                        if abs(x - dx) <= 5:  # Limit brace length
                            ED.placeBlock(
                                (xaxis + x, brace_y, zaxis + dz),
                                Block(trim_material, {"axis": "x"})
                            )
                else:
                    # Brace along z-axis
                    step_z = 1 if dz < 0 else -1
                    for z in range(dz + step_z, 0, step_z):
                        if abs(z - dz) <= 5:  # Limit brace length
                            ED.placeBlock(
                                (xaxis + dx, brace_y, zaxis + z),
                                Block(trim_material, {"axis": "z"})
                            )

def build_roof(ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials):
    """Build roof with style-appropriate design"""
    print(f"Building {building_style} style roof...")
    
    tiers = site_plan.get("tiers", 1)
    roof_material = theme_materials["roof"][0]
    roof_trim = theme_materials["trim"][0]
    
    # Determine appropriate roof style based on building style
    if building_style == "tower":
        # Conical or pyramid roof for tower
        is_circular = layout.get("is_circular", False)
        top_tier_y = y + (height * (tiers - 1))
        
        if is_circular:
            # Conical roof for circular tower
            radius = min(width, length) // 2
            cone_height = radius + 2
            
            for h in range(cone_height):
                current_radius = radius * (1 - h/cone_height)
                current_y = top_tier_y + height + h
                
                for angle in range(0, 360, 5):
                    rad = math.radians(angle)
                    dx = int(current_radius * math.cos(rad))
                    dz = int(current_radius * math.sin(rad))
                    
                    if h == 0:
                        # First layer is normal blocks
                        ED.placeBlock(
                            (xaxis + dx, current_y, zaxis + dz),
                            Block(theme_materials["accent"][0])
                        )
                    else:
                        # Determine facing direction for stairs
                        facing = "north"  # Default
                        if abs(dx) > abs(dz):
                            if dx > 0:
                                facing = "west"
                            else:
                                facing = "east"
                        else:
                            if dz > 0:
                                facing = "north"
                            else:
                                facing = "south"
                        
                        # Place stairs to create smooth cone
                        ED.placeBlock(
                            (xaxis + dx, current_y, zaxis + dz),
                            Block(roof_material, {"facing": facing, "half": "bottom"})
                        )
            
            # Add spire at top
            geo.placeCuboid(
                ED,
                (xaxis, top_tier_y + height + cone_height, zaxis),
                (xaxis, top_tier_y + height + cone_height + 3, zaxis),
                Block(roof_trim, {"axis": "y"})
            )
            
            # Add a lantern or other decorative element
            ED.placeBlock(
                (xaxis, top_tier_y + height + cone_height + 4, zaxis),
                Block("lantern")
            )
        
        else:
            # Pyramid roof for square tower
            roof_height = min(width, length) // 2 + 2
            
            for h in range(roof_height):
                layer_width = width - (h * 2)
                layer_length = length - (h * 2)
                
                if layer_width <= 0 or layer_length <= 0:
                    break
                
                current_y = top_tier_y + height + h
                
                for dx in range(-layer_width//2, layer_width//2 + 1):
                    for dz in range(-layer_length//2, layer_length//2 + 1):
                        if dx == -layer_width//2 or dx == layer_width//2 or dz == -layer_length//2 or dz == layer_length//2:
                            # Determine facing for stairs on the edge
                            facing = "north"  # Default
                            if dx == -layer_width//2:
                                facing = "east"
                            elif dx == layer_width//2:
                                facing = "west"
                            elif dz == -layer_length//2:
                                facing = "north"
                            elif dz == layer_length//2:
                                facing = "south"
                            
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(roof_material, {"facing": facing})
                            )
                        elif h > 0:
                            # Fill interior
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )
            
            # Add a decorative spire at the top
            remaining_height = 3
            geo.placeCuboid(
                ED,
                (xaxis, top_tier_y + height + roof_height, zaxis),
                (xaxis, top_tier_y + height + roof_height + remaining_height, zaxis),
                Block(roof_trim, {"axis": "y"})
            )
            
            # Add a lantern at the very top
            ED.placeBlock(
                (xaxis, top_tier_y + height + roof_height + remaining_height + 1, zaxis),
                Block("lantern")
            )
    
    elif building_style == "platform":
        # Simple roof for stilt house - either a-frame or flat
        a_frame_roof = random() > 0.3  # 70% chance of A-frame roof
        base_y = site_plan.get("base_height", y)
        
        if a_frame_roof:
            # A-frame/gabled roof
            max_height = width//2 + 2
            
            # Build the sloped roof
            for h in range(max_height + 1):
                current_y = base_y + height - 1 + h
                
                for dz in range(-length//2, length//2 + 1):
                    if h == max_height:  # Ridge beam at the top
                        ED.placeBlock(
                            (xaxis, current_y, zaxis + dz),
                            Block(roof_trim, {"axis": "z"})
                        )
                    else:
                        # West-facing (east side)
                        for dx in range(h + 1):
                            if dx == h:  # Outer edge gets stairs
                                ED.placeBlock(
                                    (xaxis + dx, current_y, zaxis + dz),
                                    Block(roof_material, {"facing": "west"})
                                )
                            elif dx > 0:  # Interior gets solid blocks
                                ED.placeBlock(
                                    (xaxis + dx, current_y, zaxis + dz),
                                    Block(theme_materials["roof"][1])
                                )
                        
                        # East-facing (west side)
                        for dx in range(h + 1):
                            if dx == h:  # Outer edge gets stairs
                                ED.placeBlock(
                                    (xaxis - dx, current_y, zaxis + dz),
                                    Block(roof_material, {"facing": "east"})
                                )
                            elif dx > 0:  # Interior gets solid blocks
                                ED.placeBlock(
                                    (xaxis - dx, current_y, zaxis + dz),
                                    Block(theme_materials["roof"][1])
                                )
        else:
            # Simple flat roof with small edge
            for dx in range(-width//2 - 1, width//2 + 2):
                for dz in range(-length//2 - 1, length//2 + 2):
                    roof_y = base_y + height - 1
                    
                    if dx == -width//2 - 1 or dx == width//2 + 1 or dz == -length//2 - 1 or dz == length//2 + 1:
                        # Edge trim
                        ED.placeBlock(
                            (xaxis + dx, roof_y, zaxis + dz),
                            Block(theme_materials["trim"][1])
                        )
                    else:
                        # Main roof
                        ED.placeBlock(
                            (xaxis + dx, roof_y, zaxis + dz),
                            Block(theme_materials["floor"][0])
                        )
            
            # Add some railings/low walls around the roof
            for dx in range(-width//2, width//2 + 1, 2):
                ED.placeBlock((xaxis + dx, base_y + height, zaxis - length//2), Block(theme_materials["details"][1]))
                ED.placeBlock((xaxis + dx, base_y + height, zaxis + length//2), Block(theme_materials["details"][1]))
            
            for dz in range(-length//2, length//2 + 1, 2):
                ED.placeBlock((xaxis - width//2, base_y + height, zaxis + dz), Block(theme_materials["details"][1]))
                ED.placeBlock((xaxis + width//2, base_y + height, zaxis + dz), Block(theme_materials["details"][1]))
    
    elif building_style == "compound":
        # Separate roof for each building
        for room in layout["rooms"]:
            if room.get("is_separate", False):
                # Get room dimensions
                room_x1, room_z1 = room["x1"], room["z1"]
                room_x2, room_z2 = room["x2"], room["z2"]
                room_width = room_x2 - room_x1 + 1
                room_length = room_z2 - room_z1 + 1
                room_center_x = (room_x1 + room_x2) // 2
                room_center_z = (room_z1 + room_z2) // 2
                
                # Simple gabled roof
                max_height = room_width//2 + 1
                
                # Add roof
                for h in range(max_height):
                    current_y = y + height - 1 + h
                    remaining_width = room_width - (h * 2)
                    
                    if remaining_width <= 0:
                        break
                    
                    for dz in range(room_z1, room_z2 + 1):
                        for dx in range(max(room_x1, room_center_x - remaining_width//2), 
                                        min(room_x2 + 1, room_center_x + remaining_width//2 + 1)):
                            
                            if dx == room_center_x - remaining_width//2 or dx == room_center_x + remaining_width//2:
                                # Edge blocks get stairs
                                facing = "east" if dx == room_center_x - remaining_width//2 else "west"
                                ED.placeBlock(
                                    (xaxis + dx, current_y, zaxis + dz),
                                    Block(roof_material, {"facing": facing})
                                )
                            else:
                                # Interior fills with solid blocks
                                ED.placeBlock(
                                    (xaxis + dx, current_y, zaxis + dz),
                                    Block(theme_materials["roof"][1])
                                )
                
                # Add decorative elements
                if room["name"] == "main_building":
                    # Add a chimney
                    chimney_x = room_center_x + room_width//4
                    chimney_z = room_center_z
                    
                    geo.placeCuboid(
                        ED,
                        (xaxis + chimney_x, y, zaxis + chimney_z),
                        (xaxis + chimney_x, y + height + max_height + 1, zaxis + chimney_z),
                        Block(choice(theme_materials["accent"]))
                    )
                    
                    # Add smoke effect
                    ED.placeBlock(
                        (xaxis + chimney_x, y + height + max_height + 2, zaxis + chimney_z),
                        Block("campfire", {"lit": "true"})
                    )
                    
                    # Add some decoration at the roof ends
                    ED.placeBlock(
                        (xaxis + room_center_x, y + height + max_height - 1, zaxis + room_z1 - 1),
                        Block(roof_trim)
                    )
                    ED.placeBlock(
                        (xaxis + room_center_x, y + height + max_height - 1, zaxis + room_z2 + 1),
                        Block(roof_trim)
                    )
    
    elif building_style == "courtyard":
        # Find courtyard boundaries
        courtyard_area = None
        for feature in layout["special_features"]:
            if feature.get("type") == "courtyard":
                courtyard_area = feature
                break
        
        if courtyard_area:
            courtyard_x1, courtyard_z1 = courtyard_area["x1"], courtyard_area["z1"]
            courtyard_x2, courtyard_z2 = courtyard_area["x2"], courtyard_area["z2"]
            
            # For each wing around the courtyard
            # North wing
            build_sloped_roof_section(
                ED, xaxis, zaxis, y + height - 1,
                -width//2, courtyard_x1, courtyard_z2, length//2,
                "north", theme_materials
            )
            
            # South wing
            build_sloped_roof_section(
                ED, xaxis, zaxis, y + height - 1,
                -width//2, courtyard_x1, -length//2, courtyard_z1,
                "south", theme_materials
            )
            
            # East wing
            build_sloped_roof_section(
                ED, xaxis, zaxis, y + height - 1,
                courtyard_x2, width//2, courtyard_z1, courtyard_z2,
                "east", theme_materials
            )
            
            # West wing
            build_sloped_roof_section(
                ED, xaxis, zaxis, y + height - 1,
                -width//2, courtyard_x1, courtyard_z1, courtyard_z2,
                "west", theme_materials
            )
    
    else:  # Default roof for cottage, longhouse, split-level
        for tier in range(tiers):
            tier_y = y
            if tier > 0:
                tier_y = site_plan.get("multi_level_heights", [y])[tier]
            
            # Find rooms for this tier
            tier_rooms = [room for room in layout["rooms"] if room.get("tier", 0) == tier and not room.get("is_sub_room", False)]
            
            # If no specific rooms for tier, use default size
            if not tier_rooms:
                tier_x_min, tier_z_min = -width//2, -length//2
                tier_x_max, tier_z_max = width//2, length//2
                tier_width = width
                tier_length = length
            else:
                # Find bounds of all rooms in this tier
                tier_x_min = min([room["x1"] for room in tier_rooms])
                tier_x_max = max([room["x2"] for room in tier_rooms])
                tier_z_min = min([room["z1"] for room in tier_rooms])
                tier_z_max = max([room["z2"] for room in tier_rooms])
                tier_width = tier_x_max - tier_x_min + 1
                tier_length = tier_z_max - tier_z_min + 1
            
            # Build sloped roof
            if building_style == "longhouse":
                # Longhouse gets a roof that slopes along the short axis
                if tier_length > tier_width:
                    # Roof slopes from center ridge along width
                    max_height = tier_width//2 + 1
                    
                    # Build the roof
                    for h in range(max_height):
                        current_y = tier_y + height - 1 + h
                        
                        for dz in range(tier_z_min, tier_z_max + 1):
                            if h == max_height - 1:  # Ridge beam
                                ED.placeBlock(
                                    (xaxis, current_y, zaxis + dz),
                                    Block(roof_trim, {"axis": "z"})
                                )
                            else:
                                # West-facing side (east slope)
                                for dx in range(tier_x_min + h, 0):
                                    if dx == tier_x_min + h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "west"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                                
                                # East-facing side (west slope)
                                for dx in range(0, tier_x_max - h + 1):
                                    if dx == tier_x_max - h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "east"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                    
                    # Add decorative gable ends
                    for h in range(max_height):
                        current_y = tier_y + height - 1 + h
                        for dx in range(tier_x_min + h, tier_x_max - h + 1):
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + tier_z_min - 1),
                                Block(theme_materials["trim"][1])
                            )
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + tier_z_max + 1),
                                Block(theme_materials["trim"][1])
                            )
                else:
                    # Roof slopes from center ridge along length
                    max_height = tier_length//2 + 1
                    
                    # Build the roof
                    for h in range(max_height):
                        current_y = tier_y + height - 1 + h
                        
                        for dx in range(tier_x_min, tier_x_max + 1):
                            if h == max_height - 1:  # Ridge beam
                                ED.placeBlock(
                                    (xaxis + dx, current_y, zaxis),
                                    Block(roof_trim, {"axis": "x"})
                                )
                            else:
                                # North-facing side (south slope)
                                for dz in range(tier_z_min + h, 0):
                                    if dz == tier_z_min + h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "north"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                                
                                # South-facing side (north slope)
                                for dz in range(0, tier_z_max - h + 1):
                                    if dz == tier_z_max - h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "south"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                    
                    # Add decorative gable ends
                    for h in range(max_height):
                        current_y = tier_y + height - 1 + h
                        for dz in range(tier_z_min + h, tier_z_max - h + 1):
                            ED.placeBlock(
                                (xaxis + tier_x_min - 1, current_y, zaxis + dz),
                                Block(theme_materials["trim"][1])
                            )
                            ED.placeBlock(
                                (xaxis + tier_x_max + 1, current_y, zaxis + dz),
                                Block(theme_materials["trim"][1])
                            )
            
            else:  # cottage and split-level
                # Simple gabled roof - slope along width
                max_height = tier_width//2 + 1
                
                # Build the roof
                for h in range(max_height):
                    current_y = tier_y + height - 1 + h
                    
                    for dz in range(tier_z_min - 1, tier_z_max + 2):
                        if h == max_height - 1:  # Ridge beam
                            ED.placeBlock(
                                (xaxis, current_y, zaxis + dz),
                                Block(roof_trim, {"axis": "z"})
                            )
                        else:
                            # West-facing side (east slope)
                            for dx in range(max(-width//2, tier_x_min - 1), 1):
                                if abs(dx) >= max_height - h:
                                    if abs(dx) == max_height - h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "west"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                            
                            # East-facing side (west slope)
                            for dx in range(0, min(width//2, tier_x_max + 1) + 1):
                                if dx >= max_height - h:
                                    if dx == max_height - h:  # Edge
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(roof_material, {"facing": "east"})
                                        )
                                    else:  # Fill
                                        ED.placeBlock(
                                            (xaxis + dx, current_y, zaxis + dz),
                                            Block(theme_materials["roof"][1])
                                        )
                
                # Add roof extensions at gable ends
                for tier_end_z in [tier_z_min - 1, tier_z_max + 1]:
                    for h in range(1, max_height):
                        current_y = tier_y + height - 1 + h
                        
                        for dx in range(-max_height + h, max_height - h + 1):
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + tier_end_z),
                                Block(theme_materials["trim"][1])
                            )

def build_sloped_roof_section(ED, xaxis, zaxis, base_y, x1, x2, z1, z2, slope_direction, theme_materials):
    """Helper function to build sloped roof section for complex buildings"""
    roof_material = theme_materials["roof"][0]
    roof_trim = theme_materials["trim"][0]
    
    section_width = x2 - x1 + 1
    section_length = z2 - z1 + 1
    
    if slope_direction in ["north", "south"]:
        # Slope runs along z-axis
        max_height = section_length // 2 + 1
        
        for h in range(max_height):
            current_y = base_y + h
            
            for dx in range(x1, x2 + 1):
                if slope_direction == "south":
                    # North to South slope
                    for dz in range(z1, z1 + max_height):
                        if dz - z1 == h:
                            # Edge gets stairs
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(roof_material, {"facing": "south"})
                            )
                        elif dz - z1 < h:
                            # Interior gets full blocks
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )
                else:  # "north"
                    # South to North slope
                    for dz in range(z2 - max_height + 1, z2 + 1):
                        if z2 - dz == h:
                            # Edge gets stairs
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(roof_material, {"facing": "north"})
                            )
                        elif z2 - dz < h:
                            # Interior gets full blocks
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )
    
    else:  # "east" or "west"
        # Slope runs along x-axis
        max_height = section_width // 2 + 1
        
        for h in range(max_height):
            current_y = base_y + h
            
            for dz in range(z1, z2 + 1):
                if slope_direction == "east":
                    # West to East slope
                    for dx in range(x1, x1 + max_height):
                        if dx - x1 == h:
                            # Edge gets stairs
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(roof_material, {"facing": "east"})
                            )
                        elif dx - x1 < h:
                            # Interior gets full blocks
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )
                else:  # "west"
                    # East to West slope
                    for dx in range(x2 - max_height + 1, x2 + 1):
                        if x2 - dx == h:
                            # Edge gets stairs
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(roof_material, {"facing": "west"})
                            )
                        elif x2 - dx < h:
                            # Interior gets full blocks
                            ED.placeBlock(
                                (xaxis + dx, current_y, zaxis + dz),
                                Block(theme_materials["roof"][1])
                            )

def add_interior_details(ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials):
    """Add interior details including furniture and decorations"""
    print("Adding interior details...")
    
    tiers = site_plan.get("tiers", 1)
    
    # Process special features
    for feature in layout["special_features"]:
        feature_type = feature.get("type", "")
        feature_tier = feature.get("tier", 0)
        tier_y = y
        
        if feature_tier > 0 and feature_tier < len(site_plan.get("multi_level_heights", [y])):
            tier_y = site_plan.get("multi_level_heights")[feature_tier]
        elif building_style == "platform" and site_plan.get("base_height"):
            tier_y = site_plan.get("base_height")
        
        if feature_type == "fireplace":
            build_fireplace(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "hearth":
            build_hearth(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "table":
            length = feature.get("length", 3)
            build_table(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, length, theme_materials)
        
        elif feature_type == "bookshelf":
            build_bookshelf(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "stairs":
            if "to_tier" in feature and feature["to_tier"] > 0:
                dest_y = site_plan.get("multi_level_heights", [y, y + height])[feature["to_tier"]]
                build_interior_stairs(
                    ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, 
                    dest_y - tier_y, feature["facing"], theme_materials
                )
        
        elif feature_type == "stairs_down":
            if "length" in feature:
                build_exterior_stairs(
                    ED, xaxis + feature["x"], zaxis + feature["z"], tier_y,
                    feature["length"], feature["facing"], theme_materials
                )
        
        elif feature_type == "well":
            build_well(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "garden":
            build_garden_feature(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "bed":
            build_bed(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "storage":
            build_storage(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "kitchen":
            build_kitchen(ED, xaxis + feature["x"], zaxis + feature["z"], tier_y, theme_materials)
        
        elif feature_type == "path" and "x1" in feature and "z1" in feature and "x2" in feature and "z2" in feature:
            build_path(
                ED, xaxis + feature["x1"], zaxis + feature["z1"], 
                xaxis + feature["x2"], zaxis + feature["z2"], tier_y - 1, theme_materials
            )
    
    # Add random decorations in rooms
    for room in layout["rooms"]:
        room_tier = room.get("tier", 0)
        if room.get("is_sub_room", False):
            continue
        
        tier_y = y
        if room_tier > 0 and room_tier < len(site_plan.get("multi_level_heights", [y])):
            tier_y = site_plan.get("multi_level_heights")[room_tier]
        elif building_style == "platform" and site_plan.get("base_height"):
            tier_y = site_plan.get("base_height")
        
        # Get room dimensions
        room_x1, room_z1 = room["x1"], room["z1"]
        room_x2, room_z2 = room["x2"], room["z2"]
        room_width = room_x2 - room_x1
        room_length = room_z2 - room_z1
        room_area = room_width * room_length
        
        # Add carpet if it's a large enough room
        if room_area > 20 and random() < 0.7:
            carpet_color = choice(["red", "blue", "light_blue", "light_gray", "green", "cyan"])
            carpet_width = min(room_width - 2, 5)
            carpet_length = min(room_length - 2, 5)
            carpet_x = (room_x1 + room_x2) // 2
            carpet_z = (room_z1 + room_z2) // 2
            
            for dx in range(-carpet_width//2, carpet_width//2 + 1):
                for dz in range(-carpet_length//2, carpet_length//2 + 1):
                    ED.placeBlock(
                        (xaxis + carpet_x + dx, tier_y, zaxis + carpet_z + dz),
                        Block(f"{carpet_color}_carpet")
                    )
        
        # Add lighting
        num_lights = max(1, room_area // 12)
        for _ in range(num_lights):
            light_x = randint(room_x1 + 1, room_x2 - 1)
            light_z = randint(room_z1 + 1, room_z2 - 1)
            
            if random() < 0.7:
                # Ceiling light
                ED.placeBlock(
                    (xaxis + light_x, tier_y + height - 1, zaxis + light_z),
                    Block("lantern", {"hanging": "true"})
                )
            else:
                # Standing light
                ED.placeBlock(
                    (xaxis + light_x, tier_y, zaxis + light_z),
                    Block(theme_materials["details"][1])  # fence post
                )
                ED.placeBlock(
                    (xaxis + light_x, tier_y + 1, zaxis + light_z),
                    Block("lantern")
                )
        
        # Add some paintings or item frames to walls
        num_decorations = max(1, (room_width + room_length) // 4)
        for _ in range(num_decorations):
            # Choose a wall
            wall_choice = randint(0, 3)
            
            if wall_choice == 0:  # North wall
                deco_x = randint(room_x1 + 1, room_x2 - 1)
                deco_z = room_z2
                facing = "south"
            elif wall_choice == 1:  # South wall
                deco_x = randint(room_x1 + 1, room_x2 - 1)
                deco_z = room_z1
                facing = "north"
            elif wall_choice == 2:  # East wall
                deco_x = room_x2
                deco_z = randint(room_z1 + 1, room_z2 - 1)
                facing = "west"
            else:  # West wall
                deco_x = room_x1
                deco_z = randint(room_z1 + 1, room_z2 - 1)
                facing = "east"
            
            # Add wall decoration
            deco_y = tier_y + randint(1, height - 2)
            
            # Since we can't place paintings directly, we place colored wool as a representation
            deco_block = choice([
                ("red_wool", facing),
                ("blue_wool", facing),
                ("green_wool", facing),
                ("yellow_wool", facing),
                ("light_blue_wool", facing)
            ])
            
            # Place the decoration against the wall
            if facing == "north":
                ED.placeBlock((xaxis + deco_x, deco_y, zaxis + deco_z - 1), Block(deco_block[0]))
            elif facing == "south":
                ED.placeBlock((xaxis + deco_x, deco_y, zaxis + deco_z + 1), Block(deco_block[0]))
            elif facing == "west":
                ED.placeBlock((xaxis + deco_x - 1, deco_y, zaxis + deco_z), Block(deco_block[0]))
            elif facing == "east":
                ED.placeBlock((xaxis + deco_x + 1, deco_y, zaxis + deco_z), Block(deco_block[0]))
        
        # Add bookshelves or barrels against walls for larger rooms
        if room_area > 16:
            num_shelves = randint(1, 3)
            for _ in range(num_shelves):
                # Choose wall similar to decorations
                wall_choice = randint(0, 3)
                
                if wall_choice == 0:  # North wall
                    shelf_x = randint(room_x1 + 1, room_x2 - 1)
                    shelf_z = room_z2 - 1
                elif wall_choice == 1:  # South wall
                    shelf_x = randint(room_x1 + 1, room_x2 - 1)
                    shelf_z = room_z1 + 1
                elif wall_choice == 2:  # East wall
                    shelf_x = room_x2 - 1
                    shelf_z = randint(room_z1 + 1, room_z2 - 1)
                else:  # West wall
                    shelf_x = room_x1 + 1
                    shelf_z = randint(room_z1 + 1, room_z2 - 1)
                
                # Place shelf
                if random() < 0.7:
                    # Bookshelf
                    ED.placeBlock((xaxis + shelf_x, tier_y, zaxis + shelf_z), Block("bookshelf"))
                    if random() < 0.5:  # Double height bookshelf
                        ED.placeBlock((xaxis + shelf_x, tier_y + 1, zaxis + shelf_z), Block("bookshelf"))
                else:
                    # Storage barrel
                    ED.placeBlock((xaxis + shelf_x, tier_y, zaxis + shelf_z), Block("barrel"))

def build_fireplace(ED, x, z, y, theme_materials):
    """Build a fireplace structure"""
    # Base
    ED.placeBlock((x, y - 1, z), Block(theme_materials["accent"][0]))
    
    # Sides
    ED.placeBlock((x - 1, y, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x + 1, y, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x, y, z - 1), Block(theme_materials["accent"][0]))
    
    # Second level sides
    ED.placeBlock((x - 1, y + 1, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x + 1, y + 1, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x, y + 1, z - 1), Block(theme_materials["accent"][0]))
    
    # Top
    ED.placeBlock((x - 1, y + 2, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x, y + 2, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x + 1, y + 2, z), Block(theme_materials["accent"][0]))
    ED.placeBlock((x, y + 2, z - 1), Block(theme_materials["accent"][0]))
    
    # Chimney
    for height in range(3, 7):
        ED.placeBlock((x, y + height, z - 1), Block(theme_materials["accent"][0]))
    
    # Fire
    ED.placeBlock((x, y, z), Block("fire"))
    
    # Mantle decoration
    ED.placeBlock((x - 1, y + 3, z), Block("flower_pot"))
    ED.placeBlock((x + 1, y + 3, z), Block("lantern"))
    
    # Campfire smoke effect at top
    ED.placeBlock((x, y + 7, z - 1), Block("campfire", {"lit": "true"}))

def build_hearth(ED, x, z, y, theme_materials):
    """Build a large hearth for great halls"""
    hearth_size = randint(2, 3)
    
    # Base stone
    for dx in range(-hearth_size, hearth_size + 1):
        for dz in range(-hearth_size, hearth_size + 1):
            if abs(dx) + abs(dz) <= hearth_size + 1:
                ED.placeBlock((x + dx, y - 1, z + dz), Block(theme_materials["accent"][0]))
    
    # Back and sides
    for dx in range(-hearth_size, hearth_size + 1):
        for height in range(4):
            if abs(dx) == hearth_size or height >= 2:
                ED.placeBlock((x + dx, y + height, z - hearth_size), Block(theme_materials["accent"][0]))
    
    # Top
    for dx in range(-hearth_size, hearth_size + 1):
        ED.placeBlock((x + dx, y + 3, z - hearth_size + 1), Block(theme_materials["accent"][0]))
    
    # Fire pit center
    ED.placeBlock((x, y, z), Block("campfire", {"lit": "true"}))
    
    # Surrounding stone slabs
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx != 0 or dz != 0:
                if dz > -hearth_size:  # Don't place in the back wall
                    ED.placeBlock((x + dx, y, z + dz), Block("stone_slab"))
    
    # Andirons
    ED.placeBlock((x - 1, y + 1, z), Block("iron_bars"))
    ED.placeBlock((x + 1, y + 1, z), Block("iron_bars"))
    
    # Mantle decorations
    ED.placeBlock((x - 2, y + 3, z - hearth_size + 1), Block("lantern"))
    ED.placeBlock((x + 2, y + 3, z - hearth_size + 1), Block("lantern"))
    ED.placeBlock((x, y + 3, z - hearth_size + 1), Block("flower_pot"))
    
    # Chimney
    for height in range(4, 10):
        ED.placeBlock((x, y + height, z - hearth_size), Block(theme_materials["accent"][0]))

def build_table(ED, x, z, y, length, theme_materials):
    """Build a table with chairs"""
    table_type = randint(0, 2)
    
    if table_type == 0:  # Long feasting table
        # Table
        for i in range(-length//2, length//2 + 1):
            ED.placeBlock((x + i, y, z), Block(theme_materials["trim"][1]))  # Leg
            ED.placeBlock((x + i, y + 1, z), Block(theme_materials["floor"][0]))  # Top
        
        # Chairs
        for i in range(-length//2 + 1, length//2):
            if i % 2 == 0:
                ED.placeBlock((x + i, y, z + 1), Block("oak_stairs", {"facing": "north"}))
                ED.placeBlock((x + i, y, z - 1), Block("oak_stairs", {"facing": "south"}))
        
        # Decorative items
        for i in range(-length//2 + 1, length//2):
            if i % 3 == 0:
                ED.placeBlock((x + i, y + 2, z), Block(choice(["lantern", "flower_pot"])))
    
    elif table_type == 1:  # Round table
        # Center post
        ED.placeBlock((x, y, z), Block(theme_materials["trim"][1]))
        
        # Table top
        for dx in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                if dx != 0 or dz != 0:  # Skip center (already has post)
                    ED.placeBlock((x + dx, y + 1, z + dz), Block(theme_materials["floor"][0]))
        
        # Chairs around table
        ED.placeBlock((x + 2, y, z), Block("oak_stairs", {"facing": "west"}))
        ED.placeBlock((x - 2, y, z), Block("oak_stairs", {"facing": "east"}))
        ED.placeBlock((x, y, z + 2), Block("oak_stairs", {"facing": "north"}))
        ED.placeBlock((x, y, z - 2), Block("oak_stairs", {"facing": "south"}))
        
        # Center decoration
        ED.placeBlock((x, y + 2, z), Block("lantern"))
    
    else:  # Simple table
        # Table
        ED.placeBlock((x, y, z), Block(theme_materials["trim"][1]))  # Leg
        ED.placeBlock((x, y + 1, z), Block(theme_materials["details"][2], {"facing": "north", "half": "top"}))  # Top
        
        # Chair
        ED.placeBlock((x + 1, y, z), Block("oak_stairs", {"facing": "west"}))
        
        # Item on table
        ED.placeBlock((x, y + 2, z), Block(choice(["flower_pot", "candle"])))

def build_bookshelf(ED, x, z, y, theme_materials):
    """Build a bookshelf or study area"""
    # Bookshelves
    for height in range(3):
        ED.placeBlock((x, y + height, z), Block("bookshelf"))
        ED.placeBlock((x + 1, y + height, z), Block("bookshelf"))
        ED.placeBlock((x - 1, y + height, z), Block("bookshelf"))
    
    # Desk in front
    ED.placeBlock((x, y, z + 1), Block("oak_fence"))
    ED.placeBlock((x, y + 1, z + 1), Block(theme_materials["details"][2], {"facing": "north", "half": "top"}))
    
    # Chair
    ED.placeBlock((x, y, z + 2), Block("oak_stairs", {"facing": "north"}))
    
    # Items on desk
    ED.placeBlock((x - 1, y + 1, z + 1), Block("flower_pot"))
    ED.placeBlock((x + 1, y + 1, z + 1), Block("lantern"))

def build_interior_stairs(ED, x, z, y, height_diff, direction, theme_materials):
    """Build stairs between floors inside a building"""
    stair_material = theme_materials["floor"][0]
    stairs_block = f"{stair_material}_stairs"
    
    if direction == "north":
        for i in range(height_diff):
            ED.placeBlock((x, y + i, z - i), Block(stairs_block, {"facing": "south"}))
    elif direction == "south":
        for i in range(height_diff):
            ED.placeBlock((x, y + i, z + i), Block(stairs_block, {"facing": "north"}))
    elif direction == "east":
        for i in range(height_diff):
            ED.placeBlock((x + i, y + i, z), Block(stairs_block, {"facing": "west"}))
    elif direction == "west":
        for i in range(height_diff):
            ED.placeBlock((x - i, y + i, z), Block(stairs_block, {"facing": "east"}))
    
    # Add railing on one side
    if direction in ["north", "south"]:
        x_offset = 1
        for i in range(height_diff):
            if direction == "north":
                ED.placeBlock((x + x_offset, y + i, z - i), Block(theme_materials["details"][1]))
            else:
                ED.placeBlock((x + x_offset, y + i, z + i), Block(theme_materials["details"][1]))
    else:  # east or west
        z_offset = 1
        for i in range(height_diff):
            if direction == "east":
                ED.placeBlock((x + i, y + i, z + z_offset), Block(theme_materials["details"][1]))
            else:
                ED.placeBlock((x - i, y + i, z + z_offset), Block(theme_materials["details"][1]))

def build_exterior_stairs(ED, x, z, y, height_diff, direction, theme_materials):
    """Build exterior stairs down to ground level (for stilt houses)"""
    stair_material = theme_materials["foundation"][0]
    stairs_block = f"{stair_material}_stairs"
    
    # Build sturdy support post at top
    ED.placeBlock((x, y - 1, z), Block(theme_materials["trim"][0]))
    
    # Wider stairs (3 blocks wide)
    if direction == "north":
        for i in range(height_diff):
            for dx in range(-1, 2):
                ED.placeBlock((x + dx, y - i, z - i), Block(stairs_block, {"facing": "south"}))
            
            # Add railings
            if i > 0:
                ED.placeBlock((x - 2, y - i, z - i), Block(theme_materials["details"][1]))
                ED.placeBlock((x + 2, y - i, z - i), Block(theme_materials["details"][1]))
    
    elif direction == "south":
        for i in range(height_diff):
            for dx in range(-1, 2):
                ED.placeBlock((x + dx, y - i, z + i), Block(stairs_block, {"facing": "north"}))
            
            # Add railings
            if i > 0:
                ED.placeBlock((x - 2, y - i, z + i), Block(theme_materials["details"][1]))
                ED.placeBlock((x + 2, y - i, z + i), Block(theme_materials["details"][1]))
    
    elif direction == "east":
        for i in range(height_diff):
            for dz in range(-1, 2):
                ED.placeBlock((x + i, y - i, z + dz), Block(stairs_block, {"facing": "west"}))
            
            # Add railings
            if i > 0:
                ED.placeBlock((x + i, y - i, z - 2), Block(theme_materials["details"][1]))
                ED.placeBlock((x + i, y - i, z + 2), Block(theme_materials["details"][1]))
    
    elif direction == "west":
        for i in range(height_diff):
            for dz in range(-1, 2):
                ED.placeBlock((x - i, y - i, z + dz), Block(stairs_block, {"facing": "east"}))
            
            # Add railings
            if i > 0:
                ED.placeBlock((x - i, y - i, z - 2), Block(theme_materials["details"][1]))
                ED.placeBlock((x - i, y - i, z + 2), Block(theme_materials["details"][1]))
    
    # Add lantern posts at top and bottom
    if direction == "north":
        ED.placeBlock((x - 2, y, z), Block("lantern"))
        ED.placeBlock((x + 2, y, z), Block("lantern"))
        ED.placeBlock((x - 2, y - height_diff + 1, z - height_diff), Block("lantern"))
        ED.placeBlock((x + 2, y - height_diff + 1, z - height_diff), Block("lantern"))
    
    elif direction == "south":
        ED.placeBlock((x - 2, y, z), Block("lantern"))
        ED.placeBlock((x + 2, y, z), Block("lantern"))
        ED.placeBlock((x - 2, y - height_diff + 1, z + height_diff), Block("lantern"))
        ED.placeBlock((x + 2, y - height_diff + 1, z + height_diff), Block("lantern"))
    
    elif direction == "east":
        ED.placeBlock((x, y, z - 2), Block("lantern"))
        ED.placeBlock((x, y, z + 2), Block("lantern"))
        ED.placeBlock((x + height_diff, y - height_diff + 1, z - 2), Block("lantern"))
        ED.placeBlock((x + height_diff, y - height_diff + 1, z + 2), Block("lantern"))
    
    elif direction == "west":
        ED.placeBlock((x, y, z - 2), Block("lantern"))
        ED.placeBlock((x, y, z + 2), Block("lantern"))
        ED.placeBlock((x - height_diff, y - height_diff + 1, z - 2), Block("lantern"))
        ED.placeBlock((x - height_diff, y - height_diff + 1, z + 2), Block("lantern"))

def build_well(ED, x, z, y, theme_materials):
    """Build a well in the courtyard"""
    well_radius = 2
    
    # Base
    for dx in range(-well_radius, well_radius + 1):
        for dz in range(-well_radius, well_radius + 1):
            if dx**2 + dz**2 <= well_radius**2:
                ED.placeBlock((x + dx, y - 1, z + dz), Block(theme_materials["foundation"][0]))
    
    # Wall
    for angle in range(0, 360, 15):
        rad = math.radians(angle)
        wx = int(round(well_radius * math.cos(rad)))
        wz = int(round(well_radius * math.sin(rad)))
        
        if wx**2 + wz**2 <= well_radius**2:
            ED.placeBlock((x + wx, y, z + wz), Block(theme_materials["foundation"][0]))
            ED.placeBlock((x + wx, y + 1, z + wz), Block(theme_materials["foundation"][0]))
    
    # Water in center
    for dx in range(-well_radius + 1, well_radius):
        for dz in range(-well_radius + 1, well_radius):
            if dx**2 + dz**2 < (well_radius - 0.5)**2:
                ED.placeBlock((x + dx, y, z + dz), Block("water"))
    
    # Roof structure
    ED.placeBlock((x - well_radius, y, z - well_radius), Block(theme_materials["trim"][1]))
    ED.placeBlock((x + well_radius, y, z - well_radius), Block(theme_materials["trim"][1]))
    ED.placeBlock((x - well_radius, y, z + well_radius), Block(theme_materials["trim"][1]))
    ED.placeBlock((x + well_radius, y, z + well_radius), Block(theme_materials["trim"][1]))
    
    # Posts
    for post_y in range(1, 4):
        ED.placeBlock((x - well_radius, y + post_y, z - well_radius), Block(theme_materials["trim"][1]))
        ED.placeBlock((x + well_radius, y + post_y, z - well_radius), Block(theme_materials["trim"][1]))
        ED.placeBlock((x - well_radius, y + post_y, z + well_radius), Block(theme_materials["trim"][1]))
        ED.placeBlock((x + well_radius, y + post_y, z + well_radius), Block(theme_materials["trim"][1]))
    
    # Roof
    for dx in range(-well_radius - 1, well_radius + 2):
        for dz in range(-well_radius - 1, well_radius + 2):
            ED.placeBlock((x + dx, y + 4, z + dz), Block(theme_materials["floor"][0]))
    
    # Bucket and rope - simulated with a cauldron
    ED.placeBlock((x, y + 1, z), Block("cauldron"))

def build_garden_feature(ED, x, z, y, theme_materials):
    """Build a garden feature in a courtyard"""
    feature_type = randint(0, 2)
    
    if feature_type == 0:  # Flower garden
        radius = 2
        
        # Dirt base
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx**2 + dz**2 <= radius**2:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("dirt"))
        
        # Flowers
        flowers = ["poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", "corn_flower"]
        
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx**2 + dz**2 <= radius**2:
                    if random() < 0.7:  # 70% chance for a flower
                        ED.placeBlock((x + dx, y, z + dz), Block(choice(flowers)))
        
        # Maybe add a central feature
        if random() < 0.5:
            ED.placeBlock((x, y, z), Block("flower_pot"))
    
    elif feature_type == 1:  # Small fountain
        radius = 2
        
        # Base
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                if dx**2 + dz**2 <= radius**2:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block(theme_materials["foundation"][0]))
        
        # Walls
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            wx = int(round(radius * math.cos(rad)))
            wz = int(round(radius * math.sin(rad)))
            
            if wx**2 + wz**2 <= radius**2:
                ED.placeBlock((x + wx, y, z + wz), Block(theme_materials["foundation"][0]))
        
        # Water
        for dx in range(-radius + 1, radius):
            for dz in range(-radius + 1, radius):
                if dx**2 + dz**2 < (radius - 0.5)**2:
                    ED.placeBlock((x + dx, y, z + dz), Block("water"))
        
        # Center feature
        ED.placeBlock((x, y, z), Block(theme_materials["foundation"][0]))
        ED.placeBlock((x, y + 1, z), Block("sea_pickle"))
    
    else:  # Sitting area
        # Stone slab bench
        for dx in range(-2, 3):
            if dx != 0:  # Skip center for opening
                ED.placeBlock((x + dx, y, z), Block("stone_slab"))
        
        for dz in range(-2, 3):
            if dz != 0:  # Skip center for opening
                ED.placeBlock((x, y, z + dz), Block("stone_slab"))
        
        # Center table
        ED.placeBlock((x, y, z), Block("stone_slab", {"type": "bottom"}))
        
        # Maybe add lighting
        if random() < 0.7:
            ED.placeBlock((x, y + 1, z), Block("lantern"))

def build_bed(ED, x, z, y, theme_materials):
    """Build a bed with nightstands"""
    # Random bed color
    bed_color = choice(["red", "blue", "light_blue", "cyan", "white", "yellow"])
    
    # Place the bed
    ED.placeBlock((x, y, z), Block(f"{bed_color}_bed", {"facing": "north", "part": "foot"}))
    ED.placeBlock((x, y, z + 1), Block(f"{bed_color}_bed", {"facing": "north", "part": "head"}))
    
    # Nightstands
    ED.placeBlock((x + 1, y, z + 1), Block(theme_materials["floor"][0]))
    ED.placeBlock((x - 1, y, z + 1), Block(theme_materials["floor"][0]))
    
    # Lighting
    ED.placeBlock((x + 1, y + 1, z + 1), Block("lantern"))
    
    # Carpet at foot of bed
    ED.placeBlock((x, y, z - 1), Block(f"{bed_color}_carpet"))
    ED.placeBlock((x + 1, y, z - 1), Block(f"{bed_color}_carpet"))
    ED.placeBlock((x - 1, y, z - 1), Block(f"{bed_color}_carpet"))

def build_storage(ED, x, z, y, theme_materials):
    """Build storage area with chests and barrels"""
    storage_type = randint(0, 2)
    
    if storage_type == 0:  # Chest stack
        chest_directions = ["north", "south", "east", "west"]
        
        # Main chest
        ED.placeBlock((x, y, z), Block("chest", {"facing": choice(chest_directions)}))
        
        # Surrounding barrels
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            facing = "east"
            if dx == 1: facing = "west"
            elif dx == -1: facing = "east"
            elif dz == 1: facing = "north"
            elif dz == -1: facing = "south"
            
            ED.placeBlock((x + dx, y, z + dz), Block("barrel", {"facing": facing}))
        
        # Stacked barrels
        ED.placeBlock((x + 1, y + 1, z), Block("barrel", {"facing": "up"}))
        ED.placeBlock((x - 1, y + 1, z), Block("barrel", {"facing": "up"}))
    
    elif storage_type == 1:  # Shelving unit
        # Base shelf
        for dx in range(-1, 2):
            ED.placeBlock((x + dx, y, z), Block(theme_materials["floor"][0]))
        
        # Storage blocks
        ED.placeBlock((x - 1, y + 1, z), Block("barrel", {"facing": "up"}))
        ED.placeBlock((x, y + 1, z), Block("chest", {"facing": "south"}))
        ED.placeBlock((x + 1, y + 1, z), Block("barrel", {"facing": "up"}))
        
        # Top shelf
        for dx in range(-1, 2):
            ED.placeBlock((x + dx, y + 2, z), Block(theme_materials["details"][2], {"facing": "north", "half": "top"}))
        
        # Decorations on top
        ED.placeBlock((x - 1, y + 3, z), Block("flower_pot"))
        ED.placeBlock((x + 1, y + 3, z), Block("lantern"))
    
    else:  # Organized storage wall
        # Base
        for dx in range(-2, 3):
            ED.placeBlock((x + dx, y, z), Block(theme_materials["floor"][0]))
        
        # Storage row
        for dx in range(-2, 3):
            if dx % 2 == 0:
                ED.placeBlock((x + dx, y + 1, z), Block("barrel", {"facing": "south"}))
            else:
                ED.placeBlock((x + dx, y + 1, z), Block("chest", {"facing": "south"}))
        
        # Second row
        for dx in range(-2, 3, 2):
            ED.placeBlock((x + dx, y + 2, z), Block("barrel", {"facing": "south"}))

def build_kitchen(ED, x, z, y, theme_materials):
    """Build a kitchen area"""
    # Counter base
    for dx in range(-2, 3):
        ED.placeBlock((x + dx, y, z), Block(theme_materials["details"][2], {"facing": "north", "half": "top"}))
    
    # Kitchen blocks
    ED.placeBlock((x - 2, y + 1, z), Block("smoker", {"facing": "south"}))
    ED.placeBlock((x - 1, y + 1, z), Block("crafting_table"))
    ED.placeBlock((x, y + 1, z), Block("cauldron"))
    ED.placeBlock((x + 1, y + 1, z), Block("composter"))
    ED.placeBlock((x + 2, y + 1, z), Block("barrel", {"facing": "south"}))
    
    # Ceiling decorations
    ED.placeBlock((x, y + 3, z), Block("lantern", {"hanging": "true"}))
    
    # Cutting board (pressure plate)
    ED.placeBlock((x + 1, y + 2, z), Block("stone_pressure_plate"))

def build_path(ED, x1, z1, x2, z2, y, theme_materials):
    """Build a path between two points"""
    # Calculate direction vector
    dx = x2 - x1
    dz = z2 - z1
    path_length = max(abs(dx), abs(dz))
    
    if path_length < 1:
        return
    
    # Normalize direction vector
    if path_length > 0:
        dx = dx / path_length
        dz = dz / path_length
    
    # Slight curve to the path (more natural)
    curve_factor = 0.3
    mid_perpendicular_x = -dz * curve_factor * path_length
    mid_perpendicular_z = dx * curve_factor * path_length
    
    # Create the path with quadratic interpolation
    for t in range(int(path_length) + 1):
        # Parameter from 0 to 1
        t_norm = t / path_length if path_length > 0 else 0
        
        # Quadratic Bezier curve parameters
        t_sq = t_norm * t_norm
        t1_sq = (1 - t_norm) * (1 - t_norm)
        bezier_x = t1_sq * x1 + 2 * (1 - t_norm) * t_norm * (x1 + dx * path_length/2 + mid_perpendicular_x) + t_sq * x2
        bezier_z = t1_sq * z1 + 2 * (1 - t_norm) * t_norm * (z1 + dz * path_length/2 + mid_perpendicular_z) + t_sq * z2
        
        # Path width (2-3 blocks)
        path_width = path_length / 10 + 1
        path_width = min(max(path_width, 1), 2)
        
        # Place path blocks in a small area around this point
        for offset_x in range(-int(path_width), int(path_width) + 1):
            for offset_z in range(-int(path_width), int(path_width) + 1):
                # Further from center gets less chance of path block
                distance_from_center = math.sqrt(offset_x**2 + offset_z**2)
                if distance_from_center <= path_width and random() > distance_from_center/path_width/2:
                    path_block = choice(["gravel", "cobblestone", "stone", "stone_slab"])
                    ED.placeBlock((int(bezier_x) + offset_x, y, int(bezier_z) + offset_z), Block(path_block))
                    
                    # Add some decorative elements along path edges
                    if distance_from_center > path_width*0.7 and random() < 0.1:
                        if random() < 0.7:
                            # Flowers or small plants
                            plant = choice(["poppy", "dandelion", "azure_bluet", "grass"])
                            ED.placeBlock((int(bezier_x) + offset_x, y + 1, int(bezier_z) + offset_z), Block(plant))
                        else:
                            # Occasional lantern
                            ED.placeBlock((int(bezier_x) + offset_x, y + 1, int(bezier_z) + offset_z), Block("lantern"))

def add_garden_and_landscaping(ED, xaxis, zaxis, y, width, length, building_style, theme_materials, site):
    """Add garden areas and landscaping around the house"""
    print("Adding gardens and landscaping...")
    
    # Determine garden area based on house size
    garden_radius = max(width, length) + 8
    
    # Check if site has landscaping areas defined
    landscaping_spots = []
    if "landscaping" in site:
        for dx, dz in site["landscaping"]:
            landscaping_spots.append((dx, dz))
    
    # Create some spots around the building if none defined
    if not landscaping_spots:
        # Add 3-6 random landscape areas
        num_spots = randint(3, 6)
        for _ in range(num_spots):
            angle = randint(0, 360)
            distance = randint(width//2 + 2, garden_radius - 2)
            dx = int(distance * math.cos(math.radians(angle)))
            dz = int(distance * math.sin(math.radians(angle)))
            landscaping_spots.append((dx, dz))
    
    # Create landscaping at each spot
    for dx, dz in landscaping_spots:
        landscaping_type = randint(0, 5)
        
        if landscaping_type == 0:  # Flower garden
            build_flower_garden(ED, xaxis + dx, zaxis + dz, y, theme_materials)
        
        elif landscaping_type == 1:  # Tree grove
            build_tree_grove(ED, xaxis + dx, zaxis + dz, y, theme_materials)
        
        elif landscaping_type == 2:  # Rock garden
            build_rock_garden(ED, xaxis + dx, zaxis + dz, y, theme_materials)
        
        elif landscaping_type == 3:  # Small pond
            build_pond(ED, xaxis + dx, zaxis + dz, y, theme_materials)
        
        elif landscaping_type == 4:  # Sitting area
            build_sitting_area(ED, xaxis + dx, zaxis + dz, y, theme_materials)
            
        else:  # Vegetable garden
            build_vegetable_garden(ED, xaxis + dx, zaxis + dz, y, theme_materials)
    
    # Create paths between house and landscaping features
    # Main entrance position
    entrance_x, entrance_z = 0, 0
    for door in layout["doors"]:
        if door.get("is_entrance", False):
            entrance_x = door["x"]
            entrance_z = door["z"]
            break
    
    # If no main entrance found, use center of building
    if entrance_x == 0 and entrance_z == 0:
        if building_style == "courtyard":
            # For courtyard, use the south entrance
            entrance_x = 0
            entrance_z = -length//2
        else:
            # Default entrance at south center
            entrance_x = 0
            entrance_z = -length//2
    
    # Create paths from entrance to each landscaping feature
    for dx, dz in landscaping_spots:
        # Only create paths to some features (not all)
        if random() < 0.7:
            # Create curved path
            build_path(
                ED, xaxis + entrance_x, zaxis + entrance_z, 
                xaxis + dx, zaxis + dz, y - 1, theme_materials
            )
    
    # Create a main path from entrance out toward world edge
    main_path_length = garden_radius
    
    # Determine exit direction based on entrance position
    if abs(entrance_x) > abs(entrance_z):
        # Exit east/west
        exit_x = entrance_x - main_path_length if entrance_x > 0 else entrance_x + main_path_length
        exit_z = entrance_z
    else:
        # Exit north/south
        exit_x = entrance_x
        exit_z = entrance_z - main_path_length if entrance_z > 0 else entrance_z + main_path_length
    
    # Build main path
    build_path(
        ED, xaxis + entrance_x, zaxis + entrance_z,
        xaxis + exit_x, zaxis + exit_z, y - 1, theme_materials
    )
    
    # Add some random additional decoration in the garden area
    num_decorations = randint(5, 15)
    for _ in range(num_decorations):
        angle = randint(0, 360)
        distance = randint(width//2 + 2, garden_radius - 3)
        dx = int(distance * math.cos(math.radians(angle)))
        dz = int(distance * math.sin(math.radians(angle)))
        
        # Check if it's too close to existing features
        too_close = False
        for lx, lz in landscaping_spots:
            if abs(dx - lx) < 4 and abs(dz - lz) < 4:
                too_close = True
                break
                
        if not too_close:
            deco_type = randint(0, 3)
            
            if deco_type == 0:  # Lantern post
                ED.placeBlock((xaxis + dx, y, zaxis + dz), Block(theme_materials["details"][1]))
                ED.placeBlock((xaxis + dx, y + 1, zaxis + dz), Block("lantern"))
            
            elif deco_type == 1:  # Flower
                flower = choice(["poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", 
                                "orange_tulip", "red_tulip", "white_tulip", "pink_tulip"])
                ED.placeBlock((xaxis + dx, y, zaxis + dz), Block(flower))
            
            elif deco_type == 2:  # Bush
                bush_height = randint(1, 3)
                for h in range(bush_height):
                    ED.placeBlock((xaxis + dx, y + h, zaxis + dz), Block("oak_leaves"))
            
            else:  # Small decoration
                deco_block = choice(["flower_pot", "lantern", "mossy_cobblestone", "grass"])
                ED.placeBlock((xaxis + dx, y, zaxis + dz), Block(deco_block))

def build_flower_garden(ED, x, z, y, theme_materials):
    """Build a flower garden area"""
    garden_size = randint(3, 5)
    
    # Prepare soil
    for dx in range(-garden_size, garden_size + 1):
        for dz in range(-garden_size, garden_size + 1):
            if dx**2 + dz**2 <= garden_size**2:
                ED.placeBlock((x + dx, y - 1, z + dz), Block("dirt"))
                
                # Place grass/podzol for base
                if random() < 0.3:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("podzol"))
    
    # Plant flowers in a pattern
    flowers = [
        "poppy", "dandelion", "blue_orchid", "allium", "azure_bluet", 
        "orange_tulip", "red_tulip", "white_tulip", "pink_tulip",
        "cornflower", "lily_of_the_valley"
    ]
    
    garden_style = randint(0, 2)
    
    if garden_style == 0:  # Concentric rings of different flowers
        num_rings = min(3, garden_size)
        ring_size = garden_size / num_rings
        
        for dx in range(-garden_size, garden_size + 1):
            for dz in range(-garden_size, garden_size + 1):
                dist = math.sqrt(dx**2 + dz**2)
                if dist <= garden_size:
                    ring = int(dist / ring_size)
                    if ring < len(flowers) and random() < 0.7:
                        ED.placeBlock((x + dx, y, z + dz), Block(flowers[ring]))
    
    elif garden_style == 1:  # Radial pattern
        num_sections = randint(4, 8)
        section_angle = 360 / num_sections
        
        for dx in range(-garden_size, garden_size + 1):
            for dz in range(-garden_size, garden_size + 1):
                dist = math.sqrt(dx**2 + dz**2)
                if dist <= garden_size and random() < 0.7:
                    angle = math.degrees(math.atan2(dz, dx)) % 360
                    section = int(angle / section_angle)
                    flower_index = section % len(flowers)
                    ED.placeBlock((x + dx, y, z + dz), Block(flowers[flower_index]))
    
    else:  # Random mix
        for dx in range(-garden_size, garden_size + 1):
            for dz in range(-garden_size, garden_size + 1):
                if dx**2 + dz**2 <= garden_size**2 and random() < 0.7:
                    flower = choice(flowers)
                    ED.placeBlock((x + dx, y, z + dz), Block(flower))
    
    # Add a central feature
    center_feature = randint(0, 2)
    
    if center_feature == 0:  # Small statue
        ED.placeBlock((x, y, z), Block("stone_brick_wall"))
        ED.placeBlock((x, y + 1, z), Block("lantern"))
    
    elif center_feature == 1:  # Bird bath
        ED.placeBlock((x, y, z), Block("stone_brick_wall"))
        ED.placeBlock((x, y + 1, z), Block("cauldron"))
        
        # Simulate water in cauldron with a water level
        # Unfortunately water level can't be set directly, but this is for the visual concept
    
    else:  # Flower pot stack
        for h in range(3):
            ED.placeBlock((x, y + h, z), Block("flower_pot"))

def build_tree_grove(ED, x, z, y, theme_materials):
    """Build a small grove of trees"""
    grove_size = randint(4, 7)
    num_trees = randint(3, 7)
    
    # Prepare soil
    for dx in range(-grove_size, grove_size + 1):
        for dz in range(-grove_size, grove_size + 1):
            if dx**2 + dz**2 <= grove_size**2:
                ED.placeBlock((x + dx, y - 1, z + dz), Block("dirt"))
                
                # Random grass or podzol
                if random() < 0.6:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("grass_block"))
                else:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("podzol"))
    
    # Plant trees
    for _ in range(num_trees):
        # Random position within grove
        angle = random() * 2 * math.pi
        distance = random() * grove_size * 0.8
        tree_x = int(x + distance * math.cos(angle))
        tree_z = int(z + distance * math.sin(angle))
        
        # Tree style
        tree_style = randint(0, 2)
        
        if tree_style == 0:  # Oak
            tree_height = randint(4, 6)
            
            # Trunk
            for h in range(tree_height):
                ED.placeBlock((tree_x, y + h, tree_z), Block("oak_log", {"axis": "y"}))
            
            # Canopy
            canopy_radius = randint(2, 3)
            for dx in range(-canopy_radius, canopy_radius + 1):
                for dz in range(-canopy_radius, canopy_radius + 1):
                    for dy in range(2):
                        if dx**2 + dz**2 + dy**2 <= canopy_radius**2 + 1:
                            ED.placeBlock((tree_x + dx, y + tree_height - 1 + dy, tree_z + dz), Block("oak_leaves"))
        
        elif tree_style == 1:  # Birch
            tree_height = randint(5, 7)
            
            # Trunk
            for h in range(tree_height):
                ED.placeBlock((tree_x, y + h, tree_z), Block("birch_log", {"axis": "y"}))
            
            # Canopy - more upright/columnar
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    for dy in range(3):
                        canopy_y = y + tree_height - 2 + dy
                        
                        # Taper at top
                        if dy == 2 and (abs(dx) > 0 or abs(dz) > 0):
                            continue
                            
                        ED.placeBlock((tree_x + dx, canopy_y, tree_z + dz), Block("birch_leaves"))
        
        else:  # Spruce
            tree_height = randint(6, 9)
            
            # Trunk
            for h in range(tree_height):
                ED.placeBlock((tree_x, y + h, tree_z), Block("spruce_log", {"axis": "y"}))
            
            # Conical canopy in layers
            num_layers = 5
            max_radius = 3
            
            for layer in range(num_layers):
                layer_y = y + tree_height - num_layers + layer
                layer_radius = max_radius - int(layer * max_radius / num_layers)
                
                for dx in range(-layer_radius, layer_radius + 1):
                    for dz in range(-layer_radius, layer_radius + 1):
                        if dx**2 + dz**2 <= layer_radius**2 + 1:
                            ED.placeBlock((tree_x + dx, layer_y, tree_z + dz), Block("spruce_leaves"))
    
    # Add undergrowth and details
    for dx in range(-grove_size, grove_size + 1):
        for dz in range(-grove_size, grove_size + 1):
            if dx**2 + dz**2 <= grove_size**2:
                if random() < 0.1:
                    # Random undergrowth
                    undergrowth = choice(["grass", "fern", "sweet_berry_bush", "poppy", "dandelion"])
                    ED.placeBlock((x + dx, y, z + dz), Block(undergrowth))
                elif random() < 0.05:
                    # Random mushrooms
                    mushroom = choice(["red_mushroom", "brown_mushroom"])
                    ED.placeBlock((x + dx, y, z + dz), Block(mushroom))

def build_rock_garden(ED, x, z, y, theme_materials):
    """Build a decorative rock garden"""
    garden_size = randint(3, 5)
    
    # Base layer
    for dx in range(-garden_size, garden_size + 1):
        for dz in range(-garden_size, garden_size + 1):
            if dx**2 + dz**2 <= garden_size**2:
                if random() < 0.7:
                    # Gravel, coarse dirt, or stone base
                    base_block = choice(["gravel", "coarse_dirt", "stone", "andesite"])
                    ED.placeBlock((x + dx, y - 1, z + dz), Block(base_block))
                else:
                    # Some grass
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("grass_block"))
    
    # Create rock formations
    num_formations = randint(3, 7)
    
    for _ in range(num_formations):
        # Random position
        rock_x = x + randint(-garden_size + 1, garden_size - 1)
        rock_z = z + randint(-garden_size + 1, garden_size - 1)
        
        # Rock type
        rock_type = choice(["stone", "andesite", "diorite", "granite", "mossy_cobblestone"])
        
        # Rock shape and size
        rock_height = randint(1, 3)
        rock_style = randint(0, 2)
        
        if rock_style == 0:  # Single tall rock
            for h in range(rock_height):
                # Taper as it gets taller
                if h == 0:
                    radius = randint(1, 2)
                else:
                    radius = 1
                
                for dx in range(-radius, radius + 1):
                    for dz in range(-radius, radius + 1):
                        if dx**2 + dz**2 <= radius**2:
                            ED.placeBlock((rock_x + dx, y + h, rock_z + dz), Block(rock_type))
        
        elif rock_style == 1:  # Cluster of small rocks
            num_rocks = randint(2, 5)
            for _ in range(num_rocks):
                offset_x = randint(-1, 1)
                offset_z = randint(-1, 1)
                height = randint(1, 2)
                
                for h in range(height):
                    ED.placeBlock((rock_x + offset_x, y + h, rock_z + offset_z), Block(rock_type))
        
        else:  # Flat wide rock
            radius = randint(1, 2)
            for dx in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    if dx**2 + dz**2 <= radius**2 + 0.5:
                        height = 1 if random() < 0.7 else 2
                        for h in range(height):
                            ED.placeBlock((rock_x + dx, y + h, rock_z + dz), Block(rock_type))
    
    # Add decorative elements
    for dx in range(-garden_size, garden_size + 1):
        for dz in range(-garden_size, garden_size + 1):
            if dx**2 + dz**2 <= garden_size**2:
                if random() < 0.15:
                    # Check if the position is clear (no rock)
                    if ED.getBlock((x + dx, y, z + dz)).id == "air":
                        # Add decorative plant
                        plant = choice(["fern", "dead_bush", "grass", "red_mushroom", "brown_mushroom"])
                        ED.placeBlock((x + dx, y, z + dz), Block(plant))
    
    # Maybe add a central lantern
    if random() < 0.4:
        ED.placeBlock((x, y, z), Block("stone_brick_wall"))
        ED.placeBlock((x, y + 1, z), Block("lantern"))

def build_pond(ED, x, z, y, theme_materials):
    """Build a small decorative pond"""
    pond_size = randint(3, 5)
    
    # Dig out pond and create borders
    for dx in range(-pond_size, pond_size + 1):
        for dz in range(-pond_size, pond_size + 1):
            dist = math.sqrt(dx**2 + dz**2)
            if dist <= pond_size:
                # Border blocks
                if pond_size - 1 <= dist <= pond_size:
                    ED.placeBlock((x + dx, y - 1, z + dz), Block(choice(theme_materials["foundation"])))
                else:
                    # Inside pond
                    ED.placeBlock((x + dx, y - 1, z + dz), Block("dirt"))
                    
                    # Water
                    if dist <= pond_size - 0.5:
                        ED.placeBlock((x + dx, y, z + dz), Block("water"))
                        
                        # Add some clay/sand underwater
                        ED.placeBlock((x + dx, y - 1, z + dz), Block(choice(["clay", "sand"])))
    
    # Add water plants
    num_plants = randint(3, 7)
    for _ in range(num_plants):
        plant_x = x + randint(-pond_size + 2, pond_size - 2)
        plant_z = z + randint(-pond_size + 2, pond_size - 2)
        
        plant_type = randint(0, 2)
        
        if plant_type == 0:  # Lily pad
            ED.placeBlock((plant_x, y + 1, plant_z), Block("lily_pad"))
        elif plant_type == 1:  # Seagrass
            ED.placeBlock((plant_x, y, plant_z), Block("seagrass"))
        else:  # Reed on edge
            # Find a position near the edge
            edge_x = plant_x
            edge_z = plant_z
            
            # Move position toward edge
            dist = math.sqrt(edge_x**2 + edge_z**2)
            if dist > 0:
                edge_x = int(edge_x * (pond_size - 1) / dist)
                edge_z = int(edge_z * (pond_size - 1) / dist)
            
            ED.placeBlock((x + edge_x, y, z + edge_z), Block("sugar_cane"))
            ED.placeBlock((x + edge_x, y + 1, z + edge_z), Block("sugar_cane"))
    
    # Add some fish (placeholder since we can't actually spawn entities)
    # Represented by sea pickles
    for _ in range(randint(2, 4)):
        fish_x = x + randint(-pond_size + 2, pond_size - 2)
        fish_z = z + randint(-pond_size + 2, pond_size - 2)
        
        ED.placeBlock((fish_x, y, fish_z), Block("sea_pickle"))
    
    # Add decorative elements around pond
    for dx in range(-pond_size - 1, pond_size + 2):
        for dz in range(-pond_size - 1, pond_size + 2):
            dist = math.sqrt(dx**2 + dz**2)
            
            # Only areas just outside the pond
            if pond_size < dist <= pond_size + 1.5:
                if random() < 0.3:
                    # Water-loving plants
                    plant = choice(["fern", "tall_grass", "grass", "blue_orchid"])
                    ED.placeBlock((x + dx, y, z + dz), Block(plant))

def build_sitting_area(ED, x, z, y, theme_materials):
    """Build a small sitting area with benches"""
    area_size = randint(3, 4)
    
    # Create a flat area
    for dx in range(-area_size, area_size + 1):
        for dz in range(-area_size, area_size + 1):
            if abs(dx) <= area_size and abs(dz) <= area_size:
                # Paved area
                paving = choice(["stone", "cobblestone", "stone_bricks", "smooth_stone"])
                ED.placeBlock((x + dx, y - 1, z + dz), Block(paving))
    
    # Add benches around the perimeter
    for dx in [-area_size + 1, area_size - 1]:
        for dz in range(-area_size + 2, area_size - 1):
            if dx == -area_size + 1:
                ED.placeBlock((x + dx, y, z + dz), Block("oak_stairs", {"facing": "east"}))
            else:
                ED.placeBlock((x + dx, y, z + dz), Block("oak_stairs", {"facing": "west"}))
    
    for dz in [-area_size + 1, area_size - 1]:
        for dx in range(-area_size + 2, area_size - 1):
            if dz == -area_size + 1:
                ED.placeBlock((x + dx, y, z + dz), Block("oak_stairs", {"facing": "south"}))
            else:
                ED.placeBlock((x + dx, y, z + dz), Block("oak_stairs", {"facing": "north"}))
    
    # Add a central feature
    center_feature = randint(0, 2)
    
    if center_feature == 0:  # Campfire
        ED.placeBlock((x, y, z), Block("campfire", {"lit": "true"}))
        
        # Arrange seats around the campfire
        ED.placeBlock((x, y, z + 2), Block("oak_log", {"axis": "x"}))
        ED.placeBlock((x, y, z - 2), Block("oak_log", {"axis": "x"}))
        ED.placeBlock((x + 2, y, z), Block("oak_log", {"axis": "z"}))
        ED.placeBlock((x - 2, y, z), Block("oak_log", {"axis": "z"}))
    
    elif center_feature == 1:  # Table
        ED.placeBlock((x, y, z), Block("oak_fence"))
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if abs(dx) == 1 or abs(dz) == 1:
                    ED.placeBlock((x + dx, y + 1, z + dz), Block(theme_materials["details"][2], {"facing": "north", "half": "top"}))
        ED.placeBlock((x, y + 1, z), Block("flower_pot"))
    
    else:  # Statue or focal point
        geo.placeCuboid(
            ED,
            (x, y, z),
            (x, y + 2, z),
            Block(theme_materials["foundation"][0])
        )
        ED.placeBlock((x, y + 3, z), Block("lantern"))
    
    # Add some decorative elements
    for dx in range(-area_size, area_size + 1):
        for dz in range(-area_size, area_size + 1):
            # Only on the edges
            if (abs(dx) == area_size or abs(dz) == area_size) and random() < 0.4:
                ED.placeBlock((x + dx, y, z + dz), Block(choice([
                    "flower_pot", "lantern", theme_materials["details"][1]
                ])))

def build_vegetable_garden(ED, x, z, y, theme_materials):
    """Build a small vegetable garden with rows of crops"""
    garden_width = randint(4, 7)
    garden_length = randint(4, 7)
    
    # Prepare farmland
    for dx in range(-garden_width//2, garden_width//2 + 1):
        for dz in range(-garden_length//2, garden_length//2 + 1):
            # Border with path
            if abs(dx) == garden_width//2 or abs(dz) == garden_length//2:
                ED.placeBlock((x + dx, y - 1, z + dz), Block("coarse_dirt"))
            else:
                # Farmland inside
                ED.placeBlock((x + dx, y - 1, z + dz), Block("farmland", {"moisture": "7"}))
    
    # Plant crops in rows
    for dx in range(-garden_width//2 + 1, garden_width//2):
        crop_type = choice(["wheat", "carrots", "potatoes", "beetroots"])
        
        for dz in range(-garden_length//2 + 1, garden_length//2):
            # Random growth stage
            growth_stage = randint(0, 7)
            
            if crop_type == "wheat":
                ED.placeBlock((x + dx, y, z + dz), Block("wheat", {"age": str(growth_stage)}))
            elif crop_type == "carrots":
                ED.placeBlock((x + dx, y, z + dz), Block("carrots", {"age": str(growth_stage)}))
            elif crop_type == "potatoes":
                ED.placeBlock((x + dx, y, z + dz), Block("potatoes", {"age": str(growth_stage)}))
            elif crop_type == "beetroots":
                # Beetroots have stages 0-3
                beetroot_stage = min(3, growth_stage // 2)
                ED.placeBlock((x + dx, y, z + dz), Block("beetroots", {"age": str(beetroot_stage)}))
    
    # Add a scarecrow
    scarecrow_x = x
    scarecrow_z = z
    
    # Base fence post
    ED.placeBlock((scarecrow_x, y, scarecrow_z), Block(theme_materials["details"][1]))
    ED.placeBlock((scarecrow_x, y + 1, scarecrow_z), Block(theme_materials["details"][1]))
    
    # Arms (fence)
    ED.placeBlock((scarecrow_x - 1, y + 1, scarecrow_z), Block("oak_fence"))
    ED.placeBlock((scarecrow_x + 1, y + 1, scarecrow_z), Block("oak_fence"))
    
    # Head (jack-o-lantern or carved pumpkin)
    head_block = "carved_pumpkin" if random() < 0.7 else "jack_o_lantern"
    ED.placeBlock((scarecrow_x, y + 2, scarecrow_z), Block(head_block))
    
    # Add a water source
    water_x = x + garden_width//2
    water_z = z - garden_length//2
    
    ED.placeBlock((water_x, y - 1, water_z), Block("stone"))
    ED.placeBlock((water_x, y, water_z), Block("water"))
    
    # Add some decorative elements
    for _ in range(3):
        deco_x = x + randint(-garden_width//2, garden_width//2)
        deco_z = z + randint(-garden_length//2, garden_length//2)
        
        # Only place on border path
        if abs(deco_x - x) == garden_width//2 or abs(deco_z - z) == garden_length//2:
            deco_type = choice(["composter", "barrel", "lantern", "flower_pot"])
            ED.placeBlock((deco_x, y, deco_z), Block(deco_type))

def build_house_procedural():
    """Build a procedurally generated house adapted to the terrain"""
    # Analyze terrain to find best building site
    potential_sites = analyze_terrain(margin=10)
    
    # Choose a site (with some randomness)
    quality_threshold = 0.8  # Use top 80% of sites
    top_sites = potential_sites[:max(1, int(len(potential_sites) * quality_threshold))]
    selected_site = choice(top_sites)
    
    print(f"Selected building site: {selected_site['type']} (quality: {selected_site['quality']:.1f})")
    
    # Determine the dimensions of the house based on site
    if selected_site['type'] == "hillside" or selected_site['type'] == "elevated":
        # Multi-tiered building to fit terrain
        width = randint(9, 15) | 1  # Force odd number
        length = randint(11, 19) | 1
        height = randint(5, 8)
        
    elif selected_site['type'] == "shallow_water" or selected_site['type'] == "waterfront":
        # For water sites, use elevated platform
        width = randint(11, 17) | 1
        length = randint(11, 17) | 1
        height = randint(4, 6)
        
    else:  # flat or default
        # Typical house dimensions
        width = randint(13, 19) | 1
        length = randint(15, 23) | 1
        height = randint(5, 8)
    
    # Adjust size based on biome information
    if "taiga" in center_biome or "cold" in center_biome:
        # More compact houses in cold biomes
        width = max(9, width - 4)
        length = max(11, length - 4)
        height = min(7, height + 1)  # Taller for snow load
        
    elif "desert" in center_biome:
        # Wider, shorter in desert
        width = min(23, width + 4)
        length = min(27, length + 4)
        height = max(4, height - 1)
    
    # Now we have a site and dimensions, determine appropriate style
    # Get appropriate materials for the biome
    biome_theme = get_theme_for_biome(center_biome)
    theme_materials = THEMES.get(biome_theme, THEMES["plains"])
    
    # Choose a building style based on the site and biome
    building_style = choose_building_style(selected_site, biome_theme)
    
    # Create a detailed plan for how the building should adapt to terrain
    site_plan = create_terrain_adaptation_plan(
        selected_site, width, length, height, building_style
    )
    
    # Generate appropriate interior layout
    global layout  # Make accessible to other functions
    layout = create_house_layout(width, length, building_style, site_plan)
    
    # Get coordinates
    xaxis, zaxis, y = selected_site["x"], selected_site["z"], selected_site["y"]
    
    # Apply any height adjustments from site plan
    if "base_height" in site_plan:
        y = site_plan["base_height"]
    
    # Now build the structure in stages
    # 1. Foundation
    foundation_adjust_map = build_foundation(
        ED, xaxis, zaxis, y, width, length, building_style, site_plan, theme_materials
    )
    
    # 2. Walls and structural elements
    build_walls_and_structure(
        ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials
    )
    
    # 3. Roof
    build_roof(
        ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials
    )
    
    # 4. Interior details
    add_interior_details(
        ED, xaxis, zaxis, y, width, length, height, building_style, layout, site_plan, theme_materials
    )
    
    # 5. Garden and landscaping
    add_garden_and_landscaping(
        ED, xaxis, zaxis, y, width, length, building_style, theme_materials, selected_site
    )
    
    print(f"Completed {building_style} style {biome_theme} house at ({xaxis}, {y}, {zaxis})")
    
    # Return the house details
    return {
        "position": (xaxis, y, zaxis),
        "dimensions": (width, length, height),
        "style": building_style,
        "biome": biome_theme,
        "site_type": selected_site["type"]
    }

def main():
    try:
        print("Starting procedural house generation...")
        
        # Generate the house
        house_details = build_house_procedural()
        
        print(f"Successfully built a {house_details['style']} house in a {house_details['biome']} biome!")
        print(f"Located at {house_details['position']} with dimensions {house_details['dimensions']}")
        print(f"Built on {house_details['site_type']} terrain")
        
        # Make sure all changes are written
        ED.flushBuffer()
        
    except KeyboardInterrupt:
        print("Build canceled!")
        ED.flushBuffer()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        ED.flushBuffer()

if __name__ == "__main__":
    main()