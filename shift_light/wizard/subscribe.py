from odoo import _, fields, models
from odoo.exceptions import UserError


class StatusActionMixin(models.AbstractModel):
    _name = "shift.action_mixin"
    _description = "shift.action_mixin"

    cooperator_id = fields.Many2one(
        "res.partner",
        default=lambda self: self.env["res.partner"].browse(
            self._context.get("active_id")
        ),
        required=True,
    )

    def _check(self, group="shift.group_shift_management"):
        self.ensure_one()
        if not self.env.user.has_group(group):
            raise UserError(_("You don't have the required access for this operation."))
        if (
            self.cooperator_id == self.env.user.partner_id
            and not self.env.user.has_group("shift.group_cooperative_admin")
        ):
            raise UserError(_("You cannot perform this operation on yourself"))
        return self.with_context(real_uid=self._uid)
