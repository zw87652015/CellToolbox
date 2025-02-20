import cv2
import numpy as np
import os

def generate_marked_pattern():
    # Pattern parameters (matching calibration.py)
    width = 1920  # screen_width
    height = 1080  # screen_height
    margin = 40
    cell_size = 100
    
    # Calculate usable area
    usable_width = width - 2*margin
    usable_height = height - 2*margin
    num_cols = usable_width // cell_size
    num_rows = usable_height // cell_size
    
    # Create blank black image
    pattern = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw uniform grid first (thin gray lines)
    for i in range(num_cols + 1):
        x = margin + i * cell_size
        cv2.line(pattern, (x, margin), (x, margin + num_rows * cell_size),
                (128, 128, 128), 1)
    
    for j in range(num_rows + 1):
        y = margin + j * cell_size
        cv2.line(pattern, (margin, y), (margin + num_cols * cell_size, y),
                (128, 128, 128), 1)
    
    # Draw position-encoding cells with thick white lines
    for i in range(num_cols):
        for j in range(num_rows):
            x = margin + (i * cell_size)
            y = margin + (j * cell_size)
            
            # Encode X position (vertical lines)
            x_code = format(i, '04b')
            for bit_idx, bit in enumerate(x_code):
                if bit == '1':
                    line_x = int(x + (bit_idx + 1) * cell_size/6)
                    cv2.line(pattern, (line_x, y), (line_x, y + cell_size),
                           (255, 255, 255), 3)
            
            # Encode Y position (horizontal lines)
            y_code = format(j, '04b')
            for bit_idx, bit in enumerate(y_code):
                if bit == '1':
                    line_y = int(y + (bit_idx + 1) * cell_size/6)
                    cv2.line(pattern, (x, line_y), (x + cell_size, line_y),
                           (255, 255, 255), 3)
    
    # Add debug info
    debug_text = [
        f"Screen dimensions: {width}x{height}",
        f"Usable area: {usable_width}x{usable_height}",
        f"Cell size: {cell_size} pixels",
        f"Grid size: {num_cols}x{num_rows} cells",
        f"Position encoding: 4 bits (up to 16 unique positions)",
        f"Line gaps: {cell_size/6:.1f} pixels between encoding positions"
    ]
    
    y_pos = height - 20
    for text in reversed(debug_text):
        cv2.putText(pattern, text, (10, y_pos), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_pos -= 20
    
    # Save pattern
    output_path = os.path.join(os.path.dirname(__file__), "marked_pattern.png")
    cv2.imwrite(output_path, pattern)
    print(f"Pattern saved to: {output_path}")
    print("\nPattern Properties:")
    for text in debug_text:
        print(text)
    
    # Display pattern
    cv2.imshow("Marked Calibration Pattern", pattern)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    generate_marked_pattern()
