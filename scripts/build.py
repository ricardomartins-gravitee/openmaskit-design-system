"""Validate a documented DTCG subset and deterministically emit CSS and Swift.

No runtime/build dependencies are needed. Consumers use checked-in CSS or the
Swift package; generation only happens in this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^[a-z][a-zA-Z0-9]*$")
REFERENCE = re.compile(r"^\{([a-zA-Z0-9.]+)\}$")
TYPES = {"color", "dimension", "duration", "number"}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=unique_object)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def flatten(document, prefix=""):
    if not isinstance(document, dict) or not document:
        raise ValueError(f"Expected a nonempty token group: {prefix}")
    result = {}
    for name, value in document.items():
        if not NAME.fullmatch(name) or not isinstance(value, dict):
            raise ValueError(f"Invalid token/group name: {name}")
        path = prefix + name
        if "$value" in value:
            if value.get("$type") not in TYPES:
                raise ValueError(f"Unsupported token type: {path}")
            if set(value) - {"$type", "$value", "$description"}:
                raise ValueError(f"Unsupported token property: {path}")
            result[path] = value
        else:
            result.update(flatten(value, path + "."))
    return result


def validate_value(kind, value):
    if kind == "color":
        if not isinstance(value, dict) or set(value) != {
            "colorSpace",
            "components",
            "alpha",
        }:
            raise ValueError("Color requires colorSpace, components and alpha")
        if value["colorSpace"] != "srgb":
            raise ValueError("Only sRGB colors are supported")
        components = value["components"]
        if not isinstance(components, list) or len(components) != 3:
            raise ValueError("Color requires three components")
        if any(not finite(x) or not 0 <= x <= 1 for x in [*components, value["alpha"]]):
            raise ValueError("Color channels must be finite and between zero and one")
    elif kind in {"dimension", "duration"}:
        unit = "px" if kind == "dimension" else "ms"
        if not isinstance(value, dict) or set(value) != {"value", "unit"}:
            raise ValueError("Dimension/duration requires value and unit")
        if value["unit"] != unit or not finite(value["value"]) or value["value"] < 0:
            raise ValueError(f"Expected a nonnegative finite {unit} value")
    elif not finite(value):
        raise ValueError("Expected a finite number")


def resolve(document):
    tokens = flatten(document)
    resolved = {}

    def visit(name, stack):
        if name not in tokens:
            raise ValueError(f"Missing token reference: {name}")
        if name in stack:
            raise ValueError(f"Cyclic token reference: {name}")
        if name in resolved:
            return resolved[name]
        token = tokens[name]
        value = token["$value"]
        if isinstance(value, str):
            reference = REFERENCE.fullmatch(value)
            if not reference:
                raise ValueError(f"Only whole-token references are supported: {name}")
            target = visit(reference[1], [*stack, name])
            if target["$type"] != token["$type"]:
                raise ValueError(f"Reference type mismatch: {name}")
            value = target["$value"]
        validate_value(token["$type"], value)
        resolved[name] = {"$type": token["$type"], "$value": value}
        return resolved[name]

    for name in sorted(tokens):
        visit(name, [])
    symbols = [swift_name(name) for name in tokens]
    if len(set(symbols)) != len(symbols):
        raise ValueError("Swift token names collide")
    return dict(sorted(resolved.items()))


def swift_name(name):
    parts = name.split(".")
    return parts[0] + "".join(x[0].upper() + x[1:] for x in parts[1:])


def kebab(name):
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name).replace(".", "-").lower()


def css_value(token):
    value = token["$value"]
    kind = token["$type"]
    if kind == "color":
        channels = [*value["components"], value["alpha"]]
        return "#" + "".join(
            f"{round(x * 255):02x}"
            for x in channels[:3] + ([] if channels[3] == 1 else [channels[3]])
        )
    if kind in {"dimension", "duration"}:
        return f"{value['value']:g}{value['unit']}"
    return f"{value:g}"


def contrast(foreground, background):
    def luminance(color):
        channels = [
            x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
            for x in color["components"]
        ]
        if color["alpha"] != 1:
            raise ValueError("Contrast pairs must use opaque colors")
        return sum(x * weight for x, weight in zip(channels, [0.2126, 0.7152, 0.0722]))

    values = sorted([luminance(foreground), luminance(background)])
    return (values[1] + 0.05) / (values[0] + 0.05)


def validate_config(config, tokens):
    if config.get("theme") != "dark" or not re.fullmatch(
        r"\d+\.\d+\.\d+", config.get("version", "")
    ):
        raise ValueError("Expected dark theme and a semantic version")
    for css_name, target in config["web"]["aliases"].items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", css_name) or target not in tokens:
            raise ValueError("Invalid CSS binding")
    for swift, target in config["swiftColors"].items():
        if (
            not NAME.fullmatch(swift)
            or target not in tokens
            or tokens[target]["$type"] != "color"
        ):
            raise ValueError("Invalid Swift color binding")
    for name, value in config["web"]["extras"].items():
        if (
            not re.fullmatch(r"[a-z][a-z0-9-]*", name)
            or not isinstance(value, str)
            or any(x in value for x in [";", "{", "}", "\n", "url("])
        ):
            raise ValueError("Invalid CSS composite")
    policy = config["contrast"]
    if not finite(policy["minimum"]) or policy["minimum"] < 4.5:
        raise ValueError("Contrast policy must require at least 4.5:1")
    for fg in policy["foreground"]:
        for bg in policy["background"]:
            ratio = contrast(tokens[fg]["$value"], tokens[bg]["$value"])
            if ratio < policy["minimum"]:
                raise ValueError(
                    f"Contrast below {policy['minimum']}: {fg} on {bg} ({ratio:.2f})"
                )


def generate_css(tokens, config):
    lines = [
        f"/* Generated by OpenMaskit Design System {config['version']}; do not edit. */",
        ":root {",
        "  color-scheme: dark;",
    ]
    for name, token in tokens.items():
        lines.append(f"  --om-{kebab(name)}: {css_value(token)};")
    for name, target in sorted(config["web"]["aliases"].items()):
        lines.append(f"  --{name}: var(--om-{kebab(target)});")
    for name, value in sorted(config["web"]["extras"].items()):
        lines.append(f"  --{name}: {value};")
    return "\n".join([*lines, "}", ""])


def generate_swift(tokens, config):
    lines = [
        f"// Generated by OpenMaskit Design System {config['version']}; do not edit.",
        "import Foundation",
        "",
        "public enum OpenMaskitTokens {",
        f'  public static let version = "{config["version"]}"',
    ]
    for name, token in tokens.items():
        value = token["$value"]
        kind = token["$type"]
        if kind == "color":
            channels = [*value["components"], value["alpha"]]
            lines.extend([f"  public static let {swift_name(name)} = DesignColor("])
            for index, (label, channel) in enumerate(
                zip(["red", "green", "blue", "alpha"], channels)
            ):
                suffix = "," if index < 3 else ")"
                lines.append(f"    {label}: {channel:.12f}{suffix}")
        else:
            amount = value["value"] if isinstance(value, dict) else value
            # DTCG CSS px map to macOS points; durations map ms to seconds.
            if kind == "duration":
                amount /= 1000
            typename = "CGFloat" if kind == "dimension" else "Double"
            lines.append(
                f"  public static let {swift_name(name)}: {typename} = {amount:g}"
            )
    lines.extend(
        [
            "}",
            "",
            "#if canImport(SwiftUI)",
            "  import SwiftUI",
            "",
            "  public enum OpenMaskitTheme {",
        ]
    )
    for name, token in sorted(config["swiftColors"].items()):
        lines.append(
            f"    public static var {name}: Color {{ OpenMaskitTokens.{swift_name(token)}.color }}"
        )
    lines.extend(["  }", "#endif", ""])
    return "\n".join(lines)


def outputs(root=ROOT):
    tokens = resolve(read_json(root / "tokens/dark.tokens.json"))
    config = read_json(root / "design-system.json")
    validate_config(config, tokens)
    result = {
        "web/tokens.css": generate_css(tokens, config),
        "Sources/OpenMaskitDesign/Tokens.swift": generate_swift(tokens, config),
        "web/tokens.resolved.json": json.dumps(tokens, indent=2) + "\n",
    }
    # Manifest covers hand-maintained components as well as generated outputs.
    hashed = {
        name: hashlib.sha256(content.encode()).hexdigest()
        for name, content in result.items()
    }
    for name in ["web/components.css", "LICENSE", "NOTICE", "TRADEMARKS.md"]:
        hashed[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    result["design-manifest.json"] = (
        json.dumps(
            {
                "version": config["version"],
                "theme": config["theme"],
                "files": [
                    {"path": name, "sha256": digest}
                    for name, digest in sorted(hashed.items())
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in outputs().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(
                    f"Generated file is stale: {name}. Run python3 scripts/build.py"
                )
        else:
            path.write_text(content)
    print("Design tokens, accessibility pairs and generated outputs verified.")


if __name__ == "__main__":
    main()
