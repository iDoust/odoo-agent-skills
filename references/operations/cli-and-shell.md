# Odoo Shell and CLI Diagnostic Operations

Comprehensive guide for interactive debugging, headless script execution, database diagnostics, and native CLI utilities across **Odoo 17, 18, and 19**.

---

## 1. Interactive REPL (`odoo-bin shell`)

The `shell` command starts an interactive Python console with a fully initialized Odoo database cursor and ORM environment, without starting the HTTP web server.

### Starting the Shell

```bash
# Basic invocation with database
python3 odoo-bin shell -d my_database -c /etc/odoo.conf

# With specific shell interface (IPython provides tab-completion, ? docs, %timeit)
python3 odoo-bin shell -d my_database -c /etc/odoo.conf --shell-interface=ipython

# With SQL query logging visible in console
python3 odoo-bin shell -d my_database -c /etc/odoo.conf --log-level=debug_sql
```

### Pre-Loaded Local Variables

When the shell starts, Odoo injects the following global variables into the console session:

| Variable | Type | Description |
| :--- | :--- | :--- |
| `env` | `odoo.api.Environment` | Root environment running as Superuser (`SUPERUSER_ID = 1`). |
| `self` | `res.users` recordset | The administrator user record (`env.user`, ID: 1). |
| `odoo` | Module | The root `odoo` package. |

---

## 2. The Rollback-by-Default Architecture (Critical Gotcha)

Under the hood (`odoo/cli/shell.py`), Odoo wraps the shell session in a database cursor that **automatically calls `cr.rollback()` on exit**:

```python
# From odoo/cli/shell.py
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, uid, ctx)
    local_vars['env'] = env
    cr.rollback()           # Rollback on start
    self.console(local_vars)
    cr.rollback()           # Rollback on exit
```

### Key Rule for Database Changes:
- **Read-Only / Diagnostics:** Safe by default on production replicas because nothing is persisted without explicit commit.
- **Data Repairs / Maintenance:** If you create, write, or delete records and want the changes persisted in the database, you **MUST explicitly call `env.cr.commit()`**:
```python
# Interactive console example
partner = env['res.partner'].create({'name': 'Acme Corp'})
partner.action_confirm()

# Persist changes to PostgreSQL
env.cr.commit()
```

---

## 3. Headless Script Execution via Pipe (Batch Automation)

You can execute non-interactive Python repair and maintenance scripts through `odoo-bin shell` without manual typing.

When stdin is not a TTY terminal, `odoo/cli/shell.py` reads and executes the entire stream with `env` pre-configured.

### Running a Script File

```bash
# Pipe script directly into odoo shell
python3 odoo-bin shell -d my_database -c /etc/odoo.conf --no-http < fix_data.py
```

### Script Template (`fix_data.py`)

```python
# fix_data.py - env is automatically available
import logging

_logger = logging.getLogger('odoo.maintenance')

partners = env['res.partner'].search([('email', '=', False), ('customer_rank', '>', 0)])
_logger.info("Found %d customers without email addresses.", len(partners))

for idx, partner in enumerate(partners, 1):
    partner.email = f"customer_{partner.id}@placeholder.internal"
    # Commit in bounded batches to avoid huge transaction locks
    if idx % 500 == 0:
        env.cr.commit()
        _logger.info("Processed and committed %d records...", idx)

# Final commit for remaining records
env.cr.commit()
_logger.info("Data repair script finished successfully.")
```

### Inline One-Liner Execution (`--command`)

```bash
python3 odoo-bin shell -d my_database -c /etc/odoo.conf --no-http \
    --command="env['ir.cron'].search([('active', '=', True)]).method_direct_trigger(); env.cr.commit()"
```

---

## 4. Context Switching in Shell

To test access rights, multi-company rules, or language behavior in the shell:

```python
# 1. Test as specific regular user (verify ACL & Record Rules)
demo_user = env.ref('base.user_demo')
user_env = env.with_user(demo_user)
try:
    user_env['account.move'].search([])
except Exception as e:
    print("User restricted:", e)

# 2. Test in different company context
company_b = env['res.company'].browse(2)
comp_env = env.with_company(company_b)
orders_comp_b = comp_env['sale.order'].search([])

# 3. Test in different language
fr_env = env.with_context(lang='fr_FR')
product = fr_env['product.product'].browse(1)
print("French name:", product.name)

# 4. Sudo bypass
sudo_records = env['my.model'].sudo().search([])
```

---

## 5. Data Inspection and ORM Introspection in Shell

`odoo shell` provides direct access to the active Python process and ORM registry, making it the most powerful tool for investigating corrupted states, computed field logic, and security rules:

### A. Model and Field Metadata Inspection

```python
# Inspect field definition, compute methods, and dependencies
field = env['sale.order']._fields['amount_total']
print("Type:", field.type)
print("Compute method:", field.compute)
print("Depends fields:", field.depends)
print("Stored in DB:", field.store)
print("Readonly:", field.readonly)

# Inspect selection values or UI attributes
fields_info = env['sale.order'].fields_get(['state', 'partner_id'])
print("State selections:", fields_info['state']['selection'])
```

### B. In-Memory Cache and Recomputation Queue

```python
# 1. Inspect record cache vs hitting PostgreSQL
partner = env['res.partner'].browse(1)
_ = partner.name  # Loads into cache
print("Cached fields:", list(partner._cache.keys()))

# 2. Inspect pending dirty fields and recomputations
print("Dirty fields awaiting DB flush:", env.cache.get_dirty_fields())
print("Pending compute queue:", dict(env.transaction.tocompute))

# 3. Force recomputation of a specific field
partner.modified(['name'])  # Mark dirty
env.flush_all()             # Execute computes and write to DB cursor
env.invalidate_all()        # Clear cache to force clean reload from PostgreSQL
```

### C. Search Domain to SQL Resolution

```python
# Inspect the exact PostgreSQL SQL generated by an ORM search domain
domain = [('state', '=', 'sale'), ('amount_total', '>', 500)]
query = env['sale.order']._search(domain)
print("Generated SQL:", str(query.select()))
```

### D. Security & Record Rule Domain Evaluation

```python
# Diagnose why a specific user cannot see certain records
user = env.ref('base.user_demo')
# Compute active domain generated by ir.rule for this model and user
rule_domain = env['ir.rule'].with_user(user)._compute_domain('res.partner', mode='read')
print("Record rule domain applied to user:", rule_domain)

# Check specific record rule permissions directly
partner = env['res.partner'].browse(1)
try:
    partner.with_user(user).check_access_rule('read')
    print("User HAS read access to record.")
except Exception as e:
    print("Access rule violation:", e)
```

---

## 6. Interactive Testing and Sandbox Verification in Shell

Because `odoo shell` wraps the session in a transaction that automatically calls `cr.rollback()` on exit, it serves as a safe sandbox for testing workflows without polluting production or staging databases.

### A. End-to-End Business Flow Simulation

Simulate full multi-step business lifecycles and verify state assertions safely:

```python
from odoo import Command

# 1. Create temporary records in shell sandbox
partner = env['res.partner'].create({'name': 'Temporary Shell Test Co'})
order = env['sale.order'].create({
    'partner_id': partner.id,
    'order_line': [Command.create({
        'product_id': env.ref('product.product_product_4', raise_if_not_found=False).id or 1,
        'product_uom_qty': 3,
        'price_unit': 100.0,
    })],
})

# 2. Step-by-step state machine testing
assert order.state == 'draft', f"Expected draft, got {order.state}"
order.action_confirm()
assert order.state == 'sale', f"Expected sale, got {order.state}"
assert order.amount_total == 300.0, f"Expected 300.0, got {order.amount_total}"

# 3. Verify downstream side effects (e.g. picking generation)
assert len(order.picking_ids) == 1, "Expected 1 delivery order to be generated"
print("Interactive workflow test PASSED successfully!")
# Exiting without env.cr.commit() leaves ZERO footprint in the database!
```

### B. Exception and Constraint Testing with Savepoints

> [!WARNING]
> When testing that an invalid action raises an exception, **always wrap the test in `with env.cr.savepoint():`**. Without a savepoint, an uncaught PostgreSQL or Python exception will put the entire database cursor into an aborted state (`current transaction is aborted, commands ignored until end of transaction block`), requiring a shell restart.

```python
from odoo.exceptions import ValidationError, UserError

# Test custom Python constraint safely
with env.cr.savepoint():
    try:
        # Invalid partner with negative credit limit
        env['res.partner'].create({'name': 'Invalid Partner', 'credit_limit': -50.0})
        print("FAIL: Expected ValidationError was not raised!")
    except (ValidationError, UserError) as e:
        print("PASS: Caught expected validation error:", str(e))
```

### C. Live N+1 Query Detection via `sql_log_count`

Count the exact number of SQL statements executed during an operation:

```python
# Flush ORM cache to start with a clean baseline
env.invalidate_all()
env.flush_all()

count_start = env.cr.sql_log_count

# Operation being tested for N+1 performance
orders = env['sale.order'].search([], limit=30)
partner_names = [order.partner_id.name for order in orders]

env.flush_all()
total_queries = env.cr.sql_log_count - count_start
print(f"Executed {total_queries} queries for 30 records.")
# If total_queries is close to 30+, partner_id is suffering from N+1 query syndrome!
```

### D. Mocking External Integrations in Shell

Test modules that connect to external APIs (payment gateways, carriers, webhooks) without triggering real network requests:

```python
from unittest.mock import patch

# Mock payment gateway response in shell
with patch('requests.post') as mock_post:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        'status': 'APPROVED',
        'transaction_id': 'tx_sandbox_123',
    }
    # Call your module's payment or API sync method
    # provider = env['payment.provider'].search([], limit=1)
    # result = provider._action_sync()
    print("Mock integration executed safely.")
```

### E. Email & Report Rendering Previews

Verify that QWeb templates and Jinja email templates render without syntax errors before users trigger them in production:

```python
# 1. Preview email template rendering
order = env['sale.order'].search([], limit=1)
template = env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
if template and order:
    subject = template._render_field('subject', [order.id])[order.id]
    body = template._render_field('body_html', [order.id])[order.id]
    print("Rendered Subject:", subject)
    print("Rendered Body Excerpt:", body[:150], "...")

# 2. Test PDF report rendering (catches missing QWeb variables or fonts)
if order:
    report_action = env['ir.actions.report']._render_qweb_pdf('sale.report_saleorder', [order.id])
    print(f"PDF successfully rendered ({len(report_action[0])} bytes).")
```

### F. Relational Integrity Auditing

Audit for orphan records or inconsistent data across foreign keys:

```python
# Check for orphan order lines whose sale_order has been deleted
env.cr.execute("""
    SELECT sol.id, sol.order_id
    FROM sale_order_line sol
    LEFT JOIN sale_order so ON sol.order_id = so.id
    WHERE so.id IS NULL
""")
orphans = env.cr.fetchall()
print(f"Orphan order lines found: {len(orphans)}")
```

---

## 7. SQL Diagnostics and Query Profiling in Shell

Inspect raw PostgreSQL query plans and table stats directly through `env.cr`:

```python
# Execute EXPLAIN ANALYZE on slow query
env.cr.execute("""
    EXPLAIN ANALYZE
    SELECT id, name FROM sale_order
    WHERE state = 'sale' AND company_id = 1
    ORDER BY date_order DESC LIMIT 50;
""")
for row in env.cr.fetchall():
    print(row[0])

# Direct SQL query with dictionary result
env.cr.execute("SELECT id, name, state FROM account_move WHERE state = 'draft' LIMIT 5")
draft_moves = env.cr.dictfetchall()

# IMPORTANT: Invalidate ORM cache after direct SQL write
env.cr.execute("UPDATE res_partner SET active = true WHERE id = 42")
env.invalidate_all()  # Flush ORM cache to reflect raw SQL change
env.cr.commit()
```

---

## 8. Essential Odoo Native CLI Utilities (`odoo/cli/`)

Beyond `shell`, Odoo provides specialized maintenance and compliance CLI commands:

### A. Database Neutralization (`neutralize`)

**MANDATORY** after restoring a production backup onto a staging/testing server. Prevents the test server from sending real emails, processing real credit card charges, or calling external production webhooks.

```bash
# Execute neutralization scripts (runs all addons/*/data/neutralize.sql)
python3 odoo-bin neutralize -d staging_db -c /etc/odoo.conf
```

**What neutralization does automatically:**
- Deactivates all outgoing mail servers (`ir_mail_server`).
- Switches payment providers to test/dummy credentials.
- Disables external scheduled synchronizations (e.g. delivery carriers, banking syncs).
- Sets `database.is_neutralized = True` in `ir.config_parameter`.

---

### B. Database Anonymization (`obfuscate`)

Complies with GDPR and data privacy laws by scrambling personal customer information in test databases while maintaining relational integrity.

```bash
# Scramble customer names, emails, phones, and addresses
python3 odoo-bin obfuscate -d staging_db -c /etc/odoo.conf
```

---

### C. Custom Codebase Auditor (`cloc`)

Counts the exact lines of custom code in your addons (stripping comments, blank lines, and third-party libraries). Used by Odoo Enterprise for maintenance calculation and repository auditing.

```bash
# Count custom code in specific addons folder
python3 odoo-bin cloc --addons=/path/to/custom/addons
```

---

### D. Automated Code Modernization (`upgrade_code`)

Uses Python AST transformations to update deprecated syntax across major Odoo versions (e.g. updating method decorators, migrating deprecated calls).

```bash
python3 odoo-bin upgrade_code --addons=/path/to/custom/addons
```

---

## 9. Native Database CLI Manager (`odoo-bin db`)

Odoo 17, 18, and 19 provide a built-in CLI database manager (`odoo/cli/db.py`) that operates on both the PostgreSQL database **and** the filestore simultaneously. This replaces fragile manual SQL dumps and directory copies.

### A. Duplicate Database (with Filestore & Neutralize)

Quickly clone a production or staging database for local testing without manual file manipulation:

```bash
# Clone source database to target, copy filestore, and neutralize in one command:
python3 odoo-bin db duplicate -c /etc/odoo.conf -n source_db target_db

# Overwrite target database if it already exists (-f / --force):
python3 odoo-bin db duplicate -c /etc/odoo.conf -f -n prod_db dev_test_db
```

### B. Dump and Load (Zip Archive with Filestore)

```bash
# Export complete database + filestore into a single zip archive
python3 odoo-bin db dump -c /etc/odoo.conf my_database /path/to/backup.zip

# Restore from local zip file or URL, automatically neutralizing on restore:
python3 odoo-bin db load -c /etc/odoo.conf -n target_db /path/to/backup.zip

# Restore directly from a remote HTTP/S URL:
python3 odoo-bin db load -c /etc/odoo.conf -n restored_db https://backup-server.internal/nightly.zip
```

### C. Drop Database (with Filestore Cleanup)

```bash
# Safely deletes PostgreSQL database and removes its filestore directory
python3 odoo-bin db drop -c /etc/odoo.conf obsolete_db
```

---

## 10. Rapid Development Flags (`--dev`)

In development, restarting Odoo or updating modules (`-u my_module`) for every XML or Python change slows down iteration. Odoo provides `--dev` flags to enable instant reloading:

| Flag | Behavior |
| :--- | :--- |
| `--dev=xml` | **Reads XML view definitions directly from files on disk** rather than `ir_ui_view.arch_db`. Changing an XML file takes effect immediately upon browser refresh (F5) without running `-u module`! Also bypasses asset and QWeb caches. |
| `--dev=reload` | Watches Python source files using `watchdog` / `pyinotify` and automatically restarts the Odoo process on file save. |
| `--dev=qweb` | Adds node debugging comments and disables QWeb template caching. |
| `--dev=werkzeug` | Activates the interactive in-browser Werkzeug debugger console on unhandled HTTP exceptions. |
| `--dev=all` | Enables `xml`, `reload`, `qweb`, and `werkzeug` simultaneously. |

### Recommended Development Command

```bash
python3 odoo-bin -c /etc/odoo.conf -d my_dev_db --dev=xml,reload --workers=0
```

---

## 11. Interactive Debugging (`breakpoint()` & `pdb`)

When debugging Python code in Odoo using standard Python `breakpoint()`, `import pdb; pdb.set_trace()`, or an IDE debugger (VS Code, Cursor, PyCharm):

### Critical Worker Gotcha (`--workers=0`)

In multi-worker mode (`--workers > 0`), Odoo forks worker processes managed by a master process. If execution pauses at a breakpoint:
1. The master process detects that the worker has stopped answering heartbeats.
2. The worker reaches `limit_time_cpu` or `limit_time_real` timeout.
3. The master process forcibly kills the worker with `SIGKILL` or `SIGALRM`, crashing your debug session.

### Rules for Interactive Breakpoints:

1. **Always set `--workers=0` (threaded mode):**
   ```bash
   python3 odoo-bin -c /etc/odoo.conf -d my_db --workers=0
   ```
2. **Disable time limits so the session doesn't timeout while inspecting variables:**
   ```bash
   python3 odoo-bin -c /etc/odoo.conf -d my_db --workers=0 --limit-time-cpu=0 --limit-time-real=0
   ```
3. **Triggering breakpoint in code:**
```python
def action_confirm(self):
    # Execution will pause here in the console running odoo-bin
    breakpoint()
    res = super().action_confirm()
    return res
```

---

## 12. IDE Frontend Tooling (`odoo-bin tsconfig`)

For modern OWL and JavaScript/TypeScript frontend development in Odoo 17, 18, and 19:

```bash
# Generate tsconfig.json files for all custom addons paths
python3 odoo-bin tsconfig --addons-path=/home/user/odoo/addons,/home/user/custom/addons
```

This generates `tsconfig.json` configurations mapped to the module hierarchy, enabling full IDE autocomplete, type checking, and navigation across custom OWL components in VS Code and Cursor.

---

## 13. Containerized Execution Patterns (Docker / Doodba)

When running Odoo inside Docker or Docker Compose environments:

### Interactive Shell in Container

```bash
# In running container
docker compose exec web odoo-bin shell -d my_db

# One-off disposable container
docker compose run --rm web odoo-bin shell -d my_db
```

### Headless Script Piping in Container

> [!IMPORTANT]
> When piping a script into `docker compose run`, always supply the `-T` flag to disable pseudo-TTY allocation. Without `-T`, Docker may garble the standard input stream.

```bash
# Correct pipe execution into Docker container
docker compose run --rm -T web odoo-bin shell -d my_db --no-http < fix_data.py
```

## Related References

- [Production Deployment & Containers](deployment.md)
- [Structured Logging & Diagnostics](logging.md)
- [Scheduled Actions & Cron](cron.md)
- [Operations Directory Index](README.md)
- [Troubleshooting Test Failures](../testing/troubleshooting.md)
