import cv2

def get_camera_resolution(camera_index=1):
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    
    # Get the resolution
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    
    print(f"Camera Resolution: {int(width)}x{int(height)}")
    
    # Release the camera
    cap.release()

if __name__ == "__main__":
    get_camera_resolution()
