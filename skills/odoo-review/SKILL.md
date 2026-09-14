---
name: odoo-review
description: Review Odoo 17, 18, and 19 modules for correctness, security, performance, maintainability, and version compatibility.
---

# Odoo review

Use this workflow for a structured review. Identify the target version and
edition first, then inspect the implementation rather than reviewing snippets
in isolation.

Review, when relevant:

- ORM contracts, recordset behavior, computed fields, constraints, and batch
  operations;
- statutory accounting integrity, financial invariants (Debit == Credit), lock date
  compliance, and zero direct SQL ledger mutation;
- XML inheritance, expressions, actions, assets, and frontend boundaries;
- access rights, record rules, groups, elevated access, and company isolation;
- controllers, input validation, SQL, attachments, and external integrations (verifying socket timeouts and circuit breaker wrapping on third-party HTTP calls);
- blast radius and inheritance safety: downstream `_inherit` models, child view XPath targets, and dependent QWeb/report templates;
- database migration safety: impact of new `required=True` fields or constraint additions on existing database rows (verifying Contract/Expand phase migration pattern on high-volume tables);
- tests for business logic, permissions, upgrades, and failure paths;
- caching discipline: verify raw SQL operations call `invalidate_all()`, `@tools.ormcache` returns primitives only (never Recordsets), and models call `clear_caches()` on `write`/`unlink`;
- asynchronous offloading & concurrency: ensure long-running operations (>2s) and third-party API calls are queued asynchronously (`queue_job` / `ir.cron`), and inspect `FOR UPDATE` locks to prevent deadlocks; and
- performance, queries, unbounded work, reverse proxy / load balancer compatibility (`proxy_mode` compliance, no hardcoded hostnames), and latency budgets (verifying interactive UI operations stay within p95 < 500ms without starving concurrent worker throughput).

Load `../../references/security/common.md`,
`../../references/performance/guide.md`,
`../../references/operations/deployment.md` (for code hygiene gate and
Definition of Done), `../../references/operations/oca-guidelines.md` (for OCA code style & manifest gates),
and the relevant version/domain references. Run `scripts/scan_deprecations.py` to statically verify the module
against version deprecations and dangerous `cr.commit()` calls. Report evidence, severity, impact, and a minimal fix.
