"""
Numbering Module
Handles different numbering formats and rendering
"""
from enum import Enum
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont


class NumberingFormat(Enum):
    """Different numbering format options"""
    ARABIC = "1 2 3"
    CIRCLED = "① ② ③"
    LOWERCASE = "a b c"
    UPPERCASE = "A B C"
    ROMAN_LOWER = "i ii iii"
    ROMAN_UPPER = "I II III"


class NumberingPosition(Enum):
    """Nine-grid position options"""
    TOP_LEFT = "左上"
    TOP_CENTER = "中上"
    TOP_RIGHT = "右上"
    MIDDLE_LEFT = "左中"
    MIDDLE_CENTER = "正中"
    MIDDLE_RIGHT = "右中"
    BOTTOM_LEFT = "左下"
    BOTTOM_CENTER = "中下"
    BOTTOM_RIGHT = "右下"


class NumberingStyle:
    """Numbering style configuration"""
    
    def __init__(self):
        self.enabled = True
        self.format = NumberingFormat.ARABIC
        self.position = NumberingPosition.TOP_LEFT
        self.font_name = "Arial"
        self.font_size = 24
        self.color = (255, 255, 255)  # White
        self.bg_color = (0, 0, 0, 128)  # Semi-transparent black
        self.offset_x = 10
        self.offset_y = 10
        self.with_background = True
        self.padding = 5


class NumberingRenderer:
    """Renders numbering on images"""
    
    # Circled number Unicode ranges
    CIRCLED_NUMBERS = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿"
    
    def __init__(self, style: NumberingStyle):
        self.style = style
        self._font_cache = {}
    
    def _get_font(self, size: int = None) -> ImageFont.FreeTypeFont:
        """Get font with caching"""
        size = size or self.style.font_size
        cache_key = (self.style.font_name, size)
        
        if cache_key not in self._font_cache:
            try:
                self._font_cache[cache_key] = ImageFont.truetype(
                    self.style.font_name, size
                )
            except:
                # Fallback to default font
                try:
                    self._font_cache[cache_key] = ImageFont.truetype(
                        "arial.ttf", size
                    )
                except:
                    # Use default PIL font
                    self._font_cache[cache_key] = ImageFont.load_default()
        
        return self._font_cache[cache_key]
    
    def format_number(self, index: int) -> str:
        """
        Format index to string based on current format
        index is 0-based
        """
        num = index + 1  # Convert to 1-based
        
        if self.style.format == NumberingFormat.ARABIC:
            return str(num)
        
        elif self.style.format == NumberingFormat.CIRCLED:
            if num <= len(self.CIRCLED_NUMBERS):
                return self.CIRCLED_NUMBERS[num - 1]
            else:
                return f"({num})"  # Fallback for large numbers
        
        elif self.style.format == NumberingFormat.LOWERCASE:
            return self._to_letter(num, 'a')
        
        elif self.style.format == NumberingFormat.UPPERCASE:
            return self._to_letter(num, 'A')
        
        elif self.style.format == NumberingFormat.ROMAN_LOWER:
            return self._to_roman(num).lower()
        
        elif self.style.format == NumberingFormat.ROMAN_UPPER:
            return self._to_roman(num)
        
        return str(num)
    
    def _to_letter(self, num: int, start_char: str) -> str:
        """Convert number to letter (a, b, c, ... aa, ab, ...)"""
        result = ""
        num = num - 1  # Make 0-based
        while True:
            result = chr(ord(start_char) + (num % 26)) + result
            num = num // 26
            if num == 0:
                break
            num -= 1
        return result
    
    def _to_roman(self, num: int) -> str:
        """Convert number to Roman numerals"""
        values = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]
        result = ""
        for value, numeral in values:
            count = num // value
            if count:
                result += numeral * count
                num -= value * count
        return result
    
    def calculate_text_position(self, text: str, cell_width: int, cell_height: int) -> Tuple[int, int]:
        """
        Calculate text position based on numbering position
        Returns: (x, y) coordinates for text anchor
        """
        font = self._get_font()
        
        # Get text bounding box
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Add padding
        padding = self.style.padding
        text_width += 2 * padding
        text_height += 2 * padding
        
        # Calculate position based on alignment
        pos = self.style.position
        
        # Horizontal position
        if pos in [NumberingPosition.TOP_LEFT, NumberingPosition.MIDDLE_LEFT, NumberingPosition.BOTTOM_LEFT]:
            x = self.style.offset_x
        elif pos in [NumberingPosition.TOP_CENTER, NumberingPosition.MIDDLE_CENTER, NumberingPosition.BOTTOM_CENTER]:
            x = (cell_width - text_width) // 2
        else:  # RIGHT
            x = cell_width - text_width - self.style.offset_x
        
        # Vertical position
        if pos in [NumberingPosition.TOP_LEFT, NumberingPosition.TOP_CENTER, NumberingPosition.TOP_RIGHT]:
            y = self.style.offset_y
        elif pos in [NumberingPosition.MIDDLE_LEFT, NumberingPosition.MIDDLE_CENTER, NumberingPosition.MIDDLE_RIGHT]:
            y = (cell_height - text_height) // 2
        else:  # BOTTOM
            y = cell_height - text_height - self.style.offset_y
        
        return x, y
    
    def draw_number(self, image: Image.Image, index: int) -> Image.Image:
        """
        Draw number on image
        Args:
            image: PIL Image to draw on
            index: 0-based index
        Returns: Modified image
        """
        if not self.style.enabled:
            return image
        
        # Ensure image is in RGBA mode
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create drawing context
        draw = ImageDraw.Draw(image)
        font = self._get_font()
        
        # Format number
        text = self.format_number(index)
        
        # Calculate position
        x, y = self.calculate_text_position(text, image.width, image.height)
        
        # Get text bounding box
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        padding = self.style.padding
        
        # Draw background if enabled
        if self.style.with_background:
            bg_rect = [
                x - padding,
                y - padding,
                x + text_width + padding,
                y + text_height + padding
            ]
            draw.rectangle(bg_rect, fill=self.style.bg_color)
        
        # Draw text
        draw.text((x, y), text, fill=self.style.color, font=font)
        
        return image
    
    def check_text_overflow(self, index: int, cell_width: int, cell_height: int) -> bool:
        """
        Check if text would overflow cell boundaries
        Returns: True if overflow detected
        """
        text = self.format_number(index)
        font = self._get_font()
        
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0] + 2 * self.style.padding
        text_height = bbox[3] - bbox[1] + 2 * self.style.padding
        
        x, y = self.calculate_text_position(text, cell_width, cell_height)
        
        # Check boundaries
        if x < 0 or y < 0:
            return True
        if x + text_width > cell_width:
            return True
        if y + text_height > cell_height:
            return True
        
        return False
    
    def get_available_fonts(self) -> list:
        """Get list of available system fonts"""
        import os
        import platform
        
        fonts = ["Arial", "Times New Roman", "Courier New", "Verdana", "Georgia"]
        
        # Platform-specific font directories
        if platform.system() == "Windows":
            font_dir = "C:\\Windows\\Fonts"
            if os.path.exists(font_dir):
                for file in os.listdir(font_dir):
                    if file.endswith(('.ttf', '.TTF')):
                        font_name = file[:-4]
                        if font_name not in fonts:
                            fonts.append(font_name)
        
        return sorted(fonts)
