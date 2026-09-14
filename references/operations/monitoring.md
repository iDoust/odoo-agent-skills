# Post-Deployment Monitoring and Hypercare

Reference for monitoring an Odoo instance after deployment, defining hypercare
periods, and establishing closure criteria.

## Post-Deployment Monitoring Checklist

Monitor these areas continuously during the hypercare period. Any failure
triggers immediate investigation.

### Server Health

```text
✓ Odoo service running (systemctl status odoo)
✓ No OOM kills or service restarts in system log
✓ CPU usage within baseline (compare to pre-deployment)
✓ Memory usage within baseline
✓ Disk space sufficient (especially /var/log, database storage)
✓ No zombie worker processes
```

### Throughput and Latency SLAs

```text
✓ Interactive UI request latency within SLA (p50 < 150ms, p95 < 500ms, p99 < 2000ms)
✓ Application throughput stable without worker starvation (RPS matches peak traffic baseline)
✓ Zero HTTP 502 Bad Gateway or 504 Gateway Timeout bursts at reverse proxy
✓ Background asynchronous jobs processing latency < 60s from enqueue (queue_job / mail queue)
✓ PostgreSQL transaction throughput and buffer cache hit ratio > 98%
```

### Application Errors

```text
✓ No 500 errors in Odoo log (grep for "Internal Server Error")
✓ No unhandled exceptions in odoo.log
✓ No RPC errors in browser console
✓ No XML/QWeb template rendering errors
✓ No missing view/action errors
✓ No "registry reload" loops
```

### Cron and Background Jobs

```text
✓ All scheduled actions executing on schedule (ir.cron)
✓ No failed cron executions (check ir.cron last_call vs interval)
✓ Queue jobs processing (if queue_job module installed)
✓ Mail queue processing (mail.mail outgoing)
✓ No stuck cron locks (check pg_stat_activity for long-running cron)
```

### Database Health

```text
✓ No long-running queries (> 30s in pg_stat_activity)
✓ No lock contention (pg_locks with granted = false)
✓ No bloated tables (pg_stat_user_tables dead tuple ratio)
✓ Transaction ID wraparound headroom sufficient
✓ Connection pool not exhausted
✓ No "could not serialize access" errors
```

### Integration Endpoints

```text
✓ External API endpoints responding (XML-RPC, JSON-RPC)
✓ Payment provider callbacks working
✓ EDI/e-invoicing connections active
✓ Email server (SMTP/IMAP) connected
✓ File storage (S3, local) accessible
```

### Business Transaction Integrity

```text
✓ No unbalanced journal entries (SELECT id FROM account_move
    WHERE state = 'posted' AND ... debit != credit)
✓ No orphaned stock moves (stock.move without picking or production)
✓ No duplicate sequences (ir.sequence gaps or collisions)
✓ No missing tax lines on invoices
✓ No reconciliation anomalies
```

### User-Reported Issues

```text
✓ Helpdesk/support channel monitored
✓ Key user feedback collected
✓ No reports of data loss or corruption
✓ No reports of missing records or broken views
✓ No reports of performance degradation
```

## Monitoring Queries

Quick diagnostic queries for PostgreSQL:

```sql
-- Active long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration,
       query, state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds'
  AND state != 'idle'
ORDER BY duration DESC;

-- Lock contention
SELECT blocked.pid AS blocked_pid,
       blocked.query AS blocked_query,
       blocking.pid AS blocking_pid,
       blocking.query AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_stat_activity blocked ON blocked.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Unbalanced posted journal entries (critical financial integrity check)
SELECT am.id, am.name, am.date,
       SUM(aml.debit) AS total_debit,
       SUM(aml.credit) AS total_credit,
       SUM(aml.debit) - SUM(aml.credit) AS imbalance
FROM account_move am
JOIN account_move_line aml ON aml.move_id = am.id
WHERE am.state = 'posted'
GROUP BY am.id, am.name, am.date
HAVING ABS(SUM(aml.debit) - SUM(aml.credit)) > 0.01
ORDER BY am.date DESC;

-- Failed cron jobs (last execution older than 2x interval)
SELECT name, model_id, interval_number, interval_type,
       lastcall, nextcall,
       CASE WHEN nextcall < now() - interval '1 hour'
            THEN 'OVERDUE' ELSE 'OK' END AS status
FROM ir_cron
WHERE active = true
ORDER BY nextcall;

-- Database transaction throughput and buffer cache hit ratio (should be > 98%)
SELECT datname,
       xact_commit,
       xact_rollback,
       blks_read,
       blks_hit,
       ROUND(blks_hit * 100.0 / NULLIF(blks_hit + blks_read, 0), 2) AS buffer_cache_hit_pct
FROM pg_stat_database
WHERE datname = current_database();
```

### HTTP Latency & Throughput Diagnostics

Extract latency percentiles (`p50`, `p95`, `p99`) and throughput from Nginx access logs:

```bash
# Calculate request latency percentiles from Nginx access log (last field $request_time)
awk '($9 ~ /200/) {print $NF}' /var/log/nginx/odoo.access.log | sort -n | \
  awk '{all[NR] = $0} END {print "Total Requests:", NR, "| p50:", all[int(NR*0.5)], "s | p95:", all[int(NR*0.95)], "s | p99:", all[int(NR*0.99)], "s"}'
```

## Hypercare Definition

Hypercare is the stabilization period immediately after production deployment.
During this period, the development team provides elevated support and
monitoring.

### Duration

| Risk Level | Duration | Criteria |
| --- | --- | --- |
| Low (cosmetic, view changes) | 1 business day | No new models, no accounting impact |
| Medium (new features, workflows) | 2–3 business days | New models or workflows, no financial changes |
| High (accounting, integrations, migration) | 3–5 business days | Financial impact, external integrations, data migration |
| Critical (major version upgrade) | 5–10 business days | Full version upgrade, database migration |

### Escalation Procedure

```text
Level 1 (Immediate, < 30 min):
  - Service down / application unreachable
  - Data loss or corruption detected
  - Unbalanced financial entries in production
  - Security breach or unauthorized access
  → Action: Rollback immediately, notify all stakeholders

Level 2 (Urgent, < 2 hours):
  - Critical business flow broken (cannot create SO/PO/invoice)
  - Cron jobs failing repeatedly
  - Integration endpoints down
  → Action: Hotfix deployment, temporary workaround if available

Level 3 (High, < 1 business day):
  - Non-critical flow broken (report formatting, minor UI issue)
  - Performance degradation but system usable
  - Single user affected
  → Action: Schedule fix in next maintenance window

Level 4 (Normal, < 3 business days):
  - Cosmetic issues
  - Enhancement requests discovered during hypercare
  - Documentation updates needed
  → Action: Log ticket for next sprint/release
```

### Exit Criteria

Hypercare ends when ALL of the following are true:

```text
✓ No Level 1 or Level 2 incidents in the last 24 hours
✓ All critical business flows verified stable
✓ Cron jobs executing on schedule for full hypercare duration
✓ No unbalanced journal entries created since deployment
✓ No user-reported data issues unresolved
✓ Performance metrics and latency SLAs respected (p50 < 150ms, p95 < 500ms, no 502/504 spikes)
✓ Key users confirm system is usable
✓ Client/PM formally approves exit from hypercare
```

## Closure Checklist

After hypercare, close the deployment formally:

### Documentation

```text
✓ Release note published and archived
✓ User guide updated (if UI changed)
✓ Technical documentation updated (if API or data model changed)
✓ Known issues documented with workarounds
✓ Configuration changes recorded in system documentation
```

### Ticket Management

```text
✓ Feature ticket status → DONE / CLOSED
✓ All sub-tasks closed
✓ UAT sign-off attached to ticket
✓ Deployment evidence attached (release tag, deployment log)
✓ Hypercare summary attached (incidents, resolution, final status)
```

### Lessons Learned

```text
✓ What went well in this deployment?
✓ What issues were encountered?
✓ What should be improved for next deployment?
✓ Any process changes needed?
```

## Related References

- [Production Deployment & Environment Setup](deployment.md)
- [Logging & Error Diagnosis](logging.md)
- [Performance & Profiling Guide](../performance/guide.md)
- [Operations Directory Index](README.md)

## Sources

- Odoo server administration: https://www.odoo.com/documentation/18.0/administration/on_premise.html
- PostgreSQL monitoring: https://www.postgresql.org/docs/current/monitoring-stats.html
