# Odoo source matrix

Use the matching Community and Enterprise source trees when a rule depends on
the installed edition or version. Enterprise modules extend Community models;
never infer their behavior from Community code alone.

| Version | Community source | Enterprise source |
| --- | --- | --- |
| 17 | `https://github.com/odoo/odoo/tree/17.0` | `https://github.com/odoo/enterprise/tree/17.0` |
| 18 | `https://github.com/odoo/odoo/tree/18.0` | `https://github.com/odoo/enterprise/tree/18.0` |
| 19 | `https://github.com/odoo/odoo/tree/19.0` | `https://github.com/odoo/enterprise/tree/19.0` |

The official Enterprise branch names were checked read-only on 2026-08-14:

| Branch | Remote head checked |
| --- | --- |
| `17.0` | `4386d661606f6a13e57fe66db55d2175a947b754` |
| `18.0` | `31dc6517c2fce9a787424035f64ab1786d57d5e9` |
| `19.0` | `15a4b4e10c3547f988e5b2ba754e90da45166e38` |

For a local checkout, inspect `<odoo-root>/odoo/release.py`, Community addons
under `<odoo-root>/addons`, and Enterprise addons under
`<odoo-root>/addons_enterprise`. The checked local trees currently contain the
following Community addon counts:

| Version | Community manifests | Enterprise manifests |
| --- | ---: | ---: |
| 17 | 578 | 1,195 |
| 18 | 625 | 1,252 |
| 19 | 620 | 1,358 |

High-value domain entry points exist in all three Community trees:
`account`, `stock`, `purchase`, `sale`, `mrp`, `point_of_sale`, `website`, and
`portal`. Enterprise coverage is version-specific; search the matching
`addons_enterprise` tree for extensions such as `account_reports`,
`documents`, `hr_payroll`, `helpdesk`, and `quality`.

The local checkout `.git` directories are empty metadata directories, so
branch and remote state was not inferred from them. Use the explicit source
paths and the matching upstream branch URLs above when a branch comparison is
needed. Enterprise source access may require an active Odoo Enterprise
subscription and linked GitHub account.

## Related References

- [Odoo 17 Version Reference](17.md)
- [Odoo 18 Version Reference](18.md)
- [Odoo 19 Version Reference](19.md)
- [Odoo Editions: Community vs Enterprise](editions.md)
- [Versions Directory Index](README.md)
