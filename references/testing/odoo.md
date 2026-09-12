# Odoo Test Patterns Guide

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  TEST PATTERNS GUIDE                                                         ║
║  Comprehensive testing patterns for Odoo 17, 18, and 19 modules              ║
║  Generate when include_tests: true is specified                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Test File Structure

```
{module_name}/
├── tests/
│   ├── __init__.py
│   ├── common.py              # Shared test data and base classes
│   ├── test_{model_name}.py   # Model unit tests
│   ├── test_security.py       # Security/access tests
│   └── test_integration.py    # Integration tests
```

## Test Class Hierarchy

```python
# tests/__init__.py
from . import test_my_model
from . import test_security
from . import test_integration
```

## Base Test Classes

### Common Test Setup

```python
# tests/common.py
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged

class TestMyModuleCommon(TransactionCase):
    """Common setup for all tests in this module"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create shared test data
        cls.company = cls.env.ref('base.main_company')
        cls.user_admin = cls.env.ref('base.user_admin')

        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })

        # Create test user with specific groups
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'email': 'manager@example.com',
            'groups_id': [Command.set([
                cls.env.ref('base.group_user').id,
                cls.env.ref('my_module.group_manager').id,
            ])],
        })

        cls.user_basic = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'user@example.com',
            'groups_id': [Command.set([
                cls.env.ref('base.group_user').id,
            ])],
        })
```

## Unit Tests

### Basic Model Tests

```python
# tests/test_my_model.py
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError
from .common import TestMyModuleCommon


@tagged('post_install', '-at_install')
class TestMyModel(TestMyModuleCommon):
    """Unit tests for my.model"""

    def test_create_record(self):
        """Test basic record creation"""
        record = self.env['my.model'].create({
            'name': 'Test Record',
            'partner_id': self.partner.id,
        })
        self.assertTrue(record.id)
        self.assertEqual(record.name, 'Test Record')
        self.assertEqual(record.state, 'draft')

    def test_create_with_defaults(self):
        """Test creation with default values"""
        record = self.env['my.model'].create({
            'name': 'Test',
        })
        # Check default company
        self.assertEqual(record.company_id, self.env.company)
        # Check default state
        self.assertEqual(record.state, 'draft')

    def test_name_required(self):
        """Test that name is required"""
        with self.assertRaises(Exception):
            self.env['my.model'].create({})

    def test_state_workflow(self):
        """Test state transitions"""
        record = self.env['my.model'].create({
            'name': 'Workflow Test',
        })

        # Add required line for confirmation
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line 1',
            'quantity': 1,
        })

        # Test confirm
        self.assertEqual(record.state, 'draft')
        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')

        # Test done
        record.action_done()
        self.assertEqual(record.state, 'done')

    def test_confirm_without_lines_fails(self):
        """Test that confirmation requires lines"""
        record = self.env['my.model'].create({
            'name': 'No Lines Test',
        })

        with self.assertRaises(UserError):
            record.action_confirm()
```

### Computed Field Tests

```python
@tagged('post_install', '-at_install')
class TestMyModelComputed(TestMyModuleCommon):
    """Test computed fields"""

    def test_compute_total(self):
        """Test total computation"""
        record = self.env['my.model'].create({
            'name': 'Computed Test',
        })

        # Create lines
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line 1',
            'quantity': 2,
            'price_unit': 10.0,
        })
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line 2',
            'quantity': 3,
            'price_unit': 20.0,
        })

        # Total should be (2*10) + (3*20) = 80
        self.assertEqual(record.total_amount, 80.0)

    def test_compute_line_count(self):
        """Test line count computation"""
        record = self.env['my.model'].create({'name': 'Count Test'})
        self.assertEqual(record.line_count, 0)

        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line 1',
        })
        self.assertEqual(record.line_count, 1)
```

### Constraint Tests

```python
@tagged('post_install', '-at_install')
class TestMyModelConstraints(TestMyModuleCommon):
    """Test model constraints"""

    def test_date_constraint(self):
        """Test date_start must be before date_end"""
        with self.assertRaises(ValidationError):
            self.env['my.model'].create({
                'name': 'Date Test',
                'date_start': '2024-12-31',
                'date_end': '2024-01-01',  # Before start
            })

    def test_unique_code_per_company(self):
        """Test unique code constraint"""
        self.env['my.model'].create({
            'name': 'First',
            'code': 'TEST001',
        })

        with self.assertRaises(Exception):  # IntegrityError wrapped
            self.env['my.model'].create({
                'name': 'Duplicate',
                'code': 'TEST001',  # Same code
            })

    def test_positive_quantity(self):
        """Test quantity must be positive"""
        record = self.env['my.model'].create({'name': 'Qty Test'})

        with self.assertRaises(ValidationError):
            self.env['my.model.line'].create({
                'model_id': record.id,
                'name': 'Negative',
                'quantity': -1,
            })
```

## Security Tests

```python
# tests/test_security.py
from odoo.tests import tagged
from odoo.exceptions import AccessError
from .common import TestMyModuleCommon


@tagged('post_install', '-at_install')
class TestMyModelSecurity(TestMyModuleCommon):
    """Security and access rights tests"""

    def test_user_can_read_own_records(self):
        """Test basic user can read their own records"""
        record = self.env['my.model'].with_user(self.user_basic).create({
            'name': 'User Record',
        })

        # Should be able to read
        record.with_user(self.user_basic).read(['name'])

    def test_user_cannot_delete(self):
        """Test basic user cannot delete records"""
        record = self.env['my.model'].create({'name': 'Test'})

        with self.assertRaises(AccessError):
            record.with_user(self.user_basic).unlink()

    def test_manager_can_delete(self):
        """Test manager can delete records"""
        record = self.env['my.model'].create({'name': 'Test'})
        record.with_user(self.user_manager).unlink()
        self.assertFalse(record.exists())

    def test_multi_company_isolation(self):
        """Test records are isolated by company"""
        # Create second company
        company2 = self.env['res.company'].create({
            'name': 'Company 2',
        })

        # Create user in company2
        user_company2 = self.env['res.users'].create({
            'name': 'User Company 2',
            'login': 'user_c2',
            'company_id': company2.id,
            'company_ids': [Command.set([company2.id])],
        })

        # Create record in main company
        record = self.env['my.model'].create({
            'name': 'Main Company Record',
            'company_id': self.company.id,
        })

        # User in company2 should not see it
        records = self.env['my.model'].with_user(user_company2).search([])
        self.assertNotIn(record, records)

    def test_sudo_bypasses_rules(self):
        """Test sudo() bypasses record rules"""
        record = self.env['my.model'].create({'name': 'Test'})

        # Admin can access via sudo
        record_sudo = record.sudo()
        self.assertTrue(record_sudo.exists())
```

## Integration Tests

```python
# tests/test_integration.py
from odoo.tests import tagged, HttpCase
from .common import TestMyModuleCommon


@tagged('post_install', '-at_install')
class TestMyModelIntegration(TestMyModuleCommon):
    """Integration tests"""

    def test_full_workflow(self):
        """Test complete record lifecycle"""
        # Create
        record = self.env['my.model'].create({
            'name': 'Full Workflow Test',
            'partner_id': self.partner.id,
        })
        self.assertEqual(record.state, 'draft')

        # Add lines
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line 1',
            'quantity': 1,
            'price_unit': 100,
        })

        # Confirm
        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')

        # Check partner was notified (if mail integration)
        if hasattr(record, 'message_ids'):
            self.assertTrue(len(record.message_ids) > 0)

        # Complete
        record.action_done()
        self.assertEqual(record.state, 'done')

        # Cannot delete done records
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            record.unlink()

    def test_copy_record(self):
        """Test record duplication"""
        record = self.env['my.model'].create({
            'name': 'Original',
            'state': 'confirmed',
        })

        # Add line
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line',
        })

        # Copy
        copy = record.copy()

        self.assertNotEqual(copy.id, record.id)
        self.assertIn('(copy)', copy.name)
        self.assertEqual(copy.state, 'draft')  # Reset to draft
        self.assertEqual(len(copy.line_ids), len(record.line_ids))  # Lines copied

    def test_batch_operations(self):
        """Test batch create and write"""
        # Batch create
        records = self.env['my.model'].create([
            {'name': 'Batch 1'},
            {'name': 'Batch 2'},
            {'name': 'Batch 3'},
        ])
        self.assertEqual(len(records), 3)

        # Batch write
        records.write({'active': False})
        for record in records:
            self.assertFalse(record.active)
```

## HTTP/Tour Tests

```python
# tests/test_ui.py
from odoo.tests import tagged, HttpCase


@tagged('post_install', '-at_install')
class TestMyModelUI(HttpCase):
    """UI/Tour tests"""

    def test_ui_create_record(self):
        """Test creating record via UI"""
        self.start_tour(
            '/web',
            'my_module_create_tour',
            login='admin',
        )
```

## Test Tags Reference

| Tag | Meaning |
|-----|---------|
| `post_install` | Run after module installation |
| `-at_install` | Don't run during installation |
| `standard` | Standard test (default) |
| `external` | Requires external services |

## Supported-version test patterns

### X2many command values

```python
def test_create_with_command(self):
    """Test creation with command values."""
    from odoo.fields import Command

    record = self.env['my.model'].create({
        'name': 'Command Test',
        'line_ids': [
            Command.create({'name': 'Line 1', 'quantity': 1}),
            Command.create({'name': 'Line 2', 'quantity': 2}),
        ],
    })
    self.assertEqual(len(record.line_ids), 2)
```

### Visibility testing

```python
def test_view_visibility(self):
    """Test view visibility conditions."""
    record = self.env['my.model'].create({
        'name': 'Visibility Test',
        'state': 'draft',
    })

    # Get form view
    view = self.env['ir.ui.view'].search([
        ('model', '=', 'my.model'),
        ('type', '=', 'form'),
    ], limit=1)

    # Supported versions use Python expressions for visibility.
    # Test that the view renders correctly
    fields_view = self.env['my.model'].get_views(
        [(view.id, 'form')]
    )['views']['form']
    self.assertIn('invisible', str(fields_view))
```

### Multi-company testing

```python
def test_check_company_auto(self):
    """Test company consistency on relational fields."""
    # Create partner in different company
    company2 = self.env['res.company'].create({'name': 'Company 2'})
    partner_c2 = self.env['res.partner'].create({
        'name': 'Partner C2',
        'company_id': company2.id,
    })

    # Should raise if check_company=True
    with self.assertRaises(Exception):
        self.env['my.model'].create({
            'name': 'Cross Company',
            'company_id': self.company.id,
            'partner_id': partner_c2.id,  # Different company
        })
```

---

## Accounting & Financial Integration Tests (IFRS / GAAP)

Modules creating financial transactions (sales, purchases, inventory valuation, manufacturing, POS) must include automated verification of journal entries and balance sheet / P&L invariants:

```python
from odoo.fields import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestFinancialIntegration(AccountTestInvoicingCommon):
    """Verifies statutory accounting integrity and journal move balance."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']

    def test_invoice_posting_and_statutory_balance(self):
        """Verify: draft -> posted -> strict Debit == Credit equality -> locked audit trail."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2026-01-15',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'quantity': 5.0,
                    'price_unit': 200.0,
                    'tax_ids': [Command.set(self.company_data['default_tax_sale'].ids)],
                }),
            ],
        })

        # 1. State Verification
        self.assertEqual(invoice.state, 'draft')
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

        # 2. Strict Mathematical Balance (Debit == Credit)
        lines = invoice.line_ids
        total_debit = sum(lines.mapped('debit'))
        total_credit = sum(lines.mapped('credit'))
        self.assertAlmostEqual(total_debit, total_credit, places=2)
        self.assertGreater(total_debit, 0)

        # 3. IFRS Account Type Segregation
        receivable_lines = lines.filtered(lambda l: l.account_id.account_type == 'asset_receivable')
        income_lines = lines.filtered(lambda l: l.account_id.account_type == 'income')
        tax_lines = lines.filtered(lambda l: l.account_id.account_type == 'liability_current')

        self.assertTrue(receivable_lines)
        self.assertTrue(income_lines)
        self.assertEqual(sum(receivable_lines.mapped('debit')), invoice.amount_total)

        # 4. Immutability: Posted entries cannot be deleted (Anti-Fraud invariant)
        with self.assertRaises(UserError):
            invoice.unlink()
```

---

## Running Tests

### CLI Execution Patterns

```bash
# Run all tests for a module during installation
./odoo-bin -d testdb -i my_module --test-enable --stop-after-init

# Run all tests for an already-installed module
./odoo-bin -d testdb --test-enable --test-tags /my_module --stop-after-init

# Run specific test class in a module (format: /module:class)
./odoo-bin -d testdb --test-enable --test-tags /my_module:TestMyModel --stop-after-init

# Run single test method in a test class (format: /module:class.method)
./odoo-bin -d testdb --test-enable --test-tags /my_module:TestMyModel.test_create --stop-after-init

# Run only post_install tests in module (excluding at_install)
./odoo-bin -d testdb --test-enable --test-tags /my_module,post_install,-at_install --stop-after-init

# Run tests without HTTP server (faster CI execution for TransactionCase)
./odoo-bin -d testdb --test-enable --test-tags /my_module --stop-after-init --no-http

# Run with test coverage report
coverage run ./odoo-bin -d testdb -i my_module --test-enable --stop-after-init
coverage report -m

# Run pylint-odoo static analysis (OCA standard)
pylint --load-plugins=pylint_odoo --disable=C,R addons/my_module/
```

### `--test-tags` Grammar Reference

Under the hood (`odoo/tests/tag_selector.py`), Odoo parses `--test-tags` using the regex:
`[-][tag][/module][:class][.method][[params]]`

| Filter Syntax | Description | Example |
| :--- | :--- | :--- |
| `/module` | All tests inside the specified module | `--test-tags /sale` |
| `:class` | Specific test class across all loaded modules | `--test-tags :TestSaleOrder` |
| `/module:class` | Specific test class in a specific module | `--test-tags /sale:TestSaleOrder` |
| `/module:class.method` | Single test method in a class | `--test-tags /sale:TestSaleOrder.test_confirm` |
| `tag` | Filter by `@tagged('tag_name')` | `--test-tags post_install` |
| `-tag` | Exclude tests matching the tag | `--test-tags -at_install` |
| `*` | Run all discovered tests in all modules | `--test-tags *` |

### Interactive Test Runner in Shell (`odoo.tests.shell`)

Across Odoo 17, 18, and 19, you can run test suites directly from inside `odoo shell` without restarting the server:

```python
# In odoo shell (python3 odoo-bin shell -d testdb)
from odoo.tests.shell import run_tests

# 1. Run all tests for a module
run_tests(env, test_tags='/my_module')

# 2. Run specific class with hot reloading (reloads test files from disk!)
run_tests(env, test_tags='/my_module:TestMyModel', reload_tests=True)

# 3. Run single test method
run_tests(env, test_tags='/my_module:TestMyModel.test_create')
```


---

## Test Base Classes (Odoo 17, 18, 19)

All versions share these core base classes in `odoo.tests`:

| Class | Rollback | HTTP | Use Case |
| --- | --- | --- | --- |
| `TransactionCase` | Per test method (savepoint) | No | Most common. Business logic, CRUD, compute, constraints |
| `SingleTransactionCase` | Per class (one transaction) | No | Ordered test chains where state carries between methods |
| `HttpCase` | Per test method | Yes (browser) | Tour tests, controller tests, full-stack E2E |

```python
# Import patterns (same across v17, v18, v19)
from odoo.tests import TransactionCase, HttpCase, Form, tagged
from odoo.tests.common import SingleTransactionCase
```

---

## @tagged Decorator

Controls when tests run during `--test-enable`:

```python
# Run AFTER module is fully installed (most common for custom modules)
@tagged('post_install', '-at_install')
class TestMyModel(TransactionCase):
    ...

# Run DURING module installation (for testing install-time behavior)
@tagged('at_install')
class TestMyModelInstall(TransactionCase):
    ...

# Custom tags for filtering
@tagged('post_install', '-at_install', 'accounting', 'slow')
class TestAccountingIntegration(TransactionCase):
    ...
```

Run specific tags: `./odoo-bin --test-tags accounting`

---

## Tour Tests (E2E Browser Simulation)

Tour tests simulate real user interaction in a browser. Use `HttpCase` and
`start_tour()`. Available in Odoo 17, 18, and 19.

### Python-side Tour Test

```python
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestMyModelTour(HttpCase):
    """End-to-end browser tests via tours."""

    def test_create_record_tour(self):
        """Test creating a record through the UI."""
        self.start_tour(
            '/odoo/my-model',        # URL to navigate to
            'my_module_create_tour',  # Tour name (JS-side)
            login='admin',           # User to log in as
        )
```

### JavaScript-side Tour Definition

```javascript
/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("my_module_create_tour", {
    url: "/odoo/my-model",
    steps: () => [
        {
            trigger: ".o_list_button_add",
            content: "Click Create button",
            run: "click",
        },
        {
            trigger: ".o_field_widget[name='name'] input",
            content: "Enter record name",
            run: "edit Tour Test Record",
        },
        {
            trigger: ".o_form_button_save",
            content: "Save the record",
            run: "click",
        },
        {
            trigger: ".o_form_view .o_field_widget[name='name']:contains('Tour Test Record')",
            content: "Verify record was saved",
        },
    ],
});
```

### Common Tour Triggers

| Trigger | Action |
| --- | --- |
| `.o_list_button_add` | Click "Create" in list view |
| `.o_form_button_save` | Click "Save" in form view |
| `.o_statusbar_buttons button[name='action_confirm']` | Click workflow button |
| `.o_field_widget[name='field_name'] input` | Type in a field |
| `.o_field_many2one[name='field_name'] input` | Open many2one dropdown |
| `.breadcrumb-item:contains('Back')` | Navigate breadcrumb |

---

## HOOT JavaScript Unit Tests (v18+)

Odoo 18 and 19 use the HOOT framework for testing frontend OWL components
in isolation. HOOT tests run in the browser without a full Odoo server.

```javascript
/** @odoo-module **/

import { describe, test, expect, beforeEach } from "@odoo/hoot";
import { contains, mountView, defineModels, models, fields, onRpc } from "@web/../tests/web_test_helpers";

class MyModel extends models.Model {
    _name = "my.model";
    name = fields.Char();
    _records = [{ id: 1, name: "Test" }];
}

defineModels([MyModel]);

describe("MyModel views", () => {
    test("renders list view", async () => {
        await mountView({
            type: "list",
            resModel: "my.model",
        });
        expect(".o_data_row").toHaveCount(1);
        expect(".o_data_cell").toHaveText("Test");
    });

    test("tracks RPC calls", async () => {
        onRpc("web_search_read", () => {
            expect.step("web_search_read");
        });
        await mountView({
            type: "list",
            resModel: "my.model",
        });
        expect.verifySteps(["web_search_read"]);
    });

    test("clicking button triggers action", async () => {
        await mountView({
            type: "form",
            resModel: "my.model",
            resId: 1,
        });
        await contains(".o_form_button_save").click();
        // verify outcome via DOM assertions
    });
});
```

Key HOOT patterns (different from Jest):
- **No `jest.fn()`** — use `expect.step("label")` + `expect.verifySteps(["label"])`
- **DOM queries** — `expect(".css-selector").toHaveCount(1)` / `.toHaveText("x")`
- **DOM actions** — `await contains(".selector").click()` (from `web_test_helpers`)
- **RPC mocking** — `onRpc("method_name", handler)` (from `web_test_helpers`)
- **Models** — `models.Model` subclass + `defineModels()` (from `web_test_helpers`)

---

## QUnit JavaScript Unit Tests (Odoo 17)

In Odoo 17, frontend tests are built on QUnit (HOOT was introduced in v18). Tests live under `static/tests/` and are registered in the `web.qunit_suite_tests` asset bundle in `__manifest__.py`:

```javascript
/** @odoo-module **/

import { getFixture, mount } from "@web/../tests/helpers/utils";
import { makeTestEnv } from "@web/../tests/helpers/mock_env";
import { MyOwlComponent } from "@my_module/components/my_owl_component";

let env;
let fixture;

QUnit.module("MyModule Frontend Tests (Odoo 17)", {
    async beforeEach() {
        fixture = getFixture();
        env = await makeTestEnv();
    },
});

QUnit.test("renders component correctly", async (assert) => {
    await mount(MyOwlComponent, fixture, {
        env,
        props: { title: "Test Title" },
    });

    assert.containsOnce(fixture, ".my-component", "Component should mount into DOM");
    assert.strictEqual(
        fixture.querySelector(".my-component-title").textContent.trim(),
        "Test Title",
        "Title prop should render into title element"
    );
});
```

Key QUnit patterns in Odoo 17:
- **DOM Container**: Obtain the test DOM fixture via `getFixture()` and pass to `mount()`.
- **Environment**: Initialize test env via `await makeTestEnv()`.
- **Assertions**: Use QUnit `assert.containsOnce(fixture, selector)`, `assert.strictEqual()`, and `assert.ok()`.



## Test Generation Checklist

For each model, generate tests for:

- [ ] Basic CRUD operations (create, read, update, delete)
- [ ] All computed fields
- [ ] All constraints (Python and SQL)
- [ ] State workflow transitions
- [ ] Access rights by user group
- [ ] Record rules (multi-company, ownership)
- [ ] Onchange methods
- [ ] Action methods (buttons)
- [ ] Copy behavior
- [ ] Batch operations
- [ ] Module install on clean database
- [ ] Module upgrade on database with existing data
- [ ] Sequence generation
- [ ] Mail/chatter integration (if mail.thread)
- [ ] Cron execution (if scheduled actions)
- [ ] Negative and boundary inputs
- [ ] Concurrency safety (if concurrent writes possible)

---

## Onchange Tests (Form Utility)

Use `odoo.tests.Form` to simulate UI onchange behavior. Available in Odoo 17,
18, and 19 via `from odoo.tests import Form`.

```python
from odoo.tests import Form, tagged
from .common import TestMyModuleCommon


@tagged('post_install', '-at_install')
class TestMyModelOnchange(TestMyModuleCommon):
    """Test onchange behavior via Form simulation."""

    def test_onchange_partner_sets_defaults(self):
        """Test that selecting a partner fills dependent fields."""
        with Form(self.env['my.model']) as form:
            form.partner_id = self.partner
            # Onchange should populate payment_term, pricelist, etc.
            self.assertEqual(form.payment_term_id, self.partner.property_payment_term_id)

    def test_onchange_product_on_line(self):
        """Test that selecting a product fills line defaults."""
        record = self.env['my.model'].create({'name': 'Onchange Test'})
        with Form(record) as form:
            with form.line_ids.new() as line:
                line.product_id = self.product
                # Onchange should set name, price, UoM from product
                self.assertTrue(line.name)
                self.assertGreater(line.price_unit, 0)

    def test_onchange_quantity_recomputes_total(self):
        """Test that changing quantity triggers recomputation."""
        record = self.env['my.model'].create({'name': 'Qty Test'})
        with Form(record) as form:
            with form.line_ids.new() as line:
                line.product_id = self.product
                line.quantity = 5
                expected = 5 * line.price_unit
            # Save triggers compute
        self.assertAlmostEqual(record.line_ids[0].subtotal, expected, places=2)
```

---

## Module Install and Upgrade Tests

Verify that the module installs cleanly on an empty database and upgrades
without errors on a database with existing data.

```python
@tagged('post_install', '-at_install')
class TestMyModuleInstall(TestMyModuleCommon):
    """Test module installation and upgrade safety."""

    def test_module_is_installed(self):
        """Verify the module installed successfully."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'my_module'),
        ])
        self.assertEqual(module.state, 'installed')

    def test_all_views_valid(self):
        """Verify all views defined by this module are valid."""
        views = self.env['ir.ui.view'].search([
            ('model', '=', 'my.model'),
        ])
        for view in views:
            # get_views will raise if the view is invalid
            try:
                self.env['my.model'].with_context(
                    check_view_ids=view.ids
                ).get_views([(view.id, view.type)])
            except Exception as e:
                self.fail(f"View {view.name} (id={view.id}) is invalid: {e}")

    def test_all_access_rights_loadable(self):
        """Verify ir.model.access records are valid."""
        access = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'my.model'),
        ])
        self.assertTrue(access, "No access rights defined for my.model")
        for rule in access:
            self.assertTrue(rule.model_id, f"Access rule {rule.name} has no model")

    def test_all_xml_ids_resolvable(self):
        """Verify key XML IDs from this module resolve."""
        xml_ids = [
            'my_module.view_my_model_form',
            'my_module.view_my_model_list',
            'my_module.action_my_model',
            'my_module.menu_my_model',
        ]
        for xml_id in xml_ids:
            record = self.env.ref(xml_id, raise_if_not_found=False)
            self.assertTrue(record, f"XML ID {xml_id} not found")
```

Command-line verification (run as part of CI or manual pre-deployment):

```bash
# Clean install test
./odoo-bin -d test_install -i my_module --test-enable --stop-after-init

# Upgrade test (on database with existing data)
./odoo-bin -d test_upgrade -u my_module --test-enable --stop-after-init
```

---

## Sequence Generation Tests

```python
@tagged('post_install', '-at_install')
class TestMyModelSequence(TestMyModuleCommon):
    """Test automatic sequence generation."""

    def test_sequence_on_create(self):
        """Verify sequence is assigned on record creation or confirmation."""
        record = self.env['my.model'].create({
            'name': 'Sequence Test',
        })
        # If sequence is assigned on create:
        self.assertTrue(record.name and record.name != '/')

    def test_sequence_uniqueness(self):
        """Verify sequences are unique."""
        records = self.env['my.model'].create([
            {'name': 'Seq 1'},
            {'name': 'Seq 2'},
        ])
        names = records.mapped('name')
        self.assertEqual(len(names), len(set(names)), "Duplicate sequences found")

    def test_sequence_per_company(self):
        """Verify sequences are isolated per company."""
        company2 = self.env['res.company'].create({'name': 'Company 2'})
        record_c1 = self.env['my.model'].create({'name': 'C1'})
        record_c2 = self.env['my.model'].with_company(company2).create({
            'name': 'C2',
            'company_id': company2.id,
        })
        # Both should have valid sequences (may or may not overlap by design)
        self.assertTrue(record_c1.name and record_c1.name != '/')
        self.assertTrue(record_c2.name and record_c2.name != '/')
```

---

## Mail / Chatter Integration Tests

For models inheriting `mail.thread`, verify tracking and notification behavior.
Use `MailCommon` from `odoo.addons.mail.tests.common` when available, or test
via the ORM directly.

```python
@tagged('post_install', '-at_install')
class TestMyModelMail(TestMyModuleCommon):
    """Test mail.thread integration."""

    def test_tracking_on_state_change(self):
        """Verify state changes create tracking messages."""
        record = self.env['my.model'].create({
            'name': 'Mail Test',
        })
        initial_count = len(record.message_ids)

        # Trigger state change
        record.action_confirm()

        # Should have a new tracking message
        self.assertGreater(len(record.message_ids), initial_count)

    def test_message_post(self):
        """Verify manual message posting works."""
        record = self.env['my.model'].create({'name': 'Post Test'})
        record.message_post(
            body='Test message',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        self.assertTrue(
            record.message_ids.filtered(lambda m: 'Test message' in (m.body or ''))
        )

    def test_follower_on_create(self):
        """Verify creator is added as follower."""
        record = self.env['my.model'].create({'name': 'Follower Test'})
        follower_partners = record.message_follower_ids.mapped('partner_id')
        self.assertIn(self.env.user.partner_id, follower_partners)
```

---

## Cron / Scheduled Action Tests

```python
@tagged('post_install', '-at_install')
class TestMyModelCron(TestMyModuleCommon):
    """Test scheduled action execution."""

    def test_cron_method_exists(self):
        """Verify the cron method is callable."""
        self.assertTrue(
            hasattr(self.env['my.model'], '_cron_process_pending'),
            "Cron method _cron_process_pending not found on my.model",
        )

    def test_cron_processes_records(self):
        """Test that the cron processes pending records."""
        # Create records in pending state
        records = self.env['my.model'].create([
            {'name': 'Pending 1', 'state': 'pending'},
            {'name': 'Pending 2', 'state': 'pending'},
        ])

        # Execute cron method
        self.env['my.model']._cron_process_pending()

        # Verify records were processed
        for record in records:
            self.assertEqual(record.state, 'done')

    def test_cron_handles_empty_batch(self):
        """Test cron does not fail when nothing to process."""
        # No pending records exist
        self.env['my.model']._cron_process_pending()
        # Should not raise

    def test_cron_is_registered(self):
        """Verify cron job XML record exists and is active."""
        cron = self.env.ref(
            'my_module.ir_cron_process_pending',
            raise_if_not_found=False,
        )
        self.assertTrue(cron, "Cron XML ID not found")
        self.assertTrue(cron.active, "Cron is not active")
```

---

## Negative and Boundary Tests

Systematic approach to testing invalid and edge-case inputs.

```python
@tagged('post_install', '-at_install')
class TestMyModelNegative(TestMyModuleCommon):
    """Negative test cases — verify proper error handling."""

    def test_create_without_required_fields(self):
        """Verify creation fails without required fields."""
        with self.assertRaises(Exception):
            self.env['my.model'].create({})

    def test_invalid_state_transition(self):
        """Verify invalid state transitions are blocked."""
        record = self.env['my.model'].create({
            'name': 'Invalid Transition',
            'state': 'done',
        })
        with self.assertRaises(UserError):
            record.action_confirm()  # Cannot confirm a done record

    def test_action_on_archived_record(self):
        """Verify actions are blocked on archived records."""
        record = self.env['my.model'].create({'name': 'Archive Test'})
        record.active = False
        with self.assertRaises(UserError):
            record.action_confirm()

    def test_invalid_partner_reference(self):
        """Verify error on non-existent relational reference."""
        with self.assertRaises(Exception):
            self.env['my.model'].create({
                'name': 'Bad Partner',
                'partner_id': 99999999,
            })


@tagged('post_install', '-at_install')
class TestMyModelBoundary(TestMyModuleCommon):
    """Boundary test cases — edge values."""

    def test_zero_quantity(self):
        """Test behavior with zero quantity."""
        record = self.env['my.model'].create({'name': 'Zero Qty'})
        with self.assertRaises(ValidationError):
            self.env['my.model.line'].create({
                'model_id': record.id,
                'name': 'Zero',
                'quantity': 0,
            })

    def test_negative_price(self):
        """Test behavior with negative price."""
        record = self.env['my.model'].create({'name': 'Neg Price'})
        line = self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Negative',
            'quantity': 1,
            'price_unit': -100.0,
        })
        # Depending on business rules: either blocked or creates credit
        self.assertEqual(line.subtotal, -100.0)

    def test_100_percent_discount(self):
        """Test 100% discount does not produce negative amounts."""
        record = self.env['my.model'].create({'name': 'Full Discount'})
        line = self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Free',
            'quantity': 1,
            'price_unit': 100.0,
            'discount': 100.0,
        })
        self.assertEqual(line.subtotal, 0.0)

    def test_very_large_quantity(self):
        """Test system handles large quantities without overflow."""
        record = self.env['my.model'].create({'name': 'Large Qty'})
        line = self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Bulk',
            'quantity': 999999,
            'price_unit': 0.01,
        })
        self.assertAlmostEqual(line.subtotal, 9999.99, places=2)

    def test_precision_rounding(self):
        """Test currency precision rounding."""
        record = self.env['my.model'].create({'name': 'Precision'})
        line = self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Precise',
            'quantity': 3,
            'price_unit': 1.005,  # Edge of rounding
        })
        # Result depends on currency rounding rules
        self.assertIsInstance(line.subtotal, float)
```

---

## Concurrency Safety Tests

For models where concurrent writes are expected (e.g., stock, accounting,
sequences), verify that concurrent operations do not corrupt data. Use
`cr.savepoint()` to simulate concurrent transaction behavior within a single
test.

```python
@tagged('post_install', '-at_install')
class TestMyModelConcurrency(TestMyModuleCommon):
    """Test concurrent access safety."""

    def test_concurrent_confirm_raises(self):
        """Verify that double-confirming raises instead of corrupting."""
        record = self.env['my.model'].create({'name': 'Concurrent'})
        self.env['my.model.line'].create({
            'model_id': record.id,
            'name': 'Line',
            'quantity': 1,
        })

        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')

        # Second confirm should either be idempotent or raise
        with self.assertRaises(UserError):
            record.action_confirm()

    def test_savepoint_rollback_on_error(self):
        """Verify partial operations roll back cleanly on error."""
        record = self.env['my.model'].create({'name': 'Savepoint'})

        try:
            with self.env.cr.savepoint():
                record.write({'name': 'Modified'})
                raise ValueError("Simulated concurrent error")
        except ValueError:
            pass

        # Record should be unchanged after savepoint rollback
        record.invalidate_recordset()
        self.assertEqual(record.name, 'Savepoint')
```

## Time-Dependent Tests (freeze_time)

Odoo provides its own `freeze_time` wrapper (built on `freezegun`) for testing
date-sensitive logic: lock dates, auto-posting, scheduled actions, currency
rates, and date-based filtering.

- **v18 / v19:** `from odoo.tests.common import freeze_time`
- **v17:** `from freezegun import freeze_time` (`odoo.tests.common.freeze_time` was added in v18)

```python
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import freeze_time
from odoo.fields import Command


@tagged('post_install', '-at_install')
class TestDateSensitive(TransactionCase):
    """Test behavior that depends on the current date."""

    @freeze_time('2026-01-15')
    def test_lock_date_prevents_posting(self):
        """Cannot post a move before the lock date."""
        self.env.company.fiscalyear_lock_date = '2026-01-31'
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'date': '2026-01-10',  # before lock date
            'line_ids': [
                Command.create({'debit': 100, 'account_id': self.account_debit.id}),
                Command.create({'credit': 100, 'account_id': self.account_credit.id}),
            ],
        })
        with self.assertRaises(UserError):
            move.action_post()

    @freeze_time('2026-06-01')
    def test_auto_post_on_date(self):
        """Moves with auto_post='at_date' post when date is reached."""
        move = self.env['account.move'].create({
            'date': '2026-06-01',
            'auto_post': 'at_date',
            # ... lines
        })
        move._autopost_draft_entries()
        self.assertEqual(move.state, 'posted')

    def test_freeze_time_context_manager(self):
        """freeze_time also works as a context manager."""
        with freeze_time('2026-12-31'):
            from odoo.fields import Date
            self.assertEqual(Date.today(), '2026-12-31')
```

Common `freeze_time` use cases:
- Lock date enforcement (fiscal year, tax period).
- Auto-posting by date (`account.move.auto_post`).
- Cron scheduling (`ir.cron.nextcall`).
- Currency rate lookup for a specific date.
- Sequence reset by year/month boundary.

## Wizard (TransientModel) Tests

Wizards are `TransientModel` records that typically perform actions on
an `active_ids` context. Test the wizard lifecycle: create → populate →
execute → verify side effects.

```python
@tagged('post_install', '-at_install')
class TestMyWizard(TransactionCase):
    """Test wizard that performs a batch action."""

    def test_wizard_action(self):
        """Wizard processes selected records correctly."""
        records = self.env['my.model'].create([
            {'name': 'Record 1', 'state': 'draft'},
            {'name': 'Record 2', 'state': 'draft'},
        ])

        # Create wizard with active_ids context (simulates UI selection)
        wizard = self.env['my.model.confirm.wizard'].with_context(
            active_model='my.model',
            active_ids=records.ids,
        ).create({
            'reason': 'Batch confirm',
        })

        # Execute wizard action
        wizard.action_confirm()

        # Verify side effects on the original records
        self.assertTrue(all(r.state == 'confirmed' for r in records))

    def test_wizard_validation(self):
        """Wizard raises if preconditions not met."""
        record = self.env['my.model'].create({
            'name': 'Already Done',
            'state': 'done',
        })

        wizard = self.env['my.model.confirm.wizard'].with_context(
            active_model='my.model',
            active_ids=record.ids,
        ).create({})

        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_wizard_returns_action(self):
        """Wizard returns an ir.actions.act_window after execution."""
        record = self.env['my.model'].create({'name': 'Test'})
        wizard = self.env['my.model.report.wizard'].with_context(
            active_ids=record.ids,
        ).create({'date_from': '2026-01-01', 'date_to': '2026-12-31'})

        result = wizard.action_generate()

        # Wizard should return an action dict
        self.assertEqual(result.get('type'), 'ir.actions.act_window')
```

Key wizard testing points:
- Always set `active_model` and `active_ids` in context.
- Test both success path and validation errors.
- Test the return value (action dict for redirect, or `None` for close).
- TransientModel records are auto-cleaned — no manual cleanup needed.

## Report and PDF Generation Tests

Test QWeb report rendering to ensure reports don't crash and produce
correct output.

```python
@tagged('post_install', '-at_install')
class TestMyReport(TransactionCase):
    """Test QWeb report generation."""

    def test_report_renders_without_error(self):
        """Report renders to PDF without crashing."""
        record = self.env['my.model'].create({
            'name': 'Report Test',
            'state': 'confirmed',
        })

        report = self.env.ref('my_module.action_report_my_model')
        # _render_qweb_pdf returns (pdf_content, content_type)
        pdf_content, content_type = report._render_qweb_pdf(
            report_ref='my_module.action_report_my_model',
            res_ids=record.ids,
        )

        self.assertTrue(pdf_content, "PDF content should not be empty")
        self.assertEqual(content_type, 'pdf')

    def test_report_data_accuracy(self):
        """Report HTML contains expected data values."""
        record = self.env['my.model'].create({
            'name': 'Data Check',
            'amount': 1500.00,
        })

        report = self.env.ref('my_module.action_report_my_model')
        # _render_qweb_html for inspectable HTML output
        html_content = report._render_qweb_html(
            report_ref='my_module.action_report_my_model',
            res_ids=record.ids,
        )[0]

        self.assertIn(b'Data Check', html_content)
        self.assertIn(b'1,500.00', html_content)

    def test_report_multiple_records(self):
        """Report handles multiple records in a single render."""
        records = self.env['my.model'].create([
            {'name': f'Record {i}'} for i in range(5)
        ])

        report = self.env.ref('my_module.action_report_my_model')
        pdf_content, _ = report._render_qweb_pdf(
            report_ref='my_module.action_report_my_model',
            res_ids=records.ids,
        )
        self.assertTrue(pdf_content)
```

Key report testing points:
- Use `_render_qweb_pdf()` to test PDF rendering (catches wkhtmltopdf issues).
- Use `_render_qweb_html()` to inspect actual content values.
- Test with multiple records (batch rendering).
- Test with missing/empty optional fields (don't crash on `None`).
- Reference the report via `self.env.ref('module.action_report_xml_id')`.

## Batch Record Value Assertions (assertRecordValues)

Available in `BaseCase` for **Odoo 17, 18, and 19**.

Instead of writing repetitive loops with `self.assertEqual()`, use `self.assertRecordValues()` to verify multiple fields across a recordset in a single call.

```python
from odoo.tests import TransactionCase, tagged
from odoo.fields import Command


@tagged('post_install', '-at_install')
class TestBatchAssertions(TransactionCase):

    def test_line_values_batch(self):
        """Verify multiple fields across lines in a single assertion."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({'product_id': self.product_a.id, 'product_uom_qty': 2.0, 'price_unit': 100.0}),
                Command.create({'product_id': self.product_b.id, 'product_uom_qty': 1.0, 'price_unit': 50.0}),
            ],
        })

        # Element-by-element comparison based on index order
        self.assertRecordValues(order.order_line, [
            {'product_id': self.product_a.id, 'product_uom_qty': 2.0, 'price_subtotal': 200.0},
            {'product_id': self.product_b.id, 'product_uom_qty': 1.0, 'price_subtotal': 50.0},
        ])
```

## Performance and Query Count Testing (assertQueryCount)

Available in `BaseCase` for **Odoo 17, 18, and 19**.

Guard against N+1 query regressions in compute fields, batch operations, and business methods.

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQueryPerformance(TransactionCase):

    def test_conversion_query_count(self):
        """Verify method executes within expected SQL query budget."""
        # Warm the ORM cache if testing steady-state performance
        self.env.company.currency_id._convert(100.0, self.currency_eur, self.env.company, '2026-01-01')

        # Assert exact query count (fails if N+1 query leak is introduced)
        with self.assertQueryCount(1):
            self.env.company.currency_id._convert(
                from_amount=250.0,
                to_currency=self.currency_eur,
                company=self.env.company,
                date='2026-01-01',
            )
```

## Capturing Generated Records (RecordCapturer)

Available in `odoo.tests.common` for **Odoo 17, 18, and 19**.

Captures all records created in a specific model during the execution of a code block, avoiding manual queries before and after.

```python
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import RecordCapturer


@tagged('post_install', '-at_install')
class TestRecordCapture(TransactionCase):

    def test_action_generates_expected_records(self):
        """Capture records generated downstream by a business action."""
        order = self.env['sale.order'].create({'partner_id': self.partner.id})

        with RecordCapturer(self.env['account.move'], [('company_id', '=', self.env.company.id)]) as capture:
            order.action_confirm()

        # capture.records contains only the newly created records
        self.assertEqual(len(capture.records), 1)
        self.assertEqual(capture.records.state, 'draft')
```

## Fuzzy and Decimal Comparisons (Like, Approx)

Available in `odoo.tests.common` for **Odoo 18 and 19**.

- `Like`: String comparison where `'...'` matches arbitrary substrings.
- `Approx`: Float/currency comparison using `float_compare` or currency rounding.

```python
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import Like, Approx


@tagged('post_install', '-at_install')
class TestFuzzyComparisons(TransactionCase):

    def test_fuzzy_string_matching(self):
        """Match strings with dynamic substrings using Like."""
        log_message = "Processed order SO001 for Customer Acme in 0.042s"
        self.assertEqual(log_message, Like("Processed order SO001 for Customer ... in ...s"))

    def test_approx_currency_rounding(self):
        """Compare monetary values respecting currency precision."""
        computed_tax = 10.554
        self.assertEqual(computed_tax, Approx(10.55, rounding=self.env.company.currency_id, decorate=True))
```

## Native Mocking (self.patch)

Available in `BaseCase` for **Odoo 17, 18, and 19**.

Applies `setattr` mocking via `unittest.mock.patch` with automatic cleanup (`self.addCleanup`), removing the need for nested `with patch(...)` context managers.

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNativePatching(TransactionCase):

    def test_external_service_mock(self):
        """Mock an external service or method with automatic post-test cleanup."""
        # Patch method directly; cleanup is handled automatically when test finishes
        self.patch(
            type(self.env['payment.provider']),
            '_send_payment_request',
            lambda self, *args, **kwargs: {'status': 'success', 'tx_id': 'TX123'},
        )

        res = self.provider._send_payment_request()
        self.assertEqual(res['status'], 'success')
```

## Headless Controller and JSON-RPC Testing

Available in `HttpCase` for **Odoo 17, 18, and 19**.

Test HTTP routes, REST endpoints, portals, and JSON-RPC controllers directly without starting a browser tour.

```python
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestControllerEndpoints(HttpCase):

    def test_jsonrpc_search_read(self):
        """Call JSON-RPC endpoint directly via make_jsonrpc_request."""
        self.authenticate('admin', 'admin')
        result = self.make_jsonrpc_request('/web/dataset/call_kw', {
            'model': 'res.partner',
            'method': 'search_read',
            'args': [[('id', '=', self.env.ref('base.partner_admin').id)]],
            'kwargs': {'fields': ['name', 'email']},
        })
        self.assertTrue(result)
        self.assertEqual(result[0]['name'], 'Mitchell Admin')

    def test_http_endpoint_response(self):
        """Call standard HTTP route directly via url_open."""
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Database', response.content)
```

## Button and Action Testing

Available for **Odoo 17, 18, and 19**.

Buttons in views either execute a model method (`type="object"`) or trigger an action (`type="action"`). Test both state transitions and returned action dictionaries:

```python
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestButtonActions(TransactionCase):

    def test_button_state_transition(self):
        """Test object button triggering state change."""
        record = self.env['my.model'].create({'name': 'Test'})
        self.assertEqual(record.state, 'draft')

        # Click confirm button
        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')

        # Invariant: clicking confirm on already confirmed record fails
        with self.assertRaises(UserError):
            record.action_confirm()

    def test_button_returns_wizard_action(self):
        """Test object button returning an act_window popup dictionary."""
        record = self.env['my.model'].create({'name': 'Test'})
        action = record.action_open_wizard()

        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'my.wizard')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('active_id'), record.id)
```

## View Architecture and XPath Testing

Available for **Odoo 17, 18, and 19**.

Ensure all module XML views parse correctly, modifiers are valid, and inherited views patch parent architectures without broken XPath:

```python
from odoo.tests import TransactionCase, Form, tagged


@tagged('post_install', '-at_install')
class TestViewArchitectures(TransactionCase):

    def test_module_views_valid(self):
        """Ensure all views in this module load without XML/arch errors."""
        views = self.env['ir.ui.view'].search([('model', 'like', 'my.module%')])
        for view in views:
            with self.subTest(view_name=view.name, view_type=view.type):
                # get_views parses arch, checks fields, and validates modifiers
                res = self.env[view.model].get_views([(view.id, view.type)])
                self.assertIn('views', res)

    def test_xpath_inheritance_applied(self):
        """Verify inherited view successfully injects custom fields into parent view."""
        arch = self.env['sale.order'].get_view(
            self.env.ref('sale.view_order_form').id,
            view_type='form',
        )['arch']
        self.assertIn('x_custom_field', arch)

    def test_form_view_subform_manipulation(self):
        """Simulate UI form view with One2many sub-form lines and onchanges."""
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner
            with form.order_line.new() as line:
                line.product_id = self.product
                line.product_uom_qty = 5.0
            with form.order_line.edit(0) as line:
                line.product_uom_qty = 10.0
            order = form.save()

        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_uom_qty, 10.0)
```

## User Test Fixtures and Context Switching (new_test_user, @users)

Available in `odoo.tests.common` for **Odoo 17, 18, and 19**.

- `new_test_user()`: Creates test users with assigned groups and valid emails in one line.
- `@users(*logins)`: Decorates a test method to execute once per listed login, automatically isolating user environments with `self.subTest()` and flushing caches via `self.env.invalidate_all()`.

```python
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user, users
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestUserPermissions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesman = new_test_user(
            cls.env,
            login='salesman_user',
            groups='base.group_user,sales_team.group_sale_salesman',
            name='Salesman User',
        )
        cls.manager = new_test_user(
            cls.env,
            login='manager_user',
            groups='base.group_user,sales_team.group_sale_manager',
            name='Manager User',
        )

    @users('salesman_user', 'manager_user')
    def test_read_access_matrix(self):
        """Runs once for salesman_user and once for manager_user with clean cache."""
        records = self.env['my.model'].search([])
        self.assertTrue(records)

    def test_unauthorized_deletion_fails(self):
        """Standard single-user permission check."""
        record = self.env['my.model'].create({'name': 'Restricted'})
        with self.assertRaises(AccessError):
            record.with_user(self.salesman).unlink()
```

## Silencing Expected Errors in Test Logs (mute_logger)

Available in `odoo.tools` for **Odoo 17, 18, and 19**.

When testing negative scenarios, Odoo often logs expected error tracebacks (e.g. from `ir.rule`, `ir.model.access`, or HTTP 404/500 handlers). Use `mute_logger` to keep test outputs clean and noise-free.

```python
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestNegativeLogging(TransactionCase):

    @mute_logger('odoo.addons.base.models.ir_rule', 'odoo.models')
    def test_expected_access_denial(self):
        """Suppress expected error stack traces in test output."""
        with self.assertRaises(AccessError):
            self.env['my.sensitive.model'].with_user(self.unprivileged_user).read(['secret_token'])

    def test_context_manager_mute(self):
        """Mute logger only for a specific critical block."""
        with mute_logger('odoo.http'):
            # Calls endpoint expecting 404 without cluttering stdout
            res = self.url_open('/nonexistent/route')
            self.assertEqual(res.status_code, 404)
```

## Structural XML and HTML Assertions (assertXMLEqual, assertHTMLEqual)

Available in `BaseCase` for **Odoo 17, 18, and 19**.

Semantic comparisons for XML view architectures and rendered HTML content that ignore insignificant whitespace differences and attribute order.

```python
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSemanticMarkup(TransactionCase):

    def test_xml_view_structure(self):
        """Compare two XML fragments semantically regardless of attribute order or indentation."""
        arch1 = '<list string="Records"><field name="name"/><field name="state"/></list>'
        arch2 = '''
        <list string="Records">
            <field name="state" />
            <field name="name" />
        </list>
        '''
        # Semantically checks nodes and attributes
        self.assertXMLEqual(arch1, arch2)

    def test_rendered_report_html_structure(self):
        """Compare rendered HTML output ignoring extra whitespace."""
        rendered = "<div><h1>Title</h1> <p>Description</p></div>"
        expected = """
        <div>
            <h1>Title</h1>
            <p>Description</p>
        </div>
        """
        self.assertHTMLEqual(rendered, expected)
```

## Advanced Test Helpers (`freeze_time`, `Like`, `Approx`)

Available in `odoo.tests.common` for **Odoo 18 and 19**:

### 1. `freeze_time` (Native Deterministic Clock)
A unified replacement for `freezegun` that works as a test class decorator, method decorator, or context manager:

```python
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import freeze_time


# A. As a class decorator (applies to all tests in class)
@tagged('post_install', '-at_install')
@freeze_time('2025-01-01 12:00:00')
class TestTimeFreezing(TransactionCase):

    def test_fixed_date(self):
        self.assertEqual(fields.Date.today().isoformat(), '2025-01-01')

    # B. As a context manager for a specific block
    def test_context_time(self):
        with freeze_time('2025-06-15'):
            self.assertEqual(fields.Date.today().isoformat(), '2025-06-15')
```

### 2. `Like` (Wildcard String Assertions)
A string-like comparison wrapper where `...` matches any substring—essential for asserting dynamic SQL queries, error messages, or logs with auto-generated IDs or timestamps:

```python
from odoo.tests.common import Like

# Matches any columns and where-clauses without brittle regexes
self.assertEqual(
    generated_query,
    Like("SELECT ... FROM res_partner WHERE id = ...")
)

# Checking elements in arrays
self.assertEqual(
    ['Partner A', 'Order SO001', 'Approved by Admin'],
    ['Partner A', Like('Order ...'), Like('Approved by ...')]
)
```

### 3. `Approx` (Float Tolerance Comparisons)
Compares floating point values using Odoo's `float_compare` engine with precision or currency rounding:

```python
from odoo.tests.common import Approx

# Tolerance check with currency or decimal rounding
self.assertEqual(calculated_total, Approx(100.50, rounding=2, decorate=False))
```
