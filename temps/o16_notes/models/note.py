from odoo import models, fields

class Note(models.Model):
    _name = 'o16_notes.note'
    _description = 'Nota de usuario'

    title = fields.Char(string='Título', required=True)
    content = fields.Text(string='Contenido')
