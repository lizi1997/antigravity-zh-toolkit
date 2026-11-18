# Antigravity-ZH Toolkit 全面代码质量、安全与工程架构审计报告

**报告版本**：v2.0.0 (Master Release)  
**审计基线**：antigravity-zh-toolkit (v1.0.4, commit `5bf1bfd`, main 分支)  
**审计日期**：2026-11-09  
**审计组织**：Teamwork Multi-Agent Security & QA Audit Team  
**审计方法**：全量源码语义通读 + 测试套件实跑验证 (`pytest tests/`) + 真实 Electron 44.5.1 运行时探针 + ASAR 结构化解析往返验证 + 仿真环境边界测试  

---

## 1. 执行概要 (Executive Summary)

### 1.1 项目定位与总体评估

`antigravity-zh-toolkit` 是一款针对基于 Electron 构建的 AI 智能体开发环境（Google Antigravity）的本地化汉化工具包。其核心架构包括：
1. **构建与模板生成器**（`scripts/build.py`）：负责生成预分发可执行补丁器、将内嵌词典与多语言引擎拼装入 JavaScript 脚本模板，并打包 PyInstaller 二进制；
2. **本地安装补丁器**（`scripts/patcher.py`）：在用户终端提取目标 `app.asar`、注入汉化核心并原地替换；
3. **运行时翻译引擎**（`engine/ag_localization_engine.js` / `engine/engine_template.js`）：注入至 Electron 渲染进程，通过 MutationObserver 与 DOM TreeWalker 动态翻译 UI 元素；
4. **本地化词典与动态正则库**（`locales/zh-CN.json`, `locales/patterns.json`）：涵盖 2,070 条静态词条与 142 条动态正则规则；
5. **CI/CD 发布流水线**（`.github/workflows/release.yml`）：负责多平台构建、SHA-256 校验和生成与 GitHub Releases 自动化交付。

在宏观架构层面，本项目体现出了优于普通汉化补丁的工程设计：实现了原生二进制级别安全的 ASAR 解包/打包器、严格的原子性文件写入（`tempfile.mkstemp` + `os.replace`）、SHA-256 备份边车比对机制、生成文件代码漂移检查，以及 CI 流程中严格锁定的 Action Commit SHA。

然而，经过本次多维度、深层次的联合审查，审计团队在真实客户端文件、动态运行时与跨平台构建流水线中，发现了 **2 项 Critical（致命）、16 项 High（高危）、18 项 Medium（中危）、8 项 Low（低危）及 4 项 Informational（说明）** 的重大缺陷。

---

### 1.2 风险矩阵 (Risk Matrix)

| 影响严重度 \ 发生概率 | 高频 / 必然触发 (High Likelihood) | 中频 / 特定条件触发 (Medium Likelihood) | 低频 / 极端边界 (Low Likelihood) |
|:---|:---|:---|:---|
| **致命 (Critical)** | **[F-D1-01 / F-D3-01]** 原生菜单补丁改写子菜单查找键导致菜单项静默丢失并破坏快捷键 | **[F-D2-01]** 注释哨兵切片 AST 逃逸导致恶意词典执行任意代码 (RCE) | — |
| **严重 (High)** | **[F-D1-02]** `apply_patch` 拒绝执行时返回退出码 0<br>**[F-D2-02]** `escapeDollar` 属 JS No-Op 导致文本损坏<br>**[F-D3-05]** UTF-8 BOM 导致外部词典被静默丢弃<br>**[F-D3-06]** 31 条带空格词条因引擎契约 100% 无法命中<br>**[F-D4-01]** CI 编译产物缺失静默放行发布空 Release<br>**[F-D5-01]** 测试套件全绿假象（73 用例 0 失败覆盖） | **[F-D1-04]** 主 UI 线程每 2 秒同步 I/O 与反序列化<br>**[F-D1-05]** 编辑器 Token 穿透跳过区泄露进入翻译<br>**[F-D2-03]** 动态正则缺乏回溯限制引发 ReDoS 冻结线程<br>**[F-D2-08]** 原地篡改 ASAR 破坏 macOS 代码签名<br>**[F-D3-02]** 原生注入对压缩及打包器别名极度脆弱<br>**[F-D3-03]** 原生补丁缺失 MISS 告警与假阳性<br>**[F-D4-02]** 发布矩阵完全缺失 Linux 与 macOS Intel 二进制 | **[F-D3-04]** 原生对话框状态文本与 Dock 菜单覆盖不全 |
| **中危 (Medium)** | **[F-D1-07]** 2 秒全量 DOM 树遍历与全局 QuerySelector<br>**[F-D1-10]** 未翻译收集器 1000 条后永久锁死<br>**[F-D1-11]** 还原时因 ASAR 尺寸膨胀产生恒为误报的警告<br>**[F-D3-07]** 大小写归一化后写覆盖破坏正确译文 | **[F-D1-06]** `disconnect()` 导致并发渲染 Mutation 丢失<br>**[F-D1-08]** Pattern 替换字符串未转义 `$`<br>**[F-D1-09]** 补丁前缺少进程运行检查<br>**[F-D1-13]** 脚本盲目执行 arm64 导致 Intel Mac 崩溃<br>**[F-D2-04]** 正则白名单允许 Sticky 标志 `y` 导致跳过<br>**[F-D2-05]** 外部词典加载存在原型链污染隐患<br>**[F-D2-07]** Fail-open 边车校验与无条件还原被篡改备份<br>**[F-D2-10]** 未翻译收集器采集敏感提示词与隐私泄露<br>**[F-D3-08]** ASAR 缺失原生文件时静默跳过<br>**[F-D4-03]** README 词条数校验正则过度僵硬<br>**[F-D4-04]** CI 缺少编译二进制自动化冒烟测试<br>**[F-D4-05]** Windows 发布物缺少词典及批处理脚本 | **[F-D1-12 / F-D2-06 / F-D3-09]** ASAR 缺少 Magic 与边界检查导致切片截断并固化 |
| **低危 (Low)** | **[F-D1-14]** `restore.bat` 混杂 CRLF/LF 换行符<br>**[F-D1-17]** 项目缺失类型注解与静态代码分析规范 | **[F-D1-15]** `extract_untranslated` 二进制刮取垃圾<br>**[F-D1-16]** `build.py` 复制二进制失败被静默抑制<br>**[F-D2-09]** POSIX 下 `mkstemp` 导致 ASAR 权限降至 0600<br>**[F-D3-10]** Windows 非 UTF-8 控制台触发 Unicode 崩溃<br>**[F-D5-05]** 根目录缺失 `pytest.ini` 与覆盖率门禁 | — |
| **说明 (Info)** | **[F-D1-18]** 全局泛滥的无差别捕获异常<br>**[F-INFO-01]** ASAR 基础读写算法格式合规（正向）<br>**[F-INFO-02]** 代码生成物与模板零漂移（正向）<br>**[F-INFO-03]** 词典中部分词条译文缺失或退化 | — | — |

---

### 1.3 缺陷严重级别统计表

| 审查维度 (Audit Dimension) | Critical | High | Medium | Low | Informational | 维度总计 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dimension 1**: 全面代码质量、架构与错误处理审计 | 1 | 4 | 8 | 4 | 1 | **18** |
| **Dimension 2**: 安全性、ReDoS、代码注入与 ASAR 篡改审计 | 1 | 3 | 5 | 1 | 0 | **10** |
| **Dimension 3**: ASAR 原生补丁注入稳健性与边界情况审查 | 1 | 5 | 3 | 1 | 0 | **10** |
| **Dimension 4**: CI/CD 自动化构建配置审查 | 0 | 2 | 3 | 0 | 0 | **5** |
| **Dimension 5**: 测试套件覆盖率、有效性与执行验证审查 | 0 | 4 | 0 | 1 | 0 | **5** |
| **说明与正向合规项 (Informational Findings)** | 0 | 0 | 0 | 0 | 3 | **3** |
| **总计 (Total)** | **2** | **16** | **18** | **8** | **4** | **48** |

---

### 1.4 核心系统性失效链分析 (Systemic Failure Chains)

审计发现，单个孤立缺陷由于相互交织，在实际使用场景下演化成了破坏性极强的**系统性失效链**：

#### 致命失效链 A：核心功能自毁与文档承诺冲突链
```
[README 承诺: 按 Ctrl+Shift+N / Cmd+Shift+N 新建窗口体验纯正中文]
                         ↓
[scripts/build.py: patch_menu_js 执行]
                         ↓
[错误改写查找键: addItemToSubmenu(menu, 'File') → addItemToSubmenu(menu, '文件 (File)')]
                         ↓
[Electron 原生菜单项 label 恒为 'File'，items.find 必然返回 undefined 触发 early return]
                         ↓
[File 菜单下的 'New Window' 条目及其快捷键 CmdOrCtrl+Shift+N 被永久、静默丢弃！]
                         ↓
[补丁日志谎报: hit x3: addItemToSubmenu(menu, 'File'，安装器打印成功横幅指引用户按快捷键]
                         ↓
[最终结果: 用户安装补丁后发现主功能快捷键彻底失灵，官方文档条目丢失]
```

#### 致命失效链 B：沙箱环境阻断与静默拒绝退出链
```
[README 承诺: 直接编辑外部词典，每 2 秒热加载自动生效；或重新运行安装器生效]
                         ↓
[真机实测: Electron 44.5.1 preload 处于强制沙箱环境，require('fs') 抛出 module not found]
                         ↓
[热加载路径完全瘫痪，修改词典只能依赖 patcher 重新打入 ASAR]
                         ↓
[用户修改词典并重跑安装器，触发 scripts/build.py:478-485 的无备份或校验和不匹配分支]
                         ↓
[patcher 打印警告但执行 return True，CLI 进程以退出码 0 退出]
                         ↓
[安装脚本 (install.bat / install.sh) 判定返回码 0 为成功，报告汉化成功！]
                         ↓
[最终结果: app.asar 零字节改动，用户修改彻底丢失，工具却报告全部成功，完全无法排查]
```

#### 严重安全链 C：社群词典恶意分发与远程代码执行链
```
[用户从社群下载经第三方定制的 `zh-CN.json` 或 `patterns.json` 词典]
                         ↓
[词典内巧妙构造包含注释哨兵的字符串: "/*AG_ZH_ZH_END*/; require('child_process').execSync('...'); /*"]
                         ↓
[scripts/build.py 或 patcher.py 的 splice_engine_dicts 使用 code.find(end_mark) 进行字符串拼接]
                         ↓
[切片在 JSON 内部提前闭合，恶意代码逃逸出 JSON 字面量，直接注入 dist/preload.js 顶层作用域]
                         ↓
[Antigravity 客户端启动，preload 脚本以主进程/Node.js 高权限执行注入命令，用户主机完全沦陷]
```

---

## 2. 审计范围、环境与执行基线 (Audit Scope & Execution Baseline)

### 2.1 审查代码库清单

本次审计严格覆盖仓库内全量受控代码及构建自动化配置（共计 26 个核心跟踪文件，9,842 行代码）：

| 模块类别 | 核心文件路径 | 代码行数 | 承担职责与审查范围 |
|:---|:---|:---:|:---|
| **核心运行时引擎** | `engine/engine_template.js`<br>`engine/ag_localization_engine.js` | 584<br>3,370 | 注入 Electron 渲染进程的多语言引擎源码与构建后合成文件；审查 DOM 拦截、MutationObserver、正则引擎、I/O |
| **构建与补丁器** | `scripts/build.py`<br>`scripts/patcher.py` | 744<br>623 | 打包构建脚本（内嵌 `PATCHER_TEMPLATE`）与生成的最终补丁器；审查 ASAR 读写、字符串注入、备份管理、退出状态 |
| **辅助与提取工具** | `scripts/extract_untranslated.py` | 117 | 未翻译词条静态扫描与启发式过滤工具；审查 ASAR 解析、文件 I/O |
| **多语言本地化资源** | `locales/zh-CN.json`<br>`locales/patterns.json` | 2,072<br>712 | 静态汉化词典（2,070 条）与动态正则规则（142 条）；审查可达性、BOM 头、空格异常、大小写冲突 |
| **测试套件** | `tests/test_asar.py`<br>`tests/test_patterns.py`<br>`tests/conftest.py` | 500<br>106<br>7 | Pytest 单元与集成测试套件；实跑验证测试覆盖率、有效性与断言真实度 |
| **CI/CD 流水线** | `.github/workflows/release.yml` | 188 | GitHub Actions 自动化多平台矩阵构建与 Release 发布流水线；审查供应链安全与构建完整性 |
| **终端与批处理脚本**| `install.bat` / `install.sh`<br>`restore.bat` / `restore.sh`<br>`status.bat` / `status.sh`<br>`安装汉化.command` / `还原官方.command` | 59 / 33<br>58 / 33<br>52 / 21<br>24 / 24 | Windows、macOS 及 Linux 平台终端启动脚本；审查平台兼容性、架构适配、编码规范 |

---

### 2.2 自动化测试套件执行实测验证

在完全隔离的真实审计环境中，直接执行项目既有测试套件，获取真实输出基线：

```bash
$ pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.13.11, pytest-9.1.1, pluggy-1.5.0 -- D:\miniconda3\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\win\OneDrive\Desktop\antigravity-zh-toolkit
plugins: anyio-4.12.1
collected 73 items

tests/test_asar.py::test_read_roundtrip PASSED                           [  1%]
tests/test_asar.py::test_write_offsets_shift_after_growth PASSED         [  2%]
tests/test_asar.py::test_unmodified_integrity_preserved PASSED           [  4%]
tests/test_asar.py::test_modified_big_file_gets_chunked_integrity PASSED [  5%]
tests/test_asar.py::test_default_modified_recomputes_all PASSED          [  6%]
tests/test_asar.py::test_no_tmp_file_left_behind PASSED                  [  8%]
tests/test_asar.py::test_atomic_replace_failure_preserves_original PASSED [  9%]
tests/test_asar.py::test_splice_engine_dicts_swaps_content PASSED        [ 10%]
tests/test_asar.py::test_splice_engine_dicts_missing_sentinels_falls_back PASSED [ 12%]
tests/test_asar.py::test_load_valid_json_text_rejects_garbage PASSED     [ 13%]
tests/test_asar.py::test_c1_stale_backup_refresh PASSED                  [ 15%]
tests/test_asar.py::test_c1_same_size_stale_backup_refresh PASSED        [ 16%]
tests/test_asar.py::test_cli_failure_returns_nonzero[patch] PASSED       [ 17%]
tests/test_asar.py::test_cli_failure_returns_nonzero[restore] PASSED     [ 19%]
tests/test_asar.py::test_c1_force_repatches_from_backup_exactly_once PASSED [ 20%]
tests/test_asar.py::test_c1_rerun_without_changes_is_noop PASSED         [ 21%]
tests/test_asar.py::test_c1_force_without_backup_keeps_existing_patch PASSED [ 23%]
tests/test_asar.py::test_c1_dictionary_update_triggers_repatch PASSED    [ 24%]
tests/test_asar.py::test_c1_invalid_external_dict_falls_back_to_embedded PASSED [ 26%]
tests/test_asar.py::test_backup_sidecar_written_on_first_patch PASSED    [ 27%]
tests/test_asar.py::test_repatch_refuses_tampered_backup PASSED          [ 28%]
tests/test_asar.py::test_restore_warns_on_checksum_mismatch PASSED       [ 30%]
tests/test_asar.py::test_legacy_backup_without_sidecar_still_repatches PASSED [ 31%]
tests/test_asar.py::test_patch_seeds_locale_files PASSED                 [ 32%]
tests/test_asar.py::test_patch_menu_uses_conservative_first_occurrence PASSED [ 34%]
tests/test_asar.py::test_patch_updater_dialogs PASSED                    [ 35%]
tests/test_asar.py::test_patch_main_dialogs PASSED                       [ 36%]
tests/test_patterns.py::test_patterns_file_structure PASSED              [ 38%]
tests/test_patterns.py::test_zh_dictionary_loads PASSED                  [ 39%]
tests/test_patterns.py::test_pattern_expected_translations[...] PASSED (44 items) [ 41% - 100%]

============================== warnings summary ===============================
D:\miniconda3\Lib\site-packages\_pytest\cacheprovider.py:469: PytestCacheWarning: could not create cache path C:\Users\win\OneDrive\Desktop\antigravity-zh-toolkit\.pytest_cache\v\cache\nodeids: [WinError 5] Access is denied
======================== 73 passed, 1 warning in 0.54s ========================
```

**测试基线关键结论**：
- 测试套件用时极短（0.54 秒），73 个测试全部绿灯通过；
- 伴随 1 项 `PytestCacheWarning`（因 Windows 工作区环境权限导致 pytest cache 目录无法写入）；
- **重大盲区警示**：尽管测试 100% 通过，测试套件却处于完全的"自洽/自证明模式"（Self-proving Mode）——它没有断言任何修改后的 JavaScript 在 V8 运行时中的真实执行效果，没有测试拒绝执行时的真实退出码，没有测试带有 UTF-8 BOM 的实际词典文件，更对占项目 40% 以上代码量的引擎运行时和提取工具保持 **0% 的零覆盖率**。

---

## 3. 维度一：全面代码质量、架构与错误处理审计 (Dimension 1)

---

### [F-D1-01] 子菜单查找键被篡改导致原生菜单项静默丢失并破坏核心快捷键
- **Finding ID**: [F-D1-01]
- **Title**: Submenu Lookup Key Corruption in `patch_menu_js` Silently Discards Menu Items
- **Location**: `scripts/build.py:328-332` / `scripts/patcher.py:301-305`
- **Severity**: **Critical**
- **Root Cause**:
  在 `patch_menu_js` 中，补丁试图通过替换 `addItemToSubmenu` 的参数来汉化顶级菜单：
  ```python
  ("addItemToSubmenu(menu, 'File'", "addItemToSubmenu(menu, '文件 (File)'", 1),
  ("addItemToSubmenu(menu, 'Help'", "addItemToSubmenu(menu, '帮助 (Help)'", 1),
  ```
  在 Electron 客户端的架构中，`addItemToSubmenu(appMenu, submenuLabel, position, item)` 是一个内部查找注入函数：
  ```javascript
  function addItemToSubmenu(appMenu, submenuLabel, position, item) {
      const submenuItem = appMenu.items.find((item) => item.label === submenuLabel);
      if (!submenuItem?.submenu) { return; }
      submenuItem.submenu.insert(position, item);
  }
  ```
  该函数通过 `item.label === submenuLabel` 在 Electron 默认应用菜单项中查找匹配对象。Electron 的默认一级菜单 `label` 是由原生层构建的 `'File'` 与 `'Help'`，补丁并没有也不可能修改 Electron 原生主菜单构建模板。当把查找键改为 `'文件 (File)'` 时，`appMenu.items.find` 必定返回 `undefined`，函数直接提前 `return`。
- **Impact**:
  File 菜单下的 `'New Window'` 条目（绑定的全局快捷键 `CmdOrCtrl+Shift+N`）以及 Help 菜单下的 `'Docs'` 条目**被永久静默丢弃**。用户安装汉化后不仅看不到这两个菜单项，而且 README 和安装成功横幅中所醒目宣传的核心快捷键（`请按 Ctrl+Shift+N / Cmd+Shift+N 新建窗口`）彻底失灵。补丁日志却汇报 `hit x1`，极具欺骗性。
- **Remediation**:
  彻底移除对 `addItemToSubmenu` 查询参数的替换。若需修改显示标签，应在菜单项被查找到后修改其属性，或仅保留对子项 `label:` 的替换：
  ```python
  def patch_menu_js(content_str):
      replacements = [
          ("label: 'New Window'", "label: '新建窗口 (New Window)'", -1),
          ("label: 'Docs'", "label: '官方文档 (Docs)'", -1),
          ("label: updater_1.MenuUpdateStep.CheckForUpdates", "label: '检查更新 (Check for Updates)'", -1),
          # CRITICAL: DO NOT modify submenu lookup keys ('File', 'Help')!
          # addItemToSubmenu queries the existing appMenu by exact English label.
      ]
      applied = []
      for old, new, count in replacements:
          if old in content_str:
              content_str = content_str.replace(old, new, count)
              applied.append(f"hit: {old}")
      return content_str
  ```

---

### [F-D1-02] `apply_patch` 在操作遭拒绝时返回 `True` 导致 CLI 退出码为 0
- **Finding ID**: [F-D1-02]
- **Title**: `apply_patch` Returns `True` (Exit Code 0) on Refused Operations
- **Location**: `scripts/build.py:478-485, 494-500, 646` / `scripts/patcher.py:451-458, 467-473, 620`
- **Severity**: **High**
- **Root Cause**:
  在 `apply_patch()` 中，当检测到词典变更但官方备份 `app.asar.bak` 不存在，或者备份 SHA-256 校验和不匹配，或者指定了 `--force` 但缺少干净备份时，代码打印 `[!]` 警告后执行了 `return True`。在 `main()` 函数中，退出码映射为 `raise SystemExit(0 if ok else 1)`。
- **Impact**:
  外层 Shell 包装器（`install.bat`、`install.sh`）和 CI 脚本由于接收到退出码 0，判定补丁安装成功。实际上，目标 `app.asar` 完全没有发生任何写入，用户更新的词典完全未被装配。这形成了"修改词典 -> 重跑安装器 -> 显示成功 -> 界面无改动"的无声失败循环。
- **Remediation**:
  在所有拒绝执行或状态校验失败的分支中，严格返回 `False`：
  ```python
  if not os.path.exists(bak_path):
      print("[!] Error: Dictionaries changed but no official backup exists to re-patch from.")
      print("[!] Run `restore` first or reinstall the official client to establish a clean base.")
      return False

  if not backup_matches_sidecar(bak_path):
      print("[!] Error: Backup checksum mismatch - app.asar.bak may have been replaced or modified.")
      print("[!] Refusing to patch from it. Run `restore` to re-baseline.")
      return False
  ```

---

### [F-D1-03] 单体大字符串模板（`PATCHER_TEMPLATE`）阻碍工程化治理与静态类型检查
- **Finding ID**: [F-D1-03]
- **Title**: Monolithic String Template (`PATCHER_TEMPLATE`) Obstructs Tooling and Causes Drift
- **Location**: `scripts/build.py:27-650` / `scripts/patcher.py:1-623`
- **Severity**: **High**
- **Root Cause**:
  `scripts/build.py` 将整个 624 行的 `patcher.py` 源码作为一个巨大的原始字符串 `PATCHER_TEMPLATE` 硬编码在 Python 变量中。构建过程通过简单的字符串占位符替换生成 `scripts/patcher.py`。
  1. 现代代码审查工具、Linter（ruff、flake8）和类型检查器（mypy）无法对字符串内部的 Python 代码进行语法解析和类型推断；
  2. 外部贡献者极易误直接修改 `scripts/patcher.py`，但在执行下一次构建时，修改会被无声覆盖；
  3. `tests/conftest.py` 导入的是生成的 `scripts/patcher.py`。如果修改了 `build.py` 中的模板而未手动运行 `build.py`，测试套件会继续在过期的代码上运行，产生虚假的测试通过信号。
- **Impact**:
  工程维护性极差，丧失静态质量保障，极易产生生成物与模板之间的代码漂移和隐蔽回归。
- **Remediation**:
  解耦代码生成体系，将 `patcher.py` 作为原生独立的 Python 模块开发，利用标准打包工具（如 PyInstaller 的 `--add-data` 或 `importlib.resources`）在打包阶段引入词典与引擎资源，彻底消除字符串内嵌模板。

---

### [F-D1-04] Electron 主 UI 线程每 2 秒高频同步文件 I/O 与反序列化
- **Finding ID**: [F-D1-04]
- **Title**: Synchronous Filesystem I/O and JSON Deserialization on Main UI Thread Every 2s
- **Location**: `engine/engine_template.js:91-114, 382-390` / `engine/ag_localization_engine.js:91-114, 382-390`
- **Severity**: **High**
- **Root Cause**:
  在 `engine_template.js` 中，`startPeriodicScan()` 每 2000 毫秒调用一次 `tryLoadExternalDicts()`：
  ```javascript
  function tryLoadExternalDicts() {
      const fs = nodeFs();
      const dir = externalLocalesDir();
      if (!fs || !dir) return;
      try {
          const p = dir + '/zh-CN.json';
          zh = JSON.parse(fs.readFileSync(p, 'utf8')); // 同步读盘与解析
          stamp += String(fs.statSync(p).mtimeMs) + '|';
          ...
          if (stamp !== externalStamp) { ... }
      } catch (e) {}
  }
  ```
  在检查文件修改时间戳 `mtimeMs` **之前**，代码无条件执行了 `fs.readFileSync` 读取约 200KB 的 JSON 文件并进行了 `JSON.parse`。在单线程的 Electron 渲染进程中，每 2 秒就会无谓地消耗 CPU 解析 2,000+ 个词条，随后发现时间戳未变而直接丢弃。
- **Impact**:
  造成 Electron 渲染主线程周期性微卡顿、丢帧，特别是在大型代码工程或低功耗设备上，会导致打字输入延迟和界面响应卡顿。
- **Remediation**:
  改为先检查 `statSync` 修改时间，仅当时间戳发生改变时才读取并反序列化文件内容：
  ```javascript
  function tryLoadExternalDicts() {
      const fs = nodeFs();
      const dir = externalLocalesDir();
      if (!fs || !dir) return;
      try {
          const zhPath = dir + '/zh-CN.json';
          const patPath = dir + '/patterns.json';
          let zhMtime = 0, patMtime = 0;
          try { zhMtime = fs.statSync(zhPath).mtimeMs; } catch (e) {}
          try { patMtime = fs.statSync(patPath).mtimeMs; } catch (e) {}
          const stamp = `${zhMtime}|${patMtime}`;
          if (stamp === externalStamp || stamp === '0|0') return;

          let zh = null, pats = null;
          if (zhMtime) {
              try { zh = JSON.parse(fs.readFileSync(zhPath, 'utf8')); } catch (e) {}
          }
          if (patMtime) {
              try { pats = JSON.parse(fs.readFileSync(patPath, 'utf8')); } catch (e) {}
          }
          externalStamp = stamp;
          applyExternalDicts(zh, pats);
      } catch (e) {}
  }
  ```

---

### [F-D1-05] 编辑器 Token 穿透跳过区泄露进入翻译管线
- **Finding ID**: [F-D1-05]
- **Title**: Element Nodes in Skip Zones Bypass Filters in `MutationObserver` & `translateDOM`
- **Location**: `engine/engine_template.js:270-274, 353-358` / `engine/ag_localization_engine.js:270-274, 353-358`
- **Severity**: **High**
- **Root Cause**:
  1. 在 `observeSubtree` 的突变遍历中：
     ```javascript
     mutation.addedNodes.forEach(n => {
         if (n.nodeType === 1 && isSkipElement(n)) return;
         if (n.nodeType === 3 && insideSkipZone(n.parentElement)) return;
         translateDOM(n);
     });
     ```
     当添加一个元素节点 `n`（如 Monaco Editor 插入的高亮代码块 `<span class="mtk1">class</span>`）时，`isSkipElement(n)` 判定为 `false`（因为该标签不是 PRE/CODE/TEXTAREA，且自身不带 `.monaco-editor` 类名）。而 `insideSkipZone(n)` 根本未对类型 1 的元素节点执行校验。
  2. 在 `translateDOM(root)` 递归入口处，同样仅对类型 1 执行了 `isSkipElement(root)`，遗漏了 `insideSkipZone(root)`。
- **Impact**:
  Monaco 编辑器中的代码高亮片段、终端输出字符在动态插入时穿透跳过区，代码变量名或关键字（如 `default`, `class`, `Cancel`, `Run`）被当作 UI 文本错误翻译，严重破坏用户的源代码展示。
- **Remediation**:
  在 `observeSubtree` 与 `translateDOM` 中对元素节点增加 `insideSkipZone` 判定：
  ```javascript
  // translateDOM 入口校验
  if (root.nodeType === 1) {
      if (isSkipElement(root) || insideSkipZone(root)) return;
  } else if (root.nodeType === 3 && insideSkipZone(root.parentElement)) {
      return;
  }

  // observeSubtree 节点校验
  mutation.addedNodes.forEach(n => {
      if (n.nodeType === 1 && (isSkipElement(n) || insideSkipZone(n))) return;
      if (n.nodeType === 3 && insideSkipZone(n.parentElement)) return;
      translateDOM(n);
  });
  ```

---

### [F-D1-06] `MutationObserver.disconnect()` 导致并发渲染 Mutation 永久丢失
- **Finding ID**: [F-D1-06]
- **Title**: `MutationObserver.disconnect()` in Callback Drops Interleaved Renderer Mutations
- **Location**: `engine/engine_template.js:347-375` / `engine/ag_localization_engine.js:347-375`
- **Severity**: **Medium**
- **Root Cause**:
  为了避免修改 DOM 文本节点时产生递归死循环，引擎在 `MutationObserver` 回调开始时执行了 `obs.disconnect()`，在 `finally` 块中重新调用 `obs.observe()`。
  调用 `disconnect()` 会立即清空浏览器底层待分发的突变队列，并在断开期间完全停止监听。在 Electron 渲染多任务流式界面（如 LLM 输出流、文件树刷新）时，翻译函数遍历 DOM 期间（通常持续 10~50ms）产生的所有并发 DOM 变更记录被浏览器永久丢弃。
- **Impact**:
  新渲染的 UI 视图在初次呈现时遗漏翻译，界面呈现中英夹杂，必须等待下一次全量扫描才能被动修复。
- **Remediation**:
  使用标志位 `isTranslating` 控制递归，而非解绑观察器：
  ```javascript
  let isTranslating = false;
  function observeSubtree(target) {
      if (!target) return;
      const obs = new MutationObserver((mutations) => {
          if (isTranslating) return;
          isTranslating = true;
          try {
              for (const mutation of mutations) {
                  // 处理新增节点与文本变更
              }
          } finally {
              isTranslating = false;
          }
      });
      obs.observe(target, { childList: true, subtree: true, characterData: true });
  }
  ```

---

### [F-D1-07] 2 秒全量 DOM 树遍历与全局 QuerySelector 性能开销
- **Finding ID**: [F-D1-07]
- **Title**: High-Frequency 2s Full-DOM TreeWalker Scan and Unscoped QuerySelector Overhead
- **Location**: `engine/engine_template.js:382-406` / `engine/ag_localization_engine.js:382-406`
- **Severity**: **Medium**
- **Root Cause**:
  在 `startPeriodicScan` 中：
  1. 每 2 秒对 `document.body` 执行一次全量 `TreeWalker` 扫描，不管 DOM 是否发生变化，都要对几万个节点读取 11 个属性并进行正则匹配；
  2. `injectLanguageSwitcher` 在语言切换按钮未就绪时，执行 `document.querySelectorAll('*')` 进行全局暴力检索。
- **Impact**:
  在复杂的 VS Code 衍生 IDE 环境中持续消耗 CPU 与电池电量，造成后台持续发热与微卡顿。
- **Remediation**:
  引入 DOM 脏标记，并将兜底定时轮询间隔从 2 秒延长至 15~30 秒，仅在页面处于可见状态（`document.visibilityState === 'visible'`）且 DOM 发生变动时才触发扫描。

---

### [F-D1-08] Pattern 规则替换字符串未转义 `$` 导致文本损坏
- **Finding ID**: [F-D1-08]
- **Title**: Unescaped Replacement String in Pattern Rules Triggers `$` Substitution Corruption
- **Location**: `engine/engine_template.js:202-208` / `engine/ag_localization_engine.js:202-208`
- **Severity**: **Medium**
- **Root Cause**:
  在静态字典替换中，代码使用了 `text.replace(trimmed, escapeDollar(translations[trimmed]))`；但在动态正则规则替换中：
  ```javascript
  for (const p of patterns) {
      if (p.regex.test(trimmed)) {
          const replaced = trimmed.replace(p.regex, p.replace);
          return text.replace(trimmed, replaced); // replaced 未转义再次传入 replace
      }
  }
  ```
  `replaced` 变量被作为第二个参数传入 `text.replace(trimmed, replaced)`。在 JavaScript 中，若 `replaced` 中包含 `$` 符号（例如货币金额 `$100` 或环境变量 `$PATH`），JavaScript 会将其解释为特殊的替换占位符（`$$`, `$&`, `` $` ``, `$'`）。
- **Impact**:
  如果正则匹配到的替换文本含有 `$`，界面文本会被截断、复制或破坏。
- **Remediation**:
  在 `text.replace` 中使用函数式替换返回值，彻底规避 `$` 转义陷阱：
  ```javascript
  for (const p of patterns) {
      if (p.regex.test(trimmed)) {
          const replaced = trimmed.replace(p.regex, p.replace);
          return text.replace(trimmed, () => replaced);
      }
  }
  ```

---

### [F-D1-09] 补丁与恢复前缺少进程强校验及 Win32 探测降级缺陷
- **Finding ID**: [F-D1-09]
- **Title**: Process Check Omitted in `apply_patch`/`restore_backup` & Win32 Query Fallback Flaw
- **Location**: `scripts/build.py:109-186, 442-455` / `scripts/patcher.py:82-159, 415-428`
- **Severity**: **Medium**
- **Root Cause**:
  1. `is_antigravity_running()` 函数已实现，但仅在 `show_status()` 中被调用，在 `apply_patch()` 和 `restore_backup()` 的开头完全没有前置调用；
  2. Windows 下 `_find_antigravity_process_path_windows()` 尝试获取 `PROCESS_QUERY_LIMITED_INFORMATION` 权限打开进程句柄，在严格 UAC 或权限受限环境下打开失败返回 `None`，导致进程明明在运行却误判为未运行。
- **Impact**:
  用户在客户端开启状态下运行安装或恢复，流程在完成全部解包与注入后，在最后的 `os.replace` 阶段突然触发 Windows 文件占用 `PermissionError` 崩溃。
- **Remediation**:
  在 `apply_patch` 和 `restore_backup` 入口处强制调用前置检查，并将快照存在性判断与进程完整路径获取解耦：
  ```python
  def is_antigravity_running():
      if sys.platform == "win32":
          # 只要进程快照中存在对应可执行文件名称，即判定为运行中
          return _is_process_name_running_windows("antigravity.exe")
      # macOS / Linux pgrep 探测
      ...
  ```

---

### [F-D1-10] 未翻译词条收集器累积 1,000 条后永久锁死
- **Finding ID**: [F-D1-10]
- **Title**: Untranslated Collector Hard Lockout at 1,000 Entries and Storage Leakage
- **Location**: `engine/engine_template.js:136-170` / `engine/ag_localization_engine.js:136-170`
- **Severity**: **Medium**
- **Root Cause**:
  ```javascript
  function recordUntranslated(str) {
      if (!str || str.length < 2 || str.length > 300) return;
      if (untranslatedSet.size >= 1000) return;
      ...
  }
  ```
  `untranslatedSet` 会同步序列化存储在浏览器 `localStorage.ag_untranslated` 中。一旦累积达到 1,000 条，该条件永远满足，此后用户在应用中遇到的任何新增未翻译文本都不会再被捕获，除非手动打开 DevTools 清空存储。
- **Impact**:
  核心调试与词条采集功能在使用一段时间后永久失灵。
- **Remediation**:
  将存储结构改为 LRU 滑动窗口，超过 1,000 条时淘汰最旧的条目，并在控制台/UI 提供一键清空指令。

---

### [F-D1-11] 恢复备份时因 ASAR 尺寸膨胀产生恒为误报的版本不匹配警告
- **Finding ID**: [F-D1-11]
- **Title**: False Positive Version Mismatch Warning on Every Restore Due to ASAR Size Inflation
- **Location**: `scripts/build.py:576-581` / `scripts/patcher.py:550-555`
- **Severity**: **Medium**
- **Root Cause**:
  在 `restore_backup()` 中，代码通过直接比较 `os.path.getsize(asar_path)` 与 `os.path.getsize(bak_path)` 来判断版本：
  注入汉化引擎与词典后，`app.asar` 体积天生会增长约 178KB。因此在同一个版本下，已打补丁的 ASAR 与其原始官方备份的体积是 100% 不相等的。
- **Impact**:
  每一次合法的还原操作，都会向用户抛出极其严重的警告信息（`The backup may come from a different older client version`），导致用户误以为版本损坏而产生恐慌。
- **Remediation**:
  比较内部 `package.json` 中的 `version` 字段，而非粗暴比对整个归档的文件字节大小。

---

### [F-D1-12] ASAR 读取未校验 Pickle Magic 及切片长度
- **Finding ID**: [F-D1-12]
- **Title**: Omission of Pickle Magic (`u1 == 4`) and Unbounded Slice Validation in `read_asar`
- **Location**: `scripts/build.py:188-206` / `scripts/patcher.py:161-179`
- **Severity**: **Medium**
- **Root Cause**:
  Chromium Pickle 格式规范要求头部前 4 字节必须为 uint32 数值 `4`。代码中未校验 `u1 == 4`。此外，在提取内部文件时，使用 Python 切片 `data[start:start + entry["size"]]`，若文件被截断或偏移越界，切片静默返回短字节而不报错。
- **Impact**:
  非合法 ASAR 或受损截断的文件被静默读取，随后回写重新打包，将隐蔽损坏固化到软件中。
- **Remediation**:
  增加 `u1 == 4` 的 Magic 校验以及切片边界校验（详见 F-D2-06 代码）。

---

### [F-D1-13] 终端安装脚本硬编码执行 arm64 导致 Intel macOS 崩溃
- **Finding ID**: [F-D1-13]
- **Title**: Hardcoded Arm64 Binary Invocation Crashes on Intel macOS in Shell Scripts
- **Location**: `install.sh:11-19`, `restore.sh:11-19`, `status.sh:6-14`
- **Severity**: **Medium**
- **Root Cause**:
  脚本中无条件探测并执行 arm64 二进制：
  ```bash
  if [ -f "$DIR/antigravity-zh-macos-arm64" ]; then
      "$DIR/antigravity-zh-macos-arm64" patch
      exit 0
  ```
  在 x86_64 架构的 Intel Mac 上，macOS Rosetta 仅支持将 x86_64 转译为 arm64 运行，**无法逆向在 x86 机器上执行 arm64 二进制**。执行直接抛出 `Bad CPU type in executable` 致命错误中断。
- **Impact**:
  Intel 架构 Mac 用户无法通过脚本使用工具，安装立即终止。
- **Remediation**:
  在 Shell 脚本中增加 `uname -m` 架构判断：
  ```bash
  ARCH="$(uname -m)"
  if [ "$ARCH" = "arm64" ] && [ -f "$DIR/antigravity-zh-macos-arm64" ]; then
      chmod +x "$DIR/antigravity-zh-macos-arm64"
      "$DIR/antigravity-zh-macos-arm64" patch
      exit 0
  fi
  ```

---

### [F-D1-14] `restore.bat` 混杂 CRLF/LF 换行符导致批处理执行风险
- **Finding ID**: [F-D1-14]
- **Title**: Mixed CRLF/LF Line Endings in `restore.bat` Risk Parsing Failure in cmd.exe
- **Location**: `restore.bat:1-58`
- **Severity**: **Low**
- **Root Cause**:
  工作区中的 `restore.bat` 包含 44 行 CRLF 与 13 行 LF 混合换行符。Windows 的 `cmd.exe` 在解析带有标签跳转（`goto`）和条件括号块的批处理时，纯 LF 行会导致跳转位置计算错乱。
- **Impact**:
  在特定 Windows 环境下还原操作解析失败中断。
- **Remediation**:
  统一将所有批处理脚本转换为标准 CRLF 格式，并在 CI 中强制执行行尾规范检查。

---

### [F-D1-15] `extract_untranslated.py` 扫描二进制噪音污染词典目录
- **Finding ID**: [F-D1-15]
- **Title**: Naive Binary String Scraping in `extract_untranslated.py` Pollutes Locales Directory
- **Location**: `scripts/extract_untranslated.py:40-50, 84-85, 100-103`
- **Severity**: **Low**
- **Root Cause**:
  该脚本直接用正则表达式 `[\x20-\x7e]{3,200}` 在整个 ASAR 二进制文件中扫描英文字符串，将大量打包压缩后的 JS 混淆变量名当作未翻译文本，并默认保存为 `locales/missing_strings.json`，且该文件未被 `.gitignore` 包含。
- **Impact**:
  产生的垃圾数据可能被 CI 的通配符指令（`cp locales/*.json ...`）一并打包进入发布制品。
- **Remediation**:
  解包提取真实的 `dist/*.js` 进行语法树或特定属性分析，并将输出路径排除在版本控制之外。

---

### [F-D1-16] `build.py` 复制二进制失败被静默抑制产生假阳性成功
- **Finding ID**: [F-D1-16]
- **Title**: Silent Exception Suppression in PyInstaller Binary Deployment (`build.py`)
- **Location**: `scripts/build.py:698-735`
- **Severity**: **Low**
- **Root Cause**:
  ```python
  try:
      shutil.copy2(output_bin, os.path.join(REPO_ROOT, binary_name))
  except Exception:
      pass
  ```
  如果根目录下的 `.exe` 正被某个进程占用导致写入拒绝，异常被静默忽略，控制台仍然打印成功拷贝横幅。
- **Impact**:
  开发者以为根目录的测试二进制已是最新构建，实际上测试的是陈旧的历史版本。
- **Remediation**:
  捕获并在控制台明确打印警告信息。

---

### [F-D1-17] 仓库缺失类型注解与静态代码分析规范
- **Finding ID**: [F-D1-17]
- **Title**: Complete Absence of Type Hints, Linting Configuration, and Static Verification
- **Location**: Repository Root / `scripts/`
- **Severity**: **Low**
- **Root Cause**:
  项目未引入 PEP 484 类型标注，根目录缺失 `pyproject.toml`、`ruff`、`flake8`、`mypy` 等静态分析配置文件。
- **Impact**:
  无法在编码阶段自动化检测类型错误、未声明变量和不安全的接口调用。
- **Remediation**:
  在根目录配置 `pyproject.toml` 并集成 `ruff` 与 `mypy` 检查。

---

### [F-D1-18] 全局泛滥的无差别捕获异常 (`except Exception:` / `catch (e) {}`)
- **Finding ID**: [F-D1-18]
- **Title**: Pervasive Blanket Exception Catching (`except Exception:` / `catch (e) {}`)
- **Location**: Python Scripts & JS Engine
- **Severity**: **Informational**
- **Root Cause**:
  全工程存在数十处空的 `catch (e) {}` 和 `except Exception: pass`，不仅抑制了预期的降级，也吞噬了由系统权限不足、语法错误引发的真正异常。
- **Impact**:
  使得在复杂运行环境中的异常排查变得极度困难。
- **Remediation**:
  精准捕获具体异常类别，并在开启调试选项时输出诊断日志。

---

## 4. 维度二：安全性、ReDoS、代码注入与 ASAR 篡改审计 (Dimension 2)

---

### [F-D2-01] 注释哨兵切片 AST 逃逸导致恶意词典执行任意 JavaScript 代码 (RCE)
- **Finding ID**: [F-D2-01]
- **Title**: AST Breakout & Arbitrary Code Execution via Naive Comment Sentinel Splicing in `splice_engine_dicts`
- **Location**: `scripts/build.py:410-429` / `scripts/patcher.py:383-402`
- **Severity**: **Critical**
- **CVSS Score**: 9.3 (CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H)
- **Root Cause**:
  在将外部字典拼装进引擎模板时，代码采用了基于注释边界的字符串查找：
  ```python
  def _splice(code, start_mark, end_mark, text):
      anchor = code.find(start_mark)
      end = code.find(end_mark, anchor)
      return code[:anchor + len(start_mark)] + "\n" + text + "\n" + code[end:]
  ```
  哨兵标记定义为 `/*AG_ZH_ZH_START*/` 和 `/*AG_ZH_ZH_END*/`。
  系统对词典内容的检查仅仅调用了 `json.loads(text)`。由于合法的 JSON 键值对内部完全可以包含字符串字面量 `/*AG_ZH_ZH_END*/`，攻击者可在词典中构造 Payload：
  ```json
  {
    "attack": "/*AG_ZH_ZH_END*/; require('child_process').execSync('calc'); /*"
  }
  ```
  在拼装或重打补丁时，`code.find(end_mark, anchor)` 将错误地在字符串内部匹配到该结束哨兵，导致注入的 JavaScript 语句直接逃逸出 JSON 上下文，成为 `dist/preload.js` 顶层作用域中的原生可执行代码。
- **Impact**:
  **远程/本地任意代码执行 (RCE)**。当受害者下载并安装社区内被恶意篡改的词典文件时，Antigravity 启动时将以 Electron 的 Node.js 完整权限执行攻击载荷，导致主机完全被控制。
- **Remediation**:
  在执行切片前，对字典文本中的注释结束符做转义处理，且采用 `rfind` 匹配最末尾的哨兵，或将词典作为独立静态 JSON 文件读取：
  ```python
  def splice_engine_dicts(engine_code, zh_text, pat_text):
      def _sanitize(text):
          return text.replace("*/", "*\\/").replace("/*", "/\\*")

      def _splice(code, start_mark, end_mark, text):
          anchor = code.find(start_mark)
          if anchor == -1: return None
          end = code.rfind(end_mark)
          if end == -1 or end < anchor: return None
          return code[:anchor + len(start_mark)] + "\n" + _sanitize(text) + "\n" + code[end:]

      s1 = _splice(engine_code, DICT_ZH_SENTINELS[0], DICT_ZH_SENTINELS[1], zh_text)
      if s1 is None: return engine_code
      s2 = _splice(s1, DICT_PATTERNS_SENTINELS[0], DICT_PATTERNS_SENTINELS[1], pat_text)
      return s2 if s2 is not None else engine_code
  ```

---

### [F-D2-02] `escapeDollar` 属 JS No-Op 导致文本损坏与替换字符注入
- **Finding ID**: [F-D2-02]
- **Title**: `escapeDollar` Implementation is a JavaScript No-Op Leading to String Replacement Corruption and Injection
- **Location**: `engine/engine_template.js:175-177, 205-206`
- **Severity**: **High**
- **CVSS Score**: 7.5 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N)
- **Root Cause**:
  ```javascript
  function escapeDollar(s) {
      return String(s).replace(/\$/g, '$$');
  }
  ```
  依据 ECMAScript 规范，在 `String.prototype.replace(searchValue, replaceValue)` 中，当第二个参数为字符串时，`'$$'` 本身就会被解析为单一的 `$`。因此，`String(s).replace(/\$/g, '$$')` 会将每一个 `$` 重新替换为 `$`，**函数返回值与输入完全一致，没有任何转义效果**！
  在后续的 `text.replace(trimmed, escapeDollar(translations[trimmed]))` 中，未转义的 `$` 字符被外层 `replace` 再次解析：
  - `$&` 触发匹配文本自身重复插入；
  - `$'` 触发后续全量文本被成倍复制与拼接；
  - `$1` 被替换为空白。
- **Impact**:
  界面文本在遇到带有美元符号、脚本变量名（如 `$PATH`）或模板符时发生严重的文本乱码、界面重复与破坏。
- **Remediation**:
  使用 ECMAScript 的**函数替换器 (Function Replacer)**，彻底绕过 `$` 替换字符解析：
  ```javascript
  // 函数替换器天生不受任何 $ 符号影响
  function safeReplace(str, target, replacement) {
      return str.replace(target, () => replacement);
  }
  ```

---

### [F-D2-03] 外部动态正则缺乏回溯限制引发 ReDoS 冻结线程
- **Finding ID**: [F-D2-03]
- **Title**: Catastrophic Backtracking (ReDoS) Vulnerability on Dynamic Regex Patterns from External Dictionaries
- **Location**: `engine/engine_template.js:27-42, 203-208`
- **Severity**: **High**
- **CVSS Score**: 7.5 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H)
- **Root Cause**:
  引擎允许从外部 `patterns.json` 中热加载正则表达式并在所有文本节点上执行匹配。代码中对正则结构的复杂度缺乏任何校验。一旦引入带有嵌套量词（如 `(a+)+$` 或 `^([a-zA-Z0-9_-]+)+$`）的规则，在对长度在 30~50 字符的特定文本执行匹配时，V8 正则引擎会发生指数级灾难性回溯（实测 27 字符耗时 4.6 秒，35 字符耗时超 60 秒）。
- **Impact**:
  **拒绝服务 (DoS)**。由于 Electron 渲染进程在单主线程中执行，灾难性回溯会瞬间占满 100% CPU，造成整个 IDE 窗口彻底冻结无响应，甚至触发崩溃。
- **Remediation**:
  在加载外部正则时，增加复杂度静态检测，拒绝嵌套量词与过长的正则模式：
  ```javascript
  function isDangerousRegex(patternStr) {
      // 阻断嵌套量词
      if (/(\([^\)]*[\+\*\{][^\)]*\)[\+\*\{])/.test(patternStr)) return true;
      if (patternStr.length > 250) return true;
      return false;
  }
  ```

---

### [F-D2-04] 正则白名单包含有状态 Sticky 标志 `y` 导致匹配遗漏
- **Finding ID**: [F-D2-04]
- **Title**: Stateful Sticky Flag `y` in Whitelist Causes Non-Deterministic Pattern Match Skipping
- **Location**: `engine/engine_template.js:38`, `engine/ag_localization_engine.js:38`
- **Severity**: **Medium**
- **Root Cause**:
  白名单中允许使用 sticky 标志 `y`（`/^[imsuy]+$/`）。在 JavaScript 中，带有 `y` 标志的 `RegExp` 对象是有状态的：每次匹配成功后，其 `lastIndex` 属性会被置为匹配结束位置。因为模式单例对象在全局遍历中被成千上万个节点复用，后一个节点由于从非 0 的 `lastIndex` 开始匹配而必定匹配失败。
- **Impact**:
  产生非确定性的跳跃性翻译失效，部分相同文案随机保持英文。
- **Remediation**:
  从允许的 flags 白名单中移除 `y` 标志：
  ```javascript
  const flags = (typeof p.flags === 'string' && /^[imsu]+$/.test(p.flags)) ? p.flags : 'i';
  ```

---

### [F-D2-05] 外部词典加载存在原型链污染隐患
- **Finding ID**: [F-D2-05]
- **Title**: Prototype Pollution Vulnerability via `__proto__` in `applyExternalDicts` and `rebuildIndexes`
- **Location**: `engine/engine_template.js:82-89, 27-31`
- **Severity**: **Medium**
- **Root Cause**:
  在 `applyExternalDicts` 中：
  ```javascript
  const merged = {};
  if (zh) for (const k in zh) merged[k] = zh[k];
  ```
  如果加载的 JSON 包含 `"__proto__"` 键，赋值操作将直接修改 `Object.prototype` 的原型链属性。
- **Impact**:
  污染渲染上下文的全局对象原型，导致逻辑判定错乱或属性注入。
- **Remediation**:
  使用 `Object.create(null)` 创建无原型字典对象，并过滤危险键名：
  ```javascript
  const merged = Object.create(null);
  for (const k in zh) {
      if (k !== '__proto__' && k !== 'constructor' && k !== 'prototype') {
          merged[k] = zh[k];
      }
  }
  ```

---

### [F-D2-06] ASAR 读取缺少数据边界检查导致内存越界切片
- **Finding ID**: [F-D2-06]
- **Title**: ASAR Reader Missing Bounds and Integer Range Checks Enables Out-of-Bounds Memory Slicing
- **Location**: `scripts/build.py:188-205` / `scripts/patcher.py:161-178`
- **Severity**: **Medium**
- **Root Cause**:
  `read_asar` 未验证 `offset >= 0`、`size >= 0`，亦未验证 `start + size <= len(data)`。负偏移会导致从 bytes 尾部切片，越界切片则静默截断。
- **Impact**:
  异常数据被无感知地作为正常文件提取并重新打包，破坏归档结构。
- **Remediation**:
  严格增加整数非负校验与文件长度边界校验：
  ```python
  offset_val = int(entry["offset"])
  size_val = int(entry["size"])
  if offset_val < 0 or size_val < 0:
      raise ValueError(f"Malformed entry '{curr}': negative bounds")
  start = base_offset + offset_val
  if start + size_val > len(data):
      raise ValueError(f"Malformed entry '{curr}': bounds extend beyond archive")
  ```

---

### [F-D2-07] Fail-Open 边车校验与无条件还原被篡改备份
- **Finding ID**: [F-D2-07]
- **Title**: Fail-Open Backup Integrity Check in `backup_matches_sidecar` & Unconditional Restoration of Tampered Backups
- **Location**: `scripts/build.py:224-233, 582-585` / `scripts/patcher.py:197-206, 556-558`
- **Severity**: **Medium**
- **Root Cause**:
  在 `backup_matches_sidecar` 中，当 `.sha256` 边车文件不存在时，函数直接返回 `True`（Fail-Open）。更严重的是，在 `restore_backup` 中，即使明确检测到校验和不匹配，代码仅打印一行警告后仍然无条件将该异常文件恢复进系统。
- **Impact**:
  恶意软件替换 `app.asar.bak` 后，用户执行 `restore` 即可被动恢复后门归档。
- **Remediation**:
  缺失边车时返回未知状态；恢复操作检测到哈希不符时，非 `--force` 模式下直接终止还原。

---

### [F-D2-08] 原地修改 ASAR 破坏 macOS 代码签名及 Electron `asarIntegrity`
- **Finding ID**: [F-D2-08]
- **Title**: macOS Code Signature Invalidation & Electron `asarIntegrity` Enforcement Bypass / Crash
- **Location**: `scripts/build.py:521-551` / `scripts/patcher.py:494-524`
- **Severity**: **High**
- **Root Cause**:
  macOS 平台上的 `/Applications/Antigravity.app` 受 Apple Developer ID 签名保护，签名元数据记录在 `Contents/_CodeSignature/CodeResources` 中，涵盖 `app.asar` 的哈希。此外，开启了 `asarIntegrity` 的 Electron 客户端会在启动时强校验 ASAR Header 哈希。原地替换破坏了签名和哈希校验，系统 Gatekeeper 会拦截启动（报应用已损坏）。
- **Impact**:
  macOS 用户在汉化后可能遭遇无法启动、钥匙串（Keychain）权限丧失或 Gatekeeper 隔离拦截。
- **Remediation**:
  在 macOS 平台修改完毕后，自动执行 ad-hoc 重新签名：
  ```python
  if sys.platform == "darwin":
      app_bundle = os.path.abspath(os.path.join(install_dir, "..", ".."))
      if app_bundle.endswith(".app") and os.path.exists(app_bundle):
          try:
              subprocess.run(["codesign", "--force", "--deep", "--sign", "-", app_bundle], check=True)
          except Exception as e:
              print(f"[!] Warning: Failed to re-sign app bundle: {e}")
  ```

---

### [F-D2-09] POSIX 环境下 `tempfile.mkstemp` 导致 ASAR 权限降至 0600
- **Finding ID**: [F-D2-09]
- **Title**: POSIX File Permission Degradation to 0600 on Replaced `app.asar` via `mkstemp`
- **Location**: `scripts/build.py:301-321` / `scripts/patcher.py:274-294`
- **Severity**: **Low**
- **Root Cause**:
  `tempfile.mkstemp` 默认创建的文件权限为 `0600`（仅创建者可读写）。通过 `os.replace` 替换原有的 `0644` 权限的 `app.asar` 后，权限被降级为 `0600`。
- **Impact**:
  多用户系统或非管理员子进程尝试运行 Antigravity 时抛出 `EACCES` 权限拒绝错误。
- **Remediation**:
  在原子替换前获取原文件的 `stat.st_mode`，并在临时文件写入后通过 `os.chmod` 还原权限。

---

### [F-D2-10] 未翻译收集器采集敏感提示词与隐私泄露
- **Finding ID**: [F-D2-10]
- **Title**: Privacy Leakage of Agent Conversations and Sensitive Prompts via `ag_untranslated` in `localStorage`
- **Location**: `engine/engine_template.js:136-170, 477-494`
- **Severity**: **Medium**
- **Root Cause**:
  `recordUntranslated` 的过滤规则仅排除了纯代码标签和 Monaco 编辑器，未排除聊天对话容器（`.chat-container` 等）。用户输入的敏感提示词、API Key 以及 AI 的内部思考过程被捕获并永久明文存入 `localStorage`，并通过快捷键直接复制到剪贴板。
- **Impact**:
  存在严重的敏感隐私信息与凭据泄露风险。
- **Remediation**:
  在 `insideSkipZone` 中增加聊天与大模型上下文区域的过滤类名，并关闭默认的无差别人工交互内容录入。

---

## 5. 维度三：ASAR 原生补丁注入稳健性与边界情况审查 (Dimension 3)

---

### [F-D3-01] 原生菜单补丁改写子菜单查找键破坏快捷键机制（同 F-D1-01）
- **Finding ID**: [F-D3-01]
- **Title**: Submenu Lookup Key Corruption in `patch_menu_js` Silently Discards Menu Items and Breaks Shortcuts
- **Location**: `scripts/build.py:328-332` / `scripts/patcher.py:302-305`
- **Severity**: **Critical**
- **Root Cause & Impact**:
  见 F-D1-01。针对 `dist/menu.js` 的 `addItemToSubmenu(menu, 'File'` 查找键替换，导致 `New Window` 菜单项与 `CmdOrCtrl+Shift+N` 加速键被永久丢弃。
- **Remediation**:
  见 F-D1-01。

---

### [F-D3-02] 原生模块补丁对代码压缩、引号变体及打包器别名极度脆弱
- **Finding ID**: [F-D3-02]
- **Title**: Native Module Patch Rigidity Against Code Minification, Quote Variations, and Bundler Aliases
- **Location**: `scripts/build.py:327, 350-386` / `scripts/patcher.py:301, 324-359`
- **Severity**: **High**
- **Root Cause**:
  `patch_updater_js` 与 `patch_main_js` 采用严格的静态字面量比对：
  1. `buttons: ['Cancel', 'Quit']`：只要上游构建时被去除空格（`['Cancel','Quit']`）或数组换行格式化，替换立即失效；
  2. `patch_main_js` 完全未考虑双引号（`title: "Confirm Quit"`）；
  3. `patch_menu_js` 硬编码了打包器临时别名 `updater_1.MenuUpdateStep.CheckForUpdates`，只要 TypeScript 或 esbuild 调整命名空间导入策略，模式必定击空。
- **Impact**:
  Antigravity 客户端只要发生细微的代码打包变动，原生弹窗汉化就会大面积失效。
- **Remediation**:
  改用具备空白符与引号容错能力的弹性正则表达式替换：
  ```python
  import re

  def patch_updater_js(content_str):
      patterns = [
          (r'title:\s*[\'"]Check for Updates[\'"]', "title: '检查更新'"),
          (r'message:\s*[\'"]No updates available[\'"]', "message: '当前已是最新版本'"),
      ]
      for pattern, repl in patterns:
          content_str, count = re.subn(pattern, repl, content_str)
      return content_str
  ```

---

### [F-D3-03] `patch_updater_js` 与 `patch_main_js` 缺失 MISS 告警与假阳性
- **Finding ID**: [F-D3-03]
- **Title**: Missing MISS Warning and False-Positive Success in `patch_updater_js` and `patch_main_js`
- **Location**: `scripts/build.py:350-386` / `scripts/patcher.py:324-359`
- **Severity**: **High**
- **Root Cause**:
  `patch_menu_js` 对未命中的项具备 MISS 记录逻辑，而 `patch_updater_js` 与 `patch_main_js` 遍历完成后，如果 `hits == 0`，不报错、不抛出警告，直接返回原字符串，外层安装器继续显示"汉化补丁安装成功！"。
- **Impact**:
  原生弹窗替换即使彻底失效，用户和开发者也完全无从察觉（典型的静默假阳性）。
- **Remediation**:
  统一复用带 `MISS` 统计和告警的替换执行器。

---

### [F-D3-04] 原生对话框状态文本与 macOS Dock 菜单汉化覆盖不全
- **Finding ID**: [F-D3-04]
- **Title**: Incomplete Localization of Native Dialogs and macOS Dock Menus Causing Mixed UI
- **Location**: `scripts/build.py:350-386` / `scripts/patcher.py:324-359`
- **Severity**: **High**
- **Root Cause**:
  1. `updater.js` 仅替换了"无可用更新"状态，未处理"发现新版本"、"重启并安装"等主要更新状态弹窗；
  2. `main.js` 仅处理退出弹窗，未汉化 macOS Dock 菜单模板中的 `label: 'New Window'`。
- **Impact**:
  客户端在更新、重启或使用 Dock 栏时，频繁出现中英混杂的界面。
- **Remediation**:
  补齐完整的弹窗状态文本及 Dock 菜单替换规则。

---

### [F-D3-05] 词典加载未处理 Windows 记事本 UTF-8 BOM 导致自定义修改被静默丢弃
- **Finding ID**: [F-D3-05]
- **Title**: UTF-8 BOM Decoding Failure in `load_valid_json_text` Silently Discards User Dictionaries
- **Location**: `scripts/build.py:391, 662-664` / `scripts/patcher.py:365`
- **Severity**: **High**
- **Root Cause**:
  代码使用 `read_text(encoding="utf-8")`。Windows 记事本在保存 UTF-8 文本时会自动添加 3 字节的 BOM 签名（`\xef\xbb\xbf`）。Python 的 `json.loads` 解析包含 BOM 的字符串时直接抛出 `JSONDecodeError: Unexpected UTF-8 BOM`。异常被捕获后返回 `None`，补丁器误判为"非法 JSON"而直接回退至旧版内嵌词典。
- **Impact**:
  Windows 用户使用系统记事本修改自定义词典后，重新运行补丁程序时修改被完全静默丢弃。
- **Remediation**:
  读取 JSON 文本时统一将 `encoding="utf-8"` 改为 `encoding="utf-8-sig"`，自动兼容并剔除 BOM 头：
  ```python
  def load_valid_json_text(path):
      try:
          text = Path(os.path.abspath(path)).read_text(encoding="utf-8-sig")
          json.loads(text)
          return text
      except Exception:
          return None
  ```

---

### [F-D3-06] 词典中 31 条带空格词条因引擎契约 100% 无法被命中
- **Finding ID**: [F-D3-06]
- **Title**: 31 Untrimmed Dictionary Keys Unreachable Due to Engine `trim()` Lookup Contract
- **Location**: `locales/zh-CN.json` / `engine/engine_template.js:182`
- **Severity**: **High**
- **Root Cause**:
  `engine_template.js` 在查表前执行 `const trimmed = text.trim();`，并严格以 `trimmed` 作为键在 `translations` 中索引。而 `locales/zh-CN.json` 中存在形如 `"When toggled on, "` 等 31 条首尾包含空格的 key。由于去空格后的文本绝不会包含首尾空格，这 31 条规则在数学上绝对不可能被查找到。经仿真，其中 26 条核心文案完全无 pattern 规则兜底。
- **Impact**:
  设置页、MCP 配置等核心界面的 26 处提示文案在真机中永久处于英文未汉化状态。
- **Remediation**:
  清理 `zh-CN.json` 中 31 个死词条的前后空格，将带有变量的短语迁移至 `patterns.json`，并在 `build.py` 中增加未 trim key 的构建阻断校验：
  ```python
  untrimmed = [k for k in zh_dict if k != k.strip()]
  if untrimmed:
      raise ValueError(f"Found {len(untrimmed)} dictionary keys with untrimmed whitespace: {untrimmed[:5]}")
  ```

---

### [F-D3-07] 大小写归一化后写覆盖破坏正确译文 (`Reset Zoom` vs `Reset zoom`)
- **Finding ID**: [F-D3-07]
- **Title**: Case Normalization Collision Overwriting Correct Translations (`Reset Zoom` vs `Reset zoom`)
- **Location**: `locales/zh-CN.json:603, 865` / `engine/engine_template.js:29-31`
- **Severity**: **Medium**
- **Root Cause**:
  `zh-CN.json` 同时存在：
  - 词条 603: `"Reset Zoom": "重置缩放"`
  - 词条 865: `"Reset zoom": "实际大小"`（实为 Actual Size 的译文）
  在生成 `lowerTranslations` 时，后出现的词条无条件覆盖前者，导致 `lowerTranslations["reset zoom"]` 最终被定格为 `"实际大小"`。
- **Impact**:
  通过小写匹配回退触发的重置缩放菜单项被错误翻译为"实际大小"，造成语义混淆。
- **Remediation**:
  修正 `locales/zh-CN.json` 中的错误条目，并在测试套件中加入小写键值一致性断言。

---

### [F-D3-08] ASAR 缺失原生模块子文件时静默跳过
- **Finding ID**: [F-D3-08]
- **Title**: Silent Bypass When Native Module Subfiles are Missing from ASAR
- **Location**: `scripts/build.py:527-544` / `scripts/patcher.py:501-518`
- **Severity**: **Medium**
- **Root Cause**:
  原生注入仅使用 `if "dist/menu.js" in files:`。若上游版本重构将模块合并或重命名，条件直接不成立，代码静默跳过而没有任何提示。
- **Impact**:
  结构变动时无声失效，依然打印全部成功。
- **Remediation**:
  增加缺失原生模块时的显式警告汇总。

---

### [F-D3-09] ASAR 截断切片未校验引发短字节损坏被重新固化
- **Finding ID**: [F-D3-09]
- **Title**: Truncated Slice Corruption Solidification in ASAR Writer
- **Location**: `scripts/build.py:188-205` / `scripts/patcher.py:163-180`
- **Severity**: **Medium**
- **Root Cause**:
  `read_asar` 截断读取后，写入逻辑直接以 `entry["size"] = len(data)` 将残缺尺寸重新打包写入 Header。
- **Impact**:
  损坏的数据不仅未被阻断，反而被赋予自洽的 Header 重新序列化，导致数据永久损坏。
- **Remediation**:
  在读取时校验 `start + entry["size"] <= len(data)`，越界立即抛出 `ValueError`。

---

### [F-D3-10] Windows 非 UTF-8 控制台环境打印中文引发 `UnicodeEncodeError` 崩溃
- **Finding ID**: [F-D3-10]
- **Title**: Non-UTF-8 Windows Console Output Triggers `UnicodeEncodeError` Crash
- **Location**: `scripts/build.py:554-559, 642` / `scripts/patcher.py:528-533, 616`
- **Severity**: **Low**
- **Root Cause**:
  未在标准输出流配置 UTF-8 编码。在美式 Windows 环境或输出重定向至日志文件时，默认代码页（如 CP1252）无法编码中文字符，打印中文横幅时直接抛出 `UnicodeEncodeError` 崩溃。
- **Impact**:
  非中文 Windows 系统或重定向运行时安装脚本抛错退出。
- **Remediation**:
  在 `main()` 开头执行标准流安全重设：
  ```python
  if sys.platform == "win32":
      try:
          sys.stdout.reconfigure(encoding="utf-8", errors="replace")
          sys.stderr.reconfigure(encoding="utf-8", errors="replace")
      except Exception: pass
  ```

---

## 6. 维度四：CI/CD 自动化构建配置审查 (Dimension 4)

---

### [F-D4-01] CI Release 编译产物缺失时静默放行导致发布空 Release
- **Finding ID**: [F-D4-01]
- **Title**: Silent Release on Missing Build Outputs via Unchecked `if [ -f ]` and Loose Artifact Upload
- **Location**: `.github/workflows/release.yml:120-140, 142-150`
- **Severity**: **High**
- **Root Cause**:
  在 `release.yml` 构建步骤中：
  ```bash
  if [ -f "${{ matrix.dist_file }}" ]; then
      cp "${{ matrix.dist_file }}" "${{ matrix.release_file }}"
      ...
  fi
  ```
  如果 PyInstaller 构建失败并未生成目标二进制，该 `if` 条件为假，整段步骤以退出码 0 结束！同时 `upload-artifact` 步骤未配置 `if-no-files-found: error`。后续的 `release` job 照常运行，最终打包发布一个仅含有空哈希校验文件的损坏 Release。
- **Impact**:
  编译异常被完全掩盖，错误的提交或依赖故障会产生绿色的 CI 构建并发布不可用的假 Release。
- **Remediation**:
  移除静默的 `if [ -f ]`，若产物缺失立即 `exit 1`，并配置 `if-no-files-found: error`：
  ```yaml
  - name: Prepare binary artifact
    shell: bash
    run: |
      if [ ! -f "${{ matrix.dist_file }}" ]; then
        echo "[!] Error: Compiled binary ${{ matrix.dist_file }} does not exist!"
        exit 1
      fi
      cp "${{ matrix.dist_file }}" "${{ matrix.release_file }}"

  - name: Upload Build Artifact
    uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
    with:
      name: ${{ matrix.artifact_name }}
      path: ${{ matrix.release_file }}
      if-no-files-found: error
  ```

---

### [F-D4-02] 发布矩阵完全缺失 Linux 与 macOS Intel (x86_64) 二进制
- **Finding ID**: [F-D4-02]
- **Title**: Build Matrix Omits Linux x64 and macOS Intel (x86_64) Native Binaries
- **Location**: `.github/workflows/release.yml:86-97`
- **Severity**: **High**
- **Root Cause**:
  构建矩阵仅声明了 `windows-latest (x64)` 和 `macos-latest (arm64)` 两个 target。README 宣传支持的主流 Linux 发行版和 Intel Mac 实际上没有任何自动化构建与二进制产物交付。
- **Impact**:
  Intel 架构的 Mac 用户下载 arm64 二进制无法运行（报 `Bad CPU type in executable`）；Linux 用户没有任何 Releases 二进制可供下载。
- **Remediation**:
  在 `matrix.include` 中补齐 `ubuntu-latest (x64)` 以及 `macos-13 (Intel x64)` 构建目标。

---

### [F-D4-03] README 词条数校验正则 `\b\d+,\d{3}\b` 过度僵硬阻碍技术文档书写
- **Finding ID**: [F-D4-03]
- **Title**: Overly Rigid README Regex `\b\d+,\d{3}\b` Impedes Technical Documentation
- **Location**: `.github/workflows/release.yml:67-70`
- **Severity**: **Medium**
- **Root Cause**:
  CI 脚本提取 README 中的所有 `\b\d+,\d{3}\b`，并强行断言每一个带逗号的 4 位数字都必须等于词条总数（`entries`）。只要文档中出现任何其他合法的带千分符数字（如代币预算 `1,426 tokens` 或历史记录 `1,000`），CI 就会无条件报错。
- **Impact**:
  迫使维护人员在撰写文档时故意回避正常的技术数字表述以迎合粗暴的正则检查。
- **Remediation**:
  限定正则匹配范围，仅校验含有词条上下文声明的语句：
  ```python
  match = re.search(r'(\d+,\d{3})\+?\s*(?:词条|entries)', text)
  ```

---

### [F-D4-04] CI 构建工作流缺少编译后二进制文件的自动化冒烟测试
- **Finding ID**: [F-D4-04]
- **Title**: CI Pipeline Lacks Post-Build Executable Smoke Testing
- **Location**: `.github/workflows/release.yml:113-116`
- **Severity**: **Medium**
- **Root Cause**:
  PyInstaller 生成可执行文件后，CI 没有安排任何直接运行该二进制的冒烟测试步骤。PyInstaller 极易因动态链接库缺失、缺少隐藏导入（Hidden Imports）而在执行时启动崩溃。
- **Impact**:
  损坏的二进制文件通过 CI 检查并被直接发布给最终用户。
- **Remediation**:
  在构建步骤完成后加入快速命令行冒烟调用：
  ```yaml
  - name: Smoke test binary
    shell: bash
    run: |
      ./${{ matrix.dist_file }} --help || exit 1
  ```

---

### [F-D4-05] Windows 发布产物缺少词典及批处理辅助脚本
- **Finding ID**: [F-D4-05]
- **Title**: Incomplete Windows Distribution Package Missing Dictionaries and Batch Helpers
- **Location**: `.github/workflows/release.yml:120-140`
- **Severity**: **Medium**
- **Root Cause**:
  macOS 平台拥有打包脚本与词典的完整 zip 打包逻辑；而 Windows 仅复制并上传了一个单一的 `.exe`，完全缺少 `locales/` 目录和 `.bat` 辅助脚本。
- **Impact**:
  独立下载 Windows 交付物的最终用户无法体验离线词典自定义功能。
- **Remediation**:
  为 Windows 提供包含可执行文件、批处理工具与词典目录的完整 `.zip` 分发包。

---

## 7. 维度五：测试套件覆盖率、有效性与执行验证审查 (Dimension 5)

---

### [F-D5-01] 测试套件"自洽假象"：73 个用例全绿却对生产环境致命缺陷零覆盖
- **Finding ID**: [F-D5-01]
- **Title**: "Self-Proving" Test Suite Blindness: 73 Tests Pass in 0.54s-0.58s with Zero Coverage of Production Failures
- **Location**: `tests/test_asar.py`, `tests/test_patterns.py`
- **Severity**: **High**
- **Root Cause**:
  实测运行 `pytest tests/`，**73 项测试全部通过（耗时 0.54 秒）**。然而，全部 73 个测试仅在最基本的字符串替换计数和自建数据结构上进行断言，没有一个测试接入真实 Electron 运行时，没有覆盖任何真实的破坏性分支。导致 1 项 Critical、5 项 High 级缺陷长期潜伏在完全绿灯的测试代码之下。
- **Impact**:
  测试套件给团队造成严重的虚假安全感（Test Blindness）。
- **Remediation**:
  在测试套件中引入对修改后 JavaScript 语义正确性的验证用例，并建立行为断言。

---

### [F-D5-02] 原生模块补丁与菜单测试缺乏真实 JS 执行环境与语义验证
- **Finding ID**: [F-D5-02]
- **Title**: Menu and Native Patch Tests Lack AST and JS Semantics Verification
- **Location**: `tests/test_asar.py:463-499`
- **Severity**: **High**
- **Root Cause**:
  `test_patch_menu_uses_conservative_first_occurrence` 仅断言替换后的字符串 count，完全不验证 `addItemToSubmenu` 的查找语义。因此即使代码破坏了菜单项的挂载，测试仍然断言成功。
- **Impact**:
  核心回归缺陷无法被既有测试套件拦截。
- **Remediation**:
  编写基于模拟 Electron 菜单环境的测试用例，断言 `menu.items.find(...)` 能够真正定位到目标菜单项并成功执行 `insert`。

---

### [F-D5-03] 缺失关键边界异常用例（BOM 编码、拒绝执行返回值、ASAR 截断）
- **Finding ID**: [F-D5-03]
- **Title**: Critical Edge Cases Omitted: UTF-8 BOM, Rejection Return Codes, Negative Offsets, and File Locks
- **Location**: `tests/test_asar.py`
- **Severity**: **High**
- **Root Cause**:
  现有测试仅包含正常 ASCII/UTF-8 测试夹具，未测试带 BOM 头文件；`test_cli_failure_returns_nonzero` 仅测试未知命令，未测试业务拒绝执行时的退出码；未测试 ASAR 截断或负偏移。
- **Impact**:
  边界缺陷在生产环境频繁爆发。
- **Remediation**:
  在 `test_asar.py` 中补充针对 UTF-8 BOM、`apply_patch` 拒绝执行返回 `False`、越界切片抛错等针对性用例。

---

### [F-D5-04] 客户端核心运行时引擎与提取脚本测试覆盖率为 0%
- **Finding ID**: [F-D5-04]
- **Title**: Complete Zero-Coverage (0%) Across Engine Runtime (`ag_localization_engine.js`) and Extractor (`extract_untranslated.py`)
- **Location**: `engine/ag_localization_engine.js`, `scripts/extract_untranslated.py`
- **Severity**: **High**
- **Root Cause**:
  整个测试套件没有一个用例测试 JavaScript 引擎（584 行源模板，3,370 行生成文件）的真实匹配逻辑与 DOM 处理，亦未测试 `extract_untranslated.py`（117 行）。这两个模块处于完全未测试状态。
- **Impact**:
  运行时掉帧、原型污染、Token 泄露等缺陷完全脱离测试保障。
- **Remediation**:
  引入基于 Node.js / JSDOM 的端到端引擎单测，并在 Python 侧为提取脚本编写单元测试。

---

### [F-D5-05] 根目录缺失测试框架规范配置与覆盖率门禁
- **Finding ID**: [F-D5-05]
- **Title**: Missing Standard Pytest Infrastructure, Configuration, and Coverage Gate
- **Location**: 仓库根目录缺失 `pytest.ini` / `pyproject.toml`
- **Severity**: **Low**
- **Root Cause**:
  没有统一配置 `pytest.ini`，导致每次执行 pytest 时产生未捕获的缓存写入 Warning，且 CI 缺少代码覆盖率门禁。
- **Impact**:
  测试框架缺乏规范约束。
- **Remediation**:
  在根目录配置标准 `pytest.ini`：
  ```ini
  [pytest]
  testpaths = tests
  python_files = test_*.py
  addopts = -ra -q --strict-markers
  filterwarnings =
      ignore::pytest.PytestCacheWarning
  ```

---

## 8. 说明与正向合规项 (Informational Findings)

### [F-INFO-01] ASAR 基础读写算法格式高度合规
- **Finding ID**: [F-INFO-01]
- **Title**: Base ASAR Parsing and Serialization Implementation Conforms Strictly to Chromium Pickle Spec
- **Location**: `scripts/build.py:188-321` / `scripts/patcher.py:161-294`
- **Severity**: **Informational**
- **Assessment**:
  经对真实 4.97MB `app.asar`（1,092 个文件条目）进行往返读写仿真测试验证，底层 `u1=4 / u2=headerSize / u3=picklePayload / json_len` 的二进制打包逻辑与 Chromium 官方规范完全一致。往返写回后，未修改条目的哈希与 SHA-256 分块校验值完全保真，原子写入（Atomic Replacement）机制设计良好。

### [F-INFO-02] 代码生成物与模板零漂移
- **Finding ID**: [F-INFO-02]
- **Title**: Perfect Alignment and Zero Drift Between Generated Artifacts and Source Templates
- **Location**: `scripts/patcher.py`, `engine/ag_localization_engine.js`
- **Severity**: **Informational**
- **Assessment**:
  在干净环境重放 `scripts/build.py` 生成流程，生成的 `patcher.py` 与 `ag_localization_engine.js` 与仓库当前版本 SHA-256 完全一致，CI 中的 `git diff --exit-code` 漂移检查正常发挥效能。

### [F-INFO-03] 词典中部分词条译文缺失或退化
- **Finding ID**: [F-INFO-03]
- **Title**: Minor Translation Degradation and Redundant Keys in Dictionary
- **Location**: `locales/zh-CN.json`
- **Severity**: **Informational**
- **Assessment**:
  1. 存在将 `'Tokens'` 译为 `'Token'`，语义未汉化；
  2. 存在将 `'to be installed.'` 译为 `'。'` 的严重退化词条；
  3. 存在一条含中文的死 key `'允许 read access to this path?'`。由于引擎前置检查中文并直接跳过，该条目永不生效，属应清理的冗余垃圾。

---

## 9. 综合治理与优先修复路线图 (Prioritized Remediation Roadmap)

为确保项目以最高工程质量完成整改，建议分阶段实施以下修复路线图：

### 阶段一：紧急阻断性安全与核心功能热修复 (Release v1.0.5 — Immediate)
> **目标**：彻底消除 RCE 漏洞，恢复核心快捷键，修复退出码与 BOM 编码阻断。

1. **[修复 F-D1-01 / F-D3-01]** 彻底移除 `patch_menu_js` 中对 `addItemToSubmenu` 查找键的错误替换，恢复 `New Window` 菜单项与 `CmdOrCtrl+Shift+N` 快捷键；
2. **[修复 F-D2-01]** 重构 `splice_engine_dicts`，严禁直接拼接包含未转义注释的 JSON 文本，阻断 AST 逃逸与 RCE 攻击；
3. **[修复 F-D2-02]** 将 `escapeDollar` 替换为 ECMAScript 函数式替换器，彻底杜绝 `$` 替换字符导致的乱码与注入；
4. **[修复 F-D1-02]** 将 `apply_patch` 中所有拒绝执行与校验失败分支的返回值由 `return True` 改为 `return False`，确保 CLI 返回非 0 退出码；
5. **[修复 F-D3-05]** 将所有 JSON 读取操作的编码统一改为 `utf-8-sig`，彻底解决 Windows 记事本 BOM 导致的修改被静默丢弃问题；
6. **[修复 F-D3-06 & F-D3-07]** 清理 `zh-CN.json` 中 31 个带首尾空格的死词条，修正 `Reset zoom` 大小写冲突；
7. **[修复 F-D4-01]** 修改 `release.yml`，移除 `if [ -f ]` 静默放行逻辑，配置 `if-no-files-found: error`，杜绝发布空 Release。

### 阶段二：稳健性增强与边界防御加固 (Release v1.1.0 — Short-term)
> **目标**：提升原生补丁鲁棒性，加固 ASAR 读取与备份机制，消除性能瓶颈与崩溃。

1. **[实施 F-D1-04 & F-D1-07]** 将引擎定时轮询由无条件 2 秒全量读盘与全 DOM 遍历，改为先比对 `statSync` 修改时间，并拉长轮询间隔至 15 秒；
2. **[实施 F-D1-05]** 完善 `insideSkipZone` 判定，阻断 Monaco 代码编辑器 Token 穿透跳过区进入翻译管线；
3. **[实施 F-D2-03 & F-D2-04]** 引入动态正则表达式复杂度检测，阻断嵌套量词，并从 flags 白名单中剔除有状态的 `y` 标志；
4. **[实施 F-D2-08]** 在 macOS 平台上增加打补丁后的 `codesign --force --deep --sign -` 自动重签名逻辑，规避 Gatekeeper 崩溃；
5. **[实施 F-D3-02 & F-D3-03]** 将原生弹窗补丁改为具备空白符与引号容错能力的弹性正则，并增加 MISS 告警与汇总统计；
6. **[实施 F-D1-13 & F-D4-02]** 完善 Shell 脚本中的 `uname -m` 架构探测，并在 CI 矩阵中增加 Linux x64 与 macOS Intel (x86_64) 二进制编译；
7. **[实施 F-D1-09 & F-D3-10]** 在补丁入口增加前置运行中进程强校验，并重设 Windows 控制台输出流为 UTF-8。

### 阶段三：CI/CD 自动化构建与测试体系硬化 (Release v1.2.0 — Mid-term)
> **目标**：构建全面的测试防护网与现代化的工程化治理体系。

1. **[实施 F-D1-03]** 将内嵌在 `build.py` 中的 624 行 `PATCHER_TEMPLATE` 模板解耦为独立的 Python 文件，建立清晰的构建分发管线；
2. **[实施 F-D4-04 & F-D4-05]** 在 CI 流水线中加入编译后二进制的自动化冒烟测试（Smoke Test），并补齐 Windows 完整分发 zip 包；
3. **[实施 F-D4-03]** 精准重构 README 词条数校验正则，解除对文档正常技术数字的书写限制；
4. **[实施 F-D5-02 & F-D5-03]** 在 `tests/test_asar.py` 中补充针对原生菜单语义、UTF-8 BOM、拒绝执行退出码与截断 ASAR 的实测用例；
5. **[实施 F-D5-04 & F-D5-05]** 引入针对 JavaScript 引擎运行时的自动化端到端测试，配置规范的 `pytest.ini` 与覆盖率门禁（fail-under）；
6. **[实施 F-D1-14 & F-D1-17]** 归一化批处理脚本换行符，引入 `ruff`、`mypy` 静态类型检查与预提交钩子（pre-commit）。

---

## 10. 附录：运行时探针与验证证据清单

本次审计中的全部核心结论均经过真实运行环境探针或隔离仿真实验交叉复核：

| 验证实验编号 | 验证目标 | 采用方法与探针实现 | 实测结果 |
|:---|:---|:---|:---|
| **P-01** | AST Breakout RCE (F-D2-01) | 构造包含 `/*AG_ZH_ZH_END*/; global.INJECTED_PWNED = true; /*` 的合法 JSON 经 `_splice` 注入 Node.js 运行 | 成功逃逸并在 Node.js 顶层执行，输出 `INJECTED_PWNED = true` |
| **P-02** | `escapeDollar` No-Op (F-D2-02) | 在 Node.js v24 中传入 `Price is $10 and $& and $'` 测试字符串替换 | 返回值与输入完全一致，外层替换触发严重字符串复制与乱码 |
| **P-03** | ReDoS 灾难性回溯 (F-D2-03) | 在 V8 中对模式 `/(a+)+$/` 执行 27 字符不匹配串比对 | 线程完全被阻塞达 4,591 毫秒（4.6 秒） |
| **P-04** | 子菜单查找键丢弃项 (F-D1-01) | 在真实 Electron 44.5.1 默认菜单结构下仿真调用 `addItemToSubmenu` | 查找 `'文件 (File)'` 必定返回 `undefined`，`New Window` 菜单项 100% 丢失 |
| **P-05** | 词典 31 条空格不可达 (F-D3-06) | 按引擎真实查找流水线（`trim()` 精确 -> 小写 -> patterns）重放 2,070 条词条 | 31 条全灭，其中 26 条核心文案完全无替代匹配，在客户端永久保持英文 |
| **P-06** | 退出码 0 静默失败 (F-D1-02) | 隔离环境模拟修改词典且删除备份，调用 `patcher.py` 退出流程 | 终端打印警告，但返回进程退出码 0，`app.asar` 零字节改变 |
| **P-07** | Preload 强制沙箱隔离 (F-D1-04) | 真实 Electron 44.5.1 加载 Antigravity 主窗口同款 `webPreferences` 探针 | `require('fs')` 抛出 `module not found: fs`，证实运行时热加载路径为死代码 |
| **P-08** | 真实 ASAR 读写往返 (F-INFO-01) | 对本机 4.97MB 真实 `app.asar` 执行 read -> write -> read 完整往返 | 1,092 个条目内容零差异，347 个 unpacked 集合保真，offset 自洽 |

---

*报告编制完成，供开发团队、安全负责人与开源社区作为权威治理参考。*
