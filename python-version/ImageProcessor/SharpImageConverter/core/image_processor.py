"""
核心图像处理模块
提供TIFF图像加载、像素级放大和导出功能
"""

import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像处理器（支持TIFF和PNG，灰度和RGB）"""
    
    def __init__(self):
        self.original_image = None
        self.original_rgb_image = None  # 保存原始RGB图像
        self.expanded_image = None
        self.original_size = None
        self.bit_depth = None
        self.scale_factor = 1
        self.is_rgb = False  # 是否为RGB图像
        self.selected_channel = None  # 选择的通道 ('R', 'G', 'B', None)
        
    def load_image(self, path, channel=None):
        """
        读取图像文件（支持TIFF和PNG，自动识别灰度或RGB）
        
        Args:
            path: 图像文件路径（TIFF或PNG）
            channel: 对于TIFF RGB图像，选择通道 ('R', 'G', 'B', None)
                    None表示使用灰度图或转换为灰度
                    注意：PNG文件忽略此参数，直接使用原始RGB
            
        Returns:
            tuple: (numpy数组, 原始尺寸(width, height), 位深度, 是否RGB)
            
        Raises:
            ValueError: 如果图像格式不支持
            IOError: 如果文件无法读取
        """
        try:
            # 检查文件类型
            from pathlib import Path
            file_ext = Path(path).suffix.lower()
            is_png = file_ext == '.png'
            
            with Image.open(path) as img:
                img_mode = img.mode
                logger.info(f"检测到图像模式: {img_mode}, 文件类型: {file_ext}")
                
                # 判断是RGB还是灰度
                if img_mode in ['RGB', 'RGBA']:
                    # RGB图像
                    self.is_rgb = True
                    self.original_rgb_image = np.array(img)
                    
                    # 提取RGB图像的位深度（通常是8位）
                    if self.original_rgb_image.dtype == np.uint8:
                        bit_depth = 8
                    elif self.original_rgb_image.dtype == np.uint16:
                        bit_depth = 16
                    else:
                        bit_depth = 8
                    
                    # PNG文件直接使用RGB，TIFF根据通道选择
                    if is_png:
                        # PNG直接使用RGB数组
                        img_array = self.original_rgb_image
                        logger.info("PNG文件：保持RGB格式")
                        self.selected_channel = None
                    else:
                        # TIFF文件：根据通道选择提取单通道
                        if channel == 'R':
                            img_array = self.original_rgb_image[:, :, 0]
                            logger.info("提取红色通道")
                        elif channel == 'G':
                            img_array = self.original_rgb_image[:, :, 1]
                            logger.info("提取绿色通道")
                        elif channel == 'B':
                            img_array = self.original_rgb_image[:, :, 2]
                            logger.info("提取蓝色通道")
                        else:
                            # 转换为灰度
                            img_gray = img.convert('L')
                            img_array = np.array(img_gray)
                            logger.info("转换为灰度图")
                        
                        self.selected_channel = channel
                    
                elif img_mode in ['L', 'I;16', 'I']:
                    # 灰度图像
                    self.is_rgb = False
                    self.original_rgb_image = None
                    self.selected_channel = None
                    img_array = np.array(img)
                    
                    # 确定位深度
                    if img_array.dtype == np.uint8:
                        bit_depth = 8
                    elif img_array.dtype in [np.uint16, np.int16]:
                        bit_depth = 16
                    else:
                        bit_depth = 16  # 默认为16位
                    
                    logger.info("灰度图像")
                    
                else:
                    raise ValueError(f"不支持的图像模式: {img_mode}")
                
                # 保存图像信息
                width, height = img.size
                self.original_image = img_array
                self.original_size = img.size  # (width, height)
                self.bit_depth = bit_depth
                
                logger.info(f"加载图像: {path}")
                logger.info(f"原始尺寸: {width} x {height}, 位深度: {bit_depth}位, RGB: {self.is_rgb}")
                
                return img_array, self.original_size, bit_depth, self.is_rgb
                
        except Exception as e:
            logger.error(f"加载图像文件失败: {e}")
            raise
    
    def load_tiff(self, path, channel=None):
        """向后兼容的方法名，调用load_image"""
        return self.load_image(path, channel)
    
    def pixel_expand(self, image_array, scale_factor):
        """
        使用最近邻插值放大图像（像素块复制）
        
        Args:
            image_array: 输入图像numpy数组
            scale_factor: 放大倍数（整数）
            
        Returns:
            numpy数组: 放大后的图像
        """
        if scale_factor <= 0:
            raise ValueError("放大倍数必须为正整数")
        
        if scale_factor == 1:
            return image_array.copy()
        
        # 处理2D灰度图和3D RGB图
        if len(image_array.shape) == 2:
            h, w = image_array.shape
        else:
            h, w = image_array.shape[:2]
        new_h, new_w = h * scale_factor, w * scale_factor
        
        # 内存检查：如果输出图像超过1GB，发出警告
        output_size_mb = (new_h * new_w * image_array.itemsize) / (1024 * 1024)
        if output_size_mb > 1024:
            logger.warning(f"输出图像尺寸较大: {output_size_mb:.1f} MB")
        
        # 使用numpy.repeat实现像素块放大（最近邻插值）
        logger.info(f"开始放大图像: {w}x{h} -> {new_w}x{new_h} (倍数: {scale_factor}x)")
        
        # 先沿Y轴（axis=0）重复，再沿X轴（axis=1）重复
        expanded = np.repeat(image_array, scale_factor, axis=0)
        expanded = np.repeat(expanded, scale_factor, axis=1)
        
        # 保持原始数据类型
        expanded = expanded.astype(image_array.dtype)
        
        self.expanded_image = expanded
        self.scale_factor = scale_factor
        
        logger.info(f"图像放大完成")
        
        return expanded
    
    def expand_current_image(self, scale_factor, channel=None):
        """
        放大当前加载的图像
        
        Args:
            scale_factor: 放大倍数
            channel: 对于RGB图像，选择通道 ('R', 'G', 'B', None)
            
        Returns:
            numpy数组: 放大后的图像
        """
        if self.original_image is None and self.original_rgb_image is None:
            raise ValueError("请先加载图像")
        
        # 如果是RGB图像且需要切换通道
        if self.is_rgb and channel != self.selected_channel:
            if channel == 'R':
                img_to_expand = self.original_rgb_image[:, :, 0]
                logger.info("切换到红色通道")
            elif channel == 'G':
                img_to_expand = self.original_rgb_image[:, :, 1]
                logger.info("切换到绿色通道")
            elif channel == 'B':
                img_to_expand = self.original_rgb_image[:, :, 2]
                logger.info("切换到蓝色通道")
            else:
                img_to_expand = self.original_image
            
            self.selected_channel = channel
            self.original_image = img_to_expand
        else:
            img_to_expand = self.original_image
        
        return self.pixel_expand(img_to_expand, scale_factor)
    
    def save_image(self, path, image_array=None, format='PNG', bit_depth=None, use_pseudocolor=True):
        """
        保存图像
        
        Args:
            path: 保存路径
            image_array: 要保存的图像数组（如果为None，则保存expanded_image）
            format: 保存格式（'PNG'或'TIFF'）
            bit_depth: 输出位深度（8或16，如果为None则保持原始位深）
            use_pseudocolor: 是否使用伪色图（仅对RGB通道有效）
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if image_array is None:
                if self.expanded_image is None:
                    raise ValueError("没有可保存的图像")
                image_array = self.expanded_image
            
            # 确定输出位深度
            if bit_depth is None:
                bit_depth = self.bit_depth
            
            # 检查是否需要生成伪色图
            should_use_pseudocolor = (use_pseudocolor and 
                                     self.selected_channel in ['R', 'G', 'B'])
            
            # 根据位深度转换图像
            if bit_depth == 8:
                # 转换为8位
                if image_array.dtype == np.uint16:
                    # 16位转8位：线性映射到实际范围
                    img_max = image_array.max()
                    img_min = image_array.min()
                    if img_max > img_min:
                        # 归一化到0-255
                        image_array = ((image_array - img_min).astype(np.float32) / (img_max - img_min) * 255).astype(np.uint8)
                    else:
                        image_array = np.zeros_like(image_array, dtype=np.uint8)
                else:
                    image_array = image_array.astype(np.uint8)
                
                # 检查是否是RGB图像（3D数组）
                if len(image_array.shape) == 3:
                    # RGB图像：直接保存为RGB
                    img = Image.fromarray(image_array, mode='RGB')
                    logger.info("保存RGB图像（8位）")
                elif should_use_pseudocolor:
                    # 生成伪色图
                    img = self._create_pseudocolor_image(image_array, self.selected_channel)
                    logger.info(f"生成{self.selected_channel}通道伪色图")
                else:
                    # 灰度图
                    img = Image.fromarray(image_array, mode='L')
                
            else:
                # 16位图像处理
                if image_array.dtype == np.uint8:
                    # 8位转16位：扩展值域
                    image_array = image_array.astype(np.uint16) * 257
                elif image_array.dtype != np.uint16:
                    # 确保是uint16类型
                    image_array = image_array.astype(np.uint16)
                
                # 16位图像需要特殊处理
                # 使用TIFF格式保存16位，PNG不可靠
                if format.upper() == 'PNG':
                    # PNG 16位支持有限，转换为8位
                    logger.warning("PNG格式对16位支持有限，转换为8位")
                    img_max = image_array.max()
                    img_min = image_array.min()
                    if img_max > img_min:
                        image_array_8bit = ((image_array - img_min).astype(np.float32) / (img_max - img_min) * 255).astype(np.uint8)
                    else:
                        image_array_8bit = np.zeros_like(image_array, dtype=np.uint8)
                    
                    # 检查是否是RGB图像（3D数组）
                    if len(image_array_8bit.shape) == 3:
                        # PNG RGB图像：直接保存为RGB
                        img = Image.fromarray(image_array_8bit, mode='RGB')
                        logger.info("PNG RGB图像（8位）")
                    elif should_use_pseudocolor:
                        # 生成伪色图
                        img = self._create_pseudocolor_image(image_array_8bit, self.selected_channel)
                        logger.info(f"生成{self.selected_channel}通道伪色图（8位）")
                    else:
                        # 灰度图
                        img = Image.fromarray(image_array_8bit, mode='L')
                else:
                    # TIFF格式可以正确保存16位
                    # 检查是否是RGB图像（3D数组）
                    if len(image_array.shape) == 3:
                        # RGB 16位图像：TIFF不直接支持16位RGB，转换为8位
                        logger.warning("TIFF RGB图像转换为8位")
                        img_max = image_array.max()
                        img_min = image_array.min()
                        if img_max > img_min:
                            image_array_8bit = ((image_array - img_min).astype(np.float32) / (img_max - img_min) * 255).astype(np.uint8)
                        else:
                            image_array_8bit = np.zeros_like(image_array, dtype=np.uint8)
                        img = Image.fromarray(image_array_8bit, mode='RGB')
                        logger.info("保存RGB图像（8位）到TIFF")
                    elif should_use_pseudocolor:
                        # 伪色图需要转换为8位RGB
                        logger.warning("16位TIFF伪色图转换为8位RGB")
                        img_max = image_array.max()
                        img_min = image_array.min()
                        if img_max > img_min:
                            image_array_8bit = ((image_array - img_min).astype(np.float32) / (img_max - img_min) * 255).astype(np.uint8)
                        else:
                            image_array_8bit = np.zeros_like(image_array, dtype=np.uint8)
                        img = self._create_pseudocolor_image(image_array_8bit, self.selected_channel)
                        logger.info(f"生成{self.selected_channel}通道伪色图（8位RGB）")
                    else:
                        # 16位灰度TIFF
                        img = Image.fromarray(image_array, mode='I;16')
            
            # 保存图像
            if format.upper() == 'PNG':
                img.save(path, 'PNG', optimize=False)
            elif format.upper() == 'TIFF':
                img.save(path, 'TIFF', compression=None)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"图像已保存: {path}")
            return True
            
        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            return False
    
    def _create_pseudocolor_image(self, gray_array, channel):
        """
        创建伪色图
        
        Args:
            gray_array: 8位灰度数组
            channel: 通道类型 ('R', 'G', 'B')
            
        Returns:
            PIL.Image: RGB伪色图
        """
        # 创建RGB数组
        h, w = gray_array.shape
        rgb_array = np.zeros((h, w, 3), dtype=np.uint8)
        
        # 根据通道填充对应颜色
        if channel == 'R':
            # 红色伪色图：R通道=灰度值，G和B=0
            rgb_array[:, :, 0] = gray_array  # Red
            rgb_array[:, :, 1] = 0           # Green
            rgb_array[:, :, 2] = 0           # Blue
        elif channel == 'G':
            # 绿色伪色图：G通道=灰度值，R和B=0
            rgb_array[:, :, 0] = 0           # Red
            rgb_array[:, :, 1] = gray_array  # Green
            rgb_array[:, :, 2] = 0           # Blue
        elif channel == 'B':
            # 蓝色伪色图：B通道=灰度值，R和G=0
            rgb_array[:, :, 0] = 0           # Red
            rgb_array[:, :, 1] = 0           # Green
            rgb_array[:, :, 2] = gray_array  # Blue
        
        # 创建RGB图像
        return Image.fromarray(rgb_array, mode='RGB')
    
    def get_display_image(self, image_array=None, use_pseudocolor=True):
        """
        获取用于显示的图像（可能是伪色图）
        
        Args:
            image_array: 图像数组（如果为None，使用original_image）
            use_pseudocolor: 是否使用伪色图
            
        Returns:
            numpy数组: 用于显示的图像（可能是RGB）
        """
        if image_array is None:
            image_array = self.original_image
        
        if image_array is None:
            return None
        
        # 检查是否需要生成伪色图
        if use_pseudocolor and self.selected_channel in ['R', 'G', 'B']:
            # 确保是8位
            if image_array.dtype == np.uint16:
                img_max = image_array.max()
                img_min = image_array.min()
                if img_max > img_min:
                    image_array_8bit = ((image_array - img_min).astype(np.float32) / (img_max - img_min) * 255).astype(np.uint8)
                else:
                    image_array_8bit = np.zeros_like(image_array, dtype=np.uint8)
            else:
                image_array_8bit = image_array.astype(np.uint8)
            
            # 生成伪色图RGB数组
            h, w = image_array_8bit.shape
            rgb_array = np.zeros((h, w, 3), dtype=np.uint8)
            
            if self.selected_channel == 'R':
                rgb_array[:, :, 0] = image_array_8bit
            elif self.selected_channel == 'G':
                rgb_array[:, :, 1] = image_array_8bit
            elif self.selected_channel == 'B':
                rgb_array[:, :, 2] = image_array_8bit
            
            return rgb_array
        else:
            return image_array
    
    def get_memory_estimate(self, scale_factor):
        """
        估算放大后的内存占用
        
        Args:
            scale_factor: 放大倍数
            
        Returns:
            float: 估算的内存占用（MB）
        """
        if self.original_image is None:
            return 0
        
        # 处理2D灰度图和3D RGB图
        if len(self.original_image.shape) == 2:
            h, w = self.original_image.shape
        else:
            h, w = self.original_image.shape[:2]
        new_h, new_w = h * scale_factor, w * scale_factor
        bytes_per_pixel = self.original_image.itemsize
        
        memory_mb = (new_h * new_w * bytes_per_pixel) / (1024 * 1024)
        return memory_mb
    
    def get_output_resolution(self, scale_factor):
        """
        计算输出分辨率
        
        Args:
            scale_factor: 放大倍数
            
        Returns:
            tuple: (宽度, 高度)
        """
        if self.original_size is None:
            return (0, 0)
        
        w, h = self.original_size
        return (w * scale_factor, h * scale_factor)
