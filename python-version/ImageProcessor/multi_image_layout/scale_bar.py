"""
Scale Bar Module
Renders calibrated scale bars on composite images
"""
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional
from enum import Enum


class Objective(Enum):
    """Microscope objective magnifications"""
    OBJ_4X = "4X"
    OBJ_10X = "10X"
    OBJ_20X = "20X"
    NONE = "无"


class ScaleBarStyle:
    """Scale bar rendering style configuration"""
    
    def __init__(self):
        self.enabled: bool = False
        self.objective: Objective = Objective.NONE
        self.scale_length_um: float = 10.0  # Length in micrometers
        self.bar_height: int = 5  # Height in pixels
        self.bar_color: Tuple[int, int, int] = (255, 255, 255)  # White
        self.bg_color: Tuple[int, int, int] = (0, 0, 0)  # Black
        self.with_background: bool = True
        self.font_size: int = 16
        self.text_color: Tuple[int, int, int] = (255, 255, 255)
        
        # Calibrations (μm/px for each objective)
        self.calibrations = {
            Objective.OBJ_4X: None,  # To be filled
            Objective.OBJ_10X: 1.0304,  # Given calibration
            Objective.OBJ_20X: None,  # To be filled
            Objective.NONE: None
        }
    
    def get_calibration(self) -> Optional[float]:
        """Get calibration for current objective"""
        return self.calibrations.get(self.objective, None)
    
    def set_calibration(self, objective: Objective, um_per_px: float):
        """Set calibration for an objective"""
        self.calibrations[objective] = um_per_px
    
    def calculate_bar_width_px(self, scale_factor: float = 1.0) -> Optional[int]:
        """
        Calculate scale bar width in pixels
        
        Args:
            scale_factor: Scaling factor from original image to cell size
                         (cell_size / original_size)
        
        Returns:
            Width in pixels for the scaled image
        """
        calibration = self.get_calibration()
        if calibration is None or calibration == 0:
            return None
        
        # Calculate width in original image pixels
        # scale_length_um / (um_per_px) = pixels in original image
        width_px_original = self.scale_length_um / calibration
        
        # Scale to cell size
        width_px_scaled = int(width_px_original * scale_factor)
        
        return width_px_scaled


class ScaleBarRenderer:
    """Renders scale bar on images"""
    
    def __init__(self, style: ScaleBarStyle):
        self.style = style
        self._font = None
    
    def _get_font(self) -> ImageFont.FreeTypeFont:
        """Get font for text"""
        if self._font is None:
            try:
                # Try to use Arial
                self._font = ImageFont.truetype("arial.ttf", self.style.font_size)
            except:
                try:
                    # Fallback to default
                    self._font = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", self.style.font_size)
                except:
                    # Use default bitmap font
                    self._font = ImageFont.load_default()
        return self._font
    
    def draw_scale_bar(self, image: Image.Image, 
                      position: str = "bottom_center",
                      margin: int = 20,
                      scale_factor: float = 1.0) -> Image.Image:
        """
        Draw scale bar on image
        
        Args:
            image: PIL Image to draw on
            position: Position string (bottom_left, bottom_center, bottom_right)
            margin: Margin from edge in pixels
            scale_factor: Scaling factor from original image to cell size
        
        Returns:
            Image with scale bar drawn
        """
        if not self.style.enabled:
            return image
        
        # Calculate bar width with scale factor
        bar_width_px = self.style.calculate_bar_width_px(scale_factor)
        if bar_width_px is None or bar_width_px <= 0:
            return image
        
        # Create drawing context
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Get image dimensions
        img_width, img_height = img_copy.size
        
        # Prepare text
        text = f"{self.style.scale_length_um:.0f} μm"
        font = self._get_font()
        
        # Get text size
        try:
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except:
            text_width = len(text) * self.style.font_size // 2
            text_height = self.style.font_size
        
        # Calculate total size
        total_width = max(bar_width_px, text_width) + 20  # 10px padding each side
        total_height = self.style.bar_height + text_height + 15  # Spacing between bar and text
        
        # Calculate position
        if position == "bottom_left":
            x = margin
        elif position == "bottom_right":
            x = img_width - total_width - margin
        else:  # bottom_center
            x = (img_width - total_width) // 2
        
        y = img_height - total_height - margin
        
        # Draw background if enabled
        if self.style.with_background:
            bg_padding = 5
            draw.rectangle(
                [x - bg_padding, y - bg_padding, 
                 x + total_width + bg_padding, y + total_height + bg_padding],
                fill=self.style.bg_color,
                outline=None
            )
        
        # Draw scale bar
        bar_x = x + (total_width - bar_width_px) // 2
        bar_y = y + 5
        
        draw.rectangle(
            [bar_x, bar_y, bar_x + bar_width_px, bar_y + self.style.bar_height],
            fill=self.style.bar_color,
            outline=self.style.bar_color
        )
        
        # Draw text
        text_x = x + (total_width - text_width) // 2
        text_y = bar_y + self.style.bar_height + 5
        
        draw.text((text_x, text_y), text, fill=self.style.text_color, font=font)
        
        return img_copy
    
    def can_draw(self) -> bool:
        """Check if scale bar can be drawn"""
        if not self.style.enabled:
            return False
        
        if self.style.objective == Objective.NONE:
            return False
        
        calibration = self.style.get_calibration()
        if calibration is None or calibration == 0:
            return False
        
        return True
    
    def get_info_text(self) -> str:
        """Get information text about current scale bar"""
        if not self.can_draw():
            return "未配置"
        
        bar_width_px = self.style.calculate_bar_width_px()
        calibration = self.style.get_calibration()
        
        return (f"{self.style.objective.value}: "
                f"{self.style.scale_length_um:.1f} μm = {bar_width_px} px\n"
                f"比例: {calibration:.4f} μm/px")
