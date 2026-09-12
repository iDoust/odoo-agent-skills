# Odoo Migration and Data Upgrade Baseline

Comprehensive guide for migrating custom Odoo modules and transforming database records across major versions: **17 → 18** and **18 → 19**.

---

## 1. Migration Directory Architecture

Odoo automatically discovers and runs migration scripts placed inside the `migrations/` directory of a module when upgraded with `-u {module}`.

```text
my_module/
├── __init__.py
├── __manifest__.py
├── models/
├── views/
└── migrations/
    ├── 18.0.1.0/
    │   ├── pre-migrate.py    # Runs BEFORE module schema is updated by the ORM
    │   └── post-migrate.py   # Runs AFTER module schema is updated by the ORM
    └── 19.0.1.0/
        ├── pre-migrate.py
        └── post-migrate.py
```

### Script Execution Rules

- **Directory Name:** Must match the target manifest version (e.g. `18.0.1.0` or `18.0.1.0.0`).
- **Trigger Condition:** The script executes only if the database version currently stored in `ir_module_module` is lower than the directory version.
- **Entry Point:** Each script must define a top-level `migrate(cr, version)` function:

```python
def migrate(cr, version):
    """
    :param cr: database cursor (psycopg2 cursor)
    :param version: current installed version in database before upgrade (str)
    """
```

---

## 2. Pre-Migration (`pre-migrate.py`)

Run **before** the Odoo ORM updates the database schema, models, and views.

### When to Use Pre-Migration:
- Renaming an existing column or table to prevent the ORM from creating a blank new column and dropping the old one.
- Renaming a model XML ID in `ir_model_data`.
- Altering existing column constraints (e.g., removing `NOT NULL` temporarily so the ORM can add new fields without failure).

### Pre-Migration Example (Native SQL + `odoo.tools.sql`)

```python
import logging
from odoo.tools.sql import column_exists, rename_column, table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("Running pre-migration for my_module to 18.0.1.0")

    # 1. Rename column before ORM initializes to avoid losing legacy data
    # Scenario: Field 'delivery_priority' was renamed to 'priority_level'
    if column_exists(cr, "my_order", "delivery_priority"):
        # Rename to temporary column so ORM doesn't overwrite it
        rename_column(cr, "my_order", "delivery_priority", "openupgrade_legacy_delivery_priority")
        _logger.info("Renamed column delivery_priority to openupgrade_legacy_delivery_priority")

    # 2. Rename table if model was renamed
    # Scenario: Model 'my.old.model' renamed to 'my.new.model'
    if table_exists(cr, "my_old_model") and not table_exists(cr, "my_new_model"):
        cr.execute("ALTER TABLE my_old_model RENAME TO my_new_model")
        _logger.info("Renamed table my_old_model to my_new_model")
```

---

## 3. Post-Migration (`post-migrate.py`)

Run **after** the Odoo ORM has updated tables, created new columns, and loaded XML data/views.

### When to Use Post-Migration:
- Copying and transforming data from temporary columns (`openupgrade_legacy_*`) into newly created ORM fields.
- Computing values for newly added `required=True` fields that have no default.
- Updating relational links (Many2many, One2many).
- Cleaning up temporary columns.

### Post-Migration Example (Data Transformation & Cleanup)

```python
import logging
from odoo import api, SUPERUSER_ID
from odoo.tools.sql import column_exists, drop_column

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("Running post-migration for my_module to 18.0.1.0")

    # 1. Transform data from temporary column to new column
    if column_exists(cr, "my_order", "openupgrade_legacy_delivery_priority"):
        # Direct SQL data transformation is faster and avoids ORM overhead on large datasets
        cr.execute("""
            UPDATE my_order
            SET priority_level = CASE
                WHEN openupgrade_legacy_delivery_priority = 'high' THEN 'urgent'
                WHEN openupgrade_legacy_delivery_priority = 'medium' THEN 'normal'
                ELSE 'low'
            END
            WHERE priority_level IS NULL
        """)
        _logger.info("Transformed priority values into priority_level")

        # 2. Drop temporary legacy column after successful transformation
        drop_column(cr, "my_order", "openupgrade_legacy_delivery_priority")
        _logger.info("Dropped temporary column openupgrade_legacy_delivery_priority")

    # 3. Use Environment for business logic that requires model methods or recomputations
    env = api.Environment(cr, SUPERUSER_ID, {})
    orders_to_recompute = env['my.order'].search([('state', '=', 'confirmed'), ('amount_total', '=', 0.0)])
    if orders_to_recompute:
        _logger.info("Recomputing totals for %d orders", len(orders_to_recompute))
        orders_to_recompute._compute_amount_total()
```

---

## 4. Writing Idempotent Migrations

A migration script must be **idempotent**: running it multiple times (e.g. if the upgrade crashes halfway and is retried) must produce the exact same outcome without errors or data duplication.

### Idempotency Checklist:
- Always guard column operations with `column_exists(cr, table, column)`.
- Always guard table operations with `table_exists(cr, table)`.
- Use `WHERE {new_field} IS NULL` when updating default values to avoid overwriting existing valid data.
- Check XML ID renames before updating:

```python
cr.execute("""
    UPDATE ir_model_data
    SET name = 'new_xml_id'
    WHERE module = 'my_module' AND name = 'old_xml_id'
      AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'my_module' AND name = 'new_xml_id')
""")
```

---

## 5. Major Version Migration Rules (17 → 18 → 19)

### Upgrading from Odoo 17 to Odoo 18
1. **Views:** Rename `<tree>` tags to `<list>` in custom views.
2. **List XPath:** Update any xpath targeting parent tree views from `expr="//tree"` to `expr="//list"`.
3. **Product Storable:** If inheriting stock products, migrate from `detailed_type` to `is_storable=True`.
4. **Display Name Search:** Update overrides of `_name_search` to `_search_display_name`.

### Upgrading from Odoo 18 to Odoo 19
1. **Controller Routes:** Replace `type='json'` with `type='jsonrpc'` in all `@http.route` definitions.
2. **SQL Constraints:** Migrate `_sql_constraints` to `models.Constraint` objects to silence Odoo 19 deprecation warnings.
3. **Environment Properties:** Replace deprecated `record._cr`, `record._uid`, `record._context` with `record.env.cr`, `record.env.uid`, `record.env.context`.
4. **Domain Class:** Replace `odoo.osv.expression` with `odoo.fields.Domain` or `odoo.orm.domains.Domain`.

---

## 6. Migration Testing Protocol

Never run migration scripts directly on production. Follow this verification sequence:

```bash
# 1. Restore production backup onto staging/test environment
pg_restore -d test_staging_db /path/to/prod_backup.dump

# 2. Run the module upgrade with log-level=debug
odoo-bin -c /etc/odoo.conf -d test_staging_db -u my_module --stop-after-init --log-level=debug

# 3. Verify no SQL errors, missing column warnings, or broken views in logs
# 4. Check data integrity (count of records, sum of financial fields)
```

---

## 7. Migration Tooling & Community Standards

- **Automated Deprecation Scanner**: Before running migrations, scan custom addons for deprecated syntax and API incompatibilities:
  ```bash
  python3 scripts/scan_deprecations.py /path/to/addon --target 18
  python3 scripts/scan_deprecations.py /path/to/addon --target 19 --fail-on-warning
  ```
- **OCA & OpenUpgrade Guidelines**: For standard migration scripts utilizing `openupgradelib` helper utilities (table, column, model, XML ID renames) and OCA code review standards, consult:
  - [`references/operations/oca-guidelines.md`](../operations/oca-guidelines.md)
