#!/bin/bash
set -e

APP_NAME="按键精灵"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  按键精灵（Python 版）- Linux 打包脚本"
echo "============================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.10+"
    exit 1
fi

echo "[1/5] 检查系统依赖..."
echo "  确保已安装：python3-tk python3-xlib scrot python3-dev"
echo "  Debian/Ubuntu: sudo apt install python3-tk python3-xlib scrot python3-dev"
echo ""

echo "[2/5] 检查 Python 依赖..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  正在安装依赖，请稍候..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

echo "[3/5] 清理旧的构建产物..."
rm -rf "$SCRIPT_DIR/build"
rm -rf "$SCRIPT_DIR/dist"

echo "[4/5] 开始打包（onefile 模式，首次可能需要 1-2 分钟）..."
python3 -m PyInstaller --clean --noconfirm "$SCRIPT_DIR/build.spec"

echo ""
echo "[5/5] 完成！"
echo ""
echo "  输出文件：$SCRIPT_DIR/dist/$APP_NAME"
echo "  大小约 40-60 MB"
echo ""
echo "  运行方式：./$APP_NAME"
echo ""
echo "  注意："
echo "  1. 全局快捷键可能需要在窗口管理器中设置"
echo "  2. Wayland 环境下截图可能受限制，建议使用 X11"
echo ""
xdg-open "$SCRIPT_DIR/dist" 2>/dev/null || true
