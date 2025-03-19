import pygame
import json
import numpy as np
import sys
import ctypes
import math

# Win32 constants
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002

# Win32 API functions
SetWindowPos = ctypes.windll.user32.SetWindowPos

def load_calibration_data():
    """Load the latest calibration data"""
    try:
        with open('calibration/latest_calibration.json', 'r') as f:
            data = json.load(f)
            required_fields = ['scale', 'rotation', 'offset_x', 'offset_y', 
                             'camera_resolution', 'projector_resolution', 'fov_corners']
            if all(field in data for field in required_fields):
                return data
            else:
                print("Error: Calibration data is missing required fields")
                return None
    except FileNotFoundError:
        print("Error: No calibration data found. Please run calibration first.")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid calibration data format")
        return None

def main():
    # Initialize Pygame
    pygame.init()
    
    # Load calibration data
    calibration_data = load_calibration_data()
    if calibration_data is None:
        print("Failed to load calibration data")
        sys.exit(1)
    
    # Set up display
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    screen = pygame.display.set_mode((2560, 1600), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("Manual Donut Tool")
    
    # Get window handle and set it to stay on top
    hwnd = pygame.display.get_wm_info()['window']
    SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
    
    # Donut state
    center_x = screen_width // 2
    center_y = screen_height // 2
    outer_radius = 150
    inner_radius = 75
    
    # Interaction state
    dragging_center = False
    dragging_outer = False
    dragging_inner = False
    drag_start_pos = (0, 0)
    drag_start_radius_outer = outer_radius
    drag_start_radius_inner = inner_radius
    
    # Minimum distance between inner and outer radius
    min_radius_gap = 10
    # Minimum inner radius
    min_inner_radius = 10
    # Maximum outer radius
    max_outer_radius = 500
    
    # Scaling factor for mouse wheel
    SCALE_FACTOR = 0.05  # 5% change per scroll
    KEYBOARD_SCALE_FACTOR = 0.01  # 1% change per keypress (more precise)
    
    # Scaling delay for keyboard (to slow down continuous scaling)
    scale_delay = 0
    SCALE_DELAY_MAX = 3  # Only apply scaling every 3 frames
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    
    # Movement speed for keyboard controls (pixels per frame)
    MOVE_SPEED = 1  # More precise movement
    MOVE_SPEED_FAST = 5  # Faster movement with shift key
    
    # Key state tracking for continuous movement
    keys_pressed = {
        pygame.K_LEFT: False,
        pygame.K_RIGHT: False,
        pygame.K_UP: False,
        pygame.K_DOWN: False,
        pygame.K_LSHIFT: False,
        pygame.K_RSHIFT: False,
        pygame.K_MINUS: False,  # For shrinking
        pygame.K_EQUALS: False  # For growing
    }
    
    # Font for displaying radius values
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 24)
    small_font = pygame.font.SysFont('Arial', 16)  # Smaller font for instructions
    
    # Function to scale the donut while maintaining thickness
    def scale_donut(scale_up, factor=SCALE_FACTOR):
        nonlocal outer_radius, inner_radius
        
        # Calculate current thickness (absolute value)
        thickness = outer_radius - inner_radius
        
        if scale_up:
            # Increase outer radius
            new_outer = min(outer_radius * (1 + factor), max_outer_radius)
            # Maintain absolute thickness
            new_inner = new_outer - thickness
        else:
            # Decrease outer radius
            new_outer = max(outer_radius * (1 - factor), thickness + min_inner_radius)
            # Maintain absolute thickness
            new_inner = new_outer - thickness
        
        # Ensure inner radius doesn't go below minimum
        new_inner = max(new_inner, min_inner_radius)
        
        # Update radii
        outer_radius = new_outer
        inner_radius = new_inner
    
    # Main game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Track key state for continuous movement
                elif event.key in keys_pressed:
                    keys_pressed[event.key] = True
            
            elif event.type == pygame.KEYUP:
                # Update key state when released
                if event.key in keys_pressed:
                    keys_pressed[event.key] = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    
                    # Calculate distance from center
                    dx = mouse_x - center_x
                    dy = mouse_y - center_y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    # Check if clicking on inner circle border (with 10px tolerance)
                    if abs(distance - inner_radius) < 10:
                        dragging_inner = True
                        drag_start_pos = (mouse_x, mouse_y)
                        drag_start_radius_inner = inner_radius
                    
                    # Check if clicking on outer circle border (with 10px tolerance)
                    elif abs(distance - outer_radius) < 10:
                        dragging_outer = True
                        drag_start_pos = (mouse_x, mouse_y)
                        drag_start_radius_outer = outer_radius
                    
                    # Check if clicking inside the donut (for dragging the whole shape)
                    elif inner_radius < distance < outer_radius or distance < inner_radius:
                        dragging_center = True
                        drag_start_pos = (mouse_x, mouse_y)
                
                # Mouse wheel for scaling while maintaining thickness
                elif event.button == 4:  # Scroll up
                    scale_donut(True, SCALE_FACTOR)
                
                elif event.button == 5:  # Scroll down
                    scale_donut(False, SCALE_FACTOR)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    dragging_center = False
                    dragging_outer = False
                    dragging_inner = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging_center:
                    # Move the entire donut
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - drag_start_pos[0]
                    dy = mouse_y - drag_start_pos[1]
                    center_x += dx
                    center_y += dy
                    drag_start_pos = (mouse_x, mouse_y)
                
                elif dragging_outer:
                    # Resize the outer circle
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - center_x
                    dy = mouse_y - center_y
                    new_distance = math.sqrt(dx*dx + dy*dy)
                    
                    # Ensure outer radius is at least min_radius_gap larger than inner radius
                    # and not larger than max_outer_radius
                    outer_radius = max(min(new_distance, max_outer_radius), inner_radius + min_radius_gap)
                
                elif dragging_inner:
                    # Resize the inner circle
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - center_x
                    dy = mouse_y - center_y
                    new_distance = math.sqrt(dx*dx + dy*dy)
                    
                    # Ensure inner radius is at least min_inner_radius
                    # and at most (outer_radius - min_radius_gap)
                    inner_radius = max(min(new_distance, outer_radius - min_radius_gap), min_inner_radius)
        
        # Handle continuous keyboard movement
        speed = MOVE_SPEED_FAST if keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT] else MOVE_SPEED
        
        if keys_pressed[pygame.K_LEFT]:
            center_x -= speed
        if keys_pressed[pygame.K_RIGHT]:
            center_x += speed
        if keys_pressed[pygame.K_UP]:
            center_y -= speed
        if keys_pressed[pygame.K_DOWN]:
            center_y += speed
            
        # Handle continuous scaling with - and = keys (with reduced speed)
        if keys_pressed[pygame.K_EQUALS] or keys_pressed[pygame.K_MINUS]:
            scale_delay += 1
            if scale_delay >= SCALE_DELAY_MAX:
                scale_delay = 0
                if keys_pressed[pygame.K_EQUALS]:  # = key for growing
                    scale_donut(True, KEYBOARD_SCALE_FACTOR)
                if keys_pressed[pygame.K_MINUS]:  # - key for shrinking
                    scale_donut(False, KEYBOARD_SCALE_FACTOR)
        
        # Clear the screen
        screen.fill(BLACK)
        
        # Draw FOV borders using calibration data if available
        if calibration_data and 'fov_corners' in calibration_data:
            fov_corners = calibration_data['fov_corners']
            for i in range(len(fov_corners)):
                start_point = fov_corners[i]
                end_point = fov_corners[(i + 1) % len(fov_corners)]
                pygame.draw.line(screen, WHITE, 
                               (int(start_point[0]), int(start_point[1])),
                               (int(end_point[0]), int(end_point[1])), 1)
        
        # Draw the donut (filled white ring)
        pygame.draw.circle(screen, WHITE, (center_x, center_y), outer_radius)  # Outer circle (filled)
        pygame.draw.circle(screen, BLACK, (center_x, center_y), inner_radius)  # Inner circle (cuts out center)
        
        # Draw the borders of the circles for better visibility during editing
        pygame.draw.circle(screen, WHITE, (center_x, center_y), outer_radius, 2)  # Outer border
        pygame.draw.circle(screen, WHITE, (center_x, center_y), inner_radius, 2)  # Inner border
        
        # Draw radius values
        outer_text = font.render(f"Outer: {int(outer_radius)}", True, WHITE)
        inner_text = font.render(f"Inner: {int(inner_radius)}", True, WHITE)
        screen.blit(outer_text, (20, 20))
        screen.blit(inner_text, (20, 50))
        
        # Draw instructions
        instructions = [
            "ESC: Exit",
            "Arrow keys: Move donut (hold Shift for faster movement)",
            "Mouse wheel: Scale donut quickly",
            "-/= keys: Scale donut precisely",
            "Drag center/inside: Move donut",
            "Drag inner circle: Resize inner radius",
            "Drag outer circle: Resize outer radius"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, GREEN)
            screen.blit(text, (20, 100 + i * 20))  # Reduced vertical spacing
        
        # Update the display
        pygame.display.flip()
        clock.tick(60)
    
    # Save donut parameters before quitting
    donut_params = {
        "center_x": center_x,
        "center_y": center_y,
        "outer_radius": outer_radius,
        "inner_radius": inner_radius
    }
    
    try:
        with open('donut_params.json', 'w') as f:
            json.dump(donut_params, f)
        print("Donut parameters saved successfully")
    except Exception as e:
        print(f"Error saving donut parameters: {e}")
    
    # Quit Pygame
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
