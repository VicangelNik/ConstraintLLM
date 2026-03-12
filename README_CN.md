# ConstraintLLM 开源版本

## 项目简介

本仓库提供论文 **ConstraintLLM: A Neuro-Symbolic Framework for Industrial-Level Constraint Programming** 的开源发布版本。

ConstraintLLM 是一个面向工业级约束规划的神经符号框架。它将大语言模型与符号求解器结合起来，用于自动生成和评测约束规划模型。本次开源版本包含：

- 一个可运行的 ConstraintLLM 最小评测实现；
- 位于 `data/induscp/` 下发布的 `IndusCP` 数据集；
- 位于 `data/knowledge_base.json` 下发布的检索知识库；
- 对 `DIRECT`、`COT`、`RAG`、`CARM` 和 `TOT` 方法的支持。

在本开源版本中，`CARM` 是论文中约束感知检索模块的开源方法命名。

论文页面与下载链接：
- https://aclanthology.org/2025.emnlp-main.809/

## 项目结构

```text
open_source_release/
├── src/constraintllm/        # 核心实验代码
├── data/induscp/             # IndusCP 测试集
├── data/knowledge_base.json  # RAG/CARM/TOT 使用的检索知识库
├── scripts/                  # 快速运行脚本
├── configs/                  # 配置模板
├── outputs/                  # 实验结果汇总与明细
├── logs/                     # 并行运行产生的日志
├── README.md
├── README_CN.md
└── LICENSE
```

## 安装指南

### Linux / macOS

使用以下脚本创建并初始化虚拟环境：

```bash
bash setup_venv.sh
source .venv/bin/activate
```

### Windows

使用以下脚本创建并初始化虚拟环境：

```bat
setup_venv.bat
```

### 求解器与 Java 环境要求

本项目会执行生成出的 PyCSP3 模型，因此底层求解器链路需要一个可用的 Java 运行环境。

推荐环境：
- Python 3.10 或更高版本
- Java 8 或更高版本
- `java` 已加入 `PATH`

快速检查：

```bash
java -version
python --version
```

如果没有安装 Java，请先安装 OpenJDK。即使模型接口配置正确，缺少 Java 也会导致求解阶段失败。
通常 Java 8 及以上即可运行；为获得更稳定的环境，推荐使用 Java 11 及以上版本。

### 模型服务配置

运行实验前，请先配置一个兼容 OpenAI 接口的模型服务：

```bash
export CONSTRAINTLLM_API_BASE="https://api.openai.com/v1"
export CONSTRAINTLLM_API_KEY="YOUR_OPENAI_API_KEY"
export CONSTRAINTLLM_MODEL="gpt-5"
```

## 方法说明

本开源版本支持以下方法：

- `DIRECT`：直接根据题面生成 PyCSP3 代码。
- `COT`：使用带思维引导的提示词生成 PyCSP3 代码。
- `RAG`：基于题面文本与知识库样例的词面重合进行检索。
- `CARM`：基于约束标签重合进行检索。
- `TOT`：先生成多个建模思路，再根据思路生成候选代码，并通过轻量快速检查选择较优候选。

本仓库内置的 `data/knowledge_base.json` 用于 `RAG`、`CARM` 和 `TOT` 的检索，不属于 `IndusCP` 测试集本身。

## 快速开始

运行一个最小的 `COT` 示例，只处理第一个题目：

```bash
PYTHONPATH=src python -m constraintllm.run_csp --method COT --max-items 1
```

运行一个最小的 `RAG` 示例：

```bash
PYTHONPATH=src python -m constraintllm.run_csp --method RAG --max-items 1
```

运行一个最小的 `CARM` 示例：

```bash
PYTHONPATH=src python -m constraintllm.run_csp --method CARM --max-items 1
```

运行一个最小的 `TOT` 示例：

```bash
PYTHONPATH=src python -m constraintllm.run_csp --method TOT --max-items 1
```

## 全量实验示例

使用脚本运行完整实验：

```bash
export CONSTRAINTLLM_API_BASE="https://api.openai.com/v1"
export CONSTRAINTLLM_API_KEY="YOUR_OPENAI_API_KEY"
export CONSTRAINTLLM_MODEL="gpt-5"

bash scripts/run_cot.sh
bash scripts/run_rag.sh
bash scripts/run_carm.sh
bash scripts/run_tot.sh
```

使用并行分片运行：

```bash
export CONSTRAINTLLM_PARALLEL_WORKERS=4
bash scripts/run_rag.sh
```

## 输出结果说明

实验结果会写入 `outputs/`：

- `*_summary.json`：单轮实验或单个分片的汇总统计
- `*_details.json`：逐测试点的明细结果、分数和生成代码

运行日志会写入 `logs/`：

- 父日志：启动器日志
- 分片日志：每个并行分片各自的日志文件

## 已知限制

- 这是一个研究型开源版本，不是生产部署版本。
- 实验速度与稳定性高度依赖模型服务本身以及并发能力。
- 大模型在高并发下可能明显变慢。
- 公开数据中的部分参考输出仍可能需要进一步人工复核。
- 检索知识库是为研究复现目的发布的，不应视为 `IndusCP` 测试集的一部分。
- 知识库来源与许可风险说明见：
  - `docs/knowledge_base_license_review.md`

## 论文引用

如果你使用了本项目，请引用以下论文：

```bibtex
@inproceedings{shi2025constraintllm,
  title={ConstraintLLM: A Neuro-Symbolic Framework for Industrial-Level Constraint Programming},
  author={Shi, Weichun and Liu, Minghao and Zhang, Wanting and Shi, Langchen and Jia, Fuqi and Ma, Feifei and Zhang, Jian},
  booktitle={Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing},
  pages={16010--16030},
  year={2025}
}
```
