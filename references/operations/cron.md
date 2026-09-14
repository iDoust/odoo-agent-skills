# Scheduled Actions and Automation Patterns

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CRON & AUTOMATION PATTERNS                                                  ║
║  Scheduled actions, server actions, and automated rules                      ║
║  Use for background jobs, triggers, and workflow automation                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Scheduled Actions (Cron Jobs)

### Basic Cron Definition (XML)
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="ir_cron_process_pending" model="ir.cron">
        <field name="name">My Module: Process Pending Records</field>
        <field name="model_id" ref="model_my_model"/>
        <field name="state">code</field>
        <field name="code">model._cron_process_pending()</field>
        <field name="interval_number">1</field>
        <field name="interval_type">hours</field>
        <field name="numbercall">-1</field>
        <field name="active">True</field>
        <field name="doall">False</field>
    </record>
</odoo>
```

### Interval Types
| Type | Description |
|------|-------------|
| `minutes` | Run every X minutes |
| `hours` | Run every X hours |
| `days` | Run every X days |
| `weeks` | Run every X weeks |
| `months` | Run every X months |

### Cron Attributes
| Attribute | Description |
|-----------|-------------|
| `interval_number` | Number of intervals |
| `interval_type` | Type of interval |
| `numbercall` | -1 for infinite, or count |
| `active` | Enable/disable cron |
| `doall` | Run missed executions |
| `nextcall` | Next execution datetime |
| `priority` | Execution priority (lower = first) |

---

## Python Cron Methods

### Basic Cron Method
```python
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class MyModel(models.Model):
    _name = 'my.model'

    @api.model
    def _cron_process_pending(self) -> None:
        """Process pending records - called by scheduled action."""
        _logger.info("Starting cron: process pending records")

        records = self.search([('state', '=', 'pending')], limit=100)
        _logger.info(f"Found {len(records)} pending records")

        for record in records:
            try:
                record._process_single()
            except Exception as e:
                _logger.error(f"Error processing {record.id}: {e}")

        _logger.info("Cron completed: process pending records")
```

### Batch Processing Cron
```python
@api.model
def _cron_batch_process(self) -> None:
    """Process records in batches with commits."""
    batch_size = 100
    offset = 0
    processed = 0

    while True:
        # Fetch batch
        records = self.search(
            [('state', '=', 'pending')],
            limit=batch_size,
            offset=offset,
        )

        if not records:
            break

        for record in records:
            try:
                record.with_context(from_cron=True)._do_process()
                processed += 1
            except Exception as e:
                _logger.error(f"Error on record {record.id}: {e}")

        # Commit batch and clear cache
        self.env.cr.commit()
        self.env.invalidate_all()

        offset += batch_size
        _logger.info(f"Processed {processed} records so far...")

    _logger.info(f"Batch process complete: {processed} records")
```

### Time-Limited Cron
```python
import time

@api.model
def _cron_time_limited_process(self) -> None:
    """Process with time limit to prevent long-running jobs."""
    max_duration = 300  # 5 minutes
    start_time = time.time()
    processed = 0

    records = self.search([('needs_sync', '=', True)])

    for record in records:
        # Check time limit
        if time.time() - start_time > max_duration:
            _logger.warning(
                f"Time limit reached after {processed} records. "
                f"Remaining: {len(records) - processed}"
            )
            break

        try:
            record._sync_external()
            processed += 1
        except Exception as e:
            _logger.error(f"Sync error for {record.id}: {e}")

        # Periodic commit
        if processed % 50 == 0:
            self.env.cr.commit()

    _logger.info(f"Processed {processed}/{len(records)} records")
```

---

## Server Actions

### Python Code Action
```xml
<record id="action_mark_done" model="ir.actions.server">
    <field name="name">Mark as Done</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="binding_model_id" ref="model_my_model"/>
    <field name="binding_view_types">list,form</field>
    <field name="state">code</field>
    <field name="code">
if records:
    records.write({'state': 'done'})
    </field>
</record>
```

### Multi-Record Action
```xml
<record id="action_batch_confirm" model="ir.actions.server">
    <field name="name">Confirm Selected</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="binding_model_id" ref="model_my_model"/>
    <field name="binding_view_types">list</field>
    <field name="state">code</field>
    <field name="code">
for record in records:
    if record.state == 'draft':
        record.action_confirm()
    </field>
</record>
```

### Action with Notification
```xml
<record id="action_notify_users" model="ir.actions.server">
    <field name="name">Notify Users</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="binding_model_id" ref="model_my_model"/>
    <field name="state">code</field>
    <field name="code">
count = len(records)
records.action_send_notification()
action = {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
    'params': {
        'title': 'Success',
        'message': f'Notified {count} users.',
        'type': 'success',
        'sticky': False,
    }
}
    </field>
</record>
```

---

## Automated Actions (Base Automation in v17, v18, v19)

In modern Odoo (v17+), `base.automation` delegates code execution to `ir.actions.server` via `action_server_ids`. The fields `state` and `code` do NOT exist on `base.automation` itself. Legacy `on_create` and `on_write` triggers are unified into `on_create_or_write`.

### On Create/Write Trigger with Server Action
```xml
<!-- 1. Define Server Action for the automation logic -->
<record id="action_server_auto_assign" model="ir.actions.server">
    <field name="name">Auto-assign on Create Action</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="state">code</field>
    <field name="code">
for record in records:
    if not record.user_id:
        record.user_id = record.create_uid
    </field>
</record>

<!-- 2. Define Automation Rule linking to the action -->
<record id="automation_on_create" model="base.automation">
    <field name="name">Auto-assign on Create</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="trigger">on_create_or_write</field>
    <field name="action_server_ids" eval="[Command.link(ref('action_server_auto_assign'))]"/>
</record>
```

### On State Change Trigger
```xml
<record id="action_server_notify_state_change" model="ir.actions.server">
    <field name="name">Notify on State Change Action</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="state">code</field>
    <field name="code">
records.message_post(
    body="Record has been confirmed.",
    message_type='notification',
)
    </field>
</record>

<record id="automation_on_state_change" model="base.automation">
    <field name="name">Notify on State Change</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="trigger">on_create_or_write</field>
    <field name="trigger_field_ids" eval="[Command.set([ref('field_my_model__state')])]"/>
    <field name="filter_domain">[('state', '=', 'confirmed')]</field>
    <field name="action_server_ids" eval="[Command.link(ref('action_server_notify_state_change'))]"/>
</record>
```

### Time-Based Trigger (Deadline / Overdue)
```xml
<record id="action_server_mark_overdue" model="ir.actions.server">
    <field name="name">Mark Overdue Action</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="state">code</field>
    <field name="code">
records.write({'is_overdue': True})
records.message_post(body="This record is now overdue!")
    </field>
</record>

<record id="automation_overdue_check" model="base.automation">
    <field name="name">Mark Overdue Records</field>
    <field name="model_id" ref="model_my_model"/>
    <field name="trigger">on_time</field>
    <field name="trg_date_id" ref="field_my_model__deadline"/>
    <field name="trg_date_range">1</field>
    <field name="trg_date_range_type">day</field>
    <field name="filter_domain">[('state', 'not in', ['done', 'cancel'])]</field>
    <field name="action_server_ids" eval="[Command.link(ref('action_server_mark_overdue'))]"/>
</record>
```

### Modern Trigger Types (v17, v18, v19)
| Trigger | When Executed | Notes |
|---------|---------------|-------|
| `on_create_or_write` | On record creation or modification | Replaces deprecated `on_create` / `on_write` |
| `on_stage_set` | When stage field changes | Optimized for Kanban workflows |
| `on_state_set` | When state selection changes | Optimized for business document states |
| `on_user_set` | When user assignment changes | Triggers on owner/assignee update |
| `on_tag_set` | When tags are added | Many2many tag additions |
| `on_time` | Relative to a date/datetime field | Scheduled relative to deadline/event |
| `on_time_created` | X days/hours after creation | Automated follow-ups |
| `on_time_updated` | X days/hours after last write | Inactivity reminders |
| `on_unlink` | Before record deletion | Preventative audits or cascade logic |
| `on_change` | Immediate on UI value change | Client-side dynamic evaluations |
| `on_webhook` | Triggered via incoming HTTP webhook | Payload available in context |

---

## Queue Jobs (for Heavy Processing)

### Using ir.cron with Batching
```python
@api.model
def _cron_heavy_process(self) -> None:
    """Heavy process with queue-like behavior."""
    # Get unprocessed records
    to_process = self.search([
        ('processed', '=', False),
        ('attempts', '<', 3),  # Max retry attempts
    ], limit=50)

    for record in to_process:
        try:
            record.with_context(processing=True)._heavy_operation()
            record.processed = True
            record.processed_date = fields.Datetime.now()
        except Exception as e:
            record.attempts += 1
            record.last_error = str(e)
            _logger.error(f"Processing failed for {record.id}: {e}")

        # Commit after each to preserve progress
        self.env.cr.commit()
```

### Deferred Processing Pattern
```python
class MyModel(models.Model):
    _name = 'my.model'

    process_state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='pending')
    process_error = fields.Text()

    def action_queue_for_processing(self) -> None:
        """Queue records for cron processing."""
        self.write({
            'process_state': 'pending',
            'process_error': False,
        })

    @api.model
    def _cron_process_queue(self) -> None:
        """Process queued records."""
        records = self.search([
            ('process_state', '=', 'pending')
        ], limit=20)

        for record in records:
            record.process_state = 'processing'
            self.env.cr.commit()

            try:
                record._do_heavy_work()
                record.process_state = 'done'
            except Exception as e:
                record.process_state = 'error'
                record.process_error = str(e)

            self.env.cr.commit()
```

---

## Best Practices

### 1. Logging
```python
import logging
_logger = logging.getLogger(__name__)

@api.model
def _cron_task(self) -> None:
    _logger.info("Cron started: %s", self._name)
    try:
        # Work here
        _logger.info("Cron completed successfully")
    except Exception as e:
        _logger.exception("Cron failed: %s", e)
        raise
```

### 2. Transaction Safety
```python
@api.model
def _cron_safe_process(self) -> None:
    """Process with proper transaction handling."""
    records = self.search([('pending', '=', True)])

    for record in records:
        # Use new cursor for isolation
        try:
            with self.env.cr.savepoint():
                record._process()
        except Exception as e:
            _logger.error(f"Failed {record.id}: {e}")
            # Savepoint rollback - continue with next
            continue
```

### 3. Idempotency
```python
@api.model
def _cron_idempotent_sync(self) -> None:
    """Idempotent sync - safe to run multiple times."""
    records = self.search([
        ('needs_sync', '=', True),
        ('last_sync_attempt', '<', fields.Datetime.now() - timedelta(minutes=5)),
    ])

    for record in records:
        record.last_sync_attempt = fields.Datetime.now()
        self.env.cr.commit()

        try:
            record._sync()
            record.needs_sync = False
        except Exception:
            pass  # Will retry on next run
```

### 4. Monitoring
```python
@api.model
def _cron_with_monitoring(self) -> None:
    """Cron with execution tracking."""
    start = fields.Datetime.now()

    try:
        count = self._do_work()
        status = 'success'
        error = False
    except Exception as e:
        count = 0
        status = 'error'
        error = str(e)

    # Log execution
    self.env['my.cron.log'].create({
        'cron_name': 'process_pending',
        'start_time': start,
        'end_time': fields.Datetime.now(),
        'records_processed': count,
        'status': status,
        'error_message': error,
    })
```

---

## Cron Security

### Manifest Declaration
```python
# Cron data file must be in 'data' section
'data': [
    'data/cron.xml',
]
```

### Access Rights
Crons run as the user who created them (usually admin). For specific user context:

```python
@api.model
def _cron_as_specific_user(self) -> None:
    """Run as specific user for proper access rights."""
    cron_user = self.env.ref('my_module.cron_service_user')
    self_as_user = self.with_user(cron_user)
    self_as_user._do_work()
```

---

## Multi-Company Cron Execution & Financial Integrity

Crons that process financial transactions (recurring invoices, automated billing, payment retries, currency revaluations, deferred revenue) must respect multi-company boundaries and accounting lock dates:

```python
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountRecurringInvoice(models.Model):
    _name = 'account.recurring.invoice'
    _description = 'Recurring Invoice Automation'

    @api.model
    def _cron_generate_recurring_invoices(self) -> None:
        """Process recurring invoices per company with strict transaction isolation."""
        companies = self.env['res.company'].search([])

        for company in companies:
            # 1. Switch context to the specific company
            company_self = self.with_company(company)
            _logger.info("Starting recurring invoice generation for company: %s", company.name)

            today = fields.Date.context_today(company_self)

            # 2. Check Fiscal Lock Dates
            if company.period_lock_date and today <= company.period_lock_date:
                _logger.warning(
                    "Skipping company %s: accounting period is locked through %s",
                    company.name, company.period_lock_date
                )
                continue

            recurring_orders = company_self.search([
                ('company_id', '=', company.id),
                ('state', '=', 'running'),
                ('next_date', '<=', today),
            ])

            for order in recurring_orders:
                # 3. Transaction Isolation via Savepoint
                # If one order fails (e.g. invalid tax or credit limit), other orders still commit
                try:
                    with self.env.cr.savepoint():
                        invoice = order._create_invoice()
                        invoice.action_post()
                        order.next_date = order._compute_next_date(today)
                        _logger.info("Successfully generated invoice %s for order %s", invoice.name, order.id)
                except Exception as e:
                    _logger.error("Failed to generate recurring invoice for order %s: %s", order.id, e)
                    # Savepoint rolls back the failed order's partial changes; loop continues cleanly
                    continue
```

---

## Asynchronous Job Queues: `ir.cron` vs OCA `queue_job`

While Odoo's native `ir.cron` handles time-based recurring schedules, high-volume production deployments require an **asynchronous job queue** for event-driven background processing.

### Decision Matrix

| Requirement | Native `ir.cron` | OCA `queue_job` |
| :--- | :--- | :--- |
| **Execution Trigger** | Periodic time interval (minutes/hours/days) | Event-driven instant enqueue (`with_delay()`) |
| **User Experience** | Background polling only | Sub-second UI response (delegates work instantly) |
| **Automatic Retry** | Manual re-run on next cron cycle | Automatic retry with configurable exponential backoff |
| **Channel & Concurrency** | Shared cron worker threads | Dedicated priority channels (e.g. fast mail vs heavy sync) |
| **Visibility & Audit** | Basic execution log in `ir.cron` | Full UI job tracking: Pending, Enqueued, Started, Done, Failed |
| **Ideal Use Cases** | Nightly backups, daily subscription generation | Marketplace sync, carrier API labels, bulk notifications |

### OCA `queue_job` Implementation Pattern

#### 1. Manifest Dependency
In `__manifest__.py`:
```python
{
    'name': 'Marketplace Integration',
    'depends': ['sale', 'queue_job'],
    'data': [
        'data/queue_job_channel_data.xml',
    ],
}
```

#### 2. Model Method Definition (`@job`)
```python
from odoo import models, api
from odoo.addons.queue_job.job import job


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @job(default_channel='root.integration', retry_pattern={1: 60, 2: 300, 3: 900})
    def _async_sync_order_to_erp(self, target_system='sap'):
        """Executed asynchronously by a queue_job background worker."""
        self.ensure_one()
        # External HTTP request or heavy payload transformation
        payload = self._prepare_external_payload()
        response = self._call_external_api(target_system, payload)
        self.write({'external_sync_id': response.get('id')})
```

#### 3. Enqueueing from UI or Controller
```python
def action_confirm(self):
    res = super().action_confirm()
    for order in self:
        # Enqueue job immediately: returns instantly to the user without blocking HTTP worker
        order.with_delay(priority=10, description=f"Sync SO {order.name} to SAP")._async_sync_order_to_erp()
    return res
```

#### 4. Server Configuration (`odoo.conf`)
```ini
[options]
server_wide_modules = base,web,queue_job
# Channel worker concurrency allocation
queue_job.channels = root:2,root.integration:4,root.mail:2
```

---

## Related References

- [Email & Mail Routing](mail.md)
- [Logging & Error Tracking](logging.md)
- [CLI & Shell Commands](cli-and-shell.md)
- [Operations Directory Index](README.md)
- [Error Handling Patterns](../orm/error-handling-patterns.md)
