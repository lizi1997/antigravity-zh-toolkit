# Modern Chinese Localization Toolkit for Google Antigravity (Antigravity-ZH)

<p align="center">
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Release-v3.2-blue.svg?style=flat-square" alt="Release"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Platform-Windows%20x64-brightgreen.svg?style=flat-square" alt="Platform"></a>
  <a href="https://github.com/lizi1997/antigravity-zh-toolkit"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Docs-简体中文-lightgrey.svg?style=flat-square" alt="Chinese"></a>
</p>

A modern, lossless, hot-injected Chinese localization enhancement toolkit designed specifically for **Google Antigravity**.

---

## ✨ Key Features

- 🚀 **In-Place ASAR Binary Patching**: Pure Python ASAR engine with in-place read/write and automatic SHA-256 recalculation. Patches running clients without killing processes or file locks.
- 🌐 **Deep Shadow DOM Penetration**: Uses modern `TreeWalker` and `MutationObserver` to penetrate Web Components Shadow DOM, ensuring full translation coverage across complex modals, agent settings, and floating panels.
- 📖 **External Dictionaries & Hot-Reload**: Decoupled dictionary files in `locales/zh-CN.json` (1,175+ entries) and `locales/patterns.json` (82+ regex rules). Synchronized to `%APPDATA%\Antigravity\locales\` for instant user edits without rebuilding.
- 🔍 **One-Click Untranslated Text Extraction**: Press **`Ctrl + Alt + L`** anywhere in Antigravity to copy all unlocalized text on screen directly to your clipboard in JSON format.
- 🛡️ **Safe Backup & Instant Rollback**: Automatically creates `app.asar.bak` with one-click restore to official releases.
- 💻 **Zero Runtime Dependencies**: GitHub Actions automatically compiles standalone Windows `.exe` releases with no Python or Node.js required for end users.

---

## 🚀 Quick Start

### Method 1: Download Prebuilt Release (Recommended)

1. Download **`antigravity-zh.exe`** from [Releases](https://github.com/lizi1997/antigravity-zh-toolkit/releases).
2. Double-click to run. The tool automatically detects your Antigravity installation, creates a backup, and applies the patch.
3. In Antigravity, press **`Ctrl + Shift + N`** to open a new window or restart the app to enjoy the localized Chinese UI.

### Method 2: Run from Source

```bash
git clone https://github.com/lizi1997/antigravity-zh-toolkit.git
cd antigravity-zh
./install.bat
```

---

## 🛠️ Commands

| Action | Command / Shortcut |
| :--- | :--- |
| **Apply Patch** | Run `install.bat` or `python scripts/patcher.py patch --force` |
| **Restore Official** | Run `restore.bat` or `python scripts/patcher.py restore` |
| **Check Status** | Run `status.bat` or `python scripts/patcher.py status` |
| **Extract Missing Strings**| Press **`Ctrl + Alt + L`** inside Antigravity |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
