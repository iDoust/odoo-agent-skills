# Odoo Module Structure - Shared Core

This document covers module structure concepts shared by Odoo 17–19. For
version-specific implementation details, load the matching file under
`references/versions/` and inspect the target source.

## Solution Selection: Configure vs OCA vs Custom Module

Before creating a new module or adding custom Python/XML code, evaluate according to this decision hierarchy:

1. **Standard Configuration**: Can the requirement be met by standard Odoo settings, automated actions (`base.automation`), server actions, or user interface configurations?
2. **OCA Community Solutions**: Has the Odoo Community Association already developed and tested a robust module for this requirement (e.g. `web_responsive`, `queue_job`, `account_financial_report`)? Consult [`community-enterprise-solutions.md`](community-enterprise-solutions.md) and [`../operations/oca-guidelines.md`](../operations/oca-guidelines.md).
3. **Custom Minimal Module**: If the requirement represents unique business logic, build the narrowest possible module adhering to standard Odoo patterns and naming conventions.

## Module Architecture Overview

Every Odoo module follows a standard structure:

```
module_name/
├── __init__.py          # Python package initialization
├── __manifest__.py      # Module metadata and dependencies
├── models/              # Business logic (Python models)
├── views/               # UI definitions (XML)
├── security/            # Access control
├── data/                # Default data
├── demo/                # Demo data
├── static/              # Web assets (JS, CSS, images)
├── wizard/              # Transient models for wizards
├── report/              # Report definitions
├── tests/               # Unit tests
└── i18n/                # Translations
```

## Module Naming Conventions

### Technical Name (module_name)
- Lowercase letters and underscores only
- No spaces or special characters
- Descriptive and unique
- Examples: `custom_inventory`, `hr_attendance_extension`

### Human-Readable Name
- Title case
- Spaces allowed
- Shown in Apps menu
- Examples: `Custom Inventory`, `HR Attendance Extension`

## __manifest__.py Structure

The manifest file is required for every module:

```python
{
    'name': 'Module Title',           # Required: Display name
    'version': 'X.Y.Z.W.V',           # Required: Version number
    'category': 'Category',            # Module category
    'summary': 'Short description',    # One-line summary
    'description': """Long description""",
    'author': 'Author Name',
    'website': 'https://example.com',
    'license': 'LGPL-3',              # License type
    'depends': ['base'],              # Required dependencies
    'data': [],                       # Data files to load
    'demo': [],                       # Demo data files
    'assets': {},                     # Web assets for the target version
    'installable': True,              # Can be installed
    'application': False,             # Is a full app
    'auto_install': False,            # Auto-install with dependencies
}
```

## IMPORTANT: Data File Ordering

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  The ORDER of files in the 'data' list is CRITICAL.                          ║
║  A resource can ONLY be referenced AFTER it has been defined.                ║
║                                                                              ║
║  Incorrect order will cause installation errors!                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Correct Order in Manifest

```python
'data': [
    # 1. Security groups FIRST (define groups before referencing them)
    'security/custom_module_security.xml',

    # 2. Access rights (reference the groups defined above)
    'security/ir.model.access.csv',

    # 3. Data files (sequences, configuration)
    'data/custom_module_data.xml',

    # 4. Views (may reference groups for visibility)
    'views/model_views.xml',

    # 5. Menu items LAST (reference actions defined in views)
    'views/menuitems.xml',
],
```

### Why Order Matters

When Odoo loads a module:
1. Files are processed in the order listed in `data`
2. XML IDs become available only after the file is loaded
3. Referencing an undefined ID causes an error

**Example Error (wrong order):**
```
ValueError: External ID not found in the system: custom_module.group_manager
```
This happens when a view references a group that's defined in a file listed AFTER the view file.

### Order Within XML Files

The same rule applies inside XML files:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- CORRECT: Define group BEFORE using it -->
    <record id="group_manager" model="res.groups">
        <field name="name">Manager</field>
    </record>

    <!-- This can now reference group_manager -->
    <record id="rule_manager" model="ir.rule">
        <field name="groups" eval="[(4, ref('group_manager'))]"/>
    </record>
</odoo>
```

## XML Data Files & Directives

According to the official Odoo Data Files specification (`developer/reference/backend/data.html`), Odoo loads static and default data using specialized XML tags and attributes:

### 1. The `<record>` Element
Defines an ORM record to insert or update:
```xml
<record id="sale_order_priority_normal" model="sale.order.priority" forcecreate="0">
    <field name="name">Normal</field>
    <field name="sequence">10</field>
</record>
```
- **`id`**: Unique XML ID (external ID) prefixed with module name when referenced externally.
- **`model`**: Target ORM model technical name.
- **`forcecreate`**: When `"0"` or `False`, Odoo will not recreate this record during module upgrades if a database administrator deleted it. Defaults to `"1"`.

### 2. Field Value Attributes
```xml
<!-- 1. Direct scalar value -->
<field name="name">Standard Service</field>

<!-- 2. Python expression evaluation (eval) -->
<field name="active" eval="True"/>
<field name="sequence" eval="20"/>
<field name="date" eval="time.strftime('%Y-%m-01')"/>
<!-- Many2many commands via Command API or legacy tuples -->
<field name="group_ids" eval="[Command.link(ref('base.group_user'))]"/>

<!-- 3. Direct XML ID reference (ref) -->
<field name="company_id" ref="base.main_company"/>

<!-- 4. Dynamic ORM search lookup (search) -->
<field name="currency_id" search="[('name', '=', 'EUR')]"/>

<!-- 5. Binary file content (type='file' or 'base64') -->
<field name="image_1920" type="file" file="custom_module/static/src/img/default_avatar.png"/>
```

### 3. The `<function>` Tag (Executing Python on Install/Upgrade)
Invokes a model method dynamically during data loading. Useful for initializing data, syncing sequences, or executing setup routines:
```xml
<!-- Call a method without arguments -->
<function model="custom.module.installer" name="_post_init_setup"/>

<!-- Call a method passing arguments via eval (first argument is model recordset or arguments list) -->
<function model="ir.config_parameter" name="set_param"
          eval="['custom_module.api_endpoint', 'https://api.example.com/v1']"/>
```

### 4. The `<delete>` Tag (Clean Record Removal)
Deletes obsolete records during module upgrades without requiring custom SQL scripts:
```xml
<!-- Delete by external ID -->
<delete model="ir.ui.menu" id="custom_module.obsolete_legacy_menu"/>

<!-- Delete by search domain -->
<delete model="ir.rule" search="[('name', '=', 'Legacy User Restricted Rule')]"/>
```

### 5. `noupdate="1"` vs `noupdate="0"`
Controls how Odoo handles records during subsequent module upgrades (`odoo-bin -u <module>`):
```xml
<!-- Default data (user-editable, skipped on upgrade) -->
<odoo noupdate="1">
    <record id="default_system_param" model="ir.config_parameter">
        <field name="key">custom.timeout</field>
        <field name="value">30</field>
    </record>
</odoo>

<!-- System data / Views / Menus (overwritten on every upgrade) -->
<odoo noupdate="0">
    <record id="action_custom_orders" model="ir.actions.act_window">
        ...
    </record>
</odoo>
```
- **`noupdate="1"`**: Created only on initial module installation. If a user edits or deletes this record in the database, subsequent module upgrades (`-u`) will **not** overwrite or restore it.
- **`noupdate="0"`** (Default): Reset to the XML definition on every module upgrade.

### Version Numbering

Format: `ODOO_VERSION.MAJOR.MINOR.PATCH`

- `18.0.1.0.0` - Odoo 18.0, version 1.0.0
- `17.0.2.1.3` - Odoo 17.0, version 2.1.3

## Model Types

### models.Model
- Persistent data stored in database
- Has database table
- Used for business entities

### models.TransientModel
- Temporary data (wizards)
- Auto-cleaned by scheduler
- Used for user interactions

### models.AbstractModel
- No database table
- Used for mixins
- Provides shared functionality

## Essential Mixins

### mail.thread
Enables chatter (messages, followers):
```python
_inherit = ['mail.thread']
```

### mail.activity.mixin
Enables scheduled activities:
```python
_inherit = ['mail.activity.mixin']
```

### portal.mixin
Enables portal access:
```python
_inherit = ['portal.mixin']
```

## Field Types

| Type | Description | Example |
|------|-------------|---------|
| Char | Short text | `fields.Char()` |
| Text | Long text | `fields.Text()` |
| Boolean | True/False | `fields.Boolean()` |
| Integer | Whole number | `fields.Integer()` |
| Float | Decimal number | `fields.Float()` |
| Monetary | Currency amount | `fields.Monetary()` |
| Date | Date only | `fields.Date()` |
| Datetime | Date and time | `fields.Datetime()` |
| Selection | Dropdown | `fields.Selection()` |
| Many2one | Single relation | `fields.Many2one()` |
| One2many | Multiple relations | `fields.One2many()` |
| Many2many | Multiple relations | `fields.Many2many()` |
| Binary | File/image | `fields.Binary()` |
| Html | Rich text | `fields.Html()` |

## View Types

| Type | Purpose |
|------|---------|
| form | Single record editing |
| tree | List of records |
| kanban | Card-based view |
| search | Filters and grouping |
| calendar | Date-based view |
| graph | Charts and graphs |
| pivot | Pivot tables |
| gantt | Timeline view |

## Security Layers

1. **Access Rights** (ir.model.access.csv)
   - Model-level CRUD permissions

2. **Record Rules** (ir.rule)
   - Row-level filtering

3. **Field Groups**
   - Field-level visibility

4. **Menu/Action Groups**
   - UI access control

## Input Parameters Reference

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| module_name | string | Technical name (snake_case) |
| module_description | string | Human-readable description |
| odoo_version | string | Target Odoo version |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| target_apps | list | [] | Apps to extend |
| ui_stack | string | varies | UI technology |
| multi_company | boolean | false | Multi-company support |
| multi_currency | boolean | false | Multi-currency support |
| security_level | string | basic | Security level |
| performance_critical | boolean | false | Performance optimizations |
| custom_models | list | [] | Custom models to create |
| custom_fields | list | [] | Fields for existing models |
| include_tests | boolean | true | Generate tests |
| include_demo | boolean | false | Generate demo data |
| author | string | "" | Module author |
| website | string | "" | Author website |
| license | string | LGPL-3 | Module license |
| category | string | Uncategorized | Module category |

## Custom Model Definition

```json
{
  "name": "equipment.asset",
  "description": "Equipment Asset",
  "inherit_mail": true,
  "fields": [
    {
      "name": "name",
      "type": "Char",
      "required": true,
      "tracking": true
    },
    {
      "name": "serial_number",
      "type": "Char",
      "index": true
    },
    {
      "name": "status",
      "type": "Selection",
      "selection": [
        ["active", "Active"],
        ["maintenance", "Maintenance"],
        ["retired", "Retired"]
      ],
      "default": "active"
    },
    {
      "name": "purchase_date",
      "type": "Date"
    },
    {
      "name": "value",
      "type": "Monetary"
    }
  ]
}
```

## Best Practices

### Code Organization
- One model per file
- Organize fields by type (basic, relational, computed)
- Use section comments for clarity

### Naming Conventions
- Models: `module_name.model_name` (dots)
- Tables: `module_name_model_name` (underscores)
- Fields: `snake_case`
- Classes: `PascalCase`
- XML IDs: `module_name_description`

### Security First
- Always define access rights
- Use record rules for multi-tenant
- Never expose sensitive data

### Performance
- Index frequently searched fields
- Store computed fields when appropriate
- Use SQL for complex reports

### Internationalization
- Mark strings with `_()` for translation
- Use translatable field attributes
- Generate .pot files

## Common Categories

- Accounting/Finance
- Human Resources
- Sales
- Purchase
- Inventory/MRP
- Project
- Website
- Marketing
- Productivity
- Technical

## License Types

| License | Commercial Use | Source Required |
|---------|---------------|-----------------|
| LGPL-3 | Yes | Modifications only |
| AGPL-3 | Yes | All source |
| OPL-1 | Paid | No |

---

**Note**: This document is the shared 17–19 baseline. Verify version-specific
syntax against the target source before generating a module.
