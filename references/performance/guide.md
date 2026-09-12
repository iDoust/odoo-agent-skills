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
```
