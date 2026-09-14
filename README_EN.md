# Modern Chinese Localization Toolkit for Google Antigravity (Antigravity-ZH)

<p align="center">
  <a href="README.md"><b>简体中文</b></a> | <a href="README_EN.md"><b>English</b></a>
</p>

<p align="center">
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/releases"><img src="https://img.shields.io/badge/Release-v1.0.0-blue.svg?style=flat-square" alt="Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20x64-brightgreen.svg?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square" alt="Python">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit/stargazers"><img src="https://img.shields.io/github/stars/lizi1997/antigravity-zh-toolkit?style=flat-square" alt="Stars"></a>
</p>

<p align="center">
  A modern, lossless, hot-injected Chinese localization enhancement toolkit designed specifically for <b>Google Antigravity</b>.<br/>
  Resolves all legacy pain points: hardcoded dictionaries, update invalidations, Shadow DOM omissions, and unlocalized native menus.
</p>

---

## ✨ Key Features

- 🚀 **In-Place ASAR Binary Patching**: Pure Python ASAR engine with in-place read/write and automatic SHA-256 recalculation. Patches running clients without killing processes or file locks.
- 🌐 **Deep Shadow DOM Penetration**: Uses modern `TreeWalker` and `MutationObserver` to recursively penetrate Web Components Shadow DOM, ensuring full translation coverage across complex modals, agent settings, and floating panels.
- 📖 **External Dictionaries & Hot-Reload**: Decoupled dictionary files in `locales/zh-CN.json` (**1,175+** entries) and `locales/patterns.json` (**82+** regex rules). Synchronized to `%APPDATA%\Antigravity\locales\` for instant user edits without rebuilding.
- 🔍 **One-Click Untranslated Text Extraction**: Press **`Ctrl + Alt + L`** anywhere in Antigravity to copy all unlocalized text on screen directly to your clipboard in JSON format.
- 🛡️ **Safe Backup & Instant Rollback**: Automatically creates `app.asar.bak` with one-click restore to official releases.
- 💻 **Zero Runtime Dependencies**: Standalone Windows `.exe` releases compiled via GitHub Actions with no Python or Node.js required for end users.

---

## 📸 Localization Coverage

| Feature Area | Coverage Highlights |
| :--- | :--- |
| **Execution & Permissions** | General settings, agent execution policy, queued message delivery (Send Immediately / Queue), keyboard shortcuts, tool permissions, file review policy. |
| **Models & Usage** | Model quota & credits, plan tiers, dynamic remaining percentage and **live refresh countdown (e.g., refreshes in 6 days, 22 hours)**. |
| **Application & Appearance**| Application settings, prevent sleep, keep in menu bar, remote control, app version, advanced settings, verbose agent chat thinking steps, conversation width. |
| **Browser & Subagents** | Browser subagent instructions, Chrome installation guidance, JS execution policies, browser actuation rules. |
| **Advanced & Developer** | Tab completion (jump, import, speed), editor selection actions, Inline Actions floating cards, custom skills and MCP server configurations. |

---

## 🚀 Quick Start

### Method 1: Download Prebuilt Release (Recommended)

1. Download **`antigravity-zh.exe`** from the [Releases Page](https://github.com/lizi1997/antigravity-zh-toolkit/releases);
2. Double-click to run. The tool automatically detects your Antigravity installation, creates a backup, and applies the patch;
3. In Antigravity, press **`Ctrl + Shift + N`** to open a new window or restart the app to enjoy the localized Chinese UI.

### Method 2: Run from Source

```bash
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh-toolkit
./install.bat
```

---

## 🛠️ Commands & Shortcuts

| Action | Command / Shortcut |
| :--- | :--- |
| **Apply Patch** | Run `install.bat` or `python scripts/patcher.py patch --force` |
| **Restore Official** | Run `restore.bat` or `python scripts/patcher.py restore` |
| **Check Status** | Run `status.bat` or `python scripts/patcher.py status` |
| **Extract Missing Strings**| Press **`Ctrl + Alt + L`** inside Antigravity |

---

## 💻 Developer Guide & Building

To modify translation dictionaries or build the standalone `.exe` locally:

```bash
# 1. Install build dependencies
pip install -r requirements.txt

# 2. Recompile engine and build single-file executable
python scripts/build.py

# 3. Output executable will be located at dist/antigravity-zh.exe
```

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for dictionary submission guidelines.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
