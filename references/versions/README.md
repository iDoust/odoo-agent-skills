# Odoo Version and Edition References

This directory provides version-specific behavior matrices, deltas, edition comparisons,
and official upstream branch tracking for **Odoo 17, 18, and 19**.

## Version Deltas

| Version | Reference | Highlights |
| :--- | :--- | :--- |
| Odoo 17 | [17.md](17.md) | OWL 2 updates, view modifier syntax (`invisible="expr"`), searchpanel |
| Odoo 18 | [18.md](18.md) | `<list>` view root tag, `is_storable=True`, `_search_display_name` |
| Odoo 19 | [19.md](19.md) | `type='jsonrpc'`, `models.Constraint`, `Domain` class, `env` cleanup |

## Edition & Source Architecture

| Topic | Reference | Summary |
| :--- | :--- | :--- |
| Community vs Enterprise | [editions.md](editions.md) | Licensing (LGPL-3 vs OEEL), module parity, Community alternatives |
| Upstream Source Matrix | [source-matrix.md](source-matrix.md) | GitHub branches, commit heads, addon counts across 17, 18, and 19 |

## Related Workflows

- Upgrade Planning: [`../../skills/odoo-upgrade/SKILL.md`](../../skills/odoo-upgrade/SKILL.md)
- Data Migrations: [`../migrations/common.md`](../migrations/common.md)
- Deprecation Scanner: [`../../scripts/scan_deprecations.py`](../../scripts/scan_deprecations.py)
