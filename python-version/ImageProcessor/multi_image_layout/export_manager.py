"""
Export Manager Module
Handles exporting to multiple formats (PNG, JPG, TIFF, PDF, SVG, EPS)
"""
import os
import hashlib
import json
from datetime import datetime
from typing import List, Tuple, Optional, Callable
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io


class ExportFormat:
    """Export format options"""
    PNG = "PNG"
    JPG = "JPG"
    TIFF = "TIFF"
    PDF = "PDF"
    SVG = "SVG"
    EPS = "EPS"
    
    ALL_FORMATS = [PNG, JPG, TIFF, PDF, SVG, EPS]
    BITMAP_FORMATS = [PNG, JPG, TIFF]
    VECTOR_FORMATS = [PDF, SVG, EPS]


class ExportSettings:
    """Export configuration"""
    
    def __init__(self):
        self.formats: List[str] = [ExportFormat.PNG]
        self.dpi = 300
        self.output_dir = ""
        self.filename_template = "layout_{cols}x{rows}_{datetime}"
        self.include_md5 = True
        self.save_log = True


class ExportManager:
    """Manages export operations"""
    
    def __init__(self, settings: ExportSettings):
        self.settings = settings
        self.progress_callback: Optional[Callable[[int, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """Set progress callback function(percent, message)"""
        self.progress_callback = callback
    
    def _report_progress(self, percent: int, message: str):
        """Report progress"""
        if self.progress_callback:
            self.progress_callback(percent, message)
    
    def export(self, composite_image: Image.Image, 
               cols: int, rows: int, 
               cell_width: int, cell_height: int) -> Tuple[bool, str, List[str]]:
        """
        Export composite image to specified formats
        Returns: (success, message, list of created files)
        """
        if not self.settings.output_dir:
            return False, "未指定输出目录", []
        
        os.makedirs(self.settings.output_dir, exist_ok=True)
        
        # Generate filename
        filename_base = self._generate_filename(cols, rows, cell_width, cell_height)
        
        created_files = []
        
        try:
            # Export to each format
            total_formats = len(self.settings.formats)
            for idx, fmt in enumerate(self.settings.formats):
                progress = 10 + int(70 * idx / total_formats)
                self._report_progress(progress, f"导出 {fmt} 格式...")
                
                file_path = self._export_format(
                    composite_image, filename_base, fmt, cols, rows
                )
                if file_path:
                    created_files.append(file_path)
            
            # Generate MD5 checksums
            if self.settings.include_md5 and created_files:
                self._report_progress(85, "生成MD5校验...")
                md5_file = self._generate_md5_file(created_files, filename_base)
                if md5_file:
                    created_files.append(md5_file)
            
            # Save export log
            if self.settings.save_log:
                self._report_progress(90, "保存导出日志...")
                log_file = self._save_export_log(
                    filename_base, cols, rows, cell_width, cell_height, created_files
                )
                if log_file:
                    created_files.append(log_file)
            
            self._report_progress(100, "导出完成")
            return True, f"成功导出 {len(created_files)} 个文件", created_files
        
        except Exception as e:
            return False, f"导出失败: {str(e)}", created_files
    
    def _generate_filename(self, cols: int, rows: int, width: int, height: int) -> str:
        """Generate base filename from template"""
        template = self.settings.filename_template
        
        # Replace variables
        now = datetime.now()
        replacements = {
            '{cols}': str(cols),
            '{rows}': str(rows),
            '{width}': str(width),
            '{height}': str(height),
            '{datetime}': now.strftime("%Y%m%d_%H%M%S"),
            '{date}': now.strftime("%Y%m%d"),
            '{time}': now.strftime("%H%M%S"),
        }
        
        filename = template
        for key, value in replacements.items():
            filename = filename.replace(key, value)
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        return filename
    
    def _export_format(self, image: Image.Image, filename_base: str, 
                      fmt: str, cols: int, rows: int) -> Optional[str]:
        """Export to specific format"""
        try:
            if fmt == ExportFormat.PNG:
                return self._export_png(image, filename_base)
            elif fmt == ExportFormat.JPG:
                return self._export_jpg(image, filename_base)
            elif fmt == ExportFormat.TIFF:
                return self._export_tiff(image, filename_base)
            elif fmt == ExportFormat.PDF:
                return self._export_pdf(image, filename_base)
            elif fmt == ExportFormat.SVG:
                return self._export_svg(image, filename_base, cols, rows)
            elif fmt == ExportFormat.EPS:
                return self._export_eps(image, filename_base)
            return None
        except Exception as e:
            print(f"Error exporting {fmt}: {e}")
            return None
    
    def _export_png(self, image: Image.Image, filename_base: str) -> str:
        """Export to PNG"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.png")
        
        # Convert to RGB if necessary
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        dpi_tuple = (self.settings.dpi, self.settings.dpi)
        image.save(file_path, 'PNG', dpi=dpi_tuple)
        return file_path
    
    def _export_jpg(self, image: Image.Image, filename_base: str) -> str:
        """Export to JPG"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.jpg")
        
        # Convert to RGB (JPG doesn't support alpha)
        if image.mode != 'RGB':
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            else:
                image = image.convert('RGB')
        
        dpi_tuple = (self.settings.dpi, self.settings.dpi)
        image.save(file_path, 'JPEG', dpi=dpi_tuple, quality=95)
        return file_path
    
    def _export_tiff(self, image: Image.Image, filename_base: str) -> str:
        """Export to TIFF"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.tiff")
        
        dpi_tuple = (self.settings.dpi, self.settings.dpi)
        image.save(file_path, 'TIFF', dpi=dpi_tuple, compression='tiff_lzw')
        return file_path
    
    def _export_pdf(self, image: Image.Image, filename_base: str) -> str:
        """Export to PDF"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.pdf")
        
        # Convert to RGB
        if image.mode != 'RGB':
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            else:
                image = image.convert('RGB')
        
        # Calculate PDF page size to fit image
        img_width_inch = image.width / self.settings.dpi
        img_height_inch = image.height / self.settings.dpi
        page_size = (img_width_inch * 72, img_height_inch * 72)  # Convert to points
        
        # Create PDF
        c = canvas.Canvas(file_path, pagesize=page_size)
        
        # Save image to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Draw image
        c.drawImage(ImageReader(img_buffer), 0, 0, 
                   width=page_size[0], height=page_size[1])
        c.save()
        
        return file_path
    
    def _export_svg(self, image: Image.Image, filename_base: str, 
                   cols: int, rows: int) -> str:
        """Export to SVG (simplified - embeds bitmap)"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.svg")
        
        # Convert image to base64
        img_buffer = io.BytesIO()
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        import base64
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        # Create SVG
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{image.width}" height="{image.height}" 
     xmlns="http://www.w3.org/2000/svg" 
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <title>Image Layout {cols}x{rows}</title>
  <image width="{image.width}" height="{image.height}" 
         xlink:href="data:image/png;base64,{img_base64}"/>
</svg>'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return file_path
    
    def _export_eps(self, image: Image.Image, filename_base: str) -> str:
        """Export to EPS"""
        file_path = os.path.join(self.settings.output_dir, f"{filename_base}.eps")
        
        # Convert to RGB
        if image.mode != 'RGB':
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            else:
                image = image.convert('RGB')
        
        # PIL can save EPS directly
        image.save(file_path, 'EPS')
        return file_path
    
    def _generate_md5_file(self, files: List[str], filename_base: str) -> Optional[str]:
        """Generate MD5 checksum file"""
        try:
            md5_file = os.path.join(self.settings.output_dir, f"{filename_base}_MD5.txt")
            
            with open(md5_file, 'w', encoding='utf-8') as f:
                f.write(f"MD5 Checksums\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for file_path in files:
                    if os.path.exists(file_path):
                        md5_hash = self._calculate_md5(file_path)
                        filename = os.path.basename(file_path)
                        f.write(f"{md5_hash}  {filename}\n")
            
            return md5_file
        except Exception as e:
            print(f"Error generating MD5 file: {e}")
            return None
    
    def _calculate_md5(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def _save_export_log(self, filename_base: str, cols: int, rows: int,
                        cell_width: int, cell_height: int, 
                        created_files: List[str]) -> Optional[str]:
        """Save export log as JSON"""
        try:
            # Create log directory
            log_dir = os.path.join(self.settings.output_dir, '.export_logs')
            os.makedirs(log_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"log_{timestamp}.json")
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'filename_base': filename_base,
                'layout': {
                    'cols': cols,
                    'rows': rows,
                    'cell_width': cell_width,
                    'cell_height': cell_height,
                },
                'settings': {
                    'dpi': self.settings.dpi,
                    'formats': self.settings.formats,
                    'filename_template': self.settings.filename_template,
                },
                'output_files': [os.path.basename(f) for f in created_files],
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            return log_file
        except Exception as e:
            print(f"Error saving export log: {e}")
            return None
    
    def estimate_export_time(self, image_width: int, image_height: int, 
                            format_count: int) -> float:
        """
        Estimate export time in seconds
        Very rough estimation
        """
        pixels = image_width * image_height
        megapixels = pixels / 1_000_000
        
        # Rough estimates: 0.5s per megapixel per format
        time_per_format = megapixels * 0.5
        total_time = time_per_format * format_count
        
        return max(1.0, total_time)
    
    def check_vector_complexity(self, cols: int, rows: int) -> Tuple[bool, str]:
        """
        Check if vector export might be slow
        Returns: (is_warning, message)
        """
        total_cells = cols * rows
        if total_cells > 1000:
            return True, f"布局包含 {total_cells} 个单元格，矢量格式(SVG/EPS)生成可能较慢"
        return False, ""
