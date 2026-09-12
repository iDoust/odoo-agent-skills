# Odoo mail and notifications

- Declare mail dependencies explicitly and use `mail.thread` and activities
  only when the model actually needs them.
- Track important fields deliberately; do not expose sensitive values through
  chatter, followers, templates, or notifications.
- Define email templates in XML with stable XML IDs and test rendered output,
  recipients, access context, and missing-address behavior.
- Use escaped template output by default and make any trusted HTML boundary
  explicit.
- Queue bulk mail and notifications where appropriate, and avoid sending one
  synchronous message per record in a large batch.
- Test follower, activity, access, company, and unsubscribe behavior when the
  change affects communication.

Source references:

- Odoo 17 messaging reference: https://www.odoo.com/documentation/17.0/developer/reference/backend/mixins.html
- Odoo 18 messaging reference: https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins.html
- Odoo 19 messaging reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/mixins.html

## Related References

- [Mixins Reference (`mail.thread`, `mail.activity.mixin`)](../orm/mixins.md)
- [Scheduled Actions & Cron (Mail Queue)](cron.md)
- [Operations Directory Index](README.md)
