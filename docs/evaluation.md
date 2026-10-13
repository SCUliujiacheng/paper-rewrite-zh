# 测试与限制

这里把三件事分开记录：程序是否按预期工作、模型是否真的生成了改写、检测平台是否给了不同分数。前一项通过，不能推出后一项通过。

## 软件测试

Python 测试覆盖文本结构、数字与引文、候选选择、模型错误、API 的本机访问限制、实际断开连接后的取消，以及检测报告校验。模型和检测器的接口测试使用明确标记的夹具，不把预设输出计为真实模型效果。

前端测试覆盖导入、改写参数、取消、修改输入后旧报告失效、两种界面语言、JSON 往返导入及文本安全渲染。浏览器检查另看桌面和手机宽度的实际布局。GitHub Actions 会运行 Windows / Linux 的 Python 测试、前端测试及依赖审计；最新状态以该仓库的 Actions 页面为准。

```sh
uv run pytest -q
uv run ruff check src tests scripts
npm --prefix web test
npm --prefix web run build
npm --prefix web audit
```

## 真实模型复现

固定压力输入位于 [`data/smoke.jsonl`](../data/smoke.jsonl)：中文 8 段、英文 6 段，全部是虚构的学术描述。补充的 [`data/prose.jsonl`](../data/prose.jsonl) 含中文 6 段、英文 4 段方法设计草稿，写的是尚未实施的方案。它们已经用于开发，不能称为未见测试集。保护词随样例公开；原始输出不应为了展示效果而删改。

启动本机模型后，可在仓库根目录运行：

```sh
uv run python scripts/evaluate.py --backend qwen --output artifacts/my-run.json --candidates 2
```

这条命令不会自行检测外部平台，也不会覆盖已有报告。为记录实际文件，可加上 `--model-file`、`--model-repo`、`--model-revision`、`--runtime`。脚本计算本地文件的 SHA-256；仓库名、修订和运行时描述由操作者提供。文件哈希不能独立证明 HTTP 服务加载的是同一个文件，所以报告保留 `backend_identity_verification: not_verified`，不伪造远程证明。

运行报告中的指标：

| 字段 | 含义 |
| --- | --- |
| `changed_cases` | 最终输出与原文不同的样例数；不是“降 AI 率成功数” |
| `completed` | 所有可处理段落均产生被当前选择策略采用的不同文本；不是质量判定 |
| `partial` | 有改写，但另有段落被保留或失败 |
| `unchanged` | 没有候选被选中，或没有可改写正文 |
| `failed` | 没有成功改写且出现模型错误 |
| `rejected_candidates` / `hard_blocked_candidates` | 被硬性差异拦下的候选数，原文和候选都留在 JSON |
| `warning_only_withheld_candidates` | 没有硬性差异、但因为风险提示而暂不采用的候选数 |
| `warning_cases` | 出现否定或确定性等警告的样例数 |
| `total_seconds` | 本次逐段处理耗时，不是跨硬件性能排名 |

规则检查是为了发现一部分容易看漏的改动。它不能理解所有实体与数值关系，不能证明引用确实支持论点，也不能保证模型没有改变因果、方法细节或适用范围。少量样例没有出现错误，不代表真实论文上不会发生。

## 已记录的开发实验

2026-10-14 第二轮增加了整数记法、许可、要求、来源及有限用途表达检查，并修正 Qwen 正文输入的转义方式。新配置为 `qwen_academic_editing_chat_v3_literal`；温度和 presence penalty 未改。最终完整开发集重跑结果为中文压力 2/8、中文方法草稿 3/6、英文压力 4/6、英文方法草稿 2/4 个最终文本发生变化。40 个旧候选的离线重放补拦两条来源声明变化、解除一条数字记法误报。详情见[第二轮记录](core-iteration-2026-10-14.md)。这些仍不是保真率或降分成功率。

**下面到外部检测章节之前是 v0.1.0 的历史过程。** 其中的“当前/发布配置”和测试数量均指当时版本，原始报告未覆盖。

本机为 Windows、RTX 4050 Laptop 6 GB，运行 llama.cpp b11583。以下是软件实际运行记录，不是人工评分或检测降分排名。输入集全部公开，文件里的输出没有为展示而润色。记录时间为 UTC，文件名日期按开发机器所在时区。

| 实验 | 中文被自动采用 | 英文被自动采用 | 说明 |
| --- | --- | --- | --- |
| [初次 IQ2 压力测试](../artifacts/smoke-2026-10-14.json) | 3 / 8 | 4 / 6 | 旧策略仅拒绝硬差异；其中存在被采用的错误结论，不能作为成功样例数 |
| [IQ2 方法草稿，温度 1.0](../artifacts/prose-iq2-t1-2026-10-14.json) | 0 / 6 | 1 / 4 | 新策略：任何检查项都暂不采用 |
| [IQ2 方法草稿，温度 0.35](../artifacts/prose-iq2-t035-2026-10-14.json) | 3 / 6 | 4 / 4 | 同一方法草稿集及新策略，低温采样对照；仍有重复、冗长等问题 |
| [Qwen Q5 压力测试，提示 v1](../artifacts/smoke-qwen-q5-2026-10-14.json) | 5 / 8 | 2 / 6 | 部分只是空格或冠词调整，另有内容遗漏与状态变化 |
| [Qwen Q5 方法草稿，提示 v1](../artifacts/prose-qwen-q5-2026-10-14.json) | 3 / 6 | 2 / 4 | 存在只给术语加括号、将拟议操作改为现在时的问题 |
| [Qwen Q5 压力测试，提示 v2](../artifacts/smoke-qwen-q5-v2-2026-10-14.json) | 0 / 8 | 5 / 6 | 当前指令与新增情态词检查；中文全部保留原文，英文仍有说明遗漏 |
| [Qwen Q5 方法草稿，提示 v2](../artifacts/prose-qwen-q5-v2-2026-10-14.json) | 5 / 6 | 1 / 4 | 当前配置；采用数不等于质量评分，仍需逐句复核 |
| [发布配置：压力测试](../artifacts/smoke-qwen-q5-release-2026-10-14.json) | 0 / 8 | 5 / 6 | 提示 v2 加中英文计划语气检查，中文压力样例全部保留原文 |
| [发布配置：方法草稿](../artifacts/prose-qwen-q5-release-2026-10-14.json) | 4 / 6 | 1 / 4 | `prose-zh-06` 的计划语气变化被提示，原文保留；其余限制仍在 |

“被自动采用”严格指最终文本与原文不同，连新增空格也算在内，并非有效润色数、保真率或降分成功数。检查器会漏检，也会误报；这些数字不适合用来给模型排质量名次。

### 一次明确的失败，以及由此改动的处理方式

初次压力测试的 `zh-03` 中，原文是“未观察到稳定性随路径长度单调增加”，模型却写出了“路径越长越没有稳定性”。未发现递增关系，不能推出递减关系。旧版虽然提示否定措辞变化，仍选中了这个候选，这是处理策略的缺陷。

当前 `no_audit_issues_v1` 策略把警告候选也留在核对区，不直接拼进改写稿。旧文件保留旧结果，没有倒改成修复后的数字。修复不等于解决语义理解：计数规则可能漏掉别的结论变化，也会把合理的同义改写拦下来。比如“3名”改成“3个”、中文数词改成阿拉伯数字，可能需要人工查看。

我们还尝试过替换成保留学术语气的提示，结果见[提示探查](../artifacts/prompt-probe-iq2-2026-10-14.json)。这次只选择了 4 段中文和 1 段英文作诊断，不是独立测试集；温度 1.0，完整提示与两个种子的输出都在文件里。它仍出现了口语化、添加内容和不流畅的问题，因此没有仅凭改提示就宣布质量问题解决。

人工修订可以在网页右侧完成。“重新核对”只检查当前稿；JSON 中的原始模型报告不会被覆盖，人工稿放在 `manual_revision`。`checked` 仅表示执行过检查，里面仍可能有错误项，不能理解为人工批准或论文验收。

### Qwen 的初次结果同样有漏检

Qwen 使用固定的 Q5_K_M 文件，温度0.7；完整文件哈希与提示哈希见各运行记录。两组初次运行合计24个样例、40个候选，12个最终文本发生变化，但不能把12/24叫作成功率。开发时的代理文本检查发现：

- `en-05` 删掉了“引文是占位符、场景仅用于测试”的整句说明。其余虚构提示仍在，但来源声明和用途说明确实丢失了。
- `prose-en-02` 把 `would ask/include/retain` 改成 `asks/includes/retains`。后来加入了 `would`、`should` 词频变化警告；原始案例回归测试现在会保留原文。相同词频下的含义变化仍可能漏检。
- `zh-04` 把“重复引用需要完整保留”改成“重复引用已完整保留”，从要求变成了完成声明。规则没有识别这一变化。
- `zh-03/05/07` 只增加空格，`en-02` 只删掉一个冠词，`prose-zh-02` 和 `prose-en-03` 只给术语加括号。这些变化不能当作明显改善表达的证据。

保守检查也有代价：本次“没有→未”等近义替换被提示；数字写法、保护词内部空格也可能被拦下。`zh-06` 中紧邻网址的中文后文被网址规则一起识别，造成边界误报。网址前后加空格或使用 Markdown 链接能让边界更清楚，但不能解决所有歧义。

随后在固定开发集的5个案例上做了[提示诊断](../artifacts/prompt-probe-qwen-2026-10-14.json)，每案使用两个种子，完整指令和输出都保留。修订指令更明确地要求处理冗长句式、保留假设语气与声明、不要给术语添加装饰括号；这不等于已解决模型问题。所有上述审阅均为开发中的代理检查，不是独立人工盲评。

当前发布使用 `qwen_academic_editing_chat_v2` 指令，重新运行两套完整语料后另存了 v2 报告。中文压力集8段全部因检查项保留原文，方法草稿6段中5段采用了候选；英文压力集6段中5段采用候选，方法草稿4段中1段采用。v2 仍在 `en-05` 丢失同一句来源与用途说明；`en-02` 的 `invented→introduced` 弱化了原创归属表达；`prose-zh-06` 将“拟……”改为“将……”，并将“确认可以提供”改成“确认提供”，弱化了许可限定。这些都说明不能宣称完整语义保留。

`prose-en-02` 因数字写法变化保留原文；不能把这次保留全归功于情态词修复，情态词修复由固定原始失败对的回归测试单独证明。

发布前又加入中文“计划”“打算”和常见“拟……”表达的词频提示，排除“模拟”“虚拟”“拟合”“拟人”“拟声”等常见非计划用法。固定的 `prose-zh-06` 失败候选现在会被保留供人工核对。这是词面检查，不是中文语义分析器：它仍可能误报近义替换，也不能单独识别“可以提供→提供”这样的许可限定变化。

最终两套语料再次完整运行，结果保存在文件名含 `release` 的报告中，没有覆盖旧文件。最终中文压力集0/8、中文方法草稿4/6、英文压力集5/6、英文方法草稿1/4的最终文本发生变化。用途是确认当前程序、模型与记录流程确实运行；不是质量验收结论。Windows 本地软件检查为247项 Python 测试通过、1项符号链接测试因平台权限跳过；45项前端测试通过，构建与依赖审计通过。跨平台 CI 以各仓库 Actions 的实际结果为准。

## 首次外部网页检测

使用 GPTZero 官方网页 Basic Scan 对 v0.1.0 的公开合成方法草稿做了预先约定的观测。六段中文合成一份，原稿和最终稿均显示 AI 文档类别概率 99%（Model 4.1m）；该界面将中文计为 6 words，提示不足 100 words、结果可能不准。四段英文合成原稿显示 100%（4.1o），改写稿提交时要求注册，且仍显示 Text changed，因此未计入有效结果。未绕限额、注册或付费。每种语言只是一份合成文，不把段落数算作独立观测。

[原始文本、输入哈希、UTC 时间、可见结果与截图](../artifacts/gptzero-ui-2026-10-14/observations.json)均已保留。中文配对没有降分；英文没有有效配对结论。这些是网页观察，不是本项目 API 适配器的生产验证；真实密钥调用仍未验证，也没有知网、维普、万方、Turnitin 等平台的结果。

如果后续补充效果评测，应单独列出：检测器和版本、测试时间、文本许可与来源、原文/改写哈希、原始报告、失败样例、语义复核方法和费用。不要只展示几段成功样例，也不要把不同供应商的分数合成一个“通用 AI 率”。

## English summary

Software correctness, actual rewriting, and detector effectiveness are separate questions. The two synthetic development corpora contain 14 Chinese and 10 English passages in total; they are not held-out benchmarks. `changed_cases` counts any textual difference, including whitespace, not useful edits or detector wins. JSON reports retain every attempted candidate and error. Local artifact hashes verify a file, not the identity of a running server.

The first humanizer IQ2 run accepted a conclusion reversal in `zh-03`; all warnings now withhold automatic selection. Its lower-temperature prose run was more readable in some cases but still repetitive. The first Qwen Q5 runs changed 12/24 outputs, including cosmetic-only edits, lost provenance disclaimers (`en-05`), a requirement turned into a completion statement (`zh-04`), and hypothetical procedures changed to present tense (`prose-en-02`). The last failure prompted `would`/`should` count warnings and a regression test. Other semantic omissions and Chinese URL-boundary false positives remain known limitations.

The Qwen prompt probe uses five selected development cases and two seeds, not an independent benchmark. Developer-agent review is not independent human quality assessment. At v0.1.0 publication no commercial detector had been measured; the later limited web observation below does not establish effectiveness. Checks do not establish semantic equivalence or human authorship. Manual edits are exported separately in `manual_revision`; `checked` means a check ran, not that the text was approved.

The released Qwen v2 prompt was rerun on both full corpora. Automatic selections were 0/8 Chinese stress cases, 5/6 Chinese prose cases, 5/6 English stress cases and 1/4 English prose cases. All original v1 files remain available. The disclaimer omission in `en-05` persists; this release does not establish complete semantic preservation or reliably better prose. Its primary verified outcome is a runnable, reviewable local editing workflow, not a detector-bypass product.

After adding bounded Chinese proposal-marker warnings, both corpora were run again with the final release configuration (`*-release-*.json`). The final counts are 0/8 Chinese stress, 4/6 Chinese prose, 5/6 English stress and 1/4 English prose, with `prose-zh-06` now retained. Source/permission omissions are still possible. Local Windows checks passed 247 Python tests (one platform-permission skip), 45 frontend tests, build and dependency audits. Consult each repository's Actions for actual cross-platform CI results.

The second iteration uses literal manuscript input (`qwen_academic_editing_chat_v3_literal`) with unchanged sampling and bounded quantity, permission, requirement, provenance, purpose and degree-hedge checks. Final raw runs selected 2/8 Chinese stress, 3/6 Chinese prose, 4/6 English stress and 2/4 English prose outputs; these are selection counts, not quality scores. Frozen-candidate replay newly withholds two provenance failures and releases one numeric-notation false positive. The official GPTZero web UI showed 99% before and after one Chinese composite, with an under-100-word warning; an English source showed 100%, but the after-scan hit a registration limit and is not a valid result. See the [second-iteration record](core-iteration-2026-10-14.md) for evidence and remaining limits.
