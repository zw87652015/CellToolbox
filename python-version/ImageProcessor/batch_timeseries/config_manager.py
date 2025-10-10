#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 处理应用程序配置的保存和加载
Configuration Manager - Handle application configuration save and load
"""

import json
import os
import logging
from datetime import datetime

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # 默认配置
        self.default_config = {
            'version': '1.0',
            'created_date': datetime.now().isoformat(),
            'processing_parameters': {
                'gaussian_sigma': 1.5,
                'threshold_method': 'otsu',
                'min_area': 500,
                'closing_radius': 3,
                'opening_radius': 2,
                'max_components': 1
            },
            'file_paths': {
                'brightfield_path': '',
                'fluorescence_folder': '',
                'darkfield_paths': '',
                'output_folder': ''
            },
            'offset_settings': {
                'enable_offset_correction': True,
                'x_offset': 0,
                'y_offset': 16,
                'enable_offset_optimization': False
            },
            'advanced_settings': {
                'memory_map_threshold_mb': 500,
                'use_multiprocessing': False,
                'max_workers': 4,
                'chunk_size': 100,
                'save_intermediate_results': True,
                'backup_existing_files': True
            },
            'ui_settings': {
                'window_geometry': '800x700',
                'log_level': 'INFO',
                'auto_save_config': True,
                'show_preview_window': True
            }
        }
        
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 合并默认配置（处理新增的配置项）
                merged_config = self._merge_configs(self.default_config, config)
                
                self.logger.info(f"已加载配置文件: {self.config_file}")
                return merged_config
            else:
                self.logger.info("配置文件不存在，使用默认配置")
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return self.default_config.copy()
            
    def save_config(self, config):
        """保存配置文件"""
        try:
            # 添加保存时间戳
            config['last_saved'] = datetime.now().isoformat()
            
            # 创建备份
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as src:
                        with open(backup_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
                except Exception:
                    pass  # 备份失败不影响主要功能
                    
            # 保存新配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"配置已保存到: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
            
    def _merge_configs(self, default, user):
        """合并默认配置和用户配置"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
                
        return merged
        
    def get_processing_parameters(self, config):
        """获取处理参数"""
        return config.get('processing_parameters', self.default_config['processing_parameters'])
        
    def get_file_paths(self, config):
        """获取文件路径配置"""
        return config.get('file_paths', self.default_config['file_paths'])
        
    def get_advanced_settings(self, config):
        """获取高级设置"""
        return config.get('advanced_settings', self.default_config['advanced_settings'])
        
    def get_ui_settings(self, config):
        """获取UI设置"""
        return config.get('ui_settings', self.default_config['ui_settings'])
        
    def update_file_paths(self, config, **paths):
        """更新文件路径配置"""
        if 'file_paths' not in config:
            config['file_paths'] = {}
            
        for key, value in paths.items():
            if value is not None:
                config['file_paths'][key] = value
                
        return config
        
    def update_processing_parameters(self, config, **params):
        """更新处理参数"""
        if 'processing_parameters' not in config:
            config['processing_parameters'] = {}
            
        for key, value in params.items():
            if value is not None:
                config['processing_parameters'][key] = value
                
        return config
        
    def validate_config(self, config):
        """验证配置文件的有效性"""
        errors = []
        
        # 检查必需的顶级键
        required_keys = ['processing_parameters', 'file_paths']
        for key in required_keys:
            if key not in config:
                errors.append(f"缺少必需的配置节: {key}")
                
        # 验证处理参数
        if 'processing_parameters' in config:
            params = config['processing_parameters']
            
            # 验证数值范围
            if 'gaussian_sigma' in params:
                sigma = params['gaussian_sigma']
                if not isinstance(sigma, (int, float)) or sigma <= 0 or sigma > 10:
                    errors.append("gaussian_sigma 必须是 0-10 之间的数值")
                    
            if 'min_area' in params:
                area = params['min_area']
                if not isinstance(area, int) or area <= 0:
                    errors.append("min_area 必须是正整数")
                    
            if 'threshold_method' in params:
                method = params['threshold_method']
                if method not in ['otsu', 'triangle']:
                    errors.append("threshold_method 必须是 'otsu' 或 'triangle'")
                    
        # 验证文件路径
        if 'file_paths' in config:
            paths = config['file_paths']
            
            # 检查路径格式（如果不为空）
            for path_key, path_value in paths.items():
                if path_value and not isinstance(path_value, str):
                    errors.append(f"{path_key} 必须是字符串类型")
                    
        return len(errors) == 0, errors
        
    def export_config_template(self, template_file="config_template.json"):
        """导出配置模板文件"""
        try:
            template = self.default_config.copy()
            template['_description'] = {
                'version': '配置文件版本',
                'processing_parameters': {
                    'gaussian_sigma': '高斯模糊参数 (0.1-3.0)',
                    'threshold_method': '阈值算法 (otsu/triangle)',
                    'min_area': '最小细胞面积 (像素)',
                    'closing_radius': '形态学关闭半径',
                    'opening_radius': '形态学打开半径',
                    'max_components': '保留的最大连通域数量'
                },
                'file_paths': {
                    'brightfield_path': '明场图像文件路径',
                    'fluorescence_folder': '荧光图像文件夹路径',
                    'darkfield_paths': '黑场图像文件路径（多个用;分隔）',
                    'output_folder': '输出文件夹路径'
                },
                'advanced_settings': {
                    'memory_map_threshold_mb': '使用内存映射的文件大小阈值(MB)',
                    'use_multiprocessing': '是否使用多进程处理',
                    'max_workers': '最大工作进程数',
                    'chunk_size': '批处理块大小',
                    'save_intermediate_results': '是否保存中间结果',
                    'backup_existing_files': '是否备份已存在的文件'
                }
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"配置模板已导出到: {template_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出配置模板失败: {str(e)}")
            return False
            
    def reset_to_default(self):
        """重置为默认配置"""
        try:
            # 备份当前配置
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.old"
                os.rename(self.config_file, backup_file)
                
            # 保存默认配置
            self.save_config(self.default_config.copy())
            self.logger.info("配置已重置为默认值")
            return True
            
        except Exception as e:
            self.logger.error(f"重置配置失败: {str(e)}")
            return False
            
    def get_recent_paths(self, config, path_type='all'):
        """获取最近使用的路径"""
        recent_paths = config.get('recent_paths', {})
        
        if path_type == 'all':
            return recent_paths
        else:
            return recent_paths.get(path_type, [])
            
    def add_recent_path(self, config, path_type, path, max_recent=10):
        """添加最近使用的路径"""
        if 'recent_paths' not in config:
            config['recent_paths'] = {}
            
        if path_type not in config['recent_paths']:
            config['recent_paths'][path_type] = []
            
        recent_list = config['recent_paths'][path_type]
        
        # 移除重复项
        if path in recent_list:
            recent_list.remove(path)
            
        # 添加到开头
        recent_list.insert(0, path)
        
        # 限制列表长度
        config['recent_paths'][path_type] = recent_list[:max_recent]
        
        return config
