@echo off
REM ============================================================
REM  Paper Digest - 植物学论文日报
REM  双击此文件即可手动运行一次论文检索和分析
REM ============================================================

cd /d "%~dp0"

echo.
echo 🌱 Paper Digest - 植物学论文自动化阅读工具
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python！请先安装 Python 3.10+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import requests; import docx; import anthropic" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ 依赖包未安装，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
    echo.
)

REM Run the digest
python main.py

echo.
echo ============================================================
echo 按任意键退出...
pause >nul
