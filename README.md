# Odoo Agent Skills

Universal Agent Skills for modern Odoo development, focused on **Odoo 17, 18,
and 19**. The core provides reusable, version-aware guidance for module
development, ORM, XML views, security, testing, frontend work, debugging,
upgrades, and community standards.

The core is tool-neutral and can be consumed by Agent Skills-compatible coding
agents. Vendor-specific integrations are optional and are not part of the core
instructions.

## Supported Versions

| Version | Status |
| --- | --- |
| Odoo 17 | ✅ Fully supported |
| Odoo 18 | ✅ Fully supported |
| Odoo 19 | ✅ Fully supported |
| Odoo ≤ 16 | ❌ Unsupported (retained only for migration context) |

---

## Skills

Each skill provides a focused workflow and links to the references it needs.
The entry point is `skills/odoo-development/SKILL.md`.

| Skill | Purpose |
| --- | --- |
| [`odoo-development`](skills/odoo-development/SKILL.md) | Module development, ORM, views, frontend, and version-aware guidance |
| [`odoo-debug`](skills/odoo-debug/SKILL.md) | Systematic root-cause diagnosis from tracebacks, errors, and symptoms |
| [`odoo-review`](skills/odoo-review/SKILL.md) | Multi-axis code review (correctness, security, performance, maintainability) |
| [`odoo-security`](skills/odoo-security/SKILL.md) | Access rights, record rules, groups, controllers, and data exposure audits |
| [`odoo-test`](skills/odoo-test/SKILL.md) | Test planning, execution, and diagnostics across all test layers |
| [`odoo-upgrade`](skills/odoo-upgrade/SKILL.md) | Version upgrade analysis and migration script authoring (17→18, 18→19) |
| [`odoo-doodba`](skills/odoo-doodba/SKILL.md) | Doodba/Docker environment indexing and codebase search |
| [`odoo-query`](skills/odoo-query/SKILL.md) | Read-only XML-RPC live instance inspection |
| [`odoo-token-killer`](skills/odoo-token-killer/SKILL.md) | CLI compaction of noisy Odoo command output |

---

## References

Detailed knowledge lives under `references/` and is loaded progressively by
each skill as needed.

### ORM & Models

| Reference | Contents |
| --- | --- |
| [`orm/common.md`](references/orm/common.md) | Core ORM, models, fields, recordsets |
| [`orm/mixins.md`](references/orm/mixins.md) | `mail.thread`, `image.mixin`, `utm.mixin`, `portal.mixin`, etc. |
| [`orm/inheritance-patterns.md`](references/orm/inheritance-patterns.md) | Extension, delegation, prototype inheritance and view inheritance |
| [`orm/computed-field-patterns.md`](references/orm/computed-field-patterns.md) | Computed, related, and inverse fields |
| [`orm/field-type-reference.md`](references/orm/field-type-reference.md) | All field types with parameters and usage |
| [`orm/constraint-patterns.md`](references/orm/constraint-patterns.md) | Python and SQL constraints |
| [`orm/context-environment-patterns.md`](references/orm/context-environment-patterns.md) | `self.env`, `with_context`, `with_company`, `sudo()` |
| [`orm/domain-filter-patterns.md`](references/orm/domain-filter-patterns.md) | Domain syntax, operators, and composition |
| [`orm/wizard-patterns.md`](references/orm/wizard-patterns.md) | Transient models and wizard workflows |
| [`orm/workflow-state-patterns.md`](references/orm/workflow-state-patterns.md) | State machines, statusbar, and transition guards |
| [`orm/onchange-dynamic-patterns.md`](references/orm/onchange-dynamic-patterns.md) | Onchange, dynamic domains, and conditional visibility |
| [`orm/sequence-numbering-patterns.md`](references/orm/sequence-numbering-patterns.md) | `ir.sequence` and automatic numbering |
| [`orm/attachment-binary-patterns.md`](references/orm/attachment-binary-patterns.md) | Binary fields, `ir.attachment`, and file handling |
| [`orm/config-settings-patterns.md`](references/orm/config-settings-patterns.md) | `res.config.settings` and system parameters |
| [`orm/error-handling-patterns.md`](references/orm/error-handling-patterns.md) | `UserError`, `ValidationError`, and exception handling |

### Views & Frontend

| Reference | Contents |
| --- | --- |
| [`views/common.md`](references/views/common.md) | XML view architecture and view inheritance |
| [`views/xml-view-patterns.md`](references/views/xml-view-patterns.md) | Form, list, kanban, search, and calendar views |
| [`views/action-patterns.md`](references/views/action-patterns.md) | Window, server, URL, and client actions |
| [`views/menu-navigation-patterns.md`](references/views/menu-navigation-patterns.md) | Menu items, root menus, and navigation |
| [`views/widgets.md`](references/views/widgets.md) | Field widgets and custom widget usage |
| [`views/qweb-template-patterns.md`](references/views/qweb-template-patterns.md) | QWeb templates and directives |
| [`views/report-patterns.md`](references/views/report-patterns.md) | PDF/HTML reports and `ir.actions.report` |
| [`views/assets.md`](references/views/assets.md) | Asset bundles and static file registration |
| [`views/translation-i18n-patterns.md`](references/views/translation-i18n-patterns.md) | Internationalization and `_()` translations |
| [`owl/common.md`](references/owl/common.md) | OWL components, services, hooks, and frontend architecture |

### Security

| Reference | Contents |
| --- | --- |
| [`security/common.md`](references/security/common.md) | ACLs, record rules, groups, and access control |
| [`security/patterns.md`](references/security/patterns.md) | Security design patterns and best practices |
| [`security/multi-company.md`](references/security/multi-company.md) | Multi-company isolation and `company_ids` |
| [`security/portal-access-patterns.md`](references/security/portal-access-patterns.md) | Portal user access and record rules |

### Testing

| Reference | Contents |
| --- | --- |
| [`testing/common.md`](references/testing/common.md) | Shared testing baseline |
| [`testing/odoo.md`](references/testing/odoo.md) | Master testing handbook (TransactionCase, Form, HttpCase, HOOT, QUnit) |
| [`testing/qa-plan.md`](references/testing/qa-plan.md) | QA / SIT test planning and coverage matrix |
| [`testing/troubleshooting.md`](references/testing/troubleshooting.md) | Debugging test failures and common pitfalls |

### Modules & Domain Patterns

| Reference | Contents |
| --- | --- |
| [`modules/README.md`](references/modules/README.md) | Module reference index |
| [`modules/module-structure.md`](references/modules/module-structure.md) | Module directory layout and `__manifest__.py` |
| [`modules/accounting.md`](references/modules/accounting.md) | `account.move`, journals, taxes, reconciliation |
| [`modules/inventory.md`](references/modules/inventory.md) | `stock.picking`, routes, warehouses, operations |
| [`modules/purchase.md`](references/modules/purchase.md) | Purchase orders and procurement |
| [`modules/sales.md`](references/modules/sales.md) | Sale orders, CRM, and quotations |
| [`modules/manufacturing.md`](references/modules/manufacturing.md) | MRP, BoM, and production orders |
| [`modules/pos.md`](references/modules/pos.md) | Point of Sale sessions and configuration |
| [`modules/website.md`](references/modules/website.md) | Website builder and eCommerce |
| [`modules/portal.md`](references/modules/portal.md) | Customer portal and public access |
| [`modules/hr.md`](references/modules/hr.md) | HR, employees, and attendance |
| [`modules/project.md`](references/modules/project.md) | Projects, tasks, and timesheets |
| [`modules/products.md`](references/modules/products.md) | Product templates and variants |
| [`modules/pricing.md`](references/modules/pricing.md) | Pricelists and discount rules |
| [`modules/tax.md`](references/modules/tax.md) | Tax computation and fiscal positions |
| [`modules/uom.md`](references/modules/uom.md) | Units of measure |
| [`modules/lot-serial.md`](references/modules/lot-serial.md) | Lot and serial number tracking |
| [`modules/dashboard-kpi-patterns.md`](references/modules/dashboard-kpi-patterns.md) | Dashboards and KPI display patterns |
| [`modules/templates.md`](references/modules/templates.md) | Module generation templates |
| [`modules/generation-example.md`](references/modules/generation-example.md) | Full module generation walkthrough |
| [`modules/community-enterprise-solutions.md`](references/modules/community-enterprise-solutions.md) | CE alternatives for Enterprise features (Financial Reports, Barcode, Approvals, Signatures, DMS) |

### Integrations

| Reference | Contents |
| --- | --- |
| [`integrations/README.md`](references/integrations/README.md) | Integrations directory index |
| [`integrations/controllers.md`](references/integrations/controllers.md) | Web controllers, `@http.route`, and webhooks |
| [`integrations/external-api.md`](references/integrations/external-api.md) | JSON-RPC, XML-RPC, and external API access |
| [`integrations/import-export.md`](references/integrations/import-export.md) | Data import/export and CSV/Excel handling |

### Migrations & Upgrades

| Reference | Contents |
| --- | --- |
| [`migrations/common.md`](references/migrations/common.md) | Migration directory architecture, pre/post scripts, and version rules |

### Operations

| Reference | Contents |
| --- | --- |
| [`operations/README.md`](references/operations/README.md) | Operations directory index |
| [`operations/cli-and-shell.md`](references/operations/cli-and-shell.md) | `odoo-bin`, shell REPL, and debugging commands |
| [`operations/deployment.md`](references/operations/deployment.md) | Deployment, release readiness, and Definition of Done |
| [`operations/monitoring.md`](references/operations/monitoring.md) | Post-deployment monitoring and hypercare |
| [`operations/cron.md`](references/operations/cron.md) | `ir.cron` scheduled actions |
| [`operations/logging.md`](references/operations/logging.md) | Logging configuration and patterns |
| [`operations/mail.md`](references/operations/mail.md) | Mail templates and email sending |
| [`operations/oca-guidelines.md`](references/operations/oca-guidelines.md) | OCA commit conventions, manifest standards, `pylint-odoo`, and `openupgradelib` migration guide |

### Versions & Editions

| Reference | Contents |
| --- | --- |
| [`versions/README.md`](references/versions/README.md) | Versions directory index |
| [`versions/17.md`](references/versions/17.md) | Odoo 17 behavior and deltas |
| [`versions/18.md`](references/versions/18.md) | Odoo 18 behavior and deltas |
| [`versions/19.md`](references/versions/19.md) | Odoo 19 behavior and deltas |
| [`versions/editions.md`](references/versions/editions.md) | Community vs Enterprise comparison |
| [`versions/source-matrix.md`](references/versions/source-matrix.md) | Local source tree paths and version matrix |

### Performance

| Reference | Contents |
| --- | --- |
| [`performance/guide.md`](references/performance/guide.md) | Query optimization, N+1 prevention, caching, and profiling |

---

## Developer Tooling

### Deprecation Scanner

Static analysis tool that scans custom Odoo modules for deprecated APIs,
breaking syntax changes, and version incompatibilities.

```bash
# Scan targeting Odoo 18
python3 scripts/scan_deprecations.py /path/to/addon --target 18

# Scan targeting Odoo 19 with strict mode
python3 scripts/scan_deprecations.py /path/to/addon --target 19 --fail-on-warning

# JSON output for CI integration
python3 scripts/scan_deprecations.py /path/to/addon --target 19 --format json
```

Detects: `_name_search` → `_search_display_name`, `name_get` →
`_compute_display_name`, `<tree>` → `<list>`, `type='json'` → `type='jsonrpc'`,
`_sql_constraints` → `models.Constraint`, `odoo.osv.expression` → `Domain`,
`detailed_type` → `is_storable`, `group_operator` → `aggregator`, legacy
`attrs`/`states` syntax, dangerous `cr.commit()`, and more.

Zero dependencies — uses only Python standard library.

### Validation

```bash
# Validate core structure (skills, references, links, frontmatter)
python3 scripts/validate.py

# Run validator tests
python3 -m unittest scripts/test_validate.py

# Run deprecation scanner tests
python3 -m unittest scripts/test_scan_deprecations.py

# Run all script tests
python3 -m unittest discover scripts
```

---

## Project Structure

```text
skills/
├── odoo-development/SKILL.md     # Main entry point
├── odoo-debug/SKILL.md
├── odoo-review/SKILL.md
├── odoo-security/SKILL.md
├── odoo-test/SKILL.md
├── odoo-upgrade/SKILL.md
├── odoo-doodba/                  # Doodba indexer + tests
│   ├── SKILL.md
│   ├── indexer/
│   └── tests/
├── odoo-query/                   # XML-RPC client + tests
│   ├── SKILL.md
│   ├── scripts/odoo_xmlrpc.py
│   └── tests/
└── odoo-token-killer/            # Rust CLI for output compaction
    ├── SKILL.md
    └── core/
references/
├── integrations/                 # Controllers, external APIs, import/export
├── migrations/                   # Pre/post migration scripts and upgrade rules
├── modules/                      # 20 domain-specific module references
├── operations/                   # CLI, deployment, monitoring, OCA, cron, mail, logging
├── orm/                          # 15 ORM pattern references
├── owl/                          # OWL frontend architecture
├── performance/                  # Query optimization and profiling
├── security/                     # ACLs, record rules, multi-company, portal
├── testing/                      # Test handbook, QA plan, troubleshooting
├── versions/                     # Version deltas (17, 18, 19), editions, source matrix
└── views/                        # XML views, actions, widgets, QWeb, reports, assets
scripts/
├── scan_deprecations.py          # Deprecation scanner CLI
├── test_scan_deprecations.py     # Scanner unit tests
├── validate.py                   # Core structure validator
├── test_validate.py              # Validator tests
├── smoke_test.py                 # Smoke tests
└── test_real_odoo_references.py  # Reference verification against local Odoo sources
```

---

## Quick Start

1. Clone the repository and keep the directory structure intact:
   ```bash
   git clone https://github.com/iDoust/odoo-agent-skills.git
   ```

2. Point your agent to the entry skill:
   ```text
   skills/odoo-development/SKILL.md
   ```

3. Validate the core:
   ```bash
   python3 scripts/validate.py
   ```

No external dependencies are required for the core. The Doodba indexer
requires `uv` and the token-killer requires a Rust toolchain; both are
optional.

## Upstream Compatibility

This repository started as a Claude Code marketplace plugin. Reusable parts
of the Doodba, query, and output-optimization plugins now live under
`skills/`; the old marketplace wrapper and its vendor-specific files are
archived outside the repository.

The universal core is the canonical path for all new Odoo 17–19 guidance.
No adapter is required to use the core.

See [UPSTREAM.md](UPSTREAM.md) for provenance, licensing, and migration notes.

## License

MIT — see [LICENSE](LICENSE).
