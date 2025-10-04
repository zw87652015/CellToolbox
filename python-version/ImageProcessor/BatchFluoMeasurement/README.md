# 批量荧光强度测量工具

## 项目简介

这是一个专门用于单细胞时间序列荧光强度批量测量的工具，支持16位TIFF图像处理，Bayer模式拆分，自动细胞检测和荧光强度定量分析。

## 主要特性

- ✅ **零手动干预**: 全自动化处理流程
- ✅ **16位精度保持**: 保持完整的线性动态范围
- ✅ **时间戳驱动**: 使用EXIF时间戳构建时间轴
- ✅ **Bayer模式支持**: RGGB固定顺序拆分
- ✅ **黑场校正**: 自动暗电流校准
- ✅ **智能细胞检测**: Otsu/Triangle阈值算法
- ✅ **ROI区域选择**: 交互式选择单细胞区域
- ✅ **批量处理**: 支持大量图像文件
- ✅ **质量控制**: 生成叠加图像用于验证
- ✅ **中文路径支持**: 完全支持中文文件名和路径

## 系统要求

### 软件环境
- Python 3.7 或更高版本
- Windows 10/11 (推荐)
- 内存: 8GB 或更多 (处理大图像时)
- 硬盘空间: 根据图像数量而定

### Python依赖包
```bash
pip install -r requirements.txt
```

主要依赖：
- `numpy` - 数值计算
- `opencv-python` - 图像处理
- `scikit-image` - 科学图像分析
- `tifffile` - TIFF文件读写
- `pandas` - 数据处理
- `matplotlib` - 图像显示
- `Pillow` - 图像格式支持

## 安装指南

### 1. 克隆或下载项目
```bash
git clone <repository-url>
cd BatchFluoMeasurement
```
### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python batch_fluo_measurement.py
```

## 使用指南

### 文件准备

#### 输入文件要求：
1. **明场图像**: 1张TIFF文件，用于细胞定位
   - 文件名包含 `brightfield` 或以 `_BF.tif` 结尾
   - 必须为16位TIFF格式
   - 图像尺寸必须为偶数（用于Bayer拆分）

2. **荧光图像序列**: N张TIFF文件，按时间顺序拍摄
   - 同一视野，细胞位置未移动
   - 包含EXIF时间戳信息
   - 16位TIFF格式

3. **黑场图像**: 1-N张TIFF文件，用于暗电流校准
   - 文件名包含 `dark` 或以 `_dark.tif` 结尾
   - 与其他图像相同的拍摄条件

#### 输出文件：
- `results/csv/fluorescence_intensity_results.csv` - 荧光强度数据
- `results/images/cell_overlay.png` - 细胞轮廓叠加图
- `results/masks/cell_mask.png` - 细胞掩膜
- `results/logs/processing_log.txt` - 处理日志

### 操作步骤

#### 1. 启动应用
```bash
python batch_fluo_measurement.py
```

#### 2. 选择输入文件
- **明场图像**: 点击"选择"按钮选择明场TIFF文件
- **荧光图像文件夹**: 选择包含荧光序列的文件夹
- **黑场图像**: 选择一个或多个黑场文件（可选）
- **输出文件夹**: 选择结果保存位置

#### 3. 调整处理参数
- **高斯模糊 σ**: 噪声滤波强度 (0.5-3.0)
- **阈值算法**: Otsu或Triangle方法
- **最小细胞面积**: 过滤小噪声对象 (100-2000像素)

#### 4. 选择ROI区域 (可选)
- 点击"选择ROI区域"按钮
- 在明场图像上拖拽鼠标绘制矩形区域
- 用于限制细胞检测范围，专注于单个细胞
- 可以重复绘制调整ROI位置和大小

#### 5. 预览检测结果
- 点击"预览细胞检测"查看细胞识别效果
- 根据预览结果调整参数或ROI区域

#### 6. 开始批量处理
- 点击"开始批量处理"执行完整流程
- 监控进度条和日志信息
- 处理完成后查看输出文件

### 命令行界面

除了GUI界面，还提供命令行版本用于批量处理：

```bash
# 基本用法
python cli.py -i ./fluorescence_folder -b ./brightfield.tif -o ./results

# 使用ROI区域 (x=100, y=100, width=200, height=200)
python cli.py -i ./fluorescence_folder -b ./brightfield.tif -o ./results --roi 100 100 200 200

# 仅预览细胞检测效果
python cli.py -b ./brightfield.tif --preview-only --roi 100 100 200 200

# 查看所有参数选项
python cli.py --help
```

### 配置文件

应用支持配置文件保存和加载：

```json
{
    "version": "1.0",
    "processing_parameters": {
        "gaussian_sigma": 1.5,
        "threshold_method": "otsu",
        "min_area": 500,
        "closing_radius": 3,
        "opening_radius": 2,
        "max_components": 1
    },
    "file_paths": {
        "brightfield_path": "",
        "fluorescence_folder": "",
        "darkfield_paths": "",
        "output_folder": ""
    },
    "roi": [100, 100, 200, 200]
}
}
```

## 输出格式说明

### CSV数据格式
```csv
DateTimeOriginal,elapsed_s,frame_i,Mean,Total,Area,filename
2024-01-01T10:00:00,0.000,0,1234.567,987654.321,800,image001.tif
2024-01-01T10:00:30,30.000,1,1245.123,996098.400,800,image002.tif
```

**列说明**：
- `DateTimeOriginal`: 图像拍摄时间 (ISO-8601格式)
- `elapsed_s`: 相对时间 (秒，以第一张图为0点)
- `frame_i`: 帧序号
- `Mean`: 细胞区域平均荧光强度
- `Total`: 细胞区域总荧光强度
- `Area`: 细胞区域面积 (像素)
- `filename`: 原始文件名

### 叠加图像
- PNG格式，300 DPI
- 明场灰度图 + 绿色细胞轮廓
- 左上角显示处理参数和统计信息

## 技术规格

### 图像处理流程
1. **16位TIFF加载**: 支持BigTIFF和内存映射
2. **Bayer拆分**: RGGB模式，提取R通道
3. **黑场校正**: 减去平均暗电流
4. **高斯滤波**: σ=0.8-2.0像素去噪
5. **自动阈值**: Otsu或Triangle算法
6. **形态学处理**: 关闭+打开操作
7. **连通域分析**: 保留最大区域
8. **荧光定量**: 逐帧强度测量

### 性能优化
- **内存映射**: 大文件(>500MB)自动使用内存映射
- **批处理**: 高效的文件I/O和内存管理
- **异常处理**: 单个文件失败不影响整体处理
- **进度跟踪**: 实时显示处理进度

## 故障排查

### 常见问题

#### 1. "Bayer 尺寸非法"错误
**原因**: 图像尺寸不是偶数
**解决**: 确保输入图像的宽度和高度都是偶数

#### 2. 内存不足错误
**原因**: 图像文件过大
**解决**: 
- 增加系统内存
- 应用会自动使用内存映射处理大文件

#### 3. 无法读取EXIF时间戳
**原因**: TIFF文件缺少时间戳信息
**解决**: 应用会自动使用文件修改时间

#### 4. 细胞检测效果不佳
**解决**:
- 调整高斯模糊参数
- 尝试不同的阈值算法
- 修改最小细胞面积阈值

#### 5. 中文路径问题
**解决**: 应用完全支持中文路径，确保使用UTF-8编码

### 日志分析
检查 `batch_fluo_measurement.log` 文件获取详细错误信息：
```
[14:30:25] INFO: 开始批量荧光强度测量
[14:30:26] ERROR: 加载TIFF图像失败: 文件不存在
```

## 验收标准

处理完成后，请验证以下项目：

✅ **CSV行数** = 荧光图张数  
✅ **第一张图** elapsed_s = 0  
✅ **叠加图轮廓** 与明场边缘重合度目视通过  
✅ **处理日志** 无严重错误  
✅ **输出文件** 完整生成  

## 技术支持

### 引用格式
如果在研究中使用本工具，请引用：
```
批量荧光强度测量工具 v1.0
基于Python的单细胞时间序列荧光定量分析软件
```

### 第三方库引用
- OpenCV: Bradski, G. (2000). The OpenCV Library. Dr. Dobb's Journal of Software Tools.
- scikit-image: van der Walt, S. et al. (2014). scikit-image: image processing in Python. PeerJ 2:e453.

### 联系方式
如遇技术问题，请查看日志文件或联系开发团队。

## 更新日志

### v1.0 (2024-01-01)
- 初始版本发布
- 完整的批量处理流程
- GUI界面和配置系统
- 16位TIFF和Bayer模式支持
- 自动细胞检测和荧光定量
- 中文路径和文件名支持

---

**注意**: 本工具专为科研用途设计，请确保输入数据的质量和一致性以获得最佳结果。
