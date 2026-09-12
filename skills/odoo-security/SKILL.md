---
name: odoo-security
description: Design and audit Odoo 17, 18, and 19 access rights, record rules, groups, controllers, and data exposure.
---

# Odoo security

Use this workflow for security design or audit. Determine the target version,
edition, users, companies, entry points, and sensitive data before changing
permissions.

1. Inspect models, fields, inherited models, controllers, portal routes,
   attachments, exports, and scheduled jobs.
2. Review model access rights, groups, record rules, field groups, and company
   isolation together.
3. Trace every `sudo()` or equivalent elevated operation to its trust boundary.
4. Validate untrusted input and review raw SQL, file uploads, and external API
   payloads.
5. Add focused allowed and denied tests for each meaningful permission boundary.

Load `../../references/security/common.md` (and its sub-references:
`../../references/security/patterns.md`, `../../references/security/multi-company.md`,
`../../references/security/portal-access-patterns.md`) and the target version reference.
