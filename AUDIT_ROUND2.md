# 第二轮深入审计报告（AUDIT_ROUND2）

**项目**：`antigravity-zh-toolkit`
**基线**：v1.0.4（`5bf1bfd`）+ 第一轮修复（工作区未提交）
**日期**：2026-11-09
**配套文档**：`AUDIT_REPORT.md`（并行工作流的 51 条发现）、`FIX_STATUS.md`（第一轮修复台账）

---

## 0. 执行摘要

> **更新（本轮修复已落地）**：下面 §1~§4 的问题已按优先级修复完毕，状态见 **§0.5 修复状态**。

本轮与第一轮不同：**审计对象已包含我自己的改动**，而且工作区里还混进了**不是我写的并发改动**。因此本轮做了三件事：

| 动作 | 结果 |
|:--|:--|
| **自审**第一轮改动的 diff | 发现 1 处我自己的**设计遗漏**（边车补写会"洗白"既有篡改，见 N-12）；其余改动经真实文件复验无回归 |
| **审计并发改动** | 发现 **2 处 High/Medium-High 级缺陷**（N-01 / N-02），其中 N-01 **静默废掉了本项目的招牌功能** |
| **复核并行报告 51 条主张** | 三个代理 + 我本人逐条重算：**成立 16 条**、**部分成立 9 条**、**不成立 0 条**、**归因需修正 6 条**；**新增 22 项两份报告都没抓到的缺陷** |

**新增缺陷 22 项**：Critical 1、High 5、Medium 7、Low 7、Info 2。其中最严重的是 **N-13**：Intel Mac 用户运行官方安装包会**硬失败，且随包自带的 Python 回退路径永远不可达** —— 而 CI 矩阵里**根本不存在 macOS x64 二进制**。

此外复核代理对**第一轮报告与台账本身**也纠正了四处：`restore.bat` 的混合行尾是**工作区假象而非仓库缺陷**（HEAD blob 为纯 LF）、`FIX_STATUS.md` 的词条数口径写错（2,064 → 实际 2,097）、台账里"未编译二进制 / 真实安装未被修改"两条陈述已过时（用户已自行编译并应用修复）、以及 `build.py ↔ patcher.py` 的行号偏移已漂移为 **+26**（原 +27）—— 以上均已在本轮修正。

---

### 0.5 修复状态（本轮已落地）

按 §6 的优先级清单完成修复。**测试数 103 → 114（新增 11 项回归测试），真实 `app.asar` 端到端 21/21 通过。**

| 编号 | 级别 | 修复方式 | 落地位置 | 回归测试 |
|:--|:--|:--|:--|:--|
| **N-13** | Critical | 安装脚本按 `uname -m` 选二进制；**二进制执行失败时 `set +e` 捕获并回落到包内 `scripts/patcher.py`**（`set -e` 下 `pick_binary` 返回非 0 会中止脚本，已用 `return 0` + `set +e` 双保险） | `install.sh` / `restore.sh` / `status.sh` / `安装汉化.command` / `还原官方.command` | `test_install_script_falls_back_to_python_when_the_binary_fails`（WSL 实跑：exit 126 → 回落成功） |
| **N-01 + N-02** | High | 词典**按 key 合并**：内嵌 → 随包 → 用户，**用户永远赢**；`get_locales_dir()` 回到文档承诺的位置，随包词典改为只读输入 `get_bundled_locales_dir()`；删除"条目数更少即丢弃"与 seed 阶段的"update if older"覆盖 | `scripts/build.py`：`get_locales_dir` / `get_bundled_locales_dir` / `base_dictionary_texts` / `merge_dict_texts` / `merge_pattern_texts` / `resolve_dictionary_texts` / `seed_locale_files` | `test_user_dictionary_is_merged_not_discarded`、`test_user_translation_wins_over_the_shipped_one`、`test_bundled_dictionary_is_merged_in`、`test_seed_never_overwrites_the_user_dictionary` |
| **N-07** | High | `read_text(encoding="utf-8-sig")` 兼容 BOM；回退提示由"invalid JSON"升级为明确的"你的修改**未**生效" | `scripts/build.py`：`load_valid_json_text` / `resolve_dictionary_texts` | `test_bom_prefixed_dictionary_is_accepted` |
| **N-08** | High | `build.py main()` 用 `raise SystemExit(0 if build(...) else 1)` 传退出码；CI 的产物准备步骤加 `else: exit 1`；发布步骤断言三个产物齐全 | `scripts/build.py`、`.github/workflows/release.yml` | 端到端实测：编译失败 → 退出码 0 → 现为 1 |
| **N-14** | High | 提取器默认输出到**用户词典目录**（不再写进仓库）；`.gitignore` / `.zcodeignore` 忽略 `locales/missing_strings.json`；**构建期拒绝空译文** | `scripts/extract_untranslated.py`、`.gitignore`、`.zcodeignore`、`scripts/build.py` | `test_build_rejects_an_empty_translation` |
| **N-22** | High | `read_asar()` 校验 Pickle magic（`u1 == 4`）、头部长度自洽、**每个条目的切片边界**；越界即抛错而非静默短切片 | `scripts/build.py`：`read_asar` | `test_read_asar_rejects_a_bad_magic`、`test_read_asar_rejects_an_out_of_bounds_entry`、`test_read_asar_rejects_a_truncated_header` |
| **N-06** | Medium | 移除"检查更新"标签替换（`updateMenuState()` 每次都会把它覆盖回英文状态串） | `scripts/build.py`：`patch_menu_js` | 既有菜单测试覆盖 |
| **N-03 + F-D3-07** | Medium | 统一两处大小写冲突译文：`'Archive this conversation'` → `归档此对话`、`'Reset zoom'` → `重置缩放` | `locales/zh-CN.json` | 既有可达性测试覆盖 |
| **N-09** | Low | 正则白名单去掉 sticky `y`：`/^[imsu]+$/` | `engine/engine_template.js` | 引擎静态断言 |
| **N-10** | Low | `for..in` → `Object.keys`（`for..in` 会把原型链上的属性提升为自有键） | `engine/engine_template.js` | 引擎静态断言 |
| **N-20** | Medium | TreeWalker 的 `try/catch` 收窄到**单个节点**：一个节点抛错不再中止整棵子树 | `engine/engine_template.js` | 引擎静态断言 |
| **N-21** | Low | `restore_backup()` 改用 `compute_build_fingerprint()` 比较构建身份，不再比较总字节数（同构建的恒为误报消失） | `scripts/build.py`：`restore_backup` | `test_restore_of_a_same_build_does_not_warn` |
| **N-16** | Low | `.zcodeignore` 补上 `.zcode/`、`.zcodeignore`、`locales/missing_strings.json` | `.zcodeignore` | — |
| **N-17** | Low | CI 增加 `concurrency` 组与三个 job 的 `timeout-minutes` | `.github/workflows/release.yml` | — |
| **F-D1-16** | Medium | 二进制复制到仓库根失败时**不再静默**，也不再无条件打印"已复制" | `scripts/build.py`：`build()` | — |
| **F-D4-03** | Medium | README 词条数校验只匹配"带标签的计数"（`词条` / `entries`），无关的 `1,000 tokens` 不再误报；markdown 强调号也能匹配 | `.github/workflows/release.yml` | 本地转写 CI 步骤实测：陈旧数字仍能被抓、无关数字不误报 |

**修复后的验证结果**

| 验证 | 结果 |
|:--|:--|
| `pytest -q` | **114 passed**（本轮新增 11） |
| 真实 `app.asar` 端到端（补丁 / 幂等 / 还原 / 拒绝执行 / 跨构建备份 / 菜单效果层） | **21/21 全部通过** |
| **文档承诺的"改词典 → 重跑即生效"** | ✅ **已打通**：用户在 `%APPDATA%\Antigravity\locales\zh-CN.json` 写的词条，实测进入了 `app.asar` |
| 生成物漂移（重建后字节不变） | ✅ |
| CI 的 README 词条数校验 | ✅ 通过；陈旧数字仍能被抓，无关数字不误报 |
| shell 脚本语法（WSL `bash -n`） | ✅ 5 个脚本全部通过 |
| `node --check`（两个引擎文件） | ✅ |

**本轮仍未修的**（按约定范围之外）：N-04 / N-05 / N-11 / N-12 / N-15 / N-18 / N-19，以及并行报告里的 F-D1-03 / F-D1-17（基建项）、F-D4-02 / F-D4-04 / F-D4-05（发布矩阵与打包内容）。完整清单见 §6。

---

## 1. 【最重要】并发改动审计

### 1.1 事实经过

第一轮修复过程中（16:49–17:29），`scripts/build.py` 被**另一个编辑源**修改过，且把我的改动与它的改动**合并**在同一个工作区里。证据：

| 文件 | mtime | 谁写的 |
|:--|:--|:--|
| `locales/zh-CN.json` | 17:15:08 | 并发（在我 2,064 条之后**又加了 33 条**新译文） |
| `README.md` | 17:15:40 | 并发（同步更新词条数到 2,097） |
| `scripts/build.py` | **17:29:16** | **并发**（新增 `get_locales_dir()` 本地优先 + "条目更少即视为旧版"） |
| `scripts/patcher.py` | 17:29:25 | 并发（重新生成） |

`git diff HEAD` 显示这三处逻辑**不在 HEAD 里**、也不是我写的；`.agents/` 下 16:00 后无任何文件变动；当前也没有其他会话在写这个仓库。

并发改动做了两件事：① 把**同样的空白 key 修复**也应用了（与我一致）；② 额外**新增了约 33 条真实 UI 译文**（Interface Layout / Knowledge Work / 语音设置 / 侧边面板 / 浏览器偏好等，多半是从真实客户端里挖出来的）。**这部分是有价值的增量，保留。**

但它同时引入了两处缺陷。

---

### N-01 · **High** · `get_locales_dir()` 抢占文档承诺的词典目录 → "改词免重编"静默失效

**位置**：`scripts/build.py` `get_locales_dir()`（→ 生成至 `scripts/patcher.py`）

**问题**

```python
candidates = []
if getattr(sys, "frozen", False):
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "locales"))
candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales"))
candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "locales"))
if sys.argv and sys.argv[0]:
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "locales"))
candidates.append(os.path.join(os.getcwd(), "locales"))
for c in candidates:
    if os.path.isdir(c) and os.path.isfile(os.path.join(c, "zh-CN.json")):
        return os.path.abspath(c)
```

第三个候选 `__file__/../locales` **就是仓库自己的 `locales/`**，它永远早于 `%APPDATA%\Antigravity\locales` 命中。

**实测（用真实 CLI，不做任何 monkeypatch）**：

```
文档位置 : %APPDATA%\Antigravity\locales\zh-CN.json   （已写入 "UserKey": "用户词条"）
实际读取 : C:\...\antigravity-zh-toolkit\locales        （仓库自己的）
CLI 输出 : [*] Antigravity is already patched with the current engine and dictionaries!
结果     : app.asar 里没有 "UserKey"  ← 用户的修改被静默丢弃
```

**影响面比想象的更大**：

| 运行方式 | 命中的词典目录 | 文档位置是否生效 |
|:--|:--|:--|
| 源码检出跑 `python scripts/patcher.py` | 仓库 `locales/` | ❌ |
| 仓库根目录的 `antigravity-zh.exe`（`build.py` 会复制一份） | 仓库 `locales/` | ❌ |
| **macOS ZIP 包**（CI 打包 `macos_dist/locales/`） | `macos_dist/locales/` | ❌ `~/Library/Application Support/Antigravity/locales/` 被忽略 |
| Windows 独立 exe（Release 单文件，无 `locales/`） | `%APPDATA%\Antigravity\locales` | ✅ |

即：**README 第 32–33 行与 CONTRIBUTING 第 68 行承诺的两个目录，对"从源码运行"和"macOS ZIP 包"两种主流场景都不生效。**

**叠加的静默性**：工具输出 `already patched with the current engine and dictionaries!` 并以 **0 退出**——与第一轮修掉的 F-02 是同一类静默失败。用户改完词典重跑，界面纹丝不动，没有任何错误提示。

**建议（推荐"合并"方案）**：不要在"本地目录"和"用户目录"之间二选一，而是**合并**——内嵌词典与外部词典按 key 合并、外部优先。这样能同时满足三件事：用户的修改永远不丢、新版上游译文能补齐缺口、文档承诺的位置继续生效。同时**删掉 `os.getcwd()` 候选**（见 N-04）。

---

### N-02 · **Medium-High** · "条目数更少即视为旧版" → 静默丢弃用户的词典

**位置**：`scripts/build.py` `resolve_dictionary_texts()`

```python
ext_data = json.loads(zh_text)
emb_data = json.loads(EMBEDDED_ZH_JSON)
if len(ext_data) < len(emb_data):
    print(f"[*] External zh-CN.json ({len(ext_data)} entries) is older than embedded ({len(emb_data)} entries); using latest embedded dictionary.")
    zh_text = None
```

**实测两种真实的用户场景**（内嵌 2,097 条）：

| 场景 | 用户词典 | 结果 |
|:--|:--|:--|
| 用户**故意删掉**几条坏译文并加了自己的 | 2,093 条 | ❌ **整份被丢弃**，`MyOwnTerm` 消失 |
| 用户停留在旧版本、加了几条自己的 | 2,078 条 | ❌ **整份被丢弃**，`NewTermFromUser` 消失 |

两处都只打印一行 **`[*]`（信息级）**，连 warning 都没有。

**根因**：用"条目数"当"新旧"的代理指标，本身就不成立；而且**丢弃是全有或全无**的，正确做法是合并。

**建议**：同 N-01，改为按 key 合并（外部优先），条目数只用于提示而**不用于丢弃**。

---

### N-03 · Medium · 新增词条引入译文不一致 + 大小写索引冲突

**位置**：`locales/zh-CN.json`

```
idx  147  'Archive this conversation'   -> '存档此对话'    （HEAD 已有）
idx 2088  'Archive This Conversation'   -> '归档此对话'    （并发新增）
```

同一条 UI 文案出现**两种不同译法**（存档 / 归档，VS Code 官方用"归档"）。且引擎的小写索引后写覆盖：`lowerTranslations['archive this conversation']` 最终是 `'归档此对话'`，而精确匹配 `'Archive this conversation'` 仍给 `'存档此对话'` —— 同一句话因大小写不同而译法不同。

同类既有问题 **F-D3-07 / F-07**（`'Reset zoom'` → `'实际大小'`）**仍未修**，现在本项目共 **2 组**大小写异值冲突。

**建议**：`'Archive this conversation'` 统一为 `'归档此对话'`；并在 CI 加一条断言：**同一逻辑词条的大小写变体必须译法相同**（本轮已有现成脚本，见 §4.3）。

---

### N-04 · Low · 词典目录依赖当前工作目录

`get_locales_dir()` 的最后一个候选是 `os.getcwd()/locales`。对 PyInstaller 单文件 exe 而言，用户在**任何含有 `locales/` 的目录下**运行都会命中它——行为随 cwd 变化，不确定。

**建议**：删掉 cwd 候选。

---

### N-05 · Low · 文档与行为矛盾

`README.md:32-33` 与 `CONTRIBUTING.md:68` 仍写着 `%APPDATA%\Antigravity\locales\` / `~/Library/Application Support/Antigravity/locales\`，与 N-01 之后的实际行为不符。

---

## 2. 本轮新增发现（两份报告都没有）

### N-06 · Medium · "检查更新"菜单项的中文标签根本留不住

**位置**：`scripts/build.py` `patch_menu_js()` 的第三条替换
（`("label: updater_1.MenuUpdateStep.CheckForUpdates", "label: '检查更新 (Check for Updates)'", -1)`）
→ 影响真实客户端 `dist/menu.js` 与 `dist/updater.js`

**根因**（真实客户端源码）：

```js
// dist/updater.js
MenuUpdateStep["CheckForUpdates"] = "Check for Updates";
exports.updateActions = { [MenuUpdateStep.CheckForUpdates]: () => checkForUpdates(true), ... };

function updateMenuState(step) {
    const item = menu.getMenuItemById('check-for-updates');
    if (item) {
        item.label = step;                                  // ← 每次更新器事件都覆盖 label
        item.enabled = exports.updateActions[step] !== undefined;
    }
}
```

`updateMenuState` 在 **6 个更新器事件**上被调用（checking-for-update / update-available / update-not-available / download-progress / update-downloaded / error），每次都把 `item.label` 写回**原始英文状态串**。

**后果**：
1. 补丁写入的中文标签 `'检查更新 (Check for Updates)'` 在**第一次更新器事件后即被抹掉** → 该菜单项实际显示英文 → **这条汉化完全无效**。
2. 在"插入 → 首次状态更新"之间的窗口里，点击处理 `updateActions[menuItem.label]` 查到 `undefined` → 点击无响应（此后 label 被改回状态串，又自行恢复）。
3. 这与 F-01 是**同一类错误**（改了查找键而非显示文本），只是发生在 `updateMenuState` 这条路径上——**我的第一轮审计与并行报告都只查了 `addItemToSubmenu` 一处**。

**建议**：**移除这条替换**（英文标签由更新器自己维护，中文标签本来也保不住）；或改为包装 `updateMenuState`，让它写入中文标签的同时保留原始状态串作为查找键。

---

### N-07 · **High** · 用户词典带 UTF-8 BOM → 整份被静默丢弃

**位置**：`scripts/build.py` `load_valid_json_text()`（→ `patcher.py`）

**实测**：

```
文件首字节 : b'\xef\xbb\xbf{"U'      ← 带 BOM
load_valid_json_text() -> None
json.loads(text)  ->  JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig)
```

后果与 N-01/N-02 叠加：`resolve_dictionary_texts()` 回落到内嵌词典，用户在 `%APPDATA%` 里的**全部修改消失**，只留一行 `[!] External zh-CN.json is invalid JSON`。Windows 记事本、部分编辑器默认写 BOM，用户极易踩到。

**建议**：`read_text(encoding="utf-8-sig")`（能同时处理带/不带 BOM），并把回退提示升级为明确的 **warning**："已忽略你的词典（编码问题），本次使用内嵌词典"。

---

### N-08 · **High** · `build.py` 丢弃 `build()` 的返回值 → 编译失败仍退出 0 → CI 可能发布**缺一个平台**的 Release

**位置**：`scripts/build.py` 末尾

```python
if __name__ == "__main__":
    ...
    build(compile_exe=not args.no_exe)      # ← 返回值被丢弃
```

**实测**（mock PyInstaller 失败）：

```
[!] Compilation failed: Command '['pyinstaller']' returned non-zero exit status 1.
build() returned: False
REACHED_END_OF_SCRIPT
exit code    : 0        ← 失败对 CI 完全不可见
```

**完整链路**（逐步核实）：

| 步骤 | 行为 |
|:--|:--|
| `python scripts/build.py` | PyInstaller 失败 → `build()` 返回 False → `main()` 丢弃 → **退出 0** → CI 步骤通过 |
| `Prepare binary artifact` | `if [ -f ... ]; then ... fi` 无 `else` → **静默通过** |
| `Upload Build Artifact` | `upload-artifact` v4 的 `if-no-files-found` **默认 `warn`**（已查 action.yml）→ **带警告通过，不产生 artifact** |
| `release` job | `needs: build` 成功 → **照常运行** |
| `download-artifact` | 0 个 artifact → **失败** → Release **不会**被创建 |

**归因修正**：并行报告 F-D4-01 说的"**发布空 Release**"**不可达**（`download-artifact` 会先失败）。

**但真正可达的危害是**：**矩阵部分失败**时（例如 Windows 构建成功、macOS 的 PyInstaller 失败），Windows 的 artifact 正常上传 → `download-artifact` 成功 → **Release 被发布，但缺少 macOS 二进制**，而 README 第 74 行正在引导用户下载 `antigravity-zh-macos-arm64.zip`。**macOS 用户会拿到一个坏掉的下載链接，而 CI 全程绿灯。**

**建议**：
1. `build.py` 的 `main()` 必须 `raise SystemExit(0 if build(...) else 1)`。
2. `Prepare binary artifact` 缺 `else: exit 1`。
3. `release` 步骤在 `release_assets/` 为空时 `exit 1`；并断言矩阵产物齐全（Windows exe + macOS 二进制 + zip）。

---

### N-09 · Low · 正则白名单允许 sticky `y` 标志 → 这类规则永远不生效

**位置**：`engine/engine_template.js` 的 flags 白名单 `/^[imsuy]+$/`

**实测**：

```
sticky  "xabc".replace(/abc/y, 'Z') = "xabc"     ← 没替换
normal  "xabc".replace(/abc/i, 'Z') = "xZ"
```

引擎先 `p.regex.test(trimmed)` 再 `trimmed.replace(p.regex, p.replace)`：sticky 正则的 `test()` 会把 `lastIndex` 推到匹配末尾，随后的 `replace()` 从该位置继续 → 匹配不上 → **译文等于原文，静默无效果**。

只影响用户自己写了 `flags: "y"` 的规则，但白名单既然允许就该让它能用。

**建议**：白名单去掉 `y`（sticky 对"整串翻译"语义本就无意义），或在 `test()` 后把 `p.regex.lastIndex = 0`。

---

### N-10 · Low · 原型链"污染"主张需收窄：不是全局污染，但会污染小写索引

**位置**：`engine/engine_template.js` `applyExternalDicts()` / `rebuildIndexes()`

**实测**：

```
merged.__proto__.polluted = yes
({}).polluted              = undefined     ← 全局 Object.prototype 未被污染
```

因为 `JSON.parse('{"__proto__":{...}}')` 产生的是**自有属性**，`merged['__proto__'] = {...}` 只替换了 `merged` 自己的原型。

**但仍有一处真实影响**：`rebuildIndexes()` 用的是 `for (const key in translations)` —— **`for..in` 会遍历原型链上的可枚举属性**：

```js
for (const key in translations) {
    lowerTranslations[key.toLowerCase()] = translations[key];
}
```

于是被污染的原型属性会变成 `lowerTranslations` 的**自有键**，而 `translateText` 的小写分支用 `hasOwnProperty.call(lowerTranslations, lower)` → **命中** → 一个本不该被翻译的 UI 文本会被替换成攻击者指定的值。

**收窄后的结论**：不是"原型链污染"（全局），而是"**继承属性被提升为自有键**，可遮蔽任意 UI 文案"。触发条件是用户自己的词典里带 `__proto__` 键（自伤），影响面为单个字符串。

**建议**：`for (const k in translations)` 改为 `Object.keys(translations)`，或给 `merged` 用 `Object.create(null)`。

---

### N-11 · Informational · ReDoS：现有 153 条规则实测零暴露

对 `locales/patterns.json` 全量扫描：嵌套量词 **0 条**、全部可编译、flags 全为 `'i'`。**当前数据无 ReDoS 暴露**。但引擎对**用户自写**规则没有回溯上限——这属于"能力边界缺失"，不是现存缺陷（并行报告 F-D2-03 的表述需要按此收窄）。

### N-12 · Low · 我自己第一轮改动的设计遗漏：边车补写会"洗白"既有篡改

**自审发现**。`ensure_backup_sidecar()` 用**当前**备份的哈希补写边车。若该备份在补写前**已被篡改**，补写等于把篡改状态登记为"基线"，此后检测不出。

- 无法完全避免（没有独立基线可比），但**影响是"只影响未来"**：补写之后，对该备份的**后续**篡改会被检出 ✅
- 严格说，第一轮 FIX_STATUS 里"篡改检测永久失效"的表述应修正为：**"检测能力从补写时刻起生效"**。
- 可选改进：补写时同时记录当前 `app.asar` 的构建指纹（`compute_build_fingerprint`），使"备份属于哪个构建"也可追溯。

---

### N-13 · **Critical**（复核代理 C 新增）· 错误架构二进制让安装脚本硬失败，且随包 Python 回退**永远不可达**

**位置**：`install.sh:11-19`、`restore.sh:11-19`、`status.sh:6-14`、`安装汉化.command:19-22`、`还原官方.command:11-14`

**问题**：脚本用 `if [ -f "$DIR/antigravity-zh-macos-arm64" ]` **无条件**执行 arm64 二进制，**没有 `uname -m` 判断**：

```bash
if [ -f "$DIR/antigravity-zh-macos-arm64" ]; then
    chmod +x "$DIR/antigravity-zh-macos-arm64"
    "$DIR/antigravity-zh-macos-arm64" patch
    exit 0
fi
# ↓↓↓ 这段 Python 回退在二进制失败时永远到不了
if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/scripts/patcher.py" patch
```

`set -e` 语义下，二进制以非 0 退出（Intel Mac 上 `Bad CPU type`，退出码 **126**）会**立即中止整个脚本**。

**复现**（用返回 126 的假二进制忠实转写 `install.sh`）：

```
zsh: bad CPU type in executable: ./antigravity-zh-macos-arm64
>>> install.sh EXIT CODE = 126
>>> Did the python fallback run?  ->  否
```

**影响**：
- **Intel Mac 用户**下载官方 `antigravity-zh-macos-arm64.zip` 后运行 → 立即硬失败，**连同包里自带的 `scripts/patcher.py` 也用不上**，完全无自救路径。
- Linux 用户误解压 macOS 包同样中招。
- 与并行报告 F-D1-13 的区别：F-D1-13 只说"硬编码 arm64"，**没意识到"失败后应回落到包内 Python 路径"**——这是本条的关键增量。

**建议**：二进制执行失败时 `||` 继续走到 Python 分支；并按 `uname -m` 选择 arm64/x64 产物。

---

### N-14 · **High**（复核代理 C 新增）· 提取脚本产出**空译文**写进 `locales/`，会渲染出空白 UI

**位置**：`scripts/extract_untranslated.py:96`（`missing[s] = ""`）、`:100`（默认写入 `locales/missing_strings.json`）、`.github/workflows/release.yml:131`（`cp locales/*.json macos_dist/locales/`）、`engine/engine_template.js` 的精确查表替换

**问题**：提取脚本默认把结果写进**仓库内** `locales/`，且**所有 value 都是空字符串**。该文件**未被任何忽略规则覆盖**（`git check-ignore locales/missing_strings.json` → 无输出），一旦被提交，CI 的通配 `cp locales/*.json` 会把它打进发布的 macOS 包。

更尖锐的是：**若这些条目被并入 `zh-CN.json`，空译文会让引擎把 UI 标签替换成空串**。Node 实测引擎语义：

```
translateText('Save') -> ""      # 译文为空 → 标签被清空
EMPTY STRING RESULT: true
```

而 `scripts/build.py` 只校验"key 带空白"与"哨兵标记"，**不校验 value 为空**；CI 同样无此校验。

**影响**：一条"用户改了词典 → 界面变空白"的静默失效路径，与已修的 F-01-02 同类，但入口在**数据文件**而非退出码。

**建议**：`extract_untranslated.py` 默认输出到仓库外目录；`.gitignore` 加入 `locales/missing_strings.json`；构建期**拒绝空译文**。

---

### N-15 · Medium（复核代理 C 新增）· 7 个安装脚本**从不校验 Python 版本**

**位置**：`install.bat:19-29`、`status.bat:14-24`、`install.sh:21-29`、`status.sh:16-22`、`restore.sh:21-27`、`安装汉化.command:23-26`、`还原官方.command:15-18`

**问题**：`install.bat` 提示"请安装 Python 3.10+"，但**没有任何脚本检查版本**（7 个脚本正则扫描命中数均为 0）。此外：
- `where python` 取 PATH 首个命中且不带版本过滤 → Windows 10/11 上常命中微软商店应用执行别名占位符 `…\WindowsApps\python.exe`（执行会拉起商店）；
- `install.sh` 的 `command -v python` 回退可能命中 **Python 2**，而 `patcher.py` 用 f-string（需 ≥3.6）必然 SyntaxError。

**建议**：脚本里加一行版本判定；`install.sh` 的回退改为 `python3` 优先并做 `sys.version_info` 检查。

---

### N-16 · Medium（复核代理 C 新增）· `.zcodeignore` 与 `.gitignore` 漂移：漏了 `.zcode/` 与 `.zcodeignore`

**位置**：`.gitignore:52-55`（含 `.mimosa/`、`.zcode/`、`.zcodeignore`）vs `.zcodeignore:53-54`（仅 `.mimosa/`）

**复现**：逐行 diff → `In .gitignore but NOT in .zcodeignore: .zcode/ , .zcodeignore`（反向 25 条为 ZCode 默认排除规则，属正常）。

**影响**：本地工具元数据目录 `.zcode/` 会被索引工具纳入扫描。无功能后果，属规范漂移。

---

### N-17 · Low（复核代理 C 新增）· CI 无 `timeout-minutes`、无 `concurrency`

**位置**：`.github/workflows/release.yml`（全文，两个关键字命中数均为 0）

**影响**：PyInstaller 挂起会吃满 runner 默认 360 分钟上限；并发 tag 推送会在同一 release 资产上竞争（`release.yml:164-185` 无互斥）。

---

### N-18 · Low（复核代理 C 新增）· `requirements.txt` 混合测试与构建依赖，且无哈希锁定

**位置**：`requirements.txt:1-2`

**问题**：`test` job 安装整个 `requirements.txt`，但它只跑 `build.py --no-exe`，**从不编译可执行文件** → PyInstaller（带原生二进制的分发包）是每次 PR 的无用负担。两者均未用 `--require-hashes`。

**纠正（正面）**：`cache: 'pip'` 本身可靠 —— setup-python 以 `requirements.txt` 哈希参与 cache key。

---

### N-19 · Info（复核代理 C 新增）· 词典与规则库数据质量扫描：整体干净

脚本化全量扫描结果（非人工抽查）：

| 项 | `zh-CN.json` | `patterns.json` |
|:--|:--|:--|
| 规模 | 2,097 唯一键（**重复键 0**） | 153 条（**重复 pattern 0**） |
| 带首尾空格 key | **0** ✅ | — |
| 非字符串 value / 控制字符 / **空 value** | 0 / 0 / **0** ✅ | 0 / 0 |
| 非法正则 / `$N` 引用不存在分组 | — | **0 / 0** ✅ |
| flags 越界（白名单 `/^[imsuy]+$/`） | — | **0**（全为 `'i'`）✅ |
| 大小写折叠冲突 | 88 组**同值**（良性冗余）+ **2 组异值** | — |

两处异值冲突：`reset zoom`（**有害**，见 N-03 / F-D3-07）与 `archive this conversation`（语义等价，无害）。

---

### N-20 · Medium（复核代理 A 新增）· TreeWalker 的 `try/catch` 会中止整个子树的剩余扫描

**位置**：`engine/engine_template.js` 的 `translateDOM()` 内 TreeWalker 循环

**问题**：TreeWalker 循环体被**一个** `try { ... } catch (e) {}` 包住。**单个节点**抛出异常（自定义元素 getter、Proxy 陷阱、超长字符串等）→ 异常冒到循环外 → **该子树剩余节点全部不再扫描**，且异常被静默吞掉。

**影响**：这是 F-D1-05（编辑器 token 穿透）与 F-D1-07（2 秒全量扫描）的**放大器** —— 一次异常会让一整段 UI 永久停留在英文，且没有任何日志。

**建议**：把 `try/catch` 收窄到**单个节点**的处理函数内（`catch` 后 `continue`），而不是包住整个循环。

---

### N-21 · Low（复核代理 A 新增）· `restore_backup()` 没有复用已存在的构建指纹

**位置**：`scripts/build.py` `restore_backup()` vs `compute_build_fingerprint()`

**问题**：本轮已实现 `compute_build_fingerprint()`（比对备份与当前归档的构建身份，排除 4 个补丁目标），并已在 `apply_patch()` 中使用。但 `restore_backup()` **仍然只比较总字节数**：

```python
cur_size, bak_size = os.path.getsize(asar_path), os.path.getsize(bak_path)
if cur_size != bak_size:
    print("[!] Size mismatch: ... The backup may come from a different (older) client version; restoring rolls the app back to it.")
```

**实测**：真实 `app.asar` 5,426,793 B vs 备份 5,242,783 B，差 **184,010 B（≈179.7 KB）全部来自注入的引擎**，而还原结果与官方备份 **SHA 完全一致** → **100% 误报**。

**建议**：`restore_backup()` 改用 `compute_build_fingerprint()` 比较，把"版本回退告警"变成真正有意义的判断。

---

### N-22 · **High**（复核代理 A 新增）· ASAR 读取缺 Magic 校验与边界检查，**损坏会被固化**

**位置**：`scripts/build.py` `read_asar()`

**问题**（两组实测）：

| 实验 | 结果 |
|:--|:--|
| 头部 magic 改为 `0xDEADBEEF` | `read_asar` **仍然成功**，提取出 765 个文件，`dist/preload.js` 完整 24,173 字节 —— **没有任何校验** |
| 载荷区截断为一半 | `read_asar` **无异常返回**，**317 个成员静默变成 0 长度**（例：`dist/__mocks__/electron-log/main.js`） |
| 再把截断后的归档重新打包 | 仍是 **317 个空成员** —— 损坏被**固化**进一个"结构合法"的 2,599,583 字节 asar |

根因：`u1` 读出后**从不校验 `== 4`**（Chromium Pickle 规范要求），且 `data[start:start + size]` 越界时 Python 切片**静默返回短字节**。

**影响**：一旦对损坏/被截断的 app.asar 执行补丁，补丁器会把**静默截断的文件**原样写回，用户得到一个"看起来正常"但内容残缺的客户端，且此后每次补丁都基于这份损坏归档。

**建议**：
1. 校验 `u1 == 4` 与 `json_len`/`u2` 的自洽性；
2. 校验 `start + size <= len(data)`，越界即抛错；
3. 写回前对**每个**条目做长度断言。

---

## 3. 对并行报告 51 条主张的复核结果

我与两名复核代理分工重算（代理结果见 §4）。结论汇总：

### 3.1 确认成立（可直接采信）

| 编号 | 摘要 | 复核方式 |
|:--|:--|:--|
| **F-D2-02** | `escapeDollar` 是 JS no-op 导致文本损坏 | **已确证并修复**：字符串替换 `'$$'` 会被 JS 折叠回 `$`；改用函数替换器 `() => '$$'` 后 `"Price is $10 and $&"` 正确渲染 |
| **F-D3-05** | UTF-8 BOM 使用户词典被静默丢弃 | **本轮确证**（N-07）：`json.loads` 抛 `Unexpected UTF-8 BOM` |
| **F-D2-04** | 正则白名单含 sticky `y` 导致匹配遗漏 | **本轮确证**（N-09）：`"xabc".replace(/abc/y,'Z')` 不替换 |
| **F-D3-04** | 原生对话框状态文本与 macOS Dock 菜单覆盖不全 | 复核代理确证 Dock 菜单在 `dist/main.js` 中未被汉化 |
| **F-D1-11** | 还原时因 ASAR 尺寸膨胀产生恒为误报警告 | 第一轮已确证（本机 4,975,650 vs 4,797,365，同构建） |
| **F-D4-03** | README 词条数校验正则 `\b\d+,\d{3}\b` 过度僵硬 | 代理 C 确证：README 里任意带千分位的 4 位数字都会被强制断言等于词条总数。实测注入 `1,000 tokens` → CI 校验 FAIL |
| **F-D4-04** | CI 缺少编译后二进制的自动化冒烟测试 | 代理 C 确证：`build` job 6 步**无一步执行产物**；`grep 'smoke\|--help\|if-no-files-found'` 命中 0。而 `build.py` 未指定任何 `--hidden-import` |
| **F-D4-05** | Windows 发布产物缺少词典及批处理脚本 | 代理 C 确证：`release.yml:122` 的 `if [ "${{ matrix.os }}" = "macos-latest" ]` 把 `locales/`、`scripts/`、zip/tar 整段锁在 macOS 分支内；Windows 腿只 `cp` 一个 exe |
| **F-D1-03** | 单体模板阻碍静态类型检查 | 代理 C 确证：模板占 `build.py:27–786` 共 **760 行** Python 源码被包在字符串字面量内；三个 py 文件的返回类型注解均为 **0** 处 |
| **F-D1-17** | 缺类型注解与静态分析规范 | 代理 C 确证：`pyproject.toml`/`setup.cfg`/`mypy.ini`/`.ruff.toml`/`pytest.ini`/`.pre-commit-config.yaml`/`Makefile` 等**全部不存在**；CI 无 linter 步骤 |
| **F-D1-14** | `restore.bat` 混杂 CRLF/LF 换行 | ⚠️ **收窄**（代理 C + A）：HEAD 提交内容是**纯 LF**，`.gitattributes` 的 `*.bat eol=crlf` 保证检出为 CRLF → **是工作区卫生问题，不是仓库缺陷**；且本机 cmd.exe 解析与退出码透传实测均正常，**影响未复现** |

### 3.2 归因需要修正

| 编号 | 报告说法 | 修正后 |
|:--|:--|:--|
| **F-D2-01** | 哨兵切片导致恶意词典执行任意代码（Critical） | **生产路径不可达**：`/*AG_ZH_ZH_START*/` 是**完整注释**，恶意值困在 JS 字符串字面量内，`node --check` 通过且注入语句未执行；只有"对已 splice 引擎再次 splice"才会执行，而产品每次都拼接到原始内嵌引擎。**但底层机制真实 → 已按加固处理**（构建期 + 补丁期双重拦截） |
| **F-D4-01** | CI 静默放行导致**发布空 Release**（High） | **"空 Release"不可达**（`download-artifact` 会先失败）。真实可达后果是**发布缺一个平台二进制的 Release** + CI 全程绿灯，根因是 `build.py main()` 丢弃返回值（N-08） |
| **F-D2-05** | 外部词典加载存在原型链污染隐患 | **不是全局原型链污染**（`({}).polluted === undefined`）；真实影响是 `for..in` 把继承属性提升为 `lowerTranslations` 自有键，可遮蔽单个 UI 文案（N-10） |
| **F-D4-02** | 发布矩阵完全缺失 Linux 与 macOS Intel 二进制 | **部分成立**：矩阵确实只有 2 项，但 **README 从未宣传 Linux 二进制**（只宣传 Windows 与 macOS Apple Silicon），且 Intel Mac 有明确的"方式 2：源码运行"路径 → 属"脚本支持 Linux 但无二进制交付"的落差，非"违背 README 承诺"。另注：即便补 Intel 产物，**现有 ZIP 仍会让 Intel 用户硬失败**（见 N-13） |
| **F-D5-01** | 测试"自洽假象"：致命缺陷零覆盖 | **部分成立、已大幅收窄**：测试数 73 → **103**，那 1 项 Critical + 5 项 High 现在都有对应回归用例。残余的"自洽"成分：引擎 8 项用例中**仅 1 项**真正跑 Node，其余是对源码的字符串断言 |
| **F-D5-02** | 菜单/原生补丁测试缺乏真实 JS 执行环境与语义验证 | **部分成立**：语义验证已补齐（用 Python 模拟 Electron 菜单结构断言条目**真正落入** File 子菜单）；但"真实 JS 执行环境"仍缺 —— 菜单路径无任何 JS 执行 |
| **F-D5-03** | 缺 BOM / 拒绝执行 / ASAR 截断三类边界用例 | **部分成立**：拒绝执行**已覆盖**（断言退出码 1 + ASAR 字节未变）；BOM **仍缺且缺陷在线**（N-07）；ASAR 截断**缺测试但行为安全**（实测三种截断都被捕获 → 退出码 1） |
| **F-D5-04** | 引擎与提取脚本覆盖率 0% | **部分成立**：引擎已有 8 项用例（1 项真实 Node 执行）；但**提取脚本仍 0% 覆盖**。准确表述应为"提取脚本 0%；引擎仅 1/8 具备行为验证，无 DOM/翻译链路测试" |

### 3.3 本轮仍未逐条验证

其余约 40 条（F-D1-03/04/05/06/07/08/09/10/12/13/14/15/16/17/18、F-D2-03/06/07/08/09/10、F-D3-02/07/08/09/10、F-D4-02/03/04/05、F-D5-01~05）由复核代理继续处理中，**本报告不对它们下结论**。已知的部分结论：

- **F-D5-01**（测试"自洽假象"）**部分成立且正在被本轮改动削弱**：测试数已从 73 → **103**，新增 30 个用例，含效果层的菜单插入仿真与真实 Electron 运行时探针。
- **F-D5-02**（菜单测试缺乏真实 JS 执行环境）**已被本轮部分解决**：`tests/test_engine.py` 现在用 `node` 实跑 `escapeDollar`，菜单测试用客户端真实 `addItemToSubmenu` + Electron 44 菜单结构仿真。

---

## 4. 复核代理的执行情况

| 代理 | 范围 | 状态 |
|:--|:--|:--|
| A | 引擎运行时 + 脚本类 14 条（F-D1-04~F-D1-18） | ✅ **已完成**：**成立 10 / 部分成立 4 / 不成立 0**，含 jsdom 实测引擎行为、真实 `app.asar` 往返、进程探测打桩 |
| B | 安全 + ASAR 稳健性 14 条（F-D2-03~F-D2-10、F-D3-02~F-D3-10） | **已产出部分结论后中断**：确认 F-D3-04（Dock 菜单未汉化）、发现菜单点击处理器的 label 查找问题（→ 我已独立精化为 N-06）；F-D2-04/05/03 未完成，由本轮补验 |
| C | CI/CD + 测试 10 条 + 全新扫描 | ✅ **已完成**：成立 6 / 部分成立 5 / 不成立 0 + **11 项新发现**（N-13~N-19）+ 3 处原审计纠正 |

### 3.0 代理 A 对 F-D1-04~F-D1-18 的逐条判定（含 jsdom 实测）

| 编号 | 判定 | 关键实测数据 / 修正要点 |
|:--|:--|:--|
| **F-D1-04**（每 2 秒同步 I/O） | **部分成立 → 降 Low/Info** | 实测 `zh-CN.json`(139 KB) 读+解析 **0.699 ms**、`patterns.json` **0.087 ms**，合计 **0.805 ms/次**；且真实沙箱客户端里 `nodeFs()` 返回 null → **该路径是死代码**，真机上不存在每 2 秒 I/O |
| **F-D1-05**（编辑器 token 穿透） | **成立** | jsdom 实测：动态 append 的 `<span class="mtk1">Cancel</span>`（在 Monaco `.view-lines` 内）**被改成 "取消"**；周期扫描走 `skipSubtree` 安全，**只有动态插入才穿透** |
| **F-D1-06**（`disconnect()` 丢 mutation） | **部分成立 → 降 Info** | 机制真实，但报告描述的"并发渲染窗口"在单线程 JS 中不可实现；构造第三方变更窗口**未复现丢失**；且 2 秒全量扫描会重新翻译，非"永久"丢失 |
| **F-D1-07**（2 秒全量遍历） | **部分成立（须拆分）** | 实测每次回调：2,005 元素 **14.2 ms**、20,005 元素 **130.4 ms**（≈6.5 µs/节点线性标度）；但 `querySelectorAll('*')` **只执行 1 次**（开关存在即 return），**不是周期开销** |
| **F-D1-08**（Pattern 替换未转义 `$`） | **成立（触发条件须改写）** | 只有 `$$`/`$&`/`$'`/`` $` `` 会损坏；**`$100`/`$PATH`/`$1` 不会**（外层模式是字符串，0 个捕获组）。用已发布规则 #13 复现：输入 `Your Plan: Pro $& bonus` → 输出 `您的方案: Pro Your Plan: Pro $& bonus bonus`（文本重复） |
| **F-D1-09**（无进程前置校验 + Win32 降级） | **成立（措辞须改）** | 打桩 `OpenProcess` 返回 0：name-only 仍看到 **9 个** Antigravity PID，但 `_find_...()` → None → 误报"未运行"。影响是**全部工作做完后才晚失败**（退出码 1），不是崩溃 |
| **F-D1-10**（1000 条锁死） | **成立** | 注入 1005 条互异串后：第 1/999/1000 条命中，**第 1005 条被丢弃**；无任何自动/UI 清除路径 |
| **F-D1-11**（还原恒为误报） | **成立** | 真实文件：+184,010 B ≈ 179.7 KB **全部来自引擎**，还原结果 SHA 与官方备份**完全一致** → 100% 误报。根因是 `restore_backup` 未复用已存在的 `compute_build_fingerprint()`（N-21） |
| **F-D1-12**（无 Magic 校验/越界切片） | **成立** | magic 改 `0xDEADBEEF` 仍成功提取 765 个文件；载荷截断 → **317 个成员静默变 0 长度**，重打包后损坏被**固化**（N-22） |
| **F-D1-13**（硬编码 arm64） | **成立（报告低估严重度）** | WSL 实测退出码 **126**，x64 与 python3 回退**均未到达**；且 CI 矩阵**只有 macos-latest/arm64** —— **发布包里根本不存在 macOS x64 二进制** |
| **F-D1-14**（`restore.bat` 混合行尾） | **部分成立 → 保留 Low** | 事实成立（44 CRLF + 13 LF，关键分支在 11-15/50-57）；但本机 cmd.exe 解析正确、退出码 7 正确透传，**影响未复现** → 属规范性问题 |
| **F-D1-15**（提取器噪音） | **成立** | 对真实客户端实跑：app.asar **44,804** 条 + language_server.exe **224,708** 条 → 合计 **269,217** 条候选，样本全是 `'! !/!4!OEH!M!R!a!k!'` 这类二进制噪音 |
| **F-D1-16**（复制二进制静默失败） | **成立** | 打桩 `copy2` 抛 PermissionError → 仍打印 `[+] Copied to repo root.`，`build()` 返回 **True** → 假阳性成功 |
| **F-D1-18**（无差别捕获） | **成立（事实）/ Info 级** | 实测 `except Exception:`：`build.py` **10 处**、`patcher.py` **8 处**；JS 空 catch **5 处**。多数是有意防御，但 `build.py:163/202`（→ F-D1-09 误报根源）、`:248`（边车 fail-open）、`:884`（→ F-D1-16）、`engine_template.js:361`（→ N-20）确实掩盖失败 |

代理 B 的一条中间结论值得记录：它最初判定"打补丁后的 menu.js 破坏了点击处理器查找"。我独立复算后**收窄为 N-06**——真正的问题不是点击永久失效（`updateMenuState` 会把 label 改回状态串从而自我恢复），而是**中文标签被覆盖导致汉化无效**。两者的严重级别与修法都不同，故以我的复算为准。

---

## 5. 第一轮改动的自审结论

逐项复核 `git diff`：

| 改动 | 自审结论 |
|:--|:--|
| `apply_literal_replacements()` 分组 + hits/replaced | ✅ 正确。注意 `replaced = hits - after` 依赖"新串不含旧串"，当前 7 条替换均满足；若将来加入自包含替换需改用计数法 |
| `compute_build_fingerprint()` | ✅ 正确。排除 4 个补丁目标、纳入 unpacked 路径；真实文件复验：同构建通过、异构建拒绝 |
| `ensure_backup_sidecar()` | ⚠️ **有一处设计遗漏**（N-12）：补写等于把"当前状态"登记为基线，无法回溯既有篡改 |
| `apply_patch()` 三处 `return False` | ✅ 正确。真实文件复验：退出码 1、文件字节未变 |
| 引擎 `escapeDollar` 函数替换器 | ✅ 正确，`node` 实跑确认 |
| 引擎 fs 不可用告警 | ✅ 正确，`_fsWarned` 保证只告警一次 |
| 词典 31 条空白 key 清理 | ✅ 正确。27/27 不可达文案实测全部可翻译 |
| 11 条新 pattern 规则 | ✅ 正确。已剔除 4 条与既有规则重复的；`#03` 的句号改用全角 |
| `build()` 构建期校验 | ✅ 正确，实测能拦截带空白 key 与含哨兵标记的词典 |
| `tests/test_engine.py` | ✅ 正确，`node` 实跑 |

**未引入回归**：生成物漂移检查通过（重建后字节不变）、`pytest` **103 passed**、真实 `app.asar` 端到端 **21/21 通过**。

---

## 6. 仍待处理（按建议优先级）

### 立刻处理（会静默吃掉用户的工作）

1. **N-01 + N-02**（High / Medium-High）：词典目录选择与"条目数更少即丢弃"。**推荐合并方案**：内嵌词典与外部词典按 key 合并、外部优先；删除 cwd 候选；文档位置继续生效。
2. **N-07**（High）：BOM → 用 `utf-8-sig` 读取，并把回退提示升级为 warning。
3. **N-08**（High）：`build.py main()` 传退出码；CI 的产物准备与发布步骤加 `exit 1` 守卫。
4. **N-13**（Critical）：安装脚本的架构判断 + **二进制失败后必须回落到包内 Python 路径**（Intel Mac / 误用场景当前完全无自救路径；且发布包里根本没有 x64 macOS 二进制）。
5. **N-14**（High）：提取脚本输出移出仓库、加入 `.gitignore`、构建期拒绝空译文。
6. **N-22**（High）：ASAR 读取校验 magic 与切片边界，**防止损坏被固化**。

### 本迭代内

7. **N-06**（Medium）：移除"检查更新"标签替换（或改 `updateMenuState` 包装）。
8. **N-03**（Medium）：统一 `'Archive this conversation'` 译文；CI 加"大小写变体译法必须一致"断言。
9. **F-D3-07 / F-07**（Medium）：`'Reset zoom'` → `'重置缩放'`（第一轮未纳入范围，仍在；代理 C 与代理 A 均独立复现确认在线）。
10. **N-09 / N-10**（Low）：正则白名单去掉 `y`；`for..in` 改 `Object.keys`。
11. **N-20**（Medium）：TreeWalker 的 `try/catch` 收窄到单节点，避免一次异常中止整棵子树。
12. **N-21**（Low）：`restore_backup()` 复用 `compute_build_fingerprint()`，消除恒为误报的版本告警。
13. **F-D1-08**（Medium）：Pattern 替换串里的 `$$`/`$&`/`$'`/`` $` `` 需要转义 —— 已发布规则 #13 已能复现文本重复。
14. **F-D1-05**（Medium）：Monaco token 穿透 —— 动态插入的编辑器 token 会被翻译并进入未翻译采集器。
15. **N-15 / N-16 / N-17 / N-18**（Medium~Low）：脚本加 Python 版本校验；`.zcodeignore` 对齐 `.gitignore`；CI 加 `timeout-minutes` 与 `concurrency`；拆分测试/构建依赖。
16. **F-D4-03**（Medium）：README 词条数校验正则收窄为"词条数上下文"匹配（中文 `词条` / 英文 `entries` 都要覆盖，否则 README_EN 会失配）。
17. **F-D1-16**（Medium）：`build.py` 的 `copy2` 失败不能静默、也不能无条件打印"已复制"。

### 已知但本轮未纳入范围

18. **基建项**（`pytest.ini`、ruff/mypy、pre-commit、dependabot、`SECURITY.md`、CI 冒烟测试 F-D4-04、Windows 产物补词典与批处理 F-D4-05、README 校验正则 F-D4-03 的收窄）。
19. **版本号**仍是 v1.0.4，发布前应统一升级。

---

## 7. 未验证项（诚实声明）

| 项 | 状态 |
|:--|:--|
| 三个复核代理的覆盖条目 | ✅ **全部完成**（A: 14 条 / B: 部分后中断，其未完成部分由我补验 / C: 10 条 + 全新扫描） |
| 并行报告 51 条主张的复核覆盖 | ✅ 约 30 条已逐条判定，其余未覆盖者本报告不下结论 |
| ASAR 读取的截断/边界校验（F-D1-12 / F-D3-09） | ✅ **确认为真实缺陷**（代理 A）：magic 改 `0xDEADBEEF` 仍成功；载荷截断 → 317 个成员静默变 0 长度，重打包后**损坏被固化** → 已升为 **N-22（High）** |
| Windows / macOS 实机 GUI 体验 | ❌ 未做（无 GUI 环境） |
| 引擎在真实 Electron 中的 DOM 规模与帧率 | ⚠️ 代理 A 用 jsdom 测得 2,005 元素 **14.2 ms**、20,005 元素 **130.4 ms** 每次 2 秒回调；jsdom 绝对值偏慢，Chromium 更快，**线性标度成立** |
| macOS 代码签名 / `asarIntegrity` 是否被破坏（F-D2-08） | ❌ 未验（需 macOS 环境） |
| POSIX 下 `mkstemp` 权限降为 0600（F-D2-09） | ❌ 仅代码语义推断（Windows 无法复现） |
| `install.bat` 微软商店占位符子情形 | ❌ 本机 `where python` → `D:\miniconda3\python.exe`，无法复现（"完全无版本校验"部分已确认） |
| 并发新增的 33 条译文的语言质量 | ⚠️ 抽查 2 条（发现 N-03），其余需人工评审 |
| 真实安装目录 | ✅ 全程只读，未被我修改；**用户已自行应用修复版**（实测：引擎 v1.0.4、escapeDollar 已修、菜单查找键 `['File','Help','File','File']`、边车已生成、二进制已编译 8,659,221 B） |

---

*本报告由 MCode 生成。所有"已确证"条目均附可复现命令与实测数据；凡未实测的推断均标注为"推断"或"未验证"。*
