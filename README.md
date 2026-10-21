# OpenMaskit Design System

Shared design values and native components for OpenMaskit and OpenMaskit
Companion. This independently maintained project keeps both existing product
names and upstream attribution. It contains no connector or service code.

## Contents

- `tokens/dark.tokens.json`: the single source for colours, dimensions, spacing,
  typography sizes, opacity, durations and semantic component values.
- `design-system.json`: version, CSS compatibility bindings, native colour roles
  and supported contrast pairs.
- `web/tokens.css` and `web/components.css`: bundled local web assets.
- `Sources/OpenMaskitDesign`: generated values plus native SwiftUI panels,
  badges, button styles and system typography.
- `web/gallery.html`: synthetic component gallery with common states.

Only dark mode is supported today. Window dimensions, responsive page layouts,
app icons, window controls, menu bar/Dock behaviour, lifecycle and service
management remain owned by their applications. Native controls retain their
keyboard and accessibility semantics. Text captions now use a slightly brighter
muted colour to meet 4.5:1 against all three standard dark surfaces.

## Generate and test

Generation uses Python's standard library; consumers need no Python generator,
Node runtime, external CDN or network connection to render the UI.

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
swift test
uv sync --frozen
uv run --frozen playwright install chromium webkit
uv run --frozen python scripts/test_browser.py
```

The deliberately small generator accepts a documented **subset** of the
[DTCG 2025.10 format](https://www.designtokens.org/TR/2025.10/format/): explicitly
typed sRGB colours, px dimensions, ms durations, finite numbers and whole-token
references. It validates every value and alias before emitting deterministic
CSS and Swift. Other DTCG features are rejected rather than silently ignored.
CSS pixels map to macOS points; milliseconds map to Swift seconds. Web font
families use existing DM Sans/JetBrains Mono fallbacks; native typography uses
system fonts with the same semantic roles and monospaced headings.

## Consumption and updates

See [integration](docs/integration.md) and [component guidance](docs/components.md).
Applications pin exact source revisions. The web fork vendors the CSS, manifest,
licence and notice so its Python wheel/container stays self-contained. Companion
uses a revision-pinned Swift package and committed `Package.resolved`.

For a change: edit source tokens/components, increment `design-system.json`'s
version, regenerate, run CI, create an immutable version tag, then deliberately
update each consumer and run its acceptance tests. No local scheduled updater
or automatic installation is introduced. A breaking public token/component
change requires a major version bump. A new light theme requires coordinated
web and desktop changes and acceptance before either exposes a theme switch.

## Validation

CI checks aliases, schema subset, cross-platform generation, output drift,
manifest hashes and supported opaque foreground/background contrast pairs.
It runs actual SwiftUI rendering tests on Apple Silicon macOS 26 and Intel
macOS 15, plus browser acceptance in Chromium and WebKit at desktop/mobile
widths. Browser checks include keyboard focus, form labels, disabled/hover
states, no external asset requests, overflow and reduced-motion behaviour.
Screenshots are retained for review; tests assert styles and geometry rather
than claiming a universal pixel-identical baseline across platforms.

Contrast validation covers declared normal text roles and primary button text;
it does not certify every possible application combination. Border contrast,
large text, platform accessibility settings and application-specific flows
need their own acceptance checks.

Apache-2.0. See LICENSE and NOTICE.
