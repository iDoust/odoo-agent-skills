---
name: odoo-token-killer
description: Optionally compact noisy Odoo development command output with a local CLI before it reaches an agent context.
---

# Odoo output optimizer

This optional skill provides the `otk` CLI. It is explicit and vendor-neutral:
there is no automatic tool hook or agent-specific interception. Use it only
for trusted local commands whose output is safe to summarize.

## Build and install

The Rust CLI lives under `core/` and requires a Rust toolchain:

```bash
cargo test --manifest-path skills/odoo-token-killer/core/Cargo.toml
cargo install --path skills/odoo-token-killer/core
```

## Explicit usage

```bash
otk test invoke test my_module
otk logs docker compose logs odoo
otk git status
otk read addons/sale/models/sale_order.py
otk gain
```

The command wraps trusted shell arguments and preserves the underlying exit
status. It supports compact filters for tests, logs, Python/XML reads, Git,
search, directory listings, Docker, package commands, SQL, and passthrough.

## Data safety

The CLI may record command metrics and save large raw outputs in its local tee
directory so they can be recovered. Do not pass secrets in commands or use it
on output containing credentials, tokens, or sensitive production data. Set
`OTK_TEE=0` when raw-output recovery is not appropriate and review
`OTK_TEE_DIR`, `OTK_DB_PATH`, and retention settings before use.

This optimizer is independent of Odoo correctness, security, or tests. It is
never a substitute for reading full output when diagnosing a failure.
