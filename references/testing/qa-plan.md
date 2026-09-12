# QA / SIT Test Planning for Odoo Modules

Guide for planning systematic QA and SIT (System Integration Testing) beyond
developer unit tests. Use this reference when preparing test plans, writing test
cases, or reviewing QA coverage for an Odoo module.

## Test Case Template

Every test case must follow a structured format so results are traceable and
reproducible.

```text
Test Case ID   : TC-{MODULE}-{SEQ}
Module         : {module_technical_name}
Feature        : {feature or user story}
Scenario       : {one-line description}
Preconditions  : {required data, user role, module state}
Steps          :
  1. {action}
  2. {action}
Expected Result: {observable outcome}
Actual Result  : {filled during execution}
Status         : PASS | FAIL | BLOCKED | SKIPPED
Evidence       : {screenshot / log / database record}
Tester         : {name}
Date           : {YYYY-MM-DD}
Severity       : Critical | Major | Minor | Trivial
```

## Test Categories

Every feature must be tested across four categories. Do not stop at the happy
path.

### 1. Normal / Happy Path

The standard business flow that users execute daily. Verify that every step
produces the expected state transition and data.

### 2. Negative Testing

Force every known error path. Verify that Odoo raises the correct exception
(`UserError`, `ValidationError`, `AccessError`) and that no partial data is
left behind.

Common negative scenarios:

- Required fields left empty or set to `False`.
- Invalid relational references (partner that does not exist, product archived).
- Action on wrong state (confirm a cancelled order, post a draft payment).
- Unauthorized user attempts (user without group tries restricted action).
- Duplicate creation where uniqueness is expected.
- Action on locked period (posting to a locked fiscal period).

### 3. Boundary Testing

Test the edges of valid input ranges. These are the values most likely to
trigger rounding errors, overflow, or unexpected behavior.

| Boundary | Examples |
| --- | --- |
| Zero values | Quantity 0, price 0, discount 0% |
| Maximum values | Quantity 999999999, amount at currency precision limit |
| 100% boundaries | Discount 100%, tax 100% |
| Negative where unexpected | Negative quantity on SO line, negative price |
| Precision limits | 0.001 quantity, 0.01 currency amount |
| Empty collections | Confirm order with zero lines, payment with no invoices |
| Date boundaries | Start date == end date, date in locked period, future date |
| Multi-currency edge | Same currency as company, rate exactly 1.0 |

### 4. Integration / Cross-Module Testing

Verify that the feature correctly propagates data to downstream modules.
Always test the full chain, not just the originating module.

#### Standard Integration Chains

```text
Sales Chain:
  sale.order → Confirm → stock.picking (Delivery) → account.move (Invoice)
  Verify: picking created, quantities match, invoice lines match SO lines,
  journal entry balanced (debit == credit), revenue account correct

Purchase Chain:
  purchase.order → Confirm → stock.picking (Receipt) → account.move (Bill)
  Verify: receipt created, quantities match, bill lines match PO lines,
  journal entry balanced, expense/asset account correct

Inventory Chain:
  stock.picking → Validate → stock.valuation.layer → account.move
  Verify: valuation layer created, accounting entries match valuation method
  (standard/average/FIFO), inventory account debited/credited correctly

Payment Chain:
  account.payment → Post → account.move (Payment Entry) → Reconciliation
  Verify: payment journal entry balanced, bank/cash account used,
  receivable/payable reconciled, outstanding balance updated

Manufacturing Chain:
  mrp.production → Confirm → Reserve → Produce → stock.move → account.move
  Verify: raw materials consumed, finished goods produced, valuation correct
```

#### Integration Test Verification Points

For each integration chain, always verify:

1. **Data Consistency**: quantities, amounts, dates, partners propagated.
2. **Accounting Balance**: `sum(debit) == sum(credit)` on every generated move.
3. **Account Type Correctness**: receivable, payable, income, expense, COGS
   accounts used per standard chart.
4. **State Propagation**: downstream records reflect correct state.
5. **Reversal / Cancellation**: cancelling upstream correctly reverses or voids
   downstream records.

### 5. Regression Testing

After any change, verify that existing flows still work. Regression scope
depends on the change:

| Change Type | Regression Scope |
| --- | --- |
| New field on existing model | All views that display the model, existing CRUD, existing reports |
| Modified compute/onchange | All fields that depend on it, all workflows that read the result |
| Changed access rights | All user roles that interact with the model |
| New workflow state | Full lifecycle of the existing states still works |
| View inheritance change | Parent and sibling inherited views still render |
| Modified constraint | Existing valid data still passes, existing create/write flows |
| API / controller change | All callers (portal, website, external integrations) |

## Coverage Matrix per Domain

Use the following matrix as a starting checklist for each Odoo domain. Mark
each cell as PASS, FAIL, BLOCKED, or N/A.

### Sales

| Test ID | Scenario | Normal | Negative | Boundary | Integration |
| --- | --- | --- | --- | --- | --- |
| TC-SALE-001 | Create quotation | | | | |
| TC-SALE-002 | Add/remove order lines | | | | |
| TC-SALE-003 | Apply discount | | | | |
| TC-SALE-004 | Apply tax | | | | |
| TC-SALE-005 | Confirm to sale order | | | | |
| TC-SALE-006 | Create delivery | | | | Sales → Stock |
| TC-SALE-007 | Create invoice | | | | Sales → Accounting |
| TC-SALE-008 | Partial delivery | | | | |
| TC-SALE-009 | Cancel sale order | | | | |
| TC-SALE-010 | Return / Credit Note | | | | |
| TC-SALE-011 | Multi-currency SO | | | | |
| TC-SALE-012 | Multi-company SO | | | | |
| TC-SALE-013 | Access rights (user/manager) | | | | |

### Purchase

| Test ID | Scenario | Normal | Negative | Boundary | Integration |
| --- | --- | --- | --- | --- | --- |
| TC-PUR-001 | Create RFQ | | | | |
| TC-PUR-002 | Confirm purchase order | | | | |
| TC-PUR-003 | Receive goods | | | | Purchase → Stock |
| TC-PUR-004 | Create vendor bill | | | | Purchase → Accounting |
| TC-PUR-005 | Partial receipt | | | | |
| TC-PUR-006 | Return to vendor | | | | |
| TC-PUR-007 | Cancel PO | | | | |
| TC-PUR-008 | Multi-currency PO | | | | |

### Accounting

| Test ID | Scenario | Normal | Negative | Boundary | Integration |
| --- | --- | --- | --- | --- | --- |
| TC-ACC-001 | Create journal entry | | | | |
| TC-ACC-002 | Post journal entry | | | | |
| TC-ACC-003 | Verify debit == credit | | | | |
| TC-ACC-004 | Register payment | | | | |
| TC-ACC-005 | Reconcile payment | | | | |
| TC-ACC-006 | Create credit note | | | | |
| TC-ACC-007 | Lock period enforcement | | | | |
| TC-ACC-008 | Multi-currency entry | | | | |
| TC-ACC-009 | Bank reconciliation | | | | |
| TC-ACC-010 | Tax computation | | | | |
| TC-ACC-011 | Immutability of posted | | | | |

### Inventory

| Test ID | Scenario | Normal | Negative | Boundary | Integration |
| --- | --- | --- | --- | --- | --- |
| TC-INV-001 | Internal transfer | | | | |
| TC-INV-002 | Delivery order | | | | Stock → Accounting |
| TC-INV-003 | Receipt | | | | Stock → Accounting |
| TC-INV-004 | Inventory adjustment | | | | Stock → Accounting |
| TC-INV-005 | Lot/serial tracking | | | | |
| TC-INV-006 | Scrap | | | | |
| TC-INV-007 | Return | | | | |

## UAT Scenario Generation

When generating UAT scenarios from acceptance criteria, follow this structure:

```text
UAT-{SEQ}
Scenario    : {business scenario in user language}
Actor       : {user role}
Precondition: {data state}
Steps       :
  1. {business action, not technical steps}
  2. {business action}
Expected    : {business outcome}
Pass/Fail   : {filled by client}
Notes       : {client feedback}
```

UAT tests business outcomes, not technical implementation. Use real-world
terminology and realistic data. Generate UAT scenarios from the Given/When/Then
acceptance criteria defined during the analysis phase.

---

## QA Roles: Manual vs. Automation

In Odoo/ERP projects, QA work divides into two complementary disciplines.
Neither replaces the other.

### QA Manual

Focuses on business process validation, exploratory testing, and scenarios
that require human judgment.

**When to use manual testing:**

- First-time execution of newly developed features.
- Exploratory testing to find unexpected behavior.
- UAT with end users (business process verification).
- UI/UX assessment (layout, flow, usability).
- Complex multi-step business scenarios (SO → Delivery → Invoice → Payment
  → Reconciliation) where intermediate states need human verification.
- Configuration testing (system parameters, groups, sequences).
- Data migration verification (comparing old vs. new data).

**QA Manual workflow:**

```text
1. Read acceptance criteria and functional spec
2. Write test cases (TC-{MODULE}-{SEQ})
3. Prepare test data in staging environment
4. Execute test cases step by step
5. Record evidence (screenshot, log, database state)
6. Log defects for failures with severity and priority
7. Retest after developer fix
8. Sign off test cycle
```

### QA Automation

Focuses on repeatable regression tests, CI integration, and preventing
regressions after every code change.

**When to use automated testing:**

- Regression testing after any code change (prevent "fix one, break two").
- High-frequency business flows (SO confirm, invoice post, payment reconcile).
- Smoke tests after every deployment.
- Module install/upgrade verification in CI.
- Access rights and record rule enforcement.
- Accounting balance invariants (debit == credit).
- Data validation after batch operations or cron jobs.

**Odoo automation layers:**

| Layer | Tool | What it Tests |
| --- | --- | --- |
| Unit (model) | `TransactionCase` | Business logic, compute, constraints |
| Unit (view) | `Form` utility | Onchange, field visibility, defaults |
| Security | `TransactionCase` with `with_user()` | ACL, record rules, company isolation |
| Integration | `TransactionCase` chain | Cross-module flows (sale → stock → account) |
| E2E / UI | `HttpCase` + `start_tour()` | Full browser simulation with OWL/JS |
| JS Unit | HOOT framework (v18+) | Frontend components in isolation |
| Static analysis | `pylint-odoo` + OCA pre-commit | Code quality, manifest, SQL injection |
| CI Pipeline | Odoo Runbot / GitHub Actions | All of the above, automated per commit |

**Automation coverage target:**

```text
P0 (Critical path, must automate):
  - Module install/upgrade
  - CRUD on primary model
  - Main business flow (e.g., SO → Delivery → Invoice)
  - Access rights (allowed and denied per role)
  - Accounting balance (debit == credit)

P1 (High value, should automate):
  - All state transitions
  - Computed fields with dependencies
  - Constraints (Python and SQL)
  - Multi-company isolation
  - Cron job execution

P2 (Medium value, automate if time allows):
  - Copy behavior
  - Batch operations
  - Edge cases (zero qty, 100% discount)
  - Mail/chatter tracking
  - Sequence generation

P3 (Manual only):
  - Exploratory testing
  - UI/UX usability
  - First-time UAT execution
  - Ad-hoc data investigation
```

---

## Defect Lifecycle (ISTQB Standard)

When a QA tester or user finds a defect, it follows a structured lifecycle:

```text
NEW
 ↓ (QA logs defect)
ASSIGNED
 ↓ (Developer starts fix)
IN PROGRESS
 ↓ (Developer fixes)
FIXED
 ↓ (QA retests)
 ├─ PASS → VERIFIED → CLOSED
 └─ FAIL → REOPENED → ASSIGNED (loop)

Alternative paths:
 NEW → REJECTED (not a bug, by design)
 NEW → DEFERRED (valid but postponed to next release)
 NEW → DUPLICATE (same as existing defect)
```

### Defect Report Template

```text
Defect ID      : BUG-{SEQ}
Title          : {one-line summary}
Module         : {module_technical_name}
Reporter       : {QA name}
Date           : {YYYY-MM-DD}
Environment    : {staging / production / dev}
Odoo Version   : {17.0 / 18.0 / 19.0}

Severity       : Critical | Major | Minor | Trivial
Priority       : Urgent | High | Medium | Low

Steps to Reproduce:
  1. {action}
  2. {action}

Expected Result: {what should happen}
Actual Result  : {what actually happens}
Evidence       : {screenshot / traceback / log}

Related Test   : {TC-MODULE-SEQ if applicable}
Related Ticket : {feature ticket ID}
```

### Severity vs. Priority

| | Definition | Odoo Examples |
| --- | --- | --- |
| **Critical** (Severity) | System crash, data loss, security breach | Unbalanced journal entry posted, data corruption on upgrade |
| **Major** (Severity) | Feature broken, no workaround | Cannot confirm SO, cannot post invoice, access error for authorized user |
| **Minor** (Severity) | Feature works but with issues | Wrong label on form, incorrect sorting, minor calculation rounding |
| **Trivial** (Severity) | Cosmetic, no functional impact | Typo in help text, alignment issue |
| **Urgent** (Priority) | Fix immediately, blocks release | Any Critical severity + any defect blocking UAT sign-off |
| **High** (Priority) | Fix before release | Major severity in core workflow |
| **Medium** (Priority) | Fix in next sprint | Minor severity in frequently used feature |
| **Low** (Priority) | Fix when convenient | Trivial severity, nice-to-have |

---

## OCA Code Quality Gate

The OCA (Odoo Community Association) defines industry-standard quality
checks that should be part of every Odoo project's CI pipeline.

### pylint-odoo

A Pylint plugin for Odoo-specific checks. Key rules:

| Rule | What it Catches |
| --- | --- |
| `sql-injection` | Raw SQL with string formatting instead of parameterized queries |
| `manifest-required-key` | Missing mandatory keys in `__manifest__.py` |
| `translation-required` | User-facing strings without `_()` translation wrapper |
| `attribute-deprecated` | Using deprecated Odoo attributes |
| `method-required-super` | Overriding `create`/`write`/`unlink` without `super()` |
| `license-allowed` | Module license not in OCA-allowed list |
| `resource-not-exist` | Referenced XML ID or file does not exist |
| `manifest-version-format` | Version not matching `{odoo_version}.x.y.z` pattern |

### OCA pre-commit hooks

```yaml
# .pre-commit-config.yaml (OCA standard)
repos:
  - repo: https://github.com/OCA/pylint-odoo
    rev: v9.1.2  # check latest version
    hooks:
      - id: pylint_odoo
        args: ["--disable=C,R"]

  - repo: https://github.com/OCA/odoo-pre-commit-hooks
    rev: v0.0.32  # check latest version
    hooks:
      - id: oca-checks-odoo-module
      - id: oca-checks-po

  - repo: https://github.com/psf/black
    rev: "24.4.2"
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: "5.13.2"
    hooks:
      - id: isort
```

### OCA Module Quality Standards

```text
✓ __manifest__.py has all required keys (name, version, depends, license, author)
✓ Version follows {odoo_version}.x.y.z format (e.g., 18.0.1.0.0)
✓ License is LGPL-3 or AGPL-3 (OCA standard)
✓ All user-facing strings wrapped in _()
✓ No raw SQL with string formatting (use %s parameters or self.env.cr.execute)
✓ All models have ir.model.access.csv entries
✓ Tests present in tests/ directory
✓ README.rst or README.md present
✓ No print() or pdb in committed code
✓ All Python files have from __future__ import annotations (optional but recommended)
```

---

## Odoo Runbot CI Pattern

Odoo SA uses Runbot as their CI pipeline. For custom projects, replicate this
pattern using GitHub Actions, GitLab CI, or similar:

```text
On every push / PR:
  1. Provision clean PostgreSQL database
  2. Install target module(s) with --test-enable
  3. Run all Python unit tests (@tagged post_install)
  4. Run JS unit tests (HOOT framework, v18+)
  5. Run Tour tests (HttpCase.start_tour)
  6. Run pylint-odoo static analysis
  7. Report pass/fail per test

Nightly builds (optional):
  - Run module install on every supported Odoo version (17, 18, 19)
  - Run performance benchmarks (query count, response time)
  - Run localization-specific tests
```

### Minimal CI configuration example

```bash
# GitHub Actions / shell script equivalent
# 1. Install module
./odoo-bin -d ci_test -i my_module --stop-after-init --no-http

# 2. Run tests
./odoo-bin -d ci_test --test-enable --test-tags /my_module --stop-after-init --no-http

# 3. Run pylint
pylint --load-plugins=pylint_odoo --disable=C,R addons/my_module/

# 4. Exit code 0 = all passed, non-zero = failure
```

---

## Test Entry and Exit Criteria

### Entry Criteria (When to Start Testing)

```text
✓ Feature development complete (developer says "done")
✓ Developer self-test passed (Definition of Done met)
✓ Code review passed (PR approved)
✓ Module installs on test environment without errors
✓ Test data prepared in staging
✓ Test cases written and reviewed
✓ Test environment matches target version (17/18/19)
✓ Known blockers from previous cycle resolved
```

### Exit Criteria (When to Stop Testing)

```text
✓ All P0 (critical path) test cases executed
✓ All P1 (high value) test cases executed
✓ No open Critical or Major defects
✓ All Minor defects documented with workarounds
✓ Regression suite passed (no new regressions)
✓ Accounting balance verification passed (debit == credit on all posted moves)
✓ Coverage target met (if defined)
✓ QA sign-off documented
```

---

## Test Strategy Document Template

For major Odoo implementation projects, document the test strategy once and
reference it throughout the SDLC.

```text
TEST STRATEGY: {Project Name}
Version: {1.0}
Date: {YYYY-MM-DD}
Author: {QA Lead}

1. SCOPE
   - Modules in scope: {list}
   - Modules out of scope: {list}
   - Odoo version: {17/18/19}
   - Edition: {Community/Enterprise}

2. TEST APPROACH
   - Unit tests: Developer (TransactionCase, Form)
   - Integration tests: Developer + QA (cross-module flows)
   - Functional/SIT: QA Manual (test cases per coverage matrix)
   - Regression: QA Automation (automated suite on every release)
   - UAT: Client/Key Users (business scenario validation)
   - Performance: Tech Lead (query count, response time)

3. TOOLS
   - Python tests: odoo.tests (TransactionCase, HttpCase, Form)
   - JS tests: HOOT framework (v18+)
   - Static analysis: pylint-odoo, OCA pre-commit hooks
   - CI: {GitHub Actions / GitLab CI / Runbot}
   - Test management: {Odoo Project / spreadsheet / TestRail}
   - Defect tracking: {Odoo Helpdesk / Jira / GitHub Issues}

4. ENVIRONMENTS
   - Dev: developer local
   - Test/QA: shared staging server
   - UAT: client-accessible staging
   - Pre-prod: production-like (same data volume, same config)
   - Prod: production

5. ENTRY/EXIT CRITERIA
   (see above)

6. RISKS
   - {risk description} → {mitigation}

7. SCHEDULE
   - {phase} → {date range}
```

## Sources

- Odoo 17 testing: https://www.odoo.com/documentation/17.0/developer/reference/backend/testing.html
- Odoo 18 testing: https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html
- Odoo 19 testing: https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html
- OCA pylint-odoo: https://github.com/OCA/pylint-odoo
- OCA pre-commit hooks: https://github.com/OCA/odoo-pre-commit-hooks
- OCA contributing guidelines: https://github.com/OCA/odoo-community.org (wiki)
- Odoo Runbot: https://runbot.odoo.com
- ISTQB Foundation: https://www.istqb.org/certifications/certified-tester-foundation-level
