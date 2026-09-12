# Odoo module references

These references describe common extension patterns. Always inspect the exact
Community and Enterprise source for the target version before copying a model,
view, security rule, or workflow.

## Domain References

| Area | Reference | Community entry point |
| --- | --- | --- |
| Accounting | [accounting.md](accounting.md) | `addons/account` |
| Inventory | [inventory.md](inventory.md) | `addons/stock` |
| Purchase | [purchase.md](purchase.md) | `addons/purchase` |
| Sales and CRM | [sales.md](sales.md) | `addons/sale`, `addons/crm` |
| Manufacturing | [manufacturing.md](manufacturing.md) | `addons/mrp` |
| Point of Sale | [pos.md](pos.md) | `addons/point_of_sale` |
| Website | [website.md](website.md) | `addons/website` |
| Portal | [portal.md](portal.md) | `addons/portal` |
| HR | [hr.md](hr.md) | `addons/hr` |
| Project | [project.md](project.md) | `addons/project` |
| Products | [products.md](products.md) | `addons/product` |
| Pricing | [pricing.md](pricing.md) | `addons/product`, `addons/sale` |
| Tax | [tax.md](tax.md) | `addons/account` |
| Units of Measure | [uom.md](uom.md) | `addons/uom` |
| Lot and Serial Numbers | [lot-serial.md](lot-serial.md) | `addons/stock` |

## Architecture & Patterns

| Area | Reference |
| --- | --- |
| Module Structure | [module-structure.md](module-structure.md) |
| Dashboard and KPI Patterns | [dashboard-kpi-patterns.md](dashboard-kpi-patterns.md) |
| Module Generation Templates | [templates.md](templates.md) |
| Full Generation Example | [generation-example.md](generation-example.md) |
| CE for Enterprise Features | [community-enterprise-solutions.md](community-enterprise-solutions.md) |

Enterprise extensions are under `addons_enterprise` in local checkouts and the
matching branch in the official Enterprise repository. See
[../versions/source-matrix.md](../versions/source-matrix.md) for the version and edition matrix.
