# 自动汉化 MVP：独立验证报告（t4）

> 状态：**PASS（MVP 范围内）**。本报告由独立验证者（`verifier`）编写，**未修改任何实现代码、词典、生成物或文档**；
> 所有结论都可按附录 A 的命令复现，原始输出保存在 `.pytest_tmp/verify/out/`（该目录被 `.gitignore` 忽略，属临时工件）。
>
> 被验证对象：`scripts/localize.py` + `scripts/localization/`（8 个模块，t3 交付）、`tests/test_localize_mvp.py`、
> Phase 0 基线修复（生成物与 README 计数对齐）、`docs/auto-localization-mvp.md`。
> 上游：`docs/auto-localization-baseline.md`（t1）、`docs/auto-localization-design.md`（t2）。
>
> 验证环境：Windows 11 / Python 3.13.11（`D:\miniconda3\python.exe`）/ Node v24.22.1；
> DSH 沙箱为 `workspace-write`（其 Windows ACL 限制对 `mode 0o700` 目录的写入，见 §8.2）。

---

## 0. 结论摘要

| 项 | 结论 |
| :--- | :--- |
| 总体判定 | **PASS**：MVP 声称的核心能力全部独立复现，无阻塞项（blocker=0）。 |
| dry-run 默认与零写盘 | ✅ 69 个文件的全仓 sha256 快照前后**完全一致**；未创建 `.l10n/`；退出码 2（门禁失败时）语义正确。 |
| 输出确定性 | ✅ 固定 `--run-id` 时两次 dry-run 输出**字节完全相同**；不固定时仅 `run_id`（时间戳+uuid）不同，其余字段全等。 |
| QA 门禁有效性 | ✅ 23 个黑盒用例 100% 命中预期规则（H1–H13、H21、H7、H8、H9 全覆盖），失败时**不落盘**。 |
| 保真（占位符/URL/文件名/代码标识/术语） | ✅ 全量 761 条独立复算 **0 丢失**；2 条 H10 术语命中经 `CONTRIBUTING.md:54-61` 核对为**候选译文内容问题，不是误报**。 |
| 重复/空值 | ⚠️ 冲突重复行 → H9 blocker（exit 2）✅；相同重复行去重 ✅；**空/纯空白译文被静默丢弃**（不产生 H5 finding，见 F3，低）。 |
| `--apply` 幂等与确定性 | ✅ 两个独立副本产物 sha256 **完全相同**；二次 apply 0 新增、词典/引擎/patcher sha256 全等。 |
| 最小 diff / 文件格式 | ✅ 对主仓库词典 `diff --numstat` = **762 insertions / 1 deletion**；CRLF（3579 行、0 裸 LF）与结尾换行保留；重序列化字节全等。 |
| 失败回滚 | ✅ 构建失败、回读条数不符两种场景均**逐字节恢复词典**（sha256 复原），exit 4；另实测到 1 条残留不一致窗口（F7，低）。 |
| 生成物只经 `build.py` | ✅ 代码内**无**对 `engine/`、`scripts/patcher.py` 的直写；在隔离副本用 `build.py --no-exe` 重建的引擎/patcher 与主仓库产物**字节相同**。 |
| 基线门禁 | ✅ `build.py --no-exe` 后 `git diff` 无变化；临时索引复现 CI 门禁 exit 0；README 计数门禁 `2816 entries / 180 rules` 通过。 |
| 语法/测试 | ✅ `py_compile` 0、`node --check` ×2 = 0、`pytest tests/test_localize_mvp.py` **46 passed**；全套 `pytest` = 127 passed / 1 failed / 34 errors（全部为沙箱 ACL 假阴性，已用对照实验证明）。 |
| 抽样人工复核 | 82 条（10.8%）：**语义准确率 100%（0 条语义错误）**，无瑕疵 91.5%（75/82），可读性生硬 2 条（2.4%），风格小瑕 5 条（6.1%）。 |
| 非阻塞发现 | F1 文档笔误（770 vs 761）、F2 `--provider-cmd` 的 Windows 路径被 `shlex` 吃掉、F3 空译文静默丢弃、F4 H6 在提案链路不可达、F5 `merge` 报告字段不一致、F6 apply 不更新 README（真实仓库 apply 后 CI 必红）、F7 双重失败残留、F8 未知 `--waive` 规则静默接受、F9 片段拼接不可离线自证、F10 H2 对非常见路径/扩展名不告警。 |
| 范围外未实现（**不算缺陷**） | 提取器重写/探针（Phase 1）、`patterns.json` 合并与 H17–H20、引擎命中计数器与真机 V3（Phase 4）、`patch --dry-run`/客户端快照/自动回滚（Phase 4）、在线 provider（Phase 3）、跨 run 指标库（Phase 5）。 |

一句话：**t3 的 MVP 在其自我声明的范围内是可复现、可回滚、确定性的；它没有被过度宣传为「无人汉化」，但也不能直接对真实仓库 `--apply` 后保持 CI 绿（F6）。**

---

## 1. 验证方法（独立于实现）

1. **黑盒优先**：QA/CLI 用例全部通过子进程调用真实 CLI（`python scripts/localize.py …`），不 import 实现模块；只有"产物结构"类检查用独立正则/`json`/`ast` 重新解析。
2. **全仓快照**：对仓库内 69 个文件（排除 `.git/`、`.agent-teams/`、`.workbuddy/`、`.pytest_tmp/`、`__pycache__/` 等）做 sha256 快照，`dry-run` 前后逐文件比对，用于证明"零写盘"。
3. **隔离副本**：所有 `--apply` 都在 `.pytest_tmp/verify/scratch/copy{A..G}`（完整复制 `scripts/build.py`、`engine/engine_template.js`、`locales/`、候选文件）里进行，**主仓库从未执行 `--apply`**；主仓库词典 sha256 全程为 `793905e9…`（2,816 条）。
4. **双副本确定性**：copyA/copyB 用相同输入独立跑 `--apply`，比对词典/引擎/patcher 三份产物的 sha256。
5. **对照实验**：对 pytest 的 1 failed + 34 errors 做 `mode 0o700` 目录对照（§8.2），把"环境假阴性"与"真失败"分开。
6. **临时索引复现 CI**：用 `GIT_INDEX_FILE` 指向临时索引执行 `git read-tree HEAD` + `git add -A`，再跑构建与 `git diff --exit-code`，**不动真实索引/历史**。
7. **人工复核**：用固定种子 + 规则（片段/无中文/短串/长串/含 token/随机）从 761 条中抽取 82 条，逐条判读并分类（§9）。

验证用辅助脚本均在 `.pytest_tmp/verify/`（`snapshot.py`、`analyze_inputs.py`、`edge_cases.py`、`verify_artifacts.py`、`verify_patcher.py`、`stats.py`、`fragments.py`、`sample_for_review.py`、`residue.py`、`readme_gate.py`、`offline_check.py`、`fake_build.py`、`partial_build.py`、`fake_translator.py`）。它们是临时工件（gitignored），文档附录 A 给出等价的独立命令。

---

## 2. dry-run：默认、确定性、零写盘、退出码

### 2.1 真实候选集的 dry-run 结果（可复现）

```bash
python scripts/localize.py release --json --run-id fixed-dryrun   # exit 2
```

| 观测 | 值 |
| :--- | :--- |
| 候选 | 761 条，761 条带译文（`without_translation=0`） |
| provider | `file=761`、`tm=1`（`tm` 的 1 条与 `file` 同源被遮蔽；`proposals.total=761`） |
| QA | 761 条检查 → `gate=fail`，**blockers=2（H10）**，majors=0，minors=0 |
| 合并计划 | +759 additions / 0 already present / 0 conflicts / 2 quarantined |
| diff | 766 行 = 3 行 diff 头（`---`/`+++`/1 个 `@@`）+ 763 行内容（762 新增 + 1 删除；预览截断到 40 行） |
| 退出码 | **2**（门禁失败，符合 CLI 语义：0 成功 / 2 门禁 / 4 前置 / 5 内部） |
| 耗时 | 首次 ≈149 ms，后续 104–107 ms |

`--json` 输出为**单行** JSON，人类日志在 `--json` 下被抑制（stdout 仅一行）。人读模式示例（节选）：

```
QA (proposals): 761 checked -> fail   blockers=2 majors=0 minors=0
  [blocker] H10 glossary term missing: ['credits->积分', 'credits->积分']
  [blocker] H10 glossary term missing: ['customizations->自定义配置']
  rules not implemented in this MVP: H14, H15, H16, H17, H18, H19, H20, H22
plan: +759 additions, 0 already present, 0 conflicts, 2 quarantined
```

### 2.2 确定性

| 实验 | 结果 |
| :--- | :--- |
| 两次 `--run-id fixed-dryrun` | 输出文件 sha256 **相同**（逐字节一致） |
| 两次默认 run-id | `run_id` 不同（`20261124T151253-bb1be7d9` 等），删去该字段后 JSON **完全相等** |
| 未实现规则列表 | 每次报告都带 `coverage.not_implemented = H14,H15,H16,H17,H18,H19,H20,H22`（不假装全绿） |

> 观察（非缺陷）：dry-run 的 `run_id` 默认含时间戳+uuid，因此"字节级确定性"需要显式 `--run-id`；这是元数据，不影响内容确定性。设计文档未承诺字节级输出确定性，建议在文档中补一句。

### 2.3 零写盘 / 无未预期变更

- 69 文件全仓 sha256 快照：dry-run 前后 **added=0 / removed=0 / changed=0**；
- 未创建 `.l10n/`（`Test-Path .l10n` = False）；
- 三次 dry-run 后再快照，仍与基线全等；
- 验证结束时再快照：**仍全等**（`build.py --no-exe` 重写生成物后字节不变）。

### 2.4 退出码与侧信道

| 场景 | 观测 |
| :--- | :--- |
| 门禁失败 + `--apply` | exit 2，词典 sha256 不变，**不创建 `.l10n/`**（在写盘前返回） |
| 候选文件缺失 | exit 4，`error` 含 `candidate file not found` |
| `--provider online`（缺开关） | exit 4，`error` 含 `AG_L10N_ALLOW_NETWORK` |
| `--provider cmd` 命令不存在 | exit 4，`provider command not found`（不崩溃） |
| `--limit 5` | 只处理前 5 条，`inputs.limit=5`，exit 0 |

---

## 3. QA 门禁：黑盒用例矩阵（23/23 通过）

在隔离仓库（3 条小词典 + CRLF 格式）中逐例运行真实 CLI，断言"退出码 + 命中规则 + 合并计划 + 磁盘是否变化"。
全部 23 例 **0 期望失败**：

| # | 用例 | 期望 | 实测 |
| :--- | :--- | :--- | :--- |
| 1 | 空 / 纯空白译文 | exit 0，不写入 | exit 0、additions 0（**静默丢弃**，见 F3） |
| 2 | 占位符丢失 `{count}` | exit 2 / H1 | exit 2、H1、quarantined=1 |
| 3 | URL 丢失 | exit 2 / H2 | ✅ |
| 4 | 文件名丢失 `app.asar` | exit 2 / H2 | ✅ |
| 5 | 代码标识丢失 `--no-exe` | exit 2 / H3 | ✅ |
| 6 | HTML 结构变化 | exit 2 / H4 | ✅ |
| 7 | 术语缺失（workspace） | exit 2 / H10 | ✅ |
| 8 | 禁用译法（Agent→代理） | exit 2 / H11 | ✅（同时 H10，可解释） |
| 9 | 原文 >500 字符 | exit 2 / H12 blocker | ✅ |
| 10 | 译文超长（1.4×） | exit 2 / H12 major | ✅ |
| 11 | 同源冲突重复行 | exit 2 / H9 | ✅ |
| 12 | 与现有键大小写碰撞且译文不同 | exit 2 / H21 | ✅ |
| 13 | 拼接哨兵注入 | exit 2 / H7 | ✅（另命中 H3，见下） |
| 14 | 零宽字符 | exit 2 / H8 | ✅ |
| 15 | 片段标点形态变化（`Error Details:`） | exit 2 / H13 | ✅ |
| 16 | JSON 中的孤立代理字符 `\ud800` | 不崩溃 + H8 | ✅ 被净化为 U+FFFD 后由 H8 拒绝 |
| 17 | 完全相同的重复行 | 去重为 1 条 | ✅ additions=1 |
| 18 | 忠实译文（URL + `--no-exe`） | exit 0 | ✅ |
| 19 | 带首尾空白的候选键 | 归一化后写入 | ✅ 写入的是 trim 后的键（见 F4） |
| 20 | `--waive H10` | 留痕并放行 | ✅ `waived` 记录 1 条（小仓库）；真实数据上 `waived=2` |
| 21 | `--provider online` 缺开关 | exit 4 | ✅ |
| 22 | `--provider cmd` 默认低置信 | 隔离、不合并 | ✅ additions=0、quarantined=1 |
| 23 | 候选文件不存在 | exit 4 | ✅ |

补充说明：
- 例 13 的哨兵字符串同时触发 H3（标识符启发式），属**叠加告警**而非误报；
- 例 8 的 "Agent"→"代理" 同时触发 H10（缺"智能体"）与 H11（禁用"代理"），同样可解释；
- 门禁失败时一律不写盘（例 1–17 全部验证 `snapshot` 相等）。

---

## 4. 保真度（占位符/URL/文件名/代码标识/术语）

### 4.1 全量独立复核（不 import 实现）

用**独立实现**的正则（占位符 `{x}/{{x}}/${x}/%s/$1`、URL、文件名、反引号、`--flag`、快捷键、ALLCAPS_IDENT、snake_case、camelCase、缩写白名单）扫描全部 761 条候选：

| 指标 | 值 |
| :--- | :--- |
| 含 token 的候选 | **12 / 761**（共 12 个 token；这批候选以普通句子为主，token 密度低） |
| 独立复算的 token 丢失 | **0** |
| 与 QA 报告一致性 | QA 的 H1–H4 在真实数据上 **0 finding**，与独立复算一致 |
| 术语（8 个 CONTRIBUTING 术语） | 759/761 合规；**2 条缺失** = `credits`（缺「积分」）、`customizations`（缺「自定义配置」） |
| 9 条无中文译文 | 全部是产品名/标识（`Google Chat`、`Gemini 3 Pro Image`、`Flash Lite`…）——**应保留原文**，不是缺陷 |
| 40 条含 ≥2 个英文词的译文 | 逐条核对：产品名、URL、`iframe/Cookie/CSP/PWA`、`Terminal.open`、`repo-a` 等；**均为合理保留**，仅 1 条与 H10 相关（`AI Credits`） |
| 路径/文件名覆盖（探测） | `https://…`、`app.asar` 丢失 → H2 告警 ✅；`~/.env`、`/etc/hosts`、`config.ini` 丢失 → **不告警**（F10，低；本次候选数据里这些路径都被保留） |

### 4.2 两条 H10 是否误报

核对 `CONTRIBUTING.md:54-61`：`Credits -> 积分`、`Customizations -> 自定义配置` 均在术语表中。候选译文：

| 原文 | 译文 | 结论 |
| :--- | :--- | :--- |
| `AI Credits are used when you've exceeded your model quota. Keep track of your current AI Credits in the …` | `当超出模型配额时，将使用 AI Credits。可在以下位置查看当前的 AI Credits…` | 未使用「积分」→ **H10 正确**；应由人改译文或显式 `--waive H10` |
| `Customizations views` | `自定义视图` | 未使用「自定义配置」→ **H10 正确**；同上 |

> 这两条是**候选文件内容问题**，不是工具误报。唯一需要产品/术语负责人拍板的是「AI Credits」是否写成「AI 积分」——不属于验证者单方面裁决的范围。

### 4.3 片段处理与"断裂中文"

独立统计候选中的片段信号（引擎只做整串匹配，片段只能靠客户端把它渲染成独立文本节点）：

| 片段类别 | 行数 | 例子 |
| :--- | ---: | :--- |
| 以 `(` / `,` / `:` 等开放标点**结尾** | 20 | `Image URL:`、`Script return value exceeded maximum size (` |
| 以功能词结尾（the/a/of/to/for/our/your/and/or） | 31 | `Proceed to`、`Clearing cookies and site data for` |
| 以标点**开头**（`?` / `)`） | 4 | `? This action cannot be undone.`、`), use an external SSH session` |
| 强片段信号合计（去重） | **55 / 761（7.2%）** | — |
| 另外：以小写字母开头（疑似从句尾） | +22 | `icon in the URL bar.`、`this time, the website sent back…` |

验证结论：
- **H13 通过**：12 条 `:` 结尾、2 条 `,` 结尾、2 条 `(` 开头、12 条 `...` 结尾全部通过；
- **抽样 82 条中未见"断裂中文"**：片段译文多为可接受的"半句"（如 `在本例中，`、`（例如，`、`请参阅我们的`）；
- **但不能离线自证**：`?` / `)` / `e.g.,` 这类片段是否与相邻文本节点拼成通顺中文，取决于运行时 DOM 结构；设计中已如实标注（§4.2 上下文富化"不解决 text-node 拼接语法"）。抽样里 1 条语序生硬：`For Turn → 针对回合`（若运行时拼成"针对回合 3"尚可，拼成"3 针对回合"则错位）；
- `Clearing cookies and site data for → 正在清除以下站点的 Cookie 和网站数据：` 这类**改写为冒号引导**的译法在整节点渲染时更自然，但 H13 是单向规则（只查原文以 `:` 结尾），不会反对；计入"风格观察"，不计缺陷。

### 4.4 重复与空值

| 输入形态 | 行为 | 评价 |
| :--- | :--- | :--- |
| 同一原文 → 两个不同译文（候选文件重复行） | `prepare()` 先聚合成 H9 blocker → exit 2；`qa.check_batch` 对 proposals 再做 H9 兜底 | ✅ 拒绝 |
| 同一原文 → 相同译文重复行 | 去重，1 条 proposal | ✅ |
| 空 / 纯空白译文 | 被 `FileProvider` / `load_translations` 丢弃，**不产生 H5 finding、报告不计数** | ⚠️ F3：安全但不透明，建议在报告里加 `empty_translations` 计数 |
| 真实候选文件 | 0 条重复行、0 条空译文 | 本次数据无影响 |

---

## 5. `--apply`：幂等、确定性、最小 diff、回滚

### 5.1 隔离副本 apply（copyA / copyB，`--waive H10`）

| 观测 | copyA | copyB |
| :--- | :--- | :--- |
| 退出码 | 0 | 0 |
| QA | pass，waived=2 | pass，waived=2 |
| 合并 | 761 additions，2,816 → **3,577** 条 | 同 |
| 构建 | `build.py --no-exe` exit 0，回读 **engine_entries=3577 = expected**，`verified=true` | 同 |
| 词典 sha256 | `9d95dbf9…` | `9d95dbf9…`（**相同**） |
| 引擎 sha256 | `842e5681…` | `842e5681…`（**相同**） |
| patcher sha256 | `6105087d…` | `6105087d…`（**相同**） |
| 耗时 | 244 ms | 同量级（未单独计时） |

产物结构（独立解析，非 import 实现）：

| 检查 | 结果 |
| :--- | :--- |
| 原 2,816 个键的顺序 | 完全保留 |
| 原有键的值被改写 | **0** |
| 新增键集合 | 与 761 条候选源**完全一致** |
| 新增值 ≠ 候选译文 | **0**（没有静默重译） |
| 新增键顺序 | UTF-8 codepoint 升序 ✅ |
| CRLF / 结尾换行 | 3579 个 CRLF、**0 个裸 LF**、以 CRLF 结尾 ✅ |
| 全文件重序列化 | 与 `json.dumps(indent=2)`+CRLF 结果**字节全等**（这是最小 diff 的根因） |
| 引擎内嵌词典 | 与 `locales/zh-CN.json` **对象完全相等**（3577 条，不只是条数相等） |
| patcher 内嵌 | `EMBEDDED_ENGINE_CODE` 里解析出的词典 == 文件；`EMBEDDED_ZH_JSON` == 文件（3577）；patterns=180 |
| pre-merge 备份 | 与 apply 前原词典 **sha256 相同**（193,837 字节） |
| 临时文件残留 | 无 `.l10n-tmp` |

与主仓库词典的差异：`git diff --no-index --numstat` → **762 insertions(+) / 1 deletion(-)**（末行补逗号），与 t3 声称一致。

### 5.2 幂等（copyA 二次 apply）

```
exit 0；plan: additions=0, already_present=761；build.ran=false
dictionary/engine/patcher 三个 sha256 全部不变
```

### 5.3 失败回滚（三个场景）

| 场景 | 构造 | 结果 |
| :--- | :--- | :--- |
| ① 构建失败 | copyD 删除 `engine/engine_template.js` | exit **4**；`build.exit=1`；`rollback.performed=true, ok=false`；词典 **sha256 复原**（`793905e9…`）；manifest 落盘 |
| ② 构建"成功"但未重生成（回读条数不符） | copyE 用 `fake_build.py`（exit 0 但不写产物）+ 预置 2,816 条引擎 | exit **4**；`build.reason="generated engine embeds 2816 entries, expected 3577"`；`rollback.ok=true`（回滚后重建 2816 校验通过）；词典复原 |
| ③ 部分写入 + 回滚重建再失败（残留窗口） | copyG 用 `partial_build.py`（首次写引擎后 exit 1；再次调用直接 exit 1） | exit **4**；词典复原为 2,816，但引擎仍内嵌 **3,577** → **词典/生成物不一致**（F7，低）；manifest 记录 rollback.ok=false |

> 场景 ③ 说明：`rollback()` 只恢复词典并尝试重建；若重建也失败，**不会**自动恢复生成物到"词典对应的版本"。这是设计内的已知边界（"生成物只经 build.py"），但建议在 manifest/报告中显式标注"生成物可能过期"，或在 exit 4 时给出人工修复命令。

### 5.4 `--no-build` 与下次 apply 自动修复

copyF：`--apply --no-build` → exit 0、词典 3,577、**引擎不存在**（如实报告 `build.ran=false`）；
再跑 `--apply` → `plan.additions=0`、`rebuilt_stale_artifacts=true`、`build.engine_entries=3577`、`verified=true`，exit 0。

### 5.5 `merge` 子命令

copyA 上 `merge` dry-run：exit 0，additions=0、already_present=761，**未写任何文件**（整树 sha256 不变）。
F5（info）：`merge` 的 dry-run 报告里**没有 `build` 键**（`release` 的 dry-run 有），机器可读 schema 不一致；不影响安全语义。

---

## 6. 生成物：只经 `build.py` 重建 + 基线门禁

### 6.1 代码面无直写

`grep` 结论：`scripts/localization/*.py` 对磁盘的写入只有两类——`locales/zh-CN.json`（merge）与 `pre-merge/zh-CN.json`（备份）；
对 `engine/ag_localization_engine.js` 只有**读取**（回读条数）；没有任何代码手写 `scripts/patcher.py`。
管线的重建路径唯一：`subprocess.run([sys.executable, <repo>/scripts/build.py, "--no-exe"])`。

### 6.2 可复现性（强证据）

在 pristine 副本 copyC（词典 2,816 条、未 apply）直接跑 `python scripts/build.py --no-exe`，产物与主仓库生成物比较：

| 文件 | copyC 重建成品 | 主仓库 | 一致 |
| :--- | :--- | :--- | :--- |
| `engine/ag_localization_engine.js` | `ce47b0b9…` | `ce47b0b9…` | ✅ |
| `scripts/patcher.py` | `2d148c82…` | `2d148c82…` | ✅ |

即：主仓库的两个生成物就是"当前词典 + `build.py`"的确定性函数值，**没有手改痕迹**。

### 6.3 主仓库基线门禁

```bash
python scripts/build.py --no-exe          # exit 0，耗时 191 ms
git diff --exit-code -- scripts/patcher.py engine/ag_localization_engine.js   # 在工作区仍有 Phase 0 未提交改动时必然 exit 1（见下）
```

- 运行 `build.py` 前后比较 `git diff` 全量文本与 `git status`：**完全不变**（生成物是幂等的）；
- 用**临时索引**复现 CI（四个 Phase 0 文件同批"提交"后）：

```bash
GIT_INDEX_FILE=.pytest_tmp/verify/ci.index git read-tree HEAD
GIT_INDEX_FILE=.pytest_tmp/verify/ci.index git add -A
python scripts/build.py --no-exe
GIT_INDEX_FILE=.pytest_tmp/verify/ci.index git diff --exit-code -- scripts/patcher.py engine/ag_localization_engine.js   # exit 0
GIT_INDEX_FILE=.pytest_tmp/verify/ci.index git diff --exit-code -- locales/zh-CN.json README.md README_EN.md           # exit 0
```

结论：**CI 的"生成物一致性"门禁在"词典+生成物+README 同批提交"这一等价条件下为绿**；真实索引/历史未被触碰（`git status` 仍是 17 项，与验证开始时一致）。
README 计数门禁（`.github/workflows/release.yml:59-82` 逐字复刻）：`[+] README counts match locales: 2816 entries / 180 rules`，exit 0。

### 6.4 apply 不维护 README（F6）

在 copyA（已 apply 到 3,577）放入 README 后跑同一门禁 → **exit 1**：

```
[!] README.md: advertised count '3,577' missing (actual: 3577 entries / 180 rules)
[!] README.md: stale entry count '2,816' (actual: 3,577)
```

即：`release --apply` 只保证"词典 + 生成物"一致，**不更新 README 中的计数**；对真实仓库全量 apply 后，CI 的 README 门禁会红。这是流程缺口（MVP §12.2 已列为下一步），**不是本次实现的隐藏 bug**，但落地前必须处理。

---

## 7. 安全边界

| 检查 | 结果 |
| :--- | :--- |
| `scripts/localization/` 与 `scripts/localize.py` 的网络 import | **0**（socket/ssl/urllib/http/requests/aiohttp/httpx/ftplib/smtplib 全部无） |
| dry-run 时 `socket.socket/create_connection/getaddrinfo` 被 patch 成爆炸 | 仍 exit 2（门禁失败，与网络无关），**0 次调用**（`offline_check.py` 输出 `EXIT=2 SOCKET_ATTEMPTS=0`） |
| `--provider online` | 缺任一开关 → exit 4（分别验证三个组合）；双开关齐备 → 仍报 `stub, no network backend`，exit 4 |
| 外部 `--provider-cmd` | 默认 `confidence=low` → 提案全部 `quarantined`（reason=`confidence:low`），**不合并**；exit 0 |
| 客户端目录/patcher 调用 | 代码中无 `%APPDATA%`/`Application Support`/`Antigravity` 路径，无 `patcher patch/restore` 调用（仅 docstring 提到未来工作） |
| 生成物直写 | 无（§6.1） |
| 输入净化 | 孤立代理字符在入口被替换为 U+FFFD 并交由 H8 拒绝，**整轮不崩溃**（黑盒用例 16） |

---

## 8. 测试与语法门禁

### 8.1 语法

```bash
python -m py_compile scripts/localize.py scripts/build.py scripts/extract_untranslated.py scripts/patcher.py scripts/localization/*.py   # exit 0
node --check engine/engine_template.js      # exit 0
node --check engine/ag_localization_engine.js  # exit 0
```

### 8.2 pytest

| 命令 | 结果 |
| :--- | :--- |
| `python -m pytest tests/test_localize_mvp.py -q` | **46 passed**，1.82 s |
| `python -m pytest -q`（整套） | **127 passed / 1 failed / 34 errors**，7.04 s |

**1 failed + 34 errors 全部是环境假阴性，不是代码问题**。证据链：

1. 34 个 error 全部发生在 pytest 的 `tmp_path` fixture 创建阶段：
   `PermissionError: [WinError 5] 拒绝访问。: 'C:\Users\win\AppData\Local\Temp\dsh-G24tuU\pytest-of-win'`；
2. 唯一 failure 是 `tests/test_engine.py::test_escape_dollar_is_not_a_noop`，失败点是 `tempfile.TemporaryDirectory()` 下 `check.js` 的 `PermissionError`，同样不是断言失败；
3. **对照实验**（关键）：

   ```bash
   python -c "
   import os, shutil
   base='.pytest_tmp/mode_probe'; shutil.rmtree(base, ignore_errors=True); os.makedirs(base)
   os.mkdir(base+'/d700', 0o700); os.mkdir(base+'/d755')
   for label,d in (('mode 0o700',base+'/d700'),('default mode',base+'/d755')):
       try:
           open(d+'/x.txt','w').write('ok'); print(label,'-> write OK')
       except Exception as e: print(label,'->',type(e).__name__)
   "
   # mode 0o700 -> PermissionError        （pytest tmp_path / TemporaryDirectory 用的正是 0o700）
   # default mode -> write OK
   ```

   即：**不是 `%TEMP%` 的错，而是本沙箱的 Windows ACL 拒绝任何 `mode 0o700` 目录的写入**（`chmod` 也返回 `WinError 5`）。`tests/test_localize_mvp.py` 之所以绿，是因为它在 `<repo>/.pytest_tmp/` 下用默认 mode 自建临时仓库。
4. 结论：这 35 个 red 与本次 MVP 无关，也不建议通过改系统权限/ACL 绕过（本会话已禁止提权）；在普通开发机/GitHub Actions 上应全绿（CI 一直是 `pytest -q`）。
   > 诚实声明：我**没有**在普通环境复跑整套测试，因此"在 CI 上全绿"是推断而非实测。

---

## 9. 抽样人工复核（82 条，10.8%）

### 9.1 抽样方法

固定种子 `20261124`；规则：全部片段类（`:`/`,`/`...`/`(`）∪ 全部无中文 ∪ 全部短串（≤8 字符）∪ 最长 10 条 ∪ 全部含 token ∪ 15 条随机（去重后 82 条）。
逐条给出 `SRC/TGT` 与上下文（kind/prop/path:line 可回溯），清单见 `.pytest_tmp/verify/out/review_sample.txt`。

### 9.2 结果

| 分类 | 条数 | 占比 | 说明 |
| :--- | ---: | ---: | :--- |
| 无问题 | 75 | 91.5% | 语义与风格均可直接发布 |
| 风格小瑕（术语/一致性/直译） | 5 | 6.1% | `Agent ID: → 智能体ID：`（缺空格）；`Set up → 设置`（与 Settings 同形，H22 未实现）；`bundle → 捆绑包`（直译）；`Artifacts → Artifact/Artifacts`（单复数不一致） |
| 可读性生硬（语义仍正确） | 2 | 2.4% | `For Turn → 针对回合`（片段语序）；`what to do instead → 应该改做什么`（口语化） |
| **语义错误（信息丢失/错译）** | **0** | **0%** | — |
| 占位符/标识/术语违规 | 0 | 0% | 与全量复算一致 |

- **语义准确率（点估计）= 100%（0/82；若两类"生硬"也算不通过则为 97.6%）**；
- 82 条 0 错误的 95% 置信上限约 **3.6%**（Clopper-Pearson），因此"整个 761 条集合语义错误率 ≤3.6%"是可辩护的弱结论，**不能**外推为"零错误"；
- 失败分类分布：术语/直译 3 条（`Set up`、`bundle`×2）、单复数 1 条（`Artifact`）、空格 1 条（`智能体ID`）、片段语序 1 条（`For Turn`）、口语化 1 条（`应该改做什么`）。

### 9.3 全量启发式（补充）

| 检查 | 结果 |
| :--- | :--- |
| 译文与原文逐字相同 | 9 条，全部是无中文的产品名/标识（合理） |
| 译文含 ≥2 个英文词 | 40 条，逐条核对均为产品名/技术词/URL/标识（合理保留） |
| 共享译文的"不同原文" | 7 组，均为大小写变体同源（`Insert in Terminal`/`Insert in terminal`），**不是语义相反的合并**（H22 风险实测很低） |
| 词典 2,816 条中无中文的译文 | 14 条（H16 未实现，属已知覆盖缺口，非新缺陷） |

---

## 10. 覆盖率数字（汇总）

| 维度 | 数值 |
| :--- | :--- |
| 候选→译文覆盖 | 761 / 761 = **100%** |
| 候选可通过门禁（无需豁免） | 759 / 761 = **99.7%**（2 条 H10） |
| 自动合并成功率（隔离副本） | 761 / 761 = **100%**（`--waive H10` 后） |
| token 保真（独立复算） | 12 / 12 = **100%**（含 token 的候选仅 12 条） |
| 术语合规 | 759 / 761 = **99.7%** |
| QA 规则覆盖 | 15 / 23 = **65.2%**；blocker 规则 10 / 13 = **76.9%**（缺 H17–H19，属 `patterns.json` 范围外） |
| 测试 | MVP 46/46；整套 127/162（35 个环境假阴性） |
| 人工复核 | 82 / 761 = **10.8%**；语义准确率 100%（0 语义错误），无瑕疵 91.5% |
| 候选来源覆盖 | `language_server.exe` 744 条（97.8%）、`app.asar` 17 条（2.2%）；界面文本 601、UI 属性 160 |
| 词典规模变化 | 2,816 → 3,577（**+27.0%**） |
| 端到端耗时（本机） | dry-run ≈105 ms；全量 apply（含重建+校验）≈244 ms |

---

## 11. 发现清单（均非阻塞；未修改实现）

| ID | 严重级别 | 位置 | 问题 | 证据 | 建议 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1** | 文档（低） | `docs/auto-localization-mvp.md:16` | 写"770 行的候选集"，实际 761（同文 §1/§10 均为 761） | `grep -n 770 docs/auto-localization-mvp.md` | reviewer/repair 改文档，或改为"约 760 行" |
| **F2** | 中 | `scripts/localization/providers.py:182`（`shlex.split`） | `--provider-cmd "D:\miniconda3\python.exe script.py"` 中反斜杠被 POSIX 模式吃掉 → `provider command not found: D:miniconda3python.exe`；Windows 绝对路径不可用（正斜杠可绕过） | 复现命令见附录 A-9 | 改 `shlex.split(cmd, posix=False)` 并处理引号，或改用 list/`--provider-cmd-json`；默认 provider 不受影响 |
| **F3** | 低 | `providers.FileProvider` / `candidates.load_translations` | 空/纯空白译文被静默丢弃：不产生 H5、报告无计数，运维看不到"有译文条目被跳过了多少" | 黑盒用例 1 | 在报告加 `empty_translations` 计数（不一定要 fail） |
| **F4** | 低（信息） | `pipeline.prepare` + `collect_proposals` | H6（键带首尾空白）在提案链路**不可达**：provider 先 `strip()` 再交给 QA；带空白的候选键被静默归一化（本次无此类数据）。行为本身合理，但规则覆盖是名义的 | 黑盒用例 19：`"  Padded label  "` 被写为 `Padded label`，无 H6 | 文档说明这是一条"仅词典模式/直接 entry 可触发"的规则，或对原始键带空白单独告警 |
| **F5** | 低（信息） | `pipeline.run_merge` | `merge` 的 dry-run 报告缺 `build` 键，`release` 的 dry-run 有；同族命令 schema 不一致 | `merge` dry-run 输出 keys | 统一报告 schema |
| **F6** | 中（流程） | `pipeline.run_release`（无 README 更新） | 真实仓库全量 `--apply` 后 README 计数仍是 2,816 → CI 的 README 门禁必红 | copyA 放 README 后 `readme_gate.py` exit 1 | apply 后自动更新 README 计数，或让门禁改为"README ≥ 词典条数"，或把 README 更新纳入同批提交脚本 |
| **F7** | 低 | `pipeline.rollback` | 构建部分写入且回滚重建再失败时：词典已回滚、生成物残留新条数，树不一致（exit 4 有记录，但无自动二次恢复） | copyG 实验：词典 2,816 / 引擎内嵌 3,577 | 在 exit 4 报告/manifest 显式标注"生成物可能过期"并打印人工修复命令 |
| **F8** | 低（信息） | `cli --waive` | 未知规则（如 `--waive H99`）被静默接受、静默无效（失败方向安全：仍然 fail） | 黑盒实验：gate 仍 fail | 校验 `--waive` 规则名，未知值报 exit 4 |
| **F9** | 风险（信息） | 引擎整串匹配 + 候选片段 | 55/761（7.2%）是强片段信号（20 条开放标点结尾、31 条功能词结尾、4 条标点开头），H13 只保证标点形态，**不保证拼接后中文通顺**；离线无法自证 | §4.3；抽样未发现断句错误 | 归入 Phase 4 真机验证；报告中保留片段标记 |
| **F10** | 低 | `scripts/localization/qa.py` H2（`_FILE_EXTENSIONS` 白名单 + `https?://`） | 路径保真只覆盖固定扩展名与 http(s)：探测 `~/.env`、`/etc/hosts`、`config.ini` 丢失译文时**不告警**（`mailto:`/`file://` 同理） | `h2_probe.txt`：三个用例 exit 0、rules=[]；`https://…` 与 `app.asar` 用例 exit 2、H2 | 扩展名白名单补 `env/ini/cfg/conf/properties/sqlite/pem/key/log`，或对"形如路径的 token"统一告警；当前数据未出现丢失，故低 |
| — | 文档已声明 | `docs/auto-localization-mvp.md` §11 | 提取器未重写、patterns 未合并、引擎计数器/真机验证未做、在线 provider 仅 stub、真实仓库未 apply | 与实测一致 | 属范围外 deferred，**不是缺陷** |

---

## 12. MVP 范围内已验证 / 范围外未实现

### 12.1 范围内（本次独立验证通过）

- 一条命令 dry-run（默认不写盘、零网络、确定性、机器可读 JSON、退出码语义）；
- provider 链（file > tm > cmd 低置信隔离 > online 拒绝）与 `--translations` overlay；
- QA 门禁 15 条规则的拒绝能力与误报情况（23 个黑盒用例 + 761 条真实数据）；
- 合并（保序、稳定追加、最小字节 diff、CRLF、原子写、pre-merge 备份）；
- 重建（只经 `build.py`）与回读校验、失败自动回滚；
- Phase 0 基线（生成物 2,816 / README 2,816 / CI 门禁等价复现）；
- 测试与语法门禁（46 MVP 测试、py_compile、node --check）。

### 12.2 范围外（**deferred，不计缺陷**）

- Phase 1：提取器重写 / 探针 / D1 基线（SNR 0.21% → ≥30%）；
- Phase 2 尾巴：`patterns.json` 规则生成与合并、H17–H20；
- Phase 3：在线 provider 的真实实现（脱敏、审计、预算）；
- Phase 4：引擎命中/未命中计数器、`patch --dry-run`、客户端快照与自动回滚、真机 V3 验证；
- Phase 5：跨 run 指标库（M16–M20）、成本与抽样运营。

---

## 13. 诚实声明（验证者自述）

1. **未在真实仓库执行 `--apply`**：按 t3 的说明与任务约定，apply 语义在 7 个隔离副本中验证；主仓库词典 sha256 全程 `793905e9…`（2,816 条），`git status` 与验证开始时一致（17 项，含先前已存在的 Phase 0 改动）。
2. **未验证真实客户端**：没有对任何已安装的 Antigravity 执行 patch/restore，也没有运行时命中率数据（需要 Phase 4 的引擎计数器，MVP 约定不改生成物）。
3. **抽样是我本人判读**（82 条），不是第三方盲评；分类边界（尤其"风格 vs 生硬"）存在主观性，已在 §9.2 给出原始清单路径。
4. **pytest 未取得全绿基线**：35 个 red 是沙箱 `mode 0o700` ACL 假阴性（有对照实验），但"CI 上全绿"是推断。
5. **片段拼接正确性不可离线自证**：H13 只覆盖标点形态；"断裂中文"需要真机/运行时 DOM 才能判定。
6. 本报告与验证脚本**没有修改**任何实现代码、词典、生成物、README、现有文档；新增的只有本报告和 `.pytest_tmp/` 下的临时验证脚本（gitignored）。`build.py` 重写生成物后字节不变（69 文件快照全等）。
7. 未获得同源 PR 的第二次独立复核；若需要，建议由未参与 t3 的成员按附录 A 重跑关键项（§2.3、§5.3、§6.2、§8.2）。

---

## 附录 A：复现命令（自包含）

以下命令均在仓库根目录执行；`$repo` 指仓库根。A-1/A-4–A-10 为 bash 语法（Windows 可用 Git Bash/WSL；
PowerShell 等价物见 `.pytest_tmp/verify/*.py`），A-8 中的 `export` 是 bash 写法。

**A-1 全仓零写盘**
```bash
python .pytest_tmp/verify/snapshot.py "$repo" .pytest_tmp/verify/before.json
python scripts/localize.py release --json > /dev/null      # 或任意 dry-run
python .pytest_tmp/verify/snapshot.py "$repo" .pytest_tmp/verify/after.json
python -c "
import json
a=json.load(open('.pytest_tmp/verify/before.json'))['files']
b=json.load(open('.pytest_tmp/verify/after.json'))['files']
print('added:', sorted(set(b)-set(a)), 'removed:', sorted(set(a)-set(b)),
      'changed:', sorted(k for k in set(a)&set(b) if a[k]!=b[k]))
"
```
> 快照排除 `.git/`、`.agent-teams/`、`.workbuddy/`、`.pytest_tmp/`、`__pycache__/` 等（脚本内硬编码，见 `.pytest_tmp/verify/snapshot.py`）。

**A-2 dry-run 与确定性**
```bash
python scripts/localize.py release --json --run-id fixed > /tmp/d1.json; echo $?
python scripts/localize.py release --json --run-id fixed > /tmp/d2.json
cmp /tmp/d1.json /tmp/d2.json && echo "byte-identical"
```

**A-3 门禁矩阵**
```bash
python .pytest_tmp/verify/edge_cases.py     # 23 cases, 0 expectation failures
```

**A-4 隔离副本 apply（幂等/确定性）**
```bash
mkdir -p /tmp/l10n/{scripts,engine,locales}
cp scripts/build.py /tmp/l10n/scripts/; cp engine/engine_template.js /tmp/l10n/engine/
cp locales/zh-CN.json locales/patterns.json /tmp/l10n/locales/
cp untranslated_candidates.json /tmp/l10n/
python scripts/localize.py release --repo-root /tmp/l10n --candidates /tmp/l10n/untranslated_candidates.json \
  --apply --waive H10 --json --run-id r1        # exit 0, engine_entries=3577
python scripts/localize.py release --repo-root /tmp/l10n --candidates /tmp/l10n/untranslated_candidates.json \
  --apply --waive H10 --json --run-id r2        # additions=0，三份 sha256 不变
git diff --no-index --numstat locales/zh-CN.json /tmp/l10n/locales/zh-CN.json   # 762 / 1
```

**A-5 产物结构（独立解析）**
```bash
python .pytest_tmp/verify/verify_artifacts.py /tmp/l10n .   # 结构、CRLF、键序、内嵌词典
python .pytest_tmp/verify/verify_patcher.py  /tmp/l10n      # patcher 内嵌 engine/词典
```

**A-6 回滚三场景**（每次都从一个**未 apply** 的 pristine 副本开始）
```bash
mk_pristine() {   # 最小可用仓库（与 A-4 相同，不含候选的已应用状态）
  mkdir -p "$1"/{scripts,engine,locales}
  cp scripts/build.py "$1/scripts/"
  cp engine/engine_template.js "$1/engine/"
  cp locales/zh-CN.json locales/patterns.json "$1/locales/"
  cp untranslated_candidates.json "$1/"
}
mk_pristine /tmp/l10nD; mk_pristine /tmp/l10nE; mk_pristine /tmp/l10nG
SHA_BEFORE=$(sha256sum /tmp/l10nD/locales/zh-CN.json | cut -d' ' -f1)

# ① 构建失败：删掉模板，build.py 必然非 0
rm /tmp/l10nD/engine/engine_template.js
python scripts/localize.py release --repo-root /tmp/l10nD --candidates /tmp/l10nD/untranslated_candidates.json \
  --apply --waive H10 --json; echo $?          # 4；rollback.performed=true, ok=false
sha256sum /tmp/l10nD/locales/zh-CN.json         # == $SHA_BEFORE

# ② 回读条数不符：用 fake_build.py（exit 0 但不写产物）+ 预置 2,816 条引擎
cp .pytest_tmp/verify/fake_build.py /tmp/l10nE/scripts/build.py
cp engine/ag_localization_engine.js /tmp/l10nE/engine/
python scripts/localize.py release --repo-root /tmp/l10nE --candidates /tmp/l10nE/untranslated_candidates.json \
  --apply --waive H10 --json; echo $?          # 4；reason="embeds 2816, expected 3577"；rollback.ok=true

# ③ 部分写入 + 回滚重建再失败（残留窗口）
cp .pytest_tmp/verify/partial_build.py /tmp/l10nG/scripts/build.py
python scripts/localize.py release --repo-root /tmp/l10nG --candidates /tmp/l10nG/untranslated_candidates.json \
  --apply --waive H10 --json; echo $?          # 4；词典 2816 / 引擎仍嵌 3577（F7）
```

**A-7 生成物只经 build.py（可复现性）**
```bash
# 干净副本：只带 build.py + engine_template.js + 当前词典/patterns
mkdir -p /tmp/pristine/{scripts,engine,locales}
cp scripts/build.py /tmp/pristine/scripts/
cp engine/engine_template.js /tmp/pristine/engine/
cp locales/zh-CN.json locales/patterns.json /tmp/pristine/locales/
(cd /tmp/pristine && python scripts/build.py --no-exe)     # exit 0
sha256sum /tmp/pristine/engine/ag_localization_engine.js /tmp/pristine/scripts/patcher.py
sha256sum engine/ag_localization_engine.js scripts/patcher.py     # 两两相同
```

**A-8 CI 等价门禁（临时索引，不动真实索引）**
```bash
export GIT_INDEX_FILE=$PWD/.pytest_tmp/verify/ci.index
git read-tree HEAD && git add -A
python scripts/build.py --no-exe
git diff --exit-code -- scripts/patcher.py engine/ag_localization_engine.js   # 0
git diff --exit-code -- locales/zh-CN.json README.md README_EN.md             # 0
unset GIT_INDEX_FILE
python .pytest_tmp/verify/readme_gate.py                                      # 2816 entries / 180 rules
```

**A-9 F2 复现（`--provider-cmd` 反斜杠）**
```bash
python -c "import shlex,sys; print(shlex.split(sys.executable + ' x.py'))"
# ['D:miniconda3python.exe', 'x.py'] -> provider command not found
```

**A-10 测试与语法**
```bash
python -m pytest tests/test_localize_mvp.py -q     # 46 passed
python -m pytest -q                                # 127 passed / 1 failed / 34 errors（见 §8.2）
python -m py_compile scripts/localize.py scripts/build.py scripts/localization/*.py
node --check engine/engine_template.js && node --check engine/ag_localization_engine.js
```

**A-11 抽样与统计**
```bash
python .pytest_tmp/verify/sample_for_review.py .   # 82 条复核样本（固定种子）
python .pytest_tmp/verify/stats.py                 # 覆盖率汇总（§10）
python .pytest_tmp/verify/fragments.py             # 片段统计（§4.3）
python .pytest_tmp/verify/h2_probe.py              # 路径/扩展名覆盖探测（F10）
python .pytest_tmp/verify/offline_check.py .       # socket 拦截下的 dry-run（§7）
```

---

## 附录 B：关键证据索引

| 结论 | 证据文件（`.pytest_tmp/verify/out/`） |
| :--- | :--- |
| dry-run 报告 | `dry1.json`、`dry2.json`、`dry3.json`、`human_dryrun.txt` |
| 零写盘 | `baseline.json`、`after_dryrun.json`、`after_all.json` |
| 门禁矩阵 | `edge_cases.txt` |
| apply / 幂等 / 回滚 | `applyA1.json`、`applyA2.json`、`applyB1.json`、`applyD1.json`、`applyE1.json`、`applyF1.json`、`applyF2.json`、`applyG1.json` |
| 产物结构 | `artifacts.txt`、`patcher.txt` |
| 词典 QA / README / 门禁 | `qa_dict.json`、`qa_dict_strict.json`、`pytest_full.txt`、`pytest_writable_tmp.txt` |
| 安全 / 路径覆盖 | `offline_check.txt`、`h2_probe.txt` |
| 抽样与统计 | `review_sample.txt`、`residue.txt`、`stats.txt`、`fragments.txt` |

（该目录被 `.gitignore` 忽略；如需长期保留，请在合并前另存。）
