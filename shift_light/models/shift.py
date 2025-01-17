import itertools
import json
from datetime import datetime, time, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class ShiftShift(models.Model):
    _name = "shift.shift"
    _description = "shift.shift"
    _inherit = ["mail.thread"]
    _order = "start_time asc"

    def _get_selection_status(self):
        return [
            ("open", _("Open")),
            ("reserved", _("Reserved")),
            ("need_help", _("SOS")),
        ]

    def _get_color_mapping(self, state):
        return {
            "open": 0,
            "done": 10,
            "need_help": 9,
        }[state]

    name = fields.Char(tracking=True)
    task_template_id = fields.Many2one("shift.template")
    planning_id = fields.Many2one(related="task_template_id.planning_id", store=True)
    task_type_id = fields.Many2one("shift.type", string="Task Type")
    partner_id = fields.Many2one("res.partner", tracking=True)
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

    @api.depends("state")
    def _compute_color(self):
        for rec in self:
            rec.color = self._get_color_mapping(rec.state)

    def action_reserved(self):
        for rec in self:
            rec.state = "reserved"

    def action_need_help(self):
        for rec in self:
            rec.state = "need_help"

