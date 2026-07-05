# 按键精灵 · Python 版

基于 Python + customtkinter + pyautogui 的桌面自动化工具，类似商业软件"按键精灵"。支持可视化编排指令、图片识别点击、条件判断、循环、全局快捷键、全局弹窗监控等功能，可打包为独立可执行文件。

> **跨平台支持**：Windows / macOS / Linux，在各平台均提供一致的使用体验。

## 功能特性

### 指令类型

| 类型 | 说明 |
|------|------|
| 按键 | 模拟键盘按键，支持组合键（如 `ctrl+s`），支持按住一段时间 |
| 鼠标点击 | 点击指定屏幕坐标，支持左键/右键/中键、多次点击 |
| 点击图片 | 在屏幕上查找图片并点击，支持置信度、偏移量、区域限制 |
| 等待图片 | 等待图片出现在屏幕上，支持超时 |
| 输入文本 | 输入文本（ASCII 直接输入，中文通过剪贴板粘贴） |
| 延时 | 等待指定毫秒数 |
| 重复开始 / 重复结束 | 循环执行一段指令，支持嵌套 |
| 如果图片存在 / 如果图片不存在 | 条件判断，支持嵌套 |
| 如果窗口存在 | 按窗口标题模糊匹配判断，支持嵌套 |
| 条件结束 | 结束条件块 |
| 标签 / 跳转 | 自由跳转指令，可组合实现复杂循环 |

### 核心功能

- **可视化指令编辑器**：增删改查、上下移动、复制、启用/禁用，双击编辑
- **运行控制**：开始 / 暂停 / 继续 / 停止，当前行高亮
- **全局快捷键**：默认 F6 开始、F7 停止，可自定义
- **全局监控**：独立线程监控屏幕，匹配窗口标题或图片后自动执行动作（回车、ESC、关闭窗口、点击图片、自定义按键）
- **脚本保存/加载**：JSON 格式，便于分享与版本管理
- **配置持久化**：自动保存 `config.json`，下次启动恢复
- **内置截图工具**：全屏区域截图、坐标拾取，一键生成图片模板
- **运行日志**：实时显示执行状态，分级着色（info / warn / error）

## 项目结构

```
.
├── main.py              # 入口文件，依赖检查
├── app.py               # 主界面（customtkinter）
├── commands.py          # 指令类型定义与序列化
├── command_dialog.py    # 指令编辑对话框
├── executor.py          # 执行引擎（线程、循环、条件、跳转）
├── monitor.py           # 全局监控模块
├── image_capture.py     # 屏幕截图与坐标拾取工具
├── platform_utils.py    # 平台适配层（跨平台差异封装）
├── build.spec           # PyInstaller 打包配置（支持三平台）
├── build.bat            # Windows 打包脚本
├── build_mac.sh         # macOS 打包脚本
├── build_linux.sh       # Linux 打包脚本
├── requirements.txt     # Python 依赖
├── assets/              # 资源目录（图标等）
└── .github/workflows/
    └── build.yml        # GitHub Actions 三平台自动打包
```

## 快速开始

### 环境要求

- Python 3.9+（推荐 3.11）
- 支持系统：Windows 10+ / macOS 11+ / Linux (X11)

### 平台额外依赖

**macOS**：
- 首次运行需在「系统设置 → 隐私与安全性 → 辅助功能」中授予权限
- 截图功能需在「屏幕录制」中授予权限

**Linux**：
- 需安装 `python3-tk`、`python3-xlib`、`scrot` 等系统依赖
- 建议使用 X11 会话（Wayland 下全局快捷键和截图可能受限）
  - Debian/Ubuntu: `sudo apt install python3-tk python3-xlib scrot`
  - Fedora: `sudo dnf install python3-tkinter python3-xlib scrot`

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

启动时会自动检查依赖，缺失则弹出提示。

## 打包为可执行文件

> **重要**：PyInstaller 不支持交叉编译，需在对应操作系统上打包对应平台的产物。

### Windows

```bash
# 方式一：使用打包脚本
build.bat

# 方式二：直接执行
python -m PyInstaller --clean --noconfirm build.spec
```

产物位于 `dist/按键精灵.exe`，单文件约 40-60 MB，无需安装 Python 即可运行。

> 如按键/截图无反应，请右键 → **以管理员身份运行**。

### macOS

```bash
# 方式一：使用打包脚本
chmod +x build_mac.sh
./build_mac.sh

# 方式二：直接执行
python3 -m PyInstaller --clean --noconfirm build.spec
```

产物位于 `dist/按键精灵.app`，约 50-70 MB。

> 首次运行需在「系统设置 → 隐私与安全性」中允许打开，并授予辅助功能/屏幕录制权限。

### Linux

```bash
# 方式一：使用打包脚本
chmod +x build_linux.sh
./build_linux.sh

# 方式二：直接执行
python3 -m PyInstaller --clean --noconfirm build.spec
```

产物位于 `dist/按键精灵`，约 40-60 MB。

```bash
chmod +x dist/按键精灵
./dist/按键精灵
```

### GitHub Actions 自动打包

推送 `v*` 标签（如 `v1.0.0`）会自动触发三平台 Release 构建，也可在 Actions 页面手动运行 "跨平台打包" 工作流。

## 使用说明

### 1. 添加指令

点击左侧"添加"按钮，在弹窗中选择指令类型并填写参数。

- **坐标类指令**：点击"拾取屏幕坐标"按钮，在全屏状态下点击目标位置
- **图片类指令**：点击"截图区域"按钮，拖动鼠标框选目标区域，自动保存为 PNG
- **组合键**：用 `+` 连接，如 `ctrl+s`、`ctrl+shift+s`

### 2. 运行脚本

- 点击 **▶ 开始 (F6)** 或按 `F6` 运行
- 点击 **⏸ 暂停** 暂停执行
- 点击 **■ 停止 (F7)** 或按 `F7` 停止
- 运行时左侧列表会高亮当前执行的指令

### 3. 全局监控

点击菜单"全局监控设置"，添加监控规则：

- **窗口匹配**：输入窗口标题关键词（模糊匹配），检测到窗口后执行动作
- **图片匹配**：选择或截图一张图片，检测到图片后执行动作
- **可用动作**：回车、ESC、关闭窗口、点击图片、自定义按键

勾选右下角"启用全局监控"即可开启。每条规则有 2 秒冷却，避免重复触发。

### 4. 快捷键设置

点击菜单"快捷键设置"，自定义开始/停止的全局快捷键。

## 脚本文件格式

脚本以 JSON 格式保存，结构如下：

```json
{
  "commands": [
    {
      "type": "key",
      "params": { "key": "ctrl+s", "hold": 0.0 },
      "enabled": true,
      "comment": "保存"
    },
    {
      "type": "delay",
      "params": { "ms": 500 },
      "enabled": true,
      "comment": ""
    }
  ]
}
```

## 技术说明

### 执行引擎

- 运行在独立守护线程中，不阻塞 UI
- 基于程序计数器（PC）顺序执行
- 重复/条件使用栈结构实现，支持任意深度嵌套
- `sleep` 可被停止信号中断，响应及时

### 图片识别

- 基于 `pyautogui.locateCenterOnScreen`（底层使用 OpenCV）
- 置信度范围 0~1，默认 0.8
- 建议截图模板与屏幕分辨率一致，以获得最佳识别效果

### 中文输入

- 纯 ASCII 文本使用 `pyautogui.write()`
- 含中文等非 ASCII 字符时，自动回退到 `pyperclip` 剪贴板粘贴
  - Windows / Linux：`Ctrl + V`
  - macOS：`Command + V`

## 依赖清单

| 库 | 用途 |
|----|------|
| customtkinter | 现代化 GUI 界面 |
| pyautogui | 键盘/鼠标模拟、图片识别、截图 |
| opencv-python | 图片匹配底层支持 |
| Pillow | 图像处理 |
| pynput | 跨平台全局快捷键监听 |
| pygetwindow | 窗口操作（Windows/Linux） |
| pywinctl | 窗口操作（跨平台，pygetwindow 的继任者） |
| pyperclip | 剪贴板操作（中文输入） |
| numpy | 数值计算 |
| pyinstaller | 打包为可执行文件 |

> **说明**：`keyboard` 库已替换为 `pynput` 以提供更好的跨平台支持；`pywinctl` 作为 `pygetwindow` 的补充，在 macOS 上提供窗口操作能力。

## 平台差异说明

### 全局快捷键

- **Windows**：使用 `pynput`（首选）或 `keyboard` 库，功能完整
- **macOS**：使用 `pynput`，需在「辅助功能」中授予权限
- **Linux**：使用 `pynput`，X11 下工作正常；Wayland 下可能受限

### 窗口操作

- **Windows**：`pygetwindow` + `pywinctl` 双后端支持
- **macOS**：使用 `pywinctl`，需授予「辅助功能」和「自动化」权限
- **Linux**：使用 `pywinctl`，依赖 X11 的窗口管理能力

### 截图与图片识别

- **Windows**：基于 `pyautogui` + OpenCV，功能完整
- **macOS**：需授予「屏幕录制」权限
- **Linux**：X11 下正常；Wayland 环境需使用 `scrot` 或桌面环境的截图接口

## 注意事项

1. **权限问题**：
   - Windows：部分高权限程序可能拦截模拟输入，以管理员身份运行可解决
   - macOS：需在「系统设置 → 隐私与安全性」中授予辅助功能、屏幕录制、自动化权限
   - Linux：Wayland 下全局快捷键和截图可能受限，建议切换到 X11 会话

2. **DPI 缩放**：高 DPI / Retina 屏幕下图片识别可能不准确，建议截图时使用 100% 缩放

3. **安全提示**：请勿用于恶意用途，使用时请确保能随时按 `F7` 停止

4. **数据安全**：`config.json` 保存于程序同级目录，包含所有指令与设置，请勿分享敏感信息

5. **打包限制**：PyInstaller 不支持交叉编译，必须在目标平台上构建对应平台的可执行文件

## 飞书构建通知（可选）

CI/CD 构建完成后可自动把汇总消息（构建状态、变更内容、测试验证步骤、Release 下载地址）发送到指定飞书群。通知对象通过 GitHub Secrets 配置，后续增删无需改代码。

### 第一步：获取飞书群机器人 webhook 地址

webhook 地址是一串 URL，形如 `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx`，发消息到这个 URL 等同于在群里说话。获取步骤：

#### 方式 A：飞书桌面端 / 移动端（推荐）

1. 打开飞书，进入你想接收通知的**群聊**
2. 点击群聊右上角的 **「...」**（更多）按钮 → 进入**「设置」**
3. 在设置面板中找到 **「群机器人」**（旧版叫「Bots」）→ 点击 **「添加机器人」**
4. 在机器人类型列表中选择 **「自定义机器人 - 通过 Webhook 发送消息到群」**
5. 填写机器人信息：
   - **机器人名称**：随便填，如 `KeyboardWizard 构建通知`
   - **描述**：可留空
6. **安全设置**（三选一，必须选至少一种）：
   - **自定义关键词**（推荐）：填 `KeyboardWizard`。机器人只允许发送包含此关键词的消息，本项目通知内容里都有 `KeyboardWizard`，所以选这个最简单
   - **签名校验**：更安全但配置复杂，需要在 GitHub Secret 里额外存 `LARK_SIGN_SECRET`（本项目暂未实现签名校验）
   - **IP 地址白名单**：填 GitHub Actions 的 IP 段（不稳定，不推荐，因为 GitHub 的出口 IP 经常变）
7. 点击 **「添加」**，页面会显示一段 **webhook 地址**，**立即复制保存**（关闭页面后只能重新创建机器人才能再看到）
8. 点击「完成」，群里会出现「机器人已加入」的提示

> 提示：webhook 地址关闭页面后无法再次查看，但可以在「群机器人」列表里删除重建。如果地址泄露，**立即在「群机器人」列表删除该机器人**并重建。

#### 方式 B：飞书开放平台（企业自建应用，适合多群通知）

如果你是企业管理员，想用一个机器人通知多个群或做更复杂的功能：

1. 访问 [https://open.feishu.cn/app](https://open.feishu.cn/app) → 登录
2. **创建企业自建应用** → 填写应用名称和描述
3. 应用详情页左侧 → **「机器人」** → 启用机器人能力
4. 左侧 **「权限管理」** → 开通 `im:message:send_as_bot`（以机器人身份发消息）
5. **「版本管理与发布」** → 创建版本 → 提交管理员审核（个人开发可自审自批）
6. 审核通过后，在应用详情页 **「凭证与基础信息」** 拿到 `App ID` 和 `App Secret`
7. 在目标群里 **「设置 → 群机器人 → 添加机器人」** → 选择刚创建的应用

> 方式 B 需要应用通过 OAuth 换 access_token，本项目脚本暂未实现，需要改造 `scripts/notify_lark.py`。如果只是简单的群通知，**用方式 A 即可**。

### 第二步：配置 GitHub Secrets

1. 打开仓库页面（如 `https://github.com/utemfjtn/KeyboardWizard`）
2. 顶部 Tab → **`Settings`**
3. 左侧菜单 → **`Secrets and variables`** → **`Actions`**
4. 页面顶部 **`Repository secrets`** 区域 → 点击 **`New repository secret`**
5. 逐个添加以下 Secret（每个都要点一次 `New repository secret`）：

   | Secret 名 | 必填 | 说明 | 示例值 |
   |-----------|------|------|--------|
   | `LARK_WEBHOOK_URL` | **是** | 第一步获取的飞书 webhook 地址 | `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx` |
   | `LARK_AT_MOBILES` | 否 | 构建/发布完成时 @ 的手机号，逗号分隔，**必须是群成员的手机号** | `13800138000,13900139000` |
   | `LARK_AT_ALL` | 否 | 是否 @ 全员，`true` 或 `false`，默认 `false` | `false` |

6. 添加完后，`Repository secrets` 列表里会显示这三个 Secret 的名字（**值不可再次查看**，只能更新或删除）

> 安全说明：GitHub Secrets 加密存储，Actions 日志中只会显示为 `***`，不会泄露 webhook 地址。

### 第三步：触发构建验证

1. 触发一次构建（任选一种）：
   - **打 tag**：`git tag v1.2.4 && git push origin v1.2.4`（自动构建并发布）
   - **手动触发**：仓库 → `Actions` → 选择 `跨平台打包` workflow → `Run workflow`
2. 构建完成后，飞书群会收到一条汇总消息，包含：
   - 构建状态（成功 / 失败）
   - 版本号 + commit + 触发者
   - 变更内容（git log）
   - 测试验证步骤
   - Release / Actions 下载地址
3. 如果配置了 `LARK_AT_MOBILES`，对应手机号的群成员会被 @

### 通知对象管理（无需改代码）

| 需求 | 操作 |
|------|------|
| **换群通知** | 重新在新群里创建机器人 → 用新 webhook 更新 `LARK_WEBHOOK_URL` |
| **加 @ 的人** | 编辑 `LARK_AT_MOBILES`，追加手机号（逗号分隔） |
| **@ 全员** | 设 `LARK_AT_ALL` 为 `true` |
| **关闭通知** | 删除 `LARK_WEBHOOK_URL`（脚本检测到为空会自动跳过，不报错） |
| **更换机器人** | 删旧机器人，建新机器人，更新 `LARK_WEBHOOK_URL`（webhook 泄露时这样做） |

### 常见问题

- **飞书收不到消息？** 检查：
  1. Actions 日志里 `notify` job 是否成功（看 `[notify] ✅ 飞书通知发送成功`）
  2. webhook 地址是否完整（必须以 `https://` 开头）
  3. 安全策略如果是「自定义关键词」，消息内容必须包含该关键词（本项目用 `KeyboardWizard`）
  4. `LARK_AT_MOBILES` 里的手机号必须是**群成员**的手机号，否则 @ 失败但消息仍会发送
- **Actions 里显示 `未配置 LARK_WEBHOOK_URL，跳过飞书通知`？** Secret 名拼错了，必须是全大写 `LARK_WEBHOOK_URL`
- **飞书返回 `token invalid` 或 `9499`？** webhook 地址被截断或机器人被删除，重新创建机器人

## License

MIT
