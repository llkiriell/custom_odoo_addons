# -*- coding: utf-8 -*-
{
    'name': 'Unión de vistas de ventas',
    'version': '0.1',
    'summary': 'Muestra las ventas corporativas y directas en una sola vista.',
    'author': 'Kirie',
    'depends': ['sale','sale_management', 'point_of_sale'],
    'data': [
      'security/ir.model.access.csv',
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
}
