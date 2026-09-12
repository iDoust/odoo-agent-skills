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
- controllers, input validation, SQL, attachments, and external integrations;
- tests for business logic, permissions, upgrades, and failure paths; and
- performance, cache/flush behavior, queries, and unbounded work.

Load `../../references/security/common.md`,
`../../references/performance/guide.md`,
`../../references/operations/deployment.md` (for code hygiene gate and
Definition of Done), `../../references/operations/oca-guidelines.md` (for OCA code style & manifest gates),
and the relevant version/domain references. Run `scripts/scan_deprecations.py` to statically verify the module
against version deprecations and dangerous `cr.commit()` calls. Report evidence, severity, impact, and a minimal fix.
