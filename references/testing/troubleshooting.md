# Odoo debugging reference

## Request & Defect Intake Triad

Frame every user request, bug report, or issue into three explicit parts before diagnosing:

1. **User Problem**: The business goal, context, or what the user is trying to accomplish.
2. **Current Condition / Actual Behavior**: What is currently happening (exact traceback, wrong calculation, missing field, or blocked action).
3. **Expected Result**: The observable desired outcome, expected data state, or clean transition.

## Diagnostic Classification

Classify the failure before choosing a fix:

- server traceback or RPC error: read the complete Python traceback and locate
  the first project-owned frame;
- module installation or upgrade: validate manifest order, dependencies, XML,
  access data, and registry loading;
- XML parsing or view validation: inspect the inherited architecture and the
  target version's view schema;
- access error: trace model access, record rules, user groups, companies, and
  elevated access;
- frontend or OWL error: inspect the browser console, asset bundle, registry,
  service, component lifecycle, and RPC response;
- database or performance error: inspect the query, indexes, flush state,
  transaction boundary, and query count.

Always separate the transport symptom from the root exception. Inspect all
callers of a shared method before adding a guard, and leave one focused
reproduction or regression test behind.

## Related References

- [Shared Testing Baseline](common.md)
- [Master Testing Handbook](odoo.md)
- [QA / SIT Test Planning](qa-plan.md)
- [Debugging Workflow](../../skills/odoo-debug/SKILL.md)
- [Interactive Shell & Diagnostics](../operations/cli-and-shell.md)
