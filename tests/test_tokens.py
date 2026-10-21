import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.document = build.read_json(ROOT / "tokens/dark.tokens.json")
        self.tokens = build.resolve(self.document)
        self.config = build.read_json(ROOT / "design-system.json")

    def test_generated_files_are_current_and_deterministic(self):
        first = build.outputs()
        self.assertEqual(first, build.outputs())
        for name, value in first.items():
            self.assertEqual((ROOT / name).read_text(), value, name)
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/build.py"), "--check"], check=True
        )

    def test_every_token_reaches_css_and_swift(self):
        css = build.generate_css(self.tokens, self.config)
        swift = build.generate_swift(self.tokens, self.config)
        for name, value in self.tokens.items():
            self.assertIn(f"--om-{build.kebab(name)}: {build.css_value(value)};", css)
            self.assertIn(f"static let {build.swift_name(name)}", swift)
        self.assertEqual(
            json.loads((ROOT / "web/tokens.resolved.json").read_text()), self.tokens
        )

    def test_all_web_compatibility_aliases_resolve(self):
        for name, target in self.config["web"]["aliases"].items():
            self.assertIn(
                f"--{name}: var(--om-{build.kebab(target)});",
                (ROOT / "web/tokens.css").read_text(),
            )
        self.assertEqual(len(self.config["swiftColors"]), 12)

    def test_manifest_integrity_including_handwritten_components_and_license(self):
        manifest = build.read_json(ROOT / "design-manifest.json")
        for asset in manifest["files"]:
            name, digest = asset["path"], asset["sha256"]
            self.assertEqual(
                hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest
            )
        self.assertEqual(manifest["version"], self.config["version"])

    def test_supported_foregrounds_meet_wcag_aa_on_all_standard_surfaces(self):
        policy = self.config["contrast"]
        for fg in policy["foreground"]:
            for bg in policy["background"]:
                self.assertGreaterEqual(
                    build.contrast(
                        self.tokens[fg]["$value"], self.tokens[bg]["$value"]
                    ),
                    4.5,
                    (fg, bg),
                )
        self.assertGreaterEqual(
            build.contrast(
                self.tokens["color.bgRoot"]["$value"],
                self.tokens["color.accent"]["$value"],
            ),
            4.5,
        )

    def test_bad_contrast_is_rejected(self):
        self.tokens["color.textPrimary"] = copy.deepcopy(self.tokens["color.bgRoot"])
        with self.assertRaisesRegex(ValueError, "Contrast below"):
            build.validate_config(self.config, self.tokens)

    def test_chained_aliases_and_type_preservation(self):
        self.document["alias"] = {
            "first": {"$type": "dimension", "$value": "{component.button.radius}"}
        }
        self.assertEqual(
            build.resolve(self.document)["alias.first"], self.tokens["radius.button"]
        )

    def test_cycles_and_missing_references_fail(self):
        for reference in ("{missing.token}", "{space.xs}"):
            self.document["space"]["xs"]["$value"] = reference
            with self.assertRaises(ValueError):
                build.resolve(self.document)

    def test_mismatched_types_and_partial_aliases_fail(self):
        for value in ("{color.accent}", "calc({space.sm} + 2px)"):
            self.document["space"]["xs"]["$value"] = value
            with self.assertRaises(ValueError):
                build.resolve(self.document)

    def test_invalid_values_fail(self):
        for kind, value in [
            ("color", "#ffffff"),
            (
                "color",
                {"colorSpace": "display-p3", "components": [0, 0, 0], "alpha": 1},
            ),
            ("color", {"colorSpace": "srgb", "components": [0, 0, 2], "alpha": 1}),
            ("color", {"colorSpace": "srgb", "components": [0, 0], "alpha": 1}),
            ("dimension", {"unit": "rem", "value": 1}),
            ("dimension", {"unit": "px", "value": -1}),
            ("duration", {"unit": "ms", "value": float("nan")}),
            ("number", True),
            ("number", float("inf")),
        ]:
            with self.subTest(kind=kind, value=value), self.assertRaises(ValueError):
                build.validate_value(kind, value)

    def test_invalid_names_types_and_colliding_swift_symbols_fail(self):
        for document in (
            {"Bad.Name": {"$type": "number", "$value": 1}},
            {"ok": {"$type": "string", "$value": "x"}},
            {"ok": {"$type": "number", "$value": 1, "unexpected": True}},
            {
                "aB": {"$type": "number", "$value": 1},
                "a": {"b": {"$type": "number", "$value": 2}},
            },
        ):
            with self.assertRaises(ValueError):
                build.resolve(document)

    def test_duplicate_json_keys_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "duplicate.json"
            path.write_text('{"color":{},"color":{}}')
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                build.read_json(path)

    def test_invalid_bindings_and_theme_fail(self):
        for category in ("web", "swift", "theme", "version", "contrast", "composite"):
            config = copy.deepcopy(self.config)
            if category == "web":
                config["web"]["aliases"]["accent"] = "missing"
            if category == "swift":
                config["swiftColors"]["root"] = "space.sm"
            if category == "theme":
                config["theme"] = "light"
            if category == "version":
                config["version"] = '1.0.0";'
            if category == "contrast":
                config["contrast"]["minimum"] = 3
            if category == "composite":
                config["web"]["extras"]["escape"] = "url(https://example.invalid)"
            with self.assertRaises(ValueError):
                build.validate_config(config, self.tokens)

    def test_alpha_and_platform_unit_conversion(self):
        self.assertEqual(build.css_value(self.tokens["color.accentDim"]), "#58a6ff20")
        swift = build.generate_swift(self.tokens, self.config)
        self.assertIn("durationFast: Double = 0.15", swift)
        self.assertIn("spaceLg: CGFloat = 16", swift)
        self.assertIn(
            "color-scheme: dark", build.generate_css(self.tokens, self.config)
        )

    def test_check_rejects_modified_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            import shutil

            for name in [
                "scripts/build.py",
                "tokens/dark.tokens.json",
                "design-system.json",
                "web/components.css",
                "LICENSE",
                "NOTICE",
                "TRADEMARKS.md",
            ]:
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / name, root / name)
            result = subprocess.run(
                [sys.executable, str(root / "scripts/build.py"), "--check"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Generated file is stale", result.stderr)


if __name__ == "__main__":
    unittest.main()
