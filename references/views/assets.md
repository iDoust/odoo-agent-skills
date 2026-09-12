# Odoo assets baseline

Inspect the target module manifest and the matching `web` source before
changing assets.

- Declare JavaScript, styles, and templates in the appropriate manifest bundle.
- Keep bundle ownership and dependency order explicit.
- Use the target version's module syntax and import paths; do not copy paths
  from another Odoo branch without checking the source.
- Test with asset debugging enabled and verify both a clean load and a module
  upgrade.
- Keep public assets separate from backend assets and avoid shipping secrets or
  unnecessary libraries.

Sources:

- Odoo 17 assets reference: https://www.odoo.com/documentation/17.0/developer/reference/frontend/assets.html
- Odoo 18 assets reference: https://www.odoo.com/documentation/18.0/developer/reference/frontend/assets.html
- Odoo 19 assets reference: https://www.odoo.com/documentation/19.0/developer/reference/frontend/assets.html
