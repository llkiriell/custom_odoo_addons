# -*- coding: utf-8 -*-
{
    'name': 'Gestión de Canchas',
    'version': '16.0.1.0.0',
    'category': 'Services/Field Management',
    'summary': 'Sistema de gestión para alquiler de canchas de fútbol',
    'description': """
        Módulo para la gestión de canchas de fútbol que permite:
        * Administración de canchas
        * Reservas y alquileres
        * Gestión de equipos y jugadores
        * Control de partidos
        * Sistema de reservas
        * Panel de control con estadísticas
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'mail',
        'contacts',
        'account',
        'web',
        'board',
    ],
    'data': [
        'security/field_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/field_views.xml',
        'views/reservation_views.xml',
        'views/team_views.xml',
        'views/player_views.xml',
        'views/match_views.xml',
        'views/rental_views.xml',
        'views/dashboard_views.xml',
        'views/menu_items.xml',
        'report/reservation_report.xml',
    ],
    'demo': [
        'data/field_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'o16_field_management/static/src/css/field_management.css',
            'o16_field_management/static/src/js/dashboard.js',
        ],
        'web.assets_qweb': [
            'o16_field_management/static/src/xml/dashboard.xml',
        ],
    },
    'images': ['static/description/banner.png'],
}
