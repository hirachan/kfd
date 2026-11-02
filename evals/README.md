# Skill behavior evals

These regression tests evaluate the skill's **agent behavior**, not just fixture
code: recognizing conflicts, preserving existing Knowledge, stopping for human
approval, and keeping unrelated ideas in the Parking Lot. Each scenario supplies
a small project, an agent prompt, and observable expectations. A passing result
is evidence for those expectations, not proof that every KFD requirement was met.

## Run

Use Python 3.9 or later on a POSIX system with `sh` and process groups; Windows
is not supported. Install PyYAML to read scenario definitions; the optional
`lint_clean` expectation also needs the repository linter's dependencies (see the
repository README). Authenticate your chosen agent CLI separately.

```sh
python3 evals/run_evals.py --list
python3 evals/run_evals.py --agent-cmd '<your command template>' --keep
python3 evals/run_evals.py --agent-cmd '<your command template>' \
  --scenario meaning-preserving-refactor knowledge-preserving-bug-fix --jobs 2
```

**Examples to adapt** to your installed CLI version, permissions, authentication,
and model configuration; these are not guaranteed universal invocations:

```sh
# Claude Code: install the skill in the copied project's skill directory.
python3 evals/run_evals.py \
  --agent-cmd "claude -p {prompt} --permission-mode acceptEdits --allowedTools 'Bash(python3:*)'" \
  --install-skill-to .claude/skills/kfd --keep

# Codex: adapt its skill discovery/configuration to your environment.
python3 evals/run_evals.py \
  --agent-cmd 'codex exec --full-auto {prompt}' --keep
```

For Claude Code, a personal `~/.claude/skills/kfd` takes precedence over the
installed project copy. Remove or update that personal copy before evaluating
the version installed by the harness. The example allows Python commands so the
agent can run the linter and tests under `acceptEdits`; adapt permissions to your
fixtures and CLI.

Templates run through POSIX `sh -c` with the copied project as the working directory.
The harness substitutes and shell-quotes these placeholders (do not add your own
quotes around them):

| Placeholder | Value |
| --- | --- |
| `{prompt}` | Scenario prompt text, passed as one shell argument |
| `{prompt_file}` | Absolute path to the saved prompt file |
| `{workdir}` | Absolute path to the copied project |
| `{skill_dir}` | Absolute path to this skill repository |

All other braces are left alone. Only use trusted command templates and fixtures:
agent commands can execute code, and a copied project is **not a sandbox**.

Options:

- `--scenario ID ...`: select scenarios; repeatable; default is all scenarios.
- `--scenarios-dir DIR`: use a different scenario collection (default:
  `evals/scenarios` in this repository).
- `--install-skill-to REL`: copy `SKILL.md`, `VERSION`, `CHANGELOG.md`,
  `references/`, `assets/`, `examples/`, `schema/`, and `scripts/` into this
  project-relative directory.
- `--timeout SEC`: timeout per agent invocation, default 900 seconds.
- `--jobs N`: concurrent scenarios using `concurrent.futures`, default 1.
- `--results DIR`: output directory, default `evals/results/<UTC timestamp>`.
  Existing scenario result directories are never overwritten by a new run.
- `--keep`: retain successful workdirs as well as failed ones.
- `--list`: validate and list scenarios without invoking an agent.

Runs consume agent tokens, may incur provider charges, and can take minutes per
scenario. Parallelism increases simultaneous resource use and cost. Start with
one scenario when adapting your CLI template.

## Results and re-grading

For each scenario the harness copies `project/` to `<results>/<id>/workdir`,
substitutes `{{KFD_VERSION}}` in `AGENTS.md` using the repository's `VERSION`,
optionally installs the skill, and initializes a git repository with a baseline
commit when git is available. Git identity is configured locally in that copy.
The actual change baseline is a SHA-256 snapshot, independent of git tracking or
ignore rules. It excludes `.git/`, `__pycache__/`, `*.pyc`, and the skill
installation directory. Symlinks (including dangling links and links to
directories) are hashed as `b"symlink:"` plus the link target, without following
them; non-regular entries such as FIFOs are skipped. Agent processes receive
`PYTHONDONTWRITEBYTECODE=1` and closed stdin (`DEVNULL`).

The output directory saves `prompt.txt`, combined agent stdout/stderr in
`transcript.txt`, `result.json`, and the scenario/baseline/execution metadata
needed for re-grading. A lint expectation also saves `lint.txt`; command
expectations save combined stdout/stderr in `commands.txt`. `result.json`
contains `id`, `passed`, `failures`, `changed` (added, modified, or deleted paths),
`exit_code`, and `duration_s` (agent execution time). Non-zero agent exits and
timeouts fail the scenario but do not skip expectation grading.

The harness prints `PASS <id>` or `FAIL <id>: <reasons>` and a summary. Exit codes:
0 means every scenario passed; 1 means at least one failed; 2 means invalid usage,
an invalid scenario, missing PyYAML, or an unsupported platform. Per-scenario
setup/run/read errors become `harness error: <message>` failures, with
`result.json` saved when possible, without preventing other scenarios from
running. Ctrl-C kills live process groups and exits 130.

Successful workdirs are removed unless `--keep` is used. Failed workdirs are
always retained. To re-grade a retained project after inspecting or editing it,
without invoking an agent again:

```sh
python3 evals/run_evals.py --grade-only evals/results/<timestamp>/<scenario-id>
```

Re-grading uses the saved scenario expectations, snapshot, transcript, and agent
exit/timeout outcome, and overwrites `result.json` (and `lint.txt` or
`commands.txt` if applicable). It re-runs `commands_succeed` in the retained
workdir; it does not re-run the agent. It retains the workdir even if the new
grade passes. It cannot erase a recorded agent failure or re-grade a successful
run whose workdir was already removed.

## Add a scenario

Create `evals/scenarios/<kebab-case-id>/scenario.yaml` and a small `project/`
fixture. Keep fixture code real and minimal, with tests that exercise it. Use
`KFD_VERSION: {{KFD_VERSION}}` in the fixture's `AGENTS.md` rather than hardcoding
a version. Ensure fixtures are lint-clean after version substitution. Choose
expectations that distinguish correct behavior from a plausible wrong action;
inspect both project changes and the agent's report when useful.

Every prompt must end with:

> No human is available to answer questions or approve anything during this run. Follow KFD: where KFD requires human approval or a human decision, stop at that point and report what is needed.

### `scenario.yaml` reference

The four top-level fields below are required; use `expect: {}` when no
expectations are needed (a bare `expect:` is also treated as an empty mapping).
Unknown fields, unknown expectation keys, wrong value types, unsafe relative
paths, invalid globs, and invalid regular expressions are usage errors.

A complete shape (include only the expectations your scenario needs):

```yaml
id: example-change                 # kebab-case; must equal directory name
description: One-line description of the behavior under test
prompt: |
  Make the requested change.

  No human is available to answer questions or approve anything during this run. Follow KFD: where KFD requires human approval or a human decision, stop at that point and report what is needed.
expect:
  files_changed: [app/src/**]
  files_unchanged: [knowledge/**]
  file_contains:
    app/src/example.py: ['^def renamed_helper']
  file_not_contains:
    app/src/example.py: ['def old_helper']
  transcript_contains: ['completed']
  transcript_not_contains: ['Knowledge Review:']
  lint_clean: true
  commands_succeed: ['python3 -m unittest discover -s tests']
```

- `files_changed`: every glob must match at least one added, modified, or deleted
  file. This does not forbid additional changes.
- `files_unchanged`: no changed file may match any listed glob.
- Globs are project-relative with `/` separators. `*` and `?` stay within a path
  component; character classes are supported; `**` spans directories, including
  zero directories (`app/**/x.py` matches `app/x.py` and `app/a/b/x.py`).
- `file_contains`: each named file must exist, and every regex must match its
  final contents using `re.MULTILINE | re.IGNORECASE`.
- `file_not_contains`: the file may be absent; if present, none of its regexes
  may match (same flags).
- `transcript_contains` / `transcript_not_contains`: each regex must match / must
  not match combined stdout and stderr, using `re.IGNORECASE`.
- `lint_clean: true`: run `scripts/kfd_lint.py` with the harness's Python
  interpreter on the resulting project and require exit 0. Omit it, or set it
  to `false`, to skip lint grading.
- `commands_succeed`: a list of non-empty shell command strings. After the agent
  run and the post-run snapshot, run each via `sh -c` in the copied workdir with
  `PYTHONDONTWRITEBYTECODE=1`, closed stdin (`DEVNULL`), and a 300-second timeout
  per command. Each must exit 0. Failures are reported as
  `commands_succeed: '<command>' exited <code>` or
  `commands_succeed: '<command>' timed out`; combined output is saved to
  `<results>/<id>/commands.txt`. Commands may execute arbitrary code, so use
  trusted fixtures. Their changes are not part of the preceding snapshot.

File paths and globs must be relative: no absolute paths, backslashes, empty
components, `.` components, or `..` traversal. Regex strings follow Python's
`re` syntax; YAML single quotes are convenient for regex backslashes.
