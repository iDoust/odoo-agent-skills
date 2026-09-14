---
name: odoo-debug
description: Diagnose Odoo 17, 18, and 19 backend, XML, security, frontend, database, and performance problems from evidence.
---

# Odoo debugging

Use this workflow when an Odoo symptom, traceback, failed install, access
error, frontend error, or performance issue needs diagnosis.

1. Establish the diagnostic triad from the user request before inspecting code:
   - **User Problem**: What operation or business workflow the user was attempting.
   - **Current State / Symptom**: The exact error traceback, unexpected value, or failure condition observed.
   - **Expected Result**: The intended outcome, state transition, or clean execution.
2. Detect and confirm the Odoo major version and edition.
3. Identify the execution path from the entry point to the failure.
4. Read the relevant project code, Odoo core code, views, data, security, and
   callers.
5. Separate the first cause from downstream RPC or UI symptoms.
6. Check version-specific behavior and source changes before choosing a fix.
7. Fix the shared root cause in code, not only the named caller.
8. **Production Data Repair / Hotfix Protocol** (if data was corrupted by the bug):
   - **Quantify**: Inspect and count affected records via read-only query or shell before modifying anything.
   - **Atomic Transaction**: Wrap batch data fixes inside `with env.cr.savepoint():` to prevent partial corrupt commits.
   - **Mute Chatter Spam**: Apply `.with_context(mail_notrack=True, tracking_disable=True, mail_create_nolog=True)` during batch updates to prevent cascading notification emails.
   - **Reconcile**: Recompute affected stored fields, check financial invariants (Debit == Credit), and verify stock quants.
9. Add or run the smallest regression check that proves the fix.

## Common Infrastructure Failure Modes

- **Stale Cache / Cache Desync**: Modified data not appearing in UI. Diagnosis: check if raw SQL omitted `env.invalidate_all()`, or if `@tools.ormcache` method omitted `clear_caches()` on `write`/`unlink`.
- **Random User Logouts / Session Drops**: Users disconnected intermittently across clicks. Diagnosis: load balancer lacks sticky sessions (`ip_hash`), or cluster application nodes do not share a session store.
- **HTTPS Redirect Loops & Mixed Content**: Infinite redirects or broken assets. Diagnosis: `proxy_mode = False` in `odoo.conf`, or reverse proxy missing `X-Forwarded-Proto https` header.

Load `../../references/testing/troubleshooting.md` when present, together with
the version and domain references relevant to the failure. For interactive REPL
diagnostics, script piping, and SQL analysis, load
`../../references/operations/cli-and-shell.md`. For logger hierarchy, log levels,
and exception formatting, load `../../references/operations/logging.md`. For caching
architecture, load `../../references/performance/guide.md`. For load balancer and reverse
proxy setups, load `../../references/operations/deployment.md`.
