# 贡献指南 (Contributing Guide)

欢迎参与 **Antigravity 现代化汉化与多语言增强项目**！无论是反馈漏译、修正翻译用词，还是增加新的动态正则规则，我们都非常欢迎您的贡献。

---

## 🛠 如何快速贡献新词条

### 方式 1：利用内置快捷键提取（最推荐）

1. 在 Antigravity 客户端中进入尚未汉化的界面（如新版本增加的设置、面板等）；
2. 按下全局快捷键 **`Ctrl + Alt + L`**；
3. 界面右下角提示“未翻译词条已复制到剪贴板”；
4. 打开文本编辑器 `Ctrl + V` 粘贴，即可得到提取出的英文键值对格式；
5. 将翻译好的词条添加到 `locales/zh-CN.json`，并提交 Pull Request。

### 方式 2：手动补充词条

- **静态文本**：直接在 `locales/zh-CN.json` 中追加 `"English Text": "中文翻译"`。
- **带动态参数的文本**（如倒计时、数字变量、用户名）：
  在 `locales/patterns.json` 中追加正则模板规则：
  ```json
  {
    "pattern": "^You have used (\\d+) of (\\d+) credits$",
    "flags": "i",
    "replacement": "您已使用 $1 / $2 积分"
  }
  ```

---

## 📝 词条翻译规范

1. **术语统一**：
   - `Agent` -> **智能体**
   - `Subagent` -> **子智能体**
   - `Workspace` -> **工作区**
   - `Quota` -> **配额**
   - `Credits` -> **积分**
   - `Permissions` -> **权限**
   - `Customizations` -> **自定义配置**
   - `Trajectory` -> **轨迹 / 运行轨迹**
2. **符号与标点**：
   - 英文冒号 `: ` 对应中文冒号 `：`（如需保留右侧间隙请注意排版美观）。
   - 专有名词（如 `Google Chrome`、`Gemini`、`Claude`、`GitHub`、`MCP` 等）保持原样，不进行强行意译。
3. **测试验证**：
   - 提交 PR 前，先跑测试套件：`python -m pytest tests/ -v`（需 `pip install pytest`）。
   - 再运行 `python scripts/build.py --no-exe` 生成最新引擎，并运行 `python scripts/patcher.py patch` 检查实际界面渲染效果（已打补丁时重复执行是安全的幂等操作）。

---

## 🗂 代码结构与生成文件（务必先读）

本仓库有两个**生成文件**，由 `python scripts/build.py` 产出，**请勿手改**（改动会在下次构建时被静默覆盖）：

- `scripts/patcher.py` —— 由 `build.py` 内的 `PATCHER_TEMPLATE` + 引擎 + 词典拼装而成
- `engine/ag_localization_engine.js` —— 由 `engine/engine_template.js` + `locales/*.json` 拼装而成

| 想改什么 | 应编辑的源文件 |
| :--- | :--- |
| 静态词条 | `locales/zh-CN.json` |
| 动态正则规则 | `locales/patterns.json` |
| 汉化引擎逻辑 | `engine/engine_template.js` |
| 补丁器逻辑（ASAR 读写 / 安装还原） | `build.py` 中的 `PATCHER_TEMPLATE` |

改完源文件后运行 `python scripts/build.py --no-exe` 重新生成产物，并连同源文件一起提交。

> **已安装客户端的词典更新**：编辑 `%APPDATA%\Antigravity\locales\`（macOS 为 `~/Library/Application Support/Antigravity/locales/`）下的词典后，重新运行安装脚本即可生效，无需重新构建二进制。

---

## 🚀 Pull Request 提交流程

1. **Fork** 本仓库到您的个人 GitHub 账号；
2. 新建分支：`git checkout -b feat/add-new-translations`；
3. 提交更改：`git commit -m "feat: add translations for new settings panel"`；
4. 推送分支：`git push origin feat/add-new-translations`；
5. 在 GitHub 上创建 **Pull Request** 并简要说明本次补充或修复的界面。
