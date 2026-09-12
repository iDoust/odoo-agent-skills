# Odoo Community (CE) Solutions for Enterprise Features

Production-grade architectural patterns and Community/OCA alternatives for capabilities traditionally associated with Odoo Enterprise (EE).

---

## 1. Feature Comparison & Strategic Alternatives

| Enterprise Feature (`enterprise`) | Community Solution | Core / OCA Dependency | Implementation Effort |
| --- | --- | --- | --- |
| **Financial Reports** (`account_reports`) | OCA `account_financial_report` or Native Spreadsheet Dashboards | `addons/account`, OCA `account-financial-reporting` | Low (ready-to-use) to Medium |
| **Barcode Scanning** (`stock_barcode`) | Hardware HID Keyboard Wedge or OWL Camera Scanner | `addons/barcodes`, `addons/stock` | Zero (HID) to Low (OWL) |
| **Multi-Tier Approvals** (`approvals`) | OCA `base_tier_validation` or State-Machine Guard | `addons/mail`, OCA `server-tools` | Low |
| **Digital Signatures** (`sign`) | Native `widget="signature"` & Portal Signatures | `addons/web`, `addons/portal` (Built-in CE) | Zero (native to CE) |
| **Document Management** (`documents`) | Native Categorized Attachments or OCA `dms` | `addons/base` (`ir.attachment`), OCA `dms` | Low to Medium |

---

## 2. Financial Reports in Community Edition

Odoo Community contains the complete double-entry accounting engine (`account.move`, `account.move.line`, reconciliation, journals, tax engines), but excludes the dynamic interactive drill-down financial reports provided by EE `account_reports`.

### Option A: OCA `account_financial_report` (Gold Standard)

The OCA `account-financial-reporting` suite provides complete financial statements with:
- Balance Sheet, Profit and Loss (Income Statement)
- General Ledger, Trial Balance, Aged Partner Balance (Aged Receivable/Payable)
- Fast SQL aggregation, HTML drill-down, and XLSX export.

```python
# __manifest__.py
{
    "name": "Custom Financial Reports Extension",
    "version": "18.0.1.0.0",
    "depends": [
        "account",
        "account_financial_report",  # OCA module
    ],
    "installable": True,
}
```

### Option B: Built-in Community Spreadsheet Dashboards (Odoo 17, 18, 19)

Odoo Community includes the `spreadsheet` and `spreadsheet_dashboard` engines in core. Custom interactive financial dashboards can be built without any external dependencies:

```xml
<!-- views/spreadsheet_dashboard.xml -->
<record id="spreadsheet_dashboard_financial" model="spreadsheet.dashboard">
    <field name="name">Management P&amp;L Dashboard</field>
    <field name="dashboard_group_id" ref="spreadsheet_dashboard.spreadsheet_dashboard_group_finance"/>
    <field name="data" type="base64" file="my_module/data/pl_dashboard.json"/>
    <field name="sequence">10</field>
</record>
```

Spreadsheet cells query `account.move.line` balances directly via `=ODOO.BALANCE(...)` or pivot formulas.

### Option C: Custom High-Speed Read-Only SQL Reporting Model

When custom analytical reporting is needed without third-party dependencies, implement a PostgreSQL view backed by a read-only ORM model:

```python
from odoo import api, fields, models, tools


class FinancialSummaryReport(models.Model):
    _name = "financial.summary.report"
    _description = "Financial Summary Analysis"
    _auto = False
    _order = "date desc, account_id"

    date = fields.Date(readonly=True)
    journal_id = fields.Many2one("account.journal", string="Journal", readonly=True)
    account_id = fields.Many2one("account.account", string="Account", readonly=True)
    account_code = fields.Char(string="Code", readonly=True)
    debit = fields.Monetary(readonly=True, currency_field="company_currency_id")
    credit = fields.Monetary(readonly=True, currency_field="company_currency_id")
    balance = fields.Monetary(readonly=True, currency_field="company_currency_id")
    company_currency_id = fields.Many2one("res.currency", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    aml.id AS id,
                    aml.date AS date,
                    aml.journal_id AS journal_id,
                    aml.account_id AS account_id,
                    aa.code AS account_code,
                    aml.debit AS debit,
                    aml.credit AS credit,
                    (aml.debit - aml.credit) AS balance,
                    aml.company_currency_id AS company_currency_id,
                    aml.company_id AS company_id
                FROM account_move_line aml
                JOIN account_account aa ON aa.id = aml.account_id
                JOIN account_move am ON am.id = aml.move_id
                WHERE am.state = 'posted'
            )
        """)
```

---

## 3. Barcode Scanning in Community Edition

Odoo Enterprise includes `stock_barcode`, providing a dedicated full-screen mobile interface for pickings, packings, and inventory counts. Community Edition includes the underlying `barcodes` infrastructure (`addons/barcodes`), meaning barcode support is fully functional in CE with standard workflows.

### Option A: Hardware HID Keyboard Wedge (Zero Code Required)

Almost all USB and Bluetooth handheld barcode scanners operate in **HID Keyboard Wedge** mode by default:
1. The scanner scans a barcode and types the characters into the active input element in the browser.
2. The scanner sends an automatic `Enter` (Carriage Return) keystroke.
3. In standard Odoo CE forms, focusing on the product search bar, picking line `product_id`, or lot number field immediately inputs the item and selects it.
4. **Configuration**: Program the scanner (via manufacturer configuration barcodes) to append a Tab or Enter key after reading.

### Option B: Core `barcodes` Event Listener in OWL Views

To capture scans globally on a form or list view without requiring user focus on a specific input field, bind to Odoo's core `barcode` service:

```javascript
/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillDestroy } from "@odoo/owl";

export class SimpleBarcodeScanner extends Component {
    static template = "my_module.SimpleBarcodeScanner";

    setup() {
        this.barcode = useService("barcode");
        this.onBarcodeScanned = this._onBarcodeScanned.bind(this);

        onWillStart(() => {
            this.barcode.bus.addEventListener("barcode_scanned", this.onBarcodeScanned);
        });

        onWillDestroy(() => {
            this.barcode.bus.removeEventListener("barcode_scanned", this.onBarcodeScanned);
        });
    }

    _onBarcodeScanned(ev) {
        const barcode = ev.detail.barcode;
        // Process barcode (find product, update quantity on active picking)
        this.props.record.update({ barcode_input: barcode });
    }
}
```

### Option C: Mobile Camera Scanning via Native HTML5 `BarcodeDetector` API

Modern Android and iOS mobile browsers support the native `BarcodeDetector` API directly in JavaScript without extra backend modules:

```javascript
/** @odoo-module **/
export async function scanFromVideoElement(videoElement) {
    if (!("BarcodeDetector" in window)) {
        throw new Error("BarcodeDetector API not supported in this browser");
    }
    const detector = new window.BarcodeDetector({
        formats: ["code_128", "ean_13", "qr_code", "ean_8"],
    });
    const barcodes = await detector.detect(videoElement);
    return barcodes.length > 0 ? barcodes[0].rawValue : null;
}
```

---

## 4. Multi-Tier Approvals in Community Edition

Odoo Enterprise provides the `approvals` app with customizable validation rules. In Community Edition, multi-tier approvals can be implemented cleanly either through OCA standard modules or minimal native Python logic.

### Option A: OCA `base_tier_validation`

The OCA `base_tier_validation` framework allows defining approval tiers dynamically per model from the UI without coding:

```python
from odoo import models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "tier.validation"]
    _state_field = "state"
    _state_from = ["draft", "sent"]
    _state_to = ["to_approve", "purchase"]

    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res.append("date_order")
        return res
```

Users configure tiers in **Settings > Technical > Tier Definitions** with conditions like:
- Tier 1: Team Leader approval if Amount > $1,000.
- Tier 2: Finance Director approval if Amount > $10,000.

### Option B: Native State-Machine Pattern (Zero Dependencies)

For lightweight requirements, a senior developer implements approval transitions natively using standard Odoo security groups and `mail.activity`:

```python
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    state = fields.Selection(
        selection_add=[
            ("to_approve_director", "Waiting Director Approval"),
        ],
        ondelete={"to_approve_director": "set default"},
    )
    approval_threshold = fields.Float(
        string="Director Approval Threshold",
        compute="_compute_approval_threshold",
    )

    def button_confirm(self):
        threshold = 10000.0
        for order in self:
            if order.amount_total >= threshold and order.state != "to_approve_director":
                if not self.env.user.has_group("purchase.group_purchase_manager"):
                    order.write({"state": "to_approve_director"})
                    order._schedule_approval_activity()
                    continue
        return super(PurchaseOrder, self - self.filtered(lambda o: o.state == "to_approve_director")).button_confirm()

    def action_director_approve(self):
        self.ensure_one()
        if not self.env.user.has_group("purchase.group_purchase_manager"):
            raise UserError("Only purchase managers can approve orders over the limit.")
        self.activity_feedback(["mail.mail_activity_data_todo"])
        return super().button_confirm()

    def _schedule_approval_activity(self):
        manager_group = self.env.ref("purchase.group_purchase_manager")
        managers = manager_group.users
        for manager in managers:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=manager.id,
                note=f"Purchase order {self.name} requires director approval (Amount: {self.amount_total}).",
            )
```

---

## 5. Digital Signatures in Community Edition

Many teams assume digital signatures require the Enterprise `sign` module. In reality, **`widget="signature"` is fully built into Odoo Community Edition core (`addons/web`)**.

### Internal Model Signature Field

Any model in Community Edition can capture canvas signatures (drawn with finger, stylus, or mouse) natively:

```python
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    customer_signature = fields.Binary(
        string="Customer Signature",
        copy=False,
        attachment=True,
    )
    signed_by = fields.Char(
        string="Signed By",
        copy=False,
    )
    signed_on = fields.Datetime(
        string="Signed On",
        copy=False,
    )
```

In the XML form view:

```xml
<record id="view_order_form_inherit_signature" model="ir.ui.view">
    <field name="name">sale.order.form.signature</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
        <xpath expr="//page[@name='other_information']" position="inside">
            <group string="Signature &amp; Confirmation">
                <field name="signed_by"/>
                <field name="signed_on"/>
                <field name="customer_signature"
                       widget="signature"
                       options="{'full_name': 'signed_by'}"/>
            </group>
        </xpath>
    </field>
</record>
```

### Public / Portal Online Signature

Odoo CE provides `portal.signature` mixin and web controllers:
- In `sale` and `purchase`, customers can sign quotations directly from the customer portal without any Enterprise app installed.
- Portal signatures convert the SVG signature drawing into PNG binary data and automatically create an audit trail in the chatter.

---

## 6. Document Management (DMS) in Community Edition

Odoo Enterprise provides `documents` for folder-based document organization, PDF splitting, and OCR text recognition.

### Option A: Categorized Attachments Pattern (Built-in `ir.attachment`)

Create a light categorization layer on top of Odoo's native `ir.attachment`:

```python
from odoo import fields, models


class DocumentCategory(models.Model):
    _name = "document.category"
    _description = "Document Category"

    name = fields.Char(required=True)
    code = fields.Char()


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    category_id = fields.Many2one("document.category", string="Category")
    is_verified = fields.Boolean(string="Verified Document", default=False)
```

Add a smart button on any business model (Customer, Employee, Project, Order) pointing to its related `ir.attachment` records filtered by category.

### Option B: OCA `dms` (Full Document Management System)

For enterprise-scale file management in Community Edition, the OCA `dms` module provides:
- Hierarchical Directories and Folders.
- Storage backends: PostgreSQL Database, File system (local storage), or Amazon S3.
- Directory and document level access control (groups, users).
- Document revision tracking and metadata indexing.

```python
# __manifest__.py
{
    "name": "Custom Enterprise DMS Setup",
    "version": "18.0.1.0.0",
    "depends": [
        "base",
        "dms",  # OCA dms module
    ],
    "installable": True,
}
```

---

## 7. Migration & Compatibility Guidelines (CE to EE)

When designing custom modules intended for Community Edition that might later run in an Enterprise environment:

1. **Avoid Overriding Enterprise-Reserved Model Names**:
   Never name custom models `documents.document`, `sign.request`, or `approval.request`. If the database is later upgraded to Enterprise, name collisions will block schema initialization. Use clear namespaces (e.g. `custom_dms.document` or `my_approval.request`).

2. **Clean Feature Detection**:
   Use runtime module checks or separate bridge modules (`auto_install=True`) instead of hardcoding Enterprise assumptions:
   ```python
   def is_enterprise_barcode_available(self):
       return bool(self.env["ir.module.module"].search([
           ("name", "=", "stock_barcode"),
           ("state", "=", "installed"),
       ], limit=1))
   ```

3. **Keep Data Models Additive**:
   Store data in standard Odoo core tables (`account.move`, `stock.picking`, `ir.attachment`) whenever possible so transitioning to Enterprise features requires zero data migration.
