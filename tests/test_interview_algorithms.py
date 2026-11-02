"""Verify the study-guide examples and run their independent Java checks.

Set JAVA_HOME or provide java/javac on PATH. No dependencies are downloaded here.
Compilation output is isolated in a temporary directory.
"""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
JAVA_SOURCE = ROOT / "tests/java/InterviewAlgorithms.java"
GUIDE = ROOT / "docs/interview-intake-algorithms-20261102.md"
TAGS = ("quicksort", "smallest-k", "coin-change", "lca", "increasing-path")


class InterviewAlgorithmsTest(unittest.TestCase):
    def test_guide_examples_match_executed_source(self):
        source, guide = JAVA_SOURCE.read_text(), GUIDE.read_text()
        snippets = re.findall(r"^```java\n(.*?)^```", guide, flags=re.M | re.S)
        self.assertEqual(len(snippets), len(TAGS))
        for tag, snippet in zip(TAGS, snippets):
            body = source.split(f"    // BEGIN {tag}\n", 1)[1].split(f"    // END {tag}", 1)[0]
            self.assertEqual(snippet.strip(), textwrap.dedent(body).strip(), tag)

    def test_java_algorithm_checks(self):
        java_home = os.environ.get("JAVA_HOME")
        javac = str(Path(java_home) / "bin/javac") if java_home else shutil.which("javac")
        java = str(Path(java_home) / "bin/java") if java_home else shutil.which("java")
        if not javac or not java or not Path(javac).is_file() or not Path(java).is_file():
            self.skipTest("Java execution skipped: provide a JDK using JAVA_HOME or PATH")
        with tempfile.TemporaryDirectory(prefix="interview-algorithms-") as directory:
            compiled = subprocess.run(
                [javac, "-encoding", "UTF-8", "-d", directory, str(JAVA_SOURCE)],
                check=False, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            executed = subprocess.run(
                [java, "-cp", directory, "InterviewAlgorithms"],
                check=False, capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertRegex(executed.stdout, r"PASS: \d+ algorithm checks")
            print(executed.stdout.strip())


if __name__ == "__main__":
    unittest.main()
