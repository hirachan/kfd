#!/usr/bin/env python3
"""Run and re-grade agent behavior scenarios (Python 3.9+)."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import stat
import sys
import time
import threading


ROOT = Path(__file__).resolve().parents[1]
EXPECT_KEYS = {
    "files_changed", "files_unchanged", "file_contains", "file_not_contains",
    "transcript_contains", "transcript_not_contains", "lint_clean", "commands_succeed",
}
LIVE_PROCESSES = set()
PROCESS_LOCK = threading.RLock()
INTERRUPTED = threading.Event()


class UsageError(Exception):
    """An invalid invocation or scenario definition."""


def relative_path(value, label, glob=False):
    if (not isinstance(value, str) or not value or value.startswith("/")
            or "\\" in value or any(part in ("", ".", "..") for part in value.split("/"))):
        raise UsageError(f"{label}: expected a project-relative {'glob' if glob else 'path'}")
    return value


def string_list(value, label, regex=False, paths=False):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise UsageError(f"{label}: expected a list of strings")
    for item in value:
        if paths:
            relative_path(item, label, glob=True)
            try:
                glob_regex(item)
            except re.error as exc:
                raise UsageError(f"{label}: invalid glob {item!r}: {exc}") from exc
        if regex:
            try:
                re.compile(item)
            except re.error as exc:
                raise UsageError(f"{label}: invalid regex {item!r}: {exc}") from exc


def validate_scenario(data, scenario_id):
    if not isinstance(data, dict) or set(data) != {"id", "description", "prompt", "expect"}:
        raise UsageError(f"{scenario_id}: expected id, description, prompt, and expect fields")
    if (data["id"] != scenario_id or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", scenario_id)):
        raise UsageError(f"{scenario_id}: id must be kebab-case and equal the directory name")
    for field in ("description", "prompt"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise UsageError(f"{scenario_id}: {field} must be a non-empty string")
    if "\n" in data["description"].strip():
        raise UsageError(f"{scenario_id}: description must be one line")
    expect = data["expect"]
    if expect is None:
        expect = data["expect"] = {}
    if not isinstance(expect, dict):
        raise UsageError(f"{scenario_id}: expect must be a mapping")
    unknown = set(expect) - EXPECT_KEYS
    if unknown:
        raise UsageError(f"{scenario_id}: unknown expect keys: {', '.join(map(str, unknown))}")
    for key, value in expect.items():
        label = f"{scenario_id}: expect.{key}"
        if key in ("files_changed", "files_unchanged"):
            string_list(value, label, paths=True)
        elif key in ("transcript_contains", "transcript_not_contains"):
            string_list(value, label, regex=True)
        elif key == "commands_succeed":
            string_list(value, label)
            if any(not item.strip() for item in value):
                raise UsageError(f"{label}: expected non-empty commands")
        elif key in ("file_contains", "file_not_contains"):
            if not isinstance(value, dict):
                raise UsageError(f"{label}: expected a path-to-regex-list mapping")
            for path, patterns in value.items():
                relative_path(path, label)
                string_list(patterns, label, regex=True)
        elif not isinstance(value, bool):
            raise UsageError(f"{label}: expected a boolean")
    return data


def load_scenario(directory):
    try:
        import yaml
    except ImportError as exc:
        raise UsageError("Reading scenario.yaml requires PyYAML; install it with python3 -m pip install PyYAML") from exc
    try:
        data = yaml.safe_load((directory / "scenario.yaml").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise UsageError(f"{directory}: cannot read scenario.yaml: {exc}") from exc
    return validate_scenario(data, directory.name)


def glob_regex(pattern):
    """Translate path globs; a complete ** component matches zero or more directories."""
    result = ""
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if pattern[i:i + 2] == "**":
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    result += "(?:.*/)?"
                    i += 1
                else:
                    result += ".*"
                continue
            result += "[^/]*"
        elif char == "?":
            result += "[^/]"
        elif char == "[":
            end = i + 1
            if end < len(pattern) and pattern[end] in "!^":
                end += 1
            if end < len(pattern) and pattern[end] == "]":
                end += 1
            end = pattern.find("]", end)
            if end == -1:
                result += r"\["
            else:
                content = pattern[i + 1:end]
                if content.startswith("!"):
                    content = "^" + content[1:]
                elif content.startswith("^"):
                    content = "\\" + content
                result += "(?!/)[" + content.replace("\\", "\\\\") + "]"
                i = end
        else:
            result += re.escape(char)
        i += 1
    return re.compile("^" + result + "$")


def snapshot(workdir, install_dir):
    hashes = {}
    for directory, dirs, files in os.walk(workdir):
        parent = Path(directory)
        dirs[:] = sorted(name for name in dirs if name not in (".git", "__pycache__") and (
            not install_dir or (parent / name).relative_to(workdir).as_posix() != install_dir))
        for name in sorted(dirs + files):
            path = parent / name
            relative = path.relative_to(workdir).as_posix()
            if relative == install_dir or name == ".git" or name.endswith(".pyc"):
                continue
            mode = os.lstat(path).st_mode
            if stat.S_ISLNK(mode):
                content = b"symlink:" + os.fsencode(os.readlink(path))
            elif stat.S_ISREG(mode):
                content = path.read_bytes()
            else:
                continue
            hashes[relative] = hashlib.sha256(content).hexdigest()
    return hashes


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(command, workdir, timeout):
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with PROCESS_LOCK:
        if INTERRUPTED.is_set():
            raise RuntimeError("run interrupted")
        process = subprocess.Popen(["sh", "-c", command], cwd=workdir, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   env=env, start_new_session=True)
        LIVE_PROCESSES.add(process)
    timed_out = False
    try:
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_process_group(process)
            output, _ = process.communicate()
    except KeyboardInterrupt:
        kill_process_group(process)
        raise
    finally:
        with PROCESS_LOCK:
            LIVE_PROCESSES.discard(process)
    return {
        "exit_code": process.returncode,
        "duration_s": round(time.monotonic() - started, 3),
        "timed_out": timed_out,
    }, output.decode("utf-8", errors="replace")


def kill_process_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def grade(directory, scenario, baseline, execution, install_dir):
    workdir = directory / "workdir"
    after = snapshot(workdir, install_dir)
    changed = sorted(path for path in baseline.keys() | after.keys() if baseline.get(path) != after.get(path))
    transcript = (directory / "transcript.txt").read_text(encoding="utf-8", errors="replace")
    failures = []
    if execution["timed_out"]:
        failures.append("agent timed out")
    elif execution["exit_code"] != 0:
        failures.append(f"agent exited with code {execution['exit_code']}")
    for key, value in scenario["expect"].items():
        if key in ("files_changed", "files_unchanged"):
            for pattern in value:
                matches = [path for path in changed if glob_regex(pattern).fullmatch(path)]
                if key == "files_changed" and not matches:
                    failures.append(f"files_changed: no changed file matches {pattern!r}")
                elif key == "files_unchanged" and matches:
                    failures.append(f"files_unchanged: {pattern!r} matched {', '.join(matches)}")
        elif key in ("file_contains", "file_not_contains"):
            for relative, patterns in value.items():
                path = workdir / relative
                if not path.is_file():
                    if key == "file_contains":
                        failures.append(f"file_contains: missing file {relative}")
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                for pattern in patterns:
                    matched = re.search(pattern, text, re.MULTILINE | re.IGNORECASE) is not None
                    if matched != (key == "file_contains"):
                        failures.append(f"{key}: {relative}: {pattern!r}")
        elif key in ("transcript_contains", "transcript_not_contains"):
            for pattern in value:
                matched = re.search(pattern, transcript, re.IGNORECASE) is not None
                if matched != (key == "transcript_contains"):
                    failures.append(f"{key}: {pattern!r}")
        elif key == "commands_succeed":
            outputs = []
            for command in value:
                outcome, output = run_command(command, workdir, 300)
                outputs.append(f"$ {command}\n{output}\n")
                if outcome["timed_out"]:
                    failures.append(f"commands_succeed: '{command}' timed out")
                elif outcome["exit_code"] != 0:
                    failures.append(f"commands_succeed: '{command}' exited {outcome['exit_code']}")
            (directory / "commands.txt").write_text("".join(outputs), encoding="utf-8")
        elif value:
            lint = subprocess.run([sys.executable, str(ROOT / "scripts" / "kfd_lint.py"), str(workdir)],
                                  capture_output=True, text=True)
            (directory / "lint.txt").write_text(lint.stdout + lint.stderr, encoding="utf-8")
            if lint.returncode != 0:
                failures.append(f"lint_clean: linter exited with code {lint.returncode} (see lint.txt)")
    result = {"id": scenario["id"], "passed": not failures, "failures": failures,
              "changed": changed, "exit_code": execution["exit_code"], "duration_s": execution["duration_s"]}
    save_json(directory / "result.json", result)
    return result


def git_baseline(workdir):
    git = shutil.which("git")
    if not git:
        return
    commands = [
        ["init", "--quiet"], ["config", "user.name", "KFD eval"],
        ["config", "user.email", "kfd-eval@example.invalid"],
        ["config", "commit.gpgsign", "false"], ["add", "--all"],
        ["-c", "core.hooksPath=/dev/null", "commit", "--quiet", "--allow-empty", "-m", "Eval baseline"],
    ]
    for args in commands:
        completed = subprocess.run([git, *args], cwd=workdir, capture_output=True, text=True)
        if completed.returncode:
            raise UsageError(f"Cannot create git baseline: {completed.stderr.strip()}")


def run_scenario(source, scenario, args):
    directory = args.results / scenario["id"]
    directory.mkdir(parents=True, exist_ok=False)
    workdir = directory / "workdir"
    shutil.copytree(source / "project", workdir, symlinks=True)
    agents = workdir / "AGENTS.md"
    if agents.is_file():
        agents.write_text(agents.read_text(encoding="utf-8").replace(
            "{{KFD_VERSION}}", (ROOT / "VERSION").read_text(encoding="utf-8").strip()), encoding="utf-8")
    if args.install_skill_to:
        target = workdir / args.install_skill_to
        target.mkdir(parents=True, exist_ok=True)
        for name in ("SKILL.md", "VERSION", "CHANGELOG.md", "references", "assets", "examples", "schema", "scripts"):
            source_path = ROOT / name
            if source_path.is_dir():
                shutil.copytree(source_path, target / name, dirs_exist_ok=True)
            else:
                shutil.copy2(source_path, target / name)
    git_baseline(workdir)
    baseline = snapshot(workdir, args.install_skill_to)
    save_json(directory / "baseline.json", baseline)
    save_json(directory / "scenario.json", scenario)
    save_json(directory / "run.json", {"install_skill_to": args.install_skill_to})
    prompt_file = directory / "prompt.txt"
    prompt_file.write_text(scenario["prompt"], encoding="utf-8")
    placeholders = {"prompt": scenario["prompt"], "prompt_file": str(prompt_file),
                    "workdir": str(workdir), "skill_dir": str(ROOT)}
    command = re.sub(r"\{(prompt|prompt_file|workdir|skill_dir)\}",
                     lambda match: shlex.quote(placeholders[match[1]]), args.agent_cmd)
    execution, transcript = run_command(command, workdir, args.timeout)
    save_json(directory / "execution.json", execution)
    (directory / "transcript.txt").write_text(transcript, encoding="utf-8")
    result = grade(directory, scenario, baseline, execution, args.install_skill_to)
    if result["passed"] and not args.keep:
        shutil.rmtree(workdir)
    return result


def isolated_run(source, scenario, args):
    try:
        return run_scenario(source, scenario, args)
    except Exception as exc:
        result = {"id": scenario["id"], "passed": False,
                  "failures": [f"harness error: {exc}"], "changed": [],
                  "exit_code": None, "duration_s": 0}
        try:
            directory = args.results / scenario["id"]
            directory.mkdir(parents=True, exist_ok=True)
            save_json(directory / "result.json", result)
        except OSError:
            pass
        return result


def grade_only(directory):
    if not (directory / "workdir").is_dir():
        raise UsageError(f"{directory}: no retained workdir; use --keep for successful runs")
    try:
        scenario = validate_scenario(json.loads((directory / "scenario.json").read_text(encoding="utf-8")), directory.name)
        baseline = json.loads((directory / "baseline.json").read_text(encoding="utf-8"))
        execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
        install_dir = json.loads((directory / "run.json").read_text(encoding="utf-8"))["install_skill_to"]
        return grade(directory, scenario, baseline, execution, install_dir)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise UsageError(f"{directory}: invalid retained run: {exc}") from exc


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def positive_timeout(value):
    number = float(value)
    if not 0 < number < float("inf"):
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def main(argv=None):
    if os.name != "posix":
        print("error: the eval harness requires POSIX (sh and process groups)", file=sys.stderr)
        return 2
    INTERRUPTED.clear()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-cmd", help="shell command template; see evals/README.md")
    parser.add_argument("--scenario", nargs="+", action="append", default=[])
    parser.add_argument("--scenarios-dir", type=Path, default=ROOT / "evals" / "scenarios")
    parser.add_argument("--install-skill-to")
    parser.add_argument("--timeout", type=positive_timeout, default=900)
    parser.add_argument("--jobs", type=positive_int, default=1)
    parser.add_argument("--results", type=Path, default=ROOT / "evals" / "results" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))
    parser.add_argument("--keep", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--grade-only", type=Path)
    mode.add_argument("--list", action="store_true")
    args = parser.parse_args(argv)
    executor = None
    try:
        if args.grade_only:
            results = [grade_only(args.grade_only.resolve())]
        else:
            if not args.scenarios_dir.is_dir():
                raise UsageError(f"Missing scenarios directory: {args.scenarios_dir}")
            sources = {path.name: path for path in sorted(args.scenarios_dir.iterdir()) if path.is_dir() and (path / "scenario.yaml").is_file()}
            requested = [item for group in args.scenario for item in group]
            unknown = set(requested) - sources.keys()
            if unknown:
                raise UsageError(f"Unknown scenario: {', '.join(sorted(unknown))}")
            selected = list(dict.fromkeys(requested)) if requested else list(sources)
            scenarios = [(sources[name], load_scenario(sources[name])) for name in selected]
            if not scenarios:
                raise UsageError("No scenarios found")
            if args.list:
                for _, scenario in scenarios:
                    print(f"{scenario['id']}: {scenario['description']}")
                return 0
            if not args.agent_cmd:
                raise UsageError("--agent-cmd is required unless --list or --grade-only is used")
            if args.install_skill_to:
                relative_path(args.install_skill_to, "--install-skill-to")
                if ".git" in args.install_skill_to.split("/"):
                    raise UsageError("--install-skill-to cannot be inside .git")
            args.results = args.results.resolve()
            for _, scenario in scenarios:
                if (args.results / scenario["id"]).exists():
                    raise UsageError(f"Result directory already exists: {args.results / scenario['id']}")
            executor = ThreadPoolExecutor(max_workers=args.jobs)
            results = list(executor.map(lambda item: isolated_run(item[0], item[1], args), scenarios))
            executor.shutdown()
            executor = None
        for result in results:
            print(f"PASS {result['id']}" if result["passed"] else f"FAIL {result['id']}: {'; '.join(result['failures'])}")
        passed = sum(result["passed"] for result in results)
        print(f"{passed}/{len(results)} passed; {len(results) - passed} failed")
        return 0 if passed == len(results) else 1
    except KeyboardInterrupt:
        INTERRUPTED.set()
        with PROCESS_LOCK:
            for process in LIVE_PROCESSES:
                kill_process_group(process)
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)
        return 130
    except (UsageError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
