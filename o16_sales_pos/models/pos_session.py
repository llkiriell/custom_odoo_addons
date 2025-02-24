from odoo import models, api
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = "pos.session"

    @api.model
    def action_descargar(self):
        raise UserError("Este es un mensaje de prueba.")

