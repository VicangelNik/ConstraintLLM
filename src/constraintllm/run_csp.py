from __future__ import annotations

import argparse
from dataclasses import replace
import datetime
import os
from pathlib import Path
import subprocess
import sys

from tqdm import tqdm

from .classify_tag import classify_tag
from .config import COT_SYSTEM_MESSAGE, OUTPUT_ROOT, SYSTEM_MESSAGE_DIRECT, TOT_THOUGHT_SYSTEM_MESSAGE, get_settings
from .data_loader import load_induscp_records, load_retrieval_corpus
from .embedding_retrieval import EmbeddingRetriever
from .llm import get_llm
from .profiler_tool import profiler
from .run_code import evaluate_generated_code
from .tag_based_retrieval import tag_based_retrieval
from .utils import dump_json, ensure_dir, extract_python_code, sanitize_name


def _get_int_env(name: str, default_value: int) -> int:
    """Read an integer environment variable."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default_value
    try:
        return int(raw)
    except ValueError:
        return default_value


def _get_shard_indices(workers: int) -> list[int]:
    """Read shard indices to execute, defaulting to all shards."""
    raw = os.environ.get("CONSTRAINTLLM_SHARD_FILTER", "").strip()
    if not raw:
        return list(range(workers))
    shard_indices: list[int] = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            value = int(token)
        except ValueError:
            raise ValueError(f"Invalid CONSTRAINTLLM_SHARD_FILTER token: {token}") from None
        normalized = value - 1 if value >= 1 else value
        if normalized < 0 or normalized >= workers:
            raise ValueError(f"Shard filter out of range: {value} for workers={workers}")
        if normalized not in shard_indices:
            shard_indices.append(normalized)
    if not shard_indices:
        raise ValueError("CONSTRAINTLLM_SHARD_FILTER is empty after parsing")
    return shard_indices


def _slice_records(records: list, max_items: int) -> list:
    """Slice records by problem limit and shard settings."""
    sliced = records[:max_items] if max_items > 0 else list(records)
    shard_total = _get_int_env("CONSTRAINTLLM_SHARD_TOTAL", 1)
    shard_index = _get_int_env("CONSTRAINTLLM_SHARD_INDEX", 0)
    if shard_total <= 1:
        return sliced
    if shard_index < 0 or shard_index >= shard_total:
        raise ValueError(f"Invalid shard index: {shard_index}/{shard_total}")
    return [record for idx, record in enumerate(sliced) if idx % shard_total == shard_index]


def clip_text(text: str, max_chars: int) -> str:
    """Hard-truncate text by character count."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]..."


def build_reference_prefix(examples: list[dict], settings) -> str:
    """Build a context prefix from retrieved examples."""
    if not examples:
        return ""
    lines = ["Here are some reference problems and PyCSP3 models:"]
    current_length = len(lines[0])
    for index, item in enumerate(examples, start=1):
        example_problem = clip_text(item.get("problem", "").strip(), settings.retrieval_example_problem_max_chars)
        example_code = clip_text(item.get("code", "").strip(), settings.retrieval_example_code_max_chars)
        problem_block = f"Example {index} Problem:\n{example_problem}"
        code_block = f"Example {index} Code:\n```python\n{example_code}\n```"
        projected = current_length + len(problem_block) + len(code_block) + 4
        if projected > settings.retrieval_total_max_chars:
            break
        lines.append(problem_block)
        lines.append(code_block)
        current_length = projected
    return "\n\n".join(lines) + "\n\n"


def prepare_examples(method: str, problem_text: str, record, retrieval_corpus: list[dict], llm, settings, embedding_retriever: EmbeddingRetriever | None = None) -> tuple[list[dict], list[str]]:
    """Prepare retrieved examples and tags for the selected method."""
    if method == "RAG":
        if embedding_retriever is None:
            raise ValueError("RAG requires an embedding retriever")
        return embedding_retriever.topk(problem_text, settings.topk), []
    if method in {"CARM", "TOT"}:
        tags = classify_tag(problem_text, preset_constraints=record.constraints, llm=llm)
        return tag_based_retrieval(tags, retrieval_corpus, settings.topk), tags
    return [], []


def build_method_prompt(method: str, problem_text: str, record, retrieval_corpus: list[dict], llm, settings, embedding_retriever: EmbeddingRetriever | None = None) -> tuple[str, list[str], list[dict]]:
    """Build the input prompt for the selected method."""
    examples, tags = prepare_examples(method, problem_text, record, retrieval_corpus, llm, settings, embedding_retriever=embedding_retriever)
    prompt = build_reference_prefix(examples, settings) + problem_text if examples else problem_text
    return prompt, tags, examples


def generate_code(llm, system_prompt: str, prompt: str) -> str | None:
    """Generate code and retry once at low temperature if needed."""
    try:
        response = llm(system_prompt, prompt, temperature=0.01)
        code = extract_python_code(response)
        if code:
            return code
        retry_response = llm(system_prompt, prompt, temperature=0.0)
        return extract_python_code(retry_response)
    except Exception:
        # Return no code on generation timeout or API errors so the caller can skip the item.
        return None


def generate_thought(llm, prompt: str, temperature: float) -> str:
    """Generate a short modelling plan."""
    return llm(TOT_THOUGHT_SYSTEM_MESSAGE, prompt, temperature=temperature).strip()


def evaluate_candidate_quick(record, code: str, problem_text: str, llm, settings) -> int:
    """Quickly score candidate code on one case to reduce TOT selection cost."""
    quick_settings = replace(settings, cases_per_problem=1, revision_times=0)
    result = evaluate_generated_code(record, code, problem_text, llm=llm, settings=quick_settings)
    return int(result["score"])


def generate_code_with_tot(record, problem_text: str, base_prompt: str, llm, settings) -> str | None:
    """Generate candidates with a lightweight TOT flow and pick the best one."""
    initial_thoughts = max(1, _get_int_env("CONSTRAINTLLM_TOT_INITIAL_THOUGHTS", 2))
    max_depth = max(1, _get_int_env("CONSTRAINTLLM_TOT_MAX_DEPTH", 2))
    branches_per_level = max(1, _get_int_env("CONSTRAINTLLM_TOT_BRANCHES_PER_LEVEL", 2))

    thought_nodes: list[dict] = []
    best_code: str | None = None
    best_score = -1

    for index in range(initial_thoughts):
        thought_prompt = (
            f"{base_prompt}\n\n"
            f"Draft plan {index + 1}:\n"
            "Summarize a modelling approach for this problem."
        )
        try:
            content = generate_thought(llm, thought_prompt, temperature=0.7)
        except Exception:
            continue
        if not content:
            continue
        thought_nodes.append(
            {
                "content": content,
                "score": None,
                "level": 0,
                "parent_idx": None,
                "idx": len(thought_nodes),
            }
        )

    if not thought_nodes:
        return generate_code(llm, SYSTEM_MESSAGE_DIRECT, base_prompt)

    for current_level in range(max_depth):
        current_nodes = [node for node in thought_nodes if node["level"] == current_level]
        for node in current_nodes:
            code_prompt = (
                f"{base_prompt}\n\n"
                "Use the following modelling plan as guidance:\n"
                f"{node['content']}\n\n"
                "Now write the final PyCSP3 code."
            )
            code = generate_code(llm, SYSTEM_MESSAGE_DIRECT, code_prompt)
            if not code:
                node["score"] = -1
                continue
            score = evaluate_candidate_quick(record, code, problem_text, llm, settings)
            node["score"] = score
            if score > best_score:
                best_score = score
                best_code = code

        if current_level >= max_depth - 1:
            break

        ranked_nodes = sorted(
            current_nodes,
            key=lambda item: item["score"] if item["score"] is not None else -1,
            reverse=True,
        )
        parents = [item for item in ranked_nodes[:branches_per_level] if (item["score"] or 0) >= 0]
        for parent in parents:
            refine_prompt = (
                f"{base_prompt}\n\n"
                "Previous modelling plan:\n"
                f"{parent['content']}\n\n"
                "Refine this plan. Focus on missing constraints, objective modelling, and variable definitions."
            )
            try:
                refined = generate_thought(llm, refine_prompt, temperature=0.5)
            except Exception:
                continue
            if not refined:
                continue
            thought_nodes.append(
                {
                    "content": refined,
                    "score": None,
                    "level": current_level + 1,
                    "parent_idx": parent["idx"],
                    "idx": len(thought_nodes),
                }
            )

    if best_code:
        return best_code
    return generate_code(llm, SYSTEM_MESSAGE_DIRECT, base_prompt)


@profiler
def run_experiment(method: str, max_items: int = 0) -> tuple[dict, list[dict]]:
    """Run one experiment pass."""
    settings = get_settings()
    llm = get_llm(settings)
    records = load_induscp_records()
    records = _slice_records(records, max_items)

    retrieval_corpus = []
    embedding_retriever: EmbeddingRetriever | None = None
    if method in {"RAG", "CARM", "TOT"}:
        if not settings.retrieval_corpus:
            raise ValueError(f"{method} requires CONSTRAINTLLM_RETRIEVAL_CORPUS")
        retrieval_corpus = load_retrieval_corpus(settings.retrieval_corpus)
    if method == "RAG":
        if not settings.embedding_model:
            raise ValueError("RAG requires CONSTRAINTLLM_EMBEDDING_MODEL")
        embedding_retriever = EmbeddingRetriever(settings)
        embedding_retriever.build_index(retrieval_corpus)

    total_score = 0
    total_fix_success = 0
    all_details: list[dict] = []
    processed = 0
    skipped = 0

    for record in tqdm(records, total=len(records)):
        try:
            problem_text = clip_text(record.problem, settings.prompt_problem_max_chars)
            prompt, tags, _ = build_method_prompt(method, problem_text, record, retrieval_corpus, llm, settings, embedding_retriever=embedding_retriever)

            if method == "TOT":
                code = generate_code_with_tot(record, problem_text, prompt, llm, settings)
            else:
                system_prompt = COT_SYSTEM_MESSAGE if method == "COT" else SYSTEM_MESSAGE_DIRECT
                code = generate_code(llm, system_prompt, prompt)
            if not code:
                skipped += 1
                all_details.append(
                    {
                        "file_path": record.name,
                        "input": None,
                        "score": 0,
                        "expected_output": None,
                        "predicted_output": None,
                        "stdout": "",
                        "stderr": "record_error: code_generation_failed_or_timed_out",
                        "code": "",
                    }
                )
                continue

            result = evaluate_generated_code(record, code, problem_text, llm=llm, settings=settings)
            total_score += result["score"]
            total_fix_success += result["fix_success"]
            all_details.extend(result["details"])
            processed += 1
        except Exception as exc:
            # Skip a failed problem so the current shard can continue running.
            skipped += 1
            all_details.append(
                {
                    "file_path": record.name,
                    "input": None,
                    "score": 0,
                    "expected_output": None,
                    "predicted_output": None,
                    "stdout": "",
                    "stderr": f"record_error: {exc}",
                    "code": "",
                }
            )
            continue

    summary = {
        "dataset": "IndusCP",
        "method": method,
        "model": settings.model_name,
        "api_base": settings.api_base,
        "time_limit": settings.time_limit,
        "topk": settings.topk,
        "revision_times": settings.revision_times,
        "cases_per_problem": settings.cases_per_problem,
        "shard_total": _get_int_env("CONSTRAINTLLM_SHARD_TOTAL", 1),
        "shard_index": _get_int_env("CONSTRAINTLLM_SHARD_INDEX", 0),
        "processed_problems": processed,
        "skipped_problems": skipped,
        "total_score": total_score,
        "total_fix_success": total_fix_success,
    }
    return summary, all_details


def _get_parallel_workers() -> int:
    """Read the shard parallelism configured for the parent process."""
    return max(1, _get_int_env("CONSTRAINTLLM_PARALLEL_WORKERS", 1))


def _run_parallel_by_shard_if_needed(method: str, max_items: int) -> bool:
    """Spawn child shard processes from the parent process when needed."""
    workers = _get_parallel_workers()
    if workers <= 1:
        return False
    if os.environ.get("CONSTRAINTLLM_SHARD_TOTAL", "").strip():
        return False

    log_dir = OUTPUT_ROOT.parent / "logs"
    ensure_dir(log_dir)
    run_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    children: list[tuple[int, subprocess.Popen, Path, object]] = []
    package_root = OUTPUT_ROOT.parent
    src_dir = package_root / "src"
    shard_indices = _get_shard_indices(workers)

    try:
        for shard_index in shard_indices:
            env = os.environ.copy()
            env["CONSTRAINTLLM_PARALLEL_WORKERS"] = "1"
            env["CONSTRAINTLLM_SHARD_TOTAL"] = str(workers)
            env["CONSTRAINTLLM_SHARD_INDEX"] = str(shard_index)
            current_pythonpath = env.get("PYTHONPATH", "").strip()
            env["PYTHONPATH"] = f"{src_dir}:{current_pythonpath}" if current_pythonpath else str(src_dir)
            log_path = log_dir / f"{sanitize_name(method.lower())}_shard{shard_index + 1}of{workers}_{run_tag}.log"
            log_fp = log_path.open("w", encoding="utf-8")
            cmd = [
                sys.executable,
                "-m",
                "constraintllm.run_csp",
                "--method",
                method,
                "--max-items",
                str(max_items),
            ]
            proc = subprocess.Popen(
                cmd,
                cwd=package_root,
                env=env,
                stdout=log_fp,
                stderr=subprocess.STDOUT,
                text=True,
            )
            children.append((shard_index, proc, log_path, log_fp))
            print(f"[parallel] shard {shard_index + 1}/{workers} started pid={proc.pid} log={log_path}")

        failed = []
        for shard_index, proc, log_path, log_fp in children:
            rc = proc.wait()
            log_fp.close()
            if rc != 0:
                failed.append((shard_index + 1, rc, str(log_path)))
                print(f"[parallel] shard {shard_index + 1}/{workers} failed rc={rc} log={log_path}")
            else:
                print(f"[parallel] shard {shard_index + 1}/{workers} finished log={log_path}")

        if failed:
            raise RuntimeError(f"parallel shards failed: {failed}")
        print("[parallel] all shards finished")
        return True
    finally:
        for _, proc, _, log_fp in children:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
            if not log_fp.closed:
                try:
                    log_fp.close()
                except Exception:
                    pass


def save_experiment_outputs(summary: dict, details: list[dict]) -> tuple[Path, Path]:
    """Save experiment outputs."""
    ensure_dir(OUTPUT_ROOT)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    method = sanitize_name(summary["method"])
    model = sanitize_name(summary["model"])
    summary_path = OUTPUT_ROOT / f"induscp_{timestamp}_{method}_{model}_summary.json"
    details_path = OUTPUT_ROOT / f"induscp_{timestamp}_{method}_{model}_details.json"
    dump_json(summary, summary_path)
    dump_json(details, details_path)
    return summary_path, details_path


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description="Run constraintllm CSP experiments on IndusCP.")
    parser.add_argument("--method", choices=["DIRECT", "COT", "RAG", "CARM", "TOT"], default="COT")
    parser.add_argument("--max-items", type=int, default=0, help="Only run the first N problems.")
    return parser


def main() -> None:
    """Run the command-line entry point."""
    parser = build_parser()
    args = parser.parse_args()
    if _run_parallel_by_shard_if_needed(args.method, args.max_items):
        return
    summary, details = run_experiment(args.method, max_items=args.max_items)
    summary_path, details_path = save_experiment_outputs(summary, details)
    print(f"Summary saved to: {summary_path}")
    print(f"Details saved to: {details_path}")
    print(f"Total score: {summary['total_score']}")


if __name__ == "__main__":
    main()
