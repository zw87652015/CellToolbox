#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Time-Series Fluorescence Measurement Tool - Main Entry Point
"""

import tkinter as tk
import sys
from pathlib import Path

# Add parent directory to path for shared_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.main_window import BatchFluoMeasurementApp

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = BatchFluoMeasurementApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
