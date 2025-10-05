# 荧光单张图像测量工具

Fluorescence Single Image Measurement Tool - 基于白帽变换和自适应阈值的荧光图像分析工具

## 概述

本工具使用传统图像处理方法（白帽变换 + 自适应阈值）检测和测量荧光图像中的所有荧光区域。适用于背景暗淡、细胞荧光稍亮的灰度单色图像。

## 核心算法流程

1. **白帽变换 (White Top-Hat Transform)**
   - 提取比邻近背景亮的结构
   - 天然免疫背景亮度渐变
   - 使用圆形或矩形结构元素

2. **高斯模糊 (Gaussian Blur)**
   - 可选步骤，抑制读出噪声
   - 可配置sigma值

3. **自适应阈值 (Adaptive Threshold)**
   - 局部自适应阈值分割
   - 支持高斯和均值两种方法
   - 窗口大小可调

4. **形态学后处理 (Morphological Post-processing)**
   - 移除小对象（噪点过滤）
   - 闭运算填充小孔

5. **测量与量化 (Measurement)**
   - 面积（像素）
   - 平均强度
   - 总强度
   - 质心坐标

## 功能特性

✅ **16位精度保持** - 全程维持16位TIFF图像精度  
✅ **ROI支持** - 交互式选择感兴趣区域  
✅ **参数可调** - 所有处理参数均可调整  
✅ **双界面** - GUI和命令行两种使用方式  
✅ **配置管理** - 保存/加载处理参数配置  
✅ **结果可视化** - 生成叠加了检测结果的图像  
✅ **CSV导出** - 测量数据导出为CSV格式  

## 安装

### 依赖安装

```bash
pip install -r requirements.txt
```

### 依赖项

- Python 3.7+
- OpenCV (opencv-python >= 4.5.0)
- NumPy (>= 1.19.0)
- scikit-image (>= 0.18.0)
- Pillow (>= 8.0.0)

## 使用方法

### GUI模式

```bash
python gui_app.py
```

**操作流程：**

1. 点击"选择荧光图像"加载TIFF/PNG图像
2. （可选）点击"选择ROI区域"交互式选择测量区域
3. 调整处理参数：
   - 白帽变换参数（结构元素大小和形状）
   - 高斯模糊参数
   - 自适应阈值参数
   - 后处理参数
4. 点击"开始处理"
5. 在"图像预览"标签页查看结果
6. 保存结果图像和CSV文件

### 命令行模式

#### 基本用法

```bash
python cli.py -i image.tif -o output
```

#### 指定ROI区域

```bash
python cli.py -i image.tif -o output --roi 100 100 500 500
```

#### 自定义参数

```bash
python cli.py -i image.tif -o output \
  --tophat-size 20 \
  --adaptive-block 51 \
  --min-size 100
```

#### 使用配置文件

```bash
# 保存配置
python cli.py -i image.tif -o output --save-config my_params.json

# 使用配置
python cli.py -i image.tif -o output --config my_params.json
```

#### 完整参数列表

```
必需参数:
  -i, --input           输入荧光图像路径 (TIFF/PNG)
  -o, --output          输出路径（目录或CSV文件名）

ROI参数:
  --roi X Y W H         ROI区域坐标和尺寸

白帽变换参数:
  --tophat-size SIZE    结构元素大小 (默认: 15)
  --tophat-shape SHAPE  结构元素形状 (disk/rect, 默认: disk)

高斯模糊参数:
  --gaussian-sigma S    Sigma值 (默认: 1.0)
  --no-gaussian         禁用高斯模糊

自适应阈值参数:
  --adaptive-method M   方法 (gaussian/mean, 默认: gaussian)
  --adaptive-block B    窗口大小 (默认: 41)
  --adaptive-c C        常数C (默认: 2)

后处理参数:
  --min-size SIZE       最小对象面积 (默认: 50)
  --closing-size SIZE   闭运算大小 (默认: 3)

配置文件:
  --config FILE         从JSON文件加载配置
  --save-config FILE    保存当前参数到配置文件

输出控制:
  --no-image            不保存结果图像
  --no-csv              不保存CSV文件

其他:
  -v, --verbose         详细输出
  -h, --help            显示帮助信息
```

## 参数调整建议

### 结构元素大小 (tophat-size)

- **推荐值**: 细胞直径的1.5-2倍
- **细胞约100像素**: 设置为15-30
- **细胞约500像素**: 设置为75-150
- **细胞约1000像素**: 设置为150-300

### 自适应窗口大小 (adaptive-block)

- **推荐值**: 细胞直径的1.5-2倍（必须为奇数）
- **细胞约100像素**: 设置为21-41
- **细胞约500像素**: 设置为101-151
- **细胞约1000像素**: 设置为201-301

### 最小对象面积 (min-size)

- **推荐值**: 理论上最小细胞面积的一半
- **用于过滤噪点和杂质**

## 输出文件

### CSV文件

包含以下列：

- `label` - 区域标签（序号）
- `centroid_x` - 质心X坐标
- `centroid_y` - 质心Y坐标
- `area_pixels` - 面积（像素）
- `mean_intensity` - 平均强度
- `total_intensity` - 总强度（平均强度×面积）

### 结果图像

- 灰度原图作为背景
- 绿色轮廓标记检测到的区域
- 蓝色点标记质心位置
- 黄色数字标注区域序号
- 顶部显示检测统计信息

## 配置文件格式

```json
{
    "tophat_element_size": 15,
    "tophat_element_shape": "disk",
    "gaussian_sigma": 1.0,
    "enable_gaussian": true,
    "adaptive_method": "gaussian",
    "adaptive_block_size": 41,
    "adaptive_c": 2,
    "min_object_size": 50,
    "closing_size": 3,
    "roi": [100, 100, 500, 500]
}
```

## 故障排除

### 检测到太多噪点

- 增加 `--min-size` 参数
- 增加 `--closing-size` 参数
- 增加 `--adaptive-c` 参数

### 漏检荧光区域

- 减小 `--tophat-size` 参数
- 减小 `--adaptive-block` 参数
- 减小 `--adaptive-c` 参数
- 尝试切换到 `--adaptive-method mean`

### 背景不均匀导致误检

- 增加 `--tophat-size` 参数（增强背景均化）
- 确保使用 `--tophat-shape disk`（圆形对渐变更鲁棒）

### 图像太大内存不足

- 使用ROI功能限制处理区域
- 工具自动维持16位精度，大图像可能占用较多内存

## 技术细节

### 图像处理流程

```
16-bit TIFF → 归一化 → ROI掩膜 → 白帽变换 → 高斯模糊 → 自适应阈值 → 形态学处理 → 连通域分析 → 测量
```

### 坐标系统

- 所有坐标使用图像坐标系（左上角为原点）
- X轴向右，Y轴向下
- ROI格式: (x, y, width, height)

### 数据精度

- 输入: 16位TIFF或8位PNG
- 处理: 浮点型（0-1范围）
- 输出: 原始16位强度值用于测量

## 项目结构

```
FluoImagesSingleMeasurement/
├── image_processor.py      # 核心处理引擎
├── roi_selector.py         # ROI交互选择器
├── config_manager.py       # 配置管理
├── gui_app.py              # GUI应用
├── cli.py                  # 命令行接口
├── requirements.txt        # 依赖列表
├── README.md               # 本文档
├── Guideline.md            # 算法指南
└── config.json             # 配置文件（自动生成）
```

## 许可证

本工具是CellToolbox项目的一部分。

## 引用

如果本工具对您的研究有帮助，请引用相关文献。

## 联系方式

如有问题或建议，请联系开发团队。
