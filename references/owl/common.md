# OWL and frontend shared baseline

Use this baseline for frontend work in Odoo 17–19, then inspect the target
version's frontend source, registries, services, assets, and existing module
patterns.

- Confirm the target Odoo version before choosing a component or service API.
- Reuse the existing registry, service, hook, and asset-bundle conventions.
- Keep component state local to the component that owns the behavior and clean
  up listeners, timers, and subscriptions when the component is destroyed.
- Treat frontend permissions as usability only; enforce authorization on the
  server and test the actual RPC or controller boundary.
- Avoid assuming that a frontend pattern from one Odoo version has the same
  lifecycle, props, or asset behavior in another version.

## Sources

- Odoo 17 frontend framework: https://www.odoo.com/documentation/17.0/developer/reference/frontend/framework_overview.html
- Odoo 18 frontend framework: https://www.odoo.com/documentation/18.0/developer/reference/frontend/framework_overview.html
- Odoo 19 frontend framework: https://www.odoo.com/documentation/19.0/developer/reference/frontend/framework_overview.html
