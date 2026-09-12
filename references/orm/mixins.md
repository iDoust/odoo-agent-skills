# Standard ORM Mixins & Useful Classes

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  STANDARD ORM MIXINS & USEFUL CLASSES                                        ║
║  Reusable behaviors: Chatter, Activities, Images, Avatars, UTM, Ratings      ║
║  Supported across Odoo 17, 18, and 19                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

Mixins in Odoo are abstract models (`models.AbstractModel`) that encapsulate reusable fields, business logic, and UI components. When inherited via `_inherit = ['...']`, they inject standardized capabilities into your custom models.

---

## Mixin Catalog

| Mixin | Required Manifest Dependency | Primary Fields Injected | Purpose |
| :--- | :--- | :--- | :--- |
| `mail.thread` | `'depends': ['mail']` | `message_follower_ids`, `message_ids` | Chatter, messaging, audit trails, and field value tracking |
| `mail.activity.mixin` | `'depends': ['mail']` | `activity_ids`, `activity_state`, `activity_user_id` | Activity scheduling, reminders, and next-action workflows |
| `image.mixin` | None (built into `base`) | `image_1920`, `image_1024`, `image_512`, `image_256`, `image_128` | Multi-resolution responsive images with automatic PIL resizing |
| `avatar.mixin` | None (built into `base`) | Inherits `image.mixin` + `avatar_1920`..`128` | Dynamic avatars with deterministic HSL SVG generation from name |
| `utm.mixin` | `'depends': ['utm']` | `campaign_id`, `source_id`, `medium_id` | Lead acquisition and marketing campaign attribution |
| `rating.mixin` | `'depends': ['rating']` | `rating_ids`, `rating_last_value`, `rating_avg` | Customer feedback, star ratings, and satisfaction metrics |
| `portal.mixin` | `'depends': ['portal']` | `access_token`, `access_url`, `access_warning` | Secure customer portal URLs and token-based external access |

---

## 1. `mail.thread` & `mail.activity.mixin` (Chatter & Activities)

Use `mail.thread` and `mail.activity.mixin` together on any business document requiring an audit trail, customer discussions, or scheduled follow-ups.

### Model Definition

```python
from odoo import fields, models


class ProjectTask(models.Model):
    _name = 'project.task'
    _description = 'Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Title', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Assignee', tracking=True)
    state = fields.Selection([
        ('draft', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='draft', tracking=True)

    def action_complete(self):
        self.write({'state': 'done'})
        # Post message to chatter
        self.message_post(
            body="Task marked as completed.",
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
```

### Form View Integration

> [!IMPORTANT]
> **Version Syntax for Chatter**:
> - In **Odoo 18 & 19**: Use the self-closing `<chatter/>` tag at the bottom of the `<form>` view.
> - In **Odoo 17**: Use the legacy `<div class="oe_chatter">` structure.

```xml
<!-- Odoo 18 & 19 -->
<form string="Task">
    <sheet>
        <group>
            <field name="name"/>
            <field name="user_id"/>
            <field name="state"/>
        </group>
    </sheet>
    <chatter/>
</form>

<!-- Odoo 17 Legacy -->
<form string="Task">
    <sheet>
        <group>
            <field name="name"/>
            <field name="user_id"/>
            <field name="state"/>
        </group>
    </sheet>
    <div class="oe_chatter">
        <field name="message_follower_ids"/>
        <field name="activity_ids"/>
        <field name="message_ids"/>
    </div>
</form>
```

---

## 2. `image.mixin` (Multi-Resolution Images)

`image.mixin` automatically creates and synchronizes 5 resized binary fields whenever `image_1920` is uploaded. The resized fields are stored as attachments for optimal web rendering performance:
- `image_1920`: Full resolution (max 1920x1920)
- `image_1024`: Large desktop/tablet views (max 1024x1024)
- `image_512`: Medium displays (max 512x512)
- `image_256`: Kanban cards & thumbnails (max 256x256)
- `image_128`: Small icons and list views (max 128x128)

### Model Definition

```python
from odoo import fields, models


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _description = 'Vehicle'
    _inherit = ['image.mixin']

    name = fields.Char(string='License Plate', required=True)
    model_id = fields.Char(string='Model')
    # image_1920, image_1024, image_512, image_256, image_128 are automatically added
```

### View Integration

```xml
<form string="Vehicle">
    <sheet>
        <!-- Large image widget on form header -->
        <field name="image_1920" widget="image" class="oe_avatar"
               options="{'preview_image': 'image_128'}"/>
        <div class="oe_title">
            <h1><field name="name"/></h1>
        </div>
        <group>
            <field name="model_id"/>
        </group>
    </sheet>
</form>

<!-- Kanban card thumbnail -->
<kanban>
    <templates>
        <t t-name="kanban-box">
            <div class="oe_kanban_global_click">
                <field name="image_128" widget="image" class="oe_avatar me-2"/>
                <div class="oe_kanban_details">
                    <strong class="o_kanban_record_title"><field name="name"/></strong>
                </div>
            </div>
        </t>
    </templates>
</kanban>
```

---

## 3. `avatar.mixin` (Smart Fallback Avatars)

`avatar.mixin` extends `image.mixin`. If no picture has been uploaded, it automatically computes an SVG avatar with a deterministic HSL background color seeded from the record's name (`_avatar_name_field`).

### Model Definition

```python
from odoo import fields, models


class EmployeeBadge(models.Model):
    _name = 'employee.badge'
    _description = 'Employee Badge'
    _inherit = ['avatar.mixin']
    _avatar_name_field = 'display_name'  # Field used to seed fallback SVG color

    display_name = fields.Char(string='Full Name', required=True)
    department = fields.Char(string='Department')
```

### View Integration

```xml
<!-- Displays avatar with fallback SVG automatically if image is unset -->
<field name="avatar_128" widget="image" class="oe_avatar"/>
```

---

## 4. `utm.mixin` (Marketing Source Tracking)

Incorporate `utm.mixin` whenever custom records originate from campaigns, web tracking links, social media, or advertisements.

### Model Definition

```python
from odoo import fields, models


class SubscriptionLead(models.Model):
    _name = 'subscription.lead'
    _description = 'Subscription Lead'
    _inherit = ['utm.mixin']

    name = fields.Char(string='Lead Name', required=True)
    email = fields.Char(string='Email')

    # Automatically includes:
    # - campaign_id (Many2one -> 'utm.campaign')
    # - source_id (Many2one -> 'utm.source')
    # - medium_id (Many2one -> 'utm.medium')
```

### View Integration

Group UTM tracking fields under a dedicated "Marketing" notebook page:

```xml
<page string="Marketing" name="utm_tracking">
    <group>
        <group string="Attribution">
            <field name="campaign_id"/>
            <field name="medium_id"/>
            <field name="source_id"/>
        </group>
    </group>
</page>
```

---

## 5. `rating.mixin` (Customer Feedback & Satisfaction)

Allows users or external portal customers to rate a transaction, project, or support ticket.

### Model Definition

```python
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'rating.mixin']
    _rating_satisfaction_days = 30  # Compute stats over 30 days

    name = fields.Char(string='Subject', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')

    def action_request_rating(self):
        """Send satisfaction survey email to partner."""
        self.ensure_one()
        template = self.env.ref('helpdesk.rating_ticket_email_template')
        self.rating_send_request(template, partner=self.partner_id)
```

### Stat Button in Form View

```xml
<sheet>
    <div class="oe_button_box" name="button_box">
        <button name="action_open_ratings" type="object"
                class="oe_stat_button" icon="fa-smile-o"
                invisible="rating_count == 0">
            <field name="rating_count" string="Rating" widget="statinfo"/>
        </button>
    </div>
    <!-- Record fields -->
</sheet>
```

---

## 6. `portal.mixin` (Secure External URLs & Tokens)

`portal.mixin` enables models to generate secure, unguessable access tokens (`access_token`) so third-party customers can view documents without logging in.

### Model Definition

```python
from odoo import fields, models


class CustomerInvoice(models.Model):
    _name = 'customer.invoice'
    _description = 'Customer Invoice'
    _inherit = ['portal.mixin', 'mail.thread']

    name = fields.Char(string='Invoice #', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    amount_total = fields.Monetary(string='Total')
    currency_id = fields.Many2one('res.currency', string='Currency')

    def _compute_access_url(self):
        super()._compute_access_url()
        for record in self:
            record.access_url = f"/my/invoices/{record.id}"
```

### Controller Usage with `portal.mixin`

```python
from werkzeug.exceptions import NotFound, Forbidden
from odoo import http
from odoo.http import request


class CustomerPortal(http.Controller):

    @http.route('/my/invoices/<int:invoice_id>', type='http', auth='public', website=True)
    def portal_my_invoice(self, invoice_id, access_token=None, **kw):
        try:
            # portal.mixin checks access_token or current logged-in user ACL
            invoice_sudo = self._document_check_access(
                'customer.invoice', invoice_id, access_token=access_token
            )
        except (NotFound, Forbidden):
            return request.redirect('/my')

        return request.render('my_module.portal_invoice_page', {
            'invoice': invoice_sudo,
        })
```

---

## Multi-Mixin Composition Best Practice

When combining multiple mixins, follow standard Odoo MRO ordering:

```python
class SaleContract(models.Model):
    _name = 'sale.contract'
    _description = 'Sales Contract'
    _inherit = [
        'portal.mixin',
        'mail.thread',
        'mail.activity.mixin',
        'utm.mixin',
        'image.mixin',
    ]

    name = fields.Char(string='Contract Ref', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)
```

In `__manifest__.py`, declare all dependencies:
```python
{
    'name': 'Sales Contracts',
    'version': '1.0.0',
    'depends': ['base', 'mail', 'portal', 'utm'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_contract_views.xml',
    ],
}
```
