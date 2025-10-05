"""
细胞检测参数配置管理器
"""

import json
import os
import logging
from datetime import datetime

class CellDetectionConfig:
    """细胞检测参数配置管理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = "cell_detection_params.json"
        
        # 默认参数
        self.default_params = {
            "gaussian_sigma": 1.5,
            "threshold_method": "otsu",
            "min_area": 500,
            "closing_radius": 5,
            "opening_radius": 2,
            "smoothing_radius": 3,
            "created_time": datetime.now().isoformat(),
            "description": "默认细胞检测参数"
        }
        
    def save_parameters(self, params, description="用户自定义参数"):
        """
        保存细胞检测参数到配置文件
        
        Args:
            params: 参数字典
            description: 参数描述
        """
        try:
            config_data = {
                "gaussian_sigma": float(params.get("gaussian_sigma", 1.5)),
                "threshold_method": str(params.get("threshold_method", "otsu")),
                "min_area": int(params.get("min_area", 500)),
                "closing_radius": int(params.get("closing_radius", 5)),
                "opening_radius": int(params.get("opening_radius", 2)),
                "smoothing_radius": int(params.get("smoothing_radius", 3)),
                "saved_time": datetime.now().isoformat(),
                "description": description
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"细胞检测参数已保存到 {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存参数配置失败: {str(e)}")
            return False
            
    def load_parameters(self):
        """
        从配置文件加载细胞检测参数
        
        Returns:
            参数字典，如果加载失败则返回默认参数
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # 验证参数有效性
                validated_params = self._validate_parameters(config_data)
                
                self.logger.info(f"已从 {self.config_file} 加载细胞检测参数")
                return validated_params
            else:
                self.logger.info("配置文件不存在，使用默认参数")
                return self.default_params.copy()
                
        except Exception as e:
            self.logger.error(f"加载参数配置失败: {str(e)}，使用默认参数")
            return self.default_params.copy()
            
    def _validate_parameters(self, params):
        """
        验证参数有效性
        
        Args:
            params: 待验证的参数字典
            
        Returns:
            验证后的参数字典
        """
        validated = self.default_params.copy()
        
        try:
            # 验证高斯模糊参数
            sigma = float(params.get("gaussian_sigma", 1.5))
            if 0.5 <= sigma <= 3.0:
                validated["gaussian_sigma"] = sigma
                
            # 验证阈值方法
            method = str(params.get("threshold_method", "otsu"))
            if method in ["otsu", "triangle"]:
                validated["threshold_method"] = method
                
            # 验证最小面积
            min_area = int(params.get("min_area", 500))
            if min_area > 0:
                validated["min_area"] = min_area
                
            # 验证关闭半径
            closing = int(params.get("closing_radius", 5))
            if 1 <= closing <= 10:
                validated["closing_radius"] = closing
                
            # 验证打开半径
            opening = int(params.get("opening_radius", 2))
            if 1 <= opening <= 10:
                validated["opening_radius"] = opening
                
            # 验证平滑半径
            smoothing = int(params.get("smoothing_radius", 3))
            if 0 <= smoothing <= 5:
                validated["smoothing_radius"] = smoothing
                
            # 保留描述和时间信息
            validated["description"] = params.get("description", "加载的参数")
            validated["saved_time"] = params.get("saved_time", datetime.now().isoformat())
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"参数验证时发现错误: {str(e)}，使用默认值")
            
        return validated
        
    def get_config_info(self):
        """
        获取当前配置文件信息
        
        Returns:
            配置信息字符串
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                info = f"配置文件: {self.config_file}\n"
                info += f"保存时间: {config_data.get('saved_time', '未知')}\n"
                info += f"描述: {config_data.get('description', '无描述')}\n"
                info += f"参数:\n"
                info += f"  高斯σ: {config_data.get('gaussian_sigma', 'N/A')}\n"
                info += f"  阈值方法: {config_data.get('threshold_method', 'N/A')}\n"
                info += f"  最小面积: {config_data.get('min_area', 'N/A')}\n"
                info += f"  关闭半径: {config_data.get('closing_radius', 'N/A')}\n"
                info += f"  打开半径: {config_data.get('opening_radius', 'N/A')}\n"
                info += f"  边缘平滑: {config_data.get('smoothing_radius', 'N/A')}"
                
                return info
                
            except Exception as e:
                return f"读取配置文件失败: {str(e)}"
        else:
            return "配置文件不存在，将使用默认参数"
            
    def reset_to_default(self):
        """重置为默认参数并保存"""
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            self.logger.info("已重置为默认参数")
            return True
        except Exception as e:
            self.logger.error(f"重置参数失败: {str(e)}")
            return False
