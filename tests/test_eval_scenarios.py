"""Keep the eval scenario fixtures valid KFD projects.

Fixtures carry ``KFD_VERSION: {{KFD_VERSION}}``; the harness substitutes the
repository version before running an agent, so they are checked the same way here.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


REPO = Path(__file__).resolve().parents[1]
LINTER = REPO / "scripts/kfd_lint.py"
SCENARIOS = REPO / "evals/scenarios"
VERSION = (REPO / "VERSION").read_text(encoding="utf-8").strip()


class ScenarioFixtureTests(unittest.TestCase):
    def prepared_project(self, scenario):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        project = Path(temp.name) / "project"
        shutil.copytree(scenario / "project", project)
        agents = project / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        self.assertIn("KFD_VERSION: {{KFD_VERSION}}", text, agents)
        agents.write_text(text.replace("{{KFD_VERSION}}", VERSION), encoding="utf-8")
        return project

    def test_every_scenario_is_lint_clean_and_its_tests_pass(self):
        scenarios = sorted(path for path in SCENARIOS.iterdir() if path.is_dir())
        self.assertTrue(scenarios)
        for scenario in scenarios:
            with self.subTest(scenario=scenario.name):
                data = yaml.safe_load((scenario / "scenario.yaml").read_text(encoding="utf-8"))
                self.assertEqual(data["id"], scenario.name)
                project = self.prepared_project(scenario)
                lint = subprocess.run([sys.executable, str(LINTER), str(project), "--strict"],
                                      capture_output=True, text=True)
                self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
                self.assertEqual(lint.stdout, "0 error(s), 0 warning(s)\n")
                tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "app/tests", "-t", "."],
                                       cwd=project, capture_output=True, text=True)
                self.assertEqual(tests.returncode, 0, tests.stderr)
                self.assertNotIn("Ran 0 tests", tests.stderr)


if __name__ == "__main__":
    unittest.main()
