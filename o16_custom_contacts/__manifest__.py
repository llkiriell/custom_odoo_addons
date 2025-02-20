# -*- coding: utf-8 -*-
{
    'name': "Búsqueda por Tipo de Identificación en Contactos",
    'summary': """
        Agrega el campo Tipo de Identificación a la búsqueda de Contactos.
    """,
    'description': """
        Permite buscar contactos por su tipo de identificación en la vista de lista.
    """,
    'author': "kirill",
    'website': "http://www.tu-sitio-web.com",
    'category': 'Sales', 
    'version': '0.1',
    'depends': ['base', 'contacts', 'l10n_latam_base'], 
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}