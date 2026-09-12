# OCA (Odoo Community Association) Guidelines & OpenUpgrade

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  OCA STANDARDS & OPENUPGRADE MIGRATION GUIDE                                 ║
║  Best practices for community modules, git conventions, and database upgrades║
║  Targets Odoo 17, 18, and 19 module development                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

The **Odoo Community Association (OCA)** is the global non-profit organization that maintains thousands of open-source Odoo modules. OCA standards represent the de-facto industry benchmark for module code quality, git hygiene, and database schema migrations.

---

## 1. OCA Git Commit Message Conventions

OCA enforces strict, structured git commit messages to ensure clean history and automated changelog generation.

### Format
```text
[TAG] module_name: concise summary in present imperative tense

Detailed explanation of why the change is necessary, edge cases handled,
and references to tickets or upstream PRs.

Fixes #123
```

### Standard Tags
| Tag | Meaning | Example |
| :--- | :--- | :--- |
| `[FIX]` | Bug fix that resolves an unexpected error or crash | `[FIX] sale_stock: prevent negative reserved quantity on reorder` |
| `[IMP]` | Improvement or minor feature enhancement | `[IMP] account_invoice: optimize SQL query for partner balance` |
| `[ADD]` | New module or major new feature addition | `[ADD] purchase_approval: multi-tier approval workflow` |
| `[REF]` | Refactoring internal logic without altering public behavior | `[REF] stock: simplify move line allocation logic` |
| `[REM]` | Deletion of obsolete fields, views, or dead code | `[REM] pos_custom: remove obsolete v16 workarounds` |
| `[MIG]` | Migration of module to a new major Odoo version | `[MIG] hr_attendance: migrate module from 17.0 to 18.0` |
| `[MOV]` | Moving files, views, or models between locations | `[MOV] product: relocate static assets into web bundle` |

---

## 2. Manifest & Module Quality Standards

OCA modules adhere to strict manifest properties in `__manifest__.py`:

```python
{
    'name': 'Custom Purchase Multi-Approval',
    'version': '18.0.1.0.0',
    'category': 'Purchases',
    'author': 'Your Company, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/purchase-workflow',
    'license': 'LGPL-3',
    'development_status': 'Production/Stable',  # Alpha, Beta, Production/Stable, Mature
    'maintainers': ['your_github_username'],
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
```

### Code Formatting & Linters
- **Python**: PEP 8 formatted with `ruff` or `black` (line length: 88 or 120 chars).
- **pylint-odoo**: Official OCA linter plugin checking Odoo conventions:
  - Model names must use dots (`my.model`), tables must use underscores (`my_model`).
  - No SQL injection (always parameterize `%s`).
  - Translatable strings `_()` must use literal string arguments without f-strings.

---

## 3. Database Migration with `openupgradelib`

### Why `odoo-bin -u` is Not Enough for Version Upgrades
When upgrading an Odoo database between major versions (e.g. 17.0 ➔ 18.0):
- Standard `odoo-bin -u my_module` only creates newly declared columns and updates XML views.
- It **cannot** rename existing tables or columns without dropping them and recreating empty ones, leading to **data loss**.
- **`openupgradelib`** solves this by executing database transformations via SQL before and after Odoo's ORM initializes.

### Installation
```bash
pip install openupgradelib
```

### Module Migration Directory Layout
Odoo executes migration scripts automatically when updating a module if they are placed in `migrations/<version>/`:

```text
my_module/
├── __manifest__.py
├── models/
└── migrations/
    └── 18.0.1.0.0/
        ├── pre-migration.py   # Runs BEFORE models are loaded in memory
        └── post-migration.py  # Runs AFTER models and views are loaded
```

---

### Step-by-Step Migration Pattern

#### A. Pre-Migration (`pre-migration.py`)
Used for low-level schema operations: renaming tables, renaming columns, or preserving legacy columns before the ORM tries to create new ones:

```python
from openupgradelib import openupgrade


# Column renaming specification: (model_name, table_name, old_col, new_col)
column_renames = {
    'custom.equipment': [
        ('equipment_serial', 'serial_number'),
        ('cost_price', 'purchase_value'),
    ],
}

# Table renaming specification: (old_table, new_table)
table_renames = [
    ('custom_asset_legacy', 'custom_equipment'),
]


def migrate(cr, version):
    """Executes BEFORE Odoo loads model definitions."""
    if not version:
        return

    # 1. Rename tables safely
    openupgrade.rename_tables(cr, table_renames)

    # 2. Rename columns before ORM adds new ones
    openupgrade.rename_columns(cr, column_renames)

    # 3. Rename models in Odoo's metadata registry
    openupgrade.rename_models(cr, [
        ('custom.asset.legacy', 'custom.equipment'),
    ])

    # 4. Rename XML external IDs if records moved
    openupgrade.rename_xmlids(cr, [
        ('my_module.legacy_group_user', 'my_module.group_equipment_user'),
    ])
```

#### B. Post-Migration (`post-migration.py`)
Used for data transformations, populating new fields, or calculating values using the ORM:

```python
from odoo import api, SUPERUSER_ID
from openupgradelib import openupgrade


def migrate(cr, version):
    """Executes AFTER Odoo creates tables and loads models/views."""
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Map selection field values (e.g. status code changes)
    openupgrade.map_values(
        cr,
        mapping_spec={
            'custom.equipment': {
                'state': [('in_use', 'active'), ('broken', 'maintenance')],
            }
        }
    )

    # 2. Populate new computed stored values
    equipments = env['custom.equipment'].search([('purchase_value', '>', 0), ('currency_id', '=', False)])
    if equipments:
        default_currency = env.company.currency_id.id
        equipments.write({'currency_id': default_currency})
```

---

## 4. Key OpenUpgrade Helper Functions Reference

| Function | Purpose | Typical Timing |
| :--- | :--- | :--- |
| `openupgrade.rename_columns(cr, spec)` | Renames DB columns without dropping data | `pre-migration` |
| `openupgrade.rename_tables(cr, spec)` | Renames DB tables | `pre-migration` |
| `openupgrade.rename_models(cr, spec)` | Updates `ir.model`, `ir.model.fields`, and ACLs | `pre-migration` |
| `openupgrade.rename_xmlids(cr, spec)` | Updates `ir.model.data` entries for moved resources | `pre-migration` |
| `openupgrade.drop_columns(cr, spec)` | Cleans up obsolete columns after data is migrated | `post-migration` |
| `openupgrade.map_values(cr, spec)` | Converts old selection strings to new selection strings | `post-migration` |
| `openupgrade.set_defaults(env, spec)` | Sets default values on existing records for new required fields | `post-migration` |

## Related References

- [Data Migration and Upgrade Baseline](../migrations/common.md)
- [Deprecation Scanner Script](../../scripts/scan_deprecations.py)
- [Operations Directory Index](README.md)
- [Module Review Workflow](../../skills/odoo-review/SKILL.md)
- [Module Upgrade Workflow](../../skills/odoo-upgrade/SKILL.md)
