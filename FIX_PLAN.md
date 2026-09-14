# 深度审查修复计划（Fix Plan）

> 依据 2026-09-14 全项目深度审查 + 三轮决策讨论定稿。本计划只列实施内容，不包含已否决项。
> 实施时的铁律见 [§5 双源同步规则](#5-双源同步规则必须遵守)。

---

## 0. 决策记录汇总

| # | 问题 | 决策 |
| :--- | :--- | :--- |
| C1 | `--force` + 过期备份 = 客户端静默降级 | 签名感知 + 安装脚本去掉默认 `--force` |
| C2 | "词典热加载"宣传未实现 | 真正实现热加载（保留旗舰卖点） |
| C5 | integrity 单块哈希不符 asar 分块规范 | 只重算修改过的文件 + 4MB 正确分块 |
| 小修 | git 可执行位 + README 同步 | 纳入本次 |
| R2 | 性能三连 | 编辑器排除 + 写放大节流 |
| R3 | 生成文件陷阱 | GENERATED 标记 + CONTRIBUTING 警告 |
| R6 | 菜单补丁静默失败 | 命中日志 + count=1 保守替换 |
| R8 | 零测试 | 补 round-trip pytest + 正则行为测试 |
| S1 | ASAR 写入非原子 | 纳入（见 §4.9 与运行中进程的冲突注记） |
| S2 | build.py 复制产物到个人 Desktop | 移除副作用，保留 dist/ 与仓库根 |
| S3 | 引擎小修 | en 短路 + clipboard 回退浮层 + alert/confirm 有效性验证 |
| S4 | extract_untranslated.py Windows-only | 跨平台对齐 |

**明确不在本次范围**（讨论中未选中，勿顺手改）：
- patterns.json 两条 `${unit}` 模板垃圾规则的删除（正确规则已存在于其后）
- `"刚刚"` / `"账户设置"` 字面引号修正
- patterns.json 重复规则去重、zh-CN.json 恒等映射与 `${...}` 残渣词条清理
- status.bat 补 `C:\Python3xx` 回退探测

---

## 1. C1：签名感知的补丁来源选择（消除静默降级）

**改动点**（`build.py` 内 `PATCHER_TEMPLATE` 的 `apply_patch`，见 §5）：

1. 读取源决策逻辑改为：
   ```
   读当前 app.asar（而非备份）→ 检查是否含 SIGNATURE_PRELOAD
   ├─ 含签名（已被本工具补丁，与备份同版本）且 --force：
   │    从 bak 读取（干净重打，原有意图）
   ├─ 不含签名（官方原版，无论新旧）：
   │    以当前文件为准；若 bak 存在且与当前不同 → 用当前文件刷新 bak
   │    （官方未打补丁的 asar 天然是权威版本，覆盖过期备份）
   └─ bak 不存在：照旧创建
   ```
2. 刷新备份时打印：`[*] Detected app update, refreshing official backup (old backup was stale)`。
3. 三个安装入口去掉无条件 `--force`：`install.bat:12`、`install.sh:13`、`安装汉化.command:15`（改为裸 `patch`；幂等性由"已打补丁则早退"保证，重复运行安全）。
4. `restore_backup` 增加提示：还原前若当前 asar 与 bak 均存在但大小差异显著，打印两者版本线索（size/mtime）提醒用户备份可能来自旧版本（不阻断，仅警告）。

**验收**：
- [ ] 单测：bak=v1 旧内容 + 当前 asar=v2 官方（无签名）→ patch 后产物包含 v2 内容 + 签名；bak 被刷新为 v2 官方。
- [ ] 单测：当前 asar 含签名 + force → 从 bak 重打（旧行为保留）。
- [ ] 手测：连续运行两次 `install`（无 --force）结果幂等。

## 2. C2：实现词典热加载

**前置验证（第一步，决定实现路径）**：
- 解包检查 `dist/preload.js` 顶部与主进程 bundle 的 `webPreferences`：确认 `sandbox` 与 `contextIsolation` 的实际值。
- 判据：preload 内是否可用 `require('fs')`（非 sandbox）。

**路径 A（preload 非 sandbox，首选）**：
- `engine_template.js`：启动时（init 前）用 `require('fs')` 读取平台词典目录：
  - Windows：`%APPDATA%\Antigravity\locales\`
  - macOS：`~/Library/Application Support/Antigravity/locales/`
  - （目录路径由 patcher 的 `get_locales_dir()` 语义对齐，路径拼接在引擎里按 `process.platform` 分支）
- 合并策略：外部 `zh-CN.json` / `patterns.json` 条目**覆盖**内嵌词典（外部为准）；文件缺失或解析失败 → 静默回退内嵌词典。
- 热更新：复用现有 2s 周期扫描，附带 `fs.statSync` 比对 mtime，变更时重载词典（无需 Ctrl+R）；异常全部 try/catch 包裹，引擎绝不因词典文件损坏而崩。
- `apply_patch` 在补丁成功时把内嵌词典 seed 写入该目录（用户拿到可直接编辑的初始文件）。

**路径 B（preload 被 sandbox，降级预案）**：
- 引擎侧不做文件读取；改为 `apply_patch` 注入时优先合并外部词典目录内容（改词典 → 重跑 install 即生效，无需重新 build）。
- README 措辞按 B 的真实行为改写（删除"Ctrl+R 即生效"，改为"重跑安装脚本即生效"）。

**验收**：
- [ ] 编辑外部词典 →（路径 A）2s 内或 Ctrl+R 后界面生效；（路径 B）重跑 install 后生效。
- [ ] 删除外部词典目录 → 内嵌词典兜底，无报错。
- [ ] 外部 JSON 写坏（语法错误）→ 引擎不崩，回退内嵌。

## 3. C5 + S1：ASAR 写入器改造（integrity 分块 + 原子写）

**改动点**（`write_asar_inplace`）：
1. 签名增加 `modified` 参数（本次改动路径集合，如 `{"dist/preload.js", "dist/menu.js"}`）。
2. 偏移量：仍为所有 packed 文件重算（前置文件变长必然移位）。
3. integrity：
   - `modified` 集合内：size/hash/blocks 全部重算，`blocks` 按 4MB（4194304）切块逐块 SHA-256，`hash` 为整文件 SHA-256（≤4MB 文件退化为单块，与现状一致）。
   - 集合外：`size`、`integrity` 原样保留（内容未变 → 哈希依然有效），只更新 `offset`。
4. 原子写：先写同目录临时文件（`app.asar.zh_tmp`）再 `os.replace`。
   - **Windows 冲突注记**：客户端运行中可能持有 app.asar 句柄，`os.replace` 会 `PermissionError`。处理：捕获后回退到现行"原位 r+b 写入"路径，并打印一句降级说明。顺序：先试原子替换，失败再原位写。
5. `restore_backup` 同样走新的写入器（modified=∅ 时全条目仅移位，语义不变——restore 是全量同版本写回，直接传全部文件即可，见实现时取舍）。

**验收**：
- [ ] 单测 round-trip：构造含 >4MB 文件的假 asar → patch → 读回：修改文件 blocks 多块且逐块可验证；未修改文件 integrity 与原始逐字节相同；offset 全部正确、Electron 可解析（用 read_asar 自证 + 与 @electron/asar 输出对照一次即可）。
- [ ] 单测：临时文件路径在写入失败时不残留、原 asar 不受损伤。

## 4. 其余工作项明细

### 4.1 git 可执行位
- `git update-index --chmod=+x install.sh restore.sh status.sh build.sh 安装汉化.command 还原官方.command`，提交后 macOS 克隆用户可直接执行/双击。

### 4.2 README 同步（两份）
- `README.md:70`：产物名 `antigravity-zh-macos` → `antigravity-zh-macos-arm64`（zip/tar.gz 同步加 `-arm64`），与 `README_EN.md:74` 对齐。
- 词条数：1,175+/82+ → 以实际 1,255+/108+ 更新；或改为脚本自动统计注入，避免再次漂移。
- 热加载相关措辞：按 C2 最终落地路径（A/B）校准；成功横幅"词典目录"输出保留（届时是真功能）。

### 4.3 R2 性能：编辑器排除 + 写放大节流（`engine_template.js`）
- 新增 `SKIP_SUBTREE` 判定：节点为 `PRE/CODE/TEXTAREA`、`contenteditable` 非 false、或祖先 class 含 `monaco`/`codemirror`/`cm-editor`（TreeWalker 手动下钻时遇到即 `nextNode()` 跳过整棵，不进入）。
- `translateDOM` 递归入口与 MutationObserver 的 `addedNodes` 处理同样套用该判定。
- `recordUntranslated`：内存 Set 照常累加，localStorage 持久化改为防抖（如 3s trailing）+ `beforeunload` 兜底写一次 + Ctrl+Alt+L 导出时强制写。消除每条新增的全量 stringify O(n²)。

### 4.4 R3 生成文件标记
- `PATCHER_TEMPLATE` 顶部 docstring 加：`# 本文件由 scripts/build.py 生成（GENERATED）——请勿手改；改动请编辑 build.py 中的模板或 engine/engine_template.js。`
- `build.py` 生成 `ag_localization_engine.js` 时头部注入同类注释。
- `CONTRIBUTING.md` 增加"代码结构"小节：指明真实编辑入口（`locales/*.json`、`engine/engine_template.js`、`build.py` 模板），并说明 `scripts/patcher.py` 与 `engine/ag_localization_engine.js` 为产物。

### 4.5 R6 菜单补丁（`patch_menu_js`）
- 每条替换打印命中数：`[*] menu.js: 'New Window' -> hit` / `miss`（miss 时汇总提示客户端可能已改版）。
- `addItemToSubmenu(menu, 'File'` / `'Help'` 两处改用 `content_str.replace(old, new, 1)`（仅首个匹配，Python str.replace 的 count 参数），降低改写后续同键调用的连带风险。

### 4.6 R8 测试（新增 `tests/`）
- `tests/test_asar.py`：
  - round-trip：构造多目录、多尺寸（含 >4MB 与 0 字节）、含 `unpacked: true` 条目的假 asar → read → 修改 → write → read，断言 offset/size/integrity/内容。
  - C1 场景两个用例（见 §1 验收）。
  - C5 场景：未修改文件 integrity 逐字节保留。
- `tests/test_patterns.py`：加载 `locales/patterns.json`，对代表性输入断言输出。
  - **注意**：两条 `${unit}` 规则用户已决定暂不修 → 对应用例标 `@pytest.mark.xfail(reason="已知垃圾输出，见 FIX_PLAN 范围外声明")`，测试套件保持绿色同时固化该债务。
- 运行方式：`python -m pytest tests/ -v`；不新增第三方依赖（纯 stdlib + pytest，pytest 进 `requirements.txt`）。

### 4.7 S2 build.py 去个人副作用
- 删除 `build.py:384-395` Desktop 复制块（含吞异常的 try/except）；保留 `dist/` 输出与仓库根复制（后者供本地双击场景，README 已引用）。

### 4.8 S3 引擎小修三合一（`engine_template.js`）
- **en 短路**：`currentLang === 'en'` 时 init 只注入语言切换按钮，不启动 observer/周期扫描/词典匹配；切回中文经 `location.reload` 自然恢复完整引擎。
- **clipboard 回退浮层**：`navigator.clipboard` 不可用或写入失败时，弹出一个含 `<textarea>`（自动全选）的浮层承载导出 JSON，而非仅 toast 提示。
- **alert/confirm 代理**：按 C2 前置验证拿到的 `contextIsolation` 结论处置——隔离开启则删除这两段死代码（引擎 26-46 行模板区），未隔离则保留。

### 4.9 S4 extract_untranslated.py 跨平台
- `run_extraction` 默认目标复用平台判定：macOS `/Applications/Antavity.app/...`（注意拼写，正确为 Antigravity）/ Linux 候选路径；`language_server` 二进制名按平台（无 `.exe` 后缀）；Windows 保持现状。

---

## 5. 双源同步规则（必须遵守）

`scripts/patcher.py` 与 `engine/ag_localization_engine.js` 是生成文件（本次暂不重构单一来源）：

1. **所有 patcher 逻辑改动**：改 `build.py` 内 `PATCHER_TEMPLATE` → 运行 `python scripts/build.py --no-exe` 重新生成 `patcher.py` → 提交两者。
2. **所有引擎改动**：改 `engine/engine_template.js` → 同一次 `--no-exe` 构建刷新产物 → 提交两者。
3. 禁止直接编辑产物文件后提交（下次构建即被覆盖，白干）。

## 6. 实施顺序（依赖驱动）

| 步骤 | 内容 | 依赖 |
| :--- | :--- | :--- |
| 0 | §4.1 git chmod +x（独立，随时可做） | 无 |
| 1 | §4.6 测试基线（先固化当前行为） | 无 |
| 2 | §3 写入器改造（C5+S1）+ 跑测试 | 1 |
| 3 | §1 签名感知（C1）+ 安装脚本去 --force + 新增用例 | 2 |
| 4 | C2 前置验证 → 引擎热加载 + patcher seed 词典 | 2,3 |
| 5 | §4.3 性能 + §4.8 引擎三合一（同在 template 改，与 4 合并构建） | 4 |
| 6 | §4.5 菜单补丁、§4.4 生成标记、§4.7 build.py、§4.9 提取工具 | 3 |
| 7 | §4.2 README 两份同步（等 C2 路径定稿后最后写，避免二次返工） | 4 |
| 8 | 全量收尾：`python scripts/build.py`（含 exe）→ `pytest` 全绿 → `status` 实机核验（有装客户端时） | 全部 |

## 7. 总体验收

- [ ] `python -m pytest tests/ -v` 全绿（含 2 条 xfail）。
- [ ] 真机（Windows 优先）：install → 新窗口见汉化；改外部词典 → 生效；restore → 官方还原。
- [ ] `git ls-files -s` 中 6 个脚本均为 `100755`。
- [ ] 两份 README 与 CI 产物名、词条数、热加载行为零出入。
- [ ] 全新 clone + `python scripts/build.py --no-exe` 产物与提交的产物 diff 为零（双源一致性证明）。
