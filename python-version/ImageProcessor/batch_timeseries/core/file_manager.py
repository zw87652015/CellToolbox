#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理器 - 处理文件路径、搜索和验证
File Manager - Handle file paths, search and validation
"""

import os
import glob
import re
from pathlib import Path
import logging

class FileManager:
    """文件管理器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 文件匹配模式
        self.brightfield_patterns = ['*brightfield*', '*_BF.tif', '*_bf.tif']
        self.darkfield_patterns = ['*dark*', '*_dark.tif', '*_Dark.tif']
        self.fluorescence_extensions = ['.tif', '.tiff', '.TIF', '.TIFF']
        
    def find_brightfield_files(self, directory):
        """在目录中查找明场图像文件"""
        brightfield_files = []
        
        for pattern in self.brightfield_patterns:
            matches = glob.glob(os.path.join(directory, pattern))
            brightfield_files.extend(matches)
            
        # 去重并排序
        brightfield_files = list(set(brightfield_files))
        brightfield_files.sort()
        
        self.logger.info(f"在 {directory} 中找到 {len(brightfield_files)} 个明场文件")
        return brightfield_files
        
    def find_darkfield_files(self, directory):
        """在目录中查找黑场图像文件"""
        darkfield_files = []
        
        for pattern in self.darkfield_patterns:
            matches = glob.glob(os.path.join(directory, pattern))
            darkfield_files.extend(matches)
            
        # 去重并排序
        darkfield_files = list(set(darkfield_files))
        darkfield_files.sort()
        
        self.logger.info(f"在 {directory} 中找到 {len(darkfield_files)} 个黑场文件")
        return darkfield_files
        
    def find_fluorescence_files(self, directory):
        """在目录中查找荧光图像文件"""
        fluorescence_files = []
        
        # 搜索所有TIFF文件
        for ext in self.fluorescence_extensions:
            pattern = os.path.join(directory, f"*{ext}")
            matches = glob.glob(pattern)
            fluorescence_files.extend(matches)
            
        # 去重（因为可能有.tif和.TIF等重复匹配）
        fluorescence_files = list(set(fluorescence_files))
            
        # 过滤掉明场和黑场文件
        filtered_files = []
        for file_path in fluorescence_files:
            filename = os.path.basename(file_path).lower()
            
            # 检查是否为明场文件
            is_brightfield = any(
                'brightfield' in filename or 
                filename.endswith('_bf.tif') or 
                filename.endswith('_bf.tiff')
                for _ in [None]  # 简化循环
            )
            
            # 检查是否为黑场文件
            is_darkfield = any(
                'dark' in filename
                for _ in [None]  # 简化循环
            )
            
            if not is_brightfield and not is_darkfield:
                filtered_files.append(file_path)
                
        # 按文件名排序（用于时间序列）
        filtered_files.sort()
        
        self.logger.info(f"在 {directory} 中找到 {len(filtered_files)} 个荧光文件")
        return filtered_files
        
    def validate_file_exists(self, file_path):
        """验证文件是否存在"""
        if not file_path:
            return False, "文件路径为空"
            
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"
            
        if not os.path.isfile(file_path):
            return False, f"路径不是文件: {file_path}"
            
        return True, "文件验证通过"
        
    def validate_directory_exists(self, directory_path):
        """验证目录是否存在"""
        if not directory_path:
            return False, "目录路径为空"
            
        if not os.path.exists(directory_path):
            return False, f"目录不存在: {directory_path}"
            
        if not os.path.isdir(directory_path):
            return False, f"路径不是目录: {directory_path}"
            
        return True, "目录验证通过"
        
    def create_output_directory(self, base_path):
        """创建输出目录结构"""
        try:
            # 创建results子目录
            results_dir = os.path.join(base_path, "results")
            os.makedirs(results_dir, exist_ok=True)
            
            # 创建子目录
            subdirs = ["csv", "images", "logs", "masks"]
            for subdir in subdirs:
                subdir_path = os.path.join(results_dir, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                
            self.logger.info(f"创建输出目录结构: {results_dir}")
            return results_dir
            
        except Exception as e:
            self.logger.error(f"创建输出目录失败: {str(e)}")
            raise
            
    def get_file_size_mb(self, file_path):
        """获取文件大小（MB）"""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            return size_mb
        except Exception:
            return 0
            
    def is_large_file(self, file_path, threshold_mb=500):
        """检查是否为大文件（需要内存映射）"""
        return self.get_file_size_mb(file_path) > threshold_mb
        
    def validate_tiff_file(self, file_path):
        """验证TIFF文件格式"""
        try:
            # 检查文件扩展名
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.tif', '.tiff']:
                return False, f"不是TIFF文件: {file_path}"
                
            # 简单的TIFF文件头验证
            with open(file_path, 'rb') as f:
                header = f.read(4)
                
            # TIFF文件头标识
            if header[:2] in [b'II', b'MM']:  # Little-endian 或 Big-endian
                if header[2:4] in [b'*\x00', b'\x00*']:  # TIFF标识
                    return True, "TIFF文件验证通过"
                    
            return False, f"无效的TIFF文件格式: {file_path}"
            
        except Exception as e:
            return False, f"TIFF文件验证失败: {str(e)}"
            
    def get_safe_filename(self, filename):
        """获取安全的文件名（处理中文和特殊字符）"""
        # 移除或替换不安全的字符
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 确保文件名不为空且不以点开头
        if not safe_chars or safe_chars.startswith('.'):
            safe_chars = 'unnamed_file'
            
        return safe_chars
        
    def get_relative_path(self, file_path, base_path):
        """获取相对路径"""
        try:
            return os.path.relpath(file_path, base_path)
        except ValueError:
            # 如果无法计算相对路径，返回文件名
            return os.path.basename(file_path)
            
    def scan_directory_structure(self, directory):
        """扫描目录结构，返回文件统计信息"""
        stats = {
            'total_files': 0,
            'tiff_files': 0,
            'brightfield_files': 0,
            'darkfield_files': 0,
            'fluorescence_files': 0,
            'total_size_mb': 0,
            'subdirectories': []
        }
        
        try:
            for root, dirs, files in os.walk(directory):
                stats['subdirectories'].extend([
                    os.path.join(root, d) for d in dirs
                ])
                
                for file in files:
                    file_path = os.path.join(root, file)
                    stats['total_files'] += 1
                    stats['total_size_mb'] += self.get_file_size_mb(file_path)
                    
                    # 检查文件类型
                    filename_lower = file.lower()
                    if any(ext in filename_lower for ext in ['.tif', '.tiff']):
                        stats['tiff_files'] += 1
                        
                        # 分类TIFF文件
                        if any(pattern.replace('*', '') in filename_lower 
                               for pattern in ['brightfield', '_bf.tif']):
                            stats['brightfield_files'] += 1
                        elif 'dark' in filename_lower:
                            stats['darkfield_files'] += 1
                        else:
                            stats['fluorescence_files'] += 1
                            
        except Exception as e:
            self.logger.error(f"扫描目录结构失败: {str(e)}")
            
        return stats
        
    def backup_existing_file(self, file_path):
        """备份已存在的文件"""
        if not os.path.exists(file_path):
            return file_path
            
        base, ext = os.path.splitext(file_path)
        counter = 1
        
        while True:
            backup_path = f"{base}_backup_{counter}{ext}"
            if not os.path.exists(backup_path):
                try:
                    os.rename(file_path, backup_path)
                    self.logger.info(f"备份文件: {file_path} -> {backup_path}")
                    return file_path
                except Exception as e:
                    self.logger.error(f"备份文件失败: {str(e)}")
                    counter += 1
                    if counter > 100:  # 防止无限循环
                        raise Exception("无法创建备份文件")
            else:
                counter += 1
