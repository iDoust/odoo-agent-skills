---
name: odoo-doodba
description: Index and operate on Odoo codebases managed with Doodba, Docker, or similar local development environments.
---

# Odoo Doodba tooling

Use this optional skill when the project uses Doodba or when a local Odoo
source tree needs fast structural search. It is not required for ordinary
Odoo development.

## Detect the environment

Before running setup commands, inspect the project for `tasks.py`, Docker
Compose files, an Odoo source checkout, and the project's documented test
runner. Do not install tools or start containers automatically.

The indexer accepts an explicit source path through `ODOO_PATH`. It can also
use the project layout detected by its configuration module. Its SQLite index
defaults to `~/.odoo-indexer/odoo_indexer.sqlite3`; set `SQLITE_DB_PATH` to
place it elsewhere.

## Index a codebase

The indexer is an optional Python project under [`indexer/`](indexer/README.md) and requires `uv`.
From the repository root:

```bash
uv sync --project skills/odoo-doodba/indexer
uv run --project skills/odoo-doodba/indexer python \
  skills/odoo-doodba/indexer/scripts/update_index.py --full
```

Use it only after confirming the source path and index location. The index is
local development data; it must not contain production credentials.

## Useful searches

```bash
uv run --project skills/odoo-doodba/indexer python \
  skills/odoo-doodba/indexer/scripts/search.py sale.order --type model
uv run --project skills/odoo-doodba/indexer python \
  skills/odoo-doodba/indexer/scripts/get_details.py model sale.order
uv run --project skills/odoo-doodba/indexer python \
  skills/odoo-doodba/indexer/scripts/list_modules.py
uv run --project skills/odoo-doodba/indexer python \
  skills/odoo-doodba/indexer/scripts/module_stats.py sale
```

## Doodba test execution

Use the project's own documented Doodba task, normally after inspecting its
arguments and environment:

```bash
invoke test --help
```

Run the narrowest module test that proves the requested behavior. Docker,
`invoke`, and Doodba remain optional project tools rather than dependencies
of the universal Odoo references.
