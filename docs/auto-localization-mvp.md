# 自动汉化 MVP（离线纵切）：使用与范围

> 状态：**原型 / 可验证纵切**。本次交付不是完整路线图，而是
> 「Phase 0 基线门禁修复 + Phase 2 离线闭环」的最小可运行版本，用来证明
> 「候选 → 翻译提案 → QA → 合并 → 重建 → 验证 →（失败）回滚」这条链路可以
> 默认安全、可回滚、可重复地跑通，并且能诚实报出哪里不通。
>
> 上游文档：`docs/auto-localization-baseline.md`（审计与可达目标）、
> `docs/auto-localization-design.md`（端到端设计与 Phase 0–5 路线）。

---

## 0. 一句话

**默认 dry-run、零网络、只经 `build.py` 生成产物、失败自动回滚词典**；
761 行的候选集在一条命令内给出 QA 报告 + 合并计划 + diff 预览，`--apply` 才落盘。

---

## 1. 一条命令跑 dry-run

在仓库根目录：

```bash
python scripts/localize.py release
```

等价于：

```bash
python scripts/localize.py release --candidates untranslated_candidates.json --provider tm
```

它做的事：读 `untranslated_candidates.json`（默认路径）+ `locales/zh-CN.json`
→ 走 provider 链（候选自带译文 / `--translations` / 翻译记忆）→ 跑 QA 门禁
→ 打印 QA 报告 + 合并计划 + diff 预览 + 退出码。**不写任何文件**。

`--json` 输出单行 JSON（机器可读），人类日志仍在 stdout 的 JSON 之外：

```bash
python scripts/localize.py release --json
```

当前仓库的真实结果（见 §10 证据）：

- 761 条候选，761 条带译文；
- provider：`file=761`（候选自带译文）、`tm=1`（一条命中现有词典）；
- QA：`gate=fail`，**2 个 blocker（H10 术语）**，0 major、0 minor；
- 合并计划：759 条可加、2 条进隔离区；
- 退出码 **2**（门禁失败，符合设计语义：门禁失败不落盘）。

> 这 2 条不是工具误报：候选文件里
> `AI Credits are used when you've exceeded your model quota…` 的译文没用到
> 「积分」，`Customizations views` 的译文没用到「自定义配置」，而
> `CONTRIBUTING.md` 明确要求这两个术语。要么修译文，要么显式豁免。

### 「未翻译」三份口径对照

> 注：全量底稿与合并视图已移出仓库（无代码消费的中间产物）；管线唯一输入是
> `untranslated_candidates.json`（761 条），也是唯一保留在仓内的清单。

| 口径 | 说明 | 消费方 |
| :--- | :--- | :--- |
| 全量刮取（去重前，含噪音） | 底稿明细，已归档 | 人工审阅 |
| 全量刮取去重后 | 合并视图（候选 761 + 项目文案 179），可再生，已归档 | 人工审阅 |
| `untranslated_candidates.json`（761 条） | 去重 + 引擎规则过滤后 | `localize.py` 管线唯一输入 |

---

## 2. 命令面

| 命令 | 作用 | 关键参数 | 退出码 |
| :--- | :--- | :--- | :--- |
| `localize release` | 提案 → QA → 计划 →（apply）重建 → 验证 | `--apply`、`--no-build`、`--candidates`、`--translations`、`--provider`、`--provider-cmd`、`--waive`、`--limit`、`--json` | 0/2/4 |
| `localize merge` | 提案 → QA → 计划 →（apply）只写词典，不重建 | `--apply`、同上 | 0/2/4 |
| `localize qa` | 词典结构体检（默认），或对候选/译文跑完整门禁 | `--candidates`、`--translations`、`--strict`、`--json` | 0/2 |
| `localize release --apply` | **写入 + 重建 + 验证 + 失败回滚** | 同上 | 0/2/4 |

通用参数：

- `--repo-root <dir>`：把仓库根指向别处（测试与隔离演练用；默认是本 checkout）；
- `--waive RULE`（可重复）：把某条规则降级为「已豁免」并**留痕**到报告与
  `qa.json`/`manifest.json`，不允许静默放行；
- `--limit N`：只处理前 N 条候选（分批/演练）；
- `--run-dir`：run 产物目录（默认 `<repo>/.l10n/runs/<run-id>/`，已在 `.gitignore`）；
- 退出码：`0` 成功；`2` 门禁失败；`4` 前置条件失败（输入缺失、需要双开关的在线
  provider、重建失败且回滚）；`5` 内部错误。

### 三种典型用法

```bash
# 1) 纯离线 dry-run（默认，CI 友好）
python scripts/localize.py release --json

# 2) 用一份外部译文（JSON / JSONL / TSV）提案，门禁通过后落盘并重建
python scripts/localize.py release --translations overlay.tsv --apply

# 3) 只合并词典、稍后手动重建（.l10n/runs/<id>/pre-merge 有备份）
python scripts/localize.py merge --translations overlay.tsv --apply
```

### 外部 provider 适配器

```bash
python scripts/localize.py release --provider cmd \
  --provider-cmd "python my_translator.py" --cmd-confidence high --json
```

命令从 stdin 收到 `{"schema":1,"items":[{source,kind,prop,path,line},…]}`，
在 stdout 打印 `{"translations": {"原文": "译文"}}`（或
`[{"source":…,"target":…}]`）。**默认 `--cmd-confidence low`**：外部命令的输出
不可信，提案会进隔离区；只有显式提高置信度才会被合并。

在线 provider（`--provider online`）在本 MVP 中**只有接口占位**：必须同时给出
`--allow-network` 与 `AG_L10N_ALLOW_NETWORK=1`，通过后仍然直接报
「stub, no network backend」。整个 `scripts/localization/` 包**没有任何网络
import**（有测试用正则与 socket 拦截双重证明）。

---

## 3. 代码结构与数据流

```
scripts/localize.py                 # 入口（薄壳，只做 sys.path + main）
scripts/localization/
  candidates.py                     # 候选/译文加载：JSON list、JSON map、JSONL、TSV
  providers.py                      # file > tm > cmd > online(stub) 链；TM 精确/忽略大小写/术语
  qa.py                             # 确定性 QA 门禁 H1–H13、H21、H23（其余登记为 TODO）
  merge.py                          # 保序、字节最小、原子写、pre-merge 备份
  pipeline.py                       # release/merge/qa 编排、build 验证、失败回滚
  cli.py                            # argparse + 人类可读报告 + JSON 输出
  textutils.py                      # 代理字符/不可见字符/CRLF 风格/原子写
tests/test_localize_mvp.py          # 46 个测试（本 MVP）
docs/auto-localization-mvp.md       # 本文
```

```
候选文件 ─┬─ 候选自带译文（最高优先级）
          ├─ --translations（显式覆盖，最高优先级）
          ├─ TM：现有词典精确 → 忽略大小写（medium）→ 术语表
          ├─ --provider-cmd（默认 low，进隔离区）
          └─ online（stub，拒绝运行）
                │
                ▼
        QA 门禁（blocker/major 即 fail；--waive 留痕）
                │ pass
                ▼
        合并计划（已有键永不覆盖；新键按 codepoint 稳定排序追加）
                │ --apply
                ▼
   pre-merge 备份 → 原子写 locales/zh-CN.json
                ▼
   python scripts/build.py --no-exe（唯一允许改生成物的路径）
                ▼
   回读 engine/ag_localization_engine.js 内嵌条数 == 词典条数？
        ├─ 是 → exit 0
        └─ 否 → 还原 pre-merge 词典 + 重新 build → exit 4
```

---

## 4. QA 门禁：实现了哪些、没实现哪些

设计文档 §4.4.3 的 23 条规则中，本次实现 15 条；**其余 8 条仍登记在
`qa.RULES` 里，并在每次报告里以 `coverage.not_implemented` 显式列出**，
不允许「看起来全绿」：

| 规则 | 内容 | 级别 | 状态 |
| :--- | :--- | :--- | :--- |
| H1 | 占位符保真（`{x}`/`{{x}}`/`{$x}`/`${x}`/`%s`/`$1`，多重集相等） | blocker | ✅ |
| H2 | URL / 文件名逐字保真 | blocker | ✅ |
| H3 | 代码标识保真（反引号、`--flag`、快捷键、`ALLCAPS_IDENT`、`snake_case`、`camelCase`、白名单缩写） | blocker | ✅ |
| H4 | HTML 标签序列不变 | blocker | ✅ |
| H5 | 空 / 纯空白译文 | blocker | ✅ |
| H6 | 键带首尾空白（引擎 trim 后永不命中） | blocker | ✅ |
| H7 | 引擎拼接哨兵标记注入 | blocker | ✅ |
| H8 | 孤立代理字符 / BOM / 零宽 / 双向控制符 | blocker | ✅ |
| H9 | 同一原文 → 多个不同译文 | blocker | ✅ |
| H10 | 术语表必用词缺失（CONTRIBUTING 术语表） | blocker | ✅ |
| H11 | 术语表禁用译法（如 `Agent`→「代理」） | major | ✅ |
| H12 | 长度预算（`≤ max(1.4×原文长度, 8)`）/ 原文 >500 字符（引擎硬跳过） | major/blocker | ✅ |
| H13 | 片段形态（以 `:`/`,`/`…` 结尾、以 `(` 开头） | major | ✅ |
| H14 | 标点风格 | minor | ⛔ TODO |
| H15 | 换行数量 | major | ⛔ TODO |
| H16 | 英文残留 | minor | ⛔ TODO |
| H17 | 正则可编译 / flags 白名单 | blocker | ⛔ TODO（本期不合并 `patterns.json`） |
| H18 | 正则锚定 / 捕获组引用 | blocker | ⛔ TODO（同上） |
| H19 | 正则重复 / 遮蔽 | blocker | ⛔ TODO（同上） |
| H20 | ReDoS 启发式 | major | ⛔ TODO（同上） |
| H21 | 与现有键大小写碰撞（引擎小写索引会互相覆盖） | major | ✅ |
| H22 | 同一译文对应语义相反的原文 | minor | ⛔ TODO |
| H23 | NFC 归一 | minor | ✅（合并前自动归一，条数记入报告） |

已知取舍（都写进代码注释）：

- **QA 只对「将要写入」的新条目生效**：已在词典里的键由人工决策保护，重跑 QA
  只会制造噪声；同键不同译的冲突在合并计划里单列（`conflicts`），永不自动覆盖。
  每次报告都带 `proposals.total/new/already_in_dictionary`，不隐藏范围；
- **缩写白名单故意很短**（`MCP/API/JSON/HTTP/SSH/…`），不含 `URL`/`UI`/`CLI`：
  「URL bar → 地址栏」「UI → 界面」是合法译法，强制保留会制造 false positive；
- H10 用英文词边界匹配，忽略复数（`agents` 不触发）；
- H3 的 camelCase/缩写启发式对产品名（`macOS`、`iPhone`）可能误报；这类条目用
  `--waive H3` 显式放行，豁免会写进报告而不是静默丢掉；
- 词典体检（`localize qa` 默认模式）只跑 H5–H8、H12、H21、H23：对存量 2,816
  条回放 H1–H4/H10–H13 只会把人埋在历史噪声里；`--strict` 可让 major 也失败。

---

## 5. 合并与可逆保证

| 保证 | 实现方式 | 测试 |
| :--- | :--- | :--- |
| 已有键永不被覆盖 | 计划阶段已知键 → `already_present`/`conflicts`；不写入 | `test_merge_keeps_existing…`（合并单测） |
| 新键稳定顺序 | 按原文 UTF-8 codepoint 排序后追加到末尾 | 幂等/格式测试断言 `new_keys == sorted(new_keys)` |
| 字节最小 diff | 复刻原文件缩进、CRLF 与结尾换行；只新增行 + 末行补逗号 | 格式测试断言「1 行删除、N+1 行新增」 |
| 原子写 | 同目录临时文件 + `os.replace` | `textutils.write_text_atomic` |
| 可回滚 | 写前把原文件存到 `.l10n/runs/<id>/pre-merge/zh-CN.json` | 回滚测试断言 sha256 复原 |
| 失败自动回滚 | 重建失败或回读条数不符 → 还原词典 + 重新 build | `test_apply_rolls_back_when_the_rebuild_fails` |
| 可重复 | 相同输入 → 相同词典/引擎/patcher sha256 | 幂等测试 + 双仓库确定性测试 |
| 生成物只经 `build.py` | 管线调用 `python scripts/build.py --no-exe`，从不手写生成物 | 无直接写入 `engine/` 或 `scripts/patcher.py` 的代码 |

---

## 6. 安全边界（不是承诺，是机制）

- **默认零网络**：包内无 `socket/urllib/http/requests/…` import；dry-run 在
  `socket.socket` 被 monkeypatch 成「一调用就抛异常」时仍通过；在线 provider
  需双开关且仍拒绝运行。
- **不碰真实客户端**：管线不调用 `scripts/patcher.py patch/restore`，不读写
  `%APPDATA%\Antigravity`；`--apply` 只影响仓库文件。
- **不改生成物源码**：`scripts/patcher.py`、`engine/ag_localization_engine.js`
  只由 `build.py` 重写；本次没有手改它们（Phase 0 的 2,816 条对齐也是跑
  `build.py` 得到的）。
- **输入净化**：读入即替换孤立代理字符（旧提取器崩溃根因），交给 H8 拒绝而不是
  让整轮崩掉。

---

## 7. Phase 0 基线门禁修复（本次一并完成）

| 门禁 | 修复前 | 修复后 |
| :--- | :--- | :--- |
| 生成物一致性（`build.py --no-exe` + `git diff --exit-code`） | 词典 2,816 vs 生成物 2,792（差 24）→ CI 红 | 生成物已重建为 2,816；四项变更一并提交后该门禁为绿（§10 有 CI 等价复现） |
| README 计数 | `README.md`/`README_EN.md` 仍写 2,792 | 已同步为 2,816（两处正文 + 两处目录树注释） |
| 测试基线 | 80 passed / 2 failed / 34 errors（1 真失败=生成物漂移） | 127 passed / 1 failed / 34 errors（剩余 1 failed + 34 errors 全是沙箱 `%TEMP%` ACL 假阴性，见 §11） |

生成物对齐只跑了 `python scripts/build.py --no-exe`（没有手改生成文件）；README
只改了 4 行数字。

---

## 8. 与设计 Phase 0–5 的映射

| 设计阶段 | 本次状态 | 说明 |
| :--- | :--- | :--- |
| Phase 0 门禁变绿 + 度量基础 | 🟡 部分 | 生成物/README 门禁已修；**引擎命中计数、restore 自动回归未做**（属 Phase 4） |
| Phase 1 采集重写（probe/D1 基线，SNR 0.21%→≥30%） | ⛔ 未做 | 仍用现有 `untranslated_candidates.json`；旧 `extract_untranslated.py` 崩溃与噪声问题原样保留 |
| Phase 2 离线闭环（TM/文件 → QA → 合并 → 重建 → 验证 → 回滚） | ✅ 已做（本次主体） | 见 §1–§5；规则模板 `patterns.json` 合并未做 |
| Phase 3 在线可选（双开关 + 脱敏 + 审计） | ⛔ 接口占位 | 有 Protocol/开关/拒绝逻辑，无网络实现、无脱敏流程 |
| Phase 4 运行时验证（引擎计数、V3 关键路径、真机） | ⛔ 未做 | 生成物一致性验证只在构建期（回读内嵌条数），不是真机验证 |
| Phase 5 持续运营（指标 M16–M20、成本、抽样） | ⛔ 未做 | 报告里只有本轮 run 的计数，没有跨 run 指标库 |

---

## 9. 测试与覆盖

`tests/test_localize_mvp.py`（46 个测试，约 2 秒）：

- dry-run 不落盘（整仓文件 sha256 快照相等）；
- `--apply` 幂等（二次运行 0 新增、词典/引擎/patcher sha256 不变）；
- `--apply` 在两个独立仓库里字节一致（确定性）；
- CRLF 保留、键序保留、diff 只多一行逗号；
- QA 拒绝：占位符丢失、URL/文件名/代码标识丢失、HTML 结构变化、空值、带空白键、
  哨兵注入、孤立代理字符、>500 字符、H9 冲突、H21 大小写碰撞、术语缺失；
- 术语/占位符/URL/标识「保真」正例（不应误报）；
- 重建失败自动回滚（删除 `engine_template.js` 让 build 必然失败）；
- `--no-build` 后下一次 `--apply` 能自动修复过期生成物；
- `--waive` 留痕放行；
- 在线 provider 三重拒绝（缺开关 / 缺环境变量 / 都给了但仍 stub）；
- 包内无网络 import + dry-run 无 socket；
- TSV overlay、候选 map 格式、`--provider-cmd` 低置信隔离、人类可读输出。

---

## 10. 证据（可复现命令）

```bash
# 1) 测试
python -m pytest -q
#    本机：127 passed, 1 failed, 34 errors（失败/错误全部为沙箱 %TEMP% ACL 假阴性，见 §11）
python -m pytest tests/test_localize_mvp.py -q     # 46 passed

# 2) 语法
python -m py_compile scripts/*.py scripts/localization/*.py
node --check engine/engine_template.js
node --check engine/ag_localization_engine.js

# 3) 生成物一致性（CI 等价：四项变更作为一个提交时）
python scripts/build.py --no-exe
git diff --exit-code -- scripts/patcher.py engine/ag_localization_engine.js

# 4) 真实候选集 dry-run
python scripts/localize.py release --json
#    exit 2；2 个 H10 blocker；759 条可加、2 条隔离

# 5) 隔离副本里演练 apply（不污染仓库）
#    复制 scripts/build.py + engine/engine_template.js + locales/ 到临时根，然后：
python scripts/localize.py release --repo-root <tmp> --candidates untranslated_candidates.json \
  --apply --waive H10 --json
#    exit 0；761 条入词典（2,816 → 3,577）；build verified；引擎内嵌 3,577 条
#    再跑一次：0 新增，词典/引擎/patcher sha256 不变
#    与仓库版词典相 diff：762 insertions(+), 1 deletion(-)
```

本机实测（Windows 11 / Python 3.13.11 / Node v24.22.1）：

- `pytest tests/test_localize_mvp.py -q` → `46 passed`；
- `pytest -q` → `127 passed, 1 failed, 34 errors`；
- `py_compile`、两次 `node --check` → exit 0；
- `build.py --no-exe` → exit 0，`git diff --exit-code` → exit 0（四项变更同批暂存时）；
- README 计数门禁脚本 → `[+] README counts match locales: 2816 entries / 180 rules`；
- 真实 dry-run → exit 2（2 个 H10 blocker，**这是门禁在正常工作**）；
- 隔离副本 `--apply --waive H10` → exit 0、`engine_entries=3577`、`verified=true`。

---

## 11. 已知限制与诚实声明

1. **不是「无人汉化」**：本 MVP 只把「合并/重建/验证/回滚」自动化了。采集仍靠
   旧提取器产出的 761 条文件（旧提取器会因孤立代理字符崩溃、SNR≈0.21%），翻译
   质量仍由人（或候选文件里已有的译文）决定。达到设计里的 ≤30min/版 还差
   Phase 1（采集重写）与 Phase 4（真机验证）。
2. **`pytest -q` 仍有 1 failed + 34 errors**：全部来自沙箱对
   `%TEMP%\pytest-of-win` 的 ACL 拒绝（`tmp_path` / `TemporaryDirectory()`），
   与本次代码无关；`tests/test_localize_mvp.py` 因此把临时仓库建在
   `<repo>/.pytest_tmp/` 并在结束后清理。未修改任何系统权限。
3. **真实仓库的 `--apply` 没有执行**：对 761 条候选全量落盘会再制造一次
   2,816→3,577 的生成物/README 漂移，并需要先决定那 2 条术语冲突；本次只在隔离
   副本里验证了完整 apply 语义（`--repo-root` 指向副本）。
4. **`patterns.json` 不在本期范围**：动态正则规则的生成/合并/H17–H20 未实现，
   `merge` 只动 `zh-CN.json`。
5. **H14–H20、H22 未实现**：报告每次都会列出，不假装覆盖。
6. **生成物一致性门禁的语义**：`git diff --exit-code` 比较的是工作区与索引；
   当前工作区里词典与生成物都因 Phase 0 修复而处于「已改未提交」状态，因此
   只有在词典 + 生成物 + README 作为同一提交时该门禁才为绿（CI 也是在提交树上
   跑）。本文 §10 用「四项同批暂存 + 临时索引」复现了这个等价条件，没有动真实
   git 索引/历史。
7. **未验证真实客户端**：没有 patch/restore 任何已安装的 Antigravity，也没有
   运行时命中率数据（那需要 Phase 4 的引擎计数器，而本 MVP 按约定不改生成物）。

---

## 12. 下一步建议（按性价比）

1. 处理真实候选文件里的 2 条 H10 冲突（改译文或正式 `--waive`），让默认 dry-run
   变绿；
2. 把 `localize release --apply` 接进 CI 的「词典 + 生成物同批提交」检查（离线、
   零网络，可直接跑）；
3. Phase 1：重写提取器（净化代理字符、四级漏斗、候选上限），把 SNR 从 0.21%
   提到 ≥30%，否则自动化的上游始终是噪声；
4. Phase 4：给引擎加命中/未命中计数与上下文导出，才有「这次汉化好了多少」；
5. Phase 3：在线 provider 按设计接双开关 + 脱敏 + 预算；不接也能用，接了要能审计。
