# XML view patterns

Inspect the inherited view architecture in the target version before writing
an XPath or changing a modifier.

## View inheritance

- Find the parent view, its module dependency, XML ID, priority, and complete
  inheritance chain.
- Prefer a narrow XPath anchored on stable semantic attributes.
- Verify that the XPath matches exactly the intended node and survives the
  target version's parent view.
- Keep actions, menus, groups, and references on stable XML IDs.

```xml
<record id="view_my_model_form" model="ir.ui.view">
    <field name="name">my.model.form</field>
    <field name="model">my.model</field>
    <field name="inherit_id" ref="base_module.view_parent_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='partner_id']" position="after">
            <field name="reference"/>
        </xpath>
    </field>
</record>
```

## Expressions and fields

Supported Odoo versions use Python expressions for modifiers such as
`invisible`, `readonly`, and `required`.

```xml
<field name="state" invisible="not state"/>
<field name="reference" readonly="state != 'draft'"/>
<field name="partner_id" required="type == 'customer'"/>
<group invisible="not show_details">
    <field name="detail"/>
</group>
```

Fields used by an expression must be present in the view, even if they are
invisible. Relational sub-views have their own context and may use `parent`;
verify the exact target view schema.

## List views: `<tree>` vs `<list>`

The root tag for list views depends on the target version:
- **Odoo 17**: Root tag is `<tree>` (`<tree string="..."> ... </tree>`).
- **Odoo 18+**: Root tag is `<list>` (`<list string="..."> ... </list>`).

When inheriting list views via XPath:
- In Odoo 17: `<xpath expr="//tree" ...>`
- In Odoo 18+: `<xpath expr="//list" ...>` (or anchor on a specific `<field name="...">`).

**Column visibility**: In list views, use `column_invisible="condition"` instead of `invisible="condition"` to hide both the column header and cells.

## Chatter: `<div class="oe_chatter">` vs `<chatter/>`

- **Odoo 17**: Must declare chatter via `<div class="oe_chatter">` containing explicit child fields:
  ```xml
  <div class="oe_chatter">
      <field name="message_follower_ids"/>
      <field name="activity_ids"/>
      <field name="message_ids"/>
  </div>
  ```
- **Odoo 18+**: Uses the self-closing `<chatter/>` tag:
  ```xml
  <chatter reload_on_attachment="True"/>
  ```

## Actions and menus

```xml
<record id="my_model_action" model="ir.actions.act_window">
    <field name="name">My Models</field>
    <field name="res_model">my.model</field>
    <field name="view_mode">list,form</field>
</record>

<menuitem id="my_model_menu" name="My Models"
          parent="my_module_menu_root" action="my_model_action"/>
```

Use the target version's view type names and manifest conventions; inspect the
matching official source instead of assuming that a view string is portable.

## Validation

- Upgrade or install the module after XML changes.
- Test inherited views with the affected groups and companies.
- Check that hidden fields are not being mistaken for access control.
- Render the relevant form, list, search, kanban, report, and portal views.

Sources:

- Odoo 17 view architectures: https://www.odoo.com/documentation/17.0/developer/reference/user_interface/view_architectures.html
- Odoo 18 view architectures: https://www.odoo.com/documentation/18.0/developer/reference/user_interface/view_architectures.html
- Odoo 19 view architectures: https://www.odoo.com/documentation/19.0/developer/reference/user_interface/view_architectures.html
