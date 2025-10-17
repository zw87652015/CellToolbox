@echo off
echo ========================================
echo 多图拼接工具 - Multi-Image Layout Tool
echo ========================================
echo.
echo 启动程序...
echo.

python main.py
if errorlevel 1 (
    echo.
    echo ========================================
    echo 程序异常退出，错误代码: %errorlevel%
    echo 请检查以上错误信息
    echo ========================================
    pause
) else (
    echo.
    echo 程序正常退出
)
