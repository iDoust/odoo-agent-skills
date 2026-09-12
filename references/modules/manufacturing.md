# Manufacturing (MRP) Integration & Accounting Patterns

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  MANUFACTURING (MRP) INTEGRATION PATTERNS                                    ║
║  BOMs, production orders, work centers, WIP accounting, and costing          ║
║  Use for discrete manufacturing, assembly, batch jobs, and shop floor        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Module Setup

### Manifest Dependencies
```python
{
    'name': 'My Manufacturing Extension',
    'version': '18.0.1.0.0',
    'depends': ['mrp'],
    # Optional extensions: 'mrp_account' (WIP accounting), 'mrp_subcontracting'
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
}
```

---

## End-to-End Accounting Pipeline: Order-to-Manufacture (O2M)

Under international accounting standards (IAS 2 - Cost of Conversion), manufacturing transforms raw materials and direct labor/overheads into finished goods inventory:

```
[Bill of Materials (mrp.bom)]
        │
        ▼ action_confirm()
[Manufacturing Order (mrp.production)]
        │
        ▼ Raw Materials Consumption
Work in Progress (IAS 2)
Dr: Work in Progress (WIP) Account (asset_current)
Cr: Raw Materials Inventory Valuation (asset_current)
        │
        ▼ Work Center Operations & Labor (mrp.workorder)
Direct Labor & Overhead Absorption
Dr: Work in Progress (WIP) Account (asset_current)
Cr: Labor / Overhead Absorbed Account (expense)
        │
        ▼ button_mark_done()
Finished Goods Capitalization
Dr: Finished Goods Inventory Valuation (asset_current)
Cr: Work in Progress (WIP) Account (asset_current)
        │
        ▼
[Financial Reports: Balance Sheet (WIP & Finished Goods Assets), COGM]
```

---

## Extending Manufacturing Models

### 1. Extend Manufacturing Order (`mrp.production`)
```python
from odoo import api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_batch_code = fields.Char(string='Production Batch Code', copy=False, index=True)
    x_qa_inspector_id = fields.Many2one('res.users', string='QA Inspector')
    x_is_inspected = fields.Boolean(string='Quality Inspected', default=False)

    def button_mark_done(self):
        """Enforce QA inspection before completing production."""
        for order in self:
            if not order.x_is_inspected:
                raise UserError("Production order must be QA inspected before completion.")
        return super().button_mark_done()
```

### 2. Scrap Accounting Integration
When components or assemblies are scrapped during production:
- An entry is created via `stock.scrap`.
- Accounting entry (via `stock_account`):
  - **Debit**: **Scrap Expense / Factory Waste Account** (`expense`)
  - **Credit**: **Raw Materials / WIP Valuation Account** (`asset_current`)

---

## Best Practices

1. **Maintain WIP account equilibrium**: The WIP account must reconcile to zero upon order completion; unabsorbed balances reflect production variance.
2. **Do not bypass stock moves**: Never manipulate component quantities directly; always use `mrp.production.move_raw_ids` and `move_finished_ids`.
3. **Multi-company isolation**: Ensure BOMs, work centers, and production orders belong to the matching `company_id`.
4. **Lot/Serial traceability**: Use `lot_producing_id` to link finished goods to component serial numbers for full upstream/downstream recall capability.
5. **Costing accuracy**: When `mrp_account` is installed, define labor costs on `mrp.workcenter` (`costs_hour`) to properly capitalize labor into finished goods valuation.

---

## Sources

- Odoo 17 MRP: https://github.com/odoo/odoo/tree/17.0/addons/mrp
- Odoo 18 MRP: https://github.com/odoo/odoo/tree/18.0/addons/mrp
- Odoo 19 MRP: https://github.com/odoo/odoo/tree/19.0/addons/mrp
