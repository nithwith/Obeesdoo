# Copyright 2020 Coop IT Easy SCRL fs
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    eater = fields.Selection(
        [("eater", "Eater"), ("worker_eater", "Worker and Eater")],
        string="Eater/Worker",
    )
    child_eater_ids = fields.One2many(
        "res.partner",
        "parent_eater_id",
        domain=[("eater", "=", "eater")],
    )
    parent_eater_id = fields.Many2one(
        "res.partner",
        string="Parent Worker",
        readonly=True,
        domain=[("eater", "=", "worker_eater")],
    )

    @api.constrains("eater", "parent_eater_id")
    def _check_parent_is_worker(self):
        """The parent of an eater must be a worker_eater, and worker_eaters
        cannot have parents.
        """
        for partner in self:
            parent = partner.parent_eater_id
            if partner.eater == "eater" and parent:
                if parent.eater != "worker_eater":
                    raise ValidationError(
                        _(
                            "{0} cannot be the parent of {1} because the parent"
                            " must be a worker."
                        ).format(parent.name, partner.name)
                    )
            if partner.eater == "worker_eater" and parent:
                raise ValidationError(
                    _(
                        "%s cannot have a parent worker because they are"
                        " themselves a worker."
                    )
                    % partner.name
                )

    def _new_eater(self, surname, name, email):
        partner_data = {
            "lastname": name,
            "firstname": surname,
            "eater": "eater",
            "parent_eater_id": self.id,
            "email": email,
            "country_id": self.country_id.id,
        }
        return self.env["res.partner"].create(partner_data)
