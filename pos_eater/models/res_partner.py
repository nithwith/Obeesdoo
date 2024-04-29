from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def get_eater(self):
        self.ensure_one()
        # todo check for max eater
        return [eater.name for eater in self.child_eater_ids]
