from odoo import models

class PosSession(models.Model):
    _inherit = "pos.session"

    def show_message_test(self):
        raise models.ValidationError("Hola Mundo")