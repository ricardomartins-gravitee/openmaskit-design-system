# Component guidance

| Concept | Web | Native macOS |
| --- | --- | --- |
| Panel | `.om-panel` | `OpenMaskitPanel` with a heading accessibility trait |
| Primary action | `.om-button.om-button-primary` | `OpenMaskitButtonStyle(kind: .primary)` on a native Button |
| Secondary action | `.om-button` | `OpenMaskitButtonStyle()` |
| Destructive action | `.om-button.om-button-danger` | `.danger` style, with application-owned confirmation where needed |
| Status | `.om-badge` plus readable text | `OpenMaskitBadge` plus readable text |
| Input | labelled native HTML `.om-input` | labelled native TextField/Picker/Toggle |
| Error | red text with useful message; appropriate status announcement | readable message using `OpenMaskitTheme.red` |
| Empty/loading | explain state and next action | native Text/ProgressView with useful labels |

Use body text for content and monospaced headings for short section names.
Never communicate status through colour alone. Preserve readable labels,
keyboard focus and disabled semantics. Use the platform's native focus engine;
custom styles must preserve it. Web transitions honour reduced-motion settings;
native components add no custom animation.

Keep layouts compact but allow wrapping and scrolling. Numeric spacing values
are shared; window sizes and web breakpoints remain application decisions.
The web fork initially adopts tokens globally and shared button primitives on
the privacy screen. Existing page-specific components can migrate incrementally
without forcing an upstream-wide UI rewrite.
