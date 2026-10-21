# Integration

## Web fork

The fork's `design-system.lock.json` records the exact Git commit, version and
SHA-256 hashes of the vendored files. Its maintenance script verifies downloads
against those hashes before writing and supports offline `--check` and online
`--check-upstream`. CSS is included in the existing Python wheel/container.
Existing `--bg-root`, `--accent`, radius and other variable names are compatibility
aliases generated here. No product/package names change.

## Companion

Add the `OpenMaskitDesign` Swift package product using an exact revision in
`desktop/macos/Package.swift`; commit `Package.resolved` and run native tests on
both supported architectures. The app owns its brand icon and uses aliases to
the shared native components. Preferences, Dock, menu bar, settings actions,
window lifecycle and service code stay in the app repository.

## Coordinated update

1. Review the source token/component change and public API compatibility.
2. Bump the design version, generate outputs and run all shared CI.
3. Tag the tested design-system commit without moving an existing tag.
4. Update the web lock, vendored assets and Companion revision/resolution.
5. Run both consumer suites and review screenshots; merge consumer updates.
6. Installed apps/services update only on an explicit manual installation request.

Consumers can stay on a previous revision while an update is reviewed. A design
release never rewrites an installed app or a running web service.
