---
name: odoo-query
description: Inspect an Odoo instance through a read-only XML-RPC client when source inspection cannot answer a debugging or data question.
---

# Odoo read-only query

Use this optional skill only when the user has supplied an authorized Odoo
endpoint and the answer requires live instance data. Prefer local source,
tests, logs, and database tools already documented by the project first.

The client allows only read-oriented methods: `search`, `search_read`, `read`,
`fields_get`, `search_count`, `name_get`, `name_search`, `default_get`, and
access-check methods. It never provides create, write, unlink, or arbitrary
method execution.

## Security boundary

- Use HTTPS for non-local endpoints; plaintext HTTP is accepted only for local
  development addresses.
- Use an API key rather than a user password when the target supports it.
- Never commit, print, or paste credentials into source files or issue logs.
- Treat returned records as sensitive data and request the smallest fields,
  domain, and limit needed.
- Verify the database, user, company context, and target environment before
  querying.

## Usage

The standard-library client is at `scripts/odoo_xmlrpc.py`:

```bash
python3 skills/odoo-query/scripts/odoo_xmlrpc.py \
  --url https://odoo.example.test \
  --db production \
  --login investigator@example.test \
  --action search_read \
  --model sale.order \
  --domain "[['state', '=', 'sale']]" \
  --fields name,partner_id,amount_total \
  --limit 20
```

Set `ODOO_API_KEY` in the process environment before running the command, or
pass `--api-key` explicitly for a one-off local invocation.

Available actions are `test`, `list_models`, `fields_get`, `search_read`,
`search_count`, `read`, `describe_model`, and `find_model`. Domains are parsed
with `ast.literal_eval`; they are data, not executable Python.

Use the result to confirm a hypothesis, then reproduce and fix the root cause
in the project code with a focused test. Live querying is investigation, not a
replacement for access-control tests or migration validation.
