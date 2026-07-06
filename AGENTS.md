# AGENTS.md

## Cursor Cloud specific instructions

### Repository overview

The default/base branch `main` contains only `README.md` — a GitHub "special" profile
README (repo `Acimdamero/Acimdamero`) that renders on the owner's GitHub profile page.
There is **no application code, no dependencies, no build system, and no test suite** on
`main`, so there is nothing to install, lint, build, or run. Editing `README.md` is the
only development activity for this branch.

- Preview the profile README by rendering the Markdown (e.g. `pip install markdown` then
  `python3 -m markdown README.md`) or simply view it on GitHub.

### Feature branch: `cursor/mac-iphone-automation-hub-8703`

Substantial code lives on the unmerged branch `cursor/mac-iphone-automation-hub-8703`
under `mac-iphone-automation/`. It is a **macOS-only** "Mac ↔ iPhone Automation Hub" made
of Bash scripts, `launchd` plists, Apple Shortcuts specs, Google Apps Script, and a WAHA
(WhatsApp HTTP API) Docker integration. It relies on macOS-specific tooling
(`osascript`/AppleScript, `launchctl`, iOS Shortcuts) and therefore **cannot run
end-to-end on a Linux cloud VM**. See `mac-iphone-automation/README.md` on that branch for
its own setup wizard and guides.

### Update script

No dependency-refresh step is required for `main` (there are no dependencies).
