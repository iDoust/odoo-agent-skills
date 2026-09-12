# Odoo field widgets

Use a built-in widget when it matches the field semantics. Verify the widget
name, options, decorations, and supported attributes in the target view source.

Common examples include status bars for workflow selections, tags for many2many
values, monetary fields with an explicit currency field, avatars for users, and
handles for sequence fields.

Widget presentation is not authorization. Use field groups, model access, and
record rules for protection, and test the server-side boundary.

Source references:

- Odoo 17 view architectures: https://www.odoo.com/documentation/17.0/developer/reference/user_interface/view_architectures.html
- Odoo 18 view architectures: https://www.odoo.com/documentation/18.0/developer/reference/user_interface/view_architectures.html
- Odoo 19 view architectures: https://www.odoo.com/documentation/19.0/developer/reference/user_interface/view_architectures.html
