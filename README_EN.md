# Modern Chinese Localization Toolkit for Google Antigravity (Antigravity-ZH)

<p align="center">
  <a href="README.md"><b>简体中文</b></a> | <a href="README_EN.md"><b>English</b></a>
</p>

<p align="center">
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/releases"><img src="https://img.shields.io/badge/Release-v1.0.2-blue.svg?style=flat-square" alt="Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20(Apple%20Silicon)-brightgreen.svg?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square" alt="Python">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/stargazers"><img src="https://img.shields.io/github/stars/lizi1997/antigravity-zh-toolkit?style=flat-square" alt="Stars"></a>
</p>

<p align="center">
  A modern, lossless, hot-injected Chinese localization enhancement toolkit designed specifically for <b>Google Antigravity</b>.<br/>
  Full native support for <b>Windows</b> and <b>macOS (Apple Silicon M-Series)</b>. Resolves all legacy pain points: hardcoded dictionaries, update invalidations, Shadow DOM omissions, and unlocalized agent permission dialogs.
</p>

---

## ✨ Key Features

- 🚀 **Cross-Platform Native Support (Windows & macOS)**: Natively compatible with Windows x64 and macOS (Apple Silicon M1/M2/M3/M4). Double-click installer ready on both platforms.
- 🖱️ **Double-Click Installers for Both OSes**:
  - Windows: Double click `antigravity-zh-windows.exe`.
  - macOS: Double click `安装汉化.command` directly from the release zip folder. Zero terminal commands required!
- 🛡️ **Deep Agent Permission Localization**: 100% localization of sensitive permission request dialogs (file read/write, terminal execution, unsandboxed warnings, MCP tools, 5 rule persistence scopes, and write-in deny inputs).
- ⚡ **In-Place ASAR Binary Patching**: Pure Python ASAR engine with in-place read/write and automatic SHA-256 recalculation. Patches running clients without killing processes or file locks.
- 🌐 **Deep Shadow DOM Penetration**: Uses modern `TreeWalker` and `MutationObserver` to recursively penetrate Web Components Shadow DOM, ensuring full translation coverage across complex modals, agent settings, and floating panels.
- 📖 **External Dictionaries, No Rebuild Needed**: Decoupled dictionary files in `locales/zh-CN.json` (**1,255+** entries) and `locales/patterns.json` (**108+** regex rules).
  - Dictionary directory: `%APPDATA%\Antigravity\locales\` (Windows) / `~/Library/Application Support/Antigravity/locales/` (macOS)
  - Edit them with any text editor and re-run the installer to apply - no binary rebuild required. Clients that allow runtime file access additionally hot-reload dictionary edits automatically (checked every 2s).
- 🔍 **One-Click Untranslated Text Extraction**: Press **`Ctrl + Alt + L`** (macOS: **`Option + Cmd + L`**) anywhere in Antigravity to copy all unlocalized text on screen directly to your clipboard in JSON format.
- 🛡️ **Safe Backup & Instant Rollback**: Automatically creates `app.asar.bak` with one-click restore to official releases.

---

## 📸 Localization Coverage

| Feature Area | Coverage Highlights |
| :--- | :--- |
| **Execution & Permissions** | General settings, agent execution policy, queued message delivery (Send Immediately / Queue), keyboard shortcuts, tool permissions, file review policy. |
| **Agent Permission Dialogs**| **File read/write permission prompts, run command confirmations, unsandboxed execution warnings, 5 rule scopes, and fallback inputs.** |
| **Models & Usage** | Model quota & credits, plan tiers, dynamic remaining percentage and **live refresh countdown (e.g., refreshes in 6 days, 22 hours)**. |
| **Application & Appearance**| Application settings, prevent sleep, keep in menu bar, remote control, app version, advanced settings, verbose agent chat thinking steps, conversation width. |
| **Browser & Subagents** | Browser subagent instructions, Chrome installation guidance, JS execution policies, browser actuation rules. |
| **Advanced & Developer** | Tab completion (jump, import, speed), editor selection actions, Inline Actions floating cards, custom skills and MCP server configurations. |

---

## 🚀 Quick Start

### 🪟 Windows

#### Method 1: Prebuilt Release (Recommended)
1. Download **`antigravity-zh-windows.exe`** from the [Releases Page](https://github.com/lizi1997/antigravity-zh-toolkit/releases);
2. Double-click to run. The tool automatically detects your Antigravity installation, creates a backup, and applies the patch;
3. In Antigravity, press **`Ctrl + Shift + N`** to open a new window or restart the app to enjoy the localized Chinese UI.

#### Method 2: Run from Source
```cmd
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh-toolkit
install.bat
```

---

### 🍎 macOS

#### Method 1: Double-Click Package (Recommended for M1/M2/M3/M4)
1. Download **`antigravity-zh-macos-arm64.zip`** from the [Releases Page](https://github.com/lizi1997/antigravity-zh-toolkit/releases) and unzip it;
2. Open the unzipped folder and double-click **`安装汉化.command`**!
   > 💡 Note: If macOS displays "cannot be opened from unidentified developer", simply right-click the file and choose **Open**.
3. Restart Antigravity or press **`Cmd + Shift + N`** to see the changes.

#### Method 2: Run from Source (Works for all Macs, including legacy Intel)
```bash
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh-toolkit
chmod +x *.command *.sh
./install.sh
```

---

## 🛠️ Commands & Shortcuts

| Action | Windows | macOS (Double-Click) | Python CLI |
| :--- | :--- | :--- | :--- |
| **Apply Patch** | Double-click `install.bat` | Double-click `安装汉化.command` | `python scripts/patcher.py patch` |
| **Restore Official** | Double-click `restore.bat` | Double-click `还原官方.command` | `python scripts/patcher.py restore` |
| **Check Status** | Double-click `status.bat` | Run `./status.sh` | `python scripts/patcher.py status` |
| **Extract Missing Strings**| Press `Ctrl + Alt + L` | Press `Option + Cmd + L` | *(Real-time frontend capture)* |

---

## 📦 Directory Structure

```text
antigravity-zh-toolkit/
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions Multi-Platform Matrix CI/CD (Windows x64 + macOS arm64)
├── .gitattributes               # Cross-platform line endings
├── .gitignore                   # Git ignore file
├── LICENSE                      # MIT License
├── README.md                    # Chinese documentation
├── README_EN.md                 # English documentation
├── CONTRIBUTING.md              # Contribution guide
├── requirements.txt             # Development requirements
├── install.bat / restore.bat    # Windows batch scripts
├── 安装汉化.command             # macOS double-click installer
├── 还原官方.command             # macOS double-click uninstaller
├── install.sh / restore.sh      # Unix terminal shell scripts
├── status.bat  / status.sh      # Status check scripts
├── build.bat   / build.sh       # Local build scripts
├── locales/
│   ├── zh-CN.json               # Core dictionary (1,250+ entries)
│   └── patterns.json            # Regex templates (100+ patterns)
├── engine/
│   ├── ag_localization_engine.js# Modern localization engine injected into Electron
│   └── engine_template.js       # Engine compilation template
└── scripts/
    ├── patcher.py               # Cross-platform ASAR patcher core
    ├── build.py                 # Cross-platform packaging script
    └── extract_untranslated.py  # Static string extraction tool
```

---

## 💻 Developer Guide & Building

To modify translation dictionaries or build binaries locally:

```bash
# 1. Install build dependencies (PyInstaller)
pip install -r requirements.txt

# 2. Recompile engine and build single-file binary
python scripts/build.py
# Or run build.bat (Windows) / ./build.sh (macOS)

# 3. Output binaries are placed in dist/:
#    - Windows: dist/antigravity-zh.exe
#    - macOS:   dist/antigravity-zh
```

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for dictionary submission guidelines.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
