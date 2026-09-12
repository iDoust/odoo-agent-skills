---
name: odoo-test
description: Plan and run focused Odoo 17, 18, and 19 tests for business logic, security, XML, controllers, frontend behavior, and upgrades.
---

# Odoo testing

Use this workflow when authoring, running, or diagnosing automated tests across **Odoo 17, 18, and 19**.

## 1. Test Layer Decision Matrix

Select the narrowest test layer that proves the requested behavior:

| Target Boundary | Framework / Base Class | Version Coverage | Speed | Key Helpers |
| :--- | :--- | :--- | :--- | :--- |
| **Model & Business Logic** | `TransactionCase` | 17, 18, 19 | Fast | `assertRecordValues`, `assertQueryCount`, `RecordCapturer`, `self.patch` |
| **Form Views & Onchange** | `odoo.tests.Form` | 17, 18, 19 | Fast | `with Form(record) as f:`, `f.line_ids.new()`, `f.save()` |
| **Security & Permissions** | `TransactionCase` | 17, 18, 19 | Fast | `new_test_user`, `@users`, `with_user`, `with_company` |
| **Controllers & JSON-RPC** | `HttpCase` | 17, 18, 19 | Medium | `url_open`, `make_jsonrpc_request`, `authenticate` |
| **E2E Browser Tours** | `HttpCase.start_tour` | 17, 18, 19 | Slow | `browser_js`, tour definitions |
| **Frontend OWL Components** | **HOOT** (`@odoo/hoot`) | **18, 19** | Fast | `mountView`, `onRpc`, `expect.step`, `expect.verifySteps` |
| **Frontend OWL Components** | **QUnit** (`@web/../tests`) | **17** | Fast | `makeTestEnv`, `mount`, `getFixture`, `assert.containsOnce` |

---

## 2. Test Execution Commands

### A. Focused CLI Execution

Run only the exact test class or method being developed to maintain sub-second feedback:

```bash
# 1. Run single test method (fastest)
python3 odoo-bin -d testdb -c /etc/odoo.conf --test-enable \
    --test-tags=/my_module:TestOrder.test_confirm_order --stop-after-init --no-http

# 2. Run single test class
python3 odoo-bin -d testdb -c /etc/odoo.conf --test-enable \
    --test-tags=/my_module:TestOrder --stop-after-init --no-http

# 3. Run all post_install tests in module
python3 odoo-bin -d testdb -c /etc/odoo.conf --test-enable \
    --test-tags=/my_module,post_install,-at_install --stop-after-init
```

### B. Interactive Fast-Loop in Shell (`odoo.tests.shell`)

Eliminate server reboot time by executing test suites directly from inside `odoo shell`:

```python
# In odoo shell (python3 odoo-bin shell -d testdb -c /etc/odoo.conf)
from odoo.tests.shell import run_tests

# Run test class with hot code reloading (reloads test files modified on disk!)
run_tests(env, test_tags='/my_module:TestOrder', reload_tests=True)
```

---

## 3. Implementation Workflow

1. **State the Target Contract**: Name the exact behavior, input boundary, and expected failure condition before writing code.
2. **Write the Failing Test First (TDD)**: When fixing a bug, write the regression test reproducing the issue first; confirm it fails for the right reason.
3. **Use Modern ORM Syntax**: Always use `from odoo import Command; Command.create(...)` for x2many fields. Never use legacy integer command tuples.
4. **Enforce Financial and State Integrity**:
   - For accounting entries, assert strict `debit == credit` equality.
   - Assert that posted journal entries and confirmed records cannot be modified or deleted.
5. **Silence Expected Log Exceptions**: Wrap deliberate error triggers in `with mute_logger('odoo.sql_db', 'odoo.addons.base'):` so test logs remain clean.
6. **Guard Against Silent Rollback in Shell**: Remember that `odoo shell` rolls back transactions by default; in automated test cases, `TransactionCase` isolates each method with a savepoint.

---

## 4. Troubleshooting and Diagnostics

- **Traceback frame isolation**: Skip framework frames; inspect the first frame inside your custom module.
- **Uncaught SQL exception**: An uncaught PostgreSQL error breaks the cursor. In shell or custom scripts, wrap negative checks in `with env.cr.savepoint():`.
- **Query Count Regressions**: Wrap operations in `with self.assertQueryCount(expected_count):` to prevent N+1 queries.
- **Assertion Integrity**: Never weaken assertions or suppress test failures to achieve green builds.

---

## References to Load

- Master testing handbook: `../../references/testing/odoo.md`
- High-level test planning and QA matrix: `../../references/testing/qa-plan.md`
- Shared testing baseline: `../../references/testing/common.md`
- Interactive REPL and CLI operations: `../../references/operations/cli-and-shell.md`
- Deployment and Definition of Done: `../../references/operations/deployment.md`

