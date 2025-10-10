@echo off
chcp 65001 >nul
echo ========================================
echo 灰度TIFF像素放大工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖库...
python -c "import PyQt5, numpy, PIL" >nul 2>&1
if errorlevel 1 (
    echo [警告] 检测到缺少依赖库
    echo 是否自动安装？ (Y/N)
    set /p install_deps=
    if /i "%install_deps%"=="Y" (
        echo 正在安装依赖...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [错误] 依赖安装失败
            pause
            exit /b 1
        )
    ) else (
        echo 请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo 启动应用...
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 应用启动失败，请查看日志文件
    pause
)
