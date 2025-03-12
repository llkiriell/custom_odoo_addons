from odoo import models, fields, api, _
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import json # Para formatear el objeto
from pprint import pformat
import logging
import re
import pytz

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        """Muestra nombre y correo en la búsqueda, pero solo correo al seleccionar"""
        if self.env.context.get('show_email_as_display_name'):
            return [(partner.id, partner.email) for partner in self if partner.email]
        return super(ResPartner, self).name_get()

class ExportPosSales(models.TransientModel):
    _name = 'export.pos.sales'
    _description = 'Export POS Sales Wizard'

    def _default_email(self):
        return self.env.user.email or False

    def _default_date_start(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            session = self.env['pos.session'].browse(active_id)
            # Retornamos la fecha de apertura de la sesión
            if session.start_at:
                return session.start_at
        return False

    def _default_date_end(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            session = self.env['pos.session'].browse(active_id)
            # Si la sesión tiene fecha de cierre, la usamos
            if session.stop_at:
                return session.stop_at
            # Si no, usamos la fecha actual
            return datetime.now().replace(second=0)
        return False

    message = fields.Text(string="Mensaje", readonly=True)
    date_start = fields.Datetime(string="Fecha y Hora Inicio", default=_default_date_start)
    date_end = fields.Datetime(string="Fecha y Hora Fin", default=_default_date_end)
    all_dates = fields.Boolean(string="Todo el tiempo de la sesión", default=False)
    
    # Campos para la sesión
    session_id = fields.Integer(string="ID de Sesión")
    session_name = fields.Char(string="Nombre de Sesión")
    
    # Campos para envío por correo
    send_email = fields.Boolean(string="Enviar por correo", default=False)
    email = fields.Many2one('res.partner', string="Correo electrónico",
                          domain="[('email', '!=', False), ('email', '=like', '%@%')]",
                          context={'show_email_as_display_name': True})
    email_text = fields.Char(string="Correo", related='email.email', readonly=True)
    
    # Campos para los documentos
    cabecera_documentos = fields.Boolean(string="Cabecera de documentos emitidos", default=True)
    cierre_caja = fields.Boolean(string="Cierre caja", default=True)
    detalle_facturacion = fields.Boolean(string="Detalle de documentos de facturación", default=True)
    detalle_inventario = fields.Boolean(string="Detalle de documentos de inventario", default=True)
    detalle_cobranza = fields.Boolean(string="Detalle de documentos de cobranza", default=True)
    
    # Campo para el formato de exportación
    formato_exportacion = fields.Selection([
        ('xml', 'XML'),
        # ('json', 'JSON'),  # Deshabilitado por ahora
        # ('csv', 'CSV')     # Deshabilitado por ahora
    ], string="Formato", default='xml', required=True)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if name:
            # Validar que el término de búsqueda tenga formato de correo
            if '@' in name:
                args = [('email', operator, name)] + args
            else:
                return []
        return self.env['res.partner'].search(args, limit=limit).ids

    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            # Cuando se selecciona un contacto, actualizamos el contexto para mostrar solo el correo
            self.email = self.env['res.partner'].with_context(
                show_email_as_display_name=True,
                selected_email=True
            ).browse(self.email.id)

    @api.model
    def default_get(self, fields):
        res = super(ExportPosSales, self).default_get(fields)
        # Obtener el contexto activo
        active_id = self.env.context.get('active_id')
        if active_id:
            session = self.env['pos.session'].browse(active_id)
            res.update({
                'session_id': session.id,
                'session_name': session.name,
            })
            # Configurar el correo por defecto si existe
            if self.env.user.partner_id and self.env.user.partner_id.email and '@' in self.env.user.partner_id.email:
                res.update({
                    'email': self.env.user.partner_id.id
                })
        return res

    @api.onchange('all_dates')
    def _onchange_all_dates(self):
        """
        Maneja el cambio en el campo all_dates.
        Siempre establece las fechas de inicio y fin según los valores por defecto de la sesión,
        independientemente del estado del checkbox, ya que estas son las fechas que necesitamos usar.
        """
        self.date_start = self._default_date_start()
        self.date_end = self._default_date_end()

    @api.onchange('send_email')
    def _onchange_send_email(self):
        if not self.send_email:
            # Si se desmarca, limpiamos el correo
            self.email = False
        else:
            # Si se marca, restauramos el correo del usuario actual
            if self.env.user.partner_id and self.env.user.partner_id.email and '@' in self.env.user.partner_id.email:
                self.email = self.env.user.partner_id.id

    def action_export_zip(self):
        # Recopilar datos para exportar
        export_data = {
            'session': {
                'id': self.session_id,
                'name': self.session_name,
            },
            'date_start': self.date_start,
            'date_end': self.date_end,
            'all_dates': self.all_dates,
            'documentos': {
                'CabeceraDocumentosEmitidos': self.cabecera_documentos,
                'CierreCaja': self.cierre_caja,
                'DetalleDocumentosFacturacion': self.detalle_facturacion,
                'DetalleDocumentosInventario': self.detalle_inventario,
                'DetalleDocumentosCobranza': self.detalle_cobranza,
            },
            'formato': self.formato_exportacion,
            'envio_correo': {
                'enviar': self.send_email,
                'correo': self.email_text if self.send_email else False
            }
        }
        
        # DEBUG: Imprimir el objeto de manera formateada
        _logger.info('\n\n=== DATOS DE EXPORTACIÓN ===\n%s\n========================\n', 
                    pformat(export_data))
        
        # Mostrar notificación de éxito en la parte inferior derecha
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Exportación Iniciada'),
                'message': _('El archivo se está generando y se descargará en breve.'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_export(self):
        # Recopilar datos para exportar
        # Configurar zona horaria de Lima
        tz = pytz.timezone('America/Lima')
        
        # Convertir las fechas a la zona horaria de Lima
        date_start_lima = self.date_start.astimezone(tz) if self.date_start else False
        date_end_lima = self.date_end.astimezone(tz) if self.date_end else False
        
        export_data = {
            'session': {
                'id': self.session_id,
                'name': self.session_name,
            },
            'date_start': date_start_lima.isoformat() if date_start_lima else False,
            'date_end': date_end_lima.isoformat() if date_end_lima else False,
            'all_dates': self.all_dates,
            'documentos': {
                'CabeceraDocumentosEmitidos': self.cabecera_documentos,
                'CierreCaja': self.cierre_caja,
                'DetalleDocumentosFacturacion': self.detalle_facturacion,
                'DetalleDocumentosInventario': self.detalle_inventario,
                'DetalleDocumentosCobranza': self.detalle_cobranza,
            },
            'formato': self.formato_exportacion,
            'envio_correo': {
                'enviar': self.send_email,
                'correo': self.email_text if self.send_email else False
            }
        }
        
        # DEBUG: Imprimir el objeto de manera formateada
        _logger.info('\n\n=== DATOS DE EXPORTACIÓN ===\n%s\n========================\n', 
                    pformat(export_data))
        
        # Convertir los datos a JSON
        params = json.dumps(export_data)
        
        # Retornar la acción de descarga con la notificación incluida
        return {
            'type': 'ir.actions.act_url',
            'url': f'/pos_session/download_zip/{self.session_id}?params={params}',
            'target': 'current',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Exportación Iniciada'),
                'message': _('El archivo se está generando y se descargará en breve.'),
                'sticky': False
            }
        }