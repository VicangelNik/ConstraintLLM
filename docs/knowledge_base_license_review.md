# 知识库开源许可与来源风险复核

## 结论

对 `data/knowledge_base.json` 的当前结论如下：

- 从**测试集泄露**角度看：风险较低，可以公开作为 `RAG/CARM` 的知识库。
- 从**开源许可/来源可追溯性**角度看：风险为**中等**，可以随项目一同发布，但应明确标注其为**衍生型研究知识库**，并保留来源与风险说明。

换句话说：

- **可以开源**；
- 但**不建议把它表述为“完全原创、逐条来源清晰的原生数据集”**；
- 更适合表述为：`ConstraintLLM` 开源版附带的检索知识库，用于研究复现。

## 本地复核结果

### 1. 与当前开源版 `IndusCP` 测试集的泄露检查

本地程序复核结果：

- 知识库文件：`/home/shiwc24/code/RAG/data/csp_train_data4.json`
- 开源测试集：`/home/shiwc24/code/RAG/open_source_release/data/induscp/statements.json`
- 知识库条数：149
- 测试集条数：155
- 同名题重合：0
- 题面精确重合：0
- 代码精确重合：0

此外，历史审计报告也针对同一知识库做过复核：

- `result/audit/experiment_data_leakage_report_20260309_002738.md`
- `result/audit/leakage_local_model_report_20260309_002150.md`

这些报告的结论也是：

- 题面高风险重复：0
- 代码高风险重复：0

因此，从训练/检索语料对测试集的直接泄露角度看，这份知识库当前**没有发现明显问题**。

### 2. 仓库内来源反查

本地反查显示：

- `knowledge_base.json` 来自 `data/csp_train_data4.json`
- `csp_train_data4.json` 与 `csp_train_data3.json` 的题名重合度极高（147/149）
- 仓库中同时存在 `data/cp-bench-dataset.jsonl` 与 `data/cp-bench/`，其元数据明确指向多个公开约束编程来源

这说明当前知识库大概率是由公开约束编程问题资源**整理、改写、筛选**后形成的研究用检索语料，而不是完全从零独立创作的数据。

## 公开来源与许可信息

以下是本次复核中能确认到的主要公开来源与许可信号。

### A. CP-Bench

公开数据卡显示 `CP-Bench` 数据集采用 `Apache-2.0` 许可，并说明其来源于多个公开约束编程资源。

风险判断：**低到中**

说明：如果 `knowledge_base.json` 的相当一部分条目是由 `CP-Bench` 继续改写整理而来，那么主许可方向偏宽松；但仍建议保留来源说明，不要把它当成无来源衍生限制的数据。

### B. CPMpy

`CPMpy` 官方仓库公开说明其项目使用 `Apache 2.0` 许可。

风险判断：**低**

说明：若知识库中的部分问题描述或模型源自 `CPMpy examples`，在保留署名与许可信息的前提下，风险较低。

### C. CSPLib

`CSPLib` 官方网站注明其内容采用 `CC BY 4.0` 许可。

风险判断：**低到中**

说明：`CC BY 4.0` 允许再分发与改编，但要求适当署名。因此，如果知识库条目来源于 `CSPLib` 问题说明或模型描述，建议在项目文档中明确整体来源包含 `CSPLib`。

### D. XCSP3 / XCSP 基准

`XCSP3` 官方页面注明：

- 规范说明使用 `CC BY-SA 4.0`
- 派生软件与 benchmarks 使用 `MIT`

风险判断：**低到中**

说明：如果知识库中的部分 benchmark 来自 XCSP 体系，许可总体可兼容开源发布，但仍建议在来源说明中保留 XCSP 系列引用。

### E. MiniZinc Challenge

MiniZinc Challenge 官方规则页面明确写到：提交的 benchmark 问题原则上应置于 `MIT` 许可下，除非提交人与主办方另有约定。

风险判断：**中**

说明：这给出一个较好的正向许可信号，但它不能自动证明知识库中所有历史 challenge 相关条目都可无条件重新打包。缺少逐条 provenance 时，仍应保守处理。

### F. 其他来源（如 Hakan 示例、课程材料等）

从本地 `cp-bench` 元数据看，知识库可能还间接涉及：

- `hakan_examples`
- `aplai_course`
- 以及其他社区示例

这些来源在当前知识库文件本体中**没有逐条保留来源字段**，本次也**没有为每一条样本找到统一、明确、逐项可验证的许可声明**。

风险判断：**中到偏高**

说明：这部分不是说一定不能开源，而是说**来源可追溯性不足**。这正是当前知识库开源的主要风险点。

## 风险汇总

### 泄露风险

- 结论：**低**
- 原因：没有发现与当前 `IndusCP` 测试集的同名、题面精确重合或代码精确重合。

### 版权/许可风险

- 结论：**中等**
- 原因：
  - 知识库是衍生整理产物；
  - 上游来源可能混合了多种公开资源；
  - 当前文件缺少逐条来源与许可字段。

### 当前最主要的问题

不是“明显侵权证据”，而是：

- **逐条 provenance 缺失**；
- **无法对 149 条样本逐一给出同等强度的许可证明**。

## 发布建议

建议按以下方式发布：

1. 将该文件以 `data/knowledge_base.json` 名义发布。
2. 在 README 中明确其用途：`RAG/CARM` 的检索知识库。
3. 在文档中明确其性质：由公开约束编程资源整理/改写而成的研究知识库。
4. 保留本风险说明文档，不删除。
5. 后续如要进一步降低风险，建议补一份 `knowledge_base_provenance.json`，逐条记录原始来源。

## 参考来源

- CPMpy 官方仓库（Apache 2.0）: https://github.com/CPMpy/cpmpy
- CSPLib 官方站点（CC BY 4.0）: https://www.csplib.org/
- XCSP3 官方站点（CC BY-SA 4.0 / MIT）: https://xcsp.org/
- MiniZinc Challenge 2021 Rules（benchmark 提交默认 MIT）: https://www.minizinc.org/challenge/2021/rules/
- MiniZinc Challenge 2023 Rules（benchmark 提交默认 MIT）: https://www.minizinc.org/challenge/2023/rules/
- CP-Bench 数据卡（Apache-2.0）: https://huggingface.co/datasets/kostis-init/CP-Bench
