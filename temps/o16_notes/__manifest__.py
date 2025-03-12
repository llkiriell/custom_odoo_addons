# -*- coding: utf-8 -*-
{
    'name': "Módulo básico de notas o recordatorios en ventas",
    'summary': "Vista de notas de prueba para familiarizarse con el entorno",
    'description': "Permite mostrar notas o recordatorios simples",
    'author': "kirie",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/note_view.xml',
    ],
    'installable': True,
    'application': False,
}
