import cv2
import wmi

def get_camera_names():
    """Get a list of camera friendly names using WMI."""
    try:
        w = wmi.WMI()
        cameras = w.query("SELECT * FROM Win32_PnPEntity WHERE (PNPClass = 'Image' OR PNPClass = 'Camera')")
        return [camera.Name for camera in cameras]
    except Exception as e:
        print(f"Error getting camera names: {str(e)}")
        return []

def main():
    # Get camera names
    camera_names = get_camera_names()
    print("\nDetected cameras:", camera_names)
    
    # Try to open each camera and show its properties
    for idx in range(5):  # Check first 5 indices
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                # Get current resolution
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"\nCamera {idx}:")
                print(f"Current resolution: {width}x{height}")
                
                # Try to set 1080p resolution
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                
                # Get actual resolution (might be different from requested)
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"Set resolution to: {actual_width}x{actual_height}")
                
                cap.release()
        except Exception as e:
            continue
    
    # Let user select camera
    camera_idx = int(input("\nEnter camera index to view: "))
    
    # Open selected camera
    print(f"Opening camera {camera_idx}...")
    cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # Try to set 1080p resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    print("\nPress 'q' to quit")
    
    try:
        while True:
            # Read a frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Couldn't read frame")
                break
            
            # Display the frame
            cv2.imshow('Camera View', frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
