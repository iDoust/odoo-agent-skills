# Odoo codebase indexer

Optional local indexer for Odoo models, fields, views, actions, menus, XML
IDs, dependencies, and references. It is useful for large Community,
Enterprise, Doodba, or custom-addon source trees.

Install with `uv sync` from this directory. The scripts read the source tree
and write a local SQLite index; they do not connect to an Odoo database.

See [`../SKILL.md`](../SKILL.md) for usage instructions and search examples.
