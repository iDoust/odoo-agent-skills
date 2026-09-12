# ORM shared baseline

This is the shared ORM baseline for Odoo 17–19. It is intentionally concise;
load the target version reference and inspect the project source for details.

## Models and recordsets

- Define the model name and description deliberately.
- Treat model methods as recordset methods unless the API contract says
  otherwise; handle empty, singleton, and multi-record inputs explicitly.
- Use recordset operations and ORM queries before writing SQL.
- Preserve batch semantics for `create`, `write`, and `unlink` overrides.
- Use model and field inheritance to extend existing behavior; call `super()`
  unless replacing the behavior is intentional.

## Fields and computed values

- Declare relational fields with the correct inverse, deletion behavior, and
  company checks where the business rule requires them.
- A computed field needs complete dependencies. Add `store=True` only when
  search, grouping, or persistence requires it.
- Use constraints for invariants that must hold regardless of the UI path.
  Treat `onchange` as a form convenience, not as validation.
- Use the command API for x2many updates when the target version and existing
  project conventions support it.

## Environment and security

- Respect the current environment, user, companies, language, and context.
- Use elevated access only around the smallest operation that requires it and
  document why it is safe.
- Do not use raw SQL to bypass ORM access rules. If SQL is necessary, use the
  parameterized API supported by the target version and preserve cache and
  flush semantics.

## Key References

| Topic | Reference |
| :--- | :--- |
| Standard Mixins (`mail.thread`, `image.mixin`, `utm.mixin`, etc.) | [mixins.md](mixins.md) |
| Model & View Inheritance | [inheritance-patterns.md](inheritance-patterns.md) |
| Computed & Related Fields | [computed-field-patterns.md](computed-field-patterns.md) |
| Field Type Reference | [field-type-reference.md](field-type-reference.md) |
| Constraints & Validations | [constraint-patterns.md](constraint-patterns.md) |
| Context & Environment | [context-environment-patterns.md](context-environment-patterns.md) |
| Domain Filters | [domain-filter-patterns.md](domain-filter-patterns.md) |
| Transient Models & Wizards | [wizard-patterns.md](wizard-patterns.md) |
| Workflow & State Machines | [workflow-state-patterns.md](workflow-state-patterns.md) |
| Onchange & Dynamic Domains | [onchange-dynamic-patterns.md](onchange-dynamic-patterns.md) |
| Sequences & Numbering | [sequence-numbering-patterns.md](sequence-numbering-patterns.md) |
| Attachments & Binaries | [attachment-binary-patterns.md](attachment-binary-patterns.md) |
| Configuration Settings | [config-settings-patterns.md](config-settings-patterns.md) |
| Error Handling | [error-handling-patterns.md](error-handling-patterns.md) |

## Sources

- Odoo 17 ORM reference: https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html
- Odoo 18 ORM reference: https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html
- Odoo 19 ORM reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html
