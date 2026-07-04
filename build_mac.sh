#!/bin/bash
set -e

APP_NAME="KeyboardWizard"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  KeyboardWizard（按键精灵）- macOS 打包脚本"
echo "============================================"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.10+"
    echo "下载地址：https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] 检查依赖..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  正在安装依赖，请稍候..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

echo "[2/4] 清理旧的构建产物..."
rm -rf "$SCRIPT_DIR/build"
rm -rf "$SCRIPT_DIR/dist"

echo "[3/4] 开始打包（onefile 模式，首次可能需要 1-2 分钟）..."
python3 -m PyInstaller --clean --noconfirm "$SCRIPT_DIR/build.spec"

echo ""
echo "[4/4] 完成！"
echo ""
echo "  输出文件：$SCRIPT_DIR/dist/$APP_NAME.app"
echo ""
echo "  直接双击 app 即可运行，无需安装 Python"
echo ""
echo "  注意：首次运行可能需要在系统设置中给予"
echo "  辅助功能/屏幕录制/自动化权限"
echo ""
open "$SCRIPT_DIR/dist"
