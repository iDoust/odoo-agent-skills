# Integrations and API References

Shared patterns for exposing Odoo APIs, webhooks, portal endpoints,
external service integrations, and bulk data import/export workflows.

## Reference Index

| Topic | Reference | Summary |
| :--- | :--- | :--- |
| Web Controllers & Routes | [controllers.md](controllers.md) | HTTP controllers, `@http.route`, auth methods, CSRF, webhooks |
| External APIs & RPC | [external-api.md](external-api.md) | External client access via JSON-RPC, XML-RPC, and REST patterns |
| Import & Export | [import-export.md](import-export.md) | Bulk data loading, CSV/XLSX import via `base_import`, export formats |

## Key Rules

1. **Route Authentication**: Explicitly choose `auth='user'`, `auth='public'`, or `auth='api_key'`. Never leave sensitive routes unauthenticated.
2. **Version Compatibility**: In Odoo 19, use `type='jsonrpc'` instead of `type='json'`.
3. **Bulk Ingestion**: Use `load()` via `base_import` or batch ORM `create()` for performance; never loop individual record creates with external network calls inside transactions.

## Related Workflows

- General Development: [`../../skills/odoo-development/SKILL.md`](../../skills/odoo-development/SKILL.md)
- Security & Access Control: [`../security/common.md`](../security/common.md)
