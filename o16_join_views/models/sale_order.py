from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type = fields.Selection([
        ('direct', 'Directa'),
        ('corporate', 'Corporativa')
    ], string="Tipo de Venta", default='direct')
