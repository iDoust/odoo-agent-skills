# Security shared baseline

Security is part of the model contract, not a final UI-only step.

## Review order

1. Identify the users and companies that must access the model.
2. Define groups and model access rights with least privilege.
3. Add record rules for row-level isolation and test both allowed and denied
   cases.
4. Review field groups, related fields, computed values, exports, controllers,
   portal routes, and attachments for unintended disclosure.
5. Review every use of elevated access, context flags, and raw SQL.

Record rules do not replace model access rights, and hiding a field or button
does not enforce server-side authorization. Test permissions through the same
entry point the user will use.

## Multi-company behavior

Explicitly test cross-company reads, creates, writes, relational fields, and
scheduled jobs. Use the target version's company-check mechanisms together with
record rules; do not assume a field is isolated merely because it has a
`company_id`.

## Key References

| Topic | Reference |
| :--- | :--- |
| Security Design Patterns | [patterns.md](patterns.md) |
| Multi-Company Isolation | [multi-company.md](multi-company.md) |
| Portal Access Patterns | [portal-access-patterns.md](portal-access-patterns.md) |

## Sources

- Odoo 17 security reference: https://www.odoo.com/documentation/17.0/developer/reference/backend/security.html
- Odoo 18 security reference: https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html
- Odoo 19 security reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/security.html
