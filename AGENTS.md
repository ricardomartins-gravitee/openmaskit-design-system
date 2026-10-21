# OpenMaskit Design System

Preserve OpenMaskit and OpenMaskit Companion names and existing app behaviour.
Edit tokens/dark.tokens.json and shared components, then run scripts/build.py.
Generated CSS and Swift files must be committed and pass --check.
Keep SwiftUI controls native; window, menu bar, Dock and lifecycle belong to Companion.
Use synthetic fixtures; never commit runtime state, logs or credentials.
Only dark mode is supported; add a future theme to both consumers together.
Changes to public token names or component APIs require a major version bump.
Do not add local scheduled jobs or silently update installed applications.
