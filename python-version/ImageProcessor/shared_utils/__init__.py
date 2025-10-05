#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Utilities Module for Fluorescence Measurement Tools

This module contains common utilities used across multiple fluorescence
measurement projects to avoid code duplication.

Available modules:
- roi_selector: Interactive ROI selection widget
- config_manager: Configuration management utilities  
- image_utils: Common image processing operations
"""

__version__ = '1.0.0'
__author__ = 'CellToolbox Team'

# Import commonly used classes for convenience
from .roi_selector import ROISelector

__all__ = ['ROISelector']
