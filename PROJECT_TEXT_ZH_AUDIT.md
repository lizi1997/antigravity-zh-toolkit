# 项目自身文案与说明汉化清单

> 排查范围：本仓库内**面向用户或维护者**的说明、描述与文案（安装/还原/状态脚本、补丁器 CLI、构建器、提取工具、
> 引擎提示、GitHub Actions 工作流、`.gitignore` 注释），以及 `locales/zh-CN.json` 中的残留英文。
> 不包含：`README_EN.md`（面向英文用户的正式英文文档，应保留）、`LICENSE`（法律文本）、
> 已交付的客户端界面漏译清单（见 `UNTRANSLATED_UI_STRINGS.md`）、`tests/` 与大量内部代码注释（见文末说明）。

## 统计

| 级别 | 条数 | 含义 |
| :--- | ---: | :--- |
| P0 用户可见 | 94 | 终端用户直接看到 |
| P1 维护者可见 | 28 | 维护者/构建者看到 |
| P2 内部/CI | 40 | CI 日志或仓库内部 |
| P3 可选 | 17 | 可选/注释类 |
| **合计** | **179** | |

> `scripts/patcher.py` 是生成文件，勿直接改；“说明”列给出 `scripts/build.py` 的对应源行号（生成物行号 + 26）。
> 修改后运行 `python scripts/build.py --no-exe` 重新生成，否则下次构建会被覆盖。

## A. 安装 / 还原 / 状态脚本（31 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `install.sh` | 11-14 | # Pick the binary that matches this machine and fall back to the bundled<br># Python when it cannot run here (wrong architecture, missing exec permission).<br># A binary that fails must NOT abort the script: the bundled<br># scripts/patcher.py is the portable fallback and has to stay reachable. | # 选择与当前机器匹配的可执行文件；若其无法在本机运行（架构不符、缺少执行权限），<br># 则回退到随包附带的 Python 脚本。<br># 可执行文件运行失败时绝不能中止脚本：随包的<br># scripts/patcher.py 是可移植的后备方案，必须保持可调用。 | 注释（说明性文字） |
| `status.sh` | 6-9 | # Pick the binary that matches this machine and fall back to the bundled<br># Python when it cannot run here (wrong architecture, missing exec permission).<br># A binary that fails must NOT abort the script: the bundled<br># scripts/patcher.py is the portable fallback and has to stay reachable. | # 选择与当前机器匹配的可执行文件；若其无法在本机运行（架构不符、缺少执行权限），<br># 则回退到随包附带的 Python 脚本。<br># 可执行文件运行失败时绝不能中止脚本：随包的<br># scripts/patcher.py 是可移植的后备方案，必须保持可调用。 | 注释（说明性文字） |
| `restore.sh` | 11-14 | # Pick the binary that matches this machine and fall back to the bundled<br># Python when it cannot run here (wrong architecture, missing exec permission).<br># A binary that fails must NOT abort the script: the bundled<br># scripts/patcher.py is the portable fallback and has to stay reachable. | # 选择与当前机器匹配的可执行文件；若其无法在本机运行（架构不符、缺少执行权限），<br># 则回退到随包附带的 Python 脚本。<br># 可执行文件运行失败时绝不能中止脚本：随包的<br># scripts/patcher.py 是可移植的后备方案，必须保持可调用。 | 注释（说明性文字） |
| `安装汉化.command` | 20-23 | # Pick the binary that matches this machine and fall back to the bundled<br># Python when it cannot run here (wrong architecture, missing exec permission).<br># A binary that fails must NOT abort the script: the bundled<br># scripts/patcher.py is the portable fallback and has to stay reachable. | # 选择与当前机器匹配的可执行文件；若其无法在本机运行（架构不符、缺少执行权限），<br># 则回退到随包附带的 Python 脚本。<br># 可执行文件运行失败时绝不能中止脚本：随包的<br># scripts/patcher.py 是可移植的后备方案，必须保持可调用。 | 注释（说明性文字） |
| `还原官方.command` | 12-15 | # Pick the binary that matches this machine and fall back to the bundled<br># Python when it cannot run here (wrong architecture, missing exec permission).<br># A binary that fails must NOT abort the script: the bundled<br># scripts/patcher.py is the portable fallback and has to stay reachable. | # 选择与当前机器匹配的可执行文件；若其无法在本机运行（架构不符、缺少执行权限），<br># 则回退到随包附带的 Python 脚本。<br># 可执行文件运行失败时绝不能中止脚本：随包的<br># scripts/patcher.py 是可移植的后备方案，必须保持可调用。 | 注释（说明性文字） |
| `install.sh` | 48 | [!] $binary could not run on this machine (exit $rc). | [!] $binary 无法在本机运行（退出码 $rc）。 | 用户可见错误提示 |
| `status.sh` | 43 | [!] $binary could not run on this machine (exit $rc). | [!] $binary 无法在本机运行（退出码 $rc）。 | 用户可见错误提示 |
| `restore.sh` | 48 | [!] $binary could not run on this machine (exit $rc). | [!] $binary 无法在本机运行（退出码 $rc）。 | 用户可见错误提示 |
| `安装汉化.command` | 57 | [!] $binary could not run on this machine (exit $rc). | [!] $binary 无法在本机运行（退出码 $rc）。 | 用户可见错误提示 |
| `还原官方.command` | 49 | [!] $binary could not run on this machine (exit $rc). | [!] $binary 无法在本机运行（退出码 $rc）。 | 用户可见错误提示 |
| `install.sh` | 49 | [!] Falling back to the bundled Python script. | [!] 正在回退到随包附带的 Python 脚本。 | 用户可见错误提示 |
| `status.sh` | 44 | [!] Falling back to the bundled Python script. | [!] 正在回退到随包附带的 Python 脚本。 | 用户可见错误提示 |
| `restore.sh` | 49 | [!] Falling back to the bundled Python script. | [!] 正在回退到随包附带的 Python 脚本。 | 用户可见错误提示 |
| `安装汉化.command` | 58 | [!] Falling back to the bundled Python script. | [!] 正在回退到随包附带的 Python 脚本。 | 用户可见错误提示 |
| `还原官方.command` | 50 | [!] Falling back to the bundled Python script. | [!] 正在回退到随包附带的 Python 脚本。 | 用户可见错误提示 |
| `install.sh` | 56 | [!] Error: no usable Python 3 environment and no working binary. | [!] 错误：未找到可用的 Python 3 环境，也没有可用的可执行文件。 | 用户可见错误提示 |
| `status.sh` | 51 | [!] Error: no usable Python 3 environment and no working binary. | [!] 错误：未找到可用的 Python 3 环境，也没有可用的可执行文件。 | 用户可见错误提示 |
| `restore.sh` | 56 | [!] Error: no usable Python 3 environment and no working binary. | [!] 错误：未找到可用的 Python 3 环境，也没有可用的可执行文件。 | 用户可见错误提示 |
| `安装汉化.command` | 65 | [!] Error: no usable Python 3 environment and no working binary. | [!] 错误：未找到可用的 Python 3 环境，也没有可用的可执行文件。 | 用户可见错误提示 |
| `还原官方.command` | 57 | [!] Error: no usable Python 3 environment and no working binary. | [!] 错误：未找到可用的 Python 3 环境，也没有可用的可执行文件。 | 用户可见错误提示 |
| `install.sh` | 57 |     Install Python 3.10+ or download the prebuilt release: |     请安装 Python 3.10+，或下载预编译版本： | 用户可见提示 |
| `status.sh` | 52 |     Install Python 3.10+ or download the prebuilt release: |     请安装 Python 3.10+，或下载预编译版本： | 用户可见提示 |
| `restore.sh` | 57 |     Install Python 3.10+ or download the prebuilt release: |     请安装 Python 3.10+，或下载预编译版本： | 用户可见提示 |
| `安装汉化.command` | 66 |     Install Python 3.10+ or download the prebuilt release: |     请安装 Python 3.10+，或下载预编译版本： | 用户可见提示 |
| `还原官方.command` | 58 |     Install Python 3.10+ or download the prebuilt release: |     请安装 Python 3.10+，或下载预编译版本： | 用户可见提示 |
| `安装汉化.command` | 6 | # Remove attributes only from executable entry points, not the whole folder. | # 仅移除可执行入口文件的扩展属性，不要对整个文件夹执行。 | 注释 |
| `安装汉化.command` | 80 | read -p "按回车键退出终端 (Press Enter to exit)..." | read -p "按回车键退出终端..." | 中英混排，删除英文括注 |
| `还原官方.command` | 67 | read -p "官方版本还原完成！按回车键退出终端 (Press Enter to exit)..." | read -p "官方版本还原完成！按回车键退出终端..." | 中英混排，删除英文括注 |
| `build.sh` | 7 |    Antigravity-ZH Local Build Utility (macOS / Linux) |    Antigravity-ZH 本地构建工具（macOS / Linux） | 构建脚本横幅 |
| `build.bat` | 4 |   Antigravity-ZH Local Build Utility |   Antigravity-ZH 本地构建工具 | 构建脚本横幅 |
| `build.bat` | 10 |     echo [!] Build failed. Please ensure Python and PyInstaller are installed: |     echo [!] 构建失败。请确认已安装 Python 与 PyInstaller： | 构建失败提示 |

## B. 补丁器 CLI（scripts/patcher.py）（64 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `scripts/patcher.py` | 655/793 | [!] Error: Antigravity installation not found. Specify with --dir | [!] 错误：未找到 Antigravity 安装目录。请使用 --dir 指定。 | 生成物，源：scripts/build.py:681/819 |
| `scripts/patcher.py` | 662 | [!] Error: {asar_path} does not exist. | [!] 错误：{asar_path} 不存在。 | 生成物，源：scripts/build.py:688 |
| `scripts/patcher.py` | 665 | [*] Reading current app.asar... | [*] 正在读取当前 app.asar… | 生成物，源：scripts/build.py:691 |
| `scripts/patcher.py` | 669 | [!] Error reading {asar_path}: {e} | [!] 读取 {asar_path} 失败：{e} | 生成物，源：scripts/build.py:695 |
| `scripts/patcher.py` | 673 | [!] Error: dist/preload.js not found in app.asar! | [!] 错误：app.asar 中未找到 dist/preload.js！ | 生成物，源：scripts/build.py:699 |
| `scripts/patcher.py` | 684 | [*] Antigravity is already patched with the current engine and dictionaries! | [*] Antigravity 已使用当前引擎与词典完成汉化，无需重复操作！ | 生成物，源：scripts/build.py:710 |
| `scripts/patcher.py` | 689 | [!] Dictionaries changed but no official backup exists to re-patch from; keeping current patch. | [!] 词典已变更，但不存在可用于重新打补丁的官方备份；将保留当前补丁。 | 生成物，源：scripts/build.py:715 |
| `scripts/patcher.py` | 690 | [!] The new dictionaries were NOT applied. Restore the official app.asar first, then patch again. | [!] 新词典未生效。请先还原官方 app.asar，再重新执行补丁。 | 生成物，源：scripts/build.py:716 |
| `scripts/patcher.py` | 692 | [*] Dictionaries/engine changed since last patch; re-patching from official backup... | [*] 检测到词典或引擎在上次补丁后有变更，正在从官方备份重新打补丁… | 生成物，源：scripts/build.py:718 |
| `scripts/patcher.py` | 694/715 | [!] Backup checksum mismatch - app.asar.bak may have been replaced or modified. | [!] 备份校验和不匹配 —— app.asar.bak 可能已被替换或修改。 | 生成物，源：scripts/build.py:720/741 |
| `scripts/patcher.py` | 695/716 | [!] Refusing to patch from it; keeping the current patch. Run `restore` to re-baseline. | [!] 为避免风险，已拒绝基于该备份打补丁，并保留当前补丁。请运行 `restore` 重建基线。 | 生成物，源：scripts/build.py:721/742 |
| `scripts/patcher.py` | 699/720 | [!] Error: dist/preload.js missing from backup?! | [!] 错误：备份中缺少 dist/preload.js？！ | 生成物，源：scripts/build.py:725/746 |
| `scripts/patcher.py` | 702/723 | [!] The official backup belongs to a DIFFERENT client build than the installed app.asar. | [!] 官方备份与当前安装的 app.asar 属于不同的客户端构建版本。 | 生成物，源：scripts/build.py:728/749 |
| `scripts/patcher.py` | 703/724 | [!] Refusing to rebuild from it - that would roll the client back to an older version. | [!] 已拒绝基于该备份重建 —— 这会把客户端回滚到旧版本。 | 生成物，源：scripts/build.py:729/750 |
| `scripts/patcher.py` | 704/725 | [!] Run `restore` to re-baseline the backup, then patch again. | [!] 请运行 `restore` 重建备份基线，然后重新打补丁。 | 生成物，源：scripts/build.py:730/751 |
| `scripts/patcher.py` | 711 | [!] --force requested but no official backup exists; keeping current patch as-is. | [!] 已指定 --force，但不存在官方备份；将原样保留当前补丁。 | 生成物，源：scripts/build.py:737 |
| `scripts/patcher.py` | 713 | [*] Current build already patched; re-patching from clean official backup... | [*] 当前构建已打补丁，正在从干净的官方备份重新打补丁… | 生成物，源：scripts/build.py:739 |
| `scripts/patcher.py` | 729 | [*] Creating backup of official app.asar -> {bak_path}... | [*] 正在备份官方 app.asar → {bak_path}… | 生成物，源：scripts/build.py:755 |
| `scripts/patcher.py` | 738 | [*] Official backup already exists at {bak_path} | [*] 官方备份已存在：{bak_path} | 生成物，源：scripts/build.py:764 |
| `scripts/patcher.py` | 740 | [*] Detected app update: refreshing official backup (existing one was stale) | [*] 检测到客户端已更新：正在刷新官方备份（原备份已过期） | 生成物，源：scripts/build.py:766 |
| `scripts/patcher.py` | 748 | [*] Injecting modern localization engine into dist/preload.js... | [*] 正在将现代化汉化引擎注入 dist/preload.js… | 生成物，源：scripts/build.py:774 |
| `scripts/patcher.py` | 755 | [*] Patching native menus in dist/menu.js... | [*] 正在汉化 dist/menu.js 中的原生菜单… | 生成物，源：scripts/build.py:781 |
| `scripts/patcher.py` | 761 | [*] Patching native updater in dist/updater.js... | [*] 正在汉化 dist/updater.js 中的原生更新提示… | 生成物，源：scripts/build.py:787 |
| `scripts/patcher.py` | 767 | [*] Patching native dialogs in dist/main.js... | [*] 正在汉化 dist/main.js 中的原生对话框… | 生成物，源：scripts/build.py:793 |
| `scripts/patcher.py` | 772 | [*] Writing patched files to app.asar... | [*] 正在将补丁写入 app.asar… | 生成物，源：scripts/build.py:798 |
| `scripts/patcher.py` | 776 | [!] Write error: {e} | [!] 写入失败：{e} | 生成物，源：scripts/build.py:802 |
| `scripts/patcher.py` | 782 |   [+] 汉化补丁安装成功！(Patch applied successfully!) |   [+] 汉化补丁安装成功！ | 中英混排，删除英文括注；生成物，源：scripts/build.py:808 |
| `scripts/patcher.py` | 800 | [!] No backup file found at {bak_path} | [!] 未找到备份文件：{bak_path} | 生成物，源：scripts/build.py:826 |
| `scripts/patcher.py` | 811 | [!] The backup belongs to a DIFFERENT client build than the installed app.asar. | [!] 该备份与当前安装的 app.asar 属于不同的客户端构建版本。 | 生成物，源：scripts/build.py:837 |
| `scripts/patcher.py` | 812 | [!] Restoring it would roll the client back to another version. | [!] 还原该备份会将客户端回滚到另一个版本。 | 生成物，源：scripts/build.py:838 |
| `scripts/patcher.py` | 814 | [!] Could not compare the backup against the installed archive: {e} | [!] 无法将备份与当前安装的归档进行比对：{e} | 生成物，源：scripts/build.py:840 |
| `scripts/patcher.py` | 817 | [!] WARNING: backup checksum mismatch - app.asar.bak may have been modified or replaced. | [!] 警告：备份校验和不匹配 —— app.asar.bak 可能已被修改或替换。 | 生成物，源：scripts/build.py:843 |
| `scripts/patcher.py` | 818 | [!] Restoring it anyway as requested. | [!] 将按您的要求继续还原。 | 生成物，源：scripts/build.py:844 |
| `scripts/patcher.py` | 820 | [*] Restoring original app.asar from backup... | [*] 正在从备份还原官方 app.asar… | 生成物，源：scripts/build.py:846 |
| `scripts/patcher.py` | 824 | [+] Restored official Antigravity app.asar successfully! | [+] 已成功还原官方 Antigravity app.asar！ | 生成物，源：scripts/build.py:850 |
| `scripts/patcher.py` | 827 | [!] Restore failed: {e} | [!] 还原失败：{e} | 生成物，源：scripts/build.py:853 |
| `scripts/patcher.py` | 833 | === Antigravity Localization Status === | === Antigravity 汉化状态 === | 生成物，源：scripts/build.py:859 |
| `scripts/patcher.py` | 834 | Platform:    {sys.platform} | 平台：        {sys.platform} | 生成物，源：scripts/build.py:860 |
| `scripts/patcher.py` | 835 | Install Dir: {install_dir} | 安装目录：    {install_dir} | 生成物，源：scripts/build.py:861 |
| `scripts/patcher.py` | 837 | Status: Not installed or not found. | 状态：未安装或未找到。 | 生成物，源：scripts/build.py:863 |
| `scripts/patcher.py` | 842 | app.asar exists: {os.path.exists(asar_path)} | app.asar 存在：{os.path.exists(asar_path)} | 生成物，源：scripts/build.py:868 |
| `scripts/patcher.py` | 843 | Backup exists:   {os.path.exists(bak_path)} | 备份存在：     {os.path.exists(bak_path)} | 生成物，源：scripts/build.py:869 |
| `scripts/patcher.py` | 844 | Client running:  {is_antigravity_running()} | 客户端运行中： {is_antigravity_running()} | 生成物，源：scripts/build.py:870 |
| `scripts/patcher.py` | 851 | Patched:         {is_patched} | 已汉化：       {is_patched} | 生成物，源：scripts/build.py:877 |
| `scripts/patcher.py` | 854 | Error reading app.asar: {e} | 读取 app.asar 出错：{e} | 生成物，源：scripts/build.py:880 |
| `scripts/patcher.py` | 876 | input("\n按回车键退出 (Press Enter to exit)...") | input("\n按回车键退出…") | 中英混排，删除英文括注；生成物，源：scripts/build.py:902 |
| `scripts/patcher.py` | 859 | Antigravity Modern Chinese Localization Patcher v1.0.5 | Antigravity 现代化中文汉化补丁器 v1.0.5 | argparse 描述；生成物，源：scripts/build.py:885 |
| `scripts/patcher.py` | 860 | Action to perform (default: patch) | 要执行的操作（默认：patch） | argparse help；生成物，源：scripts/build.py:886 |
| `scripts/patcher.py` | 861 | Custom Antigravity installation directory | 自定义 Antigravity 安装目录 | argparse help；生成物，源：scripts/build.py:887 |
| `scripts/patcher.py` | 862 | Force re-patching even if already patched | 即使已打补丁也强制重新打补丁 | argparse help；生成物，源：scripts/build.py:888 |
| `scripts/patcher.py` | 240/269 | [+] Recorded backup checksum: {sidecar} | [+] 已记录备份校验和：{sidecar} | 生成物，源：scripts/build.py:266/295 |
| `scripts/patcher.py` | 242/272 | [!] Could not write backup checksum {sidecar}: {e} | [!] 无法写入备份校验和 {sidecar}：{e} | 生成物，源：scripts/build.py:268/298 |
| `scripts/patcher.py` | 448 | [*] {label} patch results: | [*] {label} 补丁结果： | 生成物，源：scripts/build.py:474 |
| `scripts/patcher.py` | 452 | [!] {missed} {label} replacement(s) not found - the client UI may have changed in an update | [!] 有 {missed} 处 {label} 替换未命中 —— 客户端界面可能已在更新中变更 | 生成物，源：scripts/build.py:478 |
| `scripts/patcher.py` | 569 | [!] External zh-CN.json could not be parsed (invalid JSON or an encoding problem); | [!] 外部 zh-CN.json 无法解析（JSON 无效或编码有问题）； | 生成物，源：scripts/build.py:595 |
| `scripts/patcher.py` | 570 | [!] falling back to the bundled dictionary - your edits were NOT applied. | [!] 已回退到内置词典 —— 您的修改未生效。 | 生成物，源：scripts/build.py:596 |
| `scripts/patcher.py` | 572 | [!] External patterns.json could not be parsed; falling back to the bundled rules. | [!] 外部 patterns.json 无法解析；已回退到内置规则。 | 生成物，源：scripts/build.py:598 |
| `scripts/patcher.py` | 586 | [*] Normalized {len(padded)} key(s) with leading/trailing whitespace from external zh-CN.json. | [*] 已规范化外部 zh-CN.json 中 {len(padded)} 个首尾带空白的键。 | 生成物，源：scripts/build.py:612 |
| `scripts/patcher.py` | 591 | [!] External {label} contains an engine splice marker; ignoring that file. | [!] 外部 {label} 包含引擎拼接标记；已忽略该文件。 | 生成物，源：scripts/build.py:617 |
| `scripts/patcher.py` | 625 | [!] zh dictionary sentinel not found in engine; injecting embedded dictionaries as-is | [!] 引擎中未找到词典拼接标记；将按原样注入内置词典 | 生成物，源：scripts/build.py:651 |
| `scripts/patcher.py` | 629 | [!] patterns sentinel not found in engine; injecting embedded dictionaries as-is | [!] 引擎中未找到规则拼接标记；将按原样注入内置词典 | 生成物，源：scripts/build.py:655 |
| `scripts/patcher.py` | 647 | [+] Seeded editable dictionary: {target} | [+] 已生成可编辑词典：{target} | 生成物，源：scripts/build.py:673 |
| `scripts/patcher.py` | 649 | [!] Could not seed {target}: {e} | [!] 无法生成 {target}：{e} | 生成物，源：scripts/build.py:675 |
| `scripts/patcher.py` | 24 | SIGNATURE_PRELOAD = "// Antigravity Client Modern Chinese Localization Engine" | 保持英文（不要翻译） | 补丁识别签名；翻译后“是否已打补丁”的检测会失效，导致重复注入 |

## C. 构建器（scripts/build.py）（17 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `scripts/build.py` | 922 |   Antigravity-ZH Toolkit Builder (v1.0.5) |   Antigravity-ZH 工具包构建器 (v1.0.5) | 构建横幅 |
| `scripts/build.py` | 929 | [1/3] Loading locales and building ag_localization_engine.js... | [1/3] 正在加载词典并构建 ag_localization_engine.js… |  |
| `scripts/build.py` | 943-948 | [!] locales/zh-CN.json has {len(padded_keys)} key(s) with leading/trailing whitespace - they can never match because the engine trims the UI text before looking it up.<br>    {preview}<br>[!] Fix the keys (or move the variable part into locales/patterns.json) and rebuild. | [!] locales/zh-CN.json 中有 {len(padded_keys)} 个键的首尾带空白 —— 引擎在查表前会裁剪界面文本，因此这些键永远无法命中。<br>    {preview}<br>[!] 请修正这些键（或将变量部分移入 locales/patterns.json）后重新构建。 | 构建期校验错误 |
| `scripts/build.py` | 954-958 | [!] locales/{label} contains an engine splice marker (AG_ZH_ZH_START/END, AG_ZH_PATTERNS_START/END).<br>[!] That marker would break the engine splice - remove it and rebuild. | [!] locales/{label} 包含引擎拼接标记（AG_ZH_ZH_START/END、AG_ZH_PATTERNS_START/END）。<br>[!] 该标记会破坏引擎拼接 —— 请移除后重新构建。 | 构建期校验错误 |
| `scripts/build.py` | 964-968 | [!] locales/zh-CN.json has {len(empty_values)} entry/entries with an empty translation - the engine would render an empty label.<br>    {preview}<br>[!] Fill them in or remove them and rebuild. | [!] locales/zh-CN.json 中有 {len(empty_values)} 条词条的译文为空 —— 引擎会渲染出空白标签。<br>    {preview}<br>[!] 请补全或删除这些词条后重新构建。 | 构建期校验错误 |
| `scripts/build.py` | 977 |       Saved {engine_out} ({len(full_engine_js)} bytes) |       已保存 {engine_out}（{len(full_engine_js)} 字节） |  |
| `scripts/build.py` | 979 | [2/3] Embedding latest engine into scripts/patcher.py... | [2/3] 正在将最新引擎嵌入 scripts/patcher.py… |  |
| `scripts/build.py` | 988 |       Updated {patcher_py} |       已更新 {patcher_py} |  |
| `scripts/build.py` | 993 | [3/3] Compiling {binary_name} with PyInstaller... | [3/3] 正在使用 PyInstaller 编译 {binary_name}… |  |
| `scripts/build.py` | 1018 | [+] Copied to repo root. | [+] 已复制到仓库根目录。 |  |
| `scripts/build.py` | 1020 | [!] Could not copy the binary to the repo root: {e} | [!] 无法将可执行文件复制到仓库根目录：{e} |  |
| `scripts/build.py` | 1030 |   [+] Build Succeeded! |   [+] 构建成功！ |  |
| `scripts/build.py` | 1031 |   [+] Binary: {output_bin} |   [+] 可执行文件：{output_bin} |  |
| `scripts/build.py` | 1035 | [!] Compilation failed: {e} | [!] 编译失败：{e} |  |
| `scripts/build.py` | 1038 | [+] Engine and patcher updated (skipping executable compilation). | [+] 引擎与补丁器已更新（已跳过可执行文件编译）。 |  |
| `scripts/build.py` | 1042 | Antigravity-ZH Builder v1.0.5 | Antigravity-ZH 构建器 v1.0.5 | argparse 描述 |
| `scripts/build.py` | 1043 | Skip PyInstaller compilation | 跳过 PyInstaller 编译 | argparse help |

## D. 未翻译提取工具（scripts/extract_untranslated.py）（11 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `scripts/extract_untranslated.py` | 3-7 | Antigravity Untranslated String Extractor<br>Extracts candidate UI strings from language_server and app.asar,<br>compares with existing zh-CN.json, and outputs missing entries. | Antigravity 未翻译字符串提取器<br>从 language_server 与 app.asar 中提取候选界面字符串，<br>与现有 zh-CN.json 比对后输出缺失词条。 | 模块文档字符串 |
| `scripts/extract_untranslated.py` | 19 | """The user's editable dictionary directory (same location as the patcher).""" | """用户可编辑的词典目录（与补丁器使用的位置一致）。""" | 函数文档字符串 |
| `scripts/extract_untranslated.py` | 54 | print(f"[*] Scanning binary: {bin_path}...") | print(f"[*] 正在扫描二进制文件：{bin_path}…") |  |
| `scripts/extract_untranslated.py` | 91 | print(f"[*] Found {len(strings)} raw candidate strings in {os.path.basename(bin_path)}") | print(f"[*] 在 {os.path.basename(bin_path)} 中找到 {len(strings)} 条原始候选字符串") |  |
| `scripts/extract_untranslated.py` | 95 | """Platform-aware candidates for the Antigravity installation.""" | """按平台推断 Antigravity 的候选安装目录。""" | 函数文档字符串 |
| `scripts/extract_untranslated.py` | 118 | print(f"[*] Loaded existing dictionary: {len(existing_dict)} entries") | print(f"[*] 已加载现有词典：{len(existing_dict)} 条") |  |
| `scripts/extract_untranslated.py` | 140 | print(f"[+] Total missing untranslated candidate strings: {len(missing)}") | print(f"[+] 缺失的未翻译候选字符串总数：{len(missing)}") |  |
| `scripts/extract_untranslated.py` | 153 | print(f"[+] Saved missing candidates to: {out_path}") | print(f"[+] 缺失候选已保存到：{out_path}") |  |
| `scripts/extract_untranslated.py` | 157 | description="Extract untranslated strings from Antigravity binaries" | description="从 Antigravity 二进制文件中提取未翻译字符串" | argparse 描述 |
| `scripts/extract_untranslated.py` | 158 | help="Output JSON file for missing strings" | help="缺失字符串的输出 JSON 文件" | argparse help |
| `scripts/extract_untranslated.py` | 159 | help="Antigravity installation directory" | help="Antigravity 安装目录" | argparse help |

## E. 汉化引擎提示（engine/engine_template.js）（3 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `engine/engine_template.js` | 14 | console.error('[AG-ZH] Failed to read lang preference:', e); | console.error('[AG-ZH] 读取语言偏好失败：', e); | 控制台调试提示 |
| `engine/engine_template.js` | 80-81 | console.warn('[AG-ZH] Runtime dictionary hot loading is unavailable in this client '<br>                + '(sandboxed preload). Re-run the patcher after editing the dictionary.'); | console.warn('[AG-ZH] 当前客户端不支持运行时热加载词典 '<br>                + '（preload 处于沙箱中）。修改词典后请重新运行补丁器。'); | 控制台警告（用户可能看到） |
| `engine/engine_template.js` | 631 | console.error('[AG-ZH] Init error:', e); | console.error('[AG-ZH] 初始化错误：', e); | 控制台调试提示 |

## F. GitHub Actions（.github/workflows/release.yml）（32 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `.github/workflows/release.yml` | 1 | name: Build and Release | name: 构建与发布 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 3 | # A new push on the same ref must not race with a running one. | # 同一 ref 上的新推送不得与正在运行的工作流竞争。 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 19 | name: Test and verify generated files | name: 测试并校验生成文件 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 26 | name: Checkout repository | name: 检出仓库 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 29 | name: Set up Python | name: 配置 Python | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 35 | name: Set up Node.js | name: 配置 Node.js | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 40 | name: Install dependencies | name: 安装依赖 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 45 | name: Run tests | name: 运行测试 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 48 | name: Check Python and JavaScript syntax | name: 检查 Python 与 JavaScript 语法 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 54 | name: Verify generated files are current | name: 校验生成文件是否为最新 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 59 | name: Verify README dictionary counts | name: 校验 README 中的词典条数 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 85 | name: Build on ${{ matrix.os }} (${{ matrix.arch }}) | name: 在 ${{ matrix.os }} (${{ matrix.arch }}) 上构建 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 108 | name: Checkout repository | name: 检出仓库 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 111 | name: Set up Python | name: 配置 Python | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 117 | name: Install dependencies | name: 安装依赖 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 122 | name: Build executable | name: 构建可执行文件 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 126 | name: Prepare binary artifact | name: 准备二进制产物 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 150 | echo "::error::the build produced no ${{ matrix.dist_file }}" | echo "::error::构建未生成 ${{ matrix.dist_file }}" | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 71 | print(f"[!] {path}: advertised count '{exp}' missing (actual: {entries} entries / {rules} rules)") | print(f"[!] {path}: 缺少声明的条数 '{exp}'（实际：{entries} 条 / {rules} 条规则）") | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 77 | print(f"[!] {path}: stale entry count '{m.group(1)}' (actual: {entries:,})") | print(f"[!] {path}: 词条数已过期 '{m.group(1)}'（实际：{entries:,}）") | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 80 | print(f"[+] README counts match locales: {entries} entries / {rules} rules") | print(f"[+] README 条数与 locales 一致：{entries} 条 / {rules} 条规则") | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 135 | # Create structured macOS distribution directory | # 创建结构化的 macOS 发行目录 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 143 | # Package into double-clickable zip and tar.gz | # 打包为可双击的 zip 与 tar.gz | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 187 | # A release must never ship without the artifacts it advertises. | # 发布包绝不能缺少其所声明的产物。 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 193 | echo "::error::missing release artifact(s):$missing" | echo "::error::缺少发布产物：$missing" | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 154 | name: Upload Build Artifact | name: 上传构建产物 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 164 | name: Create GitHub Release | name: 创建 GitHub Release | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 173 | name: Checkout repository | name: 检出仓库 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 176 | name: Download all build artifacts | name: 下载全部构建产物 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 181 | name: Prepare release files | name: 准备发布文件 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 197 | name: Generate SHA256 checksums | name: 生成 SHA256 校验和 | CI 名称/日志（不直接影响终端用户） |
| `.github/workflows/release.yml` | 203 | name: Create GitHub Release | name: 创建 GitHub Release | CI 名称/日志（不直接影响终端用户） |

## G. 仓库配置注释（.gitignore / .gitattributes）（13 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `.gitignore` | 1 | # Byte-compiled / optimized / DLL files | # 字节码编译 / 优化 / DLL 文件 | 仓库配置注释（开发者可见） |
| `.gitignore` | 8 | # Distribution / packaging | # 发布 / 打包 | 仓库配置注释（开发者可见） |
| `.gitignore` | 14 | # PyInstaller & Executables | # PyInstaller 与可执行文件 | 仓库配置注释（开发者可见） |
| `.gitignore` | 18 | # Backup files | # 备份文件 | 仓库配置注释（开发者可见） |
| `.gitignore` | 21 | # Extractor output (untranslated candidates, must never be committed) | # 提取器输出（未翻译候选，严禁提交） | 仓库配置注释（开发者可见） |
| `.gitignore` | 27 | # Logs and databases | # 日志与数据库 | 仓库配置注释（开发者可见） |
| `.gitignore` | 30 | # Environments | # 虚拟环境 | 仓库配置注释（开发者可见） |
| `.gitignore` | 37 | # IDE & OS files | # IDE 与操作系统文件 | 仓库配置注释（开发者可见） |
| `.gitignore` | 49 | # macOS & Unix binaries | # macOS 与 Unix 可执行文件 | 仓库配置注释（开发者可见） |
| `.gitignore` | 55 | # Local metadata | # 本地元数据 | 仓库配置注释（开发者可见） |
| `.gitattributes` | 1 | # Auto-detect text files and normalize line endings | # 自动识别文本文件并规范化行尾 | 仓库配置注释（开发者可见） |
| `.gitattributes` | 4 | # Windows batch files must use CRLF | # Windows 批处理文件必须使用 CRLF | 仓库配置注释（开发者可见） |
| `.gitattributes` | 8 | # Unix shell scripts and workflows must always use LF | # Unix shell 脚本与工作流必须始终使用 LF | 仓库配置注释（开发者可见） |

## H. 词典与文档中的残留英文（8 条）

| 文件 | 行号 | 原文 | 建议中文译文 | 说明 |
| :--- | ---: | :--- | :--- | :--- |
| `locales/zh-CN.json` | 661 | "Best of": "Best of" | "Best of": "择优生成（Best of）" | 唯一一条真正未汉化的界面词条；同文件内 "Best of N" 作为产品术语保留 |
| `locales/zh-CN.json` | 1058 | "to be installed.": "。" | （无需修改） | 片段词条；上下文已由相邻词条拼成完整中文句子，值为“。”是有意为之 |
| `locales/zh-CN.json` | 1172 | "Tokens": "Token" | "Tokens": "Token"（计量单位，可保留） | 单位名，保留原文 |
| `locales/zh-CN.json` | 1395 | "Cascade ID": "Cascade ID" | "Cascade ID": "Cascade ID"（技术标识，可保留） | 技术标识，保留原文 |
| `README.md` | 31 | **2,792** 词条 | **2,816** 词条 | 与当前 locales/zh-CN.json（2,816 条）不一致；CI 的 README 条数校验会失败 |
| `README.md` | 126 | # 核心汉化静态词典 (2,792 词条) | # 核心汉化静态词典 (2,816 词条) | 目录树中的同类过期数字 |
| `README_EN.md` | 31 | **2,792** entries | **2,816** entries | 英文版数字同样过期 |
| `README_EN.md` | 124 | # Core dictionary (2,792 entries) | # Core dictionary (2,816 entries) | 英文版目录树中的同类过期数字 |

---

## 未逐条展开的部分（按范围排除）

| 范围 | 英文内容量 | 是否建议汉化 | 原因 |
| :--- | :--- | :--- | :--- |
| `README_EN.md` | 180 行 | 否 | 面向英文用户的正式英文文档，翻译会破坏双语入口 |
| `LICENSE` | 21 行 | 否 | MIT 法律文本，保持原文 |
| `tests/*.py` | 约 137 行英文测试名/注释 | 可选 | 仅开发者阅读，不影响用户与 CI 输出 |
| 内部代码注释/文档字符串 | `patcher.py` 约 122 行、`engine_template.js` 约 66 行、`build.py` 约 21 行、`extract_untranslated.py` 约 16 行 | 可选 | 维护者文档；如需 100% 中文仓库可再单独处理 |
| `AUDIT_REPORT.md` / `AUDIT_ROUND2.md` 中的英文 | 代码块/测试输出/引用 | 否 | 审计证据原文，翻译会失真 |

## 建议处理顺序

1. **P0**：先改用户可见的失败提示与混排文案（安装/还原/状态/补丁器），避免中文用户看到英文报错。
2. **P0**：修正 `README.md` / `README_EN.md` 的 2,792 → 2,816，恢复 CI 的 README 条数校验。
3. **P1**：补丁器成功路径与构建器输出；改 `scripts/build.py` 后重建 `scripts/patcher.py`。
4. **P2/P3**：CI 名称、`.gitignore` 注释、引擎调试日志，可按需批量处理。
5. 客户端界面漏译的 752 条建议译文见 `UNTRANSLATED_UI_STRINGS.md`，入库前按上下文复核片段条目。

*本清单只做排查与译法建议，未修改任何源码或词典。*
