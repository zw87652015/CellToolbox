"""
Image Manager Module
Handles image loading, caching, aspect ratio validation
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
from datetime import datetime


class ImageMetadata:
    """Metadata for a single image"""
    def __init__(self, path: str, width: int, height: int, aspect_ratio: float, mtime: float):
        self.path = path
        self.width = width
        self.height = height
        self.aspect_ratio = aspect_ratio
        self.mtime = mtime
        self._image_cache: Optional[Image.Image] = None
    
    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'width': self.width,
            'height': self.height,
            'aspect_ratio': self.aspect_ratio,
            'mtime': self.mtime
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageMetadata':
        return cls(
            data['path'],
            data['width'],
            data['height'],
            data['aspect_ratio'],
            data['mtime']
        )
    
    def load_image(self, force_reload: bool = False) -> Image.Image:
        """Load the image with caching"""
        if self._image_cache is None or force_reload:
            self._image_cache = Image.open(self.path)
        return self._image_cache
    
    def release_cache(self):
        """Release cached image to free memory"""
        if self._image_cache is not None:
            self._image_cache.close()
            self._image_cache = None


class ImageManager:
    """Manages image collection with caching and validation"""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}
    CACHE_FILENAME = '.image_layout_cache.json'
    ASPECT_RATIO_TOLERANCE = 0.01  # 1% tolerance
    
    def __init__(self):
        self.images: List[ImageMetadata] = []
        self.base_aspect_ratio: Optional[float] = None
        self.cache_dir: Optional[str] = None
    
    def load_from_folder(self, folder_path: str) -> Tuple[bool, str]:
        """
        Load all images from a folder
        Returns: (success, message)
        """
        folder_path = os.path.abspath(folder_path)
        if not os.path.isdir(folder_path):
            return False, "指定的路径不是有效的文件夹"
        
        self.cache_dir = folder_path
        
        # Find all supported image files
        image_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if Path(file).suffix.lower() in self.SUPPORTED_FORMATS:
                    image_files.append(os.path.join(root, file))
        
        if not image_files:
            return False, "文件夹中未检测到图片"
        
        # Sort by filename
        image_files.sort()
        
        # Try to load from cache
        cached_metadata = self._load_cache()
        
        # Load images
        self.images = []
        for file_path in image_files:
            metadata = self._load_image_metadata(file_path, cached_metadata)
            if metadata:
                self.images.append(metadata)
        
        if not self.images:
            return False, "未能加载任何图片"
        
        # Validate aspect ratios
        self.base_aspect_ratio = self.images[0].aspect_ratio
        incompatible = self._find_incompatible_images()
        
        if incompatible:
            return False, f"检测到 {len(incompatible)} 张图片的宽高比与第一张图不同"
        
        # Save cache
        self._save_cache()
        
        return True, f"成功加载 {len(self.images)} 张图片"
    
    def load_from_files(self, file_paths: List[str]) -> Tuple[bool, str]:
        """
        Load specific image files
        Returns: (success, message)
        """
        if not file_paths:
            return False, "未选择任何文件"
        
        # Determine cache directory from first file
        self.cache_dir = os.path.dirname(file_paths[0])
        
        # Try to load from cache
        cached_metadata = self._load_cache()
        
        # Load images
        self.images = []
        for file_path in file_paths:
            if Path(file_path).suffix.lower() not in self.SUPPORTED_FORMATS:
                continue
            metadata = self._load_image_metadata(file_path, cached_metadata)
            if metadata:
                self.images.append(metadata)
        
        if not self.images:
            return False, "未能加载任何图片"
        
        # Validate aspect ratios
        self.base_aspect_ratio = self.images[0].aspect_ratio
        incompatible = self._find_incompatible_images()
        
        if incompatible:
            return False, f"检测到 {len(incompatible)} 张图片的宽高比与第一张图不同"
        
        # Save cache
        self._save_cache()
        
        return True, f"成功加载 {len(self.images)} 张图片"
    
    def crop_incompatible_images(self) -> int:
        """
        Crop incompatible images to match base aspect ratio
        Returns: number of images cropped
        """
        if not self.base_aspect_ratio:
            return 0
        
        incompatible = self._find_incompatible_images()
        count = 0
        
        for idx in incompatible:
            metadata = self.images[idx]
            img = metadata.load_image()
            
            # Calculate crop dimensions
            target_aspect = self.base_aspect_ratio
            current_aspect = metadata.aspect_ratio
            
            if current_aspect > target_aspect:
                # Too wide, crop width
                new_width = int(metadata.height * target_aspect)
                new_height = metadata.height
                left = (metadata.width - new_width) // 2
                top = 0
            else:
                # Too tall, crop height
                new_width = metadata.width
                new_height = int(metadata.width / target_aspect)
                left = 0
                top = (metadata.height - new_height) // 2
            
            cropped = img.crop((left, top, left + new_width, top + new_height))
            
            # Update metadata
            metadata.width = new_width
            metadata.height = new_height
            metadata.aspect_ratio = new_width / new_height
            metadata._image_cache = cropped
            
            count += 1
        
        # Update cache after cropping
        self._save_cache()
        
        return count
    
    def _load_image_metadata(self, file_path: str, cache: Dict) -> Optional[ImageMetadata]:
        """Load metadata for a single image"""
        try:
            mtime = os.path.getmtime(file_path)
            
            # Check cache
            if file_path in cache:
                cached = cache[file_path]
                if abs(cached['mtime'] - mtime) < 1.0:  # 1 second tolerance
                    return ImageMetadata.from_dict(cached)
            
            # Load from file
            with Image.open(file_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                return ImageMetadata(file_path, width, height, aspect_ratio, mtime)
        
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _find_incompatible_images(self) -> List[int]:
        """Find images with incompatible aspect ratios"""
        if not self.base_aspect_ratio:
            return []
        
        incompatible = []
        for idx, metadata in enumerate(self.images):
            if abs(metadata.aspect_ratio - self.base_aspect_ratio) > self.ASPECT_RATIO_TOLERANCE:
                incompatible.append(idx)
        
        return incompatible
    
    def _load_cache(self) -> Dict:
        """Load metadata cache"""
        if not self.cache_dir:
            return {}
        
        cache_path = os.path.join(self.cache_dir, self.CACHE_FILENAME)
        if not os.path.exists(cache_path):
            return {}
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    
    def _save_cache(self):
        """Save metadata cache"""
        if not self.cache_dir:
            return
        
        cache_path = os.path.join(self.cache_dir, self.CACHE_FILENAME)
        cache_data = {img.path: img.to_dict() for img in self.images}
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_image_count(self) -> int:
        """Get number of loaded images"""
        return len(self.images)
    
    def get_base_size(self) -> Tuple[int, int]:
        """Get size of first image"""
        if not self.images:
            return 100, 100
        return self.images[0].width, self.images[0].height
    
    def release_all_caches(self):
        """Release all cached images to free memory"""
        for img in self.images:
            img.release_cache()
    
    def swap_images(self, idx1: int, idx2: int):
        """Swap two images in the list"""
        if 0 <= idx1 < len(self.images) and 0 <= idx2 < len(self.images):
            self.images[idx1], self.images[idx2] = self.images[idx2], self.images[idx1]
    
    def replace_image(self, idx: int, new_path: str) -> Tuple[bool, str]:
        """Replace an image at given index"""
        if not (0 <= idx < len(self.images)):
            return False, "无效的索引"
        
        metadata = self._load_image_metadata(new_path, {})
        if not metadata:
            return False, "无法加载新图片"
        
        # Check aspect ratio
        if abs(metadata.aspect_ratio - self.base_aspect_ratio) > self.ASPECT_RATIO_TOLERANCE:
            return False, "新图片的宽高比与现有图片不匹配"
        
        # Release old image cache
        self.images[idx].release_cache()
        
        # Replace
        self.images[idx] = metadata
        self._save_cache()
        
        return True, "替换成功"
    
    def estimate_memory_usage(self, cell_width: int, cell_height: int) -> Tuple[float, bool]:
        """
        Estimate memory usage in MB
        Returns: (memory_mb, is_warning)
        """
        count = len(self.images)
        bytes_per_pixel = 4  # RGBA
        memory_bytes = count * cell_width * cell_height * bytes_per_pixel
        memory_mb = memory_bytes / (1024 * 1024)
        
        # Warning if > 1GB or single image > 50MB
        single_mb = cell_width * cell_height * bytes_per_pixel / (1024 * 1024)
        is_warning = memory_mb > 1024 or single_mb > 50
        
        return memory_mb, is_warning
