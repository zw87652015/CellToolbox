"""
灰度TIFF像素放大工具 - 程序入口
使用最近邻插值算法进行像素级图像放大
"""

import sys
import logging
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.main_window import MainWindow


def setup_logging():
    """配置日志系统"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('sharp_image_converter.log', encoding='utf-8')
        ]
    )


def check_dependencies():
    """检查依赖库"""
    required_modules = [
        ('PyQt5', 'PyQt5'),
        ('numpy', 'numpy'),
        ('PIL', 'Pillow')
    ]
    
    missing = []
    
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("缺少以下依赖库:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\n请运行以下命令安装:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """主函数"""
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("灰度TIFF像素放大工具启动")
    logger.info("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("SharpImageConverter")
    app.setOrganizationName("CellToolbox")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    try:
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        
        # 显示错误对话框
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("错误")
        msg.setText("应用启动失败")
        msg.setDetailedText(str(e))
        msg.exec_()
        
        sys.exit(1)


if __name__ == '__main__':
    main()
