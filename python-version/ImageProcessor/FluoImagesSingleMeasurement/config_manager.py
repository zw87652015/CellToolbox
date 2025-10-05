#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
Configuration Manager Module
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 默认配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    # Bayer图像处理参数
    'is_bayer': False,
    'bayer_pattern': 'RGGB',
    'use_r_channel': True,
    
    # 白帽变换参数
    'tophat_element_size': 15,
    'tophat_element_shape': 'disk',
    
    # 高斯模糊参数
    'gaussian_sigma': 1.0,
    'enable_gaussian': True,
    
    # 自适应阈值参数
    'adaptive_method': 'gaussian',
    'adaptive_block_size': 41,
    'adaptive_c': 2,
    
    # 后处理参数
    'min_object_size': 50,
    'closing_size': 3,
    
    # 测量参数
    'measure_metrics': ['area', 'mean_intensity', 'total_intensity'],
}


def load_config(config_path: Optional[Path] = None) -> Dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，None表示使用默认路径
        
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = CONFIG_FILE
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"配置已加载: {config_path}")
            
            # 合并默认配置（确保所有必需的键都存在）
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
        else:
            logger.info("配置文件不存在，使用默认配置")
            return DEFAULT_CONFIG.copy()
            
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        logger.info("使用默认配置")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict, config_path: Optional[Path] = None):
    """
    保存配置到文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径，None表示使用默认路径
    """
    if config_path is None:
        config_path = CONFIG_FILE
    
    try:
        # 确保目录存在
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        logger.info(f"配置已保存: {config_path}")
        
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        raise


def get_default_config() -> Dict:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return DEFAULT_CONFIG.copy()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("默认配置:")
    config = get_default_config()
    print(json.dumps(config, indent=4, ensure_ascii=False))
    
    # 保存测试
    save_config(config)
    
    # 加载测试
    loaded_config = load_config()
    print("\n加载的配置:")
    print(json.dumps(loaded_config, indent=4, ensure_ascii=False))
