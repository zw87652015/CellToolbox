# 快速开始指南

## 安装

```bash
cd FluoImagesSingleMeasurement
pip install -r requirements.txt
```

## 运行

### GUI模式（推荐新手）

```bash
python main.py
```

或直接运行：

```bash
python gui_app.py
```

### 命令行模式（推荐批处理）

```bash
python cli.py -i your_image.tif -o output_folder
```

### 运行测试

```bash
python test_processor.py
```

## 5分钟上手教程

### 使用GUI

1. **启动程序**
   ```bash
   python main.py
   ```

2. **加载图像**
   - 点击"选择荧光图像"
   - 选择你的TIFF或PNG图像

3. **（可选）选择ROI**
   - 点击"选择ROI区域"
   - 用鼠标拖拽绘制矩形
   - 点击"确认选择"

4. **调整参数**（可选，使用默认值通常就够用）
   - 白帽变换大小：设置为细胞直径的1.5-2倍
   - 自适应窗口：同样设置为细胞直径的1.5-2倍

5. **开始处理**
   - 点击"开始处理"按钮
   - 等待处理完成

6. **查看结果**
   - 在"图像预览"标签页查看检测结果
   - 在"处理日志"标签页查看详细日志

7. **保存结果**
   - 点击"保存结果图像"保存可视化图像
   - 点击"保存CSV"保存测量数据

### 使用命令行

```bash
# 基本用法
python cli.py -i fluorescence.tif -o results

# 带ROI
python cli.py -i fluorescence.tif -o results --roi 100 100 500 500

# 自定义参数
python cli.py -i fluorescence.tif -o results \
  --tophat-size 20 \
  --adaptive-block 51 \
  --min-size 100
```

## 常见问题

### Q: 检测到太多噪点怎么办？

**A:** 增加最小对象面积参数
```bash
python cli.py -i image.tif -o output --min-size 100
```

### Q: 漏检了一些荧光区域怎么办？

**A:** 减小结构元素大小和自适应窗口
```bash
python cli.py -i image.tif -o output --tophat-size 10 --adaptive-block 21
```

### Q: 背景不均匀导致误检怎么办？

**A:** 增加结构元素大小（增强背景均化能力）
```bash
python cli.py -i image.tif -o output --tophat-size 30
```

### Q: 如何保存我的参数配置？

**A:** 使用 `--save-config` 参数
```bash
python cli.py -i image.tif -o output --tophat-size 20 --save-config my_params.json
```

然后下次使用：
```bash
python cli.py -i image.tif -o output --config my_params.json
```

## 参数速查表

| 参数 | 默认值 | 推荐范围 | 说明 |
|------|--------|----------|------|
| tophat-size | 15 | 细胞直径×1.5-2 | 结构元素大小 |
| adaptive-block | 41 | 细胞直径×1.5-2 | 自适应窗口（奇数） |
| min-size | 50 | 最小细胞面积÷2 | 最小对象面积 |
| closing-size | 3 | 1-5 | 闭运算大小 |
| gaussian-sigma | 1.0 | 0.5-3.0 | 高斯模糊强度 |
| adaptive-c | 2 | 0-10 | 阈值常数 |

## 示例命令

```bash
# 小细胞（约100像素直径）
python cli.py -i image.tif -o output --tophat-size 15 --adaptive-block 31

# 中等细胞（约500像素直径）
python cli.py -i image.tif -o output --tophat-size 75 --adaptive-block 101

# 大细胞（约1000像素直径）
python cli.py -i image.tif -o output --tophat-size 150 --adaptive-block 201

# 高噪声图像
python cli.py -i image.tif -o output --min-size 100 --closing-size 5

# 低对比度图像
python cli.py -i image.tif -o output --adaptive-c 1 --gaussian-sigma 2.0
```

## 下一步

- 阅读完整的 [README.md](README.md) 了解详细信息
- 查看 [Guideline.md](Guideline.md) 了解算法原理
- 运行 `python test_processor.py` 验证安装
