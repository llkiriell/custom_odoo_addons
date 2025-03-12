# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class Rental(models.Model):
    _name = 'field_management.rental'
    _description = 'Alquiler de Cancha'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(
        string='Referencia', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('Nuevo Alquiler')
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Cliente',
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
        ('draft', 'Borrador'),
        ('in_progress', 'En Progreso'),
        ('done', 'Completado'),
        ('cancelled', 'Cancelado')
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
    reservation_id = fields.Many2one(
        'field_management.reservation',
        string='Reserva Origen',
        readonly=True
    )
    match_ids = fields.One2many(
        'field_management.match',
        'rental_id',
        string='Partidos'
    )
    notes = fields.Text(
        string='Notas',
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo Alquiler')) == _('Nuevo Alquiler'):
                vals['name'] = self.env['ir.sequence'].next_by_code('field_management.rental') or _('Nuevo Alquiler')
        return super(Rental, self).create(vals_list)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rental in self:
            if rental.start_datetime and rental.end_datetime:
                duration = (rental.end_datetime - rental.start_datetime).total_seconds() / 3600
                rental.duration = round(duration, 2)
            else:
                rental.duration = 0.0

    @api.depends('duration', 'field_id.price_per_hour')
    def _compute_total_amount(self):
        for rental in self:
            if rental.duration and rental.field_id:
                rental.total_amount = rental.duration * rental.field_id.price_per_hour
            else:
                rental.total_amount = 0.0

    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for rental in self:
            if rental.start_datetime and rental.end_datetime:
                if rental.start_datetime >= rental.end_datetime:
                    raise ValidationError(_('La fecha de fin debe ser posterior a la fecha de inicio.'))
                
                duration = (rental.end_datetime - rental.start_datetime).total_seconds() / 3600
                if duration < 1:
                    raise ValidationError(_('El alquiler debe ser de al menos 1 hora.'))
                if duration > 4:
                    raise ValidationError(_('El alquiler no puede exceder las 4 horas.'))

    @api.constrains('field_id', 'start_datetime', 'end_datetime', 'state')
    def _check_availability(self):
        for rental in self:
            if rental.state in ['draft', 'in_progress']:
                if rental.field_id and rental.start_datetime and rental.end_datetime:
                    # Verificar otros alquileres
                    domain = [
                        ('field_id', '=', rental.field_id.id),
                        ('state', 'in', ['in_progress']),
                        ('id', '!=', rental.id),
                        '|',
                        '&', ('start_datetime', '<', rental.end_datetime),
                        ('end_datetime', '>', rental.start_datetime),
                        '&', ('start_datetime', '=', rental.start_datetime),
                        ('end_datetime', '=', rental.end_datetime)
                    ]
                    
                    conflicting_rentals = self.search_count(domain)
                    if conflicting_rentals > 0:
                        return {
                            'type': 'ir.actions.act_window',
                            'name': _('Crear Reserva'),
                            'res_model': 'field_management.reservation',
                            'view_mode': 'form',
                            'target': 'new',
                            'context': {
                                'default_field_id': rental.field_id.id,
                                'default_start_datetime': rental.start_datetime,
                                'default_end_datetime': rental.end_datetime,
                                'default_customer_id': rental.customer_id.id if rental.customer_id else False,
                                'default_team_id': rental.team_id.id if rental.team_id else False,
                                'default_players_ids': [(6, 0, rental.players_ids.ids)] if rental.players_ids else False,
                            }
                        }
                    
                    if rental.field_id.state == 'maintenance':
                        raise ValidationError(_('La cancha está en mantenimiento y no puede ser alquilada.'))

    def action_start(self):
        for rental in self:
            if rental.state != 'draft':
                raise ValidationError(_('Solo los alquileres en borrador pueden iniciarse.'))
            rental.write({'state': 'in_progress'})
            rental.field_id.write({'state': 'occupied'})

    def action_done(self):
        for rental in self:
            if rental.state != 'in_progress':
                raise ValidationError(_('Solo los alquileres en progreso pueden ser completados.'))
            rental.write({'state': 'done'})
            rental.field_id.write({'state': 'available'})

    def action_cancel(self):
        for rental in self:
            if rental.state == 'done':
                raise ValidationError(_('No se puede cancelar un alquiler completado.'))
            rental.write({'state': 'cancelled'})
            if rental.state == 'in_progress':
                rental.field_id.write({'state': 'available'})

    def action_draft(self):
        for rental in self:
            if rental.state != 'cancelled':
                raise ValidationError(_('Solo los alquileres cancelados pueden volver a estado borrador.'))
            rental.write({'state': 'draft'})

    def action_create_reservation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Reserva'),
            'res_model': 'field_management.reservation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_field_id': self.field_id.id,
                'default_start_datetime': self.start_datetime,
                'default_end_datetime': self.end_datetime,
                'default_customer_id': self.customer_id.id if self.customer_id else False,
                'default_team_id': self.team_id.id if self.team_id else False,
                'default_players_ids': [(6, 0, self.players_ids.ids)] if self.players_ids else False,
            }
        }

    @api.constrains('players_ids')
    def _check_players_capacity(self):
        for rental in self:
            if len(rental.players_ids) > rental.field_id.capacity:
                raise ValidationError(_('El número de jugadores excede la capacidad de la cancha')) 