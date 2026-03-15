from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from pathlib import Path

from .config import FIX_CODE_SYSTEM_MESSAGE, TMP_ROOT, Settings, get_settings
from .delete_log import delete_log_xml_files
from .llm import OpenAICompatibleLLM, get_llm
from .utils import collect_case_pairs, ensure_dir, extract_python_code


def clip_text(text: str, max_chars: int) -> str:
    """Hard-truncate text by character count."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]..."


def get_isolated_tmp_dir(problem_name: str) -> Path:
    """Create an isolated temporary directory for one problem evaluation."""
    run_id = f"{problem_name}_{os.getpid()}_{int(time.time() * 1000)}"
    tmp_dir = TMP_ROOT / run_id
    ensure_dir(tmp_dir)
    return tmp_dir


def extract_cleanup_markers(command: list[str]) -> set[str]:
    """Extract targeted cleanup markers from the command."""
    markers: set[str] = set()
    for arg in command:
        if arg.endswith(".json"):
            markers.add(Path(arg).name)
        if arg.startswith("-data="):
            markers.add(Path(arg.split("=", 1)[1]).name)
    return markers


def terminate_process_group(pid: int, timeout: float = 2.0) -> None:
    """Terminate a process group gracefully, then force-kill on timeout."""
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def kill_java_by_markers(markers: set[str]) -> None:
    """Only kill leftover Java solver processes tagged by the current command."""
    if not markers:
        return
    try:
        result = subprocess.run(["ps", "-eo", "user,pid,args"], capture_output=True, text=True, check=True)
    except Exception:
        return
    current_user = os.environ.get("USER", "")
    current_pid = os.getpid()
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        user_name, pid_text, args = parts
        if current_user and user_name != current_user:
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        tokens = args.split()
        if not tokens:
            continue
        executable = Path(tokens[0]).name
        if not executable.startswith("java"):
            continue
        if not any(marker in args for marker in markers):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass


def run_program(tmp_dir: Path, command: list[str], code: str, time_limit: int) -> tuple[str, str]:
    """Run PyCSP3 code and return stdout and stderr."""
    code_file_path = tmp_dir / "user_code.py"
    code_file_path.write_text(code, encoding="utf-8")
    process = None
    markers = extract_cleanup_markers(command)
    start = time.perf_counter()
    try:
        env = os.environ.copy()
        java_opts = env.get("JAVA_TOOL_OPTIONS", "")
        if "-Xmx" not in java_opts:
            env["JAVA_TOOL_OPTIONS"] = (java_opts + " -Xmx4g").strip()
        process = subprocess.Popen(
            command,
            cwd=tmp_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            env=env,
        )
        stdout, stderr = process.communicate(timeout=time_limit)
        elapsed = time.perf_counter() - start
        print(f"[solver] status=ok elapsed={elapsed:.2f}s cmd={' '.join(command)}")
        return stdout, stderr
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        print(f"[solver] status=timeout elapsed={elapsed:.2f}s cmd={' '.join(command)}")
        return "Timeout: solver exceeded the time limit", "Timeout"
    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"[solver] status=error elapsed={elapsed:.2f}s error={type(exc).__name__} cmd={' '.join(command)}")
        return f"Error: {exc}", str(exc)
    finally:
        if process is not None:
            terminate_process_group(process.pid)
            kill_java_by_markers(markers)
        delete_log_xml_files(tmp_dir)


def extract_cost(output_text: str) -> str | None:
    """Extract the objective value from solver output."""
    match = re.search(r'cost="([^"]+)"', output_text)
    if match:
        return match.group(1).strip()
    match = re.search(r"my answer is\s+([^\n\.]+)", output_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def build_fix_prompt(problem_text: str, code: str, input_text: str, expected_output: str, output_text: str, error_text: str) -> str:
    """Build the repair prompt."""
    settings = get_settings()
    return (
        "Problem statement:\n"
        f"{clip_text(problem_text, settings.fix_problem_max_chars)}\n\n"
        "Current code:\n"
        f"```python\n{clip_text(code, settings.fix_code_max_chars)}\n```\n\n"
        "Input instance:\n"
        f"{clip_text(input_text, settings.fix_input_max_chars)}\n\n"
        "Expected output:\n"
        f"{expected_output}\n\n"
        "Observed stdout:\n"
        f"{clip_text(output_text, settings.fix_output_max_chars)}\n\n"
        "Observed stderr:\n"
        f"{clip_text(error_text, settings.fix_error_max_chars)}\n"
    )


def request_code_fix(llm: OpenAICompatibleLLM, problem_text: str, code: str, input_text: str, expected_output: str, output_text: str, error_text: str) -> str | None:
    """Ask the model to repair the code."""
    start = time.perf_counter()
    try:
        raw_text = llm(
            FIX_CODE_SYSTEM_MESSAGE,
            build_fix_prompt(problem_text, code, input_text, expected_output, output_text, error_text),
            temperature=0.0,
        )
    except Exception as exc:
        # Abort this repair attempt on timeout or transient API errors without failing the full evaluation.
        elapsed = time.perf_counter() - start
        print(f"[fix] status=failed elapsed={elapsed:.2f}s error={type(exc).__name__}")
        return None
    elapsed = time.perf_counter() - start
    print(f"[fix] status=ok elapsed={elapsed:.2f}s")
    return extract_python_code(raw_text)


def evaluate_generated_code(record, code: str, problem_text: str, llm: OpenAICompatibleLLM | None = None, settings: Settings | None = None) -> dict:
    """Evaluate a generated solution for one problem."""
    settings = settings or get_settings()
    if llm is None:
        llm = get_llm(settings)

    if record.base_dir is None:
        raise ValueError(f"record {record.name} missing base_dir")

    case_pairs = collect_case_pairs(record.base_dir, settings.cases_per_problem)
    tmp_dir = get_isolated_tmp_dir(record.name)
    details = []
    total_score = 0
    successful_fix_count = 0
    eval_start = time.perf_counter()

    for input_path, output_path in case_pairs:
        if output_path is None:
            print(f"[case] problem={record.name} input={input_path.name} skipped=no_expected_output")
            continue

        try:
            input_text = input_path.read_text(encoding="utf-8")
            expected_output = output_path.read_text(encoding="utf-8").strip()
            command = ["python3", str(tmp_dir / "user_code.py"), f"-data={input_path}", "-solve"]

            current_code = code
            used_fix = False
            stdout = ""
            stderr = ""
            extracted_cost = None
            case_start = time.perf_counter()

            for attempt in range(settings.revision_times + 1):
                round_start = time.perf_counter()
                stdout, stderr = run_program(tmp_dir, command, current_code, settings.time_limit)
                extracted_cost = extract_cost(stdout)
                round_elapsed = time.perf_counter() - round_start
                print(
                    f"[case] problem={record.name} input={input_path.name} round={attempt + 1}/{settings.revision_times + 1} "
                    f"solver_elapsed={round_elapsed:.2f}s matched={extracted_cost == expected_output}"
                )
                if extracted_cost == expected_output:
                    break
                if attempt >= settings.revision_times:
                    break
                fixed_code = request_code_fix(llm, problem_text, current_code, input_text, expected_output, stdout, stderr)
                if not fixed_code:
                    break
                current_code = fixed_code
                used_fix = True

            score = 1 if extracted_cost == expected_output else 0
            case_elapsed = time.perf_counter() - case_start
            if score:
                total_score += 1
                if used_fix:
                    successful_fix_count += 1
            print(
                f"[case] problem={record.name} input={input_path.name} score={score} "
                f"used_fix={used_fix} total_elapsed={case_elapsed:.2f}s"
            )

            details.append(
                {
                    "file_path": record.name,
                    "input": input_path.name,
                    "score": score,
                    "expected_output": expected_output,
                    "predicted_output": extracted_cost,
                    "stdout": stdout,
                    "stderr": stderr,
                    "code": current_code,
                    "case_elapsed_sec": round(case_elapsed, 3),
                    "used_fix": used_fix,
                }
            )
        except Exception as exc:
            # Record zero for a failed case and continue so one case does not break the whole problem.
            case_elapsed = time.perf_counter() - case_start if "case_start" in locals() else None
            print(
                f"[case] problem={record.name} input={input_path.name} status=exception "
                f"elapsed={(case_elapsed or 0):.2f}s error={type(exc).__name__}"
            )
            details.append(
                {
                    "file_path": record.name,
                    "input": input_path.name,
                    "score": 0,
                    "expected_output": None,
                    "predicted_output": None,
                    "stdout": "",
                    "stderr": f"case_error: {exc}",
                    "code": code,
                    "case_elapsed_sec": round(case_elapsed, 3) if case_elapsed is not None else None,
                    "used_fix": False,
                }
            )

    eval_elapsed = time.perf_counter() - eval_start
    print(
        f"[eval] problem={record.name} score={total_score} fix_success={successful_fix_count} "
        f"cases={len(details)} total_elapsed={eval_elapsed:.2f}s"
    )
    return {
        "score": total_score,
        "fix_success": successful_fix_count,
        "details": details,
        "eval_elapsed_sec": round(eval_elapsed, 3),
    }
