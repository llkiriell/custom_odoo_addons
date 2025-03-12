# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Team(models.Model):
    _name = 'field_management.team'
    _description = 'Equipo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, tracking=True)
    captain_id = fields.Many2one('res.partner', string='Capitán', required=True, tracking=True, domain=[('is_player', '=', True)])
    players_ids = fields.Many2many('res.partner', string='Jugadores', domain=[('is_player', '=', True)])
    active = fields.Boolean(default=True)
    match_ids = fields.One2many('field_management.match', 'team_1_id', string='Partidos como Local')
    match_ids_2 = fields.One2many('field_management.match', 'team_2_id', string='Partidos como Visitante')
    total_matches = fields.Integer(
        string='Total de Partidos',
        compute='_compute_total_matches',
        store=True
    )
    team_image = fields.Binary(
        string='Logo del Equipo',
        attachment=True
    )

    @api.depends('match_ids', 'match_ids_2')
    def _compute_total_matches(self):
        for team in self:
            team.total_matches = len(team.match_ids) + len(team.match_ids_2)

    @api.constrains('captain_id', 'players_ids')
    def _check_captain_in_players(self):
        for team in self:
            if team.captain_id and team.captain_id not in team.players_ids:
                team.players_ids = [(4, team.captain_id.id)] 