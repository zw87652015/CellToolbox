import pygame
import json
import numpy as np
import sys

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
    pygame.display.set_caption("Manual Rectangle Tool")
    
    # Rectangle state
    rect = pygame.Rect(screen_width//4, screen_height//4, 200, 200)  # Initial rectangle
    dragging = False
    resizing = False
    resize_margin = 10  # Pixels from edge where resizing is activated
    
    # Main loop
    running = True
    while running:
        # Fill screen with black
        screen.fill((0, 0, 0))
        
        # Draw FOV borders using calibration data
        fov_corners = calibration_data['fov_corners']
        for i in range(len(fov_corners)):
            start_point = fov_corners[i]
            end_point = fov_corners[(i + 1) % len(fov_corners)]
            pygame.draw.line(screen, (255, 255, 255), 
                           (int(start_point[0]), int(start_point[1])),
                           (int(end_point[0]), int(end_point[1])), 1)
        
        # Draw the rectangle
        pygame.draw.rect(screen, (255, 255, 255), rect)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Check if click is near the edges (for resizing)
                if (abs(mouse_pos[0] - rect.right) < resize_margin and 
                    abs(mouse_pos[1] - rect.bottom) < resize_margin):
                    resizing = True
                elif rect.collidepoint(mouse_pos):
                    dragging = True
                    drag_offset_x = rect.x - mouse_pos[0]
                    drag_offset_y = rect.y - mouse_pos[1]
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                resizing = False
                
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mouse_pos = pygame.mouse.get_pos()
                    rect.x = mouse_pos[0] + drag_offset_x
                    rect.y = mouse_pos[1] + drag_offset_y
                elif resizing:
                    mouse_pos = pygame.mouse.get_pos()
                    width = mouse_pos[0] - rect.left
                    height = mouse_pos[1] - rect.top
                    rect.width = max(10, width)  # Minimum size of 10x10
                    rect.height = max(10, height)
        
        # Update display
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()