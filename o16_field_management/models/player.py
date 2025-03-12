# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_player = fields.Boolean(
        string='Es Jugador',
        default=False,
        help='Marcar si este contacto es un jugador'
    )
    team_ids = fields.Many2many(
        'field_management.team',
        string='Equipos',
        help='Equipos en los que participa el jugador'
    )
    match_ids = fields.Many2many(
        'field_management.match',
        string='Partidos Jugados',
        help='Historial de partidos del jugador'
    )
    reservation_ids = fields.One2many(
        'field_management.reservation',
        'customer_id',
        string='Reservas'
    )
    total_matches = fields.Integer(
        string='Total de Partidos',
        compute='_compute_total_matches',
        store=True
    )
    position = fields.Selection([
        ('goalkeeper', 'Portero'),
        ('defender', 'Defensa'),
        ('midfielder', 'Mediocampista'),
        ('forward', 'Delantero')
    ], string='Posición Preferida')

    @api.depends('match_ids')
    def _compute_total_matches(self):
        for player in self:
            player.total_matches = len(player.match_ids) 