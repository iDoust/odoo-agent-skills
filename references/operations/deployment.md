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

### Pre-Delivery Multi-Context Verification Matrix

Before handing off or deploying any feature or module change, test across the core operational dimensions:

| Dimension | Verification Item | Pass Criteria |
| :--- | :--- | :--- |
| **Role Matrix** | Admin, Standard Internal User, Portal/Public | Admin can configure; Internal User is bounded by ACL/rules; Portal cannot read internal records. |
| **Multi-Company** | Single-Company vs Multi-Company Switcher | Records created in Company A are invisible in Company B unless explicitly shared (`company_id = False`). |
| **Clean Lifecycle** | Clean Install (`-i`) and Safe Upgrade (`-u`) | Zero XML warnings, zero constraint failures on existing data, no orphaned `ir.model.data`. |
| **Blast Radius** | Inherited models (`_inherit`) and child views | No child XPath exceptions; dependent QWeb PDF reports and email templates render cleanly. |

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

## Production Load Balancer and Reverse Proxy Architecture

In production, Odoo must always run behind a reverse proxy / load balancer (such as **Nginx**, **HAProxy**, or an enterprise cloud load balancer like AWS ALB).

### Core Architectural Requirements

1. **`proxy_mode = True` (Mandatory)**:
   In `odoo.conf`, set `proxy_mode = True`. This instructs Werkzeug/Odoo to trust `X-Forwarded-For` (client IP) and `X-Forwarded-Proto` (HTTPS scheme). Without this, redirect loops occur and client IPs appear as `127.0.0.1`.
2. **Dual-Upstream Topology**:
   - **HTTP Worker Pool (Port 8069)**: Standard transactional HTTP/JSON-RPC requests.
   - **Websocket/Longpolling Pool (Port 8072)**: Real-time bus notifications, web chat, and presence.
3. **Session Affinity (Sticky Sessions)**:
   Because Odoo stores sessions in the local filesystem by default (`~/.local/share/Odoo/sessions`), multi-instance deployments must enable **sticky sessions** (e.g. Nginx `ip_hash` or cookie affinity). Otherwise, users will suffer random logouts when requests oscillate between separate servers.
4. **Health Check Probing**:
   Direct load balancer health checks to `GET /web/health`, which returns `200 OK` (HTTP body `{"status": "pass"}`) when database connectivity and worker processes are functional.

### Production Nginx Load Balancer Template

```nginx
# Upstream pool for standard transactional requests
upstream odoo_app {
    ip_hash; # Sticky session: ensures consistent routing to the same application server
    server 10.0.0.10:8069 max_fails=3 fail_timeout=30s;
    server 10.0.0.11:8069 max_fails=3 fail_timeout=30s;
}

# Upstream pool for real-time websocket and live notifications
upstream odoo_chat {
    server 10.0.0.10:8072;
    server 10.0.0.11:8072;
}

# Rate Limiting Zones: protect against brute force and API abuse
limit_req_zone $binary_remote_addr zone=odoo_login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=odoo_api:10m rate=60r/m;
limit_conn_zone $binary_remote_addr zone=odoo_conn:10m;

# HTTP -> HTTPS redirection
server {
    listen 80;
    server_name erp.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS Production Server Block
server {
    listen 443 ssl http2;
    server_name erp.example.com;

    # SSL Certificates & Security Hardening
    ssl_certificate /etc/letsencrypt/live/erp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Performance & Payload Limits
    client_max_body_size 128M;
    proxy_read_timeout 600s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 600s;

    # Buffer settings to prevent disk buffering on large Odoo view payloads
    proxy_buffers 16 64k;
    proxy_buffer_size 128k;

    # Performance logging for Throughput and Latency analysis (rt=$request_time)
    log_format odoo_perf '$remote_addr - $remote_user [$time_local] "$request" '
                         '$status $body_bytes_sent "$http_referer" "$http_user_agent" '
                         'rt=$request_time urt=$upstream_response_time';
    access_log /var/log/nginx/odoo.access.log odoo_perf;

    # Gzip Compression for static web assets
    gzip on;
    gzip_types text/css text/scss text/plain text/xml application/xml application/json application/javascript;

    # Rate-limited Login Endpoint (Stops credential stuffing and brute force)
    location = /web/login {
        limit_req zone=odoo_login burst=5 nodelay;
        limit_conn odoo_conn 10;
        proxy_pass http://odoo_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Rate-limited Public Integration APIs (REST / JSON-RPC / XML-RPC)
    location ~* ^/(jsonrpc|json/2|xmlrpc) {
        limit_req zone=odoo_api burst=20 nodelay;
        proxy_pass http://odoo_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health Check Endpoint (No auth, fast check for Load Balancer)
    location = /web/health {
        proxy_pass http://odoo_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static Assets Caching (High performance, cached in browser)
    location ~* ^/[^/]+/static/ {
        proxy_pass http://odoo_app;
        proxy_cache_valid 200 60m;
        proxy_buffering on;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # Websocket / Livechat / Bus Routing (Odoo 17, 18, 19)
    location ~* ^/(websocket|longpolling) {
        proxy_pass http://odoo_chat;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Main Transactional App Routing
    location / {
        proxy_pass http://odoo_app;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

### Fail2ban Brute-Force Protection

Configure Fail2ban to parse Odoo's application log for failed authentication attempts and block offending IPs automatically:

```ini
# /etc/fail2ban/filter.d/odoo-login.conf
[Definition]
failregex = ^.* \d+ INFO \S+ odoo\.addons\.base\.models\.res_users: Login failed for db:\S+ user:\S+ from <HOST>.*$
ignoreregex =

# /etc/fail2ban/jail.d/odoo.conf
[odoo-login]
enabled = true
port = http,https
filter = odoo-login
logpath = /var/log/odoo/odoo-server.log
maxretry = 5
findtime = 600
bantime = 3600
```

---

## 5. PostgreSQL Connection Pooling (PgBouncer) & Read Replicas

High-concurrency Odoo deployments allocate dozens of workers across multiple nodes. Because each worker thread opens independent PostgreSQL connections, direct database connections quickly exhaust PostgreSQL backend memory and `max_connections` limits.

### PgBouncer Architecture & Odoo Gotcha

- **Transaction Pooling (`pool_mode = transaction`)**:
  Recommended for standard Odoo transactional workers. Connections are assigned per transaction and returned to the pool immediately upon `commit` or `rollback`.
- **The Odoo Gotcha**: Features that rely on session-level PostgreSQL state will fail in transaction pooling:
  - `LISTEN / NOTIFY` (used by Odoo Bus / Livechat and cross-worker `@tools.ormcache` invalidation).
  - PostgreSQL advisory locks and temporary tables.
  - Session parameters like `SET search_path`.
- **Dual-Port Routing Architecture**:
  1. **Port 6432 (PgBouncer Transaction Pool)**: All standard transactional workers connect here (`db_port = 6432` in `odoo.conf`).
  2. **Port 5432 (Direct PostgreSQL)**: Longpolling/websocket workers (`odoo_chat` upstream) connect directly to PostgreSQL to preserve persistent `LISTEN/NOTIFY` channels.

### PgBouncer Production Configuration (`/etc/pgbouncer/pgbouncer.ini`)

```ini
[databases]
odoo_prod = host=127.0.0.1 port=5432 dbname=odoo_prod
odoo_replica = host=10.0.0.20 port=5432 dbname=odoo_prod # Hot Standby Read Replica

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 50
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 5
server_reset_query = DISCARD ALL
server_check_query = SELECT 1
ignore_startup_parameters = extra_float_digits
```

### Read Replica Routing for Analytical Workloads

In high-volume databases, route read-heavy, latency-insensitive queries (e.g. BI dashboards, financial ledger audit exports, or large inventory valuation queries) to a PostgreSQL read replica (Hot Standby) to isolate transactional OLTP tables from analytical read locks:

```python
# Route read-heavy analytics to secondary read replica cursor
replica_cr = self.env.registry.cursor(readonly=True)
try:
    replica_cr.execute("""
        SELECT partner_id, SUM(credit - debit) 
        FROM account_move_line 
        WHERE parent_state = 'posted' 
        GROUP BY partner_id
    """)
    balances = replica_cr.fetchall()
finally:
    replica_cr.close()
```

---

## 6. Distributed Object Storage (S3 / MinIO) for Stateless Application Nodes

Odoo's default filestore stores attachments (invoices, images, documents) on local disk under `~/.local/share/Odoo/filestore/`. In multi-server or containerized deployments, local filestores cause file desynchronization across nodes.

### Why Shared NFS Fails at Scale

- **POSIX File Lock Contention**: Heavy concurrent writes (e.g. bulk PDF generation or catalog imports) trigger file-locking deadlocks over network filesystems.
- **I/O Latency**: NFS metadata lookups create significant disk latency that slows down web asset serving.

### Cloud Object Storage Architecture (S3 / MinIO)

Decouple storage from compute so Odoo application nodes remain completely **stateless**:

1. **Storage Backend**: Use S3 or on-premise MinIO via community modules (e.g., OCA `fs_storage` or cloud attachment adapters).
2. **Environment Configuration**:
   ```bash
   AWS_ACCESS_KEY_ID="prod-storage-key"
   AWS_SECRET_ACCESS_KEY="prod-storage-secret"
   AWS_BUCKET_NAME="company-odoo-filestore"
   AWS_REGION="us-east-1"
   ```
3. **Presigned URLs**: Enable direct client downloads for large files (e.g. export archives, large PDF reports) via presigned S3 URLs, completely offloading file transfer bandwidth from transactional Odoo workers.

---

## 7. Point-in-Time Recovery (PITR) & Disaster Recovery (DR)

Standard daily dumps (`pg_dump`) have a **Recovery Point Objective (RPO) of up to 24 hours**, which is unacceptable for enterprise ERP systems. Implementing continuous WAL archiving achieves an RPO of under 5 minutes.

### RPO and RTO Targets

| Metric | Target SLA | Strategy |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | `< 5 minutes` | Continuous WAL archiving via `pgBackRest` / `WAL-G` |
| **RTO (Recovery Time Objective)** | `< 30 minutes` | Automated basebackup restore + rapid WAL replay |

### WAL Archiving Setup (`pgBackRest`)

Configure continuous PostgreSQL WAL streaming to remote object storage:

```ini
# /etc/pgbackrest/pgbackrest.ini
[global]
repo1-type=s3
repo1-s3-bucket=odoo-db-backups-wal
repo1-s3-endpoint=s3.amazonaws.com
repo1-s3-region=us-east-1
repo1-s3-key=prod-backup-key
repo1-s3-key-secret=prod-backup-secret
repo1-retention-full=4
repo1-retention-diff=14
process-max=4
log-level-console=info

[odoo-prod]
pg1-path=/var/lib/postgresql/16/main
```

### Point-in-Time Recovery (PITR) Execution

In the event of accidental data deletion or corruption:

```bash
# Restore base backup and replay WAL logs to exact minute before the corruption
sudo -u postgres pgbackrest --stanza=odoo-prod \
  --type=time \
  --target="2026-09-14 14:30:00" \
  --target-action=promote \
  restore
```

### Automated Backup Verification Runbook

Never trust unverified backups. Schedule an automated staging verification pipeline:
1. Pull the latest weekly backup dump or pgBackRest snapshot.
2. Spin up a temporary sandbox PostgreSQL instance and restore the database.
3. Run automated integrity assertions (checking row count, schema consistency, balanced ledger entries `debit == credit`).
4. Destroy the sandbox and log verification status to monitoring dashboards.

---

## 8. Zero-Downtime Deployment & Contract/Expand Schema Migrations

Production upgrades on large databases often fail due to exclusive table locks (`ACCESS EXCLUSIVE`) when adding columns or constraints on tables with millions of rows (`account_move_line`, `stock_move_line`).

### Rolling Upgrades with Reverse Proxy

In multi-node architectures behind Nginx:

1. **Drain Node 1**: Mark Node 1 as down in Nginx upstream (`server 10.0.0.10:8069 down;`) and reload Nginx (`systemctl reload nginx`). Active sessions drain to Node 2 via sticky cookies.
2. **Deploy & Upgrade Node 1**: Pull release tag, update modules with `./odoo-bin -d odoo_prod -u target_module --stop-after-init`.
3. **Verify Node 1**: Run automated health check `curl -f http://10.0.0.10:8069/web/health`.
4. **Re-enable Node 1**: Remove `down` flag in Nginx, reload Nginx.
5. **Repeat for Node 2**: Drain, update, verify, and restore Node 2.

### Contract/Expand (Phase Migration) Pattern for Large Tables

When introducing new required columns or major schema transformations without downtime:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Phase 1: EXPAND│  ──►  │ Phase 2: BACKFILL│ ──►  │ Phase 3: CONTRACT│
│ Add nullable col│       │ Background jobs │       │ Add NOT NULL,   │
│ Dual-write in app       │ fill historical │       │ switch reads,   │
└─────────────────┘       └─────────────────┘       │ drop old column │
                                                    └─────────────────┘
```

1. **Phase 1 (Expand - Release N)**:
   - Add new column as *nullable* without default values:
     ```python
     new_tracking_code = fields.Char(string="Tracking Code", index=False)
     ```
   - Application code writes to *both* old and new fields, but reads from the old field.
2. **Phase 2 (Backfill - Asynchronous Batch)**:
   - Run an asynchronous job (`queue_job` or CLI script) to populate `new_tracking_code` in batches of 5,000 records with commits, avoiding table locks.
3. **Phase 3 (Contract - Release N+1)**:
   - Switch application code to read from `new_tracking_code`.
   - Apply index concurrently via SQL:
     ```sql
     CREATE INDEX CONCURRENTLY idx_stock_move_line_tracking ON stock_move_line (new_tracking_code);
     ```
   - Mark old column as deprecated or drop it in a subsequent maintenance release.

---

## Related References

- [Post-Deployment Monitoring & Hypercare](monitoring.md)
- [CLI & Shell Operations](cli-and-shell.md)
- [Logging & Error Diagnosis](logging.md)
- [Operations Directory Index](README.md)
- [Testing & QA Protocols](../testing/qa-plan.md)

## Sources

- Odoo deployment: https://www.odoo.com/documentation/18.0/administration/on_premise.html
- Odoo CLI reference: https://www.odoo.com/documentation/18.0/developer/reference/cli.html
