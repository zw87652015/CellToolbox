"""
Monitor utilities for multi-monitor support
"""

try:
    import win32api
    HAS_WIN32API = True
except ImportError:
    HAS_WIN32API = False
    print("win32api not available. Multi-monitor support will be limited.")

def get_monitor_info():
    """
    Get information about available monitors
    
    Returns:
        list: List of monitor information dictionaries with keys:
            - left, top, right, bottom: Monitor boundaries
            - width, height: Monitor dimensions
            - is_primary: Boolean indicating if this is the primary monitor
    """
    monitors = []
    
    if HAS_WIN32API:
        try:
            # Get all monitors
            monitor_enum = win32api.EnumDisplayMonitors()
            
            for i, (hmon, hdc, rect) in enumerate(monitor_enum):
                monitor_info = win32api.GetMonitorInfo(hmon)
                
                # Get monitor rectangle
                monitor_rect = monitor_info['Monitor']
                work_rect = monitor_info['Work']
                
                monitor_data = {
                    'left': monitor_rect[0],
                    'top': monitor_rect[1], 
                    'right': monitor_rect[2],
                    'bottom': monitor_rect[3],
                    'width': monitor_rect[2] - monitor_rect[0],
                    'height': monitor_rect[3] - monitor_rect[1],
                    'work_left': work_rect[0],
                    'work_top': work_rect[1],
                    'work_right': work_rect[2],
                    'work_bottom': work_rect[3],
                    'work_width': work_rect[2] - work_rect[0],
                    'work_height': work_rect[3] - work_rect[1],
                    'is_primary': monitor_info['Flags'] == 1
                }
                
                monitors.append(monitor_data)
                
        except Exception as e:
            print(f"Error getting monitor info: {e}")
            # Fallback to single monitor
            monitors = [{
                'left': 0,
                'top': 0,
                'right': 1920,
                'bottom': 1080,
                'width': 1920,
                'height': 1080,
                'work_left': 0,
                'work_top': 0,
                'work_right': 1920,
                'work_bottom': 1040,
                'work_width': 1920,
                'work_height': 1040,
                'is_primary': True
            }]
    else:
        # Fallback when win32api is not available
        monitors = [{
            'left': 0,
            'top': 0,
            'right': 1920,
            'bottom': 1080,
            'width': 1920,
            'height': 1080,
            'work_left': 0,
            'work_top': 0,
            'work_right': 1920,
            'work_bottom': 1040,
            'work_width': 1920,
            'work_height': 1040,
            'is_primary': True
        }]
    
    return monitors
