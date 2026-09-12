---
name: odoo-debug
description: Diagnose Odoo 17, 18, and 19 backend, XML, security, frontend, database, and performance problems from evidence.
---

# Odoo debugging

Use this workflow when an Odoo symptom, traceback, failed install, access
error, frontend error, or performance issue needs diagnosis.

1. Reproduce the symptom or capture the complete traceback and request context.
2. Detect and confirm the Odoo major version and edition.
3. Identify the execution path from the entry point to the failure.
4. Read the relevant project code, Odoo core code, views, data, security, and
   callers.
5. Separate the first cause from downstream RPC or UI symptoms.
6. Check version-specific behavior and source changes before choosing a fix.
7. Fix the shared root cause, not only the named caller.
8. Add or run the smallest regression check that proves the fix.

Load `../../references/testing/troubleshooting.md` when present, together with
the version and domain references relevant to the failure. For interactive REPL
diagnostics, script piping, and SQL analysis, load
`../../references/operations/cli-and-shell.md`. For logger hierarchy, log levels,
and exception formatting, load `../../references/operations/logging.md`.
