# KFD project declaration

<!-- If the project already has AGENTS.md, merge this section into it. Do not replace existing instructions. -->
<!-- If the project also uses CLAUDE.md, .cursor/rules/, GEMINI.md, or .github/copilot-instructions.md, point those existing instructions at this file (e.g. @AGENTS.md in CLAUDE.md) instead of duplicating the KFD section; do not create tool-specific files unless the human uses that tool. -->

This project uses Knowledge-First Development (KFD).
Use the `kfd` skill for product changes, bug fixes, business-rule changes, UI behavior changes, persistence/security changes, tests, and implementation work.

KFD_VERSION: {{KFD_VERSION}}
PROJECT_HUMAN_LANGUAGE: {{PROJECT_HUMAN_LANGUAGE}}

Current product meaning is managed under `knowledge/`.
For product-meaning changes, update Knowledge before tests and implementation and use the KFD Knowledge Review flow.
