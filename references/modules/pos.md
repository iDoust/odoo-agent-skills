# Point of Sale (POS) Integration & Accounting Patterns

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  POINT OF SALE (POS) INTEGRATION PATTERNS                                    ║
║  Sessions, orders, payment methods, session closing, and accounting sync     ║
║  Use for retail automation, cash control, and daily financial reconciliation ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Module Setup

### Manifest Dependencies
```python
{
    'name': 'My POS Extension',
    'version': '18.0.1.0.0',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'my_pos_module/static/src/**/*',
        ],
    },
}
```

---

## End-to-End Accounting Pipeline: POS-to-Cash

In standard Odoo, retail transactions from the Point of Sale flow directly into double-entry accounting through daily sessions (`pos.session`):

```
[Open Session (pos.session)]
        │  Starting Cash Control
        ▼
[POS Orders (pos.order)] ────► [Payments (pos.payment)]
        │                           Cash, Bank/Card, Customer Account
        │
        ▼ action_pos_session_closing_control()
[Session Closing & Cash Count]
        │
        ▼ Generate Summary Move
[Journal Entry (account.move)]
Dr: POS Cash / Bank Clearing (asset_cash / asset_current)
Dr: Cash Difference Loss (expense, if cash short)
Cr: Product Sales Revenue (income)
Cr: Tax Payable (liability_current)
Cr: Cash Difference Gain (income_other, if cash over)
        │
        ▼ bank statement reconciliation
Bank Card Clearing
Dr: Bank Account (asset_cash)
Cr: POS Bank Clearing Account (asset_current)
        │
        ▼
[Financial Reports: Daily Sales, P&L, Balance Sheet, Tax Report]
```

---

## Session Lifecycle & Closing Control

### 1. POS Payment Methods (`pos.payment.method`)
Each POS payment method defines its own destination account:
- **Cash**: Directly posts to the POS Cash Journal or Cash Account.
- **Card / EDC / QRIS**: Posts to an intermediary **Bank Clearing / Transit Account** (`asset_current`). When the bank settlement statement arrives, bank reconciliation clears the transit account to the true bank ledger.
- **Customer Account (Credit)**: Generates a receivable on the customer's partner ledger (`asset_receivable`, `reconcile=True`).

### 2. Invoicing from POS
When a retail customer requests an official tax invoice:
- The POS order creates an individual `account.move` (`move_type='out_invoice'`).
- The POS payment is linked and automatically reconciled against the invoice receivable line (`reconcile()`).

### 3. Handling Cash Differences (Audit Compliance)
During session closing, the cashier inputs the counted physical cash (`cash_register_balance_end_real`).
- If counted < theoretical: Odoo posts the loss to the journal's configured **Loss Account** (`expense`).
- If counted > theoretical: Odoo posts the surplus to the journal's configured **Profit Account** (`income_other`).

---

## Server Model Extension Example

```python
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_member_card = fields.Char(string='Loyalty Member Card', index=True)
    x_cashier_note = fields.Text(string='Cashier Note')

    @api.model
    def _order_fields(self, ui_order):
        """Map custom fields from frontend JSON payload to backend record."""
        order_fields = super()._order_fields(ui_order)
        order_fields['x_member_card'] = ui_order.get('x_member_card')
        order_fields['x_cashier_note'] = ui_order.get('x_cashier_note')
        return order_fields
```

---

## Best Practices

1. **Do not bypass session closing**: Never attempt to post individual draft accounting entries for POS cash orders; let the session closing control aggregate them to prevent database bloat and preserve audit integrity.
2. **Dedicated clearing accounts**: Always configure separate clearing accounts for electronic payments (Credit Card, QRIS, Transfer) to allow smooth bank reconciliation against EDC settlements.
3. **Cash control enforcement**: Enforce physical opening and closing cash counts to detect cashier shortages early.
4. **Stock synchronization**: Verify whether the POS configuration uses real-time stock picking (`ship_later=False`) or bulk end-of-day stock picking.
5. **Offline safety**: Ensure custom frontend fields are preserved in local storage and correctly synced when connectivity resumes.

---

## Sources

- Odoo 17 POS: https://github.com/odoo/odoo/tree/17.0/addons/point_of_sale
- Odoo 18 POS: https://github.com/odoo/odoo/tree/18.0/addons/point_of_sale
- Odoo 19 POS: https://github.com/odoo/odoo/tree/19.0/addons/point_of_sale
