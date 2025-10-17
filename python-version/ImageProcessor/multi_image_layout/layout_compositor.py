"""
Layout Compositor Module
Creates the composite image from individual images
"""
from PIL import Image, ImageDraw
from typing import List, Tuple, Optional, Callable
from image_manager import ImageManager
from layout_engine import LayoutEngine
from numbering import NumberingRenderer
from scale_bar import ScaleBarRenderer


class LayoutCompositor:
    """Composes the final layout from individual images"""
    
    def __init__(self, image_manager: ImageManager, layout_engine: LayoutEngine):
        self.image_manager = image_manager
        self.layout_engine = layout_engine
        self.progress_callback: Optional[Callable[[int, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """Set progress callback function(percent, message)"""
        self.progress_callback = callback
    
    def _report_progress(self, percent: int, message: str):
        """Report progress"""
        if self.progress_callback:
            self.progress_callback(percent, message)
    
    def create_composite(self, cell_width: int, cell_height: int,
                        numbering_renderer: Optional[NumberingRenderer] = None,
                        scale_bar_renderer: Optional[ScaleBarRenderer] = None,
                        scale_bar_position: str = "bottom_center",
                        gap: int = 0, border: int = 0,
                        bg_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        """
        Create composite image with all cells
        
        Args:
            cell_width: Width of each cell
            cell_height: Height of each cell
            numbering_renderer: Optional numbering renderer
            gap: Gap between cells in pixels
            border: Border around entire canvas in pixels
            bg_color: Background color RGB tuple
        
        Returns:
            PIL Image of composite
        """
        # Calculate canvas size
        canvas_width, canvas_height = self.layout_engine.get_canvas_size(
            cell_width, cell_height, gap, border
        )
        
        # Create blank canvas
        self._report_progress(0, "创建画布...")
        canvas = Image.new('RGB', (canvas_width, canvas_height), bg_color)
        
        # Get image count
        image_count = self.image_manager.get_image_count()
        
        # Process each image
        for img_idx in range(image_count):
            try:
                progress = int(10 + 70 * img_idx / image_count)
                self._report_progress(progress, f"处理图片 {img_idx + 1}/{image_count}...")
                
                # Get cell position
                col, row = self.layout_engine.get_cell_position(img_idx)
                if col < 0 or row < 0:
                    continue
                
                # Get cell rectangle
                x, y, w, h = self.layout_engine.get_cell_rect(
                    col, row, cell_width, cell_height, gap, border
                )
                
                # Load and resize image
                metadata = self.image_manager.images[img_idx]
                img = metadata.load_image()
                
                # Resize to cell size
                resized = img.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if resized.mode != 'RGB':
                    if resized.mode == 'RGBA':
                        background = Image.new('RGB', resized.size, bg_color)
                        background.paste(resized, mask=resized.split()[3])
                        resized = background
                    else:
                        resized = resized.convert('RGB')
                
                # Add numbering if provided
                if numbering_renderer:
                    resized = numbering_renderer.draw_number(resized, img_idx)
                
                # Paste onto canvas
                canvas.paste(resized, (x, y))
                
            except Exception as e:
                print(f"Error processing image {img_idx}: {e}")
                # Continue with other images
                continue
        
        self._report_progress(85, "完成合成...")
        
        # Draw scale bar if provided
        if scale_bar_renderer and scale_bar_renderer.can_draw():
            self._report_progress(90, "绘制 Scale Bar...")
            
            # Calculate scale factor (cell size / original size)
            original_width, original_height = self.image_manager.get_base_size()
            scale_factor = cell_width / original_width  # Use width as reference
            
            canvas = scale_bar_renderer.draw_scale_bar(
                canvas, scale_bar_position, margin=20, scale_factor=scale_factor
            )
        
        # Release cached images to free memory
        self.image_manager.release_all_caches()
        
        self._report_progress(100, "完成")
        return canvas
    
    def create_preview(self, cell_width: int, cell_height: int,
                      numbering_renderer: Optional[NumberingRenderer] = None,
                      gap: int = 0, border: int = 0,
                      bg_color: Tuple[int, int, int] = (255, 255, 255),
                      max_dimension: int = 2000) -> Image.Image:
        """
        Create a preview composite (potentially downscaled for performance)
        
        Args:
            cell_width: Width of each cell
            cell_height: Height of each cell
            numbering_renderer: Optional numbering renderer
            gap: Gap between cells
            border: Border around canvas
            bg_color: Background color
            max_dimension: Maximum width or height for preview
        
        Returns:
            PIL Image of preview
        """
        # Calculate canvas size
        canvas_width, canvas_height = self.layout_engine.get_canvas_size(
            cell_width, cell_height, gap, border
        )
        
        # Check if we need to scale down for preview
        scale_factor = 1.0
        if canvas_width > max_dimension or canvas_height > max_dimension:
            scale_factor = min(max_dimension / canvas_width, max_dimension / canvas_height)
            
            # Scale all dimensions
            cell_width = int(cell_width * scale_factor)
            cell_height = int(cell_height * scale_factor)
            gap = int(gap * scale_factor)
            border = int(border * scale_factor)
            canvas_width = int(canvas_width * scale_factor)
            canvas_height = int(canvas_height * scale_factor)
            
            # Scale numbering if provided
            if numbering_renderer:
                numbering_renderer.style.font_size = int(
                    numbering_renderer.style.font_size * scale_factor
                )
                numbering_renderer.style.offset_x = int(
                    numbering_renderer.style.offset_x * scale_factor
                )
                numbering_renderer.style.offset_y = int(
                    numbering_renderer.style.offset_y * scale_factor
                )
                numbering_renderer.style.padding = int(
                    numbering_renderer.style.padding * scale_factor
                )
        
        # Create composite at preview size
        return self.create_composite(
            cell_width, cell_height, numbering_renderer, gap, border, bg_color
        )
    
    def estimate_memory(self, cell_width: int, cell_height: int) -> Tuple[float, str]:
        """
        Estimate memory usage
        Returns: (memory_mb, warning_message)
        """
        memory_mb, is_warning = self.image_manager.estimate_memory_usage(
            cell_width, cell_height
        )
        
        if is_warning:
            if memory_mb > 1024:
                warning = f"预计内存使用: {memory_mb:.1f} MB，可能导致内存不足，建议减小单元格尺寸"
            else:
                warning = "单张图片尺寸较大(>50MB)，可能导致内存不足"
        else:
            warning = ""
        
        return memory_mb, warning
    
    def validate_numbering_overflow(self, cell_width: int, cell_height: int,
                                   numbering_renderer: NumberingRenderer) -> List[int]:
        """
        Check which cells have numbering overflow
        Returns: List of image indices with overflow
        """
        if not numbering_renderer or not numbering_renderer.style.enabled:
            return []
        
        overflow_indices = []
        image_count = self.image_manager.get_image_count()
        
        for img_idx in range(image_count):
            if numbering_renderer.check_text_overflow(img_idx, cell_width, cell_height):
                overflow_indices.append(img_idx)
        
        return overflow_indices
