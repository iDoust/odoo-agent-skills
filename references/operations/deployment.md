# Deployment, Release, and Production Readiness

Reference for deployment planning, pre-production validation, production gates,
release management, and smoke testing of Odoo modules.

## Definition of Done (Development)

A feature is not development-complete until every applicable item passes.

### General Development DoD

```text
✓ Requirement implemented per acceptance criteria
✓ No syntax or runtime errors
✓ Existing flows not broken (regression verified)
✓ Access rights tested (allowed and denied)
✓ Input validation tested
✓ Error handling present (UserError with clear messages)
✓ Unit/self test completed and passing
✓ Module install tested (clean database)
✓ Module upgrade tested (existing database with data)
✓ Code committed to feature branch
✓ PR created with description
✓ Code review passed
```

### Odoo-Specific DoD

```text
✓ odoo-bin -i {module} --stop-after-init succeeds (clean install)
✓ odoo-bin -u {module} --stop-after-init succeeds (upgrade)
✓ CRUD operations verified (create, read, write, unlink/archive)
✓ ir.model.access.csv covers all new models
✓ Record rules present for multi-company models
✓ check_company=True on cross-company relational fields
✓ Sequence generation verified (ir.sequence)
✓ Chatter/mail.thread tracking verified if applicable
✓ Cron jobs tested if applicable
✓ Email notifications tested if applicable
✓ Accounting impact verified (debit == credit on generated moves)
✓ Inventory impact verified (stock moves and valuation)
✓ Onchange/compute fields produce correct values
✓ Stored computed fields invalidate correctly
✓ SQL and Python constraints enforced
✓ Duplicate prevention tested (copy method, unique constraints)
✓ Concurrency safe if applicable (savepoint, for_update)
✓ No print() or pdb/debugger statements in committed code
✓ No hardcoded credentials, tokens, or passwords
✓ No temporary test scripts committed
✓ No TODO/FIXME without a linked ticket
```

## Code Hygiene Gate

Before code review, verify automatically or manually:

```text
✓ No print(), pdb.set_trace(), debugger, breakpoint() in Python
✓ No console.log() in production JavaScript/OWL
✓ No hardcoded passwords, API keys, or tokens
✓ No commented-out code blocks (dead code)
✓ No temporary test data in XML data files
✓ Logging uses _logger (import logging; _logger = logging.getLogger(__name__))
✓ All new strings use _() for translation
✓ No raw SQL on financial tables (account_move, account_move_line)
```

### Automated Quality Gate (OCA Standard)

Automate the code hygiene checks above using OCA tools in CI or pre-commit:

```bash
# pylint-odoo catches Odoo-specific issues
pylint --load-plugins=pylint_odoo --disable=C,R addons/my_module/

# Key pylint-odoo rules enforced:
#   sql-injection          — no string-formatted SQL
#   manifest-required-key  — complete __manifest__.py
#   translation-required   — _() on user-facing strings
#   method-required-super  — super() on create/write/unlink
#   resource-not-exist     — valid XML ID references
#   manifest-version-format — correct version pattern
```

For continuous enforcement, add a `.pre-commit-config.yaml` to the project:

```yaml
repos:
  - repo: https://github.com/OCA/pylint-odoo
    rev: v9.1.2
    hooks:
      - id: pylint_odoo
        args: ["--disable=C,R"]
  - repo: https://github.com/OCA/odoo-pre-commit-hooks
    rev: v0.0.32
    hooks:
      - id: oca-checks-odoo-module
      - id: oca-checks-po
```

Sources: [OCA pylint-odoo](https://github.com/OCA/pylint-odoo),
[OCA pre-commit hooks](https://github.com/OCA/odoo-pre-commit-hooks)

## Pre-Production Checklist

Before deploying to staging or production:

### Module Readiness

```text
✓ __manifest__.py version matches release (e.g., 18.0.1.2.0)
✓ All module dependencies listed and available on target
✓ Module install order determined (dependencies first)
✓ No missing XML IDs referenced across modules
✓ Demo data excluded from production install (demo=False or separate file)
```

### Migration Script Readiness

```text
✓ Pre-migration scripts are idempotent (safe to rerun)
✓ Post-migration scripts are idempotent
✓ Data migration tested on a copy of production data
✓ No destructive queries (DROP, DELETE, TRUNCATE) without backup
✓ Column renames handled (not drop + create)
✓ XML ID renames use noupdate preservation
```

### Configuration Changes

```text
✓ New system parameters documented
✓ New ir.config_parameter values listed
✓ New groups/roles documented with assignment instructions
✓ New scheduled actions listed with expected intervals
✓ Email template changes documented
✓ New sequences documented
```

## Production Ready Gate

This is the final gate before production deployment. Every section must pass.

### Functional Gate

```text
✓ All acceptance criteria verified (QA + UAT)
✓ QA test plan executed — all critical/major passed
✓ UAT scenarios executed — client sign-off obtained
✓ No open critical or major bugs
✓ Regression tests passed
```

### Technical Gate

```text
✓ Code review passed (ORM, security, performance, accounting integrity)
✓ No debug/temporary code
✓ No hardcoded credentials
✓ Module installs cleanly on empty database
✓ Module upgrades cleanly on production-like data
✓ All dependencies resolved and version-pinned
✓ Performance acceptable on production-scale data
```

### Database Gate

```text
✓ Full database backup taken and verified (can be restored)
✓ Migration scripts tested on production data copy
✓ No data-destructive operations without verified backup
✓ Index changes validated on production-scale data
✓ Disk space sufficient for backup + upgrade operations
```

### Deployment Gate

```text
✓ Deployment steps documented in release note
✓ Module update order specified
✓ Configuration changes documented and ready
✓ Environment variables verified on target server
✓ Maintenance window scheduled and communicated
✓ Stakeholders notified of deployment window
```

### Rollback Gate

```text
✓ Database backup available and verified restorable
✓ Previous version/tag identified and available
✓ Rollback procedure documented and tested
✓ Rollback time estimate known
✓ Rollback decision criteria defined (what triggers rollback)
```

## Release Management

### Branch Strategy for Odoo

```text
feature/{ticket-id}-{short-desc}
    ↓ PR + code review
develop
    ↓ QA / SIT
staging
    ↓ UAT + sign-off
release/{version}
    ↓ merge
main (production)
```

### Release Tagging Convention

```text
v{odoo_major}.0.{YYYY}.{MM}.{DD}.{seq}
```

Examples:

```text
v18.0.2026.09.11.01    # First release on 2026-09-11 for Odoo 18
v18.0.2026.09.11.02    # Hotfix same day
v17.0.2026.09.15.01    # Release for Odoo 17
```

### Release Note Template

```text
Release: v{version}
Date: {YYYY-MM-DD}
Environment: {production / staging}
Deployed by: {name}

## Changes
- [{ticket-id}] {description}

## Modules Updated
- {module_name} ({old_version} → {new_version})

## Configuration Changes
- {parameter}: {old_value} → {new_value}

## Migration Notes
- {any special migration steps}

## Known Issues
- {any known limitations}

## Rollback
- Restore database backup: {backup_name}
- Revert to tag: {previous_tag}
```

## Deployment Steps

Standard Odoo production deployment sequence:

```bash
# 1. Backup
pg_dump -Fc {database} > backup_{database}_{date}.dump

# 2. Verify backup is restorable
pg_restore --list backup_{database}_{date}.dump > /dev/null

# 3. Stop Odoo service
sudo systemctl stop odoo

# 4. Update code
cd /path/to/addons
git fetch origin
git checkout {release_tag}

# 5. Update modules
./odoo-bin -d {database} -u {module1},{module2} --stop-after-init

# 6. Start Odoo service
sudo systemctl start odoo

# 7. Verify service is running
sudo systemctl status odoo
curl -s http://localhost:8069/web/login | head -1
```

### Module Update Order

When updating multiple modules, respect dependency order:

```text
1. Base/framework modules first (if changed)
2. Core business modules (account, sale, purchase, stock)
3. Bridge modules (sale_stock, purchase_stock, sale_purchase)
4. Custom modules in dependency order
5. Cosmetic/view-only modules last
```

## Smoke Test Checklist

Execute immediately after production deployment:

### Automated Smoke Testing (`scripts/smoke_test.py`)

Run the automated smoke test script immediately after service restart to verify HTTP availability, XML-RPC authentication, module states, and cron health:

```bash
# Run automated post-deploy smoke test
python3 scripts/smoke_test.py \
    --url http://localhost:8069 \
    --db my_prod_db \
    --login admin \
    --password secret \
    --modules my_module,my_extension_module
```

Exit code `0` indicates all health checks passed. Exit code `1` triggers immediate investigation or rollback.

### Critical Path Verification (Manual)

```text
✓ Login as admin — success
✓ Login as regular user — success
✓ Main menu loads — all expected menu items visible
✓ Updated module's primary list view loads — no error
✓ Updated module's primary form view loads — no error
✓ Create a test record in the updated module — success
✓ Edit the test record — success
✓ Delete/archive the test record — success (if permitted)
```

### Business Flow Verification

```text
✓ Sales: Create SO → Confirm → Delivery created (if sale_stock)
✓ Purchase: Create PO → Confirm → Receipt created (if purchase_stock)
✓ Accounting: Create invoice → Post → Verify debit == credit
✓ Inventory: Create transfer → Validate → Stock moves created
```

### Infrastructure Verification

```text
✓ Scheduled actions (cron) — no failed executions in ir.cron log
✓ Email sending — test email dispatched successfully
✓ File attachments — upload and download work
✓ Reports — PDF generation works (QWeb reports)
✓ API endpoints — external integrations respond
✓ Longpolling/websocket — real-time notifications work
```

### Performance Verification

```text
✓ Page load time acceptable (< 3s for main views)
✓ No slow queries in PostgreSQL log (> 1s)
✓ No memory spikes in server process
✓ CPU usage within normal range
```

## Related References

- [Post-Deployment Monitoring & Hypercare](monitoring.md)
- [CLI & Shell Operations](cli-and-shell.md)
- [Logging & Error Diagnosis](logging.md)
- [Operations Directory Index](README.md)
- [Testing & QA Protocols](../testing/qa-plan.md)

## Sources

- Odoo deployment: https://www.odoo.com/documentation/18.0/administration/on_premise.html
- Odoo CLI reference: https://www.odoo.com/documentation/18.0/developer/reference/cli.html
