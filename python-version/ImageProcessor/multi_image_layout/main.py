"""
Multi-Image Layout Tool - Main Application
Run this file to start the application
"""
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("多图拼接工具")
    app.setOrganizationName("CellToolbox")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
