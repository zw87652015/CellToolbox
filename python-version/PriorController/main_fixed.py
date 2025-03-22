"""
Prior Controller Application
---------------------------
Main entry point for the Prior Controller application.
"""

import os
import sys
import tkinter as tk
from prior_controller_ui_fixed import PriorControllerUI

def main():
    """Main function to start the application."""
    root = tk.Tk()
    app = PriorControllerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
