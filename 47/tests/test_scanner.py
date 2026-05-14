import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditor.models import SourceFile
from auditor.patcher import build_patch
from auditor.scanner import scan_files


class ScannerTests(unittest.TestCase):
    def test_detects_key_vulnerabilities(self):
        source = SourceFile(
            path="app.py",
            content="\n".join(
                [
                    "from flask import request",
                    'api_key = "prod-7aA9superSecretToken"',
                    'cursor.execute(f"SELECT * FROM users WHERE id={request.args.get("id")}")',
                    "subprocess.run(cmd, shell=True)",
                    "app.run(debug=True)",
                ]
            ),
        )

        findings = scan_files([source])
        titles = {finding.title for finding in findings}

        self.assertIn("Hardcoded credential", titles)
        self.assertIn("Possible SQL injection", titles)
        self.assertIn("Possible command injection", titles)
        self.assertIn("Debug mode enabled", titles)

    def test_builds_safe_patch(self):
        source = SourceFile(
            path="app.py",
            content='api_key = "prod-7aA9superSecretToken"\napp.run(debug=True)\n',
        )
        findings = scan_files([source])
        patch, changed_files = build_patch([source], findings)

        self.assertIn('import os', changed_files[0].patched)
        self.assertIn('api_key = os.getenv("API_KEY", "")', changed_files[0].patched)
        self.assertIn("app.run(debug=False)", changed_files[0].patched)
        self.assertIn("-api_key", patch)
        self.assertIn("+api_key", patch)


if __name__ == "__main__":
    unittest.main()
