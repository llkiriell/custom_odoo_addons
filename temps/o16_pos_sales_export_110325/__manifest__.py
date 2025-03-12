# -*- coding: utf-8 -*-
{
    'name': 'Exportador de documentos de session POS',
    'summary': 'Añade la funcionalidad de exportar documentos POS',
    'description': """
        Añade un botón que permite exportar la información que tiene relacionada una sesión de ventas por POS
    """,
    'version': '0.1',
    'author': "sh",
    'category': 'Sales',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_session_exporter_view.xml',
        'views/export_pos_sales_view.xml',
    ],
    'installable': True,
    'application': False,
}