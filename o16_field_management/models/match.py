# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class Match(models.Model):
    _name = 'field_management.match'
    _description = 'Partido'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'match_date desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo Partido')
    )
    field_id = fields.Many2one(
        'field_management.field',
        string='Cancha',
        required=True,
        tracking=True
    )
    match_date = fields.Datetime(
        string='Fecha y Hora',
        required=True,
        tracking=True
    )
    team_1_id = fields.Many2one(
        'field_management.team',
        string='Equipo Local',
        required=True,
        tracking=True
    )
    team_2_id = fields.Many2one(
        'field_management.team',
        string='Equipo Visitante',
        required=True,
        tracking=True
    )
    score_team_1 = fields.Integer(
        string='Goles Local',
        default=0,
        tracking=True
    )
    score_team_2 = fields.Integer(
        string='Goles Visitante',
        default=0,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('in_progress', 'En Progreso'),
        ('done', 'Finalizado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True)
    winner_id = fields.Many2one(
        'field_management.team',
        string='Equipo Ganador',
        compute='_compute_winner',
        store=True
    )
    match_history_ids = fields.Many2many(
        'field_management.match',
        compute='_compute_match_history',
        string='Historial de Enfrentamientos'
    )
    has_previous_matches = fields.Boolean(
        string='Tiene Enfrentamientos Previos',
        compute='_compute_match_history',
        store=True
    )
    duration = fields.Float(
        string='Duración (horas)',
        default=1.0,
        required=True
    )
    rental_id = fields.Many2one(
        'field_management.rental',
        string='Alquiler',
        tracking=True,
        domain="[('state', 'in', ['draft', 'in_progress']), ('field_id', '=', field_id), '|', '&', ('start_datetime', '<=', match_date), ('end_datetime', '>=', match_date), ('id', '=', False)]"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo Partido')) == _('Nuevo Partido'):
                vals['name'] = self.env['ir.sequence'].next_by_code('field_management.match') or _('Nuevo Partido')
        return super(Match, self).create(vals_list)

    @api.depends('score_team_1', 'score_team_2', 'state')
    def _compute_winner(self):
        for match in self:
            match.winner_id = False
            if match.state == 'done':
                if match.score_team_1 > match.score_team_2:
                    match.winner_id = match.team_1_id
                elif match.score_team_2 > match.score_team_1:
                    match.winner_id = match.team_2_id

    @api.constrains('team_1_id', 'team_2_id')
    def _check_teams(self):
        for match in self:
            if match.team_1_id == match.team_2_id:
                raise ValidationError(_('Los equipos deben ser diferentes'))

    def action_confirm(self):
        for match in self:
            if match.state != 'draft':
                raise ValidationError(_('Solo los partidos en borrador pueden ser confirmados'))
            
            # Si no hay alquiler seleccionado, crear uno nuevo
            if not match.rental_id:
                end_datetime = match.match_date + timedelta(hours=match.duration)
                rental_vals = {
                    'field_id': match.field_id.id,
                    'customer_id': match.team_1_id.captain_id.id,  # Usamos el capitán del equipo local como cliente
                    'start_datetime': match.match_date,
                    'end_datetime': end_datetime,
                    'state': 'draft',
                    'team_id': match.team_1_id.id,
                }
                rental = self.env['field_management.rental'].create(rental_vals)
                match.rental_id = rental.id
            
            match.write({'state': 'confirmed'})

    def action_start(self):
        for match in self:
            if match.state != 'confirmed':
                raise ValidationError(_('Solo los partidos confirmados pueden iniciar'))
            match.write({'state': 'in_progress'})

    def action_done(self):
        for match in self:
            if match.state != 'in_progress':
                raise ValidationError(_('Solo los partidos en progreso pueden ser finalizados'))
            match.write({'state': 'done'})

    def action_cancel(self):
        for match in self:
            if match.state == 'done':
                raise ValidationError(_('No se puede cancelar un partido finalizado'))
            match.write({'state': 'cancelled'})

    def action_draft(self):
        for match in self:
            if match.state != 'cancelled':
                raise ValidationError(_('Solo los partidos cancelados pueden volver a borrador'))
            match.write({'state': 'draft'})

    @api.depends('team_1_id', 'team_2_id')
    def _compute_match_history(self):
        for match in self:
            match.match_history_ids = False
            match.has_previous_matches = False
            
            if not match.team_1_id or not match.team_2_id:
                continue

            domain = [
                ('state', '=', 'done'),
                '|',
                '&', ('team_1_id', '=', match.team_1_id.id),
                ('team_2_id', '=', match.team_2_id.id),
                '&', ('team_1_id', '=', match.team_2_id.id),
                ('team_2_id', '=', match.team_1_id.id)
            ]

            # Solo excluir el registro actual si ya existe en la base de datos
            if not match._origin.id:
                history = self.search(domain, order='match_date desc')
            else:
                domain = [('id', '!=', match._origin.id)] + domain
                history = self.search(domain, order='match_date desc')

            match.match_history_ids = history
            match.has_previous_matches = bool(history) 