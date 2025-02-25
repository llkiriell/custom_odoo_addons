# -*- coding: utf-8 -*-
{
    'name': 'Ventas de POS',
    'summary': 'Listado de ventas totales hechas por POS',
    'description': """
        Lista todas las ventas realizadas en las sesiones que se abieron en el POS.
    """,
    'version': '0.1',
    'author': "kirie",
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_tree_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'o16_pos_sales/static/src/js/pos_sales_modal.js',
        ],
    },
    'installable': True,
    'application': False,
}