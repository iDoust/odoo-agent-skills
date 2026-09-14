# Changelog

## Unreleased

### Added

- Universal Odoo Agent Skills for Odoo 17, 18, and 19.
- Development, debugging, review, security, testing, and upgrade workflows.
- Optional Doodba indexing, read-only Odoo querying, and output optimization
  skills.
- Shared ORM, views, OWL, security, performance, migration, integration, and
  module references.
- Community and Enterprise source matrix for supported versions.
- Dependency-free core structure validation.
- Deprecation scanner CLI (`scripts/scan_deprecations.py`) with AST and regex
  analysis for Python and XML files targeting Odoo 17, 18, and 19.
- OCA community standards and `openupgradelib` migration guide
  (`references/operations/oca-guidelines.md`).
- Community Edition solutions for Enterprise features
  (`references/modules/community-enterprise-solutions.md`): Financial Reports,
  Barcode Scanning, Multi-tier Approvals, Digital Signatures, and DMS.
- Cross-references from migration, upgrade, review, and development skills to
  the deprecation scanner, OCA guidelines, and CE solutions guide.
- Comprehensive README with full reference index, project structure, and
  quick-start instructions.
- Dedicated directory index hubs: `references/operations/README.md`,
  `references/integrations/README.md`, and `references/versions/README.md`.
- Complete bidirectional cross-referencing across all operation references,
  integration patterns, and version delta documents.
- Expanded `odoo-development`, `odoo-debug`, `odoo-security`, and `odoo-upgrade`
  skill manifests with complete reference coverage.
- Standardized 3-element user request intake triad (User Problem, Current State/Symptom,
  Expected Result) across development, debugging, and QA references.
- Solution selection decision hierarchy (Configure vs OCA vs Custom Module) in module structure and development workflows.
- Blast radius & inheritance impact analysis gates in development and review skills.
- Production data repair and hotfix scripting protocol (atomic savepoint, notification muting context, reconciliation).
- Pre-delivery multi-context Definition of Done (DoD) verification matrix (role matrix, multi-company, clean upgrade).
- Production Load Balancer and Reverse Proxy architecture guide with Nginx configuration template (sticky session, dual-upstream, health check) in deployment operations.
- Multi-tier caching architecture (browser/assets, ORM cache, method `@tools.ormcache`), multi-worker cache invalidation, and stale cache diagnostics in performance guide.
- Infrastructure failure modes triage (stale cache desync, load balancer session drops, HTTPS redirect loops) in debugging and review skills.
- Asynchronous Job Queues guide (native `ir.cron` vs OCA `queue_job` decision matrix, `@job` decorator, channels, auto-retry with backoff) in cron operations.
- Multi-process worker parallelization sizing formula, memory budgeting rules, and row-level concurrency locking (`FOR UPDATE`) in performance guide.
- Asynchronous offloading rules and concurrency review gates in development and review skills.
- Throughput vs Latency metrics guide, Little's Law capacity planning formula, production latency budgets (p50/p95/p99), and log-based latency analysis in performance and monitoring guides.
- PostgreSQL Connection Pooling (PgBouncer dual-port transaction/session routing) and Read Replica analytical offloading guide in deployment operations.
- Perimeter rate limiting (Nginx `limit_req_zone`) and automated Fail2ban brute-force protection for `/web/login` and public integration endpoints.
- Circuit Breaker fault-tolerance pattern for third-party HTTP integrations (payment, shipping, tax) with asynchronous queue fallback in external API references.
- Stateless cluster architecture guide with distributed object storage (S3 / MinIO via `fs_storage` and presigned URLs) replacing fragile shared NFS.
- Point-in-Time Recovery (PITR) and Disaster Recovery (DR) runbook with continuous WAL archiving (`pgBackRest`), automated restore verification, and RPO < 5m / RTO < 30m targets.
- Zero-downtime rolling upgrade protocol and Contract/Expand (Expand, Backfill, Contract) database schema migration pattern for high-volume tables.
- PostgreSQL Declarative Table Partitioning by date range (`account_move_line`, `stock_move_line`) with partition pruning optimization in performance guide.

### Changed

- Moved reusable Odoo knowledge out of the legacy plugin tree.
- Moved reusable Doodba, query, and token-optimization capabilities into
  universal skills.
- Removed the root `.claude-plugin` marketplace coupling and archived the
  remaining Claude-only wrappers outside the active repository.
- Converted absolute `file:///` links in `references/orm/` to portable
  relative markdown links.
- Expanded module references README to list all 20 domain and pattern files.

### Removed

- Unsupported-only Odoo 14–16 material from universal paths.
- Pairwise version dispatchers and vendor-specific Odoo workflow commands from
  the core.
