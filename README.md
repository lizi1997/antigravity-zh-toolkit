# Antigravity 现代化全功能中文汉化增强补丁 (Antigravity-ZH)

<p align="center">
  <a href="README.md"><b>简体中文</b></a> | <a href="README_EN.md"><b>English</b></a>
</p>

<p align="center">
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/releases"><img src="https://img.shields.io/badge/Release-v1.0.0-blue.svg?style=flat-square" alt="Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20(Apple%20Silicon)-brightgreen.svg?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square" alt="Python">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/stargazers"><img src="https://img.shields.io/github/stars/lizi1997/antigravity-zh-toolkit?style=flat-square" alt="Stars"></a>
</p>

<p align="center">
  专为 <b>Google Antigravity</b> 打造的现代化、无损热注入中文汉化增强项目。<br/>
  全面原生适配 <b>Windows</b> 与 <b>macOS (Apple Silicon M系列芯片)</b>。彻底解决老版插件写死词库、升级失效、Shadow DOM 漏译、智能体权限弹窗未汉化等痛点。
</p>

---

## ✨ 核心特性

- 🚀 **全平台原生支持（Windows & macOS）**：原生兼容 Windows x64 与 macOS（Apple Silicon M1/M2/M3/M4 系列），自动探测系统安装路径与运行进程，支持跨平台一键部署。
- 🛡️ **深度汉化智能体权限询问**：不仅汉化完整界面，更针对敏感操作权限询问弹窗（读取/写入路径、执行命令、沙箱外运行、MCP 工具、5 类权限保存范围及替代输入）实现了 100% 深度中文覆盖。
- ⚡ **原地 ASAR 二进制无损补丁**：采用自研原生 Python ASAR 注入引擎，支持原地读写与 SHA-256 哈希重算，**无需杀死正在运行的客户端**，无崩溃、无文件锁死。
- 🌐 **深度穿透 Shadow DOM**：基于现代 `TreeWalker` 与 `MutationObserver`，递归穿透 Web Components Shadow DOM 盲区，全面覆盖各类深层弹窗、悬浮卡片、智能体审查策略及编辑器组件。
- 📖 **词典解耦与热加载**：词库移出二进制，独立为标准 `locales/zh-CN.json`（**1,250+** 词条）与 `locales/patterns.json`（**100+** 正则规则）。
  - Windows 热加载目录：`%APPDATA%\Antigravity\locales\`
  - macOS 热加载目录：`~/Library/Application Support/Antigravity/locales/`
  - 随时使用任意文本编辑器修改词典，客户端按 `Ctrl/Cmd + R` 刷新即生效！
- 🔍 **一键捕获未翻译词条**：运行中按下快捷键 **`Ctrl + Alt + L`**（macOS: **`Option + Cmd + L`**），实时提取屏幕上遇到的所有未汉化英文词汇到剪贴板，闭环扩充词库极为简单。
- 🛡️ **安全备份与秒级还原**：自动生成官方原始备份 `app.asar.bak`，支持一键无损复原纯净官方版本。
- 💻 **零运行依赖**：提供 GitHub Actions 自动化多平台矩阵构建的单文件二进制程序，免安装 Python 或 Node.js，即开即用。

---

## 📸 界面汉化覆盖展示

| 模块 | 汉化覆盖效果 |
| :--- | :--- |
| **通用执行与权限** | 通用设置、智能体执行策略、排队消息传递（立即发送/排队）、键盘快捷键、工具权限、文件审查策略等全量中文化 |
| **智能体权限确认** | **读取/写入路径询问、运行命令确认、沙箱外执行警告、5 类规则保存范围（本次允许/对话/非项目/项目/全局）及替代操作输入** |
| **模型配额与用量** | 模型与用量、方案等级、动态配额剩余百分比及**动态刷新倒计时（如：将在 6 天 22 小时后完全刷新）** |
| **应用程序与外观** | 应用程序、防止休眠、保留在菜单栏、远程控制设备、版本号、高级设置、详细智能体对话思考步骤、对话宽度选择等 |
| **浏览器与子智能体** | 浏览器子智能体调用说明、Chrome 安装指引、JS 执行策略、浏览器操作规则等 |
| **高级与开发设置** | Tab 补全（跳转/导入/响应速度）、编辑器选中操作、浮动即时操作 (Inline Actions)、自定义技能与 MCP 工具配置等 |

---

## 🚀 快速使用

### 🪟 Windows 系统

#### 方式 1：直接下载 Release 单文件（推荐）
1. 从 [Releases 页面](https://github.com/lizi1997/antigravity-zh-toolkit/releases) 下载最新版的 **`antigravity-zh-windows.exe`**；
2. 双击运行，程序会自动识别 Antigravity 安装目录、备份官方原版并打入汉化；
3. 在 Antigravity 中按 **`Ctrl + Shift + N`**（新开窗口）或重启客户端，即可享受纯正中文界面！

#### 方式 2：从源码一键运行
```cmd
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh-toolkit
install.bat
```

---

### 🍎 macOS 系统

#### 方式 1：Apple Silicon 芯片 (M1 / M2 / M3 / M4) —— 下载预编译程序（推荐）
1. 从 [Releases 页面](https://github.com/lizi1997/antigravity-zh-toolkit/releases) 下载最新版的 **`antigravity-zh-macos-arm64`**（或解压 `antigravity-zh-macos-arm64.tar.gz`）；
2. 打开终端（Terminal），赋予执行权限并运行：
   ```bash
   chmod +x antigravity-zh-macos-arm64
   # 若遇 macOS 安全拦截提示“无法打开”，执行命令解除隔离即可：
   xattr -cr antigravity-zh-macos-arm64
   ./antigravity-zh-macos-arm64
   ```
3. 重启 Antigravity 或按 **`Cmd + Shift + N`**，汉化立即生效！

#### 方式 2：从源码一键运行（适用于所有 Mac，包括老款 Intel 芯片）
> 提示：本项目代码使用 Python 原生内置库，**零第三方依赖**，macOS 自带的 Python 3 即可直接运行：
```bash
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh-toolkit
chmod +x *.sh
./install.sh
```

---

## 🛠️ 常用操作命令

| 操作说明 | Windows 操作 | macOS / Linux 操作 | Python 原生 CLI |
| :--- | :--- | :--- | :--- |
| **一键安装汉化** | 双击 `install.bat` | `./install.sh` | `python scripts/patcher.py patch --force` |
| **一键还原官方** | 双击 `restore.bat` | `./restore.sh` | `python scripts/patcher.py restore` |
| **查看状态检查** | 双击 `status.bat` | `./status.sh` | `python scripts/patcher.py status` |
| **捕获未翻译词条** | 客户端内按 `Ctrl + Alt + L` | 客户端内按 `Option + Cmd + L` | *(前端实时捕获)* |

---

## 📦 目录结构

```text
antigravity-zh-toolkit/
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions 多平台矩阵自动化构建流程 (Windows x64 + macOS arm64)
├── .gitignore                   # Git 排除文件配置
├── LICENSE                      # MIT 开源许可证
├── README.md                    # 中文说明文档
├── README_EN.md                 # 英文说明文档
├── CONTRIBUTING.md              # 词条贡献指南
├── requirements.txt             # 开发者依赖配置
├── install.bat / install.sh     # Windows / macOS 一键安装脚本
├── restore.bat / restore.sh     # Windows / macOS 一键还原官方原版脚本
├── status.bat  / status.sh      # Windows / macOS 汉化状态检查脚本
├── build.bat   / build.sh       # 本地一键构建编译打包脚本
├── locales/
│   ├── zh-CN.json               # 核心汉化静态词典 (1,250+ 词条)
│   └── patterns.json            # 动态正则模板库 (100+ 规则)
├── engine/
│   ├── ag_localization_engine.js# 注入 Electron 渲染层的现代化汉化引擎
│   └── engine_template.js       # 引擎构建代码模板
└── scripts/
    ├── patcher.py               # 跨平台原生 ASAR 注入与管理核心
    ├── build.py                 # 跨平台自动化编译打包脚本
    └── extract_untranslated.py  # 静态文本深度提取工具
```

---

## 💻 开发者与构建

如果您想修改词条或在本地构建多平台可执行文件：

```bash
# 1. 安装构建依赖 (需要 PyInstaller)
pip install -r requirements.txt

# 2. 修改 locales/ 词典后重新编译生成二进制程序
python scripts/build.py
# 或运行 build.bat (Windows) / ./build.sh (macOS)

# 3. 生成的二进制位于 dist/ 目录：
#    - Windows: dist/antigravity-zh.exe
#    - macOS:   dist/antigravity-zh
```

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！详细贡献规范请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源发布。
