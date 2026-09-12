# Multi-Company Architecture, Security & Financial Isolation

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  MULTI-COMPANY ARCHITECTURE & FINANCIAL INTEGRATION                          ║
║  Data isolation, check_company constraints, inter-company transactions,      ║
║  and statutory IFRS 10 consolidation rules for Odoo 17, 18, and 19           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

Multi-company isolation is a strict server-side invariant. Bypassing company boundaries without strict controls results in ledger contamination, legal compliance violations, and distorted financial statements.

---

## 1. Core Model Design Patterns

### Standard Company Field Declaration
For any model that belongs to a specific legal entity:

```python
from odoo import api, fields, models


class CustomFinancialDocument(models.Model):
    _name = 'custom.financial.document'
    _description = 'Custom Financial Document'
    _check_company_auto = True  # Enforces check_company=True on relational fields

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        check_company=True,  # Partner must belong to self.company_id or have no company
    )
    account_id = fields.Many2one(
        'account.account',
        string='Account',
        check_company=True,  # Crucial: Account MUST belong to the exact same company
    )
```

### Relational Integrity with `check_company=True`
- Set `_check_company_auto = True` on the model.
- Add `check_company=True` on all `Many2one`, `One2many`, and `Many2many` fields pointing to company-dependent models (`res.partner`, `product.product`, `account.journal`, `account.account`, `stock.warehouse`, `stock.location`).
- If an agent assigns an account or partner belonging to Company B to a document belonging to Company A, Odoo automatically raises a `UserError` before the SQL transaction commits.

---

## 2. Multi-Company Record Rules (`ir.rule`)

Every company-specific model must declare a multi-company record rule in `security/ir_rule.xml`:

```xml
<record id="custom_financial_document_company_rule" model="ir.rule">
    <field name="name">Custom Financial Document: Multi-Company Rule</field>
    <field name="model_id" ref="model_custom_financial_document"/>
    <field name="domain_force">
        ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]
    </field>
</record>
```

### Critical Distinction: `company_ids` vs `company_id` in Rules
- **`company_ids`**: The list of all companies currently selected/checked by the logged-in user in the top navigation bar switcher.
- **`company_id`**: The single active company (`env.company`).
- Never write `[('company_id', '=', user.company_id.id)]` in standard business rules; using `user.company_id.id` breaks multi-company browsing and throws access errors when a user manages multiple entities.

---

## 3. Environment & Context Switching

### Operating with `with_company()`
When performing actions on behalf of a specific company (such as running cron jobs, confirming automated orders, or posting journal entries):

```python
# CORRECT: Clean company context
for company in self.env['res.company'].search([]):
    # Switches env.company and sets allowed company_ids to [company.id]
    docs = self.env['custom.financial.document'].with_company(company).search([
        ('state', '=', 'draft'),
    ])
    for doc in docs:
        doc.action_process()
```

### ANTI-PATTERN: Indiscriminate `sudo()`
```python
# DANGEROUS ANTI-PATTERN:
# Bypasses all multi-company record rules, potentially mixing transactions
# of separate legal entities and violating audit regulations!
docs = self.env['custom.financial.document'].sudo().search([])
```
If elevated rights are required, chain `with_company` to prevent cross-company leakage:
```python
docs = self.env['custom.financial.document'].sudo().with_company(target_company).search([...])
```

---

## 4. Multi-Company Accounting & Statutory Rules (IFRS 10)

In international accounting, separate legal companies represent independent reporting entities.

### 1. General Ledger & Chart of Accounts Segregation
- Each company maintains its own Chart of Accounts (`account.account`), Journals (`account.journal`), and Accounting Sequences.
- A Journal Entry (`account.move`) is strictly bound to `company_id`. Every single move line (`account.move.line`) must have the exact same `company_id` as the header move. Cross-company move lines inside a single `account.move` are mathematically impossible and strictly prohibited by Odoo constraints.

### 2. Lock Dates are Company-Specific
Lock dates (`fiscalyear_lock_date`, `period_lock_date`, `tax_lock_date`) are stored on `res.company`.
- Auditing closing for Company A does not block transaction posting in Company B unless Company B has also set its lock date.

### 3. Inter-Company Transactions (O2C & P2P)
When sister companies trade (e.g., Operating Entity sells to Holding Entity):
- **Upstream**: Purchase Order created in Company B automatically triggers a Sales Order in Company A via inter-company rules (`res.config.settings`).
- **Midstream Logistics**: Company A ships goods (`stock.picking` delivery) -> Perpetual inventory reduces in Company A. Company B receives goods -> Stock increases in Company B.
- **Invoicing**:
  - Company A posts Customer Invoice:
    - `Dr. Inter-Company Accounts Receivable (Company B)`
    - `Cr. Inter-Company Sales Revenue`
  - Company B posts Vendor Bill:
    - `Dr. Interim Stock Receipt / Expense`
    - `Cr. Inter-Company Accounts Payable (Company A)`

### 4. IFRS 10 Consolidated Financial Reporting & Eliminations
Under IFRS 10 (Consolidated Financial Statements):
- Inter-company sales, revenues, expenses, receivables, and payables must be **eliminated** upon consolidation.
- If Company A's revenue of $100k came from Company B, group revenue cannot be reported as $100k higher.
- Dedicated inter-company clearing accounts are used so that consolidation reports can identify and offset matching debits and credits:
  - `Dr. Inter-Company Accounts Payable`
  - `Cr. Inter-Company Accounts Receivable`
  - `Dr. Inter-Company Revenue`
  - `Cr. Inter-Company Cost of Goods Sold`

---

## 5. Multi-Company Testing Checklist

When authoring unit or integration tests for multi-company features:

```python
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError
from odoo.fields import Command


@tagged('post_install', '-at_install')
class TestMultiCompanyIsolation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env['res.company'].create({'name': 'Company A'})
        cls.company_b = cls.env['res.company'].create({'name': 'Company B'})

        cls.user_a = cls.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a',
            'company_id': cls.company_a.id,
            'company_ids': [Command.set([cls.company_a.id])],
            'groups_id': [Command.set([cls.env.ref('base.group_user').id])],
        })

    def test_cross_company_isolation(self):
        """Verify User A cannot read or modify Company B records."""
        doc_b = self.env['custom.financial.document'].with_company(self.company_b).create({
            'name': 'Doc B',
            'company_id': self.company_b.id,
        })

        # User A searches for documents: must find 0 records
        user_docs = self.env['custom.financial.document'].with_user(self.user_a).search([
            ('id', '=', doc_b.id),
        ])
        self.assertFalse(user_docs)

        # Direct read attempt must raise AccessError
        with self.assertRaises(AccessError):
            doc_b.with_user(self.user_a).read(['name'])
```

---

## Best Practices Summary

1. **Always declare `company_id`** with `default=lambda self: self.env.company`.
2. **Always add `check_company=True`** on relational fields pointing to company-dependent models.
3. **Always write multi-company record rules** using `('company_id', 'in', company_ids)`.
4. **Never use bare `sudo()`** without `with_company()` when creating transactions.
5. **Enforce inter-company elimination accounts** to guarantee statutory compliance under IFRS 10.
