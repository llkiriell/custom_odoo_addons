# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Field(models.Model):
    _name = 'field_management.field'
    _description = 'Campo de Fútbol'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, tracking=True)
    location = fields.Text(string='Ubicación', required=True, tracking=True)
    description = fields.Html(string='Descripción', tracking=True)
    image = fields.Binary(string='Imagen', attachment=True)
    price_per_hour = fields.Float(
        string='Precio por Hora', 
        required=True, 
        tracking=True,
        help='Precio de alquiler por hora en la moneda de la compañía'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
        tracking=True
    )
    state = fields.Selection([
        ('available', 'Disponible'),
        ('occupied', 'Ocupada'),
        ('maintenance', 'Mantenimiento')
    ], string='Estado', default='available', required=True, tracking=True)
    capacity = fields.Integer(
        string='Capacidad Máxima', 
        required=True,
        tracking=True,
        help='Número máximo de jugadores permitidos en la cancha'
    )
    active = fields.Boolean(default=True)
    reservation_ids = fields.One2many(
        'field_management.reservation',
        'field_id',
        string='Reservas'
    )

    def check_availability(self, start_datetime, end_datetime):
        """
        Verifica la disponibilidad de la cancha para un período específico
        Retorna True si está disponible, False si no lo está
        """
        self.ensure_one()
        
        # Si la cancha está en mantenimiento, no está disponible
        if self.state == 'maintenance':
            return False
            
        # Buscar reservaciones que se solapan
        domain = [
            ('field_id', '=', self.id),
            ('state', 'not in', ['cancelled', 'draft']),  # Ignorar reservas canceladas y borradores
            '|',
            '&', ('start_datetime', '<', end_datetime), ('end_datetime', '>', start_datetime),
            '&', ('start_datetime', '=', start_datetime), ('end_datetime', '=', end_datetime)
        ]
        
        conflicting_reservations = self.env['field_management.reservation'].search_count(domain)
        return conflicting_reservations == 0

    @api.constrains('capacity')
    def _check_capacity(self):
        for field in self:
            if field.capacity <= 0:
                raise ValidationError(_('La capacidad debe ser mayor que 0'))

    @api.constrains('price_per_hour')
    def _check_price(self):
        for field in self:
            if field.price_per_hour <= 0:
                raise ValidationError(_('El precio por hora debe ser mayor que 0')) 