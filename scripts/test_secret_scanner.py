"""Prove the manifest checksum exception cannot conceal an unknown credential."""

import json
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    scanner = sys.argv[1]
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        # A generated synthetic value is never printed or committed.
        value = secrets.token_hex(32)
        (source / "design-manifest.json").write_text(json.dumps({"api_key": value}))
        result = subprocess.run(
            [
                scanner,
                "dir",
                "--config",
                str(ROOT / ".gitleaks.toml"),
                "--redact=100",
                "--report-format=json",
                "--report-path",
                str(root / "report.json"),
                "--no-banner",
                "--log-level=error",
                str(source),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 1:
            raise SystemExit("Secret scanner failed to reject the synthetic credential")
        report = json.loads((root / "report.json").read_text())
        if not any(item["RuleID"] == "generic-api-key" for item in report):
            raise SystemExit("Synthetic generic credential was not detected")
    print("Secret scanner rejects unknown credentials in the manifest.")


if __name__ == "__main__":
    main()
