from odoo import _, fields, models


class InstantiatePlanning(models.TransientModel):
    _name = "shift.generate_planning"
    _description = "shift.generate_planning"

    def _get_planning(self):
        return self._context.get("active_id")

    date_start = fields.Date("First Day of planning (should be Monday)", required=True)
    planning_id = fields.Many2one(
        "shift.planning", readonly=True, default=_get_planning
    )

    def generate_shift(self):
        self.ensure_one()
        self = self.with_context(visualize_date=self.date_start, tracking_disable=True)
        shifts = self.planning_id.shift_template_ids.generate_shift_day()
        return {
            "name": _("Generated Shift"),
            "type": "ir.actions.act_window",
            "view_mode": "calendar,tree,form,pivot",
            "res_model": "shift.shift",
            "target": "current",
            "domain": [("id", "in", shifts.ids)],
        }


    def action_grant_access(self):
        """Grant the portal access to the partner.

        If the partner has no linked user, we will create a new one in the same company
        as the partner (or in the current company if not set).

        An invitation email will be sent to the partner.
        """
        self.ensure_one()
        self._assert_user_email_uniqueness()

        if self.is_portal or self.is_internal:
            raise UserError(_('The partner "%s" already has the portal access.', self.partner_id.name))

        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')

        self._update_partner_email()
        user_sudo = self.user_id.sudo()

        if not user_sudo:
            # create a user if necessary and make sure it is in the portal group
            company = self.partner_id.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id)._create_user()

        if not user_sudo.active or not self.is_portal:
            user_sudo.write({'active': True, 'groups_id': [(4, group_portal.id), (3, group_public.id)]})
            # prepare for the signup process
            user_sudo.partner_id.signup_prepare()

        self.with_context(active_test=True)._send_email()

        return self.action_refresh_modal()