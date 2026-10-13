# 改稿台

把 AI 初稿改得自然一些，也把改动摊开来检查。

当前为实验性预览版。工作台和本地模型链路可以运行，输出仍有说明遗漏、语气变化和改动很少的问题，需要逐段修改与复核。已发现的问题和原始实验记录一并公开，不能作为直接投稿或通过检测的保证。

写论文时，有些段落意思并不复杂，生成出来却绕了好几句。直接让模型重写，又容易把“可能”改成“证明”，或者顺手改掉一个数字。改稿台把这两件事放在一起：本地模型逐段改写，旁边保留原文、被拒绝的候选和检查记录。

[发布下载](https://github.com/SCUliujiacheng/paper-rewrite-zh/releases) · [启动说明](docs/downloads.md) · [安装模型](docs/model-setup.md) · [检测结果说明](docs/detectors.md) · [测试与限制](docs/evaluation.md) · [English](README.en.md)

## 可以做什么

- 处理中文和英文的 TXT / Markdown，左右对照原稿和改写稿。
- 指定不能改动的术语，检查数字、单位、引文、公式和网址。有检查项或风险提示的候选不会自动替换原文。
- 直接修改右侧稿件，再点“重新核对”。模型原始记录不覆盖，人工修改单独保存到导出报告。
- 保留标题、表格、代码和参考文献；导出文本及含候选记录的 JSON。
- 单独比较检测结果。支持 GPTZero 官方 API 适配和已有报告导入，不把“未检测”显示成 0%。

改写可使用已有的 [humanizer 专项模型](https://huggingface.co/jialinyyzz/humanizer) 或 [Qwen3.5-4B 通用指令模型](https://huggingface.co/Qwen/Qwen3.5-4B)，不是本项目从零训练的模型。这里实现的是工作台、逐段处理、内容检查和报告。Qwen 路径并非专项检测规避训练；上游归属见 [NOTICE](NOTICE)。

**首次真实网页对照没有降分：GPTZero 对一份中文合成原稿及其改写稿均显示 99%。** 该入口同时提示文本不足 100 words、结果可能不准；英文配对因免费额度/注册要求未完成。[原始记录与限制](docs/core-iteration-2026-10-14.md)均已公开。这不是论文场景通过率，也不承诺通过知网、维普、万方、Turnitin 或其他检测。规则不能证明语义完全一致；使用时请核对内容并遵守所在机构的 AI 使用与披露要求。

## 本地运行

如果下载 Release 中带前端的 ZIP，可以省去 Node.js 和前端构建步骤，见[下载说明](docs/downloads.md)。下面是从 Git 源码运行的方法。

需要 Python 3.12、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 Node.js 22.20 或更新的 22.x 版本。模型另行安装，需要数 GB 存储和足够的运行内存；完整步骤在[模型安装说明](docs/model-setup.md)。

按安装说明启动本机 Qwen 模型服务，地址为 `http://127.0.0.1:8091`。再在仓库根目录运行：

```sh
uv sync --locked --python 3.12
npm --prefix web ci
npm --prefix web run build
uv run paper-rewrite serve --backend qwen --open
```

浏览器打开 `http://127.0.0.1:8765`。先用“载入示例”试一段，再导入自己的稿件。模型未连接时按钮不可用，界面会提示启动服务。

每篇最多 12000 字符、60 段，每个正文段落最多 1000 字符。一次生成最多尝试 3 个候选，默认 2 个；选中首个没有检查项的改写后就停止，不会循环调用检测器刷分。规则比较保守，同义改写也可能需要人工核对。当前不支持直接读取 Word / PDF。

## 命令行

```sh
# 改写；已有文件不会被覆盖
uv run paper-rewrite rewrite draft.txt -o revised.txt --report review.json --backend qwen --language zh --keep BM25

# 不调用模型，只比较两个文件
uv run paper-rewrite check draft.txt revised.txt --keep BM25
```

`rewrite` 返回码：`0` 为所有可处理段落完成改写，`2` 为部分改写或保留原文，`3` 为模型失败，`1` 为输入或文件错误。**返回 0 也不代表可以直接投稿。** `check` 返回 2 表示发现必须核对的硬性差异。

## 稿件会去哪里

默认只在本机浏览器、本机服务和本机模型之间传递；应用不保存稿件，不加分析统计，也不会自动发送给检测平台。导出的文件由你保管。

只有配置 `GPTZERO_API_KEY`、勾选发送授权并点击“运行外部检测”后，原文和改写稿才会发给 GPTZero，可能收费。取消请求会终止后续处理，但已经发出的文本无法撤回。不要把密钥放进前端或提交到 Git。

应用仅面向个人本机使用，没有账号和多人访问隔离；不要把服务绑定公网，也不要直接当成团队 SaaS 部署。

## 开发与复现

```sh
uv run pytest
uv run ruff check src tests scripts
npm --prefix web test
npm --prefix web run build
```

`data/smoke.jsonl` 包含 8 段中文、6 段英文精度压力样例；`data/prose.jsonl` 另有 6 段中文、4 段英文方法设计草稿。全部为项目编写的合成文本，不是真实论文，也不是未见测试集。运行方法、原始输出和失败说明见[测试与限制](docs/evaluation.md)。没有用单元测试通过数代替模型效果。

代码按处理流程分为 `documents`、`model`、`guards`、`pipeline`、`detectors`；CLI 和网页共用同一套 Python 逻辑。前端在 `web/`，处理过程见[架构说明](docs/architecture.md)。中英文仓库共用代码与测试，仅首页和 `src/paper_rewrite/edition.json` 默认语言不同。发现具体漏检时，请用不含私人稿件的最小例子提 issue。

## 许可

本项目代码使用 Apache-2.0；合成测试语料采用 CC0-1.0。模型、运行时和第三方依赖各自适用其许可。项目许可不授予任何私人稿件、上游训练材料或投稿内容的使用权。
