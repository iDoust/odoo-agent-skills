# Accounting Integration Patterns

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ACCOUNTING INTEGRATION PATTERNS                                             ║
║  Journal entries, invoicing, and financial operations                        ║
║  Use for ERP integrations, financial reporting, and accounting automation    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Module Setup

### Manifest Dependencies
```python
{
    'name': 'My Accounting Module',
    'version': '18.0.1.0.0',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'views/account_views.xml',
    ],
}
```

## Core Principles (IFRS / GAAP & Odoo Standard Accounting)

Odoo accounting strictly models international financial standards (IFRS and US GAAP). Every business process—sales, procurement, warehouse logistics, payroll, and point of sale—ultimately results in standard double-entry journal entries. Agents working with Odoo MUST adhere to these non-negotiable principles:

### 1. Double-Entry Bookkeeping & Balance Guarantee
- Every financial transaction is represented by an `account.move` containing multiple `account.move.line` records.
- **Fundamental Invariant**: For every move, the sum of debits MUST exactly equal the sum of credits in the company's functional currency (`sum(line.debit) == sum(line.credit)`).
- On `account.move.line`, the signed `balance` is strictly defined as `debit - credit`.
- Never create or leave unbalanced journal entries in the posted state.

### 2. Immutability of Posted Entries & Audit Trail (SOX / IFRS Compliance)
- Once a journal entry is posted (`state == 'posted'`), it becomes an immutable legal record.
- **Never delete or directly update posted entries**.
- Corrections must always be made by creating a reversing entry or credit note (`account.move.reversal`).
- Deleting accounting data or resetting posted moves silently without trace corrupts the audit trail and violates statutory compliance.

### 3. Account Types Reference (`account_type`)
In modern Odoo (v17, v18, v19), the legacy `user_type_id` is obsolete. Account classification uses the `account_type` Selection field with standardized financial categories:

| Category | `account_type` Technical Value | Description / Typical Use |
|---|---|---|
| **Balance Sheet: Assets** | `asset_receivable` | Accounts Receivable (Debtors) - `reconcile=True` |
| | `asset_cash` | Bank and Cash liquid accounts |
| | `asset_current` | Current assets, clearing accounts, inventory interim |
| | `asset_non_current` | Long-term tangible and intangible assets |
| | `asset_prepayments` | Prepaid expenses, advance deposits |
| | `asset_fixed` | Fixed assets subject to depreciation |
| **Balance Sheet: Liabilities** | `liability_payable` | Accounts Payable (Creditors) - `reconcile=True` |
| | `liability_credit_card` | Credit card liability accounts |
| | `liability_current` | Current liabilities, tax payable, short-term debt |
| | `liability_non_current` | Long-term debt and bonds |
| **Balance Sheet: Equity** | `equity` | Capital, owner investment |
| | `equity_unaffected` | Current Year Earnings / Retained Earnings (automated) |
| **Profit & Loss: Income** | `income` | Operating revenue / sales |
| | `income_other` | Non-operating income, interest, foreign exchange gain |
| **Profit & Loss: Expense** | `expense` | Operating expenses, overheads |
| | `expense_depreciation` | Depreciation and amortization expenses |
| | `expense_direct_cost` | Cost of Goods Sold (COGS) |
| | `expense_other` | Non-operating expenses, bank charges, financial losses (v19+) |
| **Off-Balance** | `off_balance` | Off-balance sheet commitments |

> **Warning against Hallucination**: Never query `user_type_id` or search using legacy strings (`'receivable'`, `'payable'`, `'liquidity'`). Always search using the modern `account_type` strings above.

### 4. Multi-Currency Accounting (IAS 21)
- `debit` and `credit` are ALWAYS denominated in the company's functional currency (`company_id.currency_id`).
- When a transaction occurs in a foreign currency:
  - `currency_id`: Points to the foreign transaction currency.
  - `amount_currency`: Stores the amount in the foreign currency (signed: positive for debit, negative for credit).
- Odoo automatically records Foreign Exchange Gain/Loss (`exchange_move_id`) during reconciliation when payment exchange rates differ from invoice exchange rates.

### 5. Period Lock Dates & Fiscal Closing
- Companies set `fiscalyear_lock_date` and `tax_lock_date` on `res.company`.
- Any attempt to post, unpost, or alter a journal entry on or before a lock date will raise an exception. Never bypass lock dates.

### 6. Two-Step Payment Processing & Bank Reconciliation
- When registering a payment via `account.payment`, Odoo does not post directly to the main Bank ledger. Instead, it posts to an **Outstanding Account** (`outstanding_receipts_account_id` or `outstanding_payments_account_id`).
- When the bank statement is imported or fetched (`account.bank.statement.line`), bank reconciliation matches the statement line against the outstanding payment line, clearing the outstanding balance into the true bank account.

### 7. Perpetual Inventory Valuation (IAS 2)
- When automated valuation is enabled (`property_valuation == 'real_time'` via `stock_account`):
  - Goods Receipt: Debits Stock Interim Received (`asset_current`), Credits Stock Valuation (`asset_current`).
  - Vendor Bill: Debits Stock Interim Received, Credits Accounts Payable (`liability_payable`).
  - Goods Delivery: Debits Cost of Goods Sold (`expense_direct_cost`), Credits Stock Valuation (`asset_current`).
  - Customer Invoice: Debits Accounts Receivable (`asset_receivable`), Credits Revenue (`income`).

### 8. Strict Rule: Never Mutate Financial Ledgers via Raw SQL
- Never execute raw SQL `UPDATE` or `DELETE` statements on `account_move` or `account_move_line`.
- Doing so bypasses tax recomputation, balance checks, currency conversions, partner ledger caches, and lock date validations, irrecoverably corrupting the financial database.

---

## Journal Entries

### Create Journal Entry
```python
from odoo import api, fields, models
from odoo.fields import Command
from odoo.exceptions import UserError


class AccountingMixin(models.AbstractModel):
    _name = 'accounting.mixin'
    _description = 'Accounting Mixin'

    def _create_journal_entry(self, lines, journal=None, ref=None, date=None):
        """Create a balanced journal entry with multiple lines.

        Args:
            lines: List of dicts with account_id, debit, credit, partner_id
            journal: account.journal record (optional)
            ref: Reference string
            date: Entry date (defaults to today)

        Returns:
            account.move record
        """
        if not journal:
            journal = self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.env.company.id),
            ], limit=1)

        move_vals = {
            'journal_id': journal.id,
            'date': date or fields.Date.today(),
            'ref': ref or self.name,
            'line_ids': [Command.create({
                'account_id': line['account_id'],
                'partner_id': line.get('partner_id'),
                'name': line.get('name', ref or '/'),
                'debit': line.get('debit', 0.0),
                'credit': line.get('credit', 0.0),
            }) for line in lines],
        }

        move = self.env['account.move'].create(move_vals)
        return move

    def _post_journal_entry(self, lines, **kwargs):
        """Create and post journal entry."""
        move = self._create_journal_entry(lines, **kwargs)
        move.action_post()
        return move
```

### Balanced Entry Example
```python
def _create_expense_entry(self, amount, expense_account, description):
    """Create expense journal entry adhering to double-entry bookkeeping."""
    bank_account = self.env['account.account'].search([
        ('account_type', '=', 'asset_cash'),
        ('company_id', '=', self.env.company.id),
    ], limit=1)

    lines = [
        {
            'account_id': expense_account.id,
            'name': description,
            'debit': amount,
            'credit': 0.0,
        },
        {
            'account_id': bank_account.id,
            'name': description,
            'debit': 0.0,
            'credit': amount,
        },
    ]

    return self._post_journal_entry(lines, ref=description)
```

---

## Invoice Creation

### Customer Invoice
```python
def _create_customer_invoice(self, partner, lines, date=None):
    """Create customer invoice.

    Args:
        partner: res.partner record
        lines: List of dicts with product_id, quantity, price_unit, tax_ids
        date: Invoice date

    Returns:
        account.move record (invoice)
    """
    invoice_vals = {
        'move_type': 'out_invoice',
        'partner_id': partner.id,
        'invoice_date': date or fields.Date.today(),
        'invoice_line_ids': [Command.create({
            'product_id': line.get('product_id'),
            'name': line.get('name', line.get('product_id') and
                           self.env['product.product'].browse(line['product_id']).name),
            'quantity': line.get('quantity', 1),
            'price_unit': line['price_unit'],
            'tax_ids': [Command.set(line.get('tax_ids', []))],
        }) for line in lines],
    }

    invoice = self.env['account.move'].create(invoice_vals)
    return invoice


def _create_and_post_invoice(self, partner, lines, **kwargs):
    """Create and post customer invoice."""
    invoice = self._create_customer_invoice(partner, lines, **kwargs)
    invoice.action_post()
    return invoice
```

### Vendor Bill
```python
def _create_vendor_bill(self, partner, lines, date=None, ref=None):
    """Create vendor bill.

    Args:
        partner: res.partner (vendor)
        lines: List of dicts with product_id, quantity, price_unit
        date: Bill date
        ref: Vendor reference

    Returns:
        account.move record (bill)
    """
    bill_vals = {
        'move_type': 'in_invoice',
        'partner_id': partner.id,
        'invoice_date': date or fields.Date.today(),
        'ref': ref,
        'invoice_line_ids': [Command.create({
            'product_id': line.get('product_id'),
            'name': line.get('name', ''),
            'quantity': line.get('quantity', 1),
            'price_unit': line['price_unit'],
        }) for line in lines],
    }

    bill = self.env['account.move'].create(bill_vals)
    return bill
```

### Credit Note
```python
def _create_credit_note(self, invoice, reason=None):
    """Create credit note for an invoice.

    Args:
        invoice: Original account.move record
        reason: Reason for credit

    Returns:
        account.move record (credit note)
    """
    # Use the reversal wizard approach
    reversal_wizard = self.env['account.move.reversal'].with_context(
        active_model='account.move',
        active_ids=invoice.ids,
    ).create({
        'reason': reason or 'Credit Note',
        'refund_method': 'refund',  # 'refund', 'cancel', 'modify'
        'journal_id': invoice.journal_id.id,
    })

    result = reversal_wizard.reverse_moves()
    credit_note = self.env['account.move'].browse(result['res_id'])

    return credit_note
```

---

## Payment Processing

### Register Payment
```python
def _register_payment(self, invoice, amount=None, date=None, journal=None):
    """Register payment for an invoice.

    Args:
        invoice: account.move record
        amount: Payment amount (defaults to invoice amount)
        date: Payment date
        journal: Payment journal

    Returns:
        account.payment record
    """
    if not journal:
        journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

    payment_vals = {
        'payment_type': 'inbound' if invoice.move_type == 'out_invoice' else 'outbound',
        'partner_type': 'customer' if invoice.move_type in ['out_invoice', 'out_refund'] else 'supplier',
        'partner_id': invoice.partner_id.id,
        'amount': amount or invoice.amount_residual,
        'date': date or fields.Date.today(),
        'journal_id': journal.id,
        'ref': invoice.name,
    }

    payment = self.env['account.payment'].create(payment_vals)
    payment.action_post()

    # Reconcile with invoice
    lines_to_reconcile = (payment.move_id.line_ids + invoice.line_ids).filtered(
        lambda l: l.account_id.reconcile and not l.reconciled
    )
    lines_to_reconcile.reconcile()

    return payment
```

### Bulk Payment
```python
def _create_batch_payment(self, invoices, journal=None):
    """Create batch payment for multiple invoices.

    Args:
        invoices: account.move recordset

    Returns:
        account.payment record
    """
    if not invoices:
        raise UserError("No invoices to pay")

    # Group by partner
    partner = invoices[0].partner_id
    if any(inv.partner_id != partner for inv in invoices):
        raise UserError("All invoices must be for the same partner")

    total_amount = sum(invoices.mapped('amount_residual'))

    payment = self._register_payment(
        invoices[0],
        amount=total_amount,
        journal=journal,
    )

    # Reconcile all invoices
    for invoice in invoices[1:]:
        lines_to_reconcile = (payment.move_id.line_ids + invoice.line_ids).filtered(
            lambda l: l.account_id.reconcile and not l.reconciled
        )
        lines_to_reconcile.reconcile()

    return payment
```

---

## Account Queries

### Get Account by Type
```python
def _get_account(self, account_type, company=None):
    """Get account by type.

    Args:
        account_type: e.g., 'asset_receivable', 'liability_payable',
                     'expense', 'income', 'asset_cash'
    """
    company = company or self.env.company
    return self.env['account.account'].search([
        ('account_type', '=', account_type),
        ('company_id', '=', company.id),
    ], limit=1)


def _get_receivable_account(self):
    return self._get_account('asset_receivable')


def _get_payable_account(self):
    return self._get_account('liability_payable')


def _get_expense_account(self, product=None):
    if product and product.property_account_expense_id:
        return product.property_account_expense_id
    return self._get_account('expense')


def _get_income_account(self, product=None):
    if product and product.property_account_income_id:
        return product.property_account_income_id
    return self._get_account('income')
```

### Get Journal by Type
```python
def _get_journal(self, journal_type, company=None):
    """Get journal by type.

    Args:
        journal_type: 'sale', 'purchase', 'cash', 'bank', 'general'
    """
    company = company or self.env.company
    return self.env['account.journal'].search([
        ('type', '=', journal_type),
        ('company_id', '=', company.id),
    ], limit=1)
```

---

## Financial Reports & Audit Trails (Downstream Output)

In standard Odoo, all operational documents (Sales, Purchases, Inventory, POS) culminate in posted `account.move.line` records that drive the standard financial reports:

### 1. The Reporting Architecture (IFRS / GAAP)

| Report | Governing Accounts / Logic | Accounting Meaning |
|---|---|---|
| **Balance Sheet** | `account_type` in `asset_*`, `liability_*`, `equity*` | Statement of Financial Position: $\text{Assets} = \text{Liabilities} + \text{Equity}$. |
| **Profit and Loss (P&L)** | `account_type` in `income*`, `expense*` | Statement of Comprehensive Income: $\text{Revenues} - \text{COGS} - \text{Expenses} = \text{Net Profit}$. |
| **Trial Balance** | All accounts with posted movements | Invariant Check: $\sum \text{Debit} = \sum \text{Credit}$. Must balance to zero. |
| **General Ledger** | Chronological lines grouped by account | Complete, immutable audit trail of all posted journal entries. |
| **Partner Ledger** | Open & cleared lines on receivable/payable | Subledger tracking customer debits and vendor liabilities. |
| **Aged Receivables / Payables** | Unreconciled lines (`reconciled = False`) | Bucketed aging analysis based on `date_maturity` and `amount_residual`. |
| **Tax Report (VAT Return)** | Tax repartition lines and tax tags | Net Tax = Output VAT (Sales) - Input VAT (Purchases). |

### 2. Partner Balance Query (ORM Standard)
```python
def _get_partner_balance(self, partner, account_type='asset_receivable'):
    """Get partner balance for specific account type (ORM-based)."""
    account = self._get_account(account_type)
    lines = self.env['account.move.line'].search([
        ('partner_id', '=', partner.id),
        ('account_id', '=', account.id),
        ('parent_state', '=', 'posted'),
    ])
    return sum(lines.mapped('balance'))


def _get_customer_receivable(self, partner):
    """Get customer receivable balance."""
    return self._get_partner_balance(partner, 'asset_receivable')


def _get_vendor_payable(self, partner):
    """Get vendor payable balance."""
    return self._get_partner_balance(partner, 'liability_payable')
```

### 3. Account Balance Query
```python
def _get_account_balance(self, account, date_from=None, date_to=None):
    """Get account balance for date range."""
    domain = [
        ('account_id', '=', account.id),
        ('parent_state', '=', 'posted'),
    ]

    if date_from:
        domain.append(('date', '>=', date_from))
    if date_to:
        domain.append(('date', '<=', date_to))

    lines = self.env['account.move.line'].search(domain)
    return sum(lines.mapped('balance'))
```

### 4. Aged Receivables / Payables Analysis
```python
def _get_aged_receivables(self, partner=None):
    """Get aged receivables report data based on maturity dates."""
    today = fields.Date.today()
    periods = [
        ('0-30', 0, 30),
        ('31-60', 31, 60),
        ('61-90', 61, 90),
        ('90+', 91, 9999),
    ]

    domain = [
        ('account_id.account_type', '=', 'asset_receivable'),
        ('parent_state', '=', 'posted'),
        ('reconciled', '=', False),
    ]

    if partner:
        domain.append(('partner_id', '=', partner.id))

    lines = self.env['account.move.line'].search(domain)

    result = {period[0]: 0.0 for period in periods}

    for line in lines:
        # Aging is strictly calculated from the maturity date (due date)
        days = (today - line.date_maturity).days if line.date_maturity else 0
        for period_name, min_days, max_days in periods:
            if min_days <= days <= max_days:
                result[period_name] += line.amount_residual
                break

    return result
```

---

## Tax Handling

### Get Taxes
```python
def _get_sale_taxes(self, product=None):
    """Get applicable sale taxes."""
    if product:
        return product.taxes_id
    return self.env['account.tax'].search([
        ('type_tax_use', '=', 'sale'),
        ('company_id', '=', self.env.company.id),
    ])


def _get_purchase_taxes(self, product=None):
    """Get applicable purchase taxes."""
    if product:
        return product.supplier_taxes_id
    return self.env['account.tax'].search([
        ('type_tax_use', '=', 'purchase'),
        ('company_id', '=', self.env.company.id),
    ])
```

### Calculate Tax
```python
def _compute_tax_amount(self, amount, taxes, price_include=False):
    """Compute tax amount for given amount and taxes.

    Args:
        amount: Base amount
        taxes: account.tax recordset
        price_include: Whether amount includes tax

    Returns:
        dict with total, taxes breakdown
    """
    tax_results = taxes.compute_all(
        amount,
        currency=self.env.company.currency_id,
        quantity=1.0,
        product=None,
        partner=None,
        is_refund=False,
    )

    return {
        'total_included': tax_results['total_included'],
        'total_excluded': tax_results['total_excluded'],
        'taxes': tax_results['taxes'],
    }
```

---

## Reconciliation

### Auto Reconcile
```python
def _auto_reconcile_partner(self, partner):
    """Auto-reconcile partner's open items."""
    receivable_account = self._get_receivable_account()

    lines = self.env['account.move.line'].search([
        ('partner_id', '=', partner.id),
        ('account_id', '=', receivable_account.id),
        ('reconciled', '=', False),
        ('parent_state', '=', 'posted'),
    ])

    # Group by exact amount match
    by_amount = {}
    for line in lines:
        amount = abs(line.balance)
        if amount not in by_amount:
            by_amount[amount] = {'debit': [], 'credit': []}

        if line.balance > 0:
            by_amount[amount]['debit'].append(line)
        else:
            by_amount[amount]['credit'].append(line)

    # Reconcile matching amounts
    for amount, grouped in by_amount.items():
        if grouped['debit'] and grouped['credit']:
            to_reconcile = grouped['debit'][0] + grouped['credit'][0]
            to_reconcile.reconcile()
```

---

## Best Practices

1. **Always balance entries** - Debits must equal credits
2. **Use correct account types** - Receivable, payable, income, expense
3. **Post entries** - Draft entries don't affect financials
4. **Handle multi-currency** - Use currency conversion methods
5. **Respect fiscal year** - Check date restrictions
6. **Use proper journals** - Sales, purchase, bank, cash, general
7. **Reconcile regularly** - Match payments to invoices
8. **Multi-company aware** - Always filter by company
9. **Tax compliance** - Use correct tax accounts
10. **Audit trail** - Don't delete, use reversals
