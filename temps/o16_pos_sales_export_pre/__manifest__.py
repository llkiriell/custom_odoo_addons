# -*- coding: utf-8 -*-
{
    'name': 'Descarga de información de session POS',
    'summary': 'Añade la funcionalidad de exportar documentos POS',
    'description': """
        Añade un botón que permite exportar la información que tiene relacionada una sesión de ventas por POS
    """,
    'version': '0.1',
    'author': "shdev",
    'category': 'Sales',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_session_views.xml'
    ],
    'installable': True,
    'application': False,
}