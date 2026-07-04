@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title KeyboardWizard - 一键打包

echo ============================================
echo   KeyboardWizard（按键精灵）- 打包为单文件 exe
echo ============================================
echo.

:: 检查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo   正在安装依赖，请稍候...
    pip install -r "%~dp0requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请手动执行：pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [2/4] 清理旧的构建产物...
if exist "%~dp0build" rmdir /s /q "%~dp0build"
if exist "%~dp0dist"  rmdir /s /q "%~dp0dist"

echo [3/4] 开始打包（onefile 模式，首次可能需要 1-2 分钟）...
python -m PyInstaller --clean --noconfirm "%~dp0build.spec"
if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请查看上方错误信息。
    pause
    exit /b 1
)

echo.
echo [4/4] 完成！
echo.
echo  输出文件：%~dp0dist\KeyboardWizard.exe
echo  大小约 40-60 MB（首次启动解压到临时目录，稍慢）
echo.
echo  直接双击 exe 即可运行，无需安装 Python
echo.
pause
start "" "%~dp0dist"
