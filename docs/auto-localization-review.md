# 自动汉化方案、原型与验证证据：独立评审报告（t5）

> 评审对象：`docs/auto-localization-baseline.md`（t1）、`docs/auto-localization-design.md`（t2）、
> `docs/auto-localization-mvp.md` + `scripts/localize.py` + `scripts/localization/` + `tests/test_localize_mvp.py`（t3）、
> `docs/auto-localization-verification.md`（t4）。
>
> 评审方式：**只读评审，不修改代码/词典/生成物**。所有关键结论都重新独立复跑（见 §2、附录 A），
> 不直接采信 t1–t4 的自述；无法在本环境复跑的部分在 §12 显式声明。
>
> **verdict：PASS（0 个阻塞项）**。范围诚实、数据安全、基线门禁、零网络、回滚语义均成立；
> 发现 3 个中等级与 10 个低/信息级问题，**均不改变「可行性结论」**，但其中 2 条（RF-01、RF-02）
> 必须在「对真实仓库执行 `--apply` / 对外宣称可用」之前以**文档或最小补丁**处理。

---

## 0. 结论摘要

| 评审维度 | 结论 | 关键证据（本报告复跑） |
| :--- | :--- | :--- |
| 范围诚实性 | ✅ 通过 | MVP 只声称「Phase 0 部分 + Phase 2 离线纵切」；Phase 1/3/4/5 与 probe、引擎计数器、`patch --dry-run`、客户端快照、在线 LLM、真机 V3 均明确标「未做」（§3） |
| 文档一致性 | ⚠️ 有小瑕疵 | `docs/auto-localization-mvp.md:16` 写 770、实际 761（t4 已记为 F1，属实）；另有 1 处「豁免留痕到 manifest.json」与实现不符（RF-04） |
| 数据安全 | ✅ 通过 | 主仓库词典 sha256 `793905e9…`、2,816 条，与 t4 声称一致；无 `.l10n/`；隔离副本 2,816→3,577 完全可复现（§5） |
| 基线门禁 | ✅ 通过 | 生成物内嵌 2,816、README 门禁 `2816 entries / 180 rules` exit 0；pristine 副本重建的引擎/patcher 与仓库产物**字节相同**（`ce47b0b9…`/`2d148c82…`），证明只经 `build.py`（§6） |
| 门禁有效性 | ✅ 基本通过 | 2 条 H10 核对 `CONTRIBUTING.md:54-62` 为**真术语缺失**；`--waive` 在报告与 `qa.json` 留痕；`--provider cmd` 默认 low→隔离。另发现 H21 有覆盖漏洞（RF-03，中） |
| 隐私/安全 | ✅ 通过 | `scripts/localization/` 零网络 import；online 仅 stub 且三重拒绝；写入面只有词典/备份/run 产物；回滚先备份后原子写（§8） |
| 测试充分性 | ✅ 基本通过 | 本机 `pytest tests/test_localize_mvp.py -q` → 46 passed / 1.79 s；全套 127 passed / 1 failed / 34 errors（失败均为沙箱 ACL，与 t4 一致）。**但 H11/H13/H23 无提交内夹具**（RF-07） |
| 对用户问题的证据支撑 | ✅ 负向结论强、正向结论需带保留 | 「全 UI 100% 不可达」有代码级硬证据（B9/B10/B1–B5）；「流水线可自动化/≤30min」的机械半段已实测，翻译覆盖半段（TM 60–85%）**仍未实测**（§10） |

**一句话**：这套交付在它自己声明的范围内是**可复现、可回滚、确定性的**，并且没有把「Phase 0 + Phase 2 纵切」吹成「无人汉化」；阻塞项为 0。剩下的问题集中在「真实仓库 apply 后的流程闭环（README）」与「可选 provider 的 Windows 路径」两处，属**已知限制级**，不需要扩大到 Phase 1/4。

---

## 1. 评审立场与独立性

1. **未复用 t4 的脚本**：t4 的验证脚本在 `.pytest_tmp/verify/`（gitignored）。本次评审只在
   `.pytest_tmp/review/` 新建独立副本，用文档化的 CLI 命令复跑关键项，评审结束后删除该目录。
2. **不 import 实现做断言**：除阅读代码外，QA/合并/回滚结论均通过 `python scripts/localize.py …`
   子进程 + 独立解析 JSON/字节完成。
3. **未修改任何受版本控制的文件**：评审前后 `git status --porcelain` 均为 17 项
   （7 个已修改 + 10 个未跟踪，与 t4 结束时一致）；词典 sha256 全程 `793905e9…`。
4. **不重复 t4 的抽样人工复核**（82 条语义判读）：那是主观判读，重做无增量价值；本报告只复核其
   **可机器验证的部分**（token 统计、术语、产物结构、门禁、回滚、测试计数）。

---

## 2. 独立复现矩阵

| # | 声称（来源） | 本次复跑命令 | 观测 | 判定 |
| :- | :--- | :--- | :--- | :--- |
| A1 | 候选 761 条、词典 2,816 条（t3/t4） | `python -c "len(json.load(...))"` | 761 / 2,816 | ✅ |
| A2 | dry-run 默认、exit 2、2 个 H10、759 可加 2 隔离（t3 §1） | `python scripts/localize.py release --json` | exit 2；`file=761, tm=1`；blockers=2 均 H10；`plan.additions=759, quarantined=2` | ✅ |
| A3 | dry-run 零写盘（t4 §2.3） | 观察仓库 `git status`、`.l10n`、词典 sha | 无 `.l10n/`；sha 不变；git status 不变 | ✅ |
| A4 | 隔离副本 `--apply` → 2,816→3,577、verified（t3/t4 §5） | `localize release --repo-root .pytest_tmp/review --apply --waive H10 --json` | exit 0；`merge 2816→3577`；`build.engine_entries=3577, verified=true` | ✅ |
| A5 | 二次 apply 0 新增、三份 sha 不变（t3/t4 §5.2） | 同 A4 再跑一次 | exit 0；`additions=0, already_present=761`；词典 sha 前后相同 | ✅ |
| A6 | 最小 diff 762/1、CRLF、无裸 LF（t3/t4 §5.1） | `git diff --no-index --numstat` + 字节统计 | 762 insertions / 1 deletion；3579 CRLF、0 裸 LF、以 CRLF 结尾 | ✅ |
| A7 | 生成物只经 build.py、可复现（t3 §7 / t4 §6.2） | pristine 副本跑 `scripts/build.py --no-exe`，比对 sha | 引擎 `ce47b0b9…`、patcher `2d148c82…` 与仓库**完全相同** | ✅ |
| A8 | README 计数门禁绿（t3 §7） | 逐字复刻 `.github/workflows/release.yml:59-82` | `[+] README counts match locales: 2816 entries / 180 rules`，exit 0 | ✅ |
| A9 | 生成物内嵌 2,816（t3 §7） | 解析 `engine/ag_localization_engine.js` 哨兵块 | `len(embedded)=2816` | ✅ |
| A10 | MVP 测试 46 passed（t3/t4） | `python -m pytest tests/test_localize_mvp.py -q` | **46 passed**，1.79 s | ✅ |
| A11 | 全套 127/1/34，red 为沙箱 ACL（t4 §8.2） | `python -m pytest -q` | 127 passed / 1 failed / 34 errors；`FAILED tests/test_engine.py::test_escape_dollar_is_not_a_noop - PermissionError`、`ERROR tests/test_asar.py… - PermissionError` | ✅（归因一致） |
| A12 | 语法门禁（t3 §10） | `python -m py_compile …`；`node --check` ×2 | exit 0 / 0 / 0 | ✅ |
| A13 | 包内零网络（t3 §6 / t4 §7） | `grep -E '^(import|from) (socket|urllib|http|requests|ssl|…)' scripts/localization` | 无匹配；`providers.py` 只有 `subprocess`（本地进程） | ✅ |
| A14 | 2 条 H10 是真术语缺失（t4 §4.2） | 读候选译文 + `CONTRIBUTING.md:52-62` 术语表 | `Credits→积分`、`Customizations→自定义配置` 均在册；两条译文确实没用到 | ✅ 非误报 |
| A15 | 基线统计（t1/t2 复核数字） | 独立复算 | 规则 180；大小写碰撞 96 组 / 216 键 / 冗余 120；>120 字符键 72；无空格键 411；无中文译文 14 | ✅ |
| A16 | 引擎硬边界 B9/B10（t1） | 读 `engine/engine_template.js:212-214` | `if (/[一-鿿]/.test(trimmed)) return null;`、`if (trimmed.length > 500) return null;` | ✅ |

> 结论：t3/t4 中所有**可机器验证**的数字与语义均复现成功，未发现夸大或造数。

---

## 3. 范围诚实性逐项核对

MVP 文档开篇（`docs/auto-localization-mvp.md:3-9`）把交付限定为「Phase 0 基线门禁修复 + Phase 2 离线闭环」，
并在 §8 用表格逐阶段标注状态。逐项核对用户点名的「未实现项」：

| 未实现项 | 是否明确列出 | 位置 | 是否被暗示为已完成 |
| :--- | :--- | :--- | :--- |
| 提取器 / probe 重写（Phase 1） | ✅ 明确 | `mvp.md:246`「⛔ 未做」；`mvp.md:318-321`「采集仍靠旧提取器…SNR≈0.21%」 | 否；反而反复强调上游仍是噪声 |
| 引擎命中/未命中计数器（Phase 4） | ✅ 明确 | `mvp.md:245`「未做」；`mvp.md:337-338`「没有运行时命中率数据」；`verification.md:470` | 否 |
| `patch --dry-run`、客户端快照/自动回滚（Phase 4） | 🟡 间接收录 | `mvp.md:249` Phase 4「⛔ 未做」；`mvp.md:218-219`「不调用 patcher patch/restore」；`verification.md:462` 逐项列出 | 否；但 MVP §11 未逐项点名（RF-08，低） |
| 在线 LLM（Phase 3） | ✅ 明确 | `mvp.md:103-106`「只有接口占位」；`mvp.md:248`「⛔ 接口占位」；`providers.py:237-261` 三重拒绝 | 否 |
| V3 真机验证（Phase 4） | ✅ 明确 | `mvp.md:249`；`mvp.md:337-338`；`verification.md:470` | 否 |
| `patterns.json` / H17–H20（Phase 2 尾巴） | ✅ 明确 | `mvp.md:175-178`、`mvp.md:329-330`；`verification.md:460` | 否 |

补充核对：

- `mvp.md:245` 对 Phase 0 也标了 **🟡 部分**（生成物/README 已修，引擎计数与 restore 自动回归未做）——这是**加分项**，
  没有把「Phase 0」整体算作完成；
- `docs/auto-localization-design.md:14-24` 的「一页结论」是**方案**而非完成声明，明确写「Phase 0 最高优先级」；
- `CONTRIBUTING.md:30-48` 新增的「方式 3」自称「离线 MVP 原型」，并指向范围文档，没有向贡献者承诺自动翻译质量。

**判定：范围诚实性通过。** 唯一可改进处是 RF-08（把 Phase 4 的四项在 MVP §11 中逐项点名）。

---

## 4. 文档一致性

| 检查 | 结果 | 说明 |
| :--- | :--- | :--- |
| `mvp.md:16`「770 行」 vs 实际 761 | ❌ 笔误 | t4 已记为 F1（`verification.md:431`），属实；同文 §1/§10 均写 761。属文档瑕疵，**不阻塞**（RF-05） |
| `mvp.md:16` 其余数字（一条命令、QA+计划+diff） | ✅ | 与 A2 一致 |
| `mvp.md:47-49` provider 计数（`file=761, tm=1`）、759/2 | ✅ | 与 A2 一致 |
| `mvp.md:71-72`「`--waive` 留痕到报告与 `qa.json`/`manifest.json`」 | ⚠️ 部分不实 | `qa.json` 与 stdout 报告有 `waived`；**`manifest.json` 只写 qa 计数**（`pipeline.py:444-452`），不含 `waived`（RF-04） |
| `mvp.md:170` H12 阈值 8 | ⚠️ 与设计不一致 | 设计 `design.md:502` 写 `max(1.4×len, 6)` 且「按钮/标签 blocker」，实现用 8 且不按控件分级（RF-06） |
| `mvp.md:299-301` apply 数字 | ✅ | 与 A4–A6 一致 |
| `mvp.md:306-312` 本机实测 | ✅ | A7–A11 全部复现 |
| `verification.md:22`「H1–H13 … 全覆盖」 | ⚠️ 措辞过强 | 23 个黑盒用例实测了 13 条中的 11 条（H5/H6 在提案链路不可达，F3/F4 已披露）＋H21；**H23 未出现在任何用例**（RF-09） |
| `verification.md:315`「MVP §12.2 已列为下一步」 | ⚠️ 交叉引用不成立 | `mvp.md:344-351` §12 第 2 条只讲 CI 接线，**没有 README 计数**；F6 目前只存在于验证报告（RF-01） |
| `design.md:500` 引 `CONTRIBUTING.md:34-44` | ⚠️ 行号漂移 | `CONTRIBUTING.md` 插入「方式 3」后术语表实际在 54–62 行（RF-14） |

---

## 5. 数据安全：真实仓库未被 apply，隔离演练可复现

| 检查 | 观测 | 判定 |
| :--- | :--- | :--- |
| 主仓库词典 | sha256 `793905e9…`、2,816 条（与 t4 §1.3 声称一致） | ✅ 未被 apply |
| 生成物 | 引擎内嵌 2,816、patcher 内嵌 2,816（A9/A7） | ✅ 与词典一致（Phase 0 已修） |
| `.l10n/` | 仓库根不存在（`Test-Path .l10n` = False） | ✅ dry-run 未落盘 |
| 隔离副本 apply | 2,816→3,577、`verified=true`、二次 apply 幂等、sha 稳定（A4/A5） | ✅ 可复现 |
| `.gitignore` 处理 | 新增 `.l10n/`（第 28-29 行）与 `.pytest_tmp/`（第 31-32 行）；`git check-ignore` 确认 `.pytest_tmp/base` 被第 31 行命中 | ✅ 合理 |
| 未被 ignore 的遗留 | 仓库根有**空目录** `.l10n_tmp/`（无文件、无任何代码引用）；git 不跟踪空目录，故不进提交 | ℹ️ RF-13（信息，建议清理） |
| 备份链 | apply 前写 `.l10n/runs/<id>/pre-merge/zh-CN.json`；`restore_dictionary` 走原子写 | ✅ |
| 真实客户端 | 代码中无 `%APPDATA%`/`Application Support` 路径、无 `patcher patch/restore` 调用 | ✅ 未碰客户端 |

> 说明：`git status` 中 `locales/zh-CN.json` 的「已修改」是 t1 之前就存在的 +24 条（baseline 已声明），
> 不是本次评审或 t3/t4 造成的；`engine/`、`scripts/patcher.py` 的修改是 `build.py` 重生成的 Phase 0 对齐。

---

## 6. 基线门禁：是否真的变绿、是否只经 `build.py`

1. **生成物一致性**（CI `release.yml:54-57`）：`build.py --no-exe` 后 `git diff --exit-code -- scripts/patcher.py engine/ag_localization_engine.js`。
   本评审在 **pristine 副本**（只含 `scripts/build.py` + `engine/engine_template.js` + `locales/*.json`）重建，
   产物与仓库生成物**逐字节相同**（`ce47b0b9…` / `2d148c82…`）——这同时证明：
   - 仓库里的两个生成物就是「当前词典 + 模板」的确定性函数值，**无人手改**；
   - 工作区里生成物与词典同为 2,816，作为同一提交时该门禁为绿（`mvp.md:332-336` 已如实说明「必须是同批提交」）。
2. **README 计数**（CI `release.yml:59-82`）：逐字复刻 → `[+] README counts match locales: 2816 entries / 180 rules`，exit 0。
3. **「只经 build.py」规则**：`grep` 全包写入面 → 仅 `locales/zh-CN.json`、`pre-merge` 备份、`.l10n` 产物；
   对 `engine/` 只读（`generated_engine_entries()`）；无任何代码写 `scripts/patcher.py`；
   `subprocess.run` 只出现在 `rebuild()`（调 build.py）与 `CommandProvider`（可选适配器）。
   **判定：规则被遵守。**

4. **注意（非缺陷）**：HEAD 里仍是 2,792/旧 README，当前「绿」只在工作区同时含
   `词典 + 生成物 + README` 四项改动时成立；CI 在提交树上跑，因此等价。`mvp.md:332-336` 已写明这一点，
   t4 用临时索引复现（`verification.md:295-301`），本评审未重复临时索引实验（A7/A8 已给出更直接的字节级证据）。

---

## 7. 门禁有效性

### 7.1 两条 H10 是不是误报

**不是误报。** 候选译文与术语表原文：

| 原文 | 候选译文 | 术语表要求（`CONTRIBUTING.md`） | 判定 |
| :--- | :--- | :--- | :--- |
| `AI Credits are used when you've exceeded your model quota…` | `当超出模型配额时，将使用 AI Credits。可在以下位置查看当前的 AI Credits…` | `Credits -> 积分`（第 59 行） | 真缺失；同时 `AI Credits` 整词未译，属**候选内容问题** |
| `Customizations views` | `自定义视图` | `Customizations -> 自定义配置`（第 61 行） | 真缺失；译文在术语上不合规 |

另外 759/761 条通过 H1–H4/H10–H13 的形式门禁；H10 之外的 major/minor 为 0（A2），说明门禁**没有大面积误报**。

### 7.2 `--waive` 留痕

- stdout 报告：`waived findings: N` + `--json` 的 `qa.waived[]`（含 rule/source/reason）✅；
- `qa.json`：`as_dict()` 含 `waived` 全量 ✅；
- `manifest.json`：**不含** `waived`（只有 qa 计数）❌ → RF-04（低，文档与实现对齐即可）。

### 7.3 外部 provider 默认低置信度

- `CommandProvider` 默认 `LOW`（`providers.py:179`、`cli.py:48-49`），`plan_merge` 对 `LOW` 一律进隔离区（`merge.py:86-91`）；
- 测试 `test_command_provider_output_is_quarantined_at_low_confidence` 覆盖；本评审的 A2/A4 未使用 cmd，但代码路径与测试一致；
- `--cmd-confidence high` 才会合并——这是**显式人工抬升**，可接受。

### 7.4 **新发现**：H21 大小写碰撞存在覆盖漏洞（RF-03，中）

`qa.py:411-437` 用 `reported` 集合按 `casefold()` 去重，**每个大小写组只报第一条 finding**，
而 `plan_merge` 只隔离「有 finding 的 source」。本评审构造的复现：

```
词典: {"Save": "保存"}
候选: "save" -> "储存"；"SAVE" -> "节省"
实测: 只有 "save" 被 H21 隔离；"SAVE" 无 finding → 进入 additions
merge 后: {"Save": "保存", "SAVE": "节省"}
```

再加上一条：**批次内**（词典里没有同形键）的两个大小写变体完全不被检测：

```
词典: {}
候选: "Docs" -> "文档"；"docs" -> "文档集"
实测: gate=pass，findings=[]
```

后果与 H21 存在的理由完全一致：`engine_template.js:34-36` 的 `lowerTranslations[key.toLowerCase()]`
是后写覆盖，两个 casefold 相同的键会互相遮蔽。当前 761 条真实数据 H21 finding=0，**无现实影响**，
但规则声称的保证不完整，属门禁有效性缺陷而非文档问题。建议：去掉 `reported` 去重（逐条报），
并把「提案批次内的 casefold 碰撞」纳入 H21（或 H9 的变体）。

### 7.5 **新发现**：已实现规则的覆盖是设计的子集（RF-06，低）

| 规则 | 设计（`design.md`） | 实现（`qa.py`） | 影响 |
| :--- | :--- | :--- | :--- |
| H2 | URL + **含 `/` 的路径** + 扩展名白名单 | 仅 `https?://` + 固定扩展名（t4 F10 已实测 `~/.env`、`/etc/hosts`、`config.ini` 不告警） | 路径丢失漏报 |
| H5 | 空 / **纯标点** / 纯空白 | 只判空与纯空白（且提案链路被 FileProvider 先丢弃，F3） | 规则名义覆盖 |
| H12 | 阈值 `max(1.4×len, 6)`、按钮/标签为 blocker | `max(int(1.4×len), 8)`，一律 major（>500 才 blocker） | 比设计宽松；未分级 |
| H13 | `:`/`,`/`…` 结尾、`(` 开头 **+ 小写开头不得改写为完整句** | 只实现前四项 | 片段语义缺口（F9 已承认不可离线自证） |

MVP 文档的规则表（`mvp.md:157-182`）对这些子集**没有逐项说明**，而 `coverage` 只按规则 ID 统计「15/23」，
读者容易高估覆盖。建议在 `mvp.md` §4 增一列「实现的是设计的哪个子集」或把未实现子项登记为 TODO（不要求本期实现）。

---

## 8. 隐私 / 安全与回滚边界

| 检查 | 结论 | 证据 |
| :--- | :--- | :--- |
| 包内零网络 | ✅ | A13；`test_localization_package_contains_no_network_code`、`test_a_full_dry_run_never_creates_a_socket` |
| online provider 仅 stub | ✅ | `providers.py:237-261`；三组合均 exit 4（测试 `test_online_provider_requires_both_switches…`） |
| 默认 provider | ✅ `tm`（离线、确定性）；`file` 仅在有 overlay 时插入链首 | `cli.py:44-45`、`providers.py:264-295` |
| 写入面 | ✅ 词典 + pre-merge 备份 + `.l10n` 产物；无生成物直写 | A7 + grep |
| 原子性 | ✅ 临时文件同目录 + `os.replace`；失败清理 tmp | `textutils.py:109-141` |
| 回滚顺序 | ✅ 先写备份 → 原子写词典 → build → 回读条数；失败才回滚 | `pipeline.py:401-464`；`merge.py:114-151` |
| 回滚是否半写 | ⚠️ 词典不会半写（原子 replace），但**「回滚后再次 build 仍失败」会留下词典=旧、生成物=新的窗口** | t4 F7 实测（`verification.md:250`）；`pipeline.py:297-310` 只恢复词典并重试 build，失败仅记 `rollback.ok=false` |
| 建议 | 在 exit 4 的 `report`/`manifest` 显式打印「生成物可能过期 + 人工修复命令」（`python scripts/build.py --no-exe`），并把 F7 写进 MVP §11 | — |

补充：`prepare()` 把「候选文件自带的译文 / `--translations` overlay」一律当作 **HIGH（人工决定）**，
只有 `--provider cmd` 是 untrusted。这对当前仓库成立（候选文件是人工维护的跟踪文件），
但**任何机器生成的 overlay 放进 JSON 就会绕过隔离区**，只剩形式门禁把关（RF-11，低，建议文档声明 overlay 必须人工复核或增加 provenance 标记）。

---

## 9. 测试充分性与维护成本

**做得好的：**

- 46 个测试覆盖了最危险的语义：dry-run 零写盘（整树 sha256）、apply 幂等、跨仓库确定性、
  CRLF/键序/最小 diff、QA 拒绝、回滚（删模板）、`--no-build` 修复、`--waive`、TSV/map/cmd、
  零网络（正则 + socket 拦截）、人类可读输出；
- 用子进程跑真实 CLI（非纯单测），与「用户实际执行」一致；
- 测试数据自建在 `<repo>/.pytest_tmp/`，绕开沙箱 ACL 的说明写在 docstring 里，可维护。

**不足（均非阻塞）：**

| # | 问题 | 影响 | 建议 |
| :- | :--- | :--- | :--- |
| RF-07 | 已实现的 15 条规则里，**H11/H13/H23 在提交内没有任何正反例夹具**（`tests/test_localize_mvp.py` 只在 `coverage` 断言里出现这三个 ID）；H23 在 t4 的黑盒矩阵里也没有用例 | 违反设计自己的「规则即测试：每条规则 ≥1 正例 + ≥1 反例」（`design.md:526`）；H23 若被改坏无回归 | 补 6 个参数化用例（约 20 行），成本极低 |
| RF-09 | t4 摘要「H1–H13 全覆盖」与用例矩阵不一致；`blocker 10/13` 的口径把提案链路不可达的 H5/H6 算作已覆盖 | 读者高估有效覆盖 | 改措辞 + 标注 H5/H6 仅在词典模式/直接调用可触发 |
| RF-12 | `qa.GLOSSARY` 与 `CONTRIBUTING.md` 术语表是**两份硬编码**（8 个术语） | CONTRIBUTING 改术语时代码不跟随，H10 会与规范脱节 | 加同步测试（读 CONTRIBUTING 断言术语存在）或注释双向引用 |
| RF-14 | 设计文档引用 `CONTRIBUTING.md:34-44`（现为 54–62）等行号 | 行号漂移，后续读者找不到 | 改用「术语表」锚点或函数名引用 |

**维护成本评估**：8 个模块 ~90 KB 代码 / 24 KB 测试，注释与 docstring 密度高，无第三方依赖，
显式 TODO 与 `coverage.not_implemented` 让「没做」可见——对原型而言成本合理。主要长期风险是
**术语表双份硬编码**与**规则子集口径**（RF-06/RF-12），不是代码复杂度。

---

## 10. 对用户问题「有方案能完美实现自动汉化吗？」的证据支撑

用户点名的最终问题，需要分两半看：

### 10.1 负向结论（「100% 完美不可达」）——证据强

| 论点 | 证据 | 本评审是否复核 |
| :--- | :--- | :--- |
| 表示不可达（closed Shadow DOM、canvas、webview、跨域 iframe、原生对话框） | `baseline.md:112-120`（B1–B5）；引擎无 iframe 处理（grep 无 `iframe`）、只递归 `shadowRoot` | ✅ 代码级复核 |
| 全集不可枚举（SNR 0.21%、服务端下发） | `baseline.md:139`：366,366 候选 / 364,400 缺失 / 真值 752 | ⚠️ **未复跑提取器**（需已装客户端 + 旧提取器；t1 记录，不再重跑） |
| 引擎硬边界 | `engine_template.js:213`（含任一 CJK 即跳过）、`:214`（>500 字符跳过） | ✅ 代码级复核 |
| 上下文单射不可判定（Save/Cancel） | `baseline.md:140`；引擎是 `key→value` 单射（`engine_template.js:24-36`） | ✅ |
| 质量不可自证 | `baseline.md:141`；MVP 只能做形式门禁（H1–H13） | ✅ |

### 10.2 正向结论（「流水线自动化可行、常规增量版 ≤30min」）——一半实测、一半估算

| 部分 | 证据强度 |
| :--- | :--- |
| 机械半段（QA/合并/重建/回读/回滚/确定性） | **已实测**：dry-run ≈105 ms、全量 apply ≈244 ms、46 测试、字节级可复现（A4–A7） |
| 翻译覆盖半段（TM/术语能命中 60–85%） | **未实测**：设计 `design.md:940` 明确是「估」；MVP 唯一真实数据里 `tm=1/761`（因为候选按定义就不在词典里），761 条译文全部来自**人工维护的候选文件**（`file=761`）。MVP 自身已承认「翻译质量仍由人决定」（`mvp.md:318-321`） |
| 人工分钟（7–20 / 23–36 min/版） | 设计里的估算模型（4 s/条），无实测 |

**结论**：最终报告可以放心写「全 UI 100% 不可达」，因为它有三层硬证据；但写「≤30min/版」时必须保留
「TM 命中率与人工分钟尚未实测」的限定，否则就是把估算当测量。MVP 文档的措辞已经是诚实的
（`mvp.md:318-321`、`design.md:21` 标「估算」），**最终答复不应比文档更乐观**。

---

## 11. 对 t4 两项中等级发现的裁决（captain 提问）

### F6：`apply` 不更新 README，真实仓库 apply 后 CI README 门禁必红

- **事实成立**：`pipeline.run_release` 成功路径只写词典 + build + manifest，不碰 README（grep 无 README 引用）；
  t4 的 copyA 实验（放 README 后门禁 exit 1）逻辑正确；本评审的 A4/A5 也确认 apply 只改词典与生成物。
- **是否阻塞「可行性结论」**：**不阻塞**。可行性结论的主体是「管线可自动化、可回滚、可度量」，
  README 计数是**仓库流程卫生**，4 行数字、可由人补，且与 MVP 声称的「自动合并 + 重建」不矛盾。
- **是否可以在真实仓库 apply 前不管**：**不可以**。这是唯一一条「按文档操作后会立刻制造红 CI」的路径，
  而 MVP 文档目前**没有写**（`mvp.md` §11 与 §12 均无；F6 只存在于 t4 报告，且 `verification.md:315`
  误称「MVP §12.2 已列为下一步」）。
- **最小修复范围（不扩到 Phase 1/4）**：
  1. `mvp.md` §11 增加一条已知限制 + §12 第 2 条补「apply 后需同步 README 计数（MVP 不自动改）」；
  2. `CONTRIBUTING.md` 方式 3 补一句同样提示；
  3. （可选，代码）`release --apply` 成功后打印 `README counts are stale: update 2,816 -> N`，或提供
     `--update-readme`（4 行替换，无新依赖）。**建议只做 1+2，代码留到 Phase 5 运营化时再做。**
- **不影响最终结论**：是。

### F2：`--provider-cmd` 在 Windows 下被 POSIX `shlex.split` 吃掉反斜杠

- **事实成立**：`providers.py:182` `shlex.split(command)`（默认 `posix=True`）；`D:\…\python.exe` → `D:…python.exe`；
  正斜杠可绕过；失败是**显式** `provider command not found`（exit 4），不是静默错译。
- **是否阻塞「可行性结论」**：**不阻塞**。`cmd` 是可选适配器，默认离线链路（`tm`/`file`）完全不受影响；
  隐私/安全语义（默认 low→隔离）也不受影响。
- **最小修复范围**：
  1. 文档：`mvp.md` §2「外部 provider 适配器」加一句「Windows 绝对路径请用正斜杠，或传参列表」；
  2. （可选，代码 1 行）`shlex.split(command, posix=(os.name != "nt"))`，但这会改变引号语义，
     更稳的做法是支持重复 `--provider-cmd-arg` 或 JSON 数组；**MVP 阶段建议只做文档**。
- **不影响最终结论**：是。

> 总结：**两条都作为「已知 MVP 限制」写入最终报告即可，不需要返工**；F6 需要一次**纯文档**的最小修复，
> F2 只需一句文档提示。二者都不需要扩大实现范围。

---

## 12. 发现清单（findings）

| ID | 级别 | 位置 | 问题 | 修复建议 | 阻塞最终结论 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RF-01** | 中（流程） | `scripts/localization/pipeline.py:437-453`；`docs/auto-localization-mvp.md` §11/§12；`docs/auto-localization-verification.md:315` | `release --apply` 只保证「词典+生成物」一致，不更新 README 计数；真实仓库全量 apply 后 CI 的 README 门禁必红（t4 F6 已实测）。MVP 文档未收录；验证报告「§12.2 已列为下一步」的交叉引用不成立 | 在 `mvp.md` §11 增一条已知限制、§12 第 2 条补「apply 后同步 README 计数」；`CONTRIBUTING.md` 方式 3 补同样提示；代码可选（打印 stale 提示或 `--update-readme`） | 否 |
| **RF-02** | 中 | `scripts/localization/providers.py:182` | `shlex.split(command)` 默认 POSIX：Windows 绝对路径反斜杠被吃掉，`--provider-cmd` 在 Windows 上用绝对路径失败（正斜杠可绕过；失败显式 exit 4） | `mvp.md` §2 补 Windows 路径提示；代码可选支持列表/`posix=False`（需处理引号，建议留到后续） | 否 |
| **RF-03** | 中 | `scripts/localization/qa.py:411-437` | H21 按 `casefold` 去重，每组只报一条 finding；同批多个大小写变体只有第一个被隔离，其余仍会合并（实测 `{"Save":"保存"}` + `save/SAVE` → 仅 `save` 隔离、`SAVE` 入词典）；批次内 `Docs`/`docs` 碰撞完全不检测。引擎小写索引后写覆盖（`engine_template.js:34-36`） | 去掉 `reported` 去重（逐条报）；把「提案批次内 casefold 碰撞」纳入 H21；补 1 个回归测试 | 否（当前 761 条真实数据 H21=0，无现实影响） |
| **RF-04** | 低 | `docs/auto-localization-mvp.md:71-72`；`scripts/localization/pipeline.py:444-452` | 文档称 `--waive` 留痕到 `manifest.json`，实际 `manifest` 的 `qa` 只有 `checked/gate/blockers/majors/minors`，无 `waived`（`qa.json` 有） | 文档改为「报告 + qa.json」，或把 `waived` 写进 manifest | 否 |
| **RF-05** | 低 | `docs/auto-localization-mvp.md:16` | 「770 行的候选集」实际 761（t4 F1 已记录） | 改为 761（或「约 760 行」） | 否 |
| **RF-06** | 低 | `docs/auto-localization-design.md:502-503`、`docs/auto-localization-mvp.md:157-182`、`scripts/localization/qa.py:280-378` | 已实现规则是设计定义的子集：H2 缺路径/非常见扩展名（t4 F10）、H5 缺「纯标点」、H12 阈值 6→8 且未按控件分级、H13 缺「小写开头不得改写为完整句」；而 coverage 只按规则 ID 计 15/23 | 在 MVP §4 增「实现子集」列或把子项登记为 TODO；H12 阈值与设计对齐或在文档说明偏离原因 | 否 |
| **RF-07** | 低 | `tests/test_localize_mvp.py:434-440`；`docs/auto-localization-design.md:526` | H11/H13/H23 在提交内没有正反例夹具（只在 coverage 断言里出现）；H23 在 t4 黑盒矩阵中也无用例；设计却要求「每条规则必带夹具」 | 补 3 条规则 ×（1 正例 + 1 反例）参数化用例（约 20 行） | 否 |
| **RF-08** | 低 | `docs/auto-localization-mvp.md:249`、`:316-338`；`docs/auto-localization-verification.md:462` | Phase 4 的 `patch --dry-run`、客户端快照、自动回滚未在 MVP §11 逐项点名（仅在 §8 按阶段笼统标「未做」） | §11 增加 3 个短条目 | 否 |
| **RF-09** | 低 | `docs/auto-localization-verification.md:22`、`:418` | 「H1–H13 … 全覆盖」措辞过强：H5/H6 在提案链路不可达（F3/F4），H23 未测；`blocker 10/13` 把 H5/H6 计入 | 改为「13 条中 11 条实测拒绝路径 + H21；H5/H6 名义覆盖、H23 未覆盖」 | 否 |
| **RF-10** | 低 | `docs/auto-localization-verification.md:479-604`（附录 A） | A-3/A-5/A-11 依赖 `.pytest_tmp/verify/*.py`（gitignored，临时）；A-2/A-4/A-6/A-7/A-8/A-10 自包含 | 把 3 个关键脚本提交到 `tools/verify/`，或在正文内联最小等价命令 | 否 |
| **RF-11** | 低（风险） | `scripts/localization/providers.py:132-158`；`scripts/localization/cli.py:42-44` | `file`/`--translations` overlay 一律 HIGH；机器生成的 overlay 放进 JSON 即可绕过 `cmd` 的 low→隔离，只剩形式门禁 | 文档声明「overlay 必须人工复核」；或给 overlay 加 `confidence`/`provenance` 字段（默认 high 不变） | 否 |
| **RF-12** | 信息 | `scripts/localization/qa.py:75-84` | `GLOSSARY` 与 `CONTRIBUTING.md` 术语表双份硬编码，存在漂移 | 加同步测试或双向注释引用 | 否 |
| **RF-13** | 信息 | 仓库根 `.l10n_tmp/` | 空目录、无代码引用、未被 `.gitignore` 覆盖（git 不跟踪空目录，故无实际影响） | 删除；如需保留则加入 `.gitignore` | 否 |
| **RF-14** | 信息 | `docs/auto-localization-design.md:500` 等 | 行号引用随 `CONTRIBUTING.md` 编辑漂移（34-44 → 实为 54-62） | 改用章节锚点/函数名引用 | 否 |

---

## 13. 诚实声明与本次评审的局限

1. **没有复跑提取器/探针**：baseline 的「366,366 候选 / SNR 0.21%」需要已安装客户端与旧提取器，
   本评审未重跑，只核对 baseline 的复现命令与数据来源（`baseline.md` 附录 A/B）；该数字属 t1 证据。
2. **没有在真实仓库执行 `--apply`**：与 t3/t4 一致，只用 `.pytest_tmp/review` 隔离副本（评审后已删除）。
3. **没有真机验证**：未 patch/restore 任何客户端；「运行时命中率」不在本报告范围。
4. **没有复跑 Linux/CI 环境**：README 门禁、生成物门禁按 `release.yml` 逐字复刻在本机复现；Linux 上的
   CRLF 归一行为未实测，但 git `text=auto` 归一使该风险很低。
5. **未重复 t4 的 82 条人工语义抽样**（主观判读）；只复核其可机器验证的统计口径。
6. **未修改任何代码/词典/生成物/README**：本报告只新增 `docs/auto-localization-review.md`，
   并在 `.pytest_tmp/review` 建过临时副本（已删除，gitignored）。
7. **评审者与被评审实现的关系**：本报告的评审者未参与 t3 实现；t4 的验证由另一成员完成，本报告是第二方复核。

---

## 附录 A：关键复现命令（本次评审实际执行）

```powershell
# A-1 基础数字
python -c "import json;print(len(json.load(open('untranslated_candidates.json',encoding='utf-8'))))"   # 761
python -c "import json;print(len(json.load(open('locales/zh-CN.json',encoding='utf-8'))))"              # 2816
python -c "import json;print(len(json.load(open('locales/patterns.json',encoding='utf-8'))))"           # 180

# A-2 dry-run（零写盘、exit 2、2×H10）
python scripts/localize.py release --json     # exit 2；blockers=2(H10)；additions=759, quarantined=2

# A-3 隔离副本 apply / 幂等 / 格式
mkdir .pytest_tmp/review/{scripts,engine,locales}
copy scripts/build.py + engine/engine_template.js + locales/*.json + untranslated_candidates.json
python scripts/localize.py release --repo-root .pytest_tmp/review --apply --waive H10 --json
#   exit 0；2816→3577；build.engine_entries=3577 verified=true
#   再跑一次：additions=0、already_present=761、词典 sha 不变
#   词典字节：244019；CRLF 3579；裸 LF 0；git diff --no-index --numstat = 762 / 1

# A-4 生成物可复现（pristine 副本）
python .pytest_tmp/review/scripts/build.py --no-exe      # exit 0
#   引擎 ce47b0b9… / patcher 2d148c82… 与仓库产物相同

# A-5 门禁
python - <<'EOF'   # 逐字复刻 release.yml 的 README 计数门禁
… （脚本见报告 §6）→ [+] README counts match locales: 2816 entries / 180 rules，exit 0
EOF

# A-6 测试与语法
python -m pytest tests/test_localize_mvp.py -q        # 46 passed
python -m pytest -q                                    # 127 passed / 1 failed / 34 errors（PermissionError，沙箱 ACL）
python -m py_compile …                                 # 0
node --check engine/engine_template.js; node --check engine/ag_localization_engine.js   # 0 / 0

# A-7 H21 覆盖漏洞复现
python -c "import sys;sys.path.insert(0,'scripts');from localization import qa,merge;
d={'Save':'保存'};e=[qa.QaEntry(source='save',target='储存'),qa.QaEntry(source='SAVE',target='节省')];
r=qa.run_qa(e,d);print([(f.rule,f.source) for f in r.findings])   # 只有 ('H21','save')"
python -c "…qa.run_qa([QaEntry('Docs','文档'),QaEntry('docs','文档集')], {})"   # gate=pass（批次内碰撞不检测）
```

---

## 附录 B：逐项核对表（任务要求 → 结论 → 证据）

| 任务要求 | 结论 | 证据位置 |
| :--- | :--- | :--- |
| 范围诚实性：只声称 Phase 0 + Phase 2 纵切 | ✅ | §3；`mvp.md:3-9/243-250`；`verification.md:457-463` |
| 未实现项明确列出（probe/计数器/patch dry-run/快照/在线/V3） | ✅（Phase 4 两项只在 §8 笼统标未做 → RF-08） | §3 |
| `mvp.md:16` 770 vs 761，确认报告是否记录 | ✅ 已记录（t4 F1），属实，不阻塞 | §4、RF-05 |
| 真实仓库未 apply（词典仍 2,816） | ✅ | §5；词典 sha `793905e9…` |
| 隔离 2,816→3,577 可复现 | ✅ | §5 / A-3 |
| `.l10n/`、`.pytest_tmp/` 的 `.gitignore` 处理 | ✅ 合理（另发现空 `.l10n_tmp/`，信息级） | §5、RF-13 |
| 生成物 2,816 与 README 计数真的变绿 | ✅ | §6 / A-4 / A-5 |
| 遵守「只经 build.py 生成」 | ✅ | §6；pristine 字节相同 + 写入面 grep |
| 2 个 H10 是真术语缺失而非误报 | ✅ | §7.1 |
| `--waive` 留痕 | ✅（`qa.json`；manifest 缺 → RF-04） | §7.2 |
| 外部 provider 默认低置信度 | ✅ | §7.3 |
| `scripts/localization/` 零网络、online 仅 stub | ✅ | §8 / A-13 |
| 回滚是否会半写 | ✅ 词典不会；生成物有 F7 残留窗口（已记录） | §8 |
| 测试充分性与维护成本 | ✅ 基本充分（RF-07/RF-09/RF-12 为改进项） | §9 |
| 对用户问题的回答是否有证据支撑 | ✅ 负向强、正向需保留「TM 命中未实测」 | §10 |
| F6 / F2 的裁决 | 均非阻塞；F6 需纯文档最小修复 | §11 |
