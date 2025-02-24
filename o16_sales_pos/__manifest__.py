# -*- coding: utf-8 -*-
{
    'name': "Ventas de POS",
    'summary': "Lista todas las ventas realizaadas en las sesiones que hubieron en POS",
    'description': "Permite mostrar todas las ventas hechas en una sesiones de POS",
    'author': "kirie",
    'category': 'Point of Sale',
    'version': '0.1',
    'depends': ['base','point_of_sale'],
    'data': [
        'views/sale_pos_view.xml',
        'views/pos_session_view.xml'
    ],
    'installable': True,
    'application': False,
}
