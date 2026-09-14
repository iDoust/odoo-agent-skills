# Odoo Performance and Large Dataset Benchmarking Guide

Comprehensive guide for profiling, optimizing, and stress-testing Odoo models across **Odoo 17, 18, and 19**.

---

## 1. Performance Optimization Principles

1. **Batching over Iteration:** Always prefer multi-record operations (`records.write()`, `records.action_confirm()`) over iterating in Python loops.
2. **Eliminate N+1 Queries:** Use relational fields and prefetching. Do not query inside loops:

```python
# Bad: Triggers 1 search per line (N+1 queries)
for line in order.order_line:
    price = self.env['product.pricelist'].search([('product_id', '=', line.product_id.id)]).price

# Good: Single batch read using ORM prefetching
prices = order.order_line.product_id.mapped('lst_price')
```

3. **Targeted SQL Indexes:** Add indexes on fields frequently used in search domains, foreign keys, or group-by filters:
   - `index=True` or `index='btree'` (Odoo 17/18/19).
4. **Cache Invalidation Discipline:** When modifying the database with raw SQL (`cr.execute()`), always invalidate the ORM cache explicitly to avoid stale reads:

```python
self.env.invalidate_all()
```

5. **ORM Method Caching (`@tools.ormcache` & `@tools.ormcache_context`):**
   For expensive compute-heavy methods or static configuration calculations that do not change frequently:

```python
from odoo import models, api, tools


class CustomConfig(models.Model):
    _name = 'custom.config'

    # Cache based on method arguments
    @tools.ormcache('key', 'category')
    def _get_setting_cached(self, key, category='general'):
        record = self.search([('key', '=', key), ('category', '=', category)], limit=1)
        return record.value if record else False

    # Cache sensitive to context keys (e.g., lang, timezone)
    @tools.ormcache_context('self.id', keys=('lang', 'tz'))
    def _get_localized_summary(self):
        self.ensure_one()
        return f"{self.name} - {self.description}"

    # Invalidation: Clear cache when records are written or deleted
    def write(self, vals):
        res = super().write(vals)
        self.clear_caches()  # Clears all ormcache entries for this registry
        return res

    def unlink(self):
        res = super().unlink()
        self.clear_caches()
        return res
```

> [!CAUTION]
> **Never return a Recordset from an `@ormcache` method!**
> Recordsets are bound to the database cursor (`cr`). Returning a recordset from cache after the transaction completes causes `psycopg2.InterfaceError: cursor already closed`. Always return primitives, IDs (`record.id`), dictionaries, or lists.

6. **Multi-Tier Caching Architecture:**
   - **Tier 1: Browser & CDN / Reverse Proxy Cache**:
     Static web assets under `/[module]/static/` (CSS, JS, images) are served with far-future expiration headers (`expires 7d; Cache-Control: public`). Cache busting is achieved via checksum hashes appended to asset bundles (e.g., `web.assets_backend.min.js?v=hash`).
   - **Tier 2: Transaction-Level ORM Cache (`env.cache`)**:
     Field values fetched during an active transaction are kept in memory on `env.cache`. Subsequent accesses within the same transaction are resolved from memory without hitting PostgreSQL. Modifications via ORM automatically invalidate dirty fields; raw SQL requires `self.env.invalidate_all()`.
   - **Tier 3: Registry-Level Method Cache (`@tools.ormcache`)**:
     Cross-request in-memory LRU cache tied to the model registry. In multi-worker environments, when one worker calls `self.clear_caches()`, Odoo broadcasts an invalidation signal via PostgreSQL `LISTEN/NOTIFY` on the `im_livechat` / registry channel so sibling workers clear their local memory cache.

7. **Stale Cache Diagnostics Checklist**:
   - If data modified via SQL or background jobs doesn't appear in the UI: check if `env.invalidate_all()` or `self.clear_caches()` was omitted.
   - In multi-server / multi-worker setups: ensure PostgreSQL signaling connections are active, or restart the application workers to force cache clearing.

8. **Multi-Process Worker Parallelization & Concurrency**:
   - **Worker Sizing Formula**:
     $$\text{Workers} = (\text{CPU Cores} \times 2) + 1$$
     Example: An 8-core CPU server should allocate `workers = 17` plus dedicated `max_cron_threads = 2`.
   - **Memory Budgeting Rules**:
     - `limit_memory_soft = workers * 1073741824` (1 GB per worker).
     - `limit_memory_hard = workers * 1342177280` (1.25 GB per worker).
     Odoo worker recycling automatically terminates processes that exceed limits after serving their current request.
   - **Row-Level Locking in Concurrent Parallel Workers**:
     When multiple workers execute transactions on related records simultaneously:
     ```python
     # Lock records explicitly to serialize access and prevent race conditions
     self.env.cr.execute("SELECT id FROM my_stock_pool WHERE id = %s FOR UPDATE NOWAIT", [pool_id])
     ```
     Use `SKIP LOCKED` when multiple parallel workers pull items from an internal queue table without contention.
   - **Asynchronous Offloading Rule**:
     Never execute blocking third-party API requests (>2s) or large batch mutations synchronously inside transactional HTTP workers. Offload to background queues (`queue_job` or `ir.cron`).

9. **Throughput vs Latency: Metrics, Budgets, and Capacity Planning**:
   - **Definitions**:
     - **Latency ($L$)**: Duration required to process and respond to an individual client request (e.g. loading a form, confirming an order). Evaluated by percentiles:
       - **p50 (Median)**: Representative interactive experience for 50% of requests.
       - **p95**: Tail latency under typical load; reveals slow queries and missing indexes.
       - **p99**: Extreme tail; catches transaction lock contention and unbounded compute loops.
     - **Throughput ($X$)**: The aggregate rate of completed requests per second (RPS) or completed business transactions per unit time (TPS: orders confirmed/sec, invoice lines generated/sec).
   - **Little's Law for Odoo Worker Sizing & Capacity**:
     $$\text{Throughput (RPS)} = \frac{\text{Concurrency (Active Workers)}}{\text{Average Latency (Seconds)}} \quad \left(X = \frac{W}{L}\right)$$
     - **Capacity Multiplier**: A cluster with $W = 16$ HTTP workers handling requests at an average latency of $L = 1.0\text{ s}$ has a hard capacity ceiling of $16\text{ RPS}$. If query optimization, ORM prefetching, and `@tools.ormcache` reduce average latency to $L = 0.1\text{ s}$ ($100\text{ ms}$), throughput capacity scales to $160\text{ RPS}$ ($10\times$) on the exact same server hardware.
     - **Worker Starvation Cascade**: When a slow computation spikes request latency from $200\text{ ms}$ to $2\text{ s}$, capacity drops by $90\%$. Incoming requests queue in Nginx buffers until worker pools exhaust, triggering HTTP 502 Bad Gateway or 504 Gateway Timeout errors.
   - **Odoo Production Latency Budget Table**:

     | Metric / Transaction Tier | Target SLA | Budget Ceiling | Degraded Action |
     | :--- | :--- | :--- | :--- |
     | **p50 (Median Interactive Reads)** | `< 150 ms` | `300 ms` | Verify browser asset caching, CDN, and ORM prefetching |
     | **p95 (Search & Record Writes)** | `< 500 ms` | `1,000 ms` | Profile SQL with `debug=1`; add indexes on search/group-by fields |
     | **p99 (Complex Multi-Line Computations)** | `< 2,000 ms` | `3,000 ms` | Eliminate Python loops over recordsets; use SQL batching or `mapped()` |
     | **Asynchronous Threshold** | `> 2,000 ms` | Sync Timeout | **Mandatory offload**: move to `queue_job` or `ir.cron`; never block HTTP workers |

   - **Performance Tuning Playbook**:
     - **To Reduce Latency**: Minimize database roundtrips with batch ORM queries, add targeted PostgreSQL B-tree indexes, eliminate N+1 loops, and memoize invariant computations using `@tools.ormcache`.
     - **To Scale Throughput**: Optimize latency first (via Little's Law), scale multi-process workers up to $(2 \times \text{CPUs}) + 1$, route sticky sessions across multiple application servers via Nginx load balancers, and isolate non-interactive work to asynchronous job queues (`queue_job`).

10. **Declarative Table Partitioning for High-Volume Historical Ledgers**:
    - **The Challenge**: Core ledger tables (`account_move_line`, `stock_move_line`, `mail_message`) can exceed 10–50 million records in enterprise environments. When table and B-tree index footprints surpass PostgreSQL `shared_buffers` RAM, disk thrashing slows down standard CRUD operations.
    - **PostgreSQL Range Partitioning Strategy**:
      Partition large ledger models by `RANGE (date)` into yearly child tables:
      ```sql
      -- Create partitioned parent table structure
      CREATE TABLE account_move_line_partitioned (
          LIKE account_move_line INCLUDING DEFAULTS INCLUDING CONSTRAINTS
      ) PARTITION BY RANGE (date);

      -- Define yearly partition child tables
      CREATE TABLE account_move_line_2024 PARTITION OF account_move_line_partitioned
          FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

      CREATE TABLE account_move_line_2025 PARTITION OF account_move_line_partitioned
          FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

      CREATE TABLE account_move_line_2026 PARTITION OF account_move_line_partitioned
          FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
      ```
    - **Partition Pruning Performance Gains**:
      When an Odoo search domain includes date filters (`[('date', '>=', '2026-01-01'), ('date', '<=', '2026-12-31')]`), the PostgreSQL query planner executes **partition pruning**, scanning solely `account_move_line_2026` and skipping all historical years. This eliminates up to 90% of disk I/O.
    - **Operational Advantages**:
      - **RAM Efficiency**: B-tree indexes for the current active fiscal year stay resident in RAM.
      - **Zero-Downtime Archiving**: Historical partitions older than compliance requirements can be detached (`ALTER TABLE ... DETACH PARTITION`) or compressed into cold tablespaces without acquiring exclusive locks on active operational data.
      - **Isolated Maintenance**: Autovacuum workers operate per partition, preventing vacuum starvation on massive monolithic tables.

---

## 2. Native Large Dataset Generation (`populate` Framework)

Odoo includes a built-in data generation framework to populate databases with realistic, high-volume datasets for load and stress testing prior to production deployment.

### How `populate` Works Across Versions:
- **Odoo 17:** Driven by `_populate_factories(self)` and generator functions (`populate.iterate`, `populate.randomize`).
- **Odoo 18 & 19:** Enhanced in `odoo/tools/populate.py` with database-level SQL duplication, automatic index dropping/restoring during insertion, sequence adjustment, and date series distribution.

### Running Populate from CLI

Generate test datasets directly on a dedicated staging database:

```bash
# Populate medium dataset for sales and partners
odoo-bin -c /etc/odoo.conf -d test_perf_db --populate --models=res.partner,sale.order --size=medium --stop-after-init

# Available size flags:
# --size=small   (hundreds of records)
# --size=medium  (thousands of records)
# --size=large   (tens/hundreds of thousands of records)
```

### Implementing `_populate_factories` on Custom Models

Define data generation rules for custom models to participate in `--populate`:

```python
from odoo import models
from odoo.tools import populate


class MyModel(models.Model):
    _inherit = 'my.model'

    def _populate_factories(self):
        """Define field value generators for populate."""
        return [
            ('name', populate.iterate('TEST_REC_%d', range(1, 10000))),
            ('priority', populate.randomize(['normal', 'urgent', 'critical'], [0.7, 0.2, 0.1])),
            ('partner_id', populate.randomize(self.env['res.partner'].search([]).ids)),
            ('amount', populate.randint(10, 5000)),
        ]

    def _populate_sizes(self):
        """Define record count per size scale."""
        return {
            'small': 100,
            'medium': 2500,
            'large': 50000,
        }
```

---

## 3. Measuring Performance in Tests

### A. Strict Query Budgeting (`assertQueryCount`)

Ensure methods do not exceed their budgeted SQL query count as datasets grow:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPerformanceBudgets(TransactionCase):

    def test_batch_invoice_query_scaling(self):
        """Verify processing 100 lines executes in bounded SQL queries (O(1), not O(N))."""
        # Warm up ORM cache
        self.env['account.move'].search([], limit=1)._compute_amount()

        # Processing must remain within the fixed query limit regardless of line count
        with self.assertQueryCount(5):
            self.move._compute_amount()
```

### B. Profiling Test Execution (`self.profile`)

Profile execution time and SQL bottlenecks inside test cases:

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProfilingExecution(TransactionCase):

    def test_recompute_speed(self):
        """Profile heavy batch operation."""
        with self.profile(description="Batch confirm 500 orders"):
            self.orders.action_confirm()
```

### C. Code Profiling and Flamegraphs (`odoo.tools.profiler.Profiler`)

Odoo includes a built-in profiler that captures SQL queries, execution durations, and Python call stacks, formatted for visualization in [Speedscope](https://www.speedscope.app):

```python
from odoo.tools.profiler import Profiler

# 1. Profile an operation in code and print summary
with Profiler(collectors=['sql', 'periodic'], description="Confirm Batch Orders") as profiler:
    orders.action_confirm()

# Print console summary (durations, query counts, and slow lines)
print(profiler.summary())

# 2. Export flamegraph JSON for visual inspection in Speedscope
with open("/tmp/profiler_flamegraph.json", "w") as f:
    f.write(profiler.json())
```

### D. UI Profiler in Developer Mode (`?debug=1`)

In Odoo 17, 18, and 19, developers can profile web requests directly from the browser:
1. Activate Developer Mode (`?debug=1`).
2. Click the bug icon in the top navbar and toggle **Start Profiling**.
3. Perform the slow user action (e.g. loading a large list view or opening a form).
4. Stop profiling to view the execution plan, total query count, and download the Speedscope flamegraph.

---

## 4. Production Performance Checklist

```text
✓ No N+1 query patterns in compute methods or loops
✓ Foreign keys used in frequent search domains have index=True
✓ Stored computed fields have minimal, precise @api.depends triggers
✓ Cron jobs process records in batches (e.g. limit=500 per run with commit)
✓ Heavy reports execute within 5 seconds for 100+ pages
✓ Large dataset stress tested with --populate on staging
✓ Production latency budgets respected: p50 < 150ms, p95 < 500ms, p99 < 2s
✓ Throughput capacity verified via Little's Law against peak concurrent traffic
```
