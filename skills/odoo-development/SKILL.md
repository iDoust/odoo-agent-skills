---
name: odoo-development
description: Develop and modify Odoo 17, 18, and 19 modules with version-aware ORM, XML views, security, OWL, testing, and upgrade guidance.
---

# Odoo development

Use this skill for Odoo module development, debugging, review, security,
testing, frontend work, and upgrades targeting Odoo 17, 18, or 19.

## Supported versions

This core supports Odoo 17, 18, and 19 only. Detect the major version before
using version-specific guidance. If the project is older than 17, say that it
is outside the supported range instead of silently applying this skill.

## Workflow

1. Understand the requested behavior and its acceptance criteria.
2. Detect the Odoo major version from the project manifest, source tree, or
   runtime metadata. Do not infer it from a module name alone.
3. Confirm that the version is 17, 18, or 19.
4. Identify the environment: Community, Enterprise, OCA, or custom addons.
5. Inspect the existing module, callers, tests, views, data, and security.
6. Inspect related Odoo core code when the behavior or version boundary matters.
7. Search for an existing project or Odoo mechanism before adding custom code.
8. Load only the references relevant to the task and detected version.
9. Implement the smallest correct change that matches the target version.
10. Review security, access rights, record rules, company isolation, ORM
    semantics, and performance when relevant.
11. Run the smallest meaningful test or validation.
12. Report any unverified version assumption explicitly.

## Reference navigation

| Task | Load |
| --- | --- |
| ORM, models, fields, recordsets | `../../references/orm/common.md` |
| Core mixins (Chatter, images, UTM, ratings) | `../../references/orm/mixins.md` |
| XML views and view inheritance | `../../references/views/common.md` |
| OWL, frontend components, services | `../../references/owl/common.md` |
| ACLs, record rules, groups, access | `../../references/security/common.md` |
| Python and browser-facing tests | `../../references/testing/common.md` |
| QA / SIT test planning and coverage matrix | `../../references/testing/qa-plan.md` |
| Module-domain patterns | `../../references/modules/README.md` |
| Performance and SQL | `../../references/performance/guide.md` |
| Web controllers and webhooks | `../../references/integrations/controllers.md` |
| External APIs (JSON-2, JSON-RPC, XML-RPC) | `../../references/integrations/external-api.md` |
| Bulk data import/export and data loading | `../../references/integrations/import-export.md` |
| Scheduled actions, background jobs, and cron | `../../references/operations/cron.md` |
| Email templates, mail server, and message routing | `../../references/operations/mail.md` |
| Structured logging, log levels, and diagnostics | `../../references/operations/logging.md` |
| Data migration and upgrades | `../../references/migrations/common.md` |
| OCA guidelines and openupgradelib | `../../references/operations/oca-guidelines.md` |
| CE solutions for Enterprise features | `../../references/modules/community-enterprise-solutions.md` |
| CLI tools, REPL shell, and debugging | `../../references/operations/cli-and-shell.md` |
| Deployment, release, and production readiness | `../../references/operations/deployment.md` |
| Post-deployment monitoring and hypercare | `../../references/operations/monitoring.md` |
| Community vs Enterprise edition differences | `../../references/versions/editions.md` |
| Source code repository matrix and branch heads | `../../references/versions/source-matrix.md` |
| Odoo 17 behavior and deltas | `../../references/versions/17.md` |
| Odoo 18 behavior and deltas | `../../references/versions/18.md` |
| Odoo 19 behavior and deltas | `../../references/versions/19.md` |

## Optional capability skills

| Capability | Load |
| --- | --- |
| Doodba environment and local code indexer | `../odoo-doodba/SKILL.md` |
| Read-only live-instance investigation | `../odoo-query/SKILL.md` |
| Explicit command-output compaction | `../odoo-token-killer/SKILL.md` |

Use the existing project implementation first, then Odoo core, installed
dependencies, relevant OCA patterns, and finally a custom implementation.
Do not introduce an Enterprise dependency into a Community project unless the
requirement is explicit.

## Standard architecture and financial integrity

Odoo is fundamentally an integrated ERP where business transactions (sales,
purchases, inventory, payments, manufacturing) flow into standard double-entry
accounting (`account.move`).

- **Do not reinvent core ERP flows**: Always extend standard Odoo models
  (`sale.order`, `purchase.order`, `stock.picking`, `account.move`) rather
  than creating parallel shadow tables or disconnected transaction logs.
- **International accounting compliance**: Strictly uphold IFRS/GAAP
  principles: every posted entry must balance (`debit == credit`), posted
  entries are immutable (correct via `account.move.reversal`), multi-currency
  must preserve functional currency balances (IAS 21), and period lock dates
  must never be bypassed.
- **Zero raw SQL mutations on ledgers**: Never perform raw SQL `UPDATE` or
  `DELETE` on financial records (`account_move`, `account_move_line`).


## Version decisions

Treat version references as deltas from the shared guidance, not as complete
copies of Odoo documentation. When a version-specific claim affects generated
code, verify it against the target Odoo source and official documentation.

For upgrades, analyze the actual source and target versions. The primary
supported paths are 17 to 18 and 18 to 19; a direct 17 to 19 upgrade needs the
same intermediate checks.

## Completion check

Before finishing, confirm that the change is version-compatible, does not
weaken access control or company isolation, preserves existing behavior outside
the requested scope, and has a focused runnable validation.
