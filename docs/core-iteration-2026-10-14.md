# 第二轮：保真修复与首次网页检测

这轮先查两件事：已知的内容变化能否被发现，以及真实检测页面有没有给出更低分数。结论不同：几处具体漏检和公式损坏得到了修复，但还没有取得降分证据。项目仍是需要逐段核对的预览工具。

## 真实网页观察

检测前已将[协议](superpowers/specs/2026-10-14-core-effectiveness-design.md)提交到 `fd74ef4`。输入来自 v0.1.0 的公开合成方法草稿：中文六段按顺序合为一份，英文四段合为一份；保留软件未改写的段落。不是挑选低分候选，也不是六次、四次独立测试。

| 文本 | GPTZero 可见模型 | 原稿 | 最终稿 | 能得出的结论 |
| --- | --- | --- | --- | --- |
| 一份中文合成文 | 4.1m | AI 99% | AI 99% | 本次没有下降；原稿与改写稿均有短文本准确性警告 |
| 一份英文合成文 | 原稿 4.1o | AI 100% | 未取得有效结果 | 后稿触发注册/额度限制，不能算配对检测 |

这里的百分数是界面显示的**整篇文档类别概率**，不是论文中 AI 句子所占比例。中文输入为 931 / 922 字符，界面计为 6 words 并提示不足 100 words、结果可能不准确。编辑器规范化段落后显示的字符数也有差别；报告记录了输入字符串与界面计数，不能把输入哈希说成对服务端实际请求的证明。

英文后稿页面仍显示 `Text changed / Scan to update`，并弹出 `Sign up to Continue`。其残留的 100% 和回退模型标识不作为有效后稿分数。到这里停止了外部检测，没有创建账号、付费、解验证码或换身份绕额度。

所有材料是项目的 CC0 合成文本，没有上传私人论文。网页观察不验证项目里的 API 适配器，也不能替代知网、维普、万方、Turnitin 或其他平台的测量。

- [原始文本、时间、输入哈希和观测元数据](../artifacts/gptzero-ui-2026-10-14/observations.json)
- [中文原稿截图](../artifacts/gptzero-ui-2026-10-14/gptzero-zh-before.jpg) / [中文改写稿截图](../artifacts/gptzero-ui-2026-10-14/gptzero-zh-after.jpg)
- [英文原稿截图](../artifacts/gptzero-ui-2026-10-14/gptzero-en-before.jpg) / [英文后稿被限额的截图](../artifacts/gptzero-ui-2026-10-14/gptzero-en-after-blocked.jpg)

同目录的 `.dom.txt` 保留实际可见文本。网页内容与截图属于供应商界面证据，不属于本项目 CC0 语料许可范围。

报告文件引用的 `artifact_sha256` 按 Git 中 LF 字节计算；Windows 工作副本原先的 CRLF 哈希另列为 `captured_*_sha256`。两种文件字节不能混用。文本输入哈希始终按实际提供给页面的 UTF-8 字符串计算。

## 改了哪些实际问题

1. 支持明确数量结构中的英文 zero–twenty、中文常用 0–99 整数记法。例如 `5 times / five times`、`五次 / 5次`。仍区分精度、单位、正负和上下界，不把 `3名 / 3组`、`5.0 / 5` 混同。不认识的写法不做宽松换算。
2. 补上有限的许可、要求、来源与用途表达提示。例如“可以提供”被删、“需要保留”变成“已保留”、引文占位说明消失，或 `would be used to clarify` 被改为 `would clarify`。
3. 新运行中又发现“较为明确”被改成“明确”。加入 `较为 / relatively` 的程度限定提示，两个负例先失败再通过，并另存最终重跑报告。
4. 中文句读结束网址匹配，避免 `https://example.org/path。后文` 被一起当作网址。仍允许中文路径，不将所有汉字直接截掉；网址后没有分隔符的歧义仍存在。
5. Qwen 现在看到原样正文，而非内嵌 JSON 字符串。HTTP 请求本身仍是 JSON；文中的 LaTeX 不再额外显示一层转义。输入含分隔标签时选用不冲突的标签。这不是提示注入防御证明，检查与人工复核仍然需要。

这些是词面提示，不是命题对齐。主语交换、相同数值换到不同组、含义相近但不等价的说法仍可能漏检；同义表达也可能误报。任何提示继续阻止自动采用，候选和原因都可查看，`requires_review` 始终为 true。

## 固定旧候选重放

不重新采样，重放 v0.1.0 两份发布报告中的全部 40 个候选。初次重放检查发现，解除数字误报后有一条用途陈述被加强，因而补充用途提示，再做最终重放。

| 决策变化 | 数量 | 案例 |
| --- | --- | --- |
| 原本放行，现在暂缓 | 2 | `en-02/0` 的 invented→introduced；`en-05/0` 整句占位引文和测试用途说明消失 |
| 原本暂缓，现在放行 | 1 | `prose-en-02/1` 的 3→three；保留 would be used to，代理逐句复核未见实质遗漏 |
| 决策未变 | 37 | 包括仍需核对的候选；不等于 37 条都正确 |

[初次重放](../artifacts/core-audit-replay-2026-10-14.json)与[最终重放](../artifacts/core-audit-replay-final-2026-10-14.json)均保留，未覆盖旧输出。审阅是开发代理检查，不是独立人工盲评；不计算保真准确率。

## 输入格式对照

[完整请求与响应](../artifacts/core-prompt-ablation-2026-10-14.json)包含四个已知开发案例、两个种子、三组配置，共 24 个候选。三组分别为 JSON 包装/penalty 1.5、原样正文/1.5、原样正文/0，温度保持 0.7。

- `zh-02`：JSON 组两个种子都多复制一个公式反斜杠；原样正文两组均保留原公式。
- 原样正文同时修改了包装措辞并加入保留反斜杠的要求，所以证据支持这一整组请求配置，不能只归因于序列化方式。
- 原样正文/1.5 仍有 `en-05` 末句丢失。格式修复不解决语义遗漏，新检查将其暂缓。
- penalty 0 在这四案上有部分更好的表现，但数据太少、已用于调试，没有据此调整默认采样。当前仍为 1.5。

提示版本单独标为 `qwen_academic_editing_chat_v3_literal`。两套完整语料重跑的初次文件名包含 `core`，程度限定修复后的最终文件名包含 `core-final`；所有候选均公开。采用计数只说明文本发生变化，哪怕只是冠词或同义词，并非有效润色数。

| 最终运行 | 中文文本发生变化 | 英文文本发生变化 |
| --- | --- | --- |
| [压力集](../artifacts/smoke-qwen-q5-core-final-2026-10-14.json) | 2/8 | 4/6 |
| [方法草稿](../artifacts/prose-qwen-q5-core-final-2026-10-14.json) | 3/6 | 2/4 |

`en-05` 保留原文；`zh-02` 的公式逐字相等；失去“较为”的 `prose-zh-01` 不再自动采用。复合英文数词只作整体保守比对，例如 twenty-one 不能被简化成末尾的 one；并未新增任意英文数词换算。

初次 `core` 运行还发现 `en-04` 的 `is a placeholder` 被写成 `remains a placeholder`，引入继续保持的轻微预设；这种时间含义未被词频规则覆盖。不能声称所有已采用文本含义完全不变。没有独立人工标注集，也没有完成新模型训练。

## English summary

The real GPTZero web comparison did **not** show a reduction: one Chinese synthetic composite scored 99% before and after, with a six-word/under-100-word warning. One English source scored 100%; the after-scan hit registration/quota and is excluded. Raw visible evidence and exact input hashes are linked above. This is a small observation of v0.1.0 output, not the later patch, an API validation, a Chinese-paper benchmark or proof of human authorship.

The patch addresses specific quantity, permission, requirement, provenance, purpose and degree-hedge failures, plus URL punctuation and literal LaTeX transport. Frozen replay of 40 candidates newly withholds two provenance failures and releases one numeric-notation false positive. The raw-input probe contains all 24 responses, including omissions. No default sampling change, new training, human semantic accuracy estimate or universal detector claim is made. A subtle is→remains presupposition and arbitrary entity/value rebindings remain limitations.
