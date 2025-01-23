from odoo import api, fields, models
from datetime import datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _

class ShiftShift(models.Model):
    _name = "shift.shift"
    _description = "shift.shift"
    _inherit = ["mail.thread"]
    _order = "start_time asc"

    def _compute_display_name(self):
        for rec in self:
            if rec.partner_id:
                rec.display_name = ("%s %s")% (rec.partner_name, rec.partner_phone or ' ')
            else:
                rec.display_name = " "

    def _get_selection_status(self):
        return [
            ("open", _("Open")),
            ("reserved", _("Reserved")),
            ("need_help", _("SOS")),
        ]

    def _get_color_mapping(self, state):
        return {
            "open": 1,
            "reserved": 10,
            "need_help": 3,
        }[state]

    name = fields.Char(tracking=True)
    shift_template_id = fields.Many2one("shift.template")
    planning_id = fields.Many2one(related="shift_template_id.planning_id", store=True)
    shift_type_id = fields.Many2one("shift.type", string="Shift Type")
    partner_id = fields.Many2one("res.partner", tracking=True)
    partner_name = fields.Char(related='partner_id.name', related_sudo=True)
    partner_phone = fields.Char(related='partner_id.phone', related_sudo=True)
    start_time = fields.Datetime(tracking=True, index=True, required=True)
    end_time = fields.Datetime(tracking=True, required=True)
    state = fields.Selection(
        selection=lambda x: x._get_selection_status(),
        default="open",
        required=True,
        tracking=True,
        group_expand="_expand_states",
    )
    color = fields.Integer(compute="_compute_color")

    def _expand_states(self, states, domain, order):
        return [key for key, val in self._fields["state"].selection(self)]
    
    def write(self, vals):
        print(vals)
        if not self.env.user.has_group('shift_light.group_shift_management') and vals.get('start_time') or vals.get('end_time'):
            raise UserError(_("You can't change shift informations."))
        return super().write(vals)

    @api.depends("state")
    def _compute_color(self):
        for rec in self:
            rec.color = self._get_color_mapping(rec.state)

    def get_action(self, initial_date=False):
        context = {}
        if initial_date:
            context['initial_date'] = initial_date
        return {
            'name': _('Shifts'),
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'shift.shift',
            'view_mode': 'calendar',
            'context': context
        }

    def action_reserved(self):
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = self.env.user.partner_id
            rec.state = "reserved"
        return self.get_action(rec[0].start_time)

    def action_need_help(self):
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = self.env.user.partner_id
            rec.state = "need_help"
        return self.get_action(rec[0].start_time)

    def action_unsubscribe(self):
        for rec in self:
            rec.partner_id = False
            rec.state = "open"
        return self.get_action(rec[0].start_time)

