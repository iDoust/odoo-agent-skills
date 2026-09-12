# XML views shared baseline

Use this baseline for Odoo 17–19, then check the target version reference and
the actual inherited view before editing XML.

## View design

- Find the existing view and its inheritance chain before adding an XPath.
- Prefer a narrow, stable inheritance expression over copying a complete view.
- List view root tag: In Odoo 17 use `<tree>`; in Odoo 18+ use `<list>`. Target
  `//tree` or `//list` accordingly in inherited XPaths.
- Keep fields needed by expressions present in the view, even when hidden.
- Use XML IDs for actions, menus, groups, and references; avoid hard-coded
  database IDs.
- Keep business validation in Python constraints or model methods, not only in
  view modifiers.

## Modifiers and frontend behavior

For supported versions, view modifiers such as `invisible`, `readonly`, and
`required` use expressions evaluated in the view context. For table column
visibility in list/tree views, use `column_invisible` to hide both header and
cells. Verify the exact expression inputs and relational sub-view behavior in
the target documentation.

Do not copy legacy modifier syntax into new supported-version views. When
migrating an old view, treat every modifier as a version-specific change and
validate the resulting XML.

## Key References

| Topic | Reference |
| :--- | :--- |
| XML View Patterns (form, list, kanban, search, calendar) | [xml-view-patterns.md](xml-view-patterns.md) |
| Actions (window, server, URL, client) | [action-patterns.md](action-patterns.md) |
| Menu & Navigation | [menu-navigation-patterns.md](menu-navigation-patterns.md) |
| Field Widgets | [widgets.md](widgets.md) |
| QWeb Templates | [qweb-template-patterns.md](qweb-template-patterns.md) |
| PDF/HTML Reports | [report-patterns.md](report-patterns.md) |
| Asset Bundles | [assets.md](assets.md) |
| Translations & i18n | [translation-i18n-patterns.md](translation-i18n-patterns.md) |

## Sources

- Odoo 17 `invisible` attribute: https://www.odoo.com/documentation/17.0/developer/reference/user_interface/view_architectures/generic_attribute_invisible.html
- Odoo 18 view architecture: https://www.odoo.com/documentation/18.0/developer/reference/user_interface/view_architectures.html
- Odoo 19 view architecture: https://www.odoo.com/documentation/19.0/developer/reference/user_interface/view_architectures.html
