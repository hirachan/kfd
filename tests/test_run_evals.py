"""Exercise the eval harness without invoking a real agent."""

import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "evals" / "run_evals.py"


class EvalHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.scenarios = self.base / "scenarios"
        self.scenario = self.scenarios / "tiny"
        self.project = self.scenario / "project"
        self.project.mkdir(parents=True)
        (self.project / "AGENTS.md").write_text("KFD_VERSION: {{KFD_VERSION}}\n", encoding="utf-8")
        (self.project / "app").mkdir()
        (self.project / "app" / "item.txt").write_text("before\n", encoding="utf-8")
        self.results = self.base / "results"
        self.write_scenario({})

    def write_scenario(self, expect):
        # JSON is a YAML subset, so tests need no direct PyYAML dependency.
        data = {"id": "tiny", "description": "A tiny fake-agent scenario", "prompt": "Write a result, don't ask.", "expect": expect}
        (self.scenario / "scenario.yaml").write_text(json.dumps(data), encoding="utf-8")

    def invoke(self, code="print('hello')", *options):
        command = shlex.quote(sys.executable) + " -c " + shlex.quote(code)
        return self.cli("--agent-cmd", command, "--results", str(self.results), *options)

    def cli(self, *options):
        return subprocess.run([sys.executable, str(HARNESS), "--scenarios-dir", str(self.scenarios), *options],
                              capture_output=True, text=True, timeout=30)

    def result(self):
        return json.loads((self.results / "tiny" / "result.json").read_text(encoding="utf-8"))

    def test_pass_and_cleanup(self):
        self.write_scenario({
            "files_changed": ["app/**"], "files_unchanged": ["AGENTS.md"],
            "file_contains": {"app/item.txt": ["^AFTER$"]},
            "file_not_contains": {"app/item.txt": ["before"], "absent.txt": ["anything"]},
            "transcript_contains": ["HELLO"], "transcript_not_contains": ["error"],
        })
        completed = self.invoke("from pathlib import Path; Path('app/item.txt').write_text('after\\n'); print('hello')")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS tiny", completed.stdout)
        self.assertEqual(self.result()["changed"], ["app/item.txt"])
        self.assertFalse((self.results / "tiny" / "workdir").exists())

    def test_each_expect_key_fails(self):
        cases = [
            ("files_changed", ["missing/**"]),
            ("files_unchanged", ["app/**"]),
            ("file_contains", {"app/item.txt": ["missing text"]}),
            ("file_not_contains", {"app/item.txt": ["after"]}),
            ("transcript_contains", ["missing text"]),
            ("transcript_not_contains", ["hello"]),
            ("lint_clean", True),
        ]
        for index, (key, value) in enumerate(cases):
            with self.subTest(key=key):
                self.results = self.base / f"failure-{index}"
                self.write_scenario({key: value})
                completed = self.invoke("from pathlib import Path; Path('app/item.txt').write_text('after'); print('hello')")
                self.assertEqual(completed.returncode, 1, completed.stderr)
                self.assertIn("FAIL tiny", completed.stdout)
                self.assertTrue(any(key in reason for reason in self.result()["failures"]))
                self.assertTrue((self.results / "tiny" / "workdir").is_dir())

    def test_missing_required_file_fails_even_with_empty_patterns(self):
        self.write_scenario({"file_contains": {"absent.txt": []}})
        self.assertEqual(self.invoke().returncode, 1)
        self.assertIn("missing file", self.result()["failures"][0])

    def test_nonzero_exit_still_grades(self):
        self.write_scenario({"transcript_contains": ["not printed"]})
        completed = self.invoke("import sys; print('hello'); sys.exit(7)")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        result = self.result()
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(len(result["failures"]), 2)
        self.assertIn("agent exited", result["failures"][0])

    def test_timeout_still_grades_and_saves_transcript(self):
        self.write_scenario({"transcript_contains": ["started"], "files_changed": ["missing.txt"]})
        completed = self.invoke("import time; print('started', flush=True); time.sleep(10)", "--timeout", "0.5")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertTrue(any("timed out" in reason for reason in self.result()["failures"]))
        self.assertTrue(any("files_changed" in reason for reason in self.result()["failures"]))
        self.assertFalse(any("transcript_contains" in reason for reason in self.result()["failures"]))

    def test_version_substitution_precedes_snapshot(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.write_scenario({"files_unchanged": ["AGENTS.md"], "file_not_contains": {"AGENTS.md": [r"\{\{KFD_VERSION\}\}"]}})
        completed = self.invoke("from pathlib import Path; print(Path('AGENTS.md').read_text())", "--keep")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        saved = self.results / "tiny" / "workdir" / "AGENTS.md"
        self.assertEqual(saved.read_text(encoding="utf-8"), f"KFD_VERSION: {version}\n")
        self.assertEqual(self.result()["changed"], [])

    def test_install_skill_excluded_from_change_detection(self):
        self.write_scenario({"files_unchanged": ["**"]})
        code = ("from pathlib import Path; p=Path('.claude/skills/kfd'); "
                "assert (p/'SKILL.md').is_file(); "
                "assert (p/'CHANGELOG.md').is_file(); "
                "assert all((p/name).is_dir() for name in ['references','assets','examples','schema','scripts']); "
                "(p/'VERSION').write_text('changed'); (p/'new.txt').write_text('added'); "
                "(p/'SKILL.md').unlink()")
        completed = self.invoke(code, "--install-skill-to", ".claude/skills/kfd", "--keep")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.result()["changed"], [])
        baseline = json.loads((self.results / "tiny" / "baseline.json").read_text(encoding="utf-8"))
        self.assertFalse(any(path.startswith(".git/") or path.startswith(".claude/skills/kfd/") for path in baseline))

    def test_grade_only_reuses_baseline_and_execution(self):
        self.write_scenario({"file_contains": {"app/item.txt": ["after"]}})
        completed = self.invoke()
        self.assertEqual(completed.returncode, 1, completed.stderr)
        directory = self.results / "tiny"
        (directory / "workdir" / "app" / "item.txt").write_text("after", encoding="utf-8")
        completed = self.cli("--grade-only", str(directory))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS tiny", completed.stdout)
        self.assertTrue((directory / "workdir").is_dir())
        self.assertEqual(self.result()["changed"], ["app/item.txt"])

    def test_glob_double_star_zero_and_multiple_directories_and_deletions(self):
        (self.project / "remove.txt").write_text("delete", encoding="utf-8")
        self.write_scenario({"files_changed": ["**/top.txt", "app/**/item.txt", "**/deep.txt", "remove.txt"],
                             "files_unchanged": ["app/*.py", "app/*/deep.txt"]})
        code = ("from pathlib import Path; Path('top.txt').write_text('new'); "
                "Path('app/item.txt').write_text('after'); "
                "Path('app/a/b').mkdir(parents=True); Path('app/a/b/deep.txt').write_text('new'); "
                "Path('remove.txt').unlink()")
        completed = self.invoke(code)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("remove.txt", self.result()["changed"])

    def test_bad_yaml_and_shape_exit_two(self):
        invalid = ["[unclosed", "[]", json.dumps({"id": "tiny"}),
                   json.dumps({"id": "other", "description": "x", "prompt": "x", "expect": {}})]
        for text in invalid:
            with self.subTest(text=text):
                (self.scenario / "scenario.yaml").write_text(text, encoding="utf-8")
                completed = self.invoke()
                self.assertEqual(completed.returncode, 2, completed.stderr)
        for expect in ({"unknown": []}, {"files_changed": "app/**"}, {"file_contains": {"../outside": ["x"]}},
                       {"files_changed": ["[z-a]"]}, {"commands_succeed": [" "]},
                       {"commands_succeed": "exit 0"}, {"commands_succeed": [3]},
                       {"transcript_contains": ["["]}, {"lint_clean": "yes"}):
            with self.subTest(expect=expect):
                self.write_scenario(expect)
                self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse(self.results.exists())

    def test_list_and_usage_errors(self):
        completed = self.cli("--list")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("tiny: A tiny", completed.stdout)
        self.assertEqual(self.cli().returncode, 2)
        self.assertEqual(self.cli("--scenario", "unknown", "--list").returncode, 2)
        self.assertEqual(self.invoke("print('hello')", "--jobs", "0").returncode, 2)
        self.assertEqual(self.invoke("print('hello')", "--install-skill-to", "../outside").returncode, 2)

    def test_placeholders_are_shell_quoted_and_braces_in_code_preserved(self):
        prompt = "$HOME `echo unsafe`\n\"double\" 'single' {workdir}"
        data = json.loads((self.scenario / "scenario.yaml").read_text(encoding="utf-8"))
        data["prompt"] = prompt
        (self.scenario / "scenario.yaml").write_text(json.dumps(data), encoding="utf-8")
        code = ("import sys; from pathlib import Path; "
                f"assert sys.argv[1] == bytes.fromhex({prompt.encode().hex()!r}).decode(); "
                "assert Path(sys.argv[2]).read_text() == sys.argv[1]; "
                "assert Path(sys.argv[3]) == Path.cwd(); "
                "assert (Path(sys.argv[4])/'SKILL.md').is_file(); print({'safe': 'hello'})")
        command = (shlex.quote(sys.executable) + " -c " + shlex.quote(code)
                   + " {prompt} {prompt_file} {workdir} {skill_dir}")
        completed = self.cli("--agent-cmd", command, "--results", str(self.results))
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_parallel_jobs_and_scenario_selection(self):
        import shutil
        second = self.scenarios / "second"
        shutil.copytree(self.scenario, second)
        data = json.loads((second / "scenario.yaml").read_text(encoding="utf-8"))
        data["id"] = "second"
        (second / "scenario.yaml").write_text(json.dumps(data), encoding="utf-8")
        completed = self.invoke("print('hello')", "--jobs", "2", "--scenario", "tiny", "second")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS tiny", completed.stdout)
        self.assertIn("PASS second", completed.stdout)
        self.assertIn("2/2 passed", completed.stdout)

    def test_null_expect_is_empty(self):
        self.write_scenario(None)
        completed = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_import_bytecode_is_ignored_and_agent_environment_is_noninteractive(self):
        (self.project / "app" / "module.py").write_text("value = 42\n", encoding="utf-8")
        self.write_scenario({"files_unchanged": ["app/**"]})
        code = ("import os, sys; assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'; "
                "assert sys.stdin.read() == ''; sys.dont_write_bytecode = False; "
                "import app.module; from pathlib import Path; "
                "assert list(Path('app/__pycache__').glob('*.pyc')); "
                "Path('app/stray.pyc').write_bytes(b'bytecode')")
        completed = self.invoke(code, "--keep")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.result()["changed"], [])

    def test_symlinks_are_snapshotted_without_following_and_fifos_are_skipped(self):
        (self.project / "link").symlink_to("app/item.txt")
        self.write_scenario({"files_changed": ["dangling", "link", "directory-link"],
                             "files_unchanged": ["pipe"]})
        code = ("import os; from pathlib import Path; Path('dangling').symlink_to('missing'); "
                "Path('link').unlink(); Path('link').symlink_to('other-missing'); "
                "Path('directory-link').symlink_to('app', target_is_directory=True); "
                "os.mkfifo('pipe')")
        completed = self.invoke(code)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.result()["changed"], ["dangling", "directory-link", "link"])

    def test_commands_succeed_runs_after_snapshot_and_reruns_when_grading(self):
        command = "printf checked; printf created > app/command-output.txt"
        self.write_scenario({"files_unchanged": ["app/**"], "commands_succeed": [command]})
        completed = self.invoke("print('hello')", "--keep")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.result()["changed"], [])
        directory = self.results / "tiny"
        self.assertIn("checked", (directory / "commands.txt").read_text(encoding="utf-8"))
        (directory / "workdir" / "app" / "command-output.txt").unlink()
        completed = self.cli("--grade-only", str(directory))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue((directory / "workdir" / "app" / "command-output.txt").is_file())

    def test_failing_commands_fail_scenario_and_save_combined_output(self):
        self.write_scenario({"commands_succeed": ["printf out; printf err >&2; exit 3", "printf next"]})
        completed = self.invoke()
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("commands_succeed: 'printf out; printf err >&2; exit 3' exited 3",
                      self.result()["failures"])
        output = (self.results / "tiny" / "commands.txt").read_text(encoding="utf-8")
        self.assertIn("outerr", output)
        self.assertIn("next", output)

    def test_missing_project_is_isolated_as_harness_failure(self):
        broken = self.scenarios / "broken"
        broken.mkdir()
        data = {"id": "broken", "description": "Missing fixture", "prompt": "Do nothing", "expect": {}}
        (broken / "scenario.yaml").write_text(json.dumps(data), encoding="utf-8")
        completed = self.invoke("print('hello')", "--jobs", "2")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("FAIL broken: harness error:", completed.stdout)
        self.assertIn("PASS tiny", completed.stdout)
        self.assertIn("1/2 passed", completed.stdout)
        result = json.loads((self.results / "broken" / "result.json").read_text(encoding="utf-8"))
        self.assertFalse(result["passed"])
        self.assertTrue(result["failures"][0].startswith("harness error: "))


if __name__ == "__main__":
    unittest.main()
