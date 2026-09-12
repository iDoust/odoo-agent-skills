---
name: odoo-upgrade
description: Analyze and plan Odoo 17 to 18 and 18 to 19 module upgrades with source-verified migration checks.
---

# Odoo upgrades

Use this workflow for a module or database upgrade. Identify both source and
target versions, edition, installed modules, custom addons, and migration
tooling before proposing changes.

1. Inventory manifests, dependencies, models, views, data, security, assets,
   controllers, tests, and migration scripts.
2. Compare the source and target Odoo Community and Enterprise code paths.
3. Search for deprecated, removed, renamed, or behaviorally changed APIs.
4. Separate mandatory fixes from optional modernization.
5. Make migration steps idempotent and safe for existing data.
6. Add focused tests for transformed data, permissions, company isolation, and
   changed workflows.
7. Validate installation, upgrade, and rollback assumptions in a representative
   environment.

Primary supported paths are 17 to 18 and 18 to 19. A direct 17 to 19 upgrade
must still apply both sets of checks.

Load `../../references/migrations/common.md`, `../../references/operations/oca-guidelines.md`,
the target version references (`../../references/versions/17.md`, `../../references/versions/18.md`,
`../../references/versions/19.md`, `../../references/versions/editions.md`), and the
relevant domain/security/frontend references. Run `scripts/scan_deprecations.py` to
statically verify custom addons against the target version.
