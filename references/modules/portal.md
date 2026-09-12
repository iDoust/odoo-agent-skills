# Customer & Vendor Portal Architecture

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  PORTAL ARCHITECTURE & FINANCIAL TRANSACTION WORKFLOWS                       ║
║  Customer portal, e-signatures, online payments, invoice downloads,          ║
║  and end-to-end accounting reconciliation in Odoo 17, 18, and 19             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

The Odoo Portal framework provides authenticated or token-secured external access for customers, vendors, and partners. Treat every portal route, token, and download path as a strict data-exposure and financial boundary.

---

## 1. Hulu ke Hilir: Order-to-Cash (O2C) in Portal

The customer portal is the primary digital touchpoint connecting external clients to upstream sales orders and downstream statutory accounting:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CUSTOMER PORTAL WORKFLOW                              │
│                                                                             │
│ 1. UPSTREAM: Quote Access & Verification                                    │
│    Customer views quote (/my/orders/<id>?access_token=...)                  │
│    Verifies products, quantities, pricelist discounts, and statutory taxes. │
│                                                                             │
│ 2. CONTRACT FORMATION: Online E-Signature (IFRS 15)                         │
│    Customer draws or types electronic signature.                            │
│    POST /my/orders/<id>/accept -> Calls order.action_confirm()              │
│    Quote transitions from 'sent' to 'sale'.                                 │
│                                                                             │
│ 3. PAYMENT: Online Payment Transaction                                      │
│    Customer clicks "Pay Now" -> payment.transaction created.                │
│    Processed via Payment Provider (Stripe, Adyen, PayPal, Wire Transfer).   │
│                                                                             │
│ 4. MIDSTREAM ACCOUNTING: Payment Posting                                    │
│    Transaction status transitions to 'done'.                                │
│    Creates and posts account.payment:                                       │
│    Dr. Outstanding Receipts / Payment Acquirer Clearing (Asset)             │
│    Cr. Customer Advance Liability / Accounts Receivable                     │
│                                                                             │
│ 5. DOWNSTREAM: Invoice Generation & Reconciliation                          │
│    Order generates invoice (account.move) upon delivery or payment term.    │
│    Invoice lines recognize revenue under IFRS 15:                           │
│    Dr. Accounts Receivable (Asset)                                          │
│    Cr. Product Sales Revenue (Income)                                       │
│    Cr. VAT / Sales Tax Payable (Liability)                                  │
│    Automated reconciliation matches account.payment against invoice.        │
│    Invoice status marks 'In Payment' or 'Paid'.                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Portal Controller Implementation

Custom modules extending the portal inherit from `CustomerPortal`:

```python
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class CustomPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """Inject document counter badge into the portal home dashboard."""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'my_doc_count' in counters:
            values['my_doc_count'] = request.env['custom.document'].search_count([
                ('partner_id', '=', partner.id),
            ])
        return values

    @http.route(['/my/documents', '/my/documents/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_documents(self, page=1, sortby=None, **kw):
        """List documents with pagination and partner security filtering."""
        partner = request.env.user.partner_id
        CustomDoc = request.env['custom.document']

        domain = [('partner_id', '=', partner.id)]

        # Searchbar sorting
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'date desc'},
            'name': {'label': 'Reference', 'order': 'name'},
        }
        sortby = sortby or 'date'
        order = searchbar_sortings[sortby]['order']

        doc_count = CustomDoc.search_count(domain)
        pager = portal_pager(
            url='/my/documents',
            total=doc_count,
            page=page,
            step=10,
        )

        documents = CustomDoc.search(
            domain,
            order=order,
            limit=10,
            offset=pager['offset'],
        )

        values = {
            'documents': documents,
            'page_name': 'my_documents',
            'pager': pager,
            'default_url': '/my/documents',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        }
        return request.render('my_module.portal_my_documents_template', values)

    @http.route(['/my/documents/<int:doc_id>'], type='http', auth='public', website=True)
    def portal_document_detail(self, doc_id, access_token=None, **kw):
        """Secure detail view with token validation (IDOR prevention)."""
        try:
            doc_sudo = self._document_check_access('custom.document', doc_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'doc': doc_sudo,
            'token': access_token,
            'page_name': 'document_detail',
        }
        return request.render('my_module.portal_document_detail_template', values)
```

---

## 3. The `portal.mixin` Contract

Models that expose records to external clients should inherit `portal.mixin`:

```python
from odoo import api, fields, models


class CustomDocument(models.Model):
    _name = 'custom.document'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = 'Portal Accessible Document'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', required=True)
    date = fields.Date(default=fields.Date.context_today)

    def _compute_access_url(self):
        """Generate canonical portal URL."""
        super()._compute_access_url()
        for record in self:
            record.access_url = f'/my/documents/{record.id}'

    def _get_portal_return_action(self):
        """Return window action when navigating back from portal."""
        self.ensure_one()
        return self.env.ref('my_module.action_custom_document')
```

---

## 4. Online Payment Integration & Accounting Verification

When accepting payments through the portal (e.g. for sales orders or invoices):

### Payment Transaction Hook
```python
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _post_process(self):
        """Post-process payment and trigger downstream invoice reconciliation."""
        super()._post_process()
        for tx in self:
            if tx.state == 'done' and tx.sale_order_ids:
                for order in tx.sale_order_ids:
                    # Confirm order if still in draft/sent
                    if order.state in ['draft', 'sent']:
                        order.action_confirm()

                    # Auto-reconcile invoices linked to this transaction
                    invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.payment_state == 'not_paid')
                    for invoice in invoices:
                        # Reconcile outstanding receipt with invoice receivable
                        tx._reconcile_after_done()
```

### Statutory Invariants for Portal Payments
1. **Never mutate accounting states in portal routes**: The controller must only invoke standard business workflows (`action_post()`, `action_confirm()`, `tx._set_done()`).
2. **Dedicated Clearing Journals**: Online payments must land in an intermediary bank/clearing journal (`account.journal` type `'bank'`), NEVER directly into the main cash drawer or unmonitored general ledger accounts.
3. **Reconciliation Traceability**: Any payment initiated from the portal leaves an immutable audit trail (`account.payment` linked to `payment.transaction` linked to `account.move` receivable line via `account.partial.reconcile`).

---

## 5. Security Checklist for Portal

- [ ] **IDOR Protection**: Always validate records using `_document_check_access()` rather than bare `browse(id)` or `sudo()`.
- [ ] **CSRF Protection**: All form submissions (especially signatures and payment clicks) must specify `csrf=True` (or leave default `True`).
- [ ] **Data Minimization**: Never expose internal chatter messages (e.g., messages with `subtype_id.internal = True`) in customer portal views.
- [ ] **Download Protection**: Binary attachments served to portal users must verify partner ownership or valid HMAC `access_token`.
- [ ] **Currency & Pricing Accuracy**: Displayed amounts in the portal must include statutory taxes according to customer fiscal position and currency formatting.
