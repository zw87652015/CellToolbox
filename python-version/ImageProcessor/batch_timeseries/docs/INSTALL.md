# 安装指南 - 批量荧光强度测量工具

## 快速安装

### 1. 检查Python版本
```bash
python --version
```
要求: Python 3.7 或更高版本

### 2. 安装依赖包
```bash
# 方法1: 使用requirements.txt (推荐)
pip install -r requirements.txt

# 方法2: 手动安装核心包
pip install numpy scipy pandas opencv-python scikit-image tifffile Pillow matplotlib
```

### 3. 验证安装
```bash
# 运行导入检查
python check_imports.py

# 运行最小测试
python test_minimal.py
```

### 4. 启动应用
```bash
# GUI版本
python batch_fluo_measurement.py

# 命令行版本
python cli.py --help
```

## 常见问题解决

### 问题1: scikit-image导入错误
```
ImportError: cannot import name 'peak_local_maxima' from 'skimage.feature'
```

**解决方案:**
```bash
# 更新scikit-image到最新版本
pip install --upgrade scikit-image

# 或者安装特定版本
pip install scikit-image>=0.19.0
```

### 问题2: OpenCV导入错误
```
ImportError: No module named 'cv2'
```

**解决方案:**
```bash
# 安装OpenCV
pip install opencv-python

# 如果仍有问题，尝试
pip uninstall opencv-python
pip install opencv-python-headless
```

### 问题3: tkinter不可用
```
ImportError: No module named 'tkinter'
```

**解决方案:**
- Windows: tkinter通常随Python安装，如果缺失请重新安装Python
- Linux: `sudo apt-get install python3-tk`
- macOS: tkinter应该已包含，如果缺失请重新安装Python

### 问题4: tifffile版本问题
```
AttributeError: module 'tifffile' has no attribute 'xxx'
```

**解决方案:**
```bash
# 更新tifffile
pip install --upgrade tifffile

# 或安装特定版本
pip install tifffile>=2021.7.2
```

### 问题5: 内存不足
```
MemoryError: Unable to allocate array
```

**解决方案:**
- 确保系统有足够内存 (推荐8GB+)
- 应用会自动使用内存映射处理大文件
- 如果仍有问题，可以降低图像分辨率

## 详细安装步骤

### Windows系统

1. **安装Python** (如果尚未安装)
   - 下载: https://www.python.org/downloads/
   - 安装时勾选 "Add Python to PATH"

2. **打开命令提示符**
   ```cmd
   # 按Win+R，输入cmd，回车
   ```

3. **导航到项目目录**
   ```cmd
   cd E:\Documents\Codes\Matlab\CellToolbox\python-version\ImageProcessor\BatchFluoMeasurement
   ```

4. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   ```

5. **验证安装**
   ```cmd
   python check_imports.py
   ```

### Linux/macOS系统

1. **确保Python3已安装**
   ```bash
   python3 --version
   pip3 --version
   ```

2. **导航到项目目录**
   ```bash
   cd /path/to/BatchFluoMeasurement
   ```

3. **创建虚拟环境** (推荐)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

4. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

5. **验证安装**
   ```bash
   python check_imports.py
   ```

## 虚拟环境使用 (推荐)

使用虚拟环境可以避免包冲突:

```bash
# 创建虚拟环境
python -m venv batch_fluo_env

# 激活虚拟环境
# Windows:
batch_fluo_env\Scripts\activate
# Linux/macOS:
source batch_fluo_env/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行应用
python batch_fluo_measurement.py

# 退出虚拟环境
deactivate
```

## 性能优化

### 可选依赖 (提升性能)
```bash
# 数值计算加速
pip install numba

# 并行处理
pip install joblib

# 更快的TIFF读取
pip install imagecodecs
```

### 系统要求
- **内存**: 8GB+ (处理大图像时)
- **存储**: 根据图像数量而定
- **CPU**: 多核处理器 (可选并行处理)

## 验证安装成功

运行以下命令确认一切正常:

```bash
# 1. 检查所有导入
python check_imports.py

# 2. 运行最小测试
python test_minimal.py

# 3. 启动GUI应用
python batch_fluo_measurement.py

# 4. 测试CLI功能
python cli.py --help
```

如果所有步骤都成功，你应该看到GUI界面或帮助信息。

## 故障排查

如果遇到问题:

1. **检查Python版本**: `python --version`
2. **更新pip**: `pip install --upgrade pip`
3. **清理缓存**: `pip cache purge`
4. **重新安装**: `pip uninstall -r requirements.txt && pip install -r requirements.txt`
5. **查看详细错误**: 运行 `python check_imports.py` 获取详细信息

## 联系支持

如果问题仍然存在，请提供以下信息:
- 操作系统和版本
- Python版本
- 完整的错误消息
- `pip list` 的输出