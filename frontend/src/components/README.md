# Shared frontend components

This directory contains frontend components that are genuinely reusable across DIVS pages.

- `ui/` — brand-neutral interface primitives (buttons, content containers, semantic sections).
- `layout/` — shared site navigation, footers, and page shells when their behavior is established.

## Component rules

1. Keep reusable primitives separate from landing-page sections and feature-specific components.
2. Keep the components accessible and typed with strict TypeScript.
3. Components expose semantic variants and class hooks; final colors, spacing, borders, and interaction states are defined after the DIVS design-system discussion.
4. Do not copy TEED/Tunakuza brand tokens into DIVS. Compare patterns, then make explicit DIVS decisions.
5. Avoid adding dependencies for simple primitives.
