# Antigravity 现代化全功能中文汉化增强补丁 (Antigravity-ZH)

<p align="center">
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Release-v1.0.0-blue.svg?style=flat-square" alt="Release"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Platform-Windows%20x64-brightgreen.svg?style=flat-square" alt="Platform"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/Docs-English-lightgrey.svg?style=flat-square" alt="English"></a>
</p>

<p align="center">
  专为 <b>Google Antigravity</b> 打造的现代化、无损热注入中文汉化增强项目。<br/>
  彻底解决老版插件写死词库、升级失效、Shadow DOM 漏译及主进程原生菜单未汉化等痛点。
</p>

---

## ✨ 核心特性

- 🚀 **原地 ASAR 二进制无损补丁**：采用自研原生 Python ASAR 注入引擎，支持原地读写与 SHA-256 哈希重算，**无需杀死正在运行的客户端**，无崩溃、无文件锁死。
- 🌐 **深度穿透 Shadow DOM**：基于现代 `TreeWalker` 与 `MutationObserver`，递归穿透 Web Components Shadow DOM 盲区，全面覆盖各类深层弹窗、悬浮卡片、智能体审查策略及编辑器组件。
- 📖 **词典解耦与热加载**：词库移出二进制，独立为标准 `locales/zh-CN.json`（**1,175+** 词条）与 `locales/patterns.json`（**82+** 正则规则）。补丁安装后在 `%APPDATA%\Antigravity\locales\` 保持同步，随时用记事本修改，刷新即生效！
- 🔍 **一键捕获未翻译词条**：运行中按下快捷键 **`Ctrl + Alt + L`**，实时提取屏幕上遇到的所有未汉化英文词汇到剪贴板，闭环扩充词库极为简单。
- 🛡️ **安全备份与秒级还原**：自动生成官方原始备份 `app.asar.bak`，支持一键无损复原纯净官方版本。
- 💻 **零运行依赖**：提供 GitHub Actions 自动构建的单文件 `antigravity-zh.exe`，免安装 Python 或 Node.js，即开即用。

---

## 📸 界面汉化覆盖展示

| 模块 | 汉化覆盖效果 |
| :--- | :--- |
| **通用执行与权限** | 通用设置、智能体执行策略、排队消息传递（立即发送/排队）、键盘快捷键、工具权限、文件审查策略等全量中文化 |
| **模型配额与用量** | 模型与用量、方案等级、动态配额剩余百分比及**动态刷新倒计时（如：将在 6 天 22 小时后完全刷新）** |
| **应用程序与外观** | 应用程序、防止休眠、保留在菜单栏、远程控制设备、版本号、高级设置、详细智能体对话思考步骤、对话宽度选择等 |
| **浏览器与子智能体** | 浏览器子智能体调用说明、Chrome 安装指引、JS 执行策略、浏览器操作规则等 |
| **高级与开发设置** | Tab 补全（跳转/导入/响应速度）、编辑器选中操作、浮动即时操作 (Inline Actions)、自定义技能与 MCP 工具配置等 |

---

## 🚀 快速使用

### 方式 A：直接下载 Release 单文件（推荐）

1. 从 [Releases 页面](https://github.com/lizi1997/antigravity-zh-toolkit/releases) 下载最新版的 **`antigravity-zh.exe`**；
2. 双击运行，程序会自动识别 Antigravity 安装目录、备份官方原版并打入汉化；
3. 在 Antigravity 中按 **`Ctrl + Shift + N`**（新开窗口）或重启客户端，即可享受纯正中文界面！

### 方式 B：从源码一键运行

1. 下载或克隆本仓库：
   ```bash
   git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
   cd antigravity-zh
   ```
2. 双击运行 **`install.bat`** 即可一键完成注入。

---

## 🛠️ 常用操作

| 操作 | 说明 |
| :--- | :--- |
| **一键安装汉化** | 双击 `install.bat` 或运行 `python scripts/patcher.py patch --force` |
| **一键还原官方** | 双击 `restore.bat` 或运行 `python scripts/patcher.py restore` |
| **查看汉化状态** | 双击 `status.bat` 或运行 `python scripts/patcher.py status` |
| **提取未汉化词条** | 客户端内按 **`Ctrl + Alt + L`**，直接复制为 JSON 格式 |

---

## 📦 目录结构

```text
antigravity-zh/
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions 自动化编译构建流程
├── .gitignore                   # Git 排除文件配置
├── LICENSE                      # MIT 开源许可证
├── README.md                    # 中文说明文档
├── README_EN.md                 # 英文说明文档
├── CONTRIBUTING.md              # 词条贡献指南
├── requirements.txt             # 开发依赖配置
├── install.bat                  # 一键安装脚本
├── restore.bat                  # 一键还原脚本
├── status.bat                   # 状态检查脚本
├── build.bat                    # 本地一键构建打包脚本
├── locales/
│   ├── zh-CN.json               # 核心汉化静态词典 (1,175+ 词条)
│   └── patterns.json            # 动态正则模板库 (82+ 规则)
├── engine/
│   ├── ag_localization_engine.js# 注入 Electron 渲染层的现代化汉化引擎
│   └── engine_template.js       # 引擎构建代码模板
└── scripts/
    ├── patcher.py               # 原生 ASAR 注入与管理核心
    ├── build.py                 # 自动化编译打包脚本
    └── extract_untranslated.py  # 静态文本深度提取工具
```

---

## 💻 开发者与构建

如果您想修改词条或自主构建独立 `.exe`：

```bash
# 1. 安装构建依赖
pip install -r requirements.txt

# 2. 修改词典后重新编译生成单文件 exe
python scripts/build.py

# 3. 生成的 exe 文件位于 dist/antigravity-zh.exe
```

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！详细贡献规范请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源发布。
