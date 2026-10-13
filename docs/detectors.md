# 外部检测 / External detection

首次真实网页观测：GPTZero 对一份中文合成原稿及其改写稿均显示 99%，没有降分；界面同时提示中文被计为 6 words、结果可能不准。英文配对因注册/额度限制未完成。[原始证据与边界](core-iteration-2026-10-14.md)公开。这不验证本项目 API 适配器：传输层测试仍使用本地 HTTP 响应夹具，未调用付费 API。检测分数不能证明作者身份、学术诚信或语义等价。

The first live web observation showed 99% before and after one Chinese synthetic composite, with a six-word/short-text warning. The English pair was blocked by registration/quota. [Evidence and limits](core-iteration-2026-10-14.md) are public. API transport tests still use local HTTP fixtures, without paid API calls; the web observation does not validate the adapter. Detector predictions do not prove authorship, academic integrity, or semantic equivalence.

## 显式授权 / Explicit consent

`GPTZeroDetector(api_key, transport=None, *, timeout_seconds=30)` 提供异步 `compare(source, candidate, consent: bool) -> DetectorReport`。仅 `consent is True` 且密钥非空时，才顺序上传两篇文本至固定的官方 `https://api.gptzero.me/v2/predict/text` 端点；不会重试、自动评测或跟随重定向。调用方只从环境变量读取密钥，不能回显。未同意返回 `not_run`；同意但无密钥返回 `not_configured`；失败返回安全错误代码。文本只在内存处理。

Only literal `True` consent plus a configured key permits two sequential uploads to the fixed official endpoint. There are no retries, automatic evaluations, or redirect following. The caller reads the key from an environment variable and must not echo it. Absent consent returns `not_run`; absent configuration returns `not_configured`; failures return safe codes. Text remains in memory.

## 报告接口 / Report contract

报告可通过 `model_dump(mode="json")` 导出：`detector`, `status`, `model_version`, `measured_at`, `source_sha256`, `output_sha256`, `before`, `after`, `error`, `provenance`, `user_supplied`。状态只允许 `completed | not_configured | not_run | error`。每侧测量包含 `probabilities`, `classification`, `raw`, `model_version`；保留经过校验的原始文档概率、分类和可用的置信字段，不保留供应商返回的文本或未知元数据。概率必须是有限的0–1数值，类别概率之和容差为0.001。不同版本会保留在各侧；未返回版本或双方不同则报告整体为 `unknown`。时间使用带时区的 UTC。

Reports export with `model_dump(mode="json")`. Each side retains validated raw document probabilities and classification, with available confidence fields. Unknown metadata and returned text are excluded. Scores must be finite numbers in [0,1], with class probabilities summing to one within 0.001. Each measurement carries its version; missing or unequal versions yield overall `unknown`. Timestamps are timezone-aware UTC.

`validate_manual_report(payload, source, candidate) -> DetectorReport` 只接收该结构的 GPTZero 报告，重新计算 UTF-8 SHA-256 并校验分数与原始字段一致、时间和状态一致；不一致抛出 `ValueError`。结果强制设置 `provenance="user_supplied"` 与 `user_supplied=true`，不信任导入文件中宣称 API 验证的标志。哈希绑定仅说明报告对应给定文本，不认证供应商或实际检测过程。

Manual import validates the same GPTZero report shape, exact UTF-8 text hashes, raw-score consistency, timestamps, and status. Invalid input raises `ValueError`. The result is always marked `user_supplied`, regardless of incoming flags. Hash binding does not authenticate the provider or establish that a detector actually ran.

## 官方契约来源 / Official contract sources

2026-10-14 核对：[GPTZero 开发者页面](https://gptzero.me/developers)给出 v2 文本端点、`document` 请求字段和 `x-api-key`；[官方结果说明](https://support.gptzero.me/articles/8947054519-how-do-i-use-and-interpret-the-results-from-your-api)说明 `document_classification`、`class_probabilities` 与置信字段。[官方概率说明](https://gptzero.me/news/chicago-booth-2026/)明确文档比较应使用类别概率而不是句级概率均值，并介绍扩展类别。官方链接的 Stoplight 详细文档路由在本次核对时返回404；尚未使用真实密钥验证返回信封与版本字段。

Checked on 2026-10-14: the official developer and support pages document the endpoint, request/authentication fields, classification, and class probabilities. The official probability article distinguishes document class probabilities from sentence averages. The linked detailed Stoplight route returned 404 during this check. Response envelope and version fields have not been verified with a real key.

## 中文支持与试用范围 / Chinese support and trial scope

2026-10-14 核对的 [GPTZero 官方语言支持页](https://support.gptzero.me/articles/1682612063-what-languages-does-gptzero-support)明确列出中文。本项目只有上述合成材料的网页观察，没有真实中文论文基准，也没有验证其他论文平台的结果。[开发者页面](https://gptzero.me/developers)提醒检测并非完全准确，对较长文本和英文散文表现更好，结果应作为进一步核查的线索。

GPTZero lists Chinese among its supported languages. The limited synthetic web observation above is not a Chinese-paper benchmark, API validation, or evidence from other paper platforms. The official developer page warns that detection is imperfect, performs best on longer texts and English prose, and should inform further review.

[官方免费试用说明](https://support.gptzero.me/articles/7472477101-can-i-try-the-api-for-free)提到有限次数的免账号、免密钥 API 试用。不过，该说明及文档首页指向的两个试用路由在本次核对时均返回404；尚未核实可用且中文范围明确的官方免密钥检测端点。当前适配器仍要求密钥与用户明确同意，没有接入未验证的试用或网页内部接口。

GPTZero documents a limited no-account, no-key API trial. Both linked trial documentation routes returned 404 during this check, so an available official no-key endpoint with a clear Chinese scope has not been verified. The current adapter requires a key and explicit consent; it does not use an unverified trial or private website interface.

## 合成样本 / Synthetic corpus

`data/smoke.jsonl` 包含14段项目原创样例（中文8段、英文6段）；`data/prose.jsonl` 补充10段尚未实施的方法设计初稿（中文6段、英文4段），共24段。两个集合均为 AI 辅助编写的 CC0 开发材料。冒烟样例中的实验、数值和引文占位符均为虚构；补充样例描述拟议方案，没有宣称完成研究或获得结果。它们不是留出集或人类论文语料，不能支持泛化或检测器效果结论；评测应公开全部案例与原始结果。

`data/smoke.jsonl` contains 14 project-authored snippets (8 Chinese, 6 English), and `data/prose.jsonl` adds 10 methodological proposals (6 Chinese, 4 English), totaling 24. Both are AI-assisted CC0 development fixtures, not held-out data or a human-paper corpus. Smoke experiments, numbers, and citation placeholders are invented; the supplement describes proposed research, without completed-study or result claims. Publish every case and its raw outcome. Neither corpus establishes generalization or detector effectiveness.
