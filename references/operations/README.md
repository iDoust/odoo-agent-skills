# Operations and Infrastructure References

Shared guidelines for Odoo operations, server administration, automation,
debugging, production deployment, and community standards.

## Reference Index

| Topic | Reference | Summary |
| :--- | :--- | :--- |
| CLI & Interactive Shell | [cli-and-shell.md](cli-and-shell.md) | CLI commands, `-d`, `-u`, `--dev`, interactive REPL shell |
| Scheduled Actions & Cron | [cron.md](cron.md) | `ir.cron` configuration, queue jobs, concurrency, idempotency |
| Production Deployment | [deployment.md](deployment.md) | Gunicorn/workers, reverse proxy (Nginx), PostgreSQL, Docker |
| Logging & Diagnostics | [logging.md](logging.md) | Logger hierarchy, log levels, formatting, log handlers |
| Email & Mail Routing | [mail.md](mail.md) | SMTP/IMAP, mail templates, mail queues, message routing |
| Monitoring & Health | [monitoring.md](monitoring.md) | Health endpoints, Prometheus/statsd metrics, system profiling |
| OCA & OpenUpgrade | [oca-guidelines.md](oca-guidelines.md) | Community Association conventions, openupgradelib, review standards |

## Related Workflows

- CLI & Shell workflow: [`../../skills/odoo-debug/SKILL.md`](../../skills/odoo-debug/SKILL.md)
- Deployment & CI checks: [`../../skills/odoo-test/SKILL.md`](../../skills/odoo-test/SKILL.md)
- Upgrade & Migration tooling: [`../../skills/odoo-upgrade/SKILL.md`](../../skills/odoo-upgrade/SKILL.md)
