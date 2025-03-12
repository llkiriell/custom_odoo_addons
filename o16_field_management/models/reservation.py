# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class Reservation(models.Model):
    _name = 'field_management.reservation'
    _description = 'Reserva de Cancha'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(
        string='Referencia', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('Nueva Reserva')
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )
    field_id = fields.Many2one(
        'field_management.field',
        string='Cancha',
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='field_id.currency_id',
        string='Moneda',
        store=True,
        readonly=True
    )
    start_datetime = fields.Datetime(
        string='Fecha y Hora de Inicio',
        required=True,
        tracking=True
    )
    end_datetime = fields.Datetime(
        string='Fecha y Hora de Fin',
        required=True,
        tracking=True
    )
    duration = fields.Float(
        string='Duración (horas)',
        compute='_compute_duration',
        store=True
    )
    total_amount = fields.Monetary(
        string='Monto Total',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )
    state = fields.Selection([
        ('draft', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('done', 'Completada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', default='draft', required=True, tracking=True)
    team_id = fields.Many2one(
        'field_management.team',
        string='Equipo',
        tracking=True
    )
    players_ids = fields.Many2many(
        'res.partner',
        string='Jugadores',
        domain=[('is_player', '=', True)]
    )
    match_id = fields.Many2one(
        'field_management.match',
        string='Partido',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nueva Reserva')) == _('Nueva Reserva'):
                vals['name'] = self.env['ir.sequence'].next_by_code('field_management.reservation') or _('Nueva Reserva')
        return super(Reservation, self).create(vals_list)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for reservation in self:
            if reservation.start_datetime and reservation.end_datetime:
                duration = (reservation.end_datetime - reservation.start_datetime).total_seconds() / 3600
                reservation.duration = round(duration, 2)
            else:
                reservation.duration = 0.0

    @api.depends('duration', 'field_id.price_per_hour')
    def _compute_total_amount(self):
        for reservation in self:
            if reservation.duration and reservation.field_id:
                reservation.total_amount = reservation.duration * reservation.field_id.price_per_hour
            else:
                reservation.total_amount = 0.0

    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for reservation in self:
            if reservation.start_datetime and reservation.end_datetime:
                if reservation.start_datetime >= reservation.end_datetime:
                    raise ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio.'))
                
                if reservation.state == 'draft' and reservation.start_datetime < fields.Datetime.now():
                    raise ValidationError(_('No se pueden crear reservas con fecha de inicio en el pasado.'))

                duration = (reservation.end_datetime - reservation.start_datetime).total_seconds() / 3600
                if duration < 1:
                    raise ValidationError(_('La reserva debe ser de al menos 1 hora.'))
                if duration > 4:
                    raise ValidationError(_('La reserva no puede exceder las 4 horas.'))

    @api.constrains('field_id', 'start_datetime', 'end_datetime', 'state')
    def _check_availability(self):
        for reservation in self:
            if reservation.state in ['draft', 'confirmed']:
                if reservation.field_id and reservation.start_datetime and reservation.end_datetime:
                    domain = [
                        ('field_id', '=', reservation.field_id.id),
                        ('state', 'not in', ['cancelled', 'draft']),
                        ('id', '!=', reservation.id),
                        '|',
                        '&', ('start_datetime', '<', reservation.end_datetime),
                        ('end_datetime', '>', reservation.start_datetime),
                        '&', ('start_datetime', '=', reservation.start_datetime),
                        ('end_datetime', '=', reservation.end_datetime)
                    ]
                    
                    conflicting_reservations = self.search_count(domain)
                    if conflicting_reservations > 0:
                        raise ValidationError(_('La cancha no está disponible para el período seleccionado.'))
                    
                    if reservation.field_id.state == 'maintenance':
                        raise ValidationError(_('La cancha está en mantenimiento y no puede ser reservada.'))

    def action_confirm(self):
        for reservation in self:
            if reservation.state != 'draft':
                raise ValidationError(_('Solo las reservas en estado borrador pueden ser confirmadas.'))
            
            # Crear alquiler automáticamente
            rental_vals = {
                'field_id': reservation.field_id.id,
                'customer_id': reservation.customer_id.id,
                'start_datetime': reservation.start_datetime,
                'end_datetime': reservation.end_datetime,
                'team_id': reservation.team_id.id if reservation.team_id else False,
                'players_ids': [(6, 0, reservation.players_ids.ids)] if reservation.players_ids else False,
                'reservation_id': reservation.id,
                'state': 'draft'
            }
            self.env['field_management.rental'].create(rental_vals)
            reservation.write({'state': 'confirmed'})

    def action_done(self):
        for reservation in self:
            if reservation.state != 'confirmed':
                raise ValidationError(_('Solo las reservas confirmadas pueden ser marcadas como completadas.'))
            reservation.write({'state': 'done'})

    def action_cancel(self):
        for reservation in self:
            if reservation.state == 'done':
                raise ValidationError(_('No se puede cancelar una reserva completada.'))
            reservation.write({'state': 'cancelled'})

    def action_draft(self):
        for reservation in self:
            if reservation.state != 'cancelled':
                raise ValidationError(_('Solo las reservas canceladas pueden volver a estado borrador.'))
            reservation.write({'state': 'draft'})

    @api.constrains('players_ids')
    def _check_players_capacity(self):
        for reservation in self:
            if len(reservation.players_ids) > reservation.field_id.capacity:
                raise ValidationError(_('El número de jugadores excede la capacidad de la cancha')) 