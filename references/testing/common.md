# Testing Shared Baseline (Odoo 17, 18, 19)

Core architectural rules, version deltas, and standard practices for writing and running automated tests in Odoo.

---

## 1. Multi-Version Testing Matrix

| Capability | Odoo 17 | Odoo 18 | Odoo 19 |
| :--- | :--- | :--- | :--- |
| **Backend Base Class** | `TransactionCase` (savepoint per test) | `TransactionCase` (savepoint per test) | `TransactionCase` (savepoint per test) |
| **Frontend Test Framework** | **QUnit** (`@web/../tests/helpers/utils`) | **HOOT** (`@odoo/hoot`) | **HOOT** (`@odoo/hoot`) |
| **UI Form Simulation** | `odoo.tests.Form` | `odoo.tests.Form` | `odoo.tests.Form` |
| **Interactive Shell Runner** | `odoo.tests.shell.run_tests` | `odoo.tests.shell.run_tests` | `odoo.tests.shell.run_tests` |
| **X2many Syntax** | `Command.create(...)` (no legacy tuples) | `Command.create(...)` (no legacy tuples) | `Command.create(...)` (no legacy tuples) |
| **Headless HTTP Testing** | `HttpCase.url_open`, `make_jsonrpc_request` | `HttpCase.url_open`, `make_jsonrpc_request` | `HttpCase.url_open`, `make_jsonrpc_request` |
| **Browser Tours** | `HttpCase.start_tour` | `HttpCase.start_tour` | `HttpCase.start_tour` |

---

## 2. Base Class Decision Tree

1. **`TransactionCase`**: The default choice for 95% of backend tests.
   - Wraps each test method in a savepoint that automatically rolls back when the method finishes.
   - Use for: model CRUD, computed field dependencies, Python/SQL constraints, ACLs, record rules, batch operations.
2. **`SingleTransactionCase`**:
   - Maintains a single open transaction across all test methods in the class, rolling back only in `tearDownClass`.
   - Use when testing sequential multi-stage workflows where subsequent tests depend on state produced by previous tests.
3. **`HttpCase`**:
   - Launches a real HTTP daemon and headless Chromium instance.
   - Use for: controller routes (`url_open`), JSON-RPC datasets (`make_jsonrpc_request`), authentication flows, and frontend browser tours (`start_tour`).
4. **`odoo.tests.Form`**:
   - Server-side form view simulation helper.
   - Automatically executes view onchanges, default values, and subview line manipulations (`with form.line_ids.new() as line:`).

---

## 3. Golden Rules of Odoo Testing

1. **Zero Legacy Tuples**: Never use deprecated integer command tuples. Always use the `Command` namespace (`Command.create()`, `Command.set()`, `Command.unlink()`).
2. **Test the Model Boundary First**: Before writing complex browser tours or controller tests, verify business logic, constraints, and computations at the ORM model level.
3. **Financial and Accounting Invariants**: Any business logic modifying journal entries (`account.move`) must assert:
   - Total Debit == Total Credit.
   - Posted entries cannot be edited or deleted without proper reversal.
4. **Multi-Company and Security Isolation**: When testing access-controlled models, test with regular non-admin users (`new_test_user`) and explicit company context (`with_company`).
5. **No Flaky Tests / Zero Unneeded Mocks**: Use real database fixtures provided by Odoo. Only mock external HTTP calls (third-party payment gateways, external APIs) using `self.patch` or `unittest.mock.patch`.
6. **Mute Expected Errors**: Use `mute_logger('odoo.sql_db')` when asserting that a constraint correctly raises an exception, keeping test logs free of distracting error traces.

---

## 4. Standard Test Execution Commands

```bash
# Run tests for a specific module
python3 odoo-bin -d testdb -c /etc/odoo.conf --test-enable --test-tags=/my_module --stop-after-init --no-http

# Run single test method
python3 odoo-bin -d testdb -c /etc/odoo.conf --test-enable --test-tags=/my_module:TestClass.test_method --stop-after-init --no-http

# Run tests interactively in shell with hot-reloading
python3 odoo-bin shell -d testdb -c /etc/odoo.conf
>>> from odoo.tests.shell import run_tests
>>> run_tests(env, test_tags='/my_module', reload_tests=True)
```

---

## Key References

| Topic | Reference |
| :--- | :--- |
| Master Testing Handbook | [odoo.md](odoo.md) |
| QA / SIT Test Planning | [qa-plan.md](qa-plan.md) |
| Troubleshooting Test Failures | [troubleshooting.md](troubleshooting.md) |

## Sources & Documentation

- Odoo 17 Testing Reference: https://www.odoo.com/documentation/17.0/developer/reference/backend/testing.html
- Odoo 18 Testing Reference: https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html
- Odoo 19 Testing Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html
